"""
Celery tasks for API monitoring and automatic failover
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

from .api_management import APIProvider, api_manager

logger = logging.getLogger('weather247')


@shared_task
def monitor_api_health():
    """Monitor API provider health and perform health checks"""
    try:
        providers = APIProvider.objects.filter(is_active=True)
        
        for provider in providers:
            try:
                # Perform health check
                health_result = api_manager.perform_health_check(provider)
                
                if health_result['healthy']:
                    logger.info(f"Health check passed for {provider.name}")
                else:
                    logger.warning(f"Health check failed for {provider.name}: {health_result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"Error performing health check for {provider.name}: {str(e)}")
                provider.update_health_status(False)
        
        return f"Health check completed for {providers.count()} providers"
        
    except Exception as e:
        logger.error(f"Error in monitor_api_health task: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def cleanup_old_usage_records():
    """Clean up old API usage records to prevent database bloat"""
    try:
        from .api_management import APIUsage, APIFailover
        
        # Keep usage records for 90 days
        cutoff_date = timezone.now().date() - timedelta(days=90)
        
        deleted_usage = APIUsage.objects.filter(date__lt=cutoff_date).delete()
        logger.info(f"Deleted {deleted_usage[0]} old usage records")
        
        # Keep failover records for 30 days
        failover_cutoff = timezone.now() - timedelta(days=30)
        deleted_failovers = APIFailover.objects.filter(
            failed_at__lt=failover_cutoff,
            resolved_at__isnull=False
        ).delete()
        logger.info(f"Deleted {deleted_failovers[0]} old failover records")
        
        return f"Cleanup completed: {deleted_usage[0]} usage records, {deleted_failovers[0]} failover records"
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_usage_records task: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def generate_cost_alerts():
    """Generate alerts when API costs exceed thresholds"""
    try:
        providers = APIProvider.objects.filter(is_active=True, monthly_budget__gt=0)
        alerts = []
        
        for provider in providers:
            usage_month = provider.get_usage_this_month()
            monthly_cost = float(usage_month.get('total_cost', 0))
            budget = float(provider.monthly_budget)
            
            if budget > 0:
                usage_percentage = (monthly_cost / budget) * 100
                
                if usage_percentage >= 90:
                    alert_message = f"CRITICAL: {provider.display_name} has used {usage_percentage:.1f}% of monthly budget (${monthly_cost:.2f}/${budget:.2f})"
                    alerts.append(alert_message)
                    logger.critical(alert_message)
                    
                elif usage_percentage >= 75:
                    alert_message = f"WARNING: {provider.display_name} has used {usage_percentage:.1f}% of monthly budget (${monthly_cost:.2f}/${budget:.2f})"
                    alerts.append(alert_message)
                    logger.warning(alert_message)
        
        return f"Cost monitoring completed. {len(alerts)} alerts generated."
        
    except Exception as e:
        logger.error(f"Error in generate_cost_alerts task: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def update_provider_success_rates():
    """Update success rates for all providers based on recent usage"""
    try:
        from django.db import models
        from .api_management import APIUsage
        
        providers = APIProvider.objects.all()
        updated_count = 0
        
        # Calculate success rates based on last 7 days
        cutoff_date = timezone.now().date() - timedelta(days=7)
        
        for provider in providers:
            recent_usage = APIUsage.objects.filter(
                provider=provider,
                date__gte=cutoff_date
            ).aggregate(
                total_requests=models.Sum('request_count'),
                total_errors=models.Sum('error_count')
            )
            
            total_requests = recent_usage['total_requests'] or 0
            total_errors = recent_usage['total_errors'] or 0
            
            if total_requests > 0:
                success_rate = ((total_requests - total_errors) / total_requests) * 100
                
                if abs(provider.success_rate - success_rate) > 0.1:  # Only update if significant change
                    provider.success_rate = success_rate
                    provider.is_healthy = success_rate >= 80 and provider.error_count < 10
                    provider.save(update_fields=['success_rate', 'is_healthy'])
                    updated_count += 1
        
        return f"Updated success rates for {updated_count} providers"
        
    except Exception as e:
        logger.error(f"Error in update_provider_success_rates task: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def auto_resolve_old_failovers():
    """Automatically resolve old failover events that are likely resolved"""
    try:
        from .api_management import APIFailover
        
        # Auto-resolve failovers older than 1 hour if primary provider is healthy
        cutoff_time = timezone.now() - timedelta(hours=1)
        
        old_failovers = APIFailover.objects.filter(
            failed_at__lt=cutoff_time,
            resolved_at__isnull=True,
            primary_provider__is_healthy=True
        )
        
        resolved_count = 0
        for failover in old_failovers:
            failover.resolved_at = timezone.now()
            failover.save()
            resolved_count += 1
            
            logger.info(f"Auto-resolved failover {failover.id}: {failover.primary_provider.name} → {failover.fallback_provider.name}")
        
        return f"Auto-resolved {resolved_count} old failover events"
        
    except Exception as e:
        logger.error(f"Error in auto_resolve_old_failovers task: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def start_real_time_monitoring():
    """Start the real-time monitoring system"""
    try:
        from .api_monitoring_realtime import real_time_monitor
        
        real_time_monitor.start_monitoring()
        logger.info("Real-time API monitoring started via Celery task")
        
        return "Real-time monitoring started successfully"
        
    except Exception as e:
        logger.error(f"Error starting real-time monitoring: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def generate_api_health_report():
    """Generate comprehensive API health report"""
    try:
        from .api_management import APIProvider, APIUsage, APIFailover, api_manager
        
        providers = APIProvider.objects.all()
        report = {
            'timestamp': timezone.now().isoformat(),
            'summary': {
                'total_providers': providers.count(),
                'active_providers': providers.filter(is_active=True).count(),
                'healthy_providers': providers.filter(is_active=True, is_healthy=True).count()
            },
            'providers': []
        }
        
        for provider in providers:
            stats = api_manager.get_provider_statistics(provider.id, days=7)
            
            # Get recent failovers
            recent_failovers = APIFailover.objects.filter(
                primary_provider=provider,
                failed_at__gte=timezone.now() - timedelta(days=7)
            ).count()
            
            provider_report = {
                'name': provider.name,
                'display_name': provider.display_name,
                'is_active': provider.is_active,
                'is_healthy': provider.is_healthy,
                'success_rate': stats['usage']['success_rate'],
                'total_requests': stats['usage']['total_requests'],
                'total_errors': stats['usage']['total_errors'],
                'avg_response_time': stats['usage']['avg_response_time'],
                'total_cost': stats['usage']['total_cost'],
                'recent_failovers': recent_failovers
            }
            
            report['providers'].append(provider_report)
        
        # Log the report
        logger.info(f"API Health Report Generated: {report['summary']}")
        
        return f"Health report generated for {len(report['providers'])} providers"
        
    except Exception as e:
        logger.error(f"Error generating health report: {str(e)}")
        return f"Error: {str(e)}"