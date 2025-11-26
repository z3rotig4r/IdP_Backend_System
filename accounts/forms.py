"""
Accounts 앱 폼 정의
MTV 패턴의 View 레이어에서 사용되는 폼 클래스들
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
import re

from .models import User


class UserRegistrationForm(UserCreationForm):
    """
    사용자 회원가입 폼
    - 전화번호, 이메일, PIN 코드 등 커스텀 필드 검증
    - Bootstrap 클래스 자동 적용
    """
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        label='전화번호',
        help_text='형식: 010-1234-5678',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '010-1234-5678'
        })
    )
    
    email = forms.EmailField(
        required=True,
        label='이메일',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@email.com'
        })
    )
    
    pin_code = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        label='PIN 코드',
        help_text='6자리 숫자',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '******'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'phone_number', 'password1', 'password2', 'pin_code')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Bootstrap 클래스 추가
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def clean_phone_number(self):
        """전화번호 형식 검증"""
        phone_number = self.cleaned_data.get('phone_number')
        
        # 한국 전화번호 형식 검증
        pattern = r'^01[0-9]-\d{3,4}-\d{4}$'
        if not re.match(pattern, phone_number):
            raise ValidationError('올바른 전화번호 형식이 아닙니다. (예: 010-1234-5678)')
        
        # 중복 검증
        if User.objects.filter(phone_number=phone_number).exists():
            raise ValidationError('이미 등록된 전화번호입니다.')
        
        return phone_number
    
    def clean_pin_code(self):
        """PIN 코드 검증"""
        pin_code = self.cleaned_data.get('pin_code')
        
        # 숫자만 허용
        if not pin_code.isdigit():
            raise ValidationError('PIN 코드는 6자리 숫자만 입력 가능합니다.')
        
        # 연속된 숫자 검증 (123456, 111111 등 방지)
        if len(set(pin_code)) == 1:
            raise ValidationError('모두 같은 숫자는 사용할 수 없습니다.')
        
        # 순차적인 숫자 검증
        is_sequential = all(
            int(pin_code[i+1]) - int(pin_code[i]) == 1 
            for i in range(len(pin_code)-1)
        )
        if is_sequential:
            raise ValidationError('순차적인 숫자는 사용할 수 없습니다.')
        
        return pin_code
    
    def save(self, commit=True):
        """
        사용자 저장 시 PIN 코드 설정 및 CI/DI 자동 생성
        """
        user = super().save(commit=False)
        
        # PIN 코드 해시화하여 저장
        pin_code = self.cleaned_data.get('pin_code')
        user.set_pin(pin_code)
        
        # CI/DI 자동 생성 (실제 환경에서는 NICE 등의 본인인증 API 사용)
        import hashlib
        import time
        
        unique_string = f"{user.username}_{user.phone_number}_{time.time()}"
        user.ci = hashlib.sha256(unique_string.encode()).hexdigest()
        user.di = hashlib.sha256(f"{user.ci}_{user.email}".encode()).hexdigest()
        
        if commit:
            user.save()
        
        return user


class CustomLoginForm(AuthenticationForm):
    """
    커스텀 로그인 폼
    - Bootstrap 스타일 적용
    """
    username = forms.CharField(
        label='사용자명',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '사용자명을 입력하세요',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        label='비밀번호',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '비밀번호를 입력하세요'
        })
    )


class PINConfirmForm(forms.Form):
    """
    PIN 확인 폼
    - 인증 확인 시 사용
    """
    pin_code = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        label='PIN 코드',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '6자리 PIN 입력',
            'autocomplete': 'off'
        })
    )
    
    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_pin_code(self):
        """PIN 코드 검증"""
        pin_code = self.cleaned_data.get('pin_code')
        
        if not pin_code.isdigit():
            raise ValidationError('PIN 코드는 6자리 숫자만 입력 가능합니다.')
        
        # 사용자의 PIN 확인
        if self.user and not self.user.check_pin(pin_code):
            raise ValidationError('PIN 코드가 일치하지 않습니다.')
        
        return pin_code


class ProfileUpdateForm(forms.ModelForm):
    """
    프로필 수정 폼
    """
    class Meta:
        model = User
        fields = ('email', 'phone_number')
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'example@email.com'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '010-1234-5678'
            })
        }
    
    def clean_phone_number(self):
        """전화번호 형식 및 중복 검증"""
        phone_number = self.cleaned_data.get('phone_number')
        
        # 형식 검증
        pattern = r'^01[0-9]-\d{3,4}-\d{4}$'
        if not re.match(pattern, phone_number):
            raise ValidationError('올바른 전화번호 형식이 아닙니다.')
        
        # 중복 검증 (자신 제외)
        if User.objects.filter(phone_number=phone_number).exclude(pk=self.instance.pk).exists():
            raise ValidationError('이미 등록된 전화번호입니다.')
        
        return phone_number


class PasswordChangeForm(forms.Form):
    """
    비밀번호 변경 폼
    """
    old_password = forms.CharField(
        label='현재 비밀번호',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '현재 비밀번호'
        })
    )
    
    new_password1 = forms.CharField(
        label='새 비밀번호',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '새 비밀번호'
        }),
        help_text='8자 이상, 영문/숫자/특수문자 포함'
    )
    
    new_password2 = forms.CharField(
        label='새 비밀번호 확인',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '새 비밀번호 확인'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_old_password(self):
        """기존 비밀번호 확인"""
        old_password = self.cleaned_data.get('old_password')
        
        if not self.user.check_password(old_password):
            raise ValidationError('현재 비밀번호가 일치하지 않습니다.')
        
        return old_password
    
    def clean_new_password2(self):
        """새 비밀번호 확인"""
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError('새 비밀번호가 일치하지 않습니다.')
        
        return password2
    
    def save(self):
        """비밀번호 변경"""
        password = self.cleaned_data.get('new_password1')
        self.user.set_password(password)
        self.user.save()
        return self.user


class PINChangeForm(forms.Form):
    """
    PIN 변경 폼
    """
    old_pin = forms.CharField(
        max_length=6,
        label='현재 PIN',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '현재 PIN'
        })
    )
    
    new_pin1 = forms.CharField(
        max_length=6,
        label='새 PIN',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '새 PIN (6자리)'
        })
    )
    
    new_pin2 = forms.CharField(
        max_length=6,
        label='새 PIN 확인',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '새 PIN 확인'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_old_pin(self):
        """기존 PIN 확인"""
        old_pin = self.cleaned_data.get('old_pin')
        
        if not self.user.check_pin(old_pin):
            raise ValidationError('현재 PIN이 일치하지 않습니다.')
        
        return old_pin
    
    def clean_new_pin1(self):
        """새 PIN 검증"""
        new_pin = self.cleaned_data.get('new_pin1')
        
        if not new_pin.isdigit():
            raise ValidationError('PIN은 6자리 숫자만 입력 가능합니다.')
        
        if len(new_pin) != 6:
            raise ValidationError('PIN은 정확히 6자리여야 합니다.')
        
        return new_pin
    
    def clean_new_pin2(self):
        """새 PIN 확인"""
        pin1 = self.cleaned_data.get('new_pin1')
        pin2 = self.cleaned_data.get('new_pin2')
        
        if pin1 and pin2 and pin1 != pin2:
            raise ValidationError('새 PIN이 일치하지 않습니다.')
        
        return pin2
    
    def save(self):
        """PIN 변경"""
        new_pin = self.cleaned_data.get('new_pin1')
        self.user.set_pin(new_pin)
        self.user.save()
        return self.user
