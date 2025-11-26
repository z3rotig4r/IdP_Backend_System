"""
Admin configuration for auth_transactions app
"""
from django.contrib import admin
from .models import AuthTransaction, NotificationLog


@admin.register(AuthTransaction)
class AuthTransactionAdmin(admin.ModelAdmin):
    """AuthTransaction admin configuration"""
    
    list_display = (
        'transaction_id', 
        'user', 
        'service_provider', 
        'status', 
        'created_at', 
        'expires_at'
    )
    list_filter = ('status', 'created_at', 'service_provider')
    search_fields = (
        'transaction_id', 
        'user__username', 
        'user__phone_number',
        'service_provider__service_name'
    )
    readonly_fields = (
        'transaction_id', 
        'created_at', 
        'updated_at', 
        'auth_code'
    )
    autocomplete_fields = ['user', 'service_provider']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('transaction_id', 'user', 'service_provider', 'status')
        }),
        ('Timing', {
            'fields': ('created_at', 'updated_at', 'expires_at')
        }),
        ('Result', {
            'fields': ('auth_code', 'failure_reason'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Transactions are created via API, not manually"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Preserve transaction history"""
        return request.user.is_superuser


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    """NotificationLog admin configuration"""
    
    list_display = (
        'user',
        'notification_type',
        'status',
        'sent_at',
        'created_at'
    )
    list_filter = ('notification_type', 'status', 'created_at')
    search_fields = ('user__username', 'user__phone_number', 'message')
    readonly_fields = ('created_at', 'sent_at')
    autocomplete_fields = ['user', 'transaction']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('user', 'transaction', 'notification_type', 'message')
        }),
        ('Status', {
            'fields': ('status', 'sent_at', 'created_at')
        }),
    )
    
    def has_add_permission(self, request):
        """Notifications are created automatically"""
        return False

