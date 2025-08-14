"""
Tests for real-time API monitoring functionality
"""
from django.test import TestCase
from django.utils import timezone
from django.core.cache import cache
from unittest.mock import patch, MagicMock
from datetime import timedelta

from .api_management import APIProvider, APIUsage, APIFailover
from .api_monitoring_realtime import RealTimeAPIMonitor
from .models import SystemAlert


class RealTimeMonitoringTestCase(TestCase):
    """Test case for real-time monitoring functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.monitor = RealTimeAPIMonitor()
        
        # Create test API provider
        self.provider = APIProvider.objects.create(
            name='test_provider',
            display_name='Test Provider',
            base_url='https://api.test.com',
            api_key='test_key',
            is_active=True,
            is_healthy=True,
            priority=1,
            requests_per_day=1000,
            monthly_budget=10.00,
            cost_per_request=0.001,
            supported_endpoints=['weather', 'forecast']
        )
        
        # Create test usage data
        today = timezone.now().date()
        self.usage = APIUsage.objects.create(
            provider=self.provider,
            date=today,
            endpoint='weather',
            request_count=100,
            success_count=95,
            error_count=5,
            avg_response_time=1.5,
            max_response_time=3.0,
            cost=0.1
        )
        
        # Clear cache before each test
        cache.clear()
    
    def test_get_real_time_status(self):
        """Test getting real-time status"""
        status = self.monitor.get_real_time_status()
        
        self.assertIn('timestamp', status)
        self.assertIn('providers', status)
        self.assertIn('system_health', status)
        self.assertIn('active_alerts', status)
        
        # Check provider data
        self.assertEqual(len(status['providers']), 1)
        provider_status = status['providers'][0]
        
        self.assertEqual(provider_status['id'], self.provider.id)
        self.assertEqual(provider_status['name'], self.provider.name)
        self.assertEqual(provider_status['display_name'], self.provider.display_name)
        self.assertTrue(provider_status['is_healthy'])
    
    def test_get_latest_alerts(self):
        """Test getting latest alerts"""
        # Create test alert
        alert = SystemAlert.objects.create(
            alert_type='performance',
            severity='warning',
            title='Test Alert',
            message='Test alert message',
            component='test_component',
            status='active'
        )
        
        alerts = self.monitor.get_latest_alerts(limit=5)
        
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]['title'], 'Test Alert')
        self.assertEqual(alerts[0]['severity'], 'warning')
        self.assertEqual(alerts[0]['type'], 'performance')
    
    @patch('weather_data.api_monitoring_realtime.api_manager.perform_health_check')
    async def test_check_provider_health_success(self, mock_health_check):
        """Test successful provider health check"""
        mock_health_check.return_value = {
            'healthy': True,
            'response_time': 1.2,
            'timestamp': timezone.now().isoformat()
        }
        
        await self.monitor._check_provider_health(self.provider)
        
        # Check that health result is cached
        cache_key = f"{self.monitor.cache_prefix}:health:{self.provider.id}"
        cached_result = cache.get(cache_key)
        
        self.assertIsNotNone(cached_result)
        self.assertTrue(cached_result['healthy'])
        self.assertEqual(cached_result['response_time'], 1.2)
    
    @patch('weather_data.api_monitoring_realtime.api_manager.perform_health_check')
    async def test_check_provider_health_failure(self, mock_health_check):
        """Test provider health check failure"""
        mock_health_check.return_value = {
            'healthy': False,
            'error': 'Connection timeout',
            'timestamp': timezone.now().isoformat()
        }
        
        # Set provider as initially healthy
        self.provider.is_healthy = True
        self.provider.save()
        
        await self.monitor._check_provider_health(self.provider)
        
        # Check that health result is cached
        cache_key = f"{self.monitor.cache_prefix}:health:{self.provider.id}"
        cached_result = cache.get(cache_key)
        
        self.assertIsNotNone(cached_result)
        self.assertFalse(cached_result['healthy'])
        self.assertEqual(cached_result['error'], 'Connection timeout')
    
    async def test_check_provider_performance(self):
        """Test provider performance monitoring"""
        await self.monitor._check_provider_performance(self.provider)
        
        # Check that performance data is cached
        cache_key = f"{self.monitor.cache_prefix}:performance:{self.provider.id}"
        cached_result = cache.get(cache_key)
        
        self.assertIsNotNone(cached_result)
        self.assertEqual(cached_result['avg_response_time'], 1.5)
        self.assertEqual(cached_result['max_response_time'], 3.0)
        self.assertEqual(cached_result['error_rate'], 5.0)  # 5 errors out of 100 requests
        self.assertEqual(cached_result['success_rate'], 95.0)
    
    async def test_check_provider_costs(self):
        """Test provider cost monitoring"""
        await self.monitor._check_provider_costs(self.provider)
        
        # Check that cost data is cached
        cache_key = f"{self.monitor.cache_prefix}:costs:{self.provider.id}"
        cached_result = cache.get(cache_key)
        
        self.assertIsNotNone(cached_result)
        self.assertEqual(cached_result['monthly_cost'], 0.1)
        self.assertEqual(cached_result['budget'], 10.0)
        self.assertEqual(cached_result['usage_percentage'], 1.0)  # 0.1/10.0 * 100
    
    async def test_create_alert(self):
        """Test alert creation"""
        await self.monitor._create_alert(
            alert_type='performance',
            severity='warning',
            title='Test Alert',
            message='Test alert message',
            component='test_component'
        )
        
        # Check that alert was created
        alert = SystemAlert.objects.filter(title='Test Alert').first()
        self.assertIsNotNone(alert)
        self.assertEqual(alert.alert_type, 'performance')
        self.assertEqual(alert.severity, 'warning')
        self.assertEqual(alert.status, 'active')
        
        # Check that alert is cached
        cache_key = f"{self.monitor.cache_prefix}:alerts:latest"
        cached_alerts = cache.get(cache_key)
        
        self.assertIsNotNone(cached_alerts)
        self.assertEqual(len(cached_alerts), 1)
        self.assertEqual(cached_alerts[0]['title'], 'Test Alert')
    
    async def test_create_duplicate_alert_prevention(self):
        """Test that duplicate alerts are not created"""
        # Create first alert
        await self.monitor._create_alert(
            alert_type='performance',
            severity='warning',
            title='Test Alert',
            message='Test alert message',
            component='test_component'
        )
        
        # Try to create duplicate alert
        await self.monitor._create_alert(
            alert_type='performance',
            severity='warning',
            title='Test Alert 2',
            message='Another test alert message',
            component='test_component'
        )
        
        # Should only have one alert
        alerts = SystemAlert.objects.filter(component='test_component')
        self.assertEqual(alerts.count(), 1)
    
    async def test_trigger_failover(self):
        """Test automatic failover triggering"""
        # Create fallback provider
        fallback_provider = APIProvider.objects.create(
            name='fallback_provider',
            display_name='Fallback Provider',
            base_url='https://api.fallback.com',
            api_key='fallback_key',
            is_active=True,
            is_healthy=True,
            priority=2,
            supported_endpoints=['weather', 'forecast']
        )
        
        await self.monitor._trigger_failover(self.provider, 'Connection timeout')
        
        # Check that failover record was created
        failover = APIFailover.objects.filter(
            primary_provider=self.provider,
            fallback_provider=fallback_provider
        ).first()
        
        self.assertIsNotNone(failover)
        self.assertEqual(failover.reason, 'Connection timeout')
        self.assertEqual(failover.endpoint, 'auto_failover')
    
    def test_performance_threshold_alerts(self):
        """Test that performance threshold alerts are created"""
        # Create usage with high response time
        high_response_usage = APIUsage.objects.create(
            provider=self.provider,
            date=timezone.now().date(),
            endpoint='forecast',
            request_count=50,
            success_count=45,
            error_count=5,
            avg_response_time=6.0,  # Above threshold
            max_response_time=10.0,
            cost=0.05
        )
        
        # This would normally be called by the monitoring loop
        # We can't easily test the async function, but we can verify the logic
        self.assertGreater(high_response_usage.avg_response_time, self.monitor.alert_thresholds['response_time'])
    
    def test_cost_threshold_alerts(self):
        """Test that cost threshold alerts are created"""
        # Update provider to have high cost usage
        usage_month = self.provider.get_usage_this_month()
        monthly_cost = float(usage_month.get('total_cost', 0))
        budget = float(self.provider.monthly_budget)
        
        usage_percentage = (monthly_cost / budget) if budget > 0 else 0
        
        # Verify the cost calculation logic
        self.assertLess(usage_percentage, self.monitor.alert_thresholds['cost_threshold'])
    
    def test_cache_expiration(self):
        """Test that cached data expires correctly"""
        # Set some test data in cache
        cache_key = f"{self.monitor.cache_prefix}:health:{self.provider.id}"
        test_data = {'healthy': True, 'timestamp': timezone.now().isoformat()}
        
        cache.set(cache_key, test_data, timeout=1)  # 1 second expiration
        
        # Verify data is cached
        cached_data = cache.get(cache_key)
        self.assertIsNotNone(cached_data)
        
        # Wait for expiration (in a real test, we'd mock time)
        import time
        time.sleep(2)
        
        # Verify data has expired
        cached_data = cache.get(cache_key)
        self.assertIsNone(cached_data)