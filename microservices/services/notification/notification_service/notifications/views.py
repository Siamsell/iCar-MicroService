from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from notification_service.authentication import StatelessJWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from .models import Notification, UserFollowPost, UserFollowUser,UserModel,VehiculeModel
from .serializers import (
    NotificationSerializer,
    UserFollowPostSerializer,
    UserFollowUserSerializer,
    UserModelSerializer,
    VehiculeModelSerializer
)

from .rabbit import publish_follow_user,publish_follow_post,publish_content_event


 
class UserModelViewSet(viewsets.ModelViewSet):
    queryset = UserModel.objects.all()
    serializer_class = UserModelSerializer   
    
class VehiculeModelViewSet(viewsets.ModelViewSet):
    queryset = VehiculeModel.objects.all()
    serializer_class = VehiculeModelSerializer   

# ──────────────────────────────────────────────────────────────────────────────
# NOTIFICATIONS
# ──────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@authentication_classes([StatelessJWTAuthentication])
@permission_classes([IsAuthenticated])
def notification_list(request):
    """
    GET /api/notifications/?user=<id>
    Returns all notifications for a user, ordered newest-first.
    """
    # user = request.user.id
    user = request.query_params.get("user")
    
    if not user:
        if request.user.is_authenticated:
            user = request.user.id
        else:
            return Response(
            {'error': 'user query param is required'},
            status=status.HTTP_400_BAD_REQUEST
            )
    notifications = Notification.objects.filter(user=user)
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
@authentication_classes([StatelessJWTAuthentication])
@permission_classes([IsAuthenticated])
def notification_mark_read(request, pk):
    """
    PATCH /api/notifications/<pk>/read/
    Marks a single notification as read.
    """
    try:
        notification = Notification.objects.get(pk=pk)
    except Notification.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    notification.is_read = True
    notification.save(update_fields=['is_read'])
    serializer = NotificationSerializer(notification)
    return Response(serializer.data)


@api_view(['PATCH'])
@authentication_classes([StatelessJWTAuthentication])
@permission_classes([IsAuthenticated])
def notification_mark_all_read(request):
    """
    PATCH /api/notifications/read-all/?user=<id>
    Marks all notifications for a user as read.
    """
    user = request.user.id
    if not user:
        return Response(
            {'error': 'user query param is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    updated = Notification.objects.filter(user=user, is_read=False).update(is_read=True)
    return Response({'updated': updated})


@api_view(['DELETE'])
@authentication_classes([StatelessJWTAuthentication])
@permission_classes([IsAuthenticated])
def notification_delete(request, pk):
    """
    DELETE /api/notifications/<pk>/
    Deletes a single notification.
    """
    try:
        notification = Notification.objects.get(pk=pk)
    except Notification.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    notification.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────────────────────
# SIMPLE NOTIFICATION (direct, no RabbitMQ — for testing / admin use)
# ──────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
def notification_create_simple(request):
    """
    POST /api/notifications/simple/
    Body: { "user": 1, "subject": "...", "message": "...", "post": null }
    Creates a notification directly (no queue). Useful for testing.
    """
    serializer = NotificationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────────────────────────────────────
# FOLLOW POST
# ──────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@authentication_classes([StatelessJWTAuthentication])
@permission_classes([IsAuthenticated])
def follow_post(request):
    """
    POST /api/follow/post/
    Body: {"id": 10 ,"user":3}
    Saves the follow relationship, then publishes a RabbitMQ message
    so the worker notifies the post owner.
    """
    
    user = request.user.id
    post = int(request.data.get("id"))
        
    
    serializer = UserFollowPostSerializer(data={
    "user": user,
    "post": post
    })
    
    if serializer.is_valid():
        try:
            instance = serializer.save()
        except Exception:
            return Response(
                {'error': 'Already following this post'},
                status=status.HTTP_409_CONFLICT
            )

        
        publish_follow_post(user, post,request.user.name)


        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@authentication_classes([StatelessJWTAuthentication])
@permission_classes([IsAuthenticated])
def unfollow_post(request):
    """
    DELETE /api/follow/post/
    Body: {"post": 10 }
    Removes the follow relationship silently — NO notification sent.
    """
    user = request.user.id
    post = request.data.get('post')

    
    deleted, _ = UserFollowPost.objects.filter(
        user=user, post=post
    ).delete()
    if deleted:
        return Response({'detail': 'Unfollowed post'}, status=status.HTTP_200_OK)
    return Response({'error': 'Follow relationship not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@authentication_classes([StatelessJWTAuthentication])
@permission_classes([IsAuthenticated])
def list_follow_post(request):
   
    user = request.user.id
    post = request.query_params.get('post')
    
  
    if request.query_params.get("user") and int(request.query_params["user"]) != int(request.user.id):
        raise PermissionDenied("You Don't Have This Permission")

    qs = UserFollowPost.objects.all()
    if user:
        qs = qs.filter(user=user)
    if post:
        qs = qs.filter(post=post)

    serializer = UserFollowPostSerializer(qs, many=True)
    return Response(serializer.data)


# ──────────────────────────────────────────────────────────────────────────────
# FOLLOW USER
# ──────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@authentication_classes([StatelessJWTAuthentication])
@permission_classes([IsAuthenticated])
def follow_user(request):
    """
    POST /api/follow/user/
    Body: { "following": 2 }
    Saves the follow relationship, then publishes a RabbitMQ message
    so the worker notifies the followed user.
    """
    follower = request.user.id
    following = request.data.get("following")
    
    data = {
        "follower":follower,
        "following":following
    }
    
    if follower == following :
        raise PermissionDenied("U Cant Follow Your Self")
    
    serializer = UserFollowUserSerializer(data=data)
    if serializer.is_valid():
        try:
            instance = serializer.save()
        except Exception:
            return Response(
                {'error': 'U Cannot Follow this User'},
                status=status.HTTP_409_CONFLICT
            )

        print(request.user.name)

        from .rabbit import publish_follow_user
        
        print(f"follower = {instance.follower.id}, following = {instance.following.id}, {request.user.name}")
        
        publish_follow_user(instance.follower.id, instance.following.id,request.user.name)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['DELETE'])
@authentication_classes([StatelessJWTAuthentication])
@permission_classes([IsAuthenticated])
def unfollow_user(request):
    """
    DELETE /api/follow/user/
    Body: { "following": 2 }
    Removes the follow relationship silently — NO notification sent.
    """
    follower  = request.user.id
    following = request.data.get('following')
    
    deleted, _ = UserFollowUser.objects.filter(
        follower=follower, following=following
    ).delete()
    if deleted:
        return Response({'detail': 'Unfollowed user'}, status=status.HTTP_200_OK)
    return Response({'error': 'Follow relationship not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@authentication_classes([StatelessJWTAuthentication])
@permission_classes([IsAuthenticated])
def list_follow_user(request):
    """
    GET /api/follow/user/?follower=<id>   → users this person follows
    GET /api/follow/user/?following=<id>  → followers of this user
    """
    follower  = request.query_params.get('follower')
    following = request.query_params.get('following')
    
    if follower != request.user.id and following != request.user.id:
        raise PermissionDenied("Permission Denied")
    
    

    qs = UserFollowUser.objects.all()
    if follower:
        qs = qs.filter(follower=follower)
    if following:
        qs = qs.filter(following=following)

    serializer = UserFollowUserSerializer(qs, many=True)
    return Response(serializer.data)


# ──────────────────────────────────────────────────────────────────────────────
# CONTENT EVENT  (simulate Main API publishing a car add/edit)
# ──────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
def content_event(request):
    """
    POST /api/events/content/
    Body: { "owner_user": 1, "post": 10, "event_type": "add_car", "title": "New Ferrari" }
    Simulates the Main API publishing a content event.
    The worker will then fan-out notifications to all followers.
    """
    owner_user = request.data.get('owner_user')
    post       = request.data.get('post')
    event_type    = request.data.get('event_type', 'content_update')
    title         = request.data.get('title', 'Content updated')

    if not owner_user:
        return Response(
            {'error': 'owner_user is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    from .rabbit import publish_content_event
    publish_content_event(owner_user, post, event_type, title)

    return Response({'detail': 'Content event published to queue'}, status=status.HTTP_202_ACCEPTED)
