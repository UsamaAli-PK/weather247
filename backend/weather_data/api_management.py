"""
API Integration Management System
"""
import logging
import requests
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from django.db import models
from django.conf import settings
from typing import Dict, List, Optional, Any
import json

logger = logging.getLogger('weather247')


class APIProvider(models.Model):
    """Model for API provider configuration"""
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100)
    base_url = models.URLField()
    api_key = models.CharField(max_length=200, blank=True)
    
    # Configuration
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    priority = models.IntegerField(default=1, help_text="Lower number = higher priority")
    
    # Rate limiting
    requests_per_minute = models.IntegerField(default=60)
    requests_per_day = models.IntegerField(default=1000)
    requests_per_month = models.IntegerField(default=100000)
    
    # Cost tracking
    cost_per_request = models.DecimalField(max_digits=10, decimal_places=6, default=0.0)
    monthly_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    
    # Health monitoring
    last_health_check = models.DateTimeField(null=True, blank=True)
    is_healthy = models.BooleanField(default=True)
    error_count = models.IntegerField(default=0)
    success_rate = models.FloatField(default=100.0)
    
    # Metadata
    supported_endpoints = models.JSONField(default=list)
    configuration = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['priority', 'name']
        verbose_name = 'API Provider'
        verbose_name_plural = 'API Providers'
    
    def __str__(self):
        return f"{self.display_name} ({'Active' if self.is_active else 'Inactive'})"
    
    def get_usage_today(self):
        """Get API usage for today"""
        today = timezone.now().date()
        return APIUsage.objects.filter(
            provider=self,
            date=today
        ).aggregate(
            total_requests=models.Sum('request_count')
        )['total_requests'] or 0
    
    def get_usage_this_month(self):
        """Get API usage for current month"""
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return APIUsage.objects.filter(
            provider=self,
            date__gte=month_start.date()
        ).aggregate(
            total_requests=models.Sum('request_count'),
            total_cost=models.Sum('cost')
        )
    
    def can_make_request(self):
        """Check if provider can make request based on rate limits"""
        if not self.is_active or not self.is_healthy:
            return False
        
        # Check daily limit
        usage_today = self.get_usage_today()
        if usage_today >= self.requests_per_day:
            return False
        
        # Check monthly budget
        usage_month = self.get_usage_this_month()
        if usage_month['total_cost'] and usage_month['total_cost'] >= self.monthly_budget:
            return False
        
        return True
    
    def update_health_status(self, success: bool):
        """Update provider health status"""
        if success:
            self.error_count = max(0, self.error_count - 1)
        else:
            self.error_count += 1
        
        # Calculate success rate based on recent requests
        recent_usage = APIUsage.objects.filter(
            provider=self,
            date__gte=timezone.now().date() - timedelta(days=7)
        ).aggregate(
            total_requests=models.Sum('request_count'),
            total_errors=models.Sum('error_count')
        )
        
        total_requests = recent_usage['total_requests'] or 0
        total_errors = recent_usage['total_errors'] or 0
        
        if total_requests > 0:
            self.success_rate = ((total_requests - total_errors) / total_requests) * 100
        
        # Update health status
        self.is_healthy = self.success_rate >= 80 and self.error_count < 10
        self.last_health_check = timezone.now()
        self.save(update_fields=['error_count', 'success_rate', 'is_healthy', 'last_health_check'])


class APIUsage(models.Model):
    """Model for tracking API usage and costs"""
    provider = models.ForeignKey(APIProvider, on_delete=models.CASCADE, related_name='usage_records')
    date = models.DateField()
    endpoint = models.CharField(max_length=200)
    
    # Usage statistics
    request_count = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    
    # Performance metrics
    avg_response_time = models.FloatField(default=0.0)
    max_response_time = models.FloatField(default=0.0)
    
    # Cost tracking
    cost = models.DecimalField(max_digits=10, decimal_places=6, default=0.0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['provider', 'date', 'endpoint']
        verbose_name = 'API Usage'
        verbose_name_plural = 'API Usage Records'
    
    def __str__(self):
        return f"{self.provider.name} - {self.endpoint} - {self.date}"


class APIFailover(models.Model):
    """Model for API failover events"""
    primary_provider = models.ForeignKey(
        APIProvider, 
        on_delete=models.CASCADE, 
        related_name='failover_events_as_primary'
    )
    fallback_provider = models.ForeignKey(
        APIProvider, 
        on_delete=models.CASCADE, 
        related_name='failover_events_as_fallback'
    )
    
    reason = models.CharField(max_length=200)
    endpoint = models.CharField(max_length=200)
    error_details = models.TextField(blank=True)
    
    # Timing
    failed_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'API Failover Event'
        verbose_name_plural = 'API Failover Events'
        ordering = ['-failed_at']
    
    def __str__(self):
        return f"Failover: {self.primary_provider.name} → {self.fallback_provider.name}"


class APIIntegrationManager:
    """Manager for API integrations with failover and monitoring"""
    
    def __init__(self):
        self.cache_timeout = 300  # 5 minutes
    
    def get_active_providers(self) -> List[APIProvider]:
        """Get all active API providers ordered by priority"""
        return APIProvider.objects.filter(is_active=True).order_by('priority')
    
    def get_primary_provider(self, endpoint: str = None) -> Optional[APIProvider]:
        """Get the primary provider for an endpoint"""
        providers = self.get_active_providers()
        
        if endpoint:
            # Filter providers that support the endpoint
            providers = [p for p in providers if endpoint in p.supported_endpoints]
        
        for provider in providers:
            if provider.can_make_request():
                return provider
        
        return None
    
    def make_request(self, endpoint: str, params: Dict = None, provider: APIProvider = None) -> Dict:
        """Make API request with automatic failover"""
        if not provider:
            provider = self.get_primary_provider(endpoint)
        
        if not provider:
            raise Exception("No available API providers")
        
        start_time = timezone.now()
        
        try:
            # Prepare request
            url = f"{provider.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            headers = self._get_headers(provider)
            request_params = self._prepare_params(provider, params or {})
            
            # Make request
            response = requests.get(url, params=request_params, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Calculate response time
            response_time = (timezone.now() - start_time).total_seconds()
            
            # Track successful request
            self._track_usage(provider, endpoint, True, response_time)
            provider.update_health_status(True)
            
            return {
                'success': True,
                'data': response.json(),
                'provider': provider.name,
                'response_time': response_time
            }
            
        except Exception as e:
            # Calculate response time
            response_time = (timezone.now() - start_time).total_seconds()
            
            # Track failed request
            self._track_usage(provider, endpoint, False, response_time)
            provider.update_health_status(False)
            
            logger.error(f"API request failed for {provider.name}: {str(e)}")
            
            # Try failover
            return self._attempt_failover(endpoint, params, provider, str(e))
    
    def _attempt_failover(self, endpoint: str, params: Dict, failed_provider: APIProvider, error: str) -> Dict:
        """Attempt failover to another provider"""
        providers = self.get_active_providers()
        
        for provider in providers:
            if provider.id == failed_provider.id:
                continue
            
            if endpoint not in provider.supported_endpoints:
                continue
            
            if not provider.can_make_request():
                continue
            
            try:
                # Log failover event
                APIFailover.objects.create(
                    primary_provider=failed_provider,
                    fallback_provider=provider,
                    reason=error,
                    endpoint=endpoint,
                    error_details=error
                )
                
                logger.info(f"Attempting failover from {failed_provider.name} to {provider.name}")
                
                # Make request with fallback provider
                result = self.make_request(endpoint, params, provider)
                result['failover'] = True
                result['original_provider'] = failed_provider.name
                
                return result
                
            except Exception as e:
                logger.error(f"Failover to {provider.name} also failed: {str(e)}")
                continue
        
        # All providers failed
        raise Exception(f"All API providers failed for endpoint: {endpoint}")
    
    def _get_headers(self, provider: APIProvider) -> Dict:
        """Get headers for API request"""
        headers = {
            'User-Agent': 'Weather247/1.0',
            'Accept': 'application/json'
        }
        
        # Add API key based on provider configuration
        if provider.api_key:
            if provider.name.lower() == 'openweathermap':
                # OpenWeatherMap uses query parameter
                pass
            elif provider.name.lower() == 'weatherapi':
                headers['X-API-Key'] = provider.api_key
            else:
                headers['Authorization'] = f'Bearer {provider.api_key}'
        
        return headers
    
    def _prepare_params(self, provider: APIProvider, params: Dict) -> Dict:
        """Prepare parameters for API request"""
        request_params = params.copy()
        
        # Add API key if needed
        if provider.api_key and provider.name.lower() == 'openweathermap':
            request_params['appid'] = provider.api_key
        
        # Add provider-specific parameters
        config = provider.configuration
        if config:
            request_params.update(config.get('default_params', {}))
        
        return request_params
    
    def _track_usage(self, provider: APIProvider, endpoint: str, success: bool, response_time: float):
        """Track API usage for analytics and billing"""
        today = timezone.now().date()
        
        usage, created = APIUsage.objects.get_or_create(
            provider=provider,
            date=today,
            endpoint=endpoint,
            defaults={
                'request_count': 0,
                'success_count': 0,
                'error_count': 0,
                'avg_response_time': 0.0,
                'max_response_time': 0.0,
                'cost': 0.0
            }
        )
        
        # Update usage statistics
        usage.request_count += 1
        if success:
            usage.success_count += 1
        else:
            usage.error_count += 1
        
        # Update response time metrics
        if usage.request_count == 1:
            usage.avg_response_time = response_time
        else:
            usage.avg_response_time = (
                (usage.avg_response_time * (usage.request_count - 1) + response_time) / 
                usage.request_count
            )
        
        usage.max_response_time = max(usage.max_response_time, response_time)
        
        # Update cost
        usage.cost += provider.cost_per_request
        
        usage.save()
    
    def get_provider_statistics(self, provider_id: int, days: int = 30) -> Dict:
        """Get comprehensive statistics for a provider"""
        provider = APIProvider.objects.get(id=provider_id)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        usage_records = APIUsage.objects.filter(
            provider=provider,
            date__gte=start_date,
            date__lte=end_date
        )
        
        # Aggregate statistics
        stats = usage_records.aggregate(
            total_requests=models.Sum('request_count'),
            total_success=models.Sum('success_count'),
            total_errors=models.Sum('error_count'),
            total_cost=models.Sum('cost'),
            avg_response_time=models.Avg('avg_response_time'),
            max_response_time=models.Max('max_response_time')
        )
        
        # Calculate derived metrics
        total_requests = stats['total_requests'] or 0
        total_errors = stats['total_errors'] or 0
        
        success_rate = 0
        if total_requests > 0:
            success_rate = ((total_requests - total_errors) / total_requests) * 100
        
        # Get daily breakdown
        daily_usage = []
        for record in usage_records.order_by('date'):
            daily_usage.append({
                'date': record.date.isoformat(),
                'requests': record.request_count,
                'errors': record.error_count,
                'cost': float(record.cost),
                'avg_response_time': record.avg_response_time
            })
        
        # Get recent failover events
        recent_failovers = APIFailover.objects.filter(
            primary_provider=provider,
            failed_at__gte=timezone.now() - timedelta(days=days)
        ).count()
        
        return {
            'provider': {
                'id': provider.id,
                'name': provider.name,
                'display_name': provider.display_name,
                'is_active': provider.is_active,
                'is_healthy': provider.is_healthy,
                'priority': provider.priority
            },
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'usage': {
                'total_requests': total_requests,
                'total_success': stats['total_success'] or 0,
                'total_errors': total_errors,
                'success_rate': round(success_rate, 2),
                'total_cost': float(stats['total_cost'] or 0),
                'avg_response_time': round(stats['avg_response_time'] or 0, 3),
                'max_response_time': round(stats['max_response_time'] or 0, 3)
            },
            'daily_usage': daily_usage,
            'failover_events': recent_failovers,
            'health_status': {
                'is_healthy': provider.is_healthy,
                'last_check': provider.last_health_check.isoformat() if provider.last_health_check else None,
                'error_count': provider.error_count,
                'success_rate': provider.success_rate
            }
        }
    
    def perform_health_check(self, provider: APIProvider) -> Dict:
        """Perform health check on a provider"""
        try:
            # Make a simple test request
            test_endpoint = provider.supported_endpoints[0] if provider.supported_endpoints else 'health'
            result = self.make_request(test_endpoint, {'test': True}, provider)
            
            return {
                'provider': provider.name,
                'healthy': True,
                'response_time': result.get('response_time', 0),
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            return {
                'provider': provider.name,
                'healthy': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
    
    def get_cost_analysis(self, days: int = 30) -> Dict:
        """Get cost analysis across all providers"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get usage for all providers
        usage_records = APIUsage.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        )
        
        # Aggregate by provider
        provider_costs = usage_records.values('provider__name', 'provider__display_name').annotate(
            total_requests=models.Sum('request_count'),
            total_cost=models.Sum('cost'),
            avg_cost_per_request=models.Avg('cost')
        ).order_by('-total_cost')
        
        # Calculate totals
        totals = usage_records.aggregate(
            total_requests=models.Sum('request_count'),
            total_cost=models.Sum('cost')
        )
        
        # Get daily cost breakdown
        daily_costs = usage_records.values('date').annotate(
            total_cost=models.Sum('cost'),
            total_requests=models.Sum('request_count')
        ).order_by('date')
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'totals': {
                'total_requests': totals['total_requests'] or 0,
                'total_cost': float(totals['total_cost'] or 0),
                'avg_cost_per_request': float(totals['total_cost'] or 0) / max(totals['total_requests'] or 1, 1)
            },
            'provider_breakdown': [
                {
                    'provider': item['provider__name'],
                    'display_name': item['provider__display_name'],
                    'requests': item['total_requests'],
                    'cost': float(item['total_cost']),
                    'avg_cost_per_request': float(item['avg_cost_per_request'] or 0)
                }
                for item in provider_costs
            ],
            'daily_costs': [
                {
                    'date': item['date'].isoformat(),
                    'cost': float(item['total_cost']),
                    'requests': item['total_requests']
                }
                for item in daily_costs
            ]
        }


# Global instance
api_manager = APIIntegrationManager()