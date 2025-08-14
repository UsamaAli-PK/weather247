"""
Celery tasks for background weather data processing
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

from .models import City, WeatherData
from .real_weather_service import weather_manager
from .cache_manager import WeatherCacheManager, invalidate_city_cache

logger = logging.getLogger('weather247')


@shared_task(bind=True, max_retries=3)
def refresh_city_weather(self, city_id):
    """Refresh weather data for a specific city"""
    try:
        city = City.objects.get(id=city_id, is_active=True)
        
        logger.info(f'Refreshing weather data for {city.name}')
        
        # Get fresh weather data
        weather_data = weather_manager.get_current_weather_with_fallback(
            city.name, city.country
        )
        
        if weather_data:
            # Invalidate cache for this city
            invalidate_city_cache(city.name)
            
            logger.info(f'Successfully refreshed weather for {city.name}: {weather_data.temperature}°C')
            return {
                'city': city.name,
                'temperature': weather_data.temperature,
                'condition': weather_data.weather_condition,
                'timestamp': weather_data.timestamp.isoformat()
            }
        else:
            logger.warning(f'Failed to refresh weather for {city.name}')
            return {'city': city.name, 'error': 'No weather data available'}
            
    except City.DoesNotExist:
        logger.error(f'City with ID {city_id} not found')
        return {'error': f'City with ID {city_id} not found'}
    except Exception as e:
        logger.error(f'Error refreshing weather for city {city_id}: {e}')
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2 ** self.request.retries)  # 60s, 120s, 240s
            logger.info(f'Retrying in {retry_delay} seconds (attempt {self.request.retries + 1})')
            raise self.retry(countdown=retry_delay, exc=e)
        
        return {'error': str(e)}


@shared_task
def refresh_all_cities_weather():
    """Refresh weather data for all active cities"""
    logger.info('Starting bulk weather refresh for all cities')
    
    cities = City.objects.filter(is_active=True)
    total_cities = cities.count()
    
    if total_cities == 0:
        logger.info('No active cities found for refresh')
        return {'message': 'No active cities found', 'updated': 0}
    
    # Create individual tasks for each city
    task_results = []
    for city in cities:
        task = refresh_city_weather.delay(city.id)
        task_results.append({
            'city_id': city.id,
            'city_name': city.name,
            'task_id': task.id
        })
    
    logger.info(f'Queued weather refresh tasks for {total_cities} cities')
    
    return {
        'message': f'Queued refresh tasks for {total_cities} cities',
        'total_cities': total_cities,
        'tasks': task_results
    }


@shared_task
def cleanup_old_weather_data(days_to_keep=30):
    """Clean up old weather data"""
    logger.info(f'Starting cleanup of weather data older than {days_to_keep} days')
    
    cutoff_date = timezone.now() - timedelta(days=days_to_keep)
    
    # Clean up weather data
    old_weather = WeatherData.objects.filter(timestamp__lt=cutoff_date)
    weather_count = old_weather.count()
    
    if weather_count > 0:
        deleted_weather = old_weather.delete()[0]
        logger.info(f'Deleted {deleted_weather} old weather records')
    else:
        deleted_weather = 0
        logger.info('No old weather records found')
    
    # Clean up air quality data
    from .models import AirQualityData
    old_air_quality = AirQualityData.objects.filter(timestamp__lt=cutoff_date)
    air_quality_count = old_air_quality.count()
    
    if air_quality_count > 0:
        deleted_air_quality = old_air_quality.delete()[0]
        logger.info(f'Deleted {deleted_air_quality} old air quality records')
    else:
        deleted_air_quality = 0
        logger.info('No old air quality records found')
    
    # Clean up old forecasts
    from .models import WeatherForecast
    old_forecasts = WeatherForecast.objects.filter(
        forecast_date__lt=timezone.now().date() - timedelta(days=7)
    )
    forecast_count = old_forecasts.count()
    
    if forecast_count > 0:
        deleted_forecasts = old_forecasts.delete()[0]
        logger.info(f'Deleted {deleted_forecasts} old forecast records')
    else:
        deleted_forecasts = 0
        logger.info('No old forecast records found')
    
    total_deleted = deleted_weather + deleted_air_quality + deleted_forecasts
    
    logger.info(f'Cleanup completed: {total_deleted} total records deleted')
    
    return {
        'message': 'Cleanup completed',
        'deleted_weather': deleted_weather,
        'deleted_air_quality': deleted_air_quality,
        'deleted_forecasts': deleted_forecasts,
        'total_deleted': total_deleted
    }


@shared_task
def warm_cache_for_popular_cities():
    """Pre-warm cache for popular cities"""
    logger.info('Starting cache warming for popular cities')
    
    # Get cities with recent activity (most weather data requests)
    from django.db.models import Count
    popular_cities = City.objects.annotate(
        weather_count=Count('weather_data')
    ).filter(
        is_active=True,
        weather_count__gt=0
    ).order_by('-weather_count')[:20]  # Top 20 cities
    
    warmed_count = 0
    failed_count = 0
    
    for city in popular_cities:
        try:
            # Get fresh weather data to warm the cache
            weather_data = weather_manager.get_current_weather_with_fallback(
                city.name, city.country
            )
            
            if weather_data:
                warmed_count += 1
                logger.debug(f'Cache warmed for {city.name}')
            else:
                failed_count += 1
                logger.warning(f'Failed to warm cache for {city.name}')
                
        except Exception as e:
            failed_count += 1
            logger.error(f'Error warming cache for {city.name}: {e}')
    
    logger.info(f'Cache warming completed: {warmed_count} successful, {failed_count} failed')
    
    return {
        'message': 'Cache warming completed',
        'warmed': warmed_count,
        'failed': failed_count,
        'total_cities': popular_cities.count()
    }


@shared_task
def monitor_api_quota():
    """Monitor API quota usage and send alerts if needed"""
    logger.info('Monitoring API quota usage')
    
    try:
        # Get service health
        health = weather_manager.get_service_health()
        
        # Check if primary service is healthy
        primary_status = health.get('primary_service', {}).get('status')
        
        if primary_status != 'healthy':
            logger.warning(f'Primary weather service status: {primary_status}')
            
            # Here you could send alerts to administrators
            # For now, just log the issue
            return {
                'status': 'warning',
                'message': f'Primary service status: {primary_status}',
                'timestamp': timezone.now().isoformat()
            }
        
        logger.info('API quota monitoring completed - all services healthy')
        return {
            'status': 'healthy',
            'message': 'All services operational',
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f'Error monitoring API quota: {e}')
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def generate_weather_analytics():
    """Generate weather analytics and cache results"""
    logger.info('Generating weather analytics')
    
    try:
        from django.db.models import Avg, Max, Min, Count
        
        # Get analytics for all active cities
        cities = City.objects.filter(is_active=True)
        analytics_generated = 0
        
        for city in cities:
            try:
                # Get recent weather data for analytics
                recent_weather = WeatherData.objects.filter(
                    city=city,
                    timestamp__gte=timezone.now() - timedelta(days=7)
                )
                
                if recent_weather.exists():
                    analytics = {
                        'city': city.name,
                        'avg_temperature': recent_weather.aggregate(Avg('temperature'))['temperature__avg'],
                        'max_temperature': recent_weather.aggregate(Max('temperature'))['temperature__max'],
                        'min_temperature': recent_weather.aggregate(Min('temperature'))['temperature__min'],
                        'avg_humidity': recent_weather.aggregate(Avg('humidity'))['humidity__avg'],
                        'data_points': recent_weather.count(),
                        'generated_at': timezone.now().isoformat()
                    }
                    
                    # Cache the analytics
                    cache_key = WeatherCacheManager.get_analytics_cache_key(city.name, 'weekly')
                    WeatherCacheManager.set_cache(cache_key, analytics, 'analytics')
                    
                    analytics_generated += 1
                    logger.debug(f'Generated analytics for {city.name}')
                
            except Exception as e:
                logger.error(f'Error generating analytics for {city.name}: {e}')
        
        logger.info(f'Analytics generation completed: {analytics_generated} cities processed')
        
        return {
            'message': 'Analytics generation completed',
            'cities_processed': analytics_generated,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f'Error generating weather analytics: {e}')
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': timezone.now().isoformat()
        }

@share
d_task
def generate_analytics_report():
    """Generate and cache analytics reports"""
    logger.info('Generating analytics reports')
    
    try:
        from .analytics import weather_analytics, health_monitor
        
        # Generate all analytics
        analytics_data = {
            'api_usage': weather_analytics.get_api_usage_stats(24),
            'cache_performance': weather_analytics.get_cache_performance_stats(),
            'data_freshness': weather_analytics.get_data_freshness_stats(),
            'weather_trends': weather_analytics.get_weather_trends(7),
            'generated_at': timezone.now().isoformat()
        }
        
        # Cache the analytics data
        cache_key = 'analytics:daily_report'
        WeatherCacheManager.set_cache(cache_key, analytics_data, 'analytics')
        
        logger.info('Analytics report generated and cached successfully')
        
        return {
            'message': 'Analytics report generated successfully',
            'timestamp': timezone.now().isoformat(),
            'data_points': {
                'api_requests': analytics_data['api_usage'].get('total_requests', 0),
                'cache_hit_rate': analytics_data['cache_performance'].get('estimated_hit_rate', 0),
                'health_score': analytics_data['data_freshness'].get('health_score', 0)
            }
        }
        
    except Exception as e:
        logger.error(f'Error generating analytics report: {e}')
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def system_health_check():
    """Perform system health check and send alerts if needed"""
    logger.info('Performing system health check')
    
    try:
        from .analytics import health_monitor
        
        # Get health report
        health_report = health_monitor.check_and_send_alerts()
        
        # Cache the health report
        cache_key = 'health:latest_report'
        WeatherCacheManager.set_cache(cache_key, health_report, 'monitoring')
        
        # Count alerts and warnings
        alert_count = len(health_report.get('alerts', []))
        warning_count = len(health_report.get('warnings', []))
        overall_status = health_report.get('overall_status', 'unknown')
        
        logger.info(f'Health check completed: {overall_status} status, {alert_count} alerts, {warning_count} warnings')
        
        # If there are critical alerts, log them prominently
        if overall_status == 'critical':
            logger.error(f'CRITICAL SYSTEM HEALTH ISSUES DETECTED: {alert_count} alerts')
            for alert in health_report.get('alerts', []):
                if alert.get('severity') == 'high':
                    logger.error(f"Critical Alert [{alert['type']}]: {alert['message']}")
        
        return {
            'message': 'Health check completed',
            'status': overall_status,
            'alert_count': alert_count,
            'warning_count': warning_count,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f'Error performing health check: {e}')
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def cleanup_analytics_cache():
    """Clean up old analytics cache entries"""
    logger.info('Cleaning up analytics cache')
    
    try:
        from django.core.cache import cache
        
        # List of analytics cache patterns to clean
        cache_patterns = [
            'analytics:api_usage:*',
            'analytics:cache_performance:*',
            'analytics:trends:*',
            'health:report:*'
        ]
        
        cleaned_count = 0
        
        # Note: This is a simplified cleanup
        # In production, you might want to use Redis-specific commands
        # or implement a more sophisticated cache cleanup strategy
        
        # For now, we'll just clean specific known keys
        old_keys = [
            'analytics:daily_report',
            'health:latest_report'
        ]
        
        for key in old_keys:
            if cache.get(key):
                cache.delete(key)
                cleaned_count += 1
        
        logger.info(f'Analytics cache cleanup completed: {cleaned_count} entries cleaned')
        
        return {
            'message': 'Cache cleanup completed',
            'cleaned_entries': cleaned_count,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f'Error cleaning analytics cache: {e}')
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': timezone.now().isoformat()
        }
@shared
_task
def optimize_system_performance():
    """Periodic system performance optimization"""
    logger.info('Starting system performance optimization')
    
    try:
        from .performance import cache_optimizer, db_optimizer, performance_monitor
        
        optimization_results = {
            'cache_optimization': None,
            'performance_analysis': None,
            'recommendations_applied': 0,
            'timestamp': timezone.now().isoformat()
        }
        
        # Optimize cache system
        try:
            cache_warming = cache_optimizer.implement_cache_warming_strategy()
            optimization_results['cache_optimization'] = cache_warming
            logger.info(f'Cache warming completed: {cache_warming.get("cities_warmed", 0)} cities')
        except Exception as e:
            logger.error(f'Cache optimization error: {e}')
            optimization_results['cache_optimization'] = {'error': str(e)}
        
        # Analyze performance and apply automatic optimizations
        try:
            analysis = performance_monitor.analyze_performance_bottlenecks()
            optimization_results['performance_analysis'] = analysis
            
            # Apply automatic optimizations based on analysis
            bottlenecks = analysis.get('bottlenecks', [])
            for bottleneck in bottlenecks:
                if bottleneck['type'] == 'cache' and bottleneck['severity'] == 'high':
                    # Trigger additional cache warming
                    cache_optimizer.implement_cache_warming_strategy()
                    optimization_results['recommendations_applied'] += 1
                    logger.info('Applied automatic cache optimization')
                
        except Exception as e:
            logger.error(f'Performance analysis error: {e}')
            optimization_results['performance_analysis'] = {'error': str(e)}
        
        logger.info(f'Performance optimization completed: {optimization_results["recommendations_applied"]} optimizations applied')
        
        return {
            'message': 'Performance optimization completed',
            'results': optimization_results
        }
        
    except Exception as e:
        logger.error(f'Error in performance optimization: {e}')
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def database_maintenance():
    """Perform database maintenance tasks"""
    logger.info('Starting database maintenance')
    
    try:
        from .performance import db_optimizer
        from django.db import connection
        
        maintenance_results = {
            'vacuum_completed': False,
            'analyze_completed': False,
            'old_data_cleaned': 0,
            'timestamp': timezone.now().isoformat()
        }
        
        # Update database statistics
        try:
            with connection.cursor() as cursor:
                cursor.execute('ANALYZE;')
                maintenance_results['analyze_completed'] = True
                logger.info('Database statistics updated')
        except Exception as e:
            logger.error(f'Database analyze error: {e}')
        
        # Clean up old data (keep last 30 days)
        try:
            deleted_count = db_optimizer.cleanup_old_data_optimized(days_to_keep=30)
            maintenance_results['old_data_cleaned'] = deleted_count
            logger.info(f'Cleaned up {deleted_count} old weather records')
        except Exception as e:
            logger.error(f'Data cleanup error: {e}')
        
        return {
            'message': 'Database maintenance completed',
            'results': maintenance_results
        }
        
    except Exception as e:
        logger.error(f'Error in database maintenance: {e}')
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': timezone.now().isoformat()
        }
# Import 
API monitoring tasks
from .api_monitoring_tasks import (
    monitor_api_health,
    cleanup_old_usage_records,
    generate_cost_alerts,
    update_provider_success_rates,
    auto_resolve_old_failovers
)