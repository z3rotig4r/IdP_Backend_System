"""
ServiceProvider and related models for IdP Backend System
"""
from django.db import models
from django.core.validators import URLValidator
import secrets
import hashlib


class ServiceProvider(models.Model):
    """
    Service Provider (이용기관) - external services that request authentication
    """
    service_name = models.CharField(
        max_length=200,
        help_text="Name of the service (e.g., 'A Shopping Mall')"
    )
    client_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Public identifier for the service"
    )
    client_secret = models.CharField(
        max_length=255,
        help_text="Hashed secret key for authentication"
    )
    callback_url = models.URLField(
        max_length=500,
        validators=[URLValidator()],
        help_text="URL to receive authentication results"
    )
    encryption_algorithm = models.CharField(
        max_length=50,
        default='AES-256-GCM',
        help_text="Encryption algorithm for data transmission"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this service provider is currently active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'services_serviceprovider'
        verbose_name = 'Service Provider'
        verbose_name_plural = 'Service Providers'
        indexes = [
            models.Index(fields=['client_id'], name='idx_sp_client_id'),
            models.Index(fields=['is_active', '-created_at'], name='idx_sp_active'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(is_active__in=[True, False]),
                name='chk_sp_active'
            ),
        ]
    
    @staticmethod
    def generate_client_id():
        """Generate a unique client ID"""
        return 'sp_' + secrets.token_urlsafe(32)[:32]
    
    @staticmethod
    def generate_client_secret():
        """Generate a client secret"""
        return secrets.token_urlsafe(64)
    
    @staticmethod
    def hash_secret(raw_secret):
        """Hash the client secret"""
        return hashlib.sha256(raw_secret.encode()).hexdigest()
    
    def check_secret(self, raw_secret):
        """Verify client secret"""
        return self.client_secret == self.hash_secret(raw_secret)
    
    def __str__(self):
        return f"{self.service_name} ({self.client_id})"


class EncryptionKey(models.Model):
    """
    Encryption keys for each service provider (Weak Entity)
    Dependent on ServiceProvider - deleted when parent is deleted
    """
    service_provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name='encryption_keys'
    )
    key_name = models.CharField(
        max_length=100,
        help_text="Identifier for this key"
    )
    key_value = models.TextField(
        help_text="Encrypted key value"
    )
    algorithm = models.CharField(
        max_length=50,
        default='AES-256-GCM'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Key expiration date (optional)"
    )
    
    class Meta:
        db_table = 'services_encryptionkey'
        verbose_name = 'Encryption Key'
        verbose_name_plural = 'Encryption Keys'
        unique_together = ('service_provider', 'key_name')
        indexes = [
            models.Index(
                fields=['service_provider', 'is_active'],
                name='idx_key_sp_active'
            ),
        ]
    
    def __str__(self):
        return f"{self.service_provider.service_name} - {self.key_name}"


class ServiceProviderStatistics(models.Model):
    """
    Daily statistics for each service provider
    """
    service_provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name='statistics'
    )
    date = models.DateField(db_index=True)
    total_requests = models.IntegerField(default=0)
    completed_requests = models.IntegerField(default=0)
    failed_requests = models.IntegerField(default=0)
    expired_requests = models.IntegerField(default=0)
    success_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        help_text="Success rate in percentage"
    )
    avg_processing_time = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.0,
        help_text="Average processing time in seconds"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'services_serviceproviderstatistics'
        verbose_name = 'Service Provider Statistics'
        verbose_name_plural = 'Service Provider Statistics'
        unique_together = ('service_provider', 'date')
        indexes = [
            models.Index(
                fields=['service_provider', '-date'],
                name='idx_stats_sp_date'
            ),
        ]
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.service_provider.service_name} - {self.date}"
