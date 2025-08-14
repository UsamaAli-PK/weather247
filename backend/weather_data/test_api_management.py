"""
Tests for API Integration Management
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .api_management import APIProvider, APIUsage, APIFailover, api_manager


class APIManagementTestCase(TestCase):
    """Test cases for API management functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.provider = APIProvider.objects.create(
            name='test_provider',
            display_name='Test Provider',
            base_url='https://api.test.com',
            api_key='test_key',
            is_active=True,
            priority=1,
            requests_per_day=100,
            cost_per_request=Decimal('0.001'),
            supported_endpoints=['weather', 'forecast']
        )
    
    def test_provider_creation(self):
        """Test API provider creation"""
        self.assertEqual(self.provider.name, 'test_provider')
        self.assertTrue(self.provider.is_active)
        self.assertTrue(self.provider.is_healthy)
        self.assertEqual(self.provider.success_rate, 100.0)
    
    def test_usage_tracking(self):
        """Test API usage tracking"""
        today = timezone.now().date()
        
        usage = APIUsage.objects.create(
            provider=self.provider,
            date=today,
            endpoint='weather',
            request_count=10,
            success_count=9,
            error_count=1,
            avg_response_time=0.5,
            cost=Decimal('0.01')
        )
        
        self.assertEqual(usage.request_count, 10)
        self.assertEqual(usage.success_count, 9)
        self.assertEqual(usage.error_count, 1)
    
    def test_get_usage_today(self):
        """Test getting today's usage"""
        today = timezone.now().date()
        
        APIUsage.objects.create(
            provider=self.provider,
            date=today,
            endpoint='weather',
            request_count=50,
            success_count=50,
            error_count=0
        )
        
        usage_today = self.provider.get_usage_today()
        self.assertEqual(usage_today, 50)
    
    def test_can_make_request(self):
        """Test request rate limiting"""
        # Provider should be able to make requests initially
        self.assertTrue(self.provider.can_make_request())
        
        # Create usage that exceeds daily limit
        today = timezone.now().date()
        APIUsage.objects.create(
            provider=self.provider,
            date=today,
            endpoint='weather',
            request_count=150,  # Exceeds daily limit of 100
            success_count=150,
            error_count=0
        )
        
        # Provider should not be able to make requests now
        self.assertFalse(self.provider.can_make_request())
    
    def test_health_status_update(self):
        """Test provider health status updates"""
        # Update with success
        self.provider.update_health_status(True)
        self.assertTrue(self.provider.is_healthy)
        
        # Update with multiple failures
        for _ in range(15):
            self.provider.update_health_status(False)
        
        # Provider should be unhealthy now
        self.assertFalse(self.provider.is_healthy)
    
    def test_failover_creation(self):
        """Test failover event creation"""
        fallback_provider = APIProvider.objects.create(
            name='fallback_provider',
            display_name='Fallback Provider',
            base_url='https://api.fallback.com',
            is_active=True,
            priority=2
        )
        
        failover = APIFailover.objects.create(
            primary_provider=self.provider,
            fallback_provider=fallback_provider,
            reason='Connection timeout',
            endpoint='weather',
            error_details='Request timed out after 30 seconds'
        )
        
        self.assertEqual(failover.primary_provider, self.provider)
        self.assertEqual(failover.fallback_provider, fallback_provider)
        self.assertIsNone(failover.resolved_at)
    
    def test_api_manager_get_active_providers(self):
        """Test getting active providers"""
        # Create another provider
        APIProvider.objects.create(
            name='inactive_provider',
            display_name='Inactive Provider',
            base_url='https://api.inactive.com',
            is_active=False,
            priority=2
        )
        
        active_providers = api_manager.get_active_providers()
        self.assertEqual(len(active_providers), 1)
        self.assertEqual(active_providers[0], self.provider)
    
    def test_api_manager_get_primary_provider(self):
        """Test getting primary provider"""
        primary = api_manager.get_primary_provider('weather')
        self.assertEqual(primary, self.provider)
        
        # Test with unsupported endpoint
        primary = api_manager.get_primary_provider('unsupported')
        self.assertIsNone(primary)
    
    def test_provider_statistics(self):
        """Test getting provider statistics"""
        # Create some usage data
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        APIUsage.objects.create(
            provider=self.provider,
            date=today,
            endpoint='weather',
            request_count=50,
            success_count=48,
            error_count=2,
            avg_response_time=0.5,
            cost=Decimal('0.05')
        )
        
        APIUsage.objects.create(
            provider=self.provider,
            date=yesterday,
            endpoint='forecast',
            request_count=30,
            success_count=30,
            error_count=0,
            avg_response_time=0.3,
            cost=Decimal('0.03')
        )
        
        stats = api_manager.get_provider_statistics(self.provider.id, days=7)
        
        self.assertEqual(stats['provider']['id'], self.provider.id)
        self.assertEqual(stats['usage']['total_requests'], 80)
        self.assertEqual(stats['usage']['total_success'], 78)
        self.assertEqual(stats['usage']['total_errors'], 2)
        self.assertEqual(stats['usage']['success_rate'], 97.5)
    
    def test_cost_analysis(self):
        """Test cost analysis functionality"""
        # Create usage data with costs
        today = timezone.now().date()
        
        APIUsage.objects.create(
            provider=self.provider,
            date=today,
            endpoint='weather',
            request_count=100,
            success_count=100,
            error_count=0,
            cost=Decimal('0.10')
        )
        
        cost_analysis = api_manager.get_cost_analysis(days=7)
        
        self.assertEqual(cost_analysis['totals']['total_requests'], 100)
        self.assertEqual(float(cost_analysis['totals']['total_cost']), 0.10)
        self.assertEqual(len(cost_analysis['provider_breakdown']), 1)
        self.assertEqual(cost_analysis['provider_breakdown'][0]['provider'], 'test_provider')
    
    def tearDown(self):
        """Clean up test data"""
        APIProvider.objects.all().delete()
        APIUsage.objects.all().delete()
        APIFailover.objects.all().delete()