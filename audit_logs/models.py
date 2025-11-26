"""
AuditLog model - Security and compliance logging
"""
from django.db import models


class AuditLog(models.Model):
    """
    Comprehensive audit logging for security and compliance
    Records all important actions in the system
    """
    ACTION_CHOICES = [
        ('USER_LOGIN', 'User Login'),
        ('USER_LOGOUT', 'User Logout'),
        ('LOGIN_FAILED', 'Login Failed'),
        ('AUTH_REQUEST', 'Authentication Request'),
        ('AUTH_COMPLETED', 'Authentication Completed'),
        ('AUTH_FAILED', 'Authentication Failed'),
        ('AUTH_EXPIRED', 'Authentication Expired'),
        ('AUTH_STATUS_CHANGE', 'Authentication Status Change'),
        ('USER_INFO_UPDATE', 'User Information Update'),
        ('CI_DI_ACCESS', 'CI/DI Data Access'),
        ('ADMIN_ACTION', 'Administrator Action'),
        ('SERVICE_PROVIDER_CREATE', 'Service Provider Created'),
        ('SERVICE_PROVIDER_UPDATE', 'Service Provider Updated'),
        ('ROLE_ASSIGNMENT', 'Role Assignment'),
    ]
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='audit_logs',
        null=True,
        blank=True,
        help_text="User who performed the action (null for system actions)"
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        db_index=True,
        help_text="Type of action performed"
    )
    details = models.TextField(
        help_text="Detailed description of the action"
    )
    ip_address = models.GenericIPAddressField(
        help_text="IP address of the client"
    )
    user_agent = models.CharField(
        max_length=255,
        blank=True,
        help_text="User agent string of the client"
    )
    request_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="API endpoint or page accessed"
    )
    request_method = models.CharField(
        max_length=10,
        blank=True,
        help_text="HTTP method (GET, POST, etc.)"
    )
    status_code = models.IntegerField(
        null=True,
        blank=True,
        help_text="HTTP status code of the response"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the action occurred"
    )
    
    class Meta:
        db_table = 'audit_logs_auditlog'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        indexes = [
            models.Index(
                fields=['user', '-timestamp'],
                name='idx_audit_user_time'
            ),
            models.Index(
                fields=['action', '-timestamp'],
                name='idx_audit_action_time'
            ),
            models.Index(
                fields=['-timestamp'],
                name='idx_audit_timestamp'
            ),
            models.Index(
                fields=['ip_address', '-timestamp'],
                name='idx_audit_ip'
            ),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        user_str = self.user.username if self.user else 'System'
        return f"{self.action} by {user_str} at {self.timestamp}"
