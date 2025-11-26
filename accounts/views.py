"""
Accounts 앱 뷰 (MTV 패턴의 View 레이어)
Class-Based Views 사용
"""
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, CreateView, UpdateView, FormView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count, Q

from .models import User, UserRoleAssignment
from .forms import (
    UserRegistrationForm, 
    CustomLoginForm, 
    ProfileUpdateForm,
    PasswordChangeForm,
    PINChangeForm
)
from auth_transactions.models import AuthTransaction


class HomeView(TemplateView):
    """
    홈페이지 뷰
    - 로그인하지 않은 사용자에게 랜딩 페이지 표시
    """
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 전체 통계 (공개 정보)
        context['total_users'] = User.objects.count()
        context['total_transactions'] = AuthTransaction.objects.count()
        context['success_rate'] = self._calculate_success_rate()
        
        return context
    
    def _calculate_success_rate(self):
        """인증 성공률 계산"""
        total = AuthTransaction.objects.count()
        if total == 0:
            return 0
        
        completed = AuthTransaction.objects.filter(status='COMPLETED').count()
        return round((completed / total) * 100, 1)


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    사용자 대시보드
    - 로그인 필요
    - 개인 인증 통계 표시
    """
    template_name = 'dashboard.html'
    login_url = reverse_lazy('accounts:login')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # 사용자별 통계
        context['auth_stats'] = self._get_user_auth_stats(user)
        
        # 최근 트랜잭션 (최근 5개)
        context['recent_transactions'] = AuthTransaction.objects.filter(
            user=user
        ).select_related('service_provider').order_by('-created_at')[:5]
        
        # 사용자 역할
        context['user_roles'] = UserRoleAssignment.objects.filter(
            user=user
        ).select_related('role')
        
        return context
    
    def _get_user_auth_stats(self, user):
        """사용자 인증 통계"""
        transactions = AuthTransaction.objects.filter(user=user)
        
        return {
            'total': transactions.count(),
            'completed': transactions.filter(status='COMPLETED').count(),
            'failed': transactions.filter(status='FAILED').count(),
            'pending': transactions.filter(status='PENDING').count(),
        }


class UserLoginView(LoginView):
    """
    사용자 로그인 뷰
    - Django의 LoginView 확장
    """
    form_class = CustomLoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """로그인 성공 시 리다이렉트"""
        return reverse_lazy('dashboard')
    
    def form_valid(self, form):
        """로그인 성공"""
        messages.success(self.request, f'{form.get_user().username}님, 환영합니다!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """로그인 실패"""
        messages.error(self.request, '사용자명 또는 비밀번호가 올바르지 않습니다.')
        return super().form_invalid(form)


class UserLogoutView(LogoutView):
    """
    사용자 로그아웃 뷰
    """
    next_page = reverse_lazy('home')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, '로그아웃되었습니다.')
        return super().dispatch(request, *args, **kwargs)


class UserRegistrationView(CreateView):
    """
    회원가입 뷰
    - CreateView를 사용한 사용자 생성
    """
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        """회원가입 성공"""
        response = super().form_valid(form)
        
        # 성공 메시지
        messages.success(
            self.request,
            f'{form.instance.username}님, 회원가입이 완료되었습니다. 로그인해주세요.'
        )
        
        return response
    
    def form_invalid(self, form):
        """회원가입 실패"""
        messages.error(self.request, '입력 정보를 확인해주세요.')
        return super().form_invalid(form)


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    사용자 프로필 조회
    """
    template_name = 'accounts/profile.html'
    login_url = reverse_lazy('accounts:login')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # 사용자 역할
        context['user_roles'] = UserRoleAssignment.objects.filter(
            user=user
        ).select_related('role')
        
        # 인증 통계
        context['auth_stats'] = {
            'total': AuthTransaction.objects.filter(user=user).count(),
            'completed': AuthTransaction.objects.filter(user=user, status='COMPLETED').count(),
            'failed': AuthTransaction.objects.filter(user=user, status='FAILED').count(),
        }
        
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """
    프로필 수정
    """
    model = User
    form_class = ProfileUpdateForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')
    login_url = reverse_lazy('accounts:login')
    
    def get_object(self, queryset=None):
        """현재 로그인한 사용자만 수정 가능"""
        return self.request.user
    
    def form_valid(self, form):
        """수정 성공"""
        messages.success(self.request, '프로필이 업데이트되었습니다.')
        return super().form_valid(form)


class PasswordChangeView(LoginRequiredMixin, FormView):
    """
    비밀번호 변경
    """
    form_class = PasswordChangeForm
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:profile')
    login_url = reverse_lazy('accounts:login')
    
    def get_form_kwargs(self):
        """폼에 현재 사용자 전달"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """비밀번호 변경 성공"""
        form.save()
        messages.success(self.request, '비밀번호가 변경되었습니다. 다시 로그인해주세요.')
        
        # 비밀번호 변경 후 로그아웃
        from django.contrib.auth import logout
        logout(self.request)
        
        return redirect('accounts:login')


class PINChangeView(LoginRequiredMixin, FormView):
    """
    PIN 변경
    """
    form_class = PINChangeForm
    template_name = 'accounts/pin_change.html'
    success_url = reverse_lazy('accounts:profile')
    login_url = reverse_lazy('accounts:login')
    
    def get_form_kwargs(self):
        """폼에 현재 사용자 전달"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """PIN 변경 성공"""
        form.save()
        messages.success(self.request, 'PIN이 변경되었습니다.')
        return super().form_valid(form)
