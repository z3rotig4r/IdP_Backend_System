"""
Admin configuration for accounts app
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserRole, UserRoleAssignment


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin with additional fields"""
    
    list_display = ('username', 'phone_number', 'email', 'is_staff', 'is_active', 'created_at')
    list_filter = ('is_staff', 'is_active', 'created_at')
    search_fields = ('username', 'phone_number', 'email')
    ordering = ('-created_at',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('IdP Information', {
            'fields': ('phone_number', 'pin_code', 'ci', 'di')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'ci', 'di')
    
    def get_readonly_fields(self, request, obj=None):
        """Make CI/DI read-only for security"""
        if obj:  # Editing an existing object
            return self.readonly_fields + ('phone_number',)
        return self.readonly_fields


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """UserRole admin configuration"""
    
    list_display = ('role_name', 'description', 'created_at')
    search_fields = ('role_name', 'description')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('role_name', 'description', 'permissions')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserRoleAssignment)
class UserRoleAssignmentAdmin(admin.ModelAdmin):
    """UserRoleAssignment admin configuration"""
    
    list_display = ('user', 'role', 'assigned_at', 'assigned_by')
    list_filter = ('role', 'assigned_at')
    search_fields = ('user__username', 'role__role_name')
    readonly_fields = ('assigned_at',)
    autocomplete_fields = ['user', 'assigned_by']
    
    def save_model(self, request, obj, form, change):
        """Automatically set assigned_by to current user"""
        if not change:  # Creating new assignment
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)

