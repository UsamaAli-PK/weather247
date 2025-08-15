from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import path, reverse
from django.shortcuts import render
from django.http import JsonResponse
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count, Avg, Max, Min
from datetime import timedelta
import json

from .models import City, WeatherData, AirQualityData, WeatherForecast
from accounts.models import User
from .models import AlertRule, WeatherAlert


class Weather247AdminSite(AdminSite):
    """Custom admin site with enhanced features"""
    site_header = 'Weather247 Administration'
    site_title = 'Weather247 Admin'
    index_title = 'System Dashboard'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
            path('system-metrics/', self.admin_view(self.system_metrics_view), name='system_metrics'),
            path('api-management/', self.admin_view(self.api_management_view), name='api_management'),
            path('cost-analysis/', self.admin_view(self.cost_analysis_view), name='cost_analysis'),
            path('api/metrics/', self.admin_view(self.metrics_api), name='metrics_api'),
            path('api/api-stats/', self.admin_view(self.api_stats_api), name='api_stats_api'),
            path('api/cost-analysis/', self.admin_view(self.cost_analysis_api), name='cost_analysis_api'),
            path('api/health-check/<int:provider_id>/', self.admin_view(self.health_check_api), name='health_check_api'),
            path('api/real-time-status/', self.admin_view(self.real_time_status_api), name='real_time_status_api'),
            path('api/latest-alerts/', self.admin_view(self.latest_alerts_api), name='latest_alerts_api'),
            path('api/bulk-health-check/', self.admin_view(self.bulk_health_check_api), name='bulk_health_check_api'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        """Enhanced dashboard with system metrics"""
        context = {
            'title': 'System Dashboard',
            'has_permission': True,
        }
        return render(request, 'admin/dashboard.html', context)
    
    def system_metrics_view(self, request):
        """System metrics page"""
        context = {
            'title': 'System Metrics',
            'has_permission': True,
        }
        return render(request, 'admin/system_metrics.html', context)
    
    def api_management_view(self, request):
        """API management dashboard"""
        context = {
            'title': 'API Integration Management',
            'has_permission': True,
        }
        return render(request, 'admin/api_management.html', context)
    
    def cost_analysis_view(self, request):
        """Cost analysis dashboard"""
        context = {
            'title': 'API Cost Analysis',
            'has_permission': True,
        }
        return render(request, 'admin/cost_analysis.html', context)
    
    def metrics_api(self, request):
        """API endpoint for dashboard metrics"""
        try:
            now = timezone.now()
            last_24h = now - timedelta(hours=24)
            last_7d = now - timedelta(days=7)
            
            # Basic statistics
            metrics = {
                'users': {
                    'total': User.objects.count(),
                    'active_24h': User.objects.filter(last_login__gte=last_24h).count(),
                    'new_7d': User.objects.filter(date_joined__gte=last_7d).count(),
                },
                'cities': {
                    'total': City.objects.count(),
                    'active': City.objects.filter(is_active=True).count(),
                },
                'weather_data': {
                    'total': WeatherData.objects.count(),
                    'last_24h': WeatherData.objects.filter(timestamp__gte=last_24h).count(),
                    'avg_temp_24h': WeatherData.objects.filter(
                        timestamp__gte=last_24h
                    ).aggregate(Avg('temperature'))['temperature__avg'] or 0,
                },
                'air_quality': {
                    'total': AirQualityData.objects.count(),
                    'last_24h': AirQualityData.objects.filter(timestamp__gte=last_24h).count(),
                },
                'forecasts': {
                    'total': WeatherForecast.objects.count(),
                    'active': WeatherForecast.objects.filter(
                        forecast_date__gte=now.date()
                    ).count(),
                }
            }
            
            # Top cities by data volume
            top_cities = WeatherData.objects.values('city__name', 'city__country').annotate(
                data_count=Count('id')
            ).order_by('-data_count')[:10]
            
            metrics['top_cities'] = list(top_cities)
            
            # Recent activity
            recent_weather = WeatherData.objects.select_related('city').order_by('-timestamp')[:10]
            metrics['recent_activity'] = [
                {
                    'city': f"{w.city.name}, {w.city.country}",
                    'temperature': w.temperature,
                    'condition': w.weather_condition,
                    'timestamp': w.timestamp.isoformat()
                }
                for w in recent_weather
            ]
            
            # Add API management metrics
            try:
                from .api_management import APIProvider, APIUsage, APIFailover
                
                # API provider metrics
                providers = APIProvider.objects.all()
                active_providers = providers.filter(is_active=True).count()
                healthy_providers = providers.filter(is_active=True, is_healthy=True).count()
                
                # Recent failovers
                recent_failovers = APIFailover.objects.filter(
                    failed_at__gte=last_24h
                ).count()
                
                # Today's API usage
                today = timezone.now().date()
                today_usage = APIUsage.objects.filter(date=today).aggregate(
                    total_requests=models.Sum('request_count'),
                    total_cost=models.Sum('cost'),
                    total_errors=models.Sum('error_count')
                )
                
                metrics['api_health'] = {
                    'total_providers': providers.count(),
                    'active_providers': active_providers,
                    'healthy_providers': healthy_providers,
                    'recent_failovers': recent_failovers
                }
                
                metrics['api_usage'] = {
                    'requests_today': today_usage['total_requests'] or 0,
                    'cost_today': float(today_usage['total_cost'] or 0),
                    'errors_today': today_usage['total_errors'] or 0
                }
                
            except Exception as e:
                # API management not available, skip these metrics
                metrics['api_health'] = {
                    'total_providers': 0,
                    'active_providers': 0,
                    'healthy_providers': 0,
                    'recent_failovers': 0
                }
                metrics['api_usage'] = {
                    'requests_today': 0,
                    'cost_today': 0.0,
                    'errors_today': 0
                }
            
            return JsonResponse(metrics)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def api_stats_api(self, request):
        """API endpoint for API provider statistics"""
        try:
            from .api_management import APIProvider, APIFailover, api_manager
            
            providers = APIProvider.objects.all()
            provider_stats = []
            
            for provider in providers:
                stats = api_manager.get_provider_statistics(provider.id, days=30)
                provider_stats.append(stats)
            
            # Overall API health
            active_providers = providers.filter(is_active=True).count()
            healthy_providers = providers.filter(is_active=True, is_healthy=True).count()
            
            # Recent failovers
            recent_failovers = APIFailover.objects.filter(
                failed_at__gte=timezone.now() - timedelta(days=7)
            ).count()
            
            return JsonResponse({
                'providers': provider_stats,
                'summary': {
                    'total_providers': providers.count(),
                    'active_providers': active_providers,
                    'healthy_providers': healthy_providers,
                    'health_percentage': (healthy_providers / max(active_providers, 1)) * 100,
                    'recent_failovers': recent_failovers
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def cost_analysis_api(self, request):
        """API endpoint for cost analysis"""
        try:
            from .api_management import api_manager
            
            days = int(request.GET.get('days', 30))
            cost_analysis = api_manager.get_cost_analysis(days)
            
            return JsonResponse(cost_analysis)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def health_check_api(self, request, provider_id):
        """API endpoint for performing health check on a provider"""
        try:
            from .api_management import APIProvider, api_manager
            
            provider = APIProvider.objects.get(id=provider_id)
            health_result = api_manager.perform_health_check(provider)
            
            return JsonResponse(health_result)
            
        except APIProvider.DoesNotExist:
            return JsonResponse({'error': 'Provider not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def real_time_status_api(self, request):
        """API endpoint for real-time provider status"""
        try:
            from .api_monitoring_realtime import real_time_monitor
            
            status_data = real_time_monitor.get_real_time_status()
            return JsonResponse(status_data)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def latest_alerts_api(self, request):
        """API endpoint for latest system alerts"""
        try:
            from .api_monitoring_realtime import real_time_monitor
            
            limit = int(request.GET.get('limit', 10))
            alerts = real_time_monitor.get_latest_alerts(limit)
            
            return JsonResponse({
                'alerts': alerts,
                'count': len(alerts),
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def bulk_health_check_api(self, request):
        """API endpoint for bulk health check"""
        try:
            from .api_management import APIProvider, api_manager
            
            providers = APIProvider.objects.filter(is_active=True)
            results = []
            
            for provider in providers:
                try:
                    health_result = api_manager.perform_health_check(provider)
                    results.append({
                        'provider': provider.name,
                        'display_name': provider.display_name,
                        'healthy': health_result['healthy'],
                        'response_time': health_result.get('response_time', 0),
                        'error': health_result.get('error')
                    })
                except Exception as e:
                    results.append({
                        'provider': provider.name,
                        'display_name': provider.display_name,
                        'healthy': False,
                        'error': str(e)
                    })
            
            return JsonResponse({
                'results': results,
                'total_checked': len(results),
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


# Create custom admin site instance
admin_site = Weather247AdminSite(name='weather247_admin')


@admin.register(City, site=admin_site)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'latitude', 'longitude', 'is_active', 'weather_data_count', 'last_update')
    list_filter = ('country', 'is_active')
    search_fields = ('name', 'country')
    list_editable = ('is_active',)
    readonly_fields = ('weather_data_count', 'last_update')
    
    def weather_data_count(self, obj):
        count = obj.weather_data.count()
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if count > 0 else 'red',
            count
        )
    weather_data_count.short_description = 'Weather Records'
    
    def last_update(self, obj):
        latest = obj.weather_data.order_by('-timestamp').first()
        if latest:
            time_diff = timezone.now() - latest.timestamp
            if time_diff.total_seconds() < 3600:  # Less than 1 hour
                color = 'green'
            elif time_diff.total_seconds() < 86400:  # Less than 24 hours
                color = 'orange'
            else:
                color = 'red'
            
            return format_html(
                '<span style="color: {};">{}</span>',
                color,
                latest.timestamp.strftime('%Y-%m-%d %H:%M')
            )
        return format_html('<span style="color: red;">No data</span>')
    last_update.short_description = 'Last Update'
    
    actions = ['activate_cities', 'deactivate_cities']
    
    def activate_cities(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} cities activated.')
    activate_cities.short_description = 'Activate selected cities'
    
    def deactivate_cities(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} cities deactivated.')
    deactivate_cities.short_description = 'Deactivate selected cities'


@admin.register(WeatherData, site=admin_site)
class WeatherDataAdmin(admin.ModelAdmin):
    list_display = ('city', 'temperature', 'humidity', 'pressure', 'weather_condition', 'timestamp', 'data_age')
    list_filter = ('weather_condition', 'timestamp', 'city__country')
    search_fields = ('city__name', 'weather_condition')
    date_hierarchy = 'timestamp'
    readonly_fields = ('data_age',)
    
    def data_age(self, obj):
        age = timezone.now() - obj.timestamp
        hours = age.total_seconds() / 3600
        
        if hours < 1:
            color = 'green'
            text = f'{int(age.total_seconds() / 60)} minutes ago'
        elif hours < 24:
            color = 'orange'
            text = f'{int(hours)} hours ago'
        else:
            color = 'red'
            text = f'{int(hours / 24)} days ago'
        
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            text
        )
    data_age.short_description = 'Data Age'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('city')


@admin.register(AirQualityData, site=admin_site)
class AirQualityDataAdmin(admin.ModelAdmin):
    list_display = ('city', 'aqi', 'pm2_5', 'pm10', 'co', 'no2', 'o3', 'so2', 'timestamp')
    list_filter = ('timestamp', 'city__country')
    search_fields = ('city__name',)
    date_hierarchy = 'timestamp'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('city')


@admin.register(WeatherForecast, site=admin_site)
class WeatherForecastAdmin(admin.ModelAdmin):
    list_display = ('city', 'forecast_date', 'temperature_min', 'temperature_max', 'weather_condition', 'created_at')
    list_filter = ('forecast_date', 'weather_condition', 'city__country')
    search_fields = ('city__name', 'weather_condition')
    date_hierarchy = 'forecast_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('city')


@admin.register(User, site=admin_site)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined', 'last_login')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    readonly_fields = ('date_joined', 'last_login')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    actions = ['activate_users', 'deactivate_users']
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users activated.')
    activate_users.short_description = 'Activate selected users'
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated.')
    deactivate_users.short_description = 'Deactivate selected users'


@admin.register(AlertRule, site=admin_site)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'city', 'name', 'severity', 'is_active', 'email_enabled', 'sms_enabled', 'push_enabled', 'updated_at'
    )
    list_filter = ('is_active', 'severity', 'email_enabled', 'sms_enabled', 'push_enabled')
    search_fields = ('user__email', 'city__name', 'name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(WeatherAlert, site=admin_site)
class WeatherAlertAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'city', 'alert_type', 'severity', 'is_emergency', 'is_read', 'created_at'
    )
    list_filter = ('alert_type', 'severity', 'is_emergency', 'is_read', 'created_at')
    search_fields = ('user__email', 'city__name', 'title', 'message')


# Register the default Django admin models with our custom site
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin

admin_site.register(Group, GroupAdmin)

# Import the API management models
from .api_management import APIProvider, APIUsage, APIFailover, api_manager


@admin.register(APIProvider, site=admin_site)
class APIProviderAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'name', 'is_active', 'is_healthy', 'priority', 'success_rate', 'usage_today', 'cost_today')
    list_filter = ('is_active', 'is_healthy', 'is_primary')
    search_fields = ('name', 'display_name')
    list_editable = ('is_active', 'priority')
    readonly_fields = ('success_rate', 'error_count', 'last_health_check', 'usage_today', 'cost_today')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'display_name', 'base_url', 'api_key')
        }),
        ('Status', {
            'fields': ('is_active', 'is_primary', 'is_healthy', 'priority')
        }),
        ('Rate Limits', {
            'fields': ('requests_per_minute', 'requests_per_day', 'requests_per_month')
        }),
        ('Cost Management', {
            'fields': ('cost_per_request', 'monthly_budget')
        }),
        ('Configuration', {
            'fields': ('supported_endpoints', 'configuration'),
            'classes': ('collapse',)
        }),
        ('Health Monitoring', {
            'fields': ('last_health_check', 'success_rate', 'error_count'),
            'classes': ('collapse',)
        }),
    )
    
    def usage_today(self, obj):
        usage = obj.get_usage_today()
        color = 'green' if usage < obj.requests_per_day * 0.8 else 'orange' if usage < obj.requests_per_day else 'red'
        return format_html(
            '<span style="color: {};">{} / {}</span>',
            color,
            usage,
            obj.requests_per_day
        )
    usage_today.short_description = 'Usage Today'
    
    def cost_today(self, obj):
        today = timezone.now().date()
        cost = APIUsage.objects.filter(
            provider=obj,
            date=today
        ).aggregate(total_cost=models.Sum('cost'))['total_cost'] or 0
        
        return f"${cost:.4f}"
    cost_today.short_description = 'Cost Today'
    
    actions = ['activate_providers', 'deactivate_providers', 'health_check']
    
    def activate_providers(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} providers activated.')
    activate_providers.short_description = 'Activate selected providers'
    
    def deactivate_providers(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} providers deactivated.')
    deactivate_providers.short_description = 'Deactivate selected providers'
    
    def health_check(self, request, queryset):
        checked = 0
        for provider in queryset:
            try:
                api_manager.perform_health_check(provider)
                checked += 1
            except Exception:
                pass
        self.message_user(request, f'Health check performed on {checked} providers.')
    health_check.short_description = 'Perform health check'


@admin.register(APIUsage, site=admin_site)
class APIUsageAdmin(admin.ModelAdmin):
    list_display = ('provider', 'endpoint', 'date', 'request_count', 'success_count', 'error_count', 'cost', 'avg_response_time')
    list_filter = ('date', 'provider', 'endpoint')
    search_fields = ('provider__name', 'endpoint')
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('provider')


@admin.register(APIFailover, site=admin_site)
class APIFailoverAdmin(admin.ModelAdmin):
    list_display = ('primary_provider', 'fallback_provider', 'endpoint', 'reason', 'failed_at', 'resolved_at', 'duration')
    list_filter = ('failed_at', 'primary_provider', 'fallback_provider')
    search_fields = ('primary_provider__name', 'fallback_provider__name', 'endpoint', 'reason')
    date_hierarchy = 'failed_at'
    readonly_fields = ('failed_at', 'duration')
    
    def duration(self, obj):
        if obj.resolved_at:
            duration = obj.resolved_at - obj.failed_at
            return f"{duration.total_seconds():.1f}s"
        return "Ongoing"
    duration.short_description = 'Duration'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('primary_provider', 'fallback_provider')