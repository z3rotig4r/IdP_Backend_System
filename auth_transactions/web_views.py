"""
Auth Transactions 앱 웹 뷰 (MTV 패턴)
Class-Based Views 사용
"""
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views import View
from django.utils import timezone
from datetime import datetime

from .models import AuthTransaction, NotificationLog


class PendingAuthListView(LoginRequiredMixin, ListView):
    """
    대기 중인 인증 요청 리스트 뷰
    - PENDING 상태의 요청만 표시
    - 만료되지 않은 요청만 표시
    """
    model = AuthTransaction
    template_name = 'auth_transactions/pending_list.html'
    context_object_name = 'pending_list'
    paginate_by = 20
    login_url = reverse_lazy('accounts:login')
    
    def get_queryset(self):
        """대기 중이고 만료되지 않은 요청만"""
        from django.db.models import Q
        return AuthTransaction.objects.filter(
            user=self.request.user,
            status='PENDING',
            expires_at__gt=timezone.now()
        ).select_related('service_provider').order_by('-created_at')


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


class ConfirmTransactionView(LoginRequiredMixin, View):
    """
    웹에서 인증 트랜잭션 승인/거부 처리
    POST 요청으로 PIN 검증 후 처리
    """
    login_url = reverse_lazy('accounts:login')
    
    def post(self, request, transaction_id):
        """승인 또는 거부 처리"""
        # 트랜잭션 조회 (본인 것만)
        transaction = get_object_or_404(
            AuthTransaction,
            transaction_id=transaction_id,
            user=request.user
        )
        
        # 상태 확인
        if transaction.status != 'PENDING':
            messages.error(request, '이미 처리된 요청입니다.')
            return redirect('auth_transactions:transaction_detail', transaction_id=transaction_id)
        
        # 만료 확인
        if transaction.is_expired:
            transaction.status = 'EXPIRED'
            transaction.failure_reason = '요청이 만료되었습니다.'
            transaction.save()
            messages.error(request, '만료된 요청입니다.')
            return redirect('auth_transactions:transaction_detail', transaction_id=transaction_id)
        
        # 액션 확인
        action = request.POST.get('action')  # 'approve' 또는 'reject'
        
        if action == 'approve':
            # PIN 검증
            pin = request.POST.get('pin')
            
            if not pin:
                messages.error(request, 'PIN을 입력해주세요.')
                return redirect('auth_transactions:transaction_detail', transaction_id=transaction_id)
            
            # PIN 검증 (User 모델의 check_pin 메서드 사용)
            try:
                if not request.user.check_pin(pin):
                    messages.error(request, f'PIN이 올바르지 않습니다. 입력한 PIN: {pin}')
                    return redirect('auth_transactions:transaction_detail', transaction_id=transaction_id)
            except Exception as e:
                messages.error(request, f'PIN 검증 오류: {str(e)}')
                return redirect('auth_transactions:transaction_detail', transaction_id=transaction_id)
            
            # 승인 처리
            transaction.status = 'COMPLETED'
            transaction.confirmed_at = timezone.now()
            transaction.save()
            
            messages.success(request, f'인증 요청을 승인했습니다. (Transaction: {transaction_id})')
            
        elif action == 'reject':
            # 거부 처리
            transaction.status = 'FAILED'
            transaction.failure_reason = '사용자가 거부함'
            transaction.confirmed_at = timezone.now()
            transaction.save()
            
            messages.warning(request, '인증 요청을 거부했습니다.')
        
        else:
            messages.error(request, '잘못된 요청입니다.')
        
        return redirect('auth_transactions:transaction_detail', transaction_id=transaction_id)
