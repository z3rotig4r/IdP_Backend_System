"""
User and Role models for IdP Backend System
"""
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from cryptography.fernet import Fernet
from django.conf import settings
import bcrypt


class User(AbstractUser):
    """
    Extended User model with IdP-specific fields
    - phone_number: Unique identifier for push notifications
    - pin_code: Hashed 6-digit PIN for authentication
    - ci: Encrypted Connecting Information (고유 식별정보)
    - di: Encrypted Duplication Information (서비스 연계정보)
    """
    
    phone_validator = RegexValidator(
        regex=r'^\d{3}-\d{4}-\d{4}$',
        message="Phone number must be in format: 010-1234-5678"
    )
    
    phone_number = models.CharField(
        max_length=13,
        unique=True,
        validators=[phone_validator],
        db_index=True,
        help_text="Format: 010-1234-5678"
    )
    pin_code = models.CharField(
        max_length=255,
        help_text="Hashed 6-digit PIN code"
    )
    ci = models.CharField(
        max_length=500,
        unique=True,
        help_text="Encrypted Connecting Information (CI)"
    )
    di = models.CharField(
        max_length=500,
        unique=True,
        help_text="Encrypted Duplication Information (DI)"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['phone_number'], name='idx_user_phone'),
            models.Index(fields=['ci'], name='idx_user_ci'),
            models.Index(fields=['-created_at'], name='idx_user_created_at'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(phone_number__regex=r'^\d{3}-\d{4}-\d{4}$'),
                name='chk_phone_format'
            ),
        ]
    
    def set_pin(self, raw_pin):
        """Hash and set PIN code"""
        hashed = bcrypt.hashpw(raw_pin.encode('utf-8'), bcrypt.gensalt())
        self.pin_code = hashed.decode('utf-8')
    
    def check_pin(self, raw_pin):
        """Verify PIN code"""
        return bcrypt.checkpw(
            raw_pin.encode('utf-8'),
            self.pin_code.encode('utf-8')
        )
    
    def __str__(self):
        return f"{self.username} ({self.phone_number})"


class UserRole(models.Model):
    """
    Role definition for RBAC (Role-Based Access Control)
    """
    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Super Administrator'),
        ('SERVICE_ADMIN', 'Service Administrator'),
        ('AUDITOR', 'Auditor'),
        ('USER', 'User'),
    ]
    
    role_name = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        unique=True
    )
    description = models.TextField(blank=True)
    permissions = models.JSONField(
        default=dict,
        help_text="JSON object containing permissions"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'accounts_userrole'
        verbose_name = 'User Role'
        verbose_name_plural = 'User Roles'
    
    def __str__(self):
        return self.get_role_name_display()


class UserRoleAssignment(models.Model):
    """
    M:N relationship between User and UserRole
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='role_assignments'
    )
    role = models.ForeignKey(
        UserRole,
        on_delete=models.CASCADE,
        related_name='user_assignments'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='role_assignments_made'
    )
    
    class Meta:
        db_table = 'accounts_userroleassignment'
        verbose_name = 'User Role Assignment'
        verbose_name_plural = 'User Role Assignments'
        unique_together = ('user', 'role')
        indexes = [
            models.Index(fields=['user', 'role'], name='idx_user_role'),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.role.role_name}"
