from django.urls import path, include
from . import views

urlpatterns = [
    # City management
    path('cities/', views.CityListCreateView.as_view(), name='city-list'),
    path('cities/<int:pk>/', views.CityDetailView.as_view(), name='city-detail'),
    
    # Weather data
    path('current/<int:city_id>/', views.get_current_weather, name='current-weather'),
    path('current/', views.get_weather_by_city_name, name='weather-by-name'),
    path('forecast/<int:city_id>/', views.get_forecast, name='weather-forecast'),
    path('air-quality/<int:city_id>/', views.get_air_quality, name='air-quality'),
    path('multiple/', views.get_multiple_cities_weather, name='multiple-cities'),
    path('refresh/', views.refresh_weather_data, name='refresh-weather'),
    
    # AI and Analytics endpoints
    path('ai-predictions/', views.get_ai_predictions, name='ai-predictions'),
    path('historical/', views.get_historical_data, name='historical-data'),
    path('compare/', views.compare_cities, name='compare-cities'),
    
    # Enhanced features
    path('analytics/', views.get_weather_analytics, name='weather-analytics'),
    path('alerts/trigger/', views.trigger_weather_alerts, name='trigger-alerts'),
    path('map-data/', views.get_weather_map_data, name='weather-map-data'),
    
    # City management features
    path('cities/search/', views.search_cities, name='search-cities'),
    path('cities/add/', views.add_city, name='add-city'),
    
    # Cache management
    path('cache/stats/', views.get_cache_stats, name='cache-stats'),
    path('cache/clear/', views.clear_cache, name='clear-cache'),
    
    # System health
    path('health/', views.system_health, name='system-health'),
    
    # Background tasks
    path('scheduler/start/', views.start_background_refresh, name='start-scheduler'),
    path('scheduler/stop/', views.stop_background_refresh, name='stop-scheduler'),
    path('scheduler/status/', views.get_scheduler_status, name='scheduler-status'),
    
    # Task monitoring and management
    path('monitoring/dashboard/', views.task_monitoring_dashboard, name='task-monitoring'),
    path('monitoring/refresh/', views.trigger_weather_refresh, name='trigger-refresh'),
    path('monitoring/task/<str:task_id>/', views.task_status, name='task-status'),
    path('monitoring/quota/', views.api_quota_status, name='api-quota'),
    path('monitoring/health/', views.system_health, name='system-health'),
    
    # Analytics and monitoring
    path('analytics/dashboard/', views.analytics_dashboard, name='analytics-dashboard'),
    path('analytics/api-usage/', views.api_usage_analytics, name='api-usage-analytics'),
    path('analytics/cache/', views.cache_analytics, name='cache-analytics'),
    path('analytics/freshness/', views.data_freshness_monitor, name='data-freshness'),
    path('analytics/trends/', views.weather_trends_analytics, name='weather-trends'),
    path('analytics/health-report/', views.system_health_report, name='health-report'),
    path('analytics/health-check/', views.trigger_health_check, name='trigger-health-check'),
    
    # Performance optimization
    path('performance/metrics/', views.performance_metrics, name='performance-metrics'),
    path('performance/analysis/', views.performance_analysis, name='performance-analysis'),
    path('performance/optimize-cache/', views.optimize_cache, name='optimize-cache'),
    path('performance/weather-data/', views.optimized_weather_data, name='optimized-weather-data'),
    path('performance/cities/', views.optimized_cities_list, name='optimized-cities'),
    path('performance/bulk-update/', views.bulk_weather_update, name='bulk-weather-update'),
    
    # API Integration Management
    path('api/providers/', views.api_providers_list, name='api-providers-list'),
    path('api/providers/create/', views.api_provider_create, name='api-provider-create'),
    path('api/providers/<int:provider_id>/', views.api_provider_detail, name='api-provider-detail'),
    path('api/providers/<int:provider_id>/health/', views.api_provider_health_check, name='api-provider-health'),
    path('api/providers/<int:provider_id>/test/', views.api_provider_test, name='api-provider-test'),
    path('api/providers/<int:provider_id>/delete/', views.api_provider_delete, name='api-provider-delete'),
    path('api/usage/', views.api_usage_analytics, name='api-usage-analytics'),
    path('api/failovers/', views.api_failover_events, name='api-failover-events'),
    path('api/failovers/<int:failover_id>/resolve/', views.api_failover_resolve, name='api-failover-resolve'),
    path('api/dashboard/', views.api_dashboard_summary, name='api-dashboard-summary'),
    path('api/cost-analysis/', views.api_cost_analysis, name='api-cost-analysis'),
    path('api/system-health/', views.api_system_health, name='api-system-health'),
    
    # Real-time API Monitoring
    path('api/real-time-status/', views.api_real_time_status, name='api-real-time-status'),
    path('api/latest-alerts/', views.api_latest_alerts, name='api-latest-alerts'),
    path('api/start-monitoring/', views.api_start_monitoring, name='api-start-monitoring'),
    path('api/bulk-health-check/', views.api_bulk_health_check, name='api-bulk-health-check'),
    
    # Push Notifications
    path('push-subscription/', views.PushSubscriptionView.as_view(), name='push-subscription'),
    path('push-subscription/verify/', views.verify_subscription, name='push-subscription-verify'),
    path('push-subscription/preferences/', views.update_preferences, name='push-subscription-preferences'),
    path('push-subscription/test/', views.send_test_notification, name='push-subscription-test'),
    path('push-subscription/status/', views.subscription_status, name='push-subscription-status'),
    path('push-notifications/weather-alert/', views.send_weather_alert, name='push-weather-alert'),
    path('push-notifications/daily-forecast/', views.send_daily_forecast, name='push-daily-forecast'),
    path('push-notifications/stats/', views.subscription_stats, name='push-subscription-stats'),
    path('push-notifications/cleanup/', views.cleanup_subscriptions, name='push-cleanup-subscriptions'),
    
    # Alerts API
    path('alerts/rules/', views.alert_rules, name='alert-rules'),
    path('alerts/rules/<int:rule_id>/', views.alert_rule_detail, name='alert-rule-detail'),
    path('alerts/recent/', views.user_alerts, name='user-alerts'),
    
    # System Monitoring
    path('monitoring/', include('weather_data.system_monitoring_urls')),
]

