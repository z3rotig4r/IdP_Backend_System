"""
AuthTransaction model - Core transaction management for IdP
"""
from django.db import models
from django.utils import timezone
import uuid
import secrets


class AuthTransaction(models.Model):
    """
    Authentication Transaction - manages the lifecycle of an authentication request
    This is the core table that tracks each authentication session
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('EXPIRED', 'Expired'),
    ]
    
    transaction_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for this authentication transaction"
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.RESTRICT,  # Preserve transaction history
        related_name='auth_transactions',
        help_text="User being authenticated"
    )
    service_provider = models.ForeignKey(
        'services.ServiceProvider',
        on_delete=models.RESTRICT,  # Preserve transaction history
        related_name='auth_transactions',
        help_text="Service requesting authentication"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        db_index=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the authentication request was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last update time"
    )
    expires_at = models.DateTimeField(
        db_index=True,
        help_text="When this transaction expires (typically 3 minutes)"
    )
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the user confirmed/rejected this transaction"
    )
    auth_code = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        help_text="One-time authorization code generated upon successful authentication"
    )
    failure_reason = models.TextField(
        blank=True,
        help_text="Reason for failure (if status is FAILED)"
    )
    
    class Meta:
        db_table = 'auth_transactions_authtransaction'
        verbose_name = 'Authentication Transaction'
        verbose_name_plural = 'Authentication Transactions'
        indexes = [
            models.Index(
                fields=['status', 'expires_at'],
                name='idx_tx_status_expires'
            ),
            models.Index(
                fields=['user', '-created_at'],
                name='idx_tx_user_created'
            ),
            models.Index(
                fields=['service_provider', '-created_at'],
                name='idx_tx_sp_created'
            ),
            models.Index(
                fields=['created_at'],
                name='idx_tx_created_at'
            ),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(status__in=['PENDING', 'COMPLETED', 'FAILED', 'EXPIRED']),
                name='chk_status_values'
            ),
            models.CheckConstraint(
                check=models.Q(expires_at__gt=models.F('created_at')),
                name='chk_expires_after_created'
            ),
        ]
        ordering = ['-created_at']
    
    @staticmethod
    def generate_auth_code():
        """Generate a secure one-time authorization code"""
        return secrets.token_urlsafe(48)
    
    @property
    def is_expired(self):
        """Check if this transaction has expired"""
        return timezone.now() > self.expires_at
    
    def can_be_confirmed(self):
        """Check if this transaction can be confirmed"""
        return self.status == 'PENDING' and not self.is_expired
    
    def __str__(self):
        return f"{self.transaction_id} - {self.user.username} - {self.status}"


class NotificationLog(models.Model):
    """
    Log of push notifications sent to users
    """
    NOTIFICATION_TYPE_CHOICES = [
        ('AUTH_REQUEST', 'Authentication Request'),
        ('AUTH_SUCCESS', 'Authentication Success'),
        ('AUTH_FAILED', 'Authentication Failed'),
        ('AUTH_EXPIRED', 'Authentication Expired'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
    ]
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    transaction = models.ForeignKey(
        AuthTransaction,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES,
        db_index=True
    )
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'auth_transactions_notificationlog'
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'
        indexes = [
            models.Index(
                fields=['user', '-created_at'],
                name='idx_notif_user'
            ),
            models.Index(
                fields=['transaction', '-created_at'],
                name='idx_notif_tx'
            ),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} to {self.user.username} at {self.created_at}"
