"""
Weather Data Analytics and Monitoring Service
"""
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Avg, Max, Min, Q
from django.core.cache import cache
from collections import defaultdict
import json

from .models import City, WeatherData, AirQualityData
from .cache_manager import WeatherCacheManager

logger = logging.getLogger('weather247')


class WeatherAnalytics:
    """Service for generating weather data analytics"""
    
    def __init__(self):
        self.cache_prefix = 'analytics'
        self.default_ttl = 3600  # 1 hour
    
    def get_api_usage_stats(self, hours=24):
        """Get API usage statistics"""
        try:
            end_time = timezone.now()
            start_time = end_time - timedelta(hours=hours)
            
            # Get weather data requests in time period
            weather_requests = WeatherData.objects.filter(
                timestamp__gte=start_time,
                timestamp__lte=end_time
            )
            
            # Calculate stats
            total_requests = weather_requests.count()
            unique_cities = weather_requests.values('city').distinct().count()
            
            # Requests per hour
            hourly_stats = []
            for i in range(hours):
                hour_start = start_time + timedelta(hours=i)
                hour_end = hour_start + timedelta(hours=1)
                
                hour_requests = weather_requests.filter(
                    timestamp__gte=hour_start,
                    timestamp__lt=hour_end
                ).count()
                
                hourly_stats.append({
                    'hour': hour_start.strftime('%Y-%m-%d %H:00'),
                    'requests': hour_requests
                })
            
            # Top cities by requests
            top_cities = weather_requests.values('city__name').annotate(
                request_count=Count('id')
            ).order_by('-request_count')[:10]
            
            stats = {
                'period': f'Last {hours} hours',
                'total_requests': total_requests,
                'unique_cities': unique_cities,
                'avg_requests_per_hour': total_requests / hours if hours > 0 else 0,
                'hourly_breakdown': hourly_stats,
                'top_cities': list(top_cities),
                'generated_at': timezone.now().isoformat()
            }
            
            # Cache the results
            cache_key = f'{self.cache_prefix}:api_usage:{hours}h'
            cache.set(cache_key, stats, self.default_ttl)
            
            return stats
            
        except Exception as e:
            logger.error(f'Error generating API usage stats: {e}')
            return {'error': str(e)}
    
    def get_cache_performance_stats(self):
        """Get cache hit rate and performance statistics"""
        try:
            # Get cache stats from WeatherCacheManager
            cache_stats = WeatherCacheManager.get_cache_stats()
            
            # Add additional performance metrics
            now = timezone.now()
            last_24h = now - timedelta(hours=24)
            
            # Calculate cache effectiveness
            recent_requests = WeatherData.objects.filter(
                timestamp__gte=last_24h
            ).count()
            
            # Estimate cache hits vs misses based on request patterns
            # This is an approximation since we don't track actual cache hits
            estimated_cache_hits = 0
            estimated_cache_misses = 0
            
            # Group requests by city and time to estimate cache effectiveness
            city_requests = WeatherData.objects.filter(
                timestamp__gte=last_24h
            ).values('city__name').annotate(
                request_count=Count('id'),
                time_span=Max('timestamp') - Min('timestamp')
            )
            
            for city_data in city_requests:
                requests = city_data['request_count']
                time_span = city_data['time_span']
                
                if time_span and time_span.total_seconds() > 0:
                    # Estimate cache hits based on request frequency
                    # If requests are close together, likely cache hits
                    avg_interval = time_span.total_seconds() / max(requests - 1, 1)
                    cache_ttl = 900  # 15 minutes default TTL
                    
                    if avg_interval < cache_ttl:
                        estimated_cache_hits += max(0, requests - 1)
                        estimated_cache_misses += 1
                    else:
                        estimated_cache_misses += requests
                else:
                    estimated_cache_misses += requests
            
            total_estimated = estimated_cache_hits + estimated_cache_misses
            hit_rate = (estimated_cache_hits / total_estimated * 100) if total_estimated > 0 else 0
            
            performance_stats = {
                'cache_backend': cache_stats.get('backend', 'Unknown'),
                'estimated_hit_rate': round(hit_rate, 2),
                'estimated_hits': estimated_cache_hits,
                'estimated_misses': estimated_cache_misses,
                'total_requests_24h': recent_requests,
                'cache_efficiency': 'Good' if hit_rate > 70 else 'Fair' if hit_rate > 40 else 'Poor',
                'recommendations': self._get_cache_recommendations(hit_rate),
                'generated_at': timezone.now().isoformat()
            }
            
            # Merge with existing cache stats
            performance_stats.update(cache_stats)
            
            return performance_stats
            
        except Exception as e:
            logger.error(f'Error generating cache performance stats: {e}')
            return {'error': str(e)}
    
    def get_data_freshness_stats(self):
        """Get weather data freshness monitoring"""
        try:
            now = timezone.now()
            
            # Define freshness thresholds
            very_fresh = now - timedelta(minutes=15)  # Very fresh
            fresh = now - timedelta(minutes=30)       # Fresh
            stale = now - timedelta(hours=2)          # Stale
            very_stale = now - timedelta(hours=6)     # Very stale
            
            # Get all active cities
            active_cities = City.objects.filter(is_active=True)
            total_cities = active_cities.count()
            
            # Categorize cities by data freshness
            freshness_stats = {
                'very_fresh': 0,    # < 15 min
                'fresh': 0,         # 15-30 min
                'stale': 0,         # 30 min - 2 hours
                'very_stale': 0,    # 2-6 hours
                'no_data': 0        # > 6 hours or no data
            }
            
            city_details = []
            
            for city in active_cities:
                latest_weather = WeatherData.objects.filter(
                    city=city
                ).order_by('-timestamp').first()
                
                if latest_weather:
                    age = now - latest_weather.timestamp
                    age_minutes = age.total_seconds() / 60
                    
                    if latest_weather.timestamp >= very_fresh:
                        freshness_stats['very_fresh'] += 1
                        status = 'very_fresh'
                    elif latest_weather.timestamp >= fresh:
                        freshness_stats['fresh'] += 1
                        status = 'fresh'
                    elif latest_weather.timestamp >= stale:
                        freshness_stats['stale'] += 1
                        status = 'stale'
                    elif latest_weather.timestamp >= very_stale:
                        freshness_stats['very_stale'] += 1
                        status = 'very_stale'
                    else:
                        freshness_stats['no_data'] += 1
                        status = 'no_data'
                    
                    city_details.append({
                        'city': city.name,
                        'country': city.country,
                        'last_update': latest_weather.timestamp.isoformat(),
                        'age_minutes': round(age_minutes, 1),
                        'status': status,
                        'temperature': latest_weather.temperature
                    })
                else:
                    freshness_stats['no_data'] += 1
                    city_details.append({
                        'city': city.name,
                        'country': city.country,
                        'last_update': None,
                        'age_minutes': None,
                        'status': 'no_data',
                        'temperature': None
                    })
            
            # Calculate percentages
            freshness_percentages = {}
            for status, count in freshness_stats.items():
                freshness_percentages[status] = round(
                    (count / total_cities * 100) if total_cities > 0 else 0, 1
                )
            
            # Overall health score
            health_score = (
                freshness_stats['very_fresh'] * 100 +
                freshness_stats['fresh'] * 80 +
                freshness_stats['stale'] * 40 +
                freshness_stats['very_stale'] * 20 +
                freshness_stats['no_data'] * 0
            ) / total_cities if total_cities > 0 else 0
            
            stats = {
                'total_cities': total_cities,
                'freshness_counts': freshness_stats,
                'freshness_percentages': freshness_percentages,
                'health_score': round(health_score, 1),
                'health_status': self._get_health_status(health_score),
                'city_details': sorted(city_details, key=lambda x: x['age_minutes'] or float('inf')),
                'recommendations': self._get_freshness_recommendations(freshness_stats, total_cities),
                'generated_at': timezone.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f'Error generating data freshness stats: {e}')
            return {'error': str(e)}
    
    def get_weather_trends(self, days=7):
        """Get weather trends and patterns"""
        try:
            end_time = timezone.now()
            start_time = end_time - timedelta(days=days)
            
            # Get weather data for the period
            weather_data = WeatherData.objects.filter(
                timestamp__gte=start_time,
                timestamp__lte=end_time
            )
            
            if not weather_data.exists():
                return {'error': 'No weather data available for the specified period'}
            
            # Overall statistics
            overall_stats = weather_data.aggregate(
                avg_temp=Avg('temperature'),
                max_temp=Max('temperature'),
                min_temp=Min('temperature'),
                avg_humidity=Avg('humidity'),
                avg_pressure=Avg('pressure')
            )
            
            # Daily trends
            daily_trends = []
            for i in range(days):
                day_start = start_time + timedelta(days=i)
                day_end = day_start + timedelta(days=1)
                
                day_data = weather_data.filter(
                    timestamp__gte=day_start,
                    timestamp__lt=day_end
                )
                
                if day_data.exists():
                    day_stats = day_data.aggregate(
                        avg_temp=Avg('temperature'),
                        max_temp=Max('temperature'),
                        min_temp=Min('temperature'),
                        avg_humidity=Avg('humidity'),
                        data_points=Count('id')
                    )
                    
                    daily_trends.append({
                        'date': day_start.strftime('%Y-%m-%d'),
                        'avg_temperature': round(day_stats['avg_temp'] or 0, 1),
                        'max_temperature': day_stats['max_temp'],
                        'min_temperature': day_stats['min_temp'],
                        'avg_humidity': round(day_stats['avg_humidity'] or 0, 1),
                        'data_points': day_stats['data_points']
                    })
            
            # Top cities by data volume
            city_stats = weather_data.values('city__name', 'city__country').annotate(
                data_points=Count('id'),
                avg_temp=Avg('temperature'),
                temp_range=Max('temperature') - Min('temperature')
            ).order_by('-data_points')[:10]
            
            trends = {
                'period': f'Last {days} days',
                'total_data_points': weather_data.count(),
                'overall_stats': {
                    'avg_temperature': round(overall_stats['avg_temp'] or 0, 1),
                    'max_temperature': overall_stats['max_temp'],
                    'min_temperature': overall_stats['min_temp'],
                    'avg_humidity': round(overall_stats['avg_humidity'] or 0, 1),
                    'avg_pressure': round(overall_stats['avg_pressure'] or 0, 1)
                },
                'daily_trends': daily_trends,
                'top_cities': list(city_stats),
                'generated_at': timezone.now().isoformat()
            }
            
            return trends
            
        except Exception as e:
            logger.error(f'Error generating weather trends: {e}')
            return {'error': str(e)}
    
    def _get_cache_recommendations(self, hit_rate):
        """Get cache optimization recommendations"""
        recommendations = []
        
        if hit_rate < 40:
            recommendations.extend([
                'Consider increasing cache TTL for weather data',
                'Review cache key strategies for better hit rates',
                'Implement cache warming for popular cities'
            ])
        elif hit_rate < 70:
            recommendations.extend([
                'Cache performance is fair - consider optimizing TTL settings',
                'Monitor cache memory usage and adjust as needed'
            ])
        else:
            recommendations.append('Cache performance is good - maintain current settings')
        
        return recommendations
    
    def _get_health_status(self, health_score):
        """Get overall health status based on score"""
        if health_score >= 80:
            return 'Excellent'
        elif health_score >= 60:
            return 'Good'
        elif health_score >= 40:
            return 'Fair'
        elif health_score >= 20:
            return 'Poor'
        else:
            return 'Critical'
    
    def _get_freshness_recommendations(self, freshness_stats, total_cities):
        """Get data freshness recommendations"""
        recommendations = []
        
        stale_percentage = (freshness_stats['stale'] + freshness_stats['very_stale'] + freshness_stats['no_data']) / total_cities * 100 if total_cities > 0 else 0
        
        if stale_percentage > 30:
            recommendations.extend([
                'High percentage of stale data detected',
                'Consider reducing refresh intervals for background tasks',
                'Check API service health and quota limits'
            ])
        elif stale_percentage > 15:
            recommendations.extend([
                'Some cities have stale data',
                'Monitor background refresh tasks',
                'Consider prioritizing popular cities for more frequent updates'
            ])
        else:
            recommendations.append('Data freshness is good across all cities')
        
        if freshness_stats['no_data'] > 0:
            recommendations.append(f'{freshness_stats["no_data"]} cities have no recent data - investigate API issues')
        
        return recommendations


class SystemHealthMonitor:
    """Monitor overall system health and generate alerts"""
    
    def __init__(self):
        self.analytics = WeatherAnalytics()
        self.alert_thresholds = {
            'cache_hit_rate_min': 40,
            'data_freshness_min': 70,
            'api_error_rate_max': 10,
            'stale_data_max': 20
        }
    
    def get_system_health_report(self):
        """Generate comprehensive system health report"""
        try:
            report = {
                'timestamp': timezone.now().isoformat(),
                'overall_status': 'healthy',
                'alerts': [],
                'warnings': [],
                'metrics': {}
            }
            
            # Get analytics data
            api_stats = self.analytics.get_api_usage_stats(24)
            cache_stats = self.analytics.get_cache_performance_stats()
            freshness_stats = self.analytics.get_data_freshness_stats()
            
            # Store metrics
            report['metrics'] = {
                'api_usage': api_stats,
                'cache_performance': cache_stats,
                'data_freshness': freshness_stats
            }
            
            # Check cache performance
            if 'estimated_hit_rate' in cache_stats:
                hit_rate = cache_stats['estimated_hit_rate']
                if hit_rate < self.alert_thresholds['cache_hit_rate_min']:
                    report['alerts'].append({
                        'type': 'cache_performance',
                        'severity': 'high',
                        'message': f'Cache hit rate is low: {hit_rate}%',
                        'recommendation': 'Review cache configuration and TTL settings'
                    })
                elif hit_rate < 60:
                    report['warnings'].append({
                        'type': 'cache_performance',
                        'message': f'Cache hit rate could be improved: {hit_rate}%'
                    })
            
            # Check data freshness
            if 'health_score' in freshness_stats:
                health_score = freshness_stats['health_score']
                if health_score < self.alert_thresholds['data_freshness_min']:
                    report['alerts'].append({
                        'type': 'data_freshness',
                        'severity': 'high',
                        'message': f'Data freshness score is low: {health_score}%',
                        'recommendation': 'Check background refresh tasks and API connectivity'
                    })
                elif health_score < 85:
                    report['warnings'].append({
                        'type': 'data_freshness',
                        'message': f'Data freshness could be improved: {health_score}%'
                    })
            
            # Check for stale data
            if 'freshness_percentages' in freshness_stats:
                stale_percentage = (
                    freshness_stats['freshness_percentages'].get('stale', 0) +
                    freshness_stats['freshness_percentages'].get('very_stale', 0) +
                    freshness_stats['freshness_percentages'].get('no_data', 0)
                )
                
                if stale_percentage > self.alert_thresholds['stale_data_max']:
                    report['alerts'].append({
                        'type': 'stale_data',
                        'severity': 'medium',
                        'message': f'{stale_percentage}% of cities have stale data',
                        'recommendation': 'Investigate API issues and refresh task performance'
                    })
            
            # Determine overall status
            if report['alerts']:
                high_severity_alerts = [a for a in report['alerts'] if a.get('severity') == 'high']
                if high_severity_alerts:
                    report['overall_status'] = 'critical'
                else:
                    report['overall_status'] = 'warning'
            elif report['warnings']:
                report['overall_status'] = 'warning'
            
            return report
            
        except Exception as e:
            logger.error(f'Error generating system health report: {e}')
            return {
                'timestamp': timezone.now().isoformat(),
                'overall_status': 'error',
                'error': str(e)
            }
    
    def check_and_send_alerts(self):
        """Check system health and send alerts if needed"""
        try:
            health_report = self.get_system_health_report()
            
            # Log alerts
            for alert in health_report.get('alerts', []):
                logger.warning(f"System Alert [{alert['type']}]: {alert['message']}")
            
            # Here you could integrate with external alerting systems
            # like email, Slack, PagerDuty, etc.
            
            return health_report
            
        except Exception as e:
            logger.error(f'Error checking system health: {e}')
            return None


# Global instances
weather_analytics = WeatherAnalytics()
health_monitor = SystemHealthMonitor()