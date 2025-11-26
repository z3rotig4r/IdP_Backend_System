"""
Admin configuration for services app
"""
from django.contrib import admin
from .models import ServiceProvider, EncryptionKey, ServiceProviderStatistics


@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    """ServiceProvider admin configuration"""
    
    list_display = ('service_name', 'client_id', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('service_name', 'client_id')
    readonly_fields = ('client_id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('service_name', 'client_id', 'client_secret', 'is_active')
        }),
        ('Configuration', {
            'fields': ('callback_url', 'encryption_algorithm')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Auto-generate client_id if not provided"""
        if not change:  # Creating new service provider
            if not obj.client_id:
                obj.client_id = ServiceProvider.generate_client_id()
            # If client_secret is set but not hashed, hash it
            if 'client_secret' in form.changed_data:
                raw_secret = form.cleaned_data['client_secret']
                obj.client_secret = ServiceProvider.hash_secret(raw_secret)
        super().save_model(request, obj, form, change)


@admin.register(EncryptionKey)
class EncryptionKeyAdmin(admin.ModelAdmin):
    """EncryptionKey admin configuration"""
    
    list_display = ('service_provider', 'key_name', 'algorithm', 'is_active', 'created_at', 'expires_at')
    list_filter = ('is_active', 'algorithm', 'created_at')
    search_fields = ('service_provider__service_name', 'key_name')
    readonly_fields = ('created_at',)
    autocomplete_fields = ['service_provider']
    
    fieldsets = (
        (None, {
            'fields': ('service_provider', 'key_name', 'key_value', 'algorithm', 'is_active')
        }),
        ('Expiration', {
            'fields': ('created_at', 'expires_at')
        }),
    )


@admin.register(ServiceProviderStatistics)
class ServiceProviderStatisticsAdmin(admin.ModelAdmin):
    """ServiceProviderStatistics admin configuration (Read-only)"""
    
    list_display = (
        'service_provider', 
        'date', 
        'total_requests', 
        'success_rate', 
        'avg_processing_time'
    )
    list_filter = ('date', 'service_provider')
    search_fields = ('service_provider__service_name',)
    readonly_fields = (
        'service_provider', 
        'date', 
        'total_requests', 
        'completed_requests',
        'failed_requests', 
        'expired_requests', 
        'success_rate', 
        'avg_processing_time',
        'created_at', 
        'updated_at'
    )
    
    def has_add_permission(self, request):
        """Statistics are generated automatically, not manually created"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of statistics"""
        return False

