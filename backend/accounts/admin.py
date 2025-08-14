from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count, Q
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from datetime import timedelta
import csv

from .models import (
    User, UserRole, UserProfile, UserActivity, 
    UserAPIUsage, UserSession
)


class UserProfileInline(admin.StackedInline):
    """Inline admin for user profiles"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    
    fieldsets = (
        ('Dashboard Preferences', {
            'fields': ('dashboard_layout', 'favorite_cities', 'default_city')
        }),
        ('Notification Settings', {
            'fields': ('email_notifications', 'sms_notifications', 'push_notifications')
        }),
        ('Weather Preferences', {
            'fields': ('show_air_quality', 'show_forecasts', 'forecast_days')
        }),
        ('Privacy', {
            'fields': ('profile_visibility',)
        }),
    )


class UserActivityInline(admin.TabularInline):
    """Inline admin for recent user activities"""
    model = UserActivity
    extra = 0
    max_num = 10
    readonly_fields = ('activity_type', 'description', 'ip_address', 'timestamp')
    can_delete = False
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-timestamp')[:10]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Enhanced user admin with comprehensive management features"""
    
    list_display = (
        'email', 'get_full_name', 'is_active', 'is_staff', 'is_verified',
        'last_activity_display', 'login_count', 'api_usage_today', 'date_joined'
    )
    list_filter = (
        'is_active', 'is_staff', 'is_superuser', 'is_verified',
        'preferred_units', 'date_joined', 'last_login'
    )
    search_fields = ('email', 'first_name', 'last_name', 'username')
    ordering = ('-date_joined',)
    
    readonly_fields = (
        'date_joined', 'last_login', 'last_activity', 'login_count',
        'api_requests_count', 'verification_token'
    )
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'phone_number', 'bio', 'location', 'timezone')
        }),
        ('Preferences', {
            'fields': ('preferred_units', 'language')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Account Status', {
            'fields': ('is_verified', 'verification_token')
        }),
        ('API Access', {
            'fields': ('api_key', 'api_requests_count', 'api_rate_limit')
        }),
        ('Activity Tracking', {
            'fields': ('last_login', 'last_activity', 'login_count', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )
    
    inlines = [UserProfileInline, UserActivityInline]
    
    actions = [
        'activate_users', 'deactivate_users', 'verify_users', 'unverify_users',
        'reset_api_usage', 'export_users_csv', 'send_bulk_notification'
    ]
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    
    def last_activity_display(self, obj):
        if not obj.last_activity:
            return format_html('<span style="color: gray;">Never</span>')
        
        time_diff = timezone.now() - obj.last_activity
        if time_diff.total_seconds() < 3600:  # Less than 1 hour
            color = 'green'
            text = f'{int(time_diff.total_seconds() / 60)}m ago'
        elif time_diff.total_seconds() < 86400:  # Less than 24 hours
            color = 'orange'
            text = f'{int(time_diff.total_seconds() / 3600)}h ago'
        else:
            color = 'red'
            text = f'{int(time_diff.total_seconds() / 86400)}d ago'
        
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            text
        )
    last_activity_display.short_description = 'Last Activity'
    
    def api_usage_today(self, obj):
        usage = obj.get_api_usage_today()
        limit = obj.api_rate_limit
        percentage = (usage / limit * 100) if limit > 0 else 0
        
        if percentage < 50:
            color = 'green'
        elif percentage < 80:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {};">{} / {} ({}%)</span>',
            color,
            usage,
            limit,
            int(percentage)
        )
    api_usage_today.short_description = 'API Usage Today'
    
    # Bulk Actions
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users activated.')
    activate_users.short_description = 'Activate selected users'
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated.')
    deactivate_users.short_description = 'Deactivate selected users'
    
    def verify_users(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} users verified.')
    verify_users.short_description = 'Verify selected users'
    
    def unverify_users(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} users unverified.')
    unverify_users.short_description = 'Unverify selected users'
    
    def reset_api_usage(self, request, queryset):
        updated = queryset.update(api_requests_count=0)
        self.message_user(request, f'API usage reset for {updated} users.')
    reset_api_usage.short_description = 'Reset API usage counter'
    
    def export_users_csv(self, request, queryset):
        """Export selected users to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Email', 'Full Name', 'Active', 'Verified', 'Staff', 'Date Joined',
            'Last Login', 'Last Activity', 'Login Count', 'API Usage Today'
        ])
        
        for user in queryset:
            writer.writerow([
                user.email,
                user.get_full_name(),
                user.is_active,
                user.is_verified,
                user.is_staff,
                user.date_joined.strftime('%Y-%m-%d %H:%M'),
                user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never',
                user.last_activity.strftime('%Y-%m-%d %H:%M') if user.last_activity else 'Never',
                user.login_count,
                user.get_api_usage_today()
            ])
        
        return response
    export_users_csv.short_description = 'Export selected users to CSV'
    
    def send_bulk_notification(self, request, queryset):
        """Send bulk notification to selected users"""
        # This would integrate with a notification system
        count = queryset.count()
        self.message_user(
            request, 
            f'Bulk notification queued for {count} users. (Feature requires notification system setup)'
        )
    send_bulk_notification.short_description = 'Send bulk notification'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('user-analytics/', self.admin_site.admin_view(self.user_analytics_view), name='user_analytics'),
            path('bulk-operations/', self.admin_site.admin_view(self.bulk_operations_view), name='bulk_operations'),
        ]
        return custom_urls + urls
    
    def user_analytics_view(self, request):
        """User analytics dashboard"""
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        
        analytics = {
            'total_users': User.objects.count(),
            'active_users_24h': User.objects.filter(last_activity__gte=last_24h).count(),
            'active_users_7d': User.objects.filter(last_activity__gte=last_7d).count(),
            'new_users_7d': User.objects.filter(date_joined__gte=last_7d).count(),
            'verified_users': User.objects.filter(is_verified=True).count(),
            'staff_users': User.objects.filter(is_staff=True).count(),
        }
        
        context = {
            'title': 'User Analytics',
            'analytics': analytics,
            'has_permission': True,
        }
        return render(request, 'admin/user_analytics.html', context)
    
    def bulk_operations_view(self, request):
        """Bulk operations interface"""
        if request.method == 'POST':
            operation = request.POST.get('operation')
            user_ids = request.POST.getlist('user_ids')
            
            if not user_ids:
                messages.error(request, 'No users selected.')
                return redirect('admin:bulk_operations')
            
            users = User.objects.filter(id__in=user_ids)
            
            if operation == 'activate':
                users.update(is_active=True)
                messages.success(request, f'{users.count()} users activated.')
            elif operation == 'deactivate':
                users.update(is_active=False)
                messages.success(request, f'{users.count()} users deactivated.')
            elif operation == 'verify':
                users.update(is_verified=True)
                messages.success(request, f'{users.count()} users verified.')
            
            return redirect('admin:bulk_operations')
        
        users = User.objects.all().order_by('-date_joined')
        context = {
            'title': 'Bulk User Operations',
            'users': users,
            'has_permission': True,
        }
        return render(request, 'admin/bulk_operations.html', context)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """Admin for custom user roles"""
    list_display = ('name', 'description', 'is_active', 'permission_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    filter_horizontal = ('permissions',)
    
    def permission_count(self, obj):
        return obj.permissions.count()
    permission_count.short_description = 'Permissions'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for user profiles"""
    list_display = ('user', 'default_city', 'email_notifications', 'profile_visibility', 'updated_at')
    list_filter = ('email_notifications', 'sms_notifications', 'push_notifications', 'profile_visibility')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'default_city')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Dashboard Preferences', {
            'fields': ('dashboard_layout', 'favorite_cities', 'default_city')
        }),
        ('Notification Settings', {
            'fields': ('email_notifications', 'sms_notifications', 'push_notifications')
        }),
        ('Weather Preferences', {
            'fields': ('show_air_quality', 'show_forecasts', 'forecast_days')
        }),
        ('Privacy', {
            'fields': ('profile_visibility',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """Admin for user activities"""
    list_display = ('user', 'activity_type', 'description', 'ip_address', 'timestamp')
    list_filter = ('activity_type', 'timestamp')
    search_fields = ('user__email', 'activity_type', 'description', 'ip_address')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(UserAPIUsage)
class UserAPIUsageAdmin(admin.ModelAdmin):
    """Admin for API usage tracking"""
    list_display = ('user', 'endpoint', 'date', 'request_count', 'success_count', 'error_count', 'success_rate')
    list_filter = ('date', 'endpoint')
    search_fields = ('user__email', 'endpoint')
    date_hierarchy = 'date'
    
    def success_rate(self, obj):
        if obj.request_count == 0:
            return '0%'
        rate = (obj.success_count / obj.request_count) * 100
        color = 'green' if rate >= 95 else 'orange' if rate >= 80 else 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color,
            rate
        )
    success_rate.short_description = 'Success Rate'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """Admin for user sessions"""
    list_display = ('user', 'session_key_short', 'ip_address', 'location', 'is_active', 'created_at', 'last_activity')
    list_filter = ('is_active', 'created_at', 'last_activity')
    search_fields = ('user__email', 'ip_address', 'location', 'session_key')
    readonly_fields = ('session_key', 'created_at', 'last_activity')
    
    def session_key_short(self, obj):
        return f"{obj.session_key[:8]}..."
    session_key_short.short_description = 'Session Key'
    
    actions = ['terminate_sessions']
    
    def terminate_sessions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} sessions terminated.')
    terminate_sessions.short_description = 'Terminate selected sessions'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
