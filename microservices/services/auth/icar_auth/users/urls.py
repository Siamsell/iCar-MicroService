from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [

    path('signup/', views.SignupView.as_view(), name='signup'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),
    
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    path('users/', views.ListUsersView.as_view(), name='list-users'),
    path('users/<int:pk>/', views.EditUserView.as_view(), name='edit-user'),
    path('admin/reset-password/<int:user_id>/', views.AdminResetPasswordView.as_view(), name='admin-reset-password'),
    
    path('users/me/delete/', views.DeleteUserView.as_view(), name='delete-own-account'),
    
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]
