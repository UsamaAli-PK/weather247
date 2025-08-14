"""
URL patterns for system monitoring endpoints
"""
from django.urls import path
from . import system_monitoring_views

app_name = 'system_monitoring'

urlpatterns = [
    # System status and overview
    path('status/', system_monitoring_views.system_status, name='system_status'),
    path('diagnostics/', system_monitoring_views.system_diagnostics_view, name='system_diagnostics'),
    path('real-time/', system_monitoring_views.real_time_monitoring, name='real_time_monitoring'),
    
    # Metrics endpoints
    path('metrics/', system_monitoring_views.system_metrics, name='system_metrics'),
    path('trends/', system_monitoring_views.performance_trends, name='performance_trends'),
    
    # Alerts endpoints
    path('alerts/', system_monitoring_views.system_alerts, name='system_alerts'),
    path('alerts/summary/', system_monitoring_views.alert_summary, name='alert_summary'),
    path('alerts/<int:alert_id>/acknowledge/', system_monitoring_views.acknowledge_alert, name='acknowledge_alert'),
    path('alerts/<int:alert_id>/resolve/', system_monitoring_views.resolve_alert, name='resolve_alert'),
    path('alerts/test/', system_monitoring_views.create_test_alert, name='create_test_alert'),
    
    # Health checks endpoints
    path('health/', system_monitoring_views.health_checks, name='health_checks'),
    path('health/run/', system_monitoring_views.run_health_checks, name='run_health_checks'),
    
    # Maintenance endpoints
    path('cleanup/', system_monitoring_views.cleanup_old_data, name='cleanup_old_data'),
]