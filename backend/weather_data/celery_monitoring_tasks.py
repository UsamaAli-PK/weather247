"""
Celery tasks for system monitoring
"""
from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from datetime import timedelta

from .system_monitoring_core import system_monitor, system_diagnostics
from .models import SystemAlert

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3)
def collect_system_metrics_periodic(self):
    """
    Periodic task to collect system metrics
    Runs every minute
    """
    try:
        logger.info("Starting periodic system metrics collection")
        
        # Collect metrics
        metrics = system_monitor.collect_system_metrics()
        
        # Store metrics in database
        system_monitor.store_metrics(metrics)
        
        # Check thresholds and create alerts
        system_monitor.check_thresholds(metrics)
        
        logger.info("System metrics collection completed successfully")
        return {
            'status': 'success',
            'timestamp': timezone.now().isoformat(),
            'metrics_collected': len(metrics)
        }
        
    except Exception as exc:
        logger.error(f"Error in system metrics collection: {str(exc)}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries), exc=exc)
        
        # Create alert for monitoring failure
        try:
            SystemAlert.objects.create(
                alert_type='error',
                severity='warning',
                title='System Monitoring Failed',
                message=f'Failed to collect system metrics: {str(exc)}',
                component='monitoring_system',
                error_details={'error': str(exc), 'task': 'collect_system_metrics_periodic'}
            )
        except Exception as alert_exc:
            logger.error(f"Failed to create monitoring failure alert: {str(alert_exc)}")
        
        return {
            'status': 'error',
            'error': str(exc),
            'timestamp': timezone.now().isoformat()
        }


@shared_task(bind=True, max_retries=3)
def perform_health_checks_periodic(self):
    """
    Periodic task to perform system health checks
    Runs every 5 minutes
    """
    try:
        logger.info("Starting periodic health checks")
        
        # Perform health checks
        health_results = system_monitor.perform_health_checks()
        
        # Check for unhealthy components and create alerts
        for component, result in health_results.items():
            if component == 'overall':
                continue
                
            if result.get('status') == 'unhealthy':
                SystemAlert.objects.get_or_create(
                    alert_type='error',
                    component=f'health_check_{component}',
                    status='active',
                    defaults={
                        'severity': 'error',
                        'title': f'{component.title()} Health Check Failed',
                        'message': result.get('error', f'{component} health check failed'),
                        'error_details': result
                    }
                )
            elif result.get('status') == 'warning':
                SystemAlert.objects.get_or_create(
                    alert_type='performance',
                    component=f'health_check_{component}',
                    status='active',
                    defaults={
                        'severity': 'warning',
                        'title': f'{component.title()} Health Warning',
                        'message': result.get('message', f'{component} health check warning'),
                        'error_details': result
                    }
                )
        
        logger.info("Health checks completed successfully")
        return {
            'status': 'success',
            'timestamp': timezone.now().isoformat(),
            'health_results': health_results
        }
        
    except Exception as exc:
        logger.error(f"Error in health checks: {str(exc)}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300 * (2 ** self.request.retries), exc=exc)
        
        return {
            'status': 'error',
            'error': str(exc),
            'timestamp': timezone.now().isoformat()
        }


@shared_task(bind=True)
def cleanup_old_monitoring_data(self):
    """
    Periodic task to clean up old monitoring data
    Runs daily
    """
    try:
        logger.info("Starting cleanup of old monitoring data")
        
        # Clean up old data
        system_monitor._cleanup_old_data()
        
        logger.info("Monitoring data cleanup completed successfully")
        return {
            'status': 'success',
            'timestamp': timezone.now().isoformat(),
            'message': 'Old monitoring data cleaned up successfully'
        }
        
    except Exception as exc:
        logger.error(f"Error in monitoring data cleanup: {str(exc)}")
        return {
            'status': 'error',
            'error': str(exc),
            'timestamp': timezone.now().isoformat()
        }


@shared_task(bind=True)
def generate_system_health_report(self):
    """
    Generate comprehensive system health report
    Runs daily
    """
    try:
        logger.info("Generating system health report")
        
        # Run full diagnostic
        diagnostic_results = system_diagnostics.run_full_diagnostic()
        
        # Check if there are critical issues
        critical_alerts = diagnostic_results.get('recent_alerts', [])
        critical_count = len([a for a in critical_alerts if a.get('severity') == 'critical'])
        
        if critical_count > 0:
            SystemAlert.objects.create(
                alert_type='error',
                severity='critical',
                title='Critical System Issues Detected',
                message=f'System health report found {critical_count} critical issues requiring immediate attention',
                component='system_health_report',
                error_details={
                    'critical_alerts': critical_count,
                    'report_timestamp': timezone.now().isoformat()
                }
            )
        
        logger.info("System health report generated successfully")
        return {
            'status': 'success',
            'timestamp': timezone.now().isoformat(),
            'critical_issues': critical_count,
            'recommendations': len(diagnostic_results.get('recommendations', []))
        }
        
    except Exception as exc:
        logger.error(f"Error generating system health report: {str(exc)}")
        return {
            'status': 'error',
            'error': str(exc),
            'timestamp': timezone.now().isoformat()
        }


@shared_task(bind=True)
def alert_escalation_check(self):
    """
    Check for unacknowledged critical alerts and escalate if needed
    Runs every 15 minutes
    """
    try:
        logger.info("Checking for alert escalation")
        
        # Find critical alerts that are older than 30 minutes and not acknowledged
        escalation_threshold = timezone.now() - timedelta(minutes=30)
        
        unacknowledged_critical = SystemAlert.objects.filter(
            severity='critical',
            status='active',
            acknowledged_at__isnull=True,
            created_at__lt=escalation_threshold
        )
        
        escalated_count = 0
        for alert in unacknowledged_critical:
            # Create escalation alert
            SystemAlert.objects.create(
                alert_type='security',  # Escalated alerts are treated as security issues
                severity='emergency',
                title=f'ESCALATED: {alert.title}',
                message=f'Critical alert has been unacknowledged for over 30 minutes: {alert.message}',
                component=f'escalation_{alert.component}',
                error_details={
                    'original_alert_id': alert.id,
                    'original_created_at': alert.created_at.isoformat(),
                    'escalation_reason': 'Unacknowledged critical alert'
                }
            )
            escalated_count += 1
        
        if escalated_count > 0:
            logger.warning(f"Escalated {escalated_count} critical alerts")
        
        return {
            'status': 'success',
            'timestamp': timezone.now().isoformat(),
            'escalated_alerts': escalated_count
        }
        
    except Exception as exc:
        logger.error(f"Error in alert escalation check: {str(exc)}")
        return {
            'status': 'error',
            'error': str(exc),
            'timestamp': timezone.now().isoformat()
        }


@shared_task(bind=True)
def system_performance_analysis(self):
    """
    Analyze system performance trends and create recommendations
    Runs every 6 hours
    """
    try:
        logger.info("Starting system performance analysis")
        
        # Get performance trends for the last 24 hours
        since = timezone.now() - timedelta(hours=24)
        
        from .models import SystemMetrics
        
        # Analyze CPU usage trends
        cpu_metrics = SystemMetrics.objects.filter(
            metric_type='cpu_usage',
            timestamp__gte=since
        ).order_by('timestamp')
        
        if cpu_metrics.exists():
            cpu_values = [m.metric_value for m in cpu_metrics]
            avg_cpu = sum(cpu_values) / len(cpu_values)
            max_cpu = max(cpu_values)
            
            if avg_cpu > 70:
                SystemAlert.objects.create(
                    alert_type='performance',
                    severity='warning',
                    title='High Average CPU Usage Detected',
                    message=f'Average CPU usage over 24h: {avg_cpu:.1f}% (max: {max_cpu:.1f}%)',
                    component='performance_analysis',
                    metric_value=avg_cpu,
                    threshold_value=70.0
                )
        
        # Analyze memory usage trends
        memory_metrics = SystemMetrics.objects.filter(
            metric_type='memory_usage',
            timestamp__gte=since
        ).order_by('timestamp')
        
        if memory_metrics.exists():
            memory_values = [m.metric_value for m in memory_metrics]
            avg_memory = sum(memory_values) / len(memory_values)
            max_memory = max(memory_values)
            
            if avg_memory > 80:
                SystemAlert.objects.create(
                    alert_type='capacity',
                    severity='warning',
                    title='High Average Memory Usage Detected',
                    message=f'Average memory usage over 24h: {avg_memory:.1f}% (max: {max_memory:.1f}%)',
                    component='performance_analysis',
                    metric_value=avg_memory,
                    threshold_value=80.0
                )
        
        logger.info("System performance analysis completed successfully")
        return {
            'status': 'success',
            'timestamp': timezone.now().isoformat(),
            'cpu_metrics_analyzed': cpu_metrics.count() if cpu_metrics.exists() else 0,
            'memory_metrics_analyzed': memory_metrics.count() if memory_metrics.exists() else 0
        }
        
    except Exception as exc:
        logger.error(f"Error in system performance analysis: {str(exc)}")
        return {
            'status': 'error',
            'error': str(exc),
            'timestamp': timezone.now().isoformat()
        }


# Task to start monitoring (called once to initialize)
@shared_task
def initialize_system_monitoring():
    """
    Initialize system monitoring
    This task should be called once when the system starts
    """
    try:
        logger.info("Initializing system monitoring")
        
        # Create initial system status check
        status = system_monitor.get_system_status()
        
        # Create initialization alert
        SystemAlert.objects.create(
            alert_type='custom',
            severity='info',
            title='System Monitoring Initialized',
            message='System monitoring has been successfully initialized and is now active',
            component='monitoring_system',
            error_details={
                'initialization_time': timezone.now().isoformat(),
                'system_status': status.get('overall_status', 'unknown')
            }
        )
        
        logger.info("System monitoring initialized successfully")
        return {
            'status': 'success',
            'timestamp': timezone.now().isoformat(),
            'message': 'System monitoring initialized successfully'
        }
        
    except Exception as exc:
        logger.error(f"Error initializing system monitoring: {str(exc)}")
        return {
            'status': 'error',
            'error': str(exc),
            'timestamp': timezone.now().isoformat()
        }