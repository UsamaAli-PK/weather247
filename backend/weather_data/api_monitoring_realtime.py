"""
Real-time API monitoring and alerting system
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from typing import Dict, List, Optional

from .api_management import APIProvider, APIUsage, APIFailover, api_manager
from .models import SystemAlert

logger = logging.getLogger('weather247')


class RealTimeAPIMonitor:
    """Real-time monitoring system for API providers"""
    
    def __init__(self):
        self.monitoring_interval = 30  # seconds
        self.alert_thresholds = {
            'response_time': 5.0,  # seconds
            'error_rate': 10.0,    # percentage
            'success_rate': 80.0,  # percentage
            'cost_threshold': 0.8  # 80% of budget
        }
        self.cache_prefix = 'api_monitor'
        
    def start_monitoring(self):
        """Start the real-time monitoring loop"""
        logger.info("Starting real-time API monitoring")
        asyncio.create_task(self._monitoring_loop())
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                await self._check_all_providers()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _check_all_providers(self):
        """Check all active providers"""
        providers = APIProvider.objects.filter(is_active=True)
        
        for provider in providers:
            try:
                await self._check_provider_health(provider)
                await self._check_provider_performance(provider)
                await self._check_provider_costs(provider)
            except Exception as e:
                logger.error(f"Error checking provider {provider.name}: {str(e)}")
    
    async def _check_provider_health(self, provider: APIProvider):
        """Check provider health and create alerts if needed"""
        try:
            # Perform health check
            health_result = api_manager.perform_health_check(provider)
            
            # Cache the result for real-time dashboard
            cache_key = f"{self.cache_prefix}:health:{provider.id}"
            cache.set(cache_key, health_result, timeout=60)
            
            # Check if provider became unhealthy
            if not health_result['healthy'] and provider.is_healthy:
                await self._create_alert(
                    alert_type='api_failure',
                    severity='error',
                    title=f'API Provider {provider.display_name} Failed',
                    message=f'Health check failed: {health_result.get("error", "Unknown error")}',
                    component=f'api_provider_{provider.id}',
                    error_details=health_result
                )
                
                # Trigger automatic failover if needed
                await self._trigger_failover(provider, health_result.get('error', 'Health check failed'))
            
            # Check if provider recovered
            elif health_result['healthy'] and not provider.is_healthy:
                await self._create_alert(
                    alert_type='api_failure',
                    severity='info',
                    title=f'API Provider {provider.display_name} Recovered',
                    message=f'Health check passed. Provider is back online.',
                    component=f'api_provider_{provider.id}'
                )
                
        except Exception as e:
            logger.error(f"Error in health check for {provider.name}: {str(e)}")
    
    async def _check_provider_performance(self, provider: APIProvider):
        """Check provider performance metrics"""
        try:
            # Get recent usage statistics
            today = timezone.now().date()
            recent_usage = APIUsage.objects.filter(
                provider=provider,
                date__gte=today - timedelta(days=1)
            ).first()
            
            if not recent_usage:
                return
            
            # Check response time
            if recent_usage.avg_response_time > self.alert_thresholds['response_time']:
                await self._create_alert(
                    alert_type='performance',
                    severity='warning',
                    title=f'High Response Time - {provider.display_name}',
                    message=f'Average response time: {recent_usage.avg_response_time:.2f}s (threshold: {self.alert_thresholds["response_time"]}s)',
                    component=f'api_provider_{provider.id}',
                    metric_value=recent_usage.avg_response_time,
                    threshold_value=self.alert_thresholds['response_time']
                )
            
            # Check error rate
            if recent_usage.request_count > 0:
                error_rate = (recent_usage.error_count / recent_usage.request_count) * 100
                if error_rate > self.alert_thresholds['error_rate']:
                    await self._create_alert(
                        alert_type='performance',
                        severity='warning',
                        title=f'High Error Rate - {provider.display_name}',
                        message=f'Error rate: {error_rate:.1f}% (threshold: {self.alert_thresholds["error_rate"]}%)',
                        component=f'api_provider_{provider.id}',
                        metric_value=error_rate,
                        threshold_value=self.alert_thresholds['error_rate']
                    )
            
            # Cache performance metrics
            cache_key = f"{self.cache_prefix}:performance:{provider.id}"
            performance_data = {
                'avg_response_time': recent_usage.avg_response_time,
                'max_response_time': recent_usage.max_response_time,
                'error_rate': (recent_usage.error_count / max(recent_usage.request_count, 1)) * 100,
                'success_rate': ((recent_usage.request_count - recent_usage.error_count) / max(recent_usage.request_count, 1)) * 100,
                'timestamp': timezone.now().isoformat()
            }
            cache.set(cache_key, performance_data, timeout=60)
            
        except Exception as e:
            logger.error(f"Error checking performance for {provider.name}: {str(e)}")
    
    async def _check_provider_costs(self, provider: APIProvider):
        """Check provider cost thresholds"""
        try:
            if provider.monthly_budget <= 0:
                return
            
            usage_month = provider.get_usage_this_month()
            monthly_cost = float(usage_month.get('total_cost', 0))
            budget = float(provider.monthly_budget)
            
            usage_percentage = (monthly_cost / budget) if budget > 0 else 0
            
            # Check cost thresholds
            if usage_percentage >= 0.95:  # 95% of budget
                await self._create_alert(
                    alert_type='capacity',
                    severity='critical',
                    title=f'Budget Almost Exceeded - {provider.display_name}',
                    message=f'Used {usage_percentage:.1f}% of monthly budget (${monthly_cost:.2f}/${budget:.2f})',
                    component=f'api_provider_{provider.id}',
                    metric_value=usage_percentage * 100,
                    threshold_value=95.0
                )
            elif usage_percentage >= self.alert_thresholds['cost_threshold']:
                await self._create_alert(
                    alert_type='capacity',
                    severity='warning',
                    title=f'Budget Warning - {provider.display_name}',
                    message=f'Used {usage_percentage:.1f}% of monthly budget (${monthly_cost:.2f}/${budget:.2f})',
                    component=f'api_provider_{provider.id}',
                    metric_value=usage_percentage * 100,
                    threshold_value=self.alert_thresholds['cost_threshold'] * 100
                )
            
            # Cache cost data
            cache_key = f"{self.cache_prefix}:costs:{provider.id}"
            cost_data = {
                'monthly_cost': monthly_cost,
                'budget': budget,
                'usage_percentage': usage_percentage * 100,
                'timestamp': timezone.now().isoformat()
            }
            cache.set(cache_key, cost_data, timeout=300)  # 5 minutes
            
        except Exception as e:
            logger.error(f"Error checking costs for {provider.name}: {str(e)}")
    
    async def _trigger_failover(self, failed_provider: APIProvider, error_reason: str):
        """Trigger automatic failover to backup provider"""
        try:
            # Find the best fallback provider
            fallback_providers = APIProvider.objects.filter(
                is_active=True,
                is_healthy=True,
                priority__gt=failed_provider.priority
            ).order_by('priority')
            
            if not fallback_providers.exists():
                logger.warning(f"No fallback providers available for {failed_provider.name}")
                return
            
            fallback_provider = fallback_providers.first()
            
            # Create failover record
            failover = APIFailover.objects.create(
                primary_provider=failed_provider,
                fallback_provider=fallback_provider,
                reason=error_reason,
                endpoint='auto_failover',
                error_details=f'Automatic failover triggered by monitoring system'
            )
            
            logger.info(f"Automatic failover triggered: {failed_provider.name} → {fallback_provider.name}")
            
            # Create alert for failover
            await self._create_alert(
                alert_type='api_failure',
                severity='warning',
                title=f'Automatic Failover Triggered',
                message=f'Failed over from {failed_provider.display_name} to {fallback_provider.display_name}',
                component='api_system',
                error_details={'failover_id': failover.id}
            )
            
        except Exception as e:
            logger.error(f"Error triggering failover for {failed_provider.name}: {str(e)}")
    
    async def _create_alert(self, alert_type: str, severity: str, title: str, 
                          message: str, component: str, **kwargs):
        """Create system alert"""
        try:
            # Check if similar alert already exists (avoid spam)
            existing_alert = SystemAlert.objects.filter(
                alert_type=alert_type,
                component=component,
                status='active',
                created_at__gte=timezone.now() - timedelta(minutes=10)
            ).first()
            
            if existing_alert:
                return  # Don't create duplicate alerts
            
            alert = SystemAlert.objects.create(
                alert_type=alert_type,
                severity=severity,
                title=title,
                message=message,
                component=component,
                metric_value=kwargs.get('metric_value'),
                threshold_value=kwargs.get('threshold_value'),
                error_details=kwargs.get('error_details', {})
            )
            
            logger.info(f"Created alert: {title}")
            
            # Cache alert for real-time dashboard
            cache_key = f"{self.cache_prefix}:alerts:latest"
            latest_alerts = cache.get(cache_key, [])
            latest_alerts.insert(0, {
                'id': alert.id,
                'type': alert_type,
                'severity': severity,
                'title': title,
                'message': message,
                'component': component,
                'created_at': alert.created_at.isoformat()
            })
            
            # Keep only last 10 alerts in cache
            latest_alerts = latest_alerts[:10]
            cache.set(cache_key, latest_alerts, timeout=3600)  # 1 hour
            
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")
    
    def get_real_time_status(self) -> Dict:
        """Get current real-time status of all providers"""
        try:
            providers = APIProvider.objects.filter(is_active=True)
            status = {
                'timestamp': timezone.now().isoformat(),
                'providers': [],
                'system_health': 'healthy',
                'active_alerts': 0
            }
            
            for provider in providers:
                # Get cached data
                health_key = f"{self.cache_prefix}:health:{provider.id}"
                performance_key = f"{self.cache_prefix}:performance:{provider.id}"
                cost_key = f"{self.cache_prefix}:costs:{provider.id}"
                
                health_data = cache.get(health_key, {})
                performance_data = cache.get(performance_key, {})
                cost_data = cache.get(cost_key, {})
                
                provider_status = {
                    'id': provider.id,
                    'name': provider.name,
                    'display_name': provider.display_name,
                    'is_healthy': health_data.get('healthy', provider.is_healthy),
                    'health_check_time': health_data.get('timestamp'),
                    'response_time': performance_data.get('avg_response_time', 0),
                    'error_rate': performance_data.get('error_rate', 0),
                    'success_rate': performance_data.get('success_rate', 100),
                    'cost_usage': cost_data.get('usage_percentage', 0),
                    'monthly_cost': cost_data.get('monthly_cost', 0),
                    'budget': cost_data.get('budget', 0)
                }
                
                status['providers'].append(provider_status)
                
                # Update system health
                if not provider_status['is_healthy']:
                    status['system_health'] = 'degraded'
            
            # Get active alerts count
            active_alerts = SystemAlert.objects.filter(status='active').count()
            status['active_alerts'] = active_alerts
            
            if active_alerts > 0:
                status['system_health'] = 'warning' if status['system_health'] == 'healthy' else status['system_health']
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting real-time status: {str(e)}")
            return {
                'timestamp': timezone.now().isoformat(),
                'error': str(e),
                'system_health': 'unknown'
            }
    
    def get_latest_alerts(self, limit: int = 10) -> List[Dict]:
        """Get latest system alerts"""
        try:
            cache_key = f"{self.cache_prefix}:alerts:latest"
            cached_alerts = cache.get(cache_key, [])
            
            if cached_alerts:
                return cached_alerts[:limit]
            
            # Fallback to database
            alerts = SystemAlert.objects.filter(
                status__in=['active', 'acknowledged']
            ).order_by('-created_at')[:limit]
            
            alert_data = []
            for alert in alerts:
                alert_data.append({
                    'id': alert.id,
                    'type': alert.alert_type,
                    'severity': alert.severity,
                    'title': alert.title,
                    'message': alert.message,
                    'component': alert.component,
                    'created_at': alert.created_at.isoformat(),
                    'status': alert.status
                })
            
            return alert_data
            
        except Exception as e:
            logger.error(f"Error getting latest alerts: {str(e)}")
            return []


# Global instance
real_time_monitor = RealTimeAPIMonitor()