"""
Core system monitoring functionality
"""
import logging
try:
	import psutil  # Optional dependency
except Exception:  # pragma: no cover
	psutil = None
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from django.utils import timezone
from django.db import connection
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger('weather247')


class SystemMonitor:
	"""Main system monitoring service"""
	
	def __init__(self):
		self.alert_thresholds = {
			'cpu_usage': {'warning': 80.0, 'critical': 95.0},
			'memory_usage': {'warning': 85.0, 'critical': 95.0},
			'disk_usage': {'warning': 85.0, 'critical': 95.0},
		}
		self.cache_prefix = 'system_monitor'
	
	def collect_system_metrics(self) -> Dict[str, Any]:
		"""Collect comprehensive system metrics"""
		metrics = {}
		
		try:
			# CPU metrics
			cpu_percent = psutil.cpu_percent(interval=1)
			cpu_count = psutil.cpu_count()
			
			metrics['cpu'] = {
				'usage_percent': cpu_percent,
				'core_count': cpu_count,
			}
			
			# Memory metrics
			memory = psutil.virtual_memory()
			
			metrics['memory'] = {
				'total_gb': round(memory.total / (1024**3), 2),
				'available_gb': round(memory.available / (1024**3), 2),
				'used_gb': round(memory.used / (1024**3), 2),
				'usage_percent': memory.percent,
			}
			
			# Disk metrics
			disk_usage = psutil.disk_usage('/')
			
			metrics['disk'] = {
				'total_gb': round(disk_usage.total / (1024**3), 2),
				'used_gb': round(disk_usage.used / (1024**3), 2),
				'free_gb': round(disk_usage.free / (1024**3), 2),
				'usage_percent': (disk_usage.used / disk_usage.total) * 100,
			}
			
			# Database metrics
			db_metrics = self._collect_database_metrics()
			metrics['database'] = db_metrics
			
			# Cache metrics
			cache_metrics = self._collect_cache_metrics()
			metrics['cache'] = cache_metrics
			
			metrics['timestamp'] = timezone.now().isoformat()
			
		except Exception as e:
			logger.error(f"Error collecting system metrics: {str(e)}")
			metrics['error'] = str(e)
		
		return metrics
	
	def _collect_database_metrics(self) -> Dict[str, Any]:
		"""Collect database performance metrics"""
		db_metrics = {}
		
		try:
			# Test database connection
			with connection.cursor() as cursor:
				cursor.execute("SELECT 1")
				cursor.fetchone()
			
			db_metrics = {
				'status': 'healthy',
				'connection_test': 'passed'
			}
					
		except Exception as e:
			logger.error(f"Error collecting database metrics: {str(e)}")
			db_metrics = {'error': str(e), 'status': 'unhealthy'}
		
		return db_metrics
	
	def _collect_cache_metrics(self) -> Dict[str, Any]:
		"""Collect cache performance metrics"""
		cache_metrics = {}
		
		try:
			# Test cache operations
			test_key = 'health_check_test'
			test_value = 'test_value'
			
			cache.set(test_key, test_value, timeout=60)
			retrieved_value = cache.get(test_key)
			cache.delete(test_key)
			
			if retrieved_value == test_value:
				cache_metrics = {
					'status': 'healthy',
					'test': 'passed'
				}
			else:
				cache_metrics = {
					'status': 'unhealthy',
					'test': 'failed'
				}
					
		except Exception as e:
			logger.error(f"Error collecting cache metrics: {str(e)}")
			cache_metrics = {'error': str(e), 'status': 'unhealthy'}
		
		return cache_metrics
	
	def store_metrics(self, metrics: Dict[str, Any]):
		"""Store metrics in database"""
		try:
			# Import models here to avoid circular imports
			from .models import SystemMetrics
			
			# Store CPU metrics
			if 'cpu' in metrics:
				cpu_data = metrics['cpu']
				SystemMetrics.objects.create(
					metric_type='cpu_usage',
					metric_name='CPU Usage Percentage',
					metric_value=cpu_data['usage_percent'],
					metric_unit='%',
					component='system',
					metadata=cpu_data
				)
			
			# Store memory metrics
			if 'memory' in metrics:
				memory_data = metrics['memory']
				SystemMetrics.objects.create(
					metric_type='memory_usage',
					metric_name='Memory Usage Percentage',
					metric_value=memory_data['usage_percent'],
					metric_unit='%',
					component='system',
					metadata=memory_data
				)
			
			# Store disk metrics
			if 'disk' in metrics:
				disk_data = metrics['disk']
				SystemMetrics.objects.create(
					metric_type='disk_usage',
					metric_name='Disk Usage Percentage',
					metric_value=disk_data['usage_percent'],
					metric_unit='%',
					component='system',
					metadata=disk_data
				)
			
		except Exception as e:
			logger.error(f"Error storing metrics: {str(e)}")
	
	def check_thresholds(self, metrics: Dict[str, Any]):
		"""Check metrics against thresholds and create alerts"""
		try:
			# Import models here to avoid circular imports
			from .models import SystemAlert
			
			# Check CPU usage
			if 'cpu' in metrics:
				cpu_usage = metrics['cpu']['usage_percent']
				self._check_threshold_alert(
					'cpu_usage', cpu_usage, 'CPU Usage',
					f'CPU usage is {cpu_usage:.1f}%', 'system'
				)
			
			# Check memory usage
			if 'memory' in metrics:
				memory_usage = metrics['memory']['usage_percent']
				self._check_threshold_alert(
					'memory_usage', memory_usage, 'Memory Usage',
					f'Memory usage is {memory_usage:.1f}%', 'system'
				)
			
			# Check disk usage
			if 'disk' in metrics:
				disk_usage = metrics['disk']['usage_percent']
				self._check_threshold_alert(
					'disk_usage', disk_usage, 'Disk Usage',
					f'Disk usage is {disk_usage:.1f}%', 'system'
				)
			
		except Exception as e:
			logger.error(f"Error checking thresholds: {str(e)}")
	
	def _check_threshold_alert(self, metric_type: str, value: float, title: str, 
							  message: str, component: str):
		"""Check a metric against its thresholds and create alerts if needed"""
		thresholds = self.alert_thresholds.get(metric_type, {})
		
		if value >= thresholds.get('critical', 100):
			self._create_alert(
				'performance', 'critical', f'Critical {title}',
				message, component, value, thresholds['critical']
			)
		elif value >= thresholds.get('warning', 100):
			self._create_alert(
				'performance', 'warning', f'High {title}',
				message, component, value, thresholds['warning']
			)
	
	def _create_alert(self, alert_type: str, severity: str, title: str, 
					 message: str, component: str, metric_value: float = None, 
					 threshold_value: float = None):
		"""Create system alert if it doesn't already exist"""
		try:
			# Import models here to avoid circular imports
			from .models import SystemAlert
			
			# Check if similar alert already exists (avoid spam)
			existing_alert = SystemAlert.objects.filter(
				alert_type=alert_type,
				component=component,
				status='active',
				created_at__gte=timezone.now() - timedelta(minutes=15)
			).first()
			
			if existing_alert:
				return  # Don't create duplicate alerts
			
			alert = SystemAlert.objects.create(
				alert_type=alert_type,
				severity=severity,
				title=title,
				message=message,
				component=component,
				metric_value=metric_value,
				threshold_value=threshold_value
			)
			
			logger.warning(f"Created system alert: {title}")
			
		except Exception as e:
			logger.error(f"Error creating alert: {str(e)}")
	
	def perform_health_checks(self) -> Dict[str, Any]:
		"""Perform comprehensive system health checks"""
		health_results = {}
		
		try:
			# Database health check
			db_health = self._check_database_health()
			health_results['database'] = db_health
			
			# Cache health check
			cache_health = self._check_cache_health()
			health_results['cache'] = cache_health
			
			# Disk space health check
			disk_health = self._check_disk_health()
			health_results['disk'] = disk_health
			
			# Overall health status
			all_healthy = all(
				result.get('status') == 'healthy' 
				for result in health_results.values()
			)
			
			health_results['overall'] = {
				'status': 'healthy' if all_healthy else 'unhealthy',
				'timestamp': timezone.now().isoformat()
			}
			
		except Exception as e:
			logger.error(f"Error performing health checks: {str(e)}")
			health_results['error'] = str(e)
		
		return health_results
	
	def _check_database_health(self) -> Dict[str, Any]:
		"""Check database connectivity and performance"""
		start_time = time.time()
		
		try:
			# Test database connection
			with connection.cursor() as cursor:
				cursor.execute("SELECT 1")
				cursor.fetchone()
			
			response_time = (time.time() - start_time) * 1000  # milliseconds
			
			return {
				'status': 'healthy',
				'response_time': response_time,
				'message': 'Database connection successful'
			}
			
		except Exception as e:
			response_time = (time.time() - start_time) * 1000
			
			return {
				'status': 'unhealthy',
				'response_time': response_time,
				'error': str(e)
			}
	
	def _check_cache_health(self) -> Dict[str, Any]:
		"""Check cache connectivity and performance"""
		start_time = time.time()
		
		try:
			# Test cache operations
			test_key = 'health_check_test'
			test_value = 'test_value'
			
			cache.set(test_key, test_value, timeout=60)
			retrieved_value = cache.get(test_key)
			cache.delete(test_key)
			
			if retrieved_value != test_value:
				raise Exception("Cache value mismatch")
			
			response_time = (time.time() - start_time) * 1000
			
			return {
				'status': 'healthy',
				'response_time': response_time,
				'message': 'Cache operations successful'
			}
			
		except Exception as e:
			response_time = (time.time() - start_time) * 1000
			
			return {
				'status': 'unhealthy',
				'response_time': response_time,
				'error': str(e)
			}
	
	def _check_disk_health(self) -> Dict[str, Any]:
		"""Check disk space and I/O health"""
		try:
			disk_usage = psutil.disk_usage('/')
			usage_percent = (disk_usage.used / disk_usage.total) * 100
			
			status = 'healthy'
			if usage_percent > 95:
				status = 'unhealthy'
			elif usage_percent > 85:
				status = 'warning'
			
			return {
				'status': status,
				'usage_percent': usage_percent,
				'free_gb': round(disk_usage.free / (1024**3), 2),
				'message': f'Disk usage: {usage_percent:.1f}%'
			}
			
		except Exception as e:
			return {
				'status': 'unknown',
				'error': str(e)
			}
	
	def get_system_status(self) -> Dict[str, Any]:
		"""Get current system status summary"""
		try:
			# Import models here to avoid circular imports
			from .models import SystemAlert
			
			# Get latest metrics
			metrics = self.collect_system_metrics()
			
			# Get health check results
			health_results = self.perform_health_checks()
			
			# Get active alerts
			active_alerts = SystemAlert.objects.filter(status='active').count()
			critical_alerts = SystemAlert.objects.filter(
				status='active', 
				severity='critical'
			).count()
			
			# Determine overall system status
			overall_status = 'healthy'
			if critical_alerts > 0:
				overall_status = 'critical'
			elif active_alerts > 0:
				overall_status = 'warning'
			elif health_results.get('overall', {}).get('status') != 'healthy':
				overall_status = 'warning'
			
			status = {
				'overall_status': overall_status,
				'timestamp': timezone.now().isoformat(),
				'metrics': metrics,
				'health_checks': health_results,
				'alerts': {
					'active': active_alerts,
					'critical': critical_alerts
				}
			}
			
			# Cache the status for dashboard
			cache.set(f'{self.cache_prefix}:system_status', status, timeout=60)
			
			return status
			
		except Exception as e:
			logger.error(f"Error getting system status: {str(e)}")
			return {
				'overall_status': 'unknown',
				'error': str(e),
				'timestamp': timezone.now().isoformat()
			}
	
	def _cleanup_old_data(self):
		"""Clean up old monitoring data"""
		try:
			# Import models here to avoid circular imports
			from .models import SystemMetrics, SystemAlert, SystemHealthCheck
			
			# Clean up old metrics (older than 30 days)
			cutoff_date = timezone.now() - timedelta(days=30)
			
			old_metrics_count = SystemMetrics.objects.filter(timestamp__lt=cutoff_date).count()
			SystemMetrics.objects.filter(timestamp__lt=cutoff_date).delete()
			
			# Clean up old health checks (older than 7 days)
			health_cutoff = timezone.now() - timedelta(days=7)
			old_health_count = SystemHealthCheck.objects.filter(timestamp__lt=health_cutoff).count()
			SystemHealthCheck.objects.filter(timestamp__lt=health_cutoff).delete()
			
			# Clean up resolved alerts (older than 90 days)
			alert_cutoff = timezone.now() - timedelta(days=90)
			old_alerts_count = SystemAlert.objects.filter(
				status='resolved',
				resolved_at__lt=alert_cutoff
			).count()
			SystemAlert.objects.filter(
				status='resolved',
				resolved_at__lt=alert_cutoff
			).delete()
			
			logger.info(f"Cleaned up {old_metrics_count} old metrics, {old_health_count} old health checks, {old_alerts_count} old alerts")
			
		except Exception as e:
			logger.error(f"Error cleaning up old data: {str(e)}")
			raise


class SystemDiagnostics:
	"""System diagnostic tools for troubleshooting"""
	
	def __init__(self):
		self.system_monitor = SystemMonitor()
	
	def run_full_diagnostic(self) -> Dict[str, Any]:
		"""Run comprehensive system diagnostic"""
		diagnostic_results = {}
		
		try:
			# Import models here to avoid circular imports
			from .models import SystemAlert
			
			# System metrics
			diagnostic_results['metrics'] = self.system_monitor.collect_system_metrics()
			
			# Health checks
			diagnostic_results['health_checks'] = self.system_monitor.perform_health_checks()
			
			# Recent alerts
			recent_alerts = SystemAlert.objects.filter(
				created_at__gte=timezone.now() - timedelta(hours=24)
			).order_by('-created_at')[:10]
			
			diagnostic_results['recent_alerts'] = [
				{
					'id': alert.id,
					'type': alert.alert_type,
					'severity': alert.severity,
					'title': alert.title,
					'message': alert.message,
					'component': alert.component,
					'created_at': alert.created_at.isoformat(),
					'status': alert.status
				}
				for alert in recent_alerts
			]
			
			# System recommendations
			diagnostic_results['recommendations'] = self._generate_recommendations(diagnostic_results)
			
			diagnostic_results['timestamp'] = timezone.now().isoformat()
			
		except Exception as e:
			logger.error(f"Error running diagnostic: {str(e)}")
			diagnostic_results['error'] = str(e)
		
		return diagnostic_results
	
	def _generate_recommendations(self, diagnostic_data: Dict[str, Any]) -> List[str]:
		"""Generate system recommendations based on diagnostic data"""
		recommendations = []
		
		try:
			metrics = diagnostic_data.get('metrics', {})
			
			# CPU recommendations
			if 'cpu' in metrics:
				cpu_usage = metrics['cpu'].get('usage_percent', 0)
				if cpu_usage > 80:
					recommendations.append(
						f"High CPU usage detected ({cpu_usage:.1f}%). Consider scaling up or optimizing processes."
					)
			
			# Memory recommendations
			if 'memory' in metrics:
				memory_usage = metrics['memory'].get('usage_percent', 0)
				if memory_usage > 85:
					recommendations.append(
						f"High memory usage detected ({memory_usage:.1f}%). Consider adding more RAM or optimizing memory usage."
					)
			
			# Disk recommendations
			if 'disk' in metrics:
				disk_usage = metrics['disk'].get('usage_percent', 0)
				if disk_usage > 85:
					recommendations.append(
						f"High disk usage detected ({disk_usage:.1f}%). Consider cleaning up old files or adding more storage."
					)
			
			# Alert recommendations
			recent_alerts = diagnostic_data.get('recent_alerts', [])
			critical_alerts = [a for a in recent_alerts if a['severity'] == 'critical']
			if critical_alerts:
				recommendations.append(
					f"You have {len(critical_alerts)} critical alerts that need immediate attention."
				)
			
			if not recommendations:
				recommendations.append("System appears to be running normally. No immediate recommendations.")
			
		except Exception as e:
			logger.error(f"Error generating recommendations: {str(e)}")
			recommendations.append("Unable to generate recommendations due to an error.")
		
		return recommendations
	
	def _get_performance_trends(self) -> Dict[str, List[Dict]]:
		"""Get performance trends for analysis"""
		try:
			# Import models here to avoid circular imports
			from .models import SystemMetrics
			
			# Get metrics from last 24 hours
			since = timezone.now() - timedelta(hours=24)
			
			trends = {}
			metric_types = ['cpu_usage', 'memory_usage', 'disk_usage']
			
			for metric_type in metric_types:
				metrics = SystemMetrics.objects.filter(
					metric_type=metric_type,
					timestamp__gte=since
				).order_by('timestamp')
				
				trends[metric_type] = [
					{
						'timestamp': metric.timestamp.isoformat(),
						'value': metric.metric_value,
						'unit': metric.metric_unit
					}
					for metric in metrics
				]
			
			return trends
			
		except Exception as e:
			logger.error(f"Error getting performance trends: {str(e)}")
			return {}


# Global instances
system_monitor = SystemMonitor()
system_diagnostics = SystemDiagnostics()