"""
URL configuration for idp_backend project.

MTV 패턴에 따른 URL 구조:
- / : 홈페이지 (웹)
- /dashboard/ : 사용자 대시보드 (웹)
- /accounts/ : 계정 관리 (웹)
- /auth/ : 인증 트랜잭션 (웹)
- /api/v1/auth/ : 인증 API (REST)
- /admin/ : 관리자 페이지
"""
from django.contrib import admin
from django.urls import path, include
from accounts.views import HomeView, DashboardView

urlpatterns = [
    # 웹 페이지
    path('', HomeView.as_view(), name='home'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    
    # 앱 URL 패턴
    path('accounts/', include('accounts.urls')),
    path('auth/', include(('auth_transactions.urls', 'auth_transactions'), namespace='auth_web')),
    
    # API 엔드포인트
    path('api/v1/auth/', include(('auth_transactions.urls', 'auth_transactions'), namespace='auth_api')),
    
    # 관리자
    path('admin/', admin.site.urls),
]

