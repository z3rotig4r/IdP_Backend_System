"""
URL configuration for auth_transactions app
API와 웹 뷰 분리
"""
from django.urls import path
from . import views, web_views

app_name = 'auth_transactions'

urlpatterns = [
    # API Endpoints (Function-Based Views - RESTful API)
    path('api/request/', views.auth_request, name='api_auth_request'),
    path('api/confirm/', views.auth_confirm, name='api_auth_confirm'),
    path('api/status/<uuid:transaction_id>/', views.auth_status, name='api_auth_status'),
    
    # Web Views (Class-Based Views - MTV Pattern)
    path('pending/', web_views.PendingAuthListView.as_view(), name='auth_pending'),
    path('history/', web_views.AuthHistoryListView.as_view(), name='auth_history'),
    path('detail/<uuid:transaction_id>/', web_views.TransactionDetailView.as_view(), name='transaction_detail'),
    path('confirm/<uuid:transaction_id>/', web_views.ConfirmTransactionView.as_view(), name='confirm_transaction'),
]

