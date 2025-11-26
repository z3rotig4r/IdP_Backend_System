"""
Auth Transactions 앱 웹 뷰 (MTV 패턴)
Class-Based Views 사용
"""
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Count, Q
from datetime import datetime

from .models import AuthTransaction, NotificationLog


class AuthHistoryListView(LoginRequiredMixin, ListView):
    """
    인증 이력 리스트 뷰
    - 로그인한 사용자의 인증 이력 표시
    - 페이지네이션 적용
    - 필터 기능 (상태, 날짜)
    """
    model = AuthTransaction
    template_name = 'auth_transactions/auth_history.html'
    context_object_name = 'object_list'
    paginate_by = 10
    login_url = reverse_lazy('accounts:login')
    
    def get_queryset(self):
        """
        현재 사용자의 트랜잭션만 필터링
        상태 및 날짜 필터 적용
        """
        queryset = AuthTransaction.objects.filter(
            user=self.request.user
        ).select_related('service_provider').order_by('-created_at')
        
        # 상태 필터
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # 날짜 필터
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=date_to_obj)
            except ValueError:
                pass
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """통계 정보 추가"""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # 전체 통계
        context['stats'] = {
            'completed': AuthTransaction.objects.filter(
                user=user, status='COMPLETED'
            ).count(),
            'failed': AuthTransaction.objects.filter(
                user=user, status='FAILED'
            ).count(),
            'pending': AuthTransaction.objects.filter(
                user=user, status='PENDING'
            ).count(),
        }
        
        return context


class TransactionDetailView(LoginRequiredMixin, DetailView):
    """
    인증 트랜잭션 상세 뷰
    - 트랜잭션 상세 정보 표시
    - 관련 알림 로그 포함
    """
    model = AuthTransaction
    template_name = 'auth_transactions/transaction_detail.html'
    context_object_name = 'object'
    slug_field = 'transaction_id'
    slug_url_kwarg = 'transaction_id'
    login_url = reverse_lazy('accounts:login')
    
    def get_queryset(self):
        """현재 사용자의 트랜잭션만 조회 가능"""
        return AuthTransaction.objects.filter(
            user=self.request.user
        ).select_related('service_provider', 'user')
    
    def get_context_data(self, **kwargs):
        """관련 알림 로그 추가"""
        context = super().get_context_data(**kwargs)
        
        # 관련 알림
        context['notifications'] = NotificationLog.objects.filter(
            transaction=self.object
        ).order_by('-sent_at')
        
        return context
