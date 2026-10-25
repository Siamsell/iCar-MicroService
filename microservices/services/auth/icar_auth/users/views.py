from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from .models import User
from .serializers import (
    UserSerializer, UserDetailSerializer, SignupSerializer, 
    LoginSerializer, UpdateProfileSerializer, ChangePasswordSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer
)
from .rabbitmq import publish_user_deleted,publish_user_created,publish_user_updated
from .permissions import IsAdmin, IsUserOrAdmin
from .tokens import CustomRefreshToken


class SignupView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = CustomRefreshToken.for_user(user)

            user = UserSerializer(user).data
            
            user.pop("role", None)
            
            publish_user_created(user=user)
            
            return Response({
                'message': 'User created successfully',
                'user': user,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            user = authenticate(email=email, password=password)
            
           
            
            if user and user.is_active:
                refresh = CustomRefreshToken.for_user(user)
                return Response({
                    'message': 'Login successful',
                    'user': UserSerializer(user).data,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated,IsUserOrAdmin]
    
    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request):
        serializer = UpdateProfileSerializer(request.user, data=request.data, context={'request': request})
        if serializer.is_valid():
            
            if not (request.user.id == request.data.get("id") or request.user.role == 'admin'):
                return Response({
                'error': 'Permission denied. You can only update your own profile.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer.save()
            
            user = serializer.data

            user["id"] = request.data.get("id")
            
            publish_user_updated(user=user)
            
            return Response({
                'message': 'Profile updated successfully',
                'user': serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({'old_password': 'Wrong password'}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                # Generate reset token (in production, use a more secure method)
                reset_token = RefreshToken.for_user(user).access_token
                
                # Send email with reset link
                reset_link = f"http://localhost:8000/api/reset-password/?token={reset_token}&email={email}"
                send_mail(
                    'Password Reset Request',
                    f'Click the link to reset your password: {reset_link}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                return Response({
                    'message': 'Password reset link has been sent to your email'
                }, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'error': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ListUsersView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    serializer_class = UserSerializer
    
    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')
        user_id = self.request.query_params.get('id')
        if user_id:
            queryset = queryset.filter(id=user_id)
        
        return queryset


class EditUserView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsUserOrAdmin]
    queryset = User.objects.all()
    serializer_class = UserSerializer
    




class AdminResetPasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    
    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            new_password = request.data.get('new_password')
            if not new_password:
                return Response({'error': 'New password is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)




class DeleteUserView(APIView):
    """
    Delete user account and publish event to RabbitMQ
    Other services will clean up their data (vehicles, notifications, follows)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request):
        
       
        if request.user.id and request.user.role == 'admin':
            target_user_id = request.user.id
        elif request.user.id:
            target_user_id = request.user.id
        else:
            return Response({
                'error': 'Permission denied. You can only delete your own account or as admin.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            user = User.objects.get(id=target_user_id)
            
            if request.user.id == target_user_id and request.user.role == 'admin':
                return Response({
                    'error': 'Admin cannot delete own account through this endpoint. Use admin interface.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Store user info before deletion
            user_id = user.id
            user_email = user.email
            user_name = user.name
            
            # Publish user deletion event to RabbitMQ
            # This will trigger cleanup in catalog and notification services
            event_published = publish_user_deleted(
                user_id=user_id,
                user_email=user_email,
                user_name=user_name
            )
            
            if not event_published:
                return Response({
                    'warning': 'User account deleted but cleanup events could not be published. Some data may remain in other services.',
                    'user_deleted': True
                }, status=status.HTTP_202_ACCEPTED)
            
            # Delete the user
            user.delete()
            
            return Response({
                'message': 'User account deleted successfully. All associated data will be cleaned up in other services.',
                'user_id': user_id,
                'email': user_email,
                'cleaned_up': {
                    'catalog_service': 'Pending - Vehicles and images will be deleted',
                    'notification_service': 'Pending - Notifications and follows will be deleted'
                }
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Failed to delete user: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
