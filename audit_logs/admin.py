"""
Admin configuration for audit_logs app
"""
from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """AuditLog admin configuration (Read-only)"""
    
    list_display = (
        'timestamp',
        'user',
        'action',
        'ip_address',
        'request_method',
        'status_code'
    )
    list_filter = ('action', 'timestamp', 'request_method', 'status_code')
    search_fields = (
        'user__username',
        'action',
        'details',
        'ip_address',
        'request_path'
    )
    readonly_fields = (
        'user',
        'action',
        'details',
        'ip_address',
        'user_agent',
        'request_path',
        'request_method',
        'status_code',
        'timestamp'
    )
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    
    fieldsets = (
        ('Action Information', {
            'fields': ('user', 'action', 'details')
        }),
        ('Request Details', {
            'fields': (
                'request_method',
                'request_path',
                'status_code',
                'ip_address',
                'user_agent'
            )
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )
    
    def has_add_permission(self, request):
        """Audit logs are created automatically"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Audit logs should never be deleted (compliance requirement)"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Audit logs should never be modified (integrity requirement)"""
        return False

