"""
Accounts 앱 URL 설정
"""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # 인증
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    
    # 프로필
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    
    # 보안
    path('password/change/', views.PasswordChangeView.as_view(), name='change_password'),
    path('pin/change/', views.PINChangeView.as_view(), name='change_pin'),
]
