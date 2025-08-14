"""
Tests for system monitoring functionality
"""
from django.test import TestCase, Client
from accounts.models import User
from django.utils import timezone
from django.core.cache import cache
from unittest.mock import patch, MagicMock
from datetime import timedelta
import json

from .system_monitoring_core import SystemMonitor, SystemDiagnostics
from .models import SystemMetrics, SystemAlert, SystemHealthCheck
from .celery_monitoring_tasks import (
    collect_system_metrics_periodic,
    perform_health_checks_periodic,
    cleanup_old_monitoring_data
)


class SystemMonitoringTestCase(TestCase):
    """Test case for system monitoring functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.monitor = SystemMonitor()
        self.diagnostics = SystemDiagnostics()
        
        # Create admin user for API tests
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.client = Client()
        self.client.force_login(self.admin_user)
        
        # Clear cache before each test
        cache.clear()
    
    def test_collect_system_metrics(self):
        """Test system metrics collection"""
        metrics = self.monitor.collect_system_metrics()
        
        # Check that all expected metric categories are present
        expected_categories = ['cpu', 'memory', 'disk', 'database', 'cache']
        
        for category in expected_categories:
            self.assertIn(category, metrics)
        
        # Check CPU metrics structure
        cpu_metrics = metrics['cpu']
        self.assertIn('usage_percent', cpu_metrics)
        self.assertIn('core_count', cpu_metrics)
        self.assertIsInstance(cpu_metrics['usage_percent'], (int, float))
        self.assertGreaterEqual(cpu_metrics['usage_percent'], 0)
        self.assertLessEqual(cpu_metrics['usage_percent'], 100)
        
        # Check memory metrics structure
        memory_metrics = metrics['memory']
        self.assertIn('usage_percent', memory_metrics)
        self.assertIn('total_gb', memory_metrics)
        self.assertIn('used_gb', memory_metrics)
        self.assertIsInstance(memory_metrics['usage_percent'], (int, float))
        
        # Check timestamp
        self.assertIn('timestamp', metrics)
    
    def test_store_metrics(self):
        """Test storing metrics in database"""
        # Collect metrics
        metrics = self.monitor.collect_system_metrics()
        
        # Store metrics
        self.monitor.store_metrics(metrics)
        
        # Check that metrics were stored
        cpu_metric = SystemMetrics.objects.filter(metric_type='cpu_usage').first()
        self.assertIsNotNone(cpu_metric)
        self.assertEqual(cpu_metric.metric_name, 'CPU Usage Percentage')
        self.assertEqual(cpu_metric.metric_unit, '%')
        self.assertEqual(cpu_metric.component, 'system')
        
        memory_metric = SystemMetrics.objects.filter(metric_type='memory_usage').first()
        self.assertIsNotNone(memory_metric)
        self.assertEqual(memory_metric.metric_name, 'Memory Usage Percentage')
    
    @patch('weather_data.system_monitoring.psutil.cpu_percent')
    def test_threshold_alerts(self, mock_cpu_percent):
        """Test threshold-based alert creation"""
        # Mock high CPU usage
        mock_cpu_percent.return_value = 95.0
        
        # Collect metrics with high CPU
        metrics = self.monitor.collect_system_metrics()
        
        # Check thresholds
        self.monitor.check_thresholds(metrics)
        
        # Check that critical alert was created
        alert = SystemAlert.objects.filter(
            alert_type='performance',
            severity='critical',
            component='system'
        ).first()
        
        self.assertIsNotNone(alert)
        self.assertIn('CPU', alert.title)
        self.assertEqual(alert.metric_value, 95.0)
    
    def test_health_checks(self):
        """Test system health checks"""
        health_results = self.monitor.perform_health_checks()
        
        # Check that all health check categories are present
        expected_checks = ['database', 'cache', 'disk', 'services', 'overall']
        
        for check in expected_checks:
            self.assertIn(check, health_results)
        
        # Check database health
        db_health = health_results['database']
        self.assertIn('status', db_health)
        self.assertIn('response_time', db_health)
        
        # Check overall status
        overall = health_results['overall']
        self.assertIn('status', overall)
        self.assertIn('timestamp', overall)
    
    def test_alert_creation(self):
        """Test alert creation and management"""
        # Create test alert
        alert = SystemAlert.objects.create(
            alert_type='performance',
            severity='warning',
            title='Test Alert',
            message='Test alert message',
            component='test_component'
        )
        
        self.assertEqual(alert.status, 'active')
        self.assertIsNone(alert.acknowledged_at)
        self.assertIsNone(alert.resolved_at)
        
        # Test acknowledge
        alert.acknowledge(user=self.admin_user)
        self.assertEqual(alert.status, 'acknowledged')
        self.assertIsNotNone(alert.acknowledged_at)
        self.assertEqual(alert.acknowledged_by, self.admin_user)
        
        # Test resolve
        alert.resolve(user=self.admin_user)
        self.assertEqual(alert.status, 'resolved')
        self.assertIsNotNone(alert.resolved_at)
        self.assertEqual(alert.resolved_by, self.admin_user)
    
    def test_system_status_api(self):
        """Test system status API endpoint"""
        response = self.client.get('/api/weather/monitoring/status/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('overall_status', data)
        self.assertIn('timestamp', data)
        self.assertIn('metrics', data)
        self.assertIn('health_checks', data)
        self.assertIn('alerts', data)
    
    def test_alerts_api(self):
        """Test alerts API endpoint"""
        # Create test alert
        SystemAlert.objects.create(
            alert_type='performance',
            severity='warning',
            title='Test API Alert',
            message='Test alert for API',
            component='api_test'
        )
        
        response = self.client.get('/api/weather/monitoring/alerts/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('alerts', data)
        self.assertIn('count', data)
        self.assertGreater(len(data['alerts']), 0)
        
        alert = data['alerts'][0]
        self.assertEqual(alert['title'], 'Test API Alert')
        self.assertEqual(alert['severity'], 'warning')
    
    def test_acknowledge_alert_api(self):
        """Test alert acknowledgment API"""
        # Create test alert
        alert = SystemAlert.objects.create(
            alert_type='performance',
            severity='warning',
            title='Test Acknowledge Alert',
            message='Test alert for acknowledgment',
            component='api_test'
        )
        
        response = self.client.post(f'/api/weather/monitoring/alerts/{alert.id}/acknowledge/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('message', data)
        self.assertEqual(data['acknowledged_by'], 'admin')
        
        # Check that alert was acknowledged
        alert.refresh_from_db()
        self.assertEqual(alert.status, 'acknowledged')
        self.assertEqual(alert.acknowledged_by, self.admin_user)
    
    def test_metrics_api(self):
        """Test metrics API endpoint"""
        # Create test metrics
        SystemMetrics.objects.create(
            metric_type='cpu_usage',
            metric_name='CPU Usage Test',
            metric_value=75.5,
            metric_unit='%',
            component='system'
        )
        
        response = self.client.get('/api/weather/monitoring/metrics/?type=cpu_usage')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('metrics', data)
        self.assertIn('count', data)
        self.assertGreater(len(data['metrics']), 0)
        
        metric = data['metrics'][0]
        self.assertEqual(metric['type'], 'cpu_usage')
        self.assertEqual(metric['value'], 75.5)
    
    def test_health_checks_api(self):
        """Test health checks API endpoint"""
        # Create test health check
        SystemHealthCheck.objects.create(
            check_type='database',
            check_name='Database Test Check',
            status='healthy',
            response_time=50.0
        )
        
        response = self.client.get('/api/weather/monitoring/health/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('health_checks', data)
        self.assertGreater(len(data['health_checks']), 0)
        
        check = data['health_checks'][0]
        self.assertEqual(check['name'], 'Database Test Check')
        self.assertEqual(check['status'], 'healthy')
    
    def test_diagnostics(self):
        """Test system diagnostics"""
        diagnostic_results = self.diagnostics.run_full_diagnostic()
        
        self.assertIn('metrics', diagnostic_results)
        self.assertIn('health_checks', diagnostic_results)
        self.assertIn('recent_alerts', diagnostic_results)
        self.assertIn('performance_trends', diagnostic_results)
        self.assertIn('recommendations', diagnostic_results)
        self.assertIn('timestamp', diagnostic_results)
        
        # Check recommendations
        recommendations = diagnostic_results['recommendations']
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
    
    def test_cleanup_old_data(self):
        """Test cleanup of old monitoring data"""
        # Create old metrics
        old_date = timezone.now() - timedelta(days=35)
        
        old_metric = SystemMetrics.objects.create(
            metric_type='cpu_usage',
            metric_name='Old CPU Metric',
            metric_value=50.0,
            metric_unit='%',
            component='system'
        )
        old_metric.timestamp = old_date
        old_metric.save()
        
        # Create recent metric
        recent_metric = SystemMetrics.objects.create(
            metric_type='cpu_usage',
            metric_name='Recent CPU Metric',
            metric_value=60.0,
            metric_unit='%',
            component='system'
        )
        
        # Run cleanup
        self.monitor._cleanup_old_data()
        
        # Check that old metric was deleted and recent one remains
        self.assertFalse(SystemMetrics.objects.filter(id=old_metric.id).exists())
        self.assertTrue(SystemMetrics.objects.filter(id=recent_metric.id).exists())
    
    def test_celery_metrics_task(self):
        """Test Celery metrics collection task"""
        result = collect_system_metrics_periodic()
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('timestamp', result)
        self.assertIn('metrics_collected', result)
        
        # Check that metrics were stored
        self.assertGreater(SystemMetrics.objects.count(), 0)
    
    def test_celery_health_checks_task(self):
        """Test Celery health checks task"""
        result = perform_health_checks_periodic()
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('timestamp', result)
        self.assertIn('health_results', result)
        
        # Check that health checks were stored
        self.assertGreater(SystemHealthCheck.objects.count(), 0)
    
    def test_celery_cleanup_task(self):
        """Test Celery cleanup task"""
        result = cleanup_old_monitoring_data()
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('timestamp', result)
    
    def test_duplicate_alert_prevention(self):
        """Test that duplicate alerts are not created"""
        # Create first alert
        self.monitor._create_alert(
            'performance', 'warning', 'Test Alert',
            'Test message', 'test_component'
        )
        
        # Try to create duplicate alert (within 15 minutes)
        self.monitor._create_alert(
            'performance', 'warning', 'Test Alert 2',
            'Another test message', 'test_component'
        )
        
        # Should only have one alert
        alerts = SystemAlert.objects.filter(component='test_component')
        self.assertEqual(alerts.count(), 1)
    
    def test_performance_trends(self):
        """Test performance trends analysis"""
        # Create test metrics over time
        base_time = timezone.now() - timedelta(hours=2)
        
        for i in range(10):
            SystemMetrics.objects.create(
                metric_type='cpu_usage',
                metric_name='CPU Usage',
                metric_value=50.0 + i * 5,  # Increasing trend
                metric_unit='%',
                component='system',
                timestamp=base_time + timedelta(minutes=i * 10)
            )
        
        trends = self.diagnostics._get_performance_trends()
        
        self.assertIn('cpu_usage', trends)
        cpu_trend = trends['cpu_usage']
        self.assertGreater(len(cpu_trend), 0)
        
        # Check trend data structure
        trend_point = cpu_trend[0]
        self.assertIn('timestamp', trend_point)
        self.assertIn('value', trend_point)
    
    def test_unauthorized_access(self):
        """Test that non-admin users cannot access monitoring APIs"""
        # Create regular user
        regular_user = User.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='testpass123'
        )
        
        client = Client()
        client.force_login(regular_user)
        
        # Try to access monitoring endpoints
        response = client.get('/api/weather/monitoring/status/')
        self.assertEqual(response.status_code, 403)
        
        response = client.get('/api/weather/monitoring/alerts/')
        self.assertEqual(response.status_code, 403)
    
    def test_real_time_monitoring_endpoint(self):
        """Test real-time monitoring endpoint"""
        response = self.client.get('/api/weather/monitoring/real-time/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('timestamp', data)
        self.assertIn('system_status', data)
        self.assertIn('active_alerts', data)
        self.assertIn('critical_alerts', data)