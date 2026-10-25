from django.urls import path,include
from . import views
from rest_framework import routers
from .views import UserModelViewSet,VehiculeModelViewSet

router = routers.DefaultRouter()

router.register(r'users',UserModelViewSet)
router.register(r'cars',VehiculeModelViewSet)


urlpatterns = [

    # ── Notifications ─────────────────────────────────────────────────────────
    path('notifications/',                views.notification_list,         name='notification-list'),
    path('notifications/simple/',         views.notification_create_simple, name='notification-simple'),
    path('notifications/read-all/',       views.notification_mark_all_read, name='notification-read-all'),
    path('notifications/<int:pk>/read/',  views.notification_mark_read,    name='notification-read'),
    path('notifications/<int:pk>/',       views.notification_delete,       name='notification-delete'),

    # ── Follow / Unfollow Post ────────────────────────────────────────────────
    path('follow/post/',  views.follow_post,       name='follow-post'),
    path('unfollow/post/', views.unfollow_post,    name='unfollow-post'),
    path('follow/post/list/', views.list_follow_post, name='list-follow-post'),

    # ── Follow / Unfollow User ────────────────────────────────────────────────
    path('follow/user/',  views.follow_user,       name='follow-user'),
    path('unfollow/user/', views.unfollow_user,    name='unfollow-user'),
    path('follow/user/list/', views.list_follow_user, name='list-follow-user'),

    # ── Content Event (simulate Main API) ────────────────────────────────────
    path('events/content/', views.content_event,   name='content-event'),
    path('',include(router.urls))
]
