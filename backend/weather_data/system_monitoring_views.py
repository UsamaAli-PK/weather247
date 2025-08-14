"""
System monitoring API views
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from datetime import timedelta
import json

from .system_monitoring_core import system_monitor, system_diagnostics
from .models import SystemMetrics, SystemAlert, SystemHealthCheck


@api_view(['GET'])
@permission_classes([IsAdminUser])
def system_status(request):
    """Get current system status"""
    try:
        status_data = system_monitor.get_system_status()
        return Response(status_data)
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def system_metrics(request):
    """Get system metrics with optional filtering"""
    try:
        # Get query parameters
        metric_type = request.GET.get('type')
        component = request.GET.get('component')
        hours = int(request.GET.get('hours', 24))
        
        # Build query
        since = timezone.now() - timedelta(hours=hours)
        queryset = SystemMetrics.objects.filter(timestamp__gte=since)
        
        if metric_type:
            queryset = queryset.filter(metric_type=metric_type)
        if component:
            queryset = queryset.filter(component=component)
        
        # Get metrics
        metrics = queryset.order_by('-timestamp')[:1000]  # Limit to 1000 records
        
        metrics_data = []
        for metric in metrics:
            metrics_data.append({
                'id': metric.id,
                'type': metric.metric_type,
                'name': metric.metric_name,
                'value': metric.metric_value,
                'unit': metric.metric_unit,
                'component': metric.component,
                'timestamp': metric.timestamp.isoformat(),
                'metadata': metric.metadata
            })
        
        return Response({
            'metrics': metrics_data,
            'count': len(metrics_data),
            'filters': {
                'type': metric_type,
                'component': component,
                'hours': hours
            }
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def system_alerts(request):
    """Get system alerts with optional filtering"""
    try:
        # Get query parameters
        alert_status = request.GET.get('status', 'active')
        severity = request.GET.get('severity')
        component = request.GET.get('component')
        hours = int(request.GET.get('hours', 24))
        
        # Build query
        since = timezone.now() - timedelta(hours=hours)
        queryset = SystemAlert.objects.filter(created_at__gte=since)
        
        if alert_status != 'all':
            queryset = queryset.filter(status=alert_status)
        if severity:
            queryset = queryset.filter(severity=severity)
        if component:
            queryset = queryset.filter(component=component)
        
        # Get alerts
        alerts = queryset.order_by('-created_at')[:100]  # Limit to 100 records
        
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                'id': alert.id,
                'type': alert.alert_type,
                'severity': alert.severity,
                'status': alert.status,
                'title': alert.title,
                'message': alert.message,
                'component': alert.component,
                'metric_value': alert.metric_value,
                'threshold_value': alert.threshold_value,
                'created_at': alert.created_at.isoformat(),
                'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                'acknowledged_by': alert.acknowledged_by.username if alert.acknowledged_by else None,
                'resolved_by': alert.resolved_by.username if alert.resolved_by else None,
                'error_details': alert.error_details
            })
        
        return Response({
            'alerts': alerts_data,
            'count': len(alerts_data),
            'filters': {
                'status': alert_status,
                'severity': severity,
                'component': component,
                'hours': hours
            }
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def acknowledge_alert(request, alert_id):
    """Acknowledge a system alert"""
    try:
        alert = SystemAlert.objects.get(id=alert_id)
        alert.acknowledge(user=request.user)
        
        return Response({
            'message': 'Alert acknowledged successfully',
            'alert_id': alert_id,
            'acknowledged_by': request.user.username,
            'acknowledged_at': alert.acknowledged_at.isoformat()
        })
        
    except SystemAlert.DoesNotExist:
        return Response(
            {'error': 'Alert not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def resolve_alert(request, alert_id):
    """Resolve a system alert"""
    try:
        alert = SystemAlert.objects.get(id=alert_id)
        alert.resolve(user=request.user)
        
        return Response({
            'message': 'Alert resolved successfully',
            'alert_id': alert_id,
            'resolved_by': request.user.username,
            'resolved_at': alert.resolved_at.isoformat()
        })
        
    except SystemAlert.DoesNotExist:
        return Response(
            {'error': 'Alert not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def health_checks(request):
    """Get system health check results"""
    try:
        # Get query parameters
        check_type = request.GET.get('type')
        hours = int(request.GET.get('hours', 24))
        
        # Build query
        since = timezone.now() - timedelta(hours=hours)
        queryset = SystemHealthCheck.objects.filter(timestamp__gte=since)
        
        if check_type:
            queryset = queryset.filter(check_type=check_type)
        
        # Get health checks
        health_checks = queryset.order_by('-timestamp')[:100]
        
        health_data = []
        for check in health_checks:
            health_data.append({
                'id': check.id,
                'type': check.check_type,
                'name': check.check_name,
                'status': check.status,
                'response_time': check.response_time,
                'error_message': check.error_message,
                'details': check.details,
                'timestamp': check.timestamp.isoformat()
            })
        
        return Response({
            'health_checks': health_data,
            'count': len(health_data),
            'filters': {
                'type': check_type,
                'hours': hours
            }
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def run_health_checks(request):
    """Manually trigger health checks"""
    try:
        health_results = system_monitor.perform_health_checks()
        return Response({
            'message': 'Health checks completed',
            'results': health_results
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def system_diagnostics_view(request):
    """Run comprehensive system diagnostics"""
    try:
        diagnostic_results = system_diagnostics.run_full_diagnostic()
        return Response(diagnostic_results)
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def performance_trends(request):
    """Get performance trends data"""
    try:
        hours = int(request.GET.get('hours', 24))
        metric_types = request.GET.getlist('metrics', ['cpu_usage', 'memory_usage', 'disk_usage'])
        
        since = timezone.now() - timedelta(hours=hours)
        trends_data = {}
        
        for metric_type in metric_types:
            metrics = SystemMetrics.objects.filter(
                metric_type=metric_type,
                timestamp__gte=since
            ).order_by('timestamp')
            
            trends_data[metric_type] = [
                {
                    'timestamp': metric.timestamp.isoformat(),
                    'value': metric.metric_value,
                    'unit': metric.metric_unit
                }
                for metric in metrics
            ]
        
        return Response({
            'trends': trends_data,
            'period_hours': hours,
            'metrics': metric_types
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def alert_summary(request):
    """Get alert summary statistics"""
    try:
        # Get time range
        hours = int(request.GET.get('hours', 24))
        since = timezone.now() - timedelta(hours=hours)
        
        # Get alert counts by severity
        alert_counts = {}
        for severity in ['info', 'warning', 'error', 'critical', 'emergency']:
            count = SystemAlert.objects.filter(
                severity=severity,
                created_at__gte=since
            ).count()
            alert_counts[severity] = count
        
        # Get alert counts by type
        alert_types = {}
        for alert_type in ['performance', 'error', 'security', 'capacity', 'api_failure', 'database', 'cache']:
            count = SystemAlert.objects.filter(
                alert_type=alert_type,
                created_at__gte=since
            ).count()
            alert_types[alert_type] = count
        
        # Get alert counts by status
        alert_status = {}
        for status_type in ['active', 'acknowledged', 'resolved', 'suppressed']:
            count = SystemAlert.objects.filter(
                status=status_type,
                created_at__gte=since
            ).count()
            alert_status[status_type] = count
        
        return Response({
            'summary': {
                'total_alerts': sum(alert_counts.values()),
                'by_severity': alert_counts,
                'by_type': alert_types,
                'by_status': alert_status,
                'period_hours': hours
            }
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# WebSocket-style real-time monitoring endpoint
@csrf_exempt
@require_http_methods(["GET"])
@staff_member_required
def real_time_monitoring(request):
    """Real-time monitoring data endpoint"""
    try:
        # Get current system status
        status_data = system_monitor.get_system_status()
        
        # Add real-time specific data
        real_time_data = {
            'timestamp': timezone.now().isoformat(),
            'system_status': status_data,
            'active_alerts': SystemAlert.objects.filter(status='active').count(),
            'critical_alerts': SystemAlert.objects.filter(
                status='active', 
                severity='critical'
            ).count(),
        }
        
        return JsonResponse(real_time_data)
        
    except Exception as e:
        return JsonResponse(
            {'error': str(e)}, 
            status=500
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_test_alert(request):
    """Create a test alert for testing purposes"""
    try:
        alert = SystemAlert.objects.create(
            alert_type='custom',
            severity='info',
            title='Test Alert',
            message='This is a test alert created for testing purposes',
            component='test_system'
        )
        
        return Response({
            'message': 'Test alert created successfully',
            'alert_id': alert.id,
            'title': alert.title
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def cleanup_old_data(request):
    """Manually trigger cleanup of old monitoring data"""
    try:
        system_monitor._cleanup_old_data()
        
        return Response({
            'message': 'Old data cleanup completed successfully'
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )