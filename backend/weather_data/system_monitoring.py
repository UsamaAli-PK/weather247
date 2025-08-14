"""
System monitoring service for Weather247 platform
Provides real-time system health monitoring, automated alerts, and performance tracking
"""
import logging
try:
	import psutil  # Optional dependency for system metrics
except Exception:  # pragma: no cover
	psutil = None
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from django.utils import timezone
from django.db import connection, connections
from django.core.cache import cache
from django.conf import settings
from django.core.mail import send_mail
try:
	from celery import shared_task
except Exception:  # pragma: no cover
	shared_task = None
import requests
import json
import statistics
import subprocess
import os

# Import models after Django is ready
def get_models():
	from .models import SystemMetrics, SystemAlert, SystemHealthCheck, PerformanceBaseline
	from accounts.models import User
	return SystemMetrics, SystemAlert, SystemHealthCheck, PerformanceBaseline, User

logger = logging.getLogger('weather247')


class SystemMonitor:
	"""Main system monitoring service"""
	
	def __init__(self):
		self.alert_thresholds = {
			'cpu_usage': {'warning': 80.0, 'critical': 95.0},
			'memory_usage': {'warning': 85.0, 'critical': 95.0},
			'disk_usage': {'warning': 85.0, 'critical': 95.0},
			'response_time': {'warning': 2000.0, 'critical': 5000.0},  # milliseconds
			'error_rate': {'warning': 5.0, 'critical': 10.0},  # percentage
			'database_connections': {'warning': 80, 'critical': 95},
			'cache_hit_rate': {'warning': 70.0, 'critical': 50.0},  # lower is worse
		}
		self.health_checks = {}
		self.metrics_history = {}
		self.monitoring_interval = 60  # seconds
		self.cache_prefix = 'system_monitor'
	
	def collect_system_metrics(self) -> Dict[str, Any]:
		"""Collect comprehensive system metrics"""
		metrics = {}
		
		try:
			# CPU metrics
			cpu_percent = psutil.cpu_percent(interval=1)
			cpu_count = psutil.cpu_count()
			load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
			
			metrics['cpu'] = {
				'usage_percent': cpu_percent,
				'core_count': cpu_count,
				'load_average_1m': load_avg[0],
				'load_average_5m': load_avg[1],
				'load_average_15m': load_avg[2],
			}
			
			# Memory metrics
			memory = psutil.virtual_memory()
			swap = psutil.swap_memory()
			
			metrics['memory'] = {
				'total_gb': round(memory.total / (1024**3), 2),
				'available_gb': round(memory.available / (1024**3), 2),
				'used_gb': round(memory.used / (1024**3), 2),
				'usage_percent': memory.percent,
				'swap_total_gb': round(swap.total / (1024**3), 2),
				'swap_used_gb': round(swap.used / (1024**3), 2),
				'swap_percent': swap.percent,
			}
			
			# Disk metrics
			disk_usage = psutil.disk_usage('/')
			disk_io = psutil.disk_io_counters()
			
			metrics['disk'] = {
				'total_gb': round(disk_usage.total / (1024**3), 2),
				'used_gb': round(disk_usage.used / (1024**3), 2),
				'free_gb': round(disk_usage.free / (1024**3), 2),
				'usage_percent': (disk_usage.used / disk_usage.total) * 100,
				'read_bytes': disk_io.read_bytes if disk_io else 0,
				'write_bytes': disk_io.write_bytes if disk_io else 0,
			}
			
			# Network metrics
			network_io = psutil.net_io_counters()
			
			metrics['network'] = {
				'bytes_sent': network_io.bytes_sent,
				'bytes_recv': network_io.bytes_recv,
				'packets_sent': network_io.packets_sent,
				'packets_recv': network_io.packets_recv,
				'errors_in': network_io.errin,
				'errors_out': network_io.errout,
			}
			
			# Process metrics
			process_count = len(psutil.pids())
			
			metrics['processes'] = {
				'total_count': process_count,
				'running': len([p for p in psutil.process_iter(['status']) if p.info['status'] == 'running']),
				'sleeping': len([p for p in psutil.process_iter(['status']) if p.info['status'] == 'sleeping']),
			}
			
			# Database metrics
			db_metrics = self._collect_database_metrics()
			metrics['database'] = db_metrics
			
			# Cache metrics
			cache_metrics = self._collect_cache_metrics()
			metrics['cache'] = cache_metrics
			
			# Application metrics
			app_metrics = self._collect_application_metrics()
			metrics['application'] = app_metrics
			
			metrics['timestamp'] = timezone.now().isoformat()
			
		except Exception as e:
			logger.error(f"Error collecting system metrics: {str(e)}")
			metrics['error'] = str(e)
		
		return metrics
	
	def _collect_database_metrics(self) -> Dict[str, Any]:
		"""Collect database performance metrics"""
		db_metrics = {}
		
		try:
			# Get database connection info
			with connection.cursor() as cursor:
				# PostgreSQL specific queries
				if 'postgresql' in settings.DATABASES['default']['ENGINE']:
					# Connection count
					cursor.execute("SELECT count(*) FROM pg_stat_activity;")
					connection_count = cursor.fetchone()[0]
					
					# Database size
					cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
					db_size = cursor.fetchone()[0]
					
					# Active queries
					cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'active';")
					active_queries = cursor.fetchone()[0]
					
					# Slow queries (longer than 1 second)
					cursor.execute("""
						SELECT count(*) FROM pg_stat_activity 
						WHERE state = 'active' AND query_start < now() - interval '1 second';
					""")
					slow_queries = cursor.fetchone()[0]
					
					db_metrics = {
						'connection_count': connection_count,
						'database_size': db_size,
						'active_queries': active_queries,
						'slow_queries': slow_queries,
						'max_connections': 100,  # Default PostgreSQL limit
					}
				
				# SQLite fallback
				else:
					db_metrics = {
						'connection_count': 1,
						'database_size': 'N/A',
						'active_queries': 0,
						'slow_queries': 0,
						'max_connections': 1,
					}
					
		except Exception as e:
			logger.error(f"Error collecting database metrics: {str(e)}")
			db_metrics = {'error': str(e)}
		
		return db_metrics
	
	def _collect_cache_metrics(self) -> Dict[str, Any]:
		"""Collect cache performance metrics"""
		cache_metrics = {}
		
		try:
			# Redis cache metrics
			if hasattr(cache, '_cache') and hasattr(cache._cache, '_client'):
				redis_client = cache._cache._client.get_client()
				info = redis_client.info()
				
				cache_metrics = {
					'used_memory': info.get('used_memory_human', 'N/A'),
					'used_memory_peak': info.get('used_memory_peak_human', 'N/A'),
					'connected_clients': info.get('connected_clients', 0),
					'total_commands_processed': info.get('total_commands_processed', 0),
					'keyspace_hits': info.get('keyspace_hits', 0),
					'keyspace_misses': info.get('keyspace_misses', 0),
					'expired_keys': info.get('expired_keys', 0),
				}
				
				# Calculate hit rate
				hits = cache_metrics['keyspace_hits']
				misses = cache_metrics['keyspace_misses']
				total = hits + misses
				hit_rate = (hits / total * 100) if total > 0 else 0
				cache_metrics['hit_rate'] = round(hit_rate, 2)
			
			else:
				# Fallback for other cache backends
				cache_metrics = {
					'type': 'local_memory',
					'hit_rate': 'N/A',
				}
				
		except Exception as e:
			logger.error(f"Error collecting cache metrics: {str(e)}")
			cache_metrics = {'error': str(e)}
		
		return cache_metrics
	
	def _collect_application_metrics(self) -> Dict[str, Any]:
		"""Collect application-specific metrics"""
		app_metrics = {}
		
		try:
			SystemMetrics, SystemAlert, SystemHealthCheck, PerformanceBaseline, User = get_models()
			
			# User metrics
			total_users = User.objects.count()
			active_users_24h = User.objects.filter(
				last_login__gte=timezone.now() - timedelta(hours=24)
			).count()
			
			# System alerts
			active_alerts = SystemAlert.objects.filter(status='active').count()
			critical_alerts = SystemAlert.objects.filter(
				status='active', 
				severity='critical'
			).count()
			
			# Recent errors (from logs or error tracking)
			recent_errors = SystemAlert.objects.filter(
				alert_type='error',
				created_at__gte=timezone.now() - timedelta(hours=1)
			).count()
			
			app_metrics = {
				'total_users': total_users,
				'active_users_24h': active_users_24h,
				'active_alerts': active_alerts,
				'critical_alerts': critical_alerts,
				'recent_errors': recent_errors,
			}
			
		except Exception as e:
			logger.error(f"Error collecting application metrics: {str(e)}")
			app_metrics = {'error': str(e)}
		
		return app_metrics
	
	def store_metrics(self, metrics: Dict[str, Any]):
		"""Store metrics in database"""
		try:
			timestamp = timezone.now()
			
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
			
			# Store database metrics
			if 'database' in metrics and 'error' not in metrics['database']:
				db_data = metrics['database']
				if 'connection_count' in db_data:
					SystemMetrics.objects.create(
						metric_type='database_connections',
						metric_name='Database Connections',
						metric_value=db_data['connection_count'],
						metric_unit='connections',
						component='database',
						metadata=db_data
					)
			
			# Store cache metrics
			if 'cache' in metrics and 'error' not in metrics['cache']:
				cache_data = metrics['cache']
				if 'hit_rate' in cache_data and isinstance(cache_data['hit_rate'], (int, float)):
					SystemMetrics.objects.create(
						metric_type='cache_hit_rate',
						metric_name='Cache Hit Rate',
						metric_value=cache_data['hit_rate'],
						metric_unit='%',
						component='cache',
						metadata=cache_data
					)
			
			# Store application metrics
			if 'application' in metrics and 'error' not in metrics['application']:
				app_data = metrics['application']
				SystemMetrics.objects.create(
					metric_type='active_users',
					metric_name='Active Users (24h)',
					metric_value=app_data['active_users_24h'],
					metric_unit='users',
					component='application',
					metadata=app_data
				)
			
		except Exception as e:
			logger.error(f"Error storing metrics: {str(e)}")
	
	def check_thresholds(self, metrics: Dict[str, Any]):
		"""Check metrics against thresholds and create alerts"""
		try:
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
			
			# Check database connections
			if 'database' in metrics and 'connection_count' in metrics['database']:
				db_data = metrics['database']
				connection_usage = (db_data['connection_count'] / db_data.get('max_connections', 100)) * 100
				self._check_threshold_alert(
					'database_connections', connection_usage, 'Database Connections',
					f'Database connection usage is {connection_usage:.1f}%', 'database'
				)
			
			# Check cache hit rate (lower is worse)
			if 'cache' in metrics and 'hit_rate' in metrics['cache']:
				hit_rate = metrics['cache']['hit_rate']
				if isinstance(hit_rate, (int, float)):
					# Reverse logic for cache hit rate
					if hit_rate < self.alert_thresholds['cache_hit_rate']['critical']:
						self._create_alert(
							'cache', 'critical', 'Low Cache Hit Rate',
							f'Cache hit rate is {hit_rate:.1f}%', 'cache',
							hit_rate, self.alert_thresholds['cache_hit_rate']['critical']
						)
					elif hit_rate < self.alert_thresholds['cache_hit_rate']['warning']:
						self._create_alert(
							'cache', 'warning', 'Low Cache Hit Rate',
							f'Cache hit rate is {hit_rate:.1f}%', 'cache',
							hit_rate, self.alert_thresholds['cache_hit_rate']['warning']
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
			
			# Send notifications for critical alerts
			if severity == 'critical':
				self._send_alert_notification(alert)
			
		except Exception as e:
			logger.error(f"Error creating alert: {str(e)}")
	
	def _send_alert_notification(self, alert: SystemAlert):
		"""Send notification for critical alerts"""
		try:
			# Email notification
			subject = f"[CRITICAL] Weather247 System Alert: {alert.title}"
			message = f"""
			Alert Details:
			- Type: {alert.alert_type}
			- Severity: {alert.severity}
			- Component: {alert.component}
			- Message: {alert.message}
			- Time: {alert.created_at}
			
			Please investigate immediately.
			"""
			
			# Get admin emails from settings
			admin_emails = [email for name, email in getattr(settings, 'ADMINS', [])]
			
			if admin_emails:
				send_mail(
					subject=subject,
					message=message,
					from_email=settings.DEFAULT_FROM_EMAIL,
					recipient_list=admin_emails,
					fail_silently=True
				)
			
		except Exception as e:
			logger.error(f"Error sending alert notification: {str(e)}")
	
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
			
			# Service health check
			service_health = self._check_services_health()
			health_results['services'] = service_health
			
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
			
			# Store health check result
			SystemHealthCheck.objects.create(
				check_type='database',
				check_name='Database Connectivity',
				status='healthy',
				response_time=response_time
			)
			
			return {
				'status': 'healthy',
				'response_time': response_time,
				'message': 'Database connection successful'
			}
			
		except Exception as e:
			response_time = (time.time() - start_time) * 1000
			
			SystemHealthCheck.objects.create(
				check_type='database',
				check_name='Database Connectivity',
				status='unhealthy',
				response_time=response_time,
				error_message=str(e)
			)
			
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
			
			SystemHealthCheck.objects.create(
				check_type='cache',
				check_name='Cache Operations',
				status='healthy',
				response_time=response_time
			)
			
			return {
				'status': 'healthy',
				'response_time': response_time,
				'message': 'Cache operations successful'
			}
			
		except Exception as e:
			response_time = (time.time() - start_time) * 1000
			
			SystemHealthCheck.objects.create(
				check_type='cache',
				check_name='Cache Operations',
				status='unhealthy',
				response_time=response_time,
				error_message=str(e)
			)
			
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
			
			SystemHealthCheck.objects.create(
				check_type='disk_space',
				check_name='Disk Space Check',
				status=status,
				details={
					'usage_percent': usage_percent,
					'free_gb': round(disk_usage.free / (1024**3), 2),
					'total_gb': round(disk_usage.total / (1024**3), 2)
				}
			)
			
			return {
				'status': status,
				'usage_percent': usage_percent,
				'free_gb': round(disk_usage.free / (1024**3), 2),
				'message': f'Disk usage: {usage_percent:.1f}%'
			}
			
		except Exception as e:
			SystemHealthCheck.objects.create(
				check_type='disk_space',
				check_name='Disk Space Check',
				status='unknown',
				error_message=str(e)
			)
			
			return {
				'status': 'unknown',
				'error': str(e)
			}
	
	def _check_services_health(self) -> Dict[str, Any]:
		"""Check health of background services"""
		try:
			services_status = {}
			
			# Check if Celery workers are running (if using Celery)
			try:
				from celery import current_app
				inspect = current_app.control.inspect()
				stats = inspect.stats()
				
				if stats:
					services_status['celery'] = {
						'status': 'healthy',
						'workers': len(stats),
						'message': f'{len(stats)} Celery workers running'
					}
				else:
					services_status['celery'] = {
						'status': 'unhealthy',
						'workers': 0,
						'message': 'No Celery workers found'
					}
			except ImportError:
				services_status['celery'] = {
					'status': 'not_configured',
					'message': 'Celery not configured'
				}
			except Exception as e:
				services_status['celery'] = {
					'status': 'unknown',
					'error': str(e)
				}
			
			# Overall services status
			all_healthy = all(
				service.get('status') == 'healthy' 
				for service in services_status.values()
				if service.get('status') not in ['not_configured']
			)
			
			overall_status = 'healthy' if all_healthy else 'warning'
			
			SystemHealthCheck.objects.create(
				check_type='services',
				check_name='Background Services',
				status=overall_status,
				details=services_status
			)
			
			return {
				'status': overall_status,
				'services': services_status,
				'message': 'Background services check completed'
			}
			
		except Exception as e:
			return {
				'status': 'unknown',
				'error': str(e)
			}
	
	def get_system_status(self) -> Dict[str, Any]:
		"""Get current system status summary"""
		try:
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
		"""Clean up old metrics and health check data"""
		try:
			# Keep metrics for 30 days
			cutoff_date = timezone.now() - timedelta(days=30)
			
			SystemMetrics.objects.filter(timestamp__lt=cutoff_date).delete()
			SystemHealthCheck.objects.filter(timestamp__lt=cutoff_date).delete()
			
			# Keep resolved alerts for 7 days
			alert_cutoff = timezone.now() - timedelta(days=7)
			SystemAlert.objects.filter(
				status='resolved',
				resolved_at__lt=alert_cutoff
			).delete()
			
		except Exception as e:
			logger.error(f"Error cleaning up old data: {str(e)}")


class SystemDiagnostics:
	"""System diagnostic tools for troubleshooting"""
	
	def __init__(self):
		self.system_monitor = SystemMonitor()
	
	def run_full_diagnostic(self) -> Dict[str, Any]:
		"""Run comprehensive system diagnostic"""
		diagnostic_results = {}
		
		try:
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
			
			# Performance trends
			diagnostic_results['performance_trends'] = self._get_performance_trends()
			
			# System recommendations
			diagnostic_results['recommendations'] = self._generate_recommendations(diagnostic_results)
			
			diagnostic_results['timestamp'] = timezone.now().isoformat()
			
		except Exception as e:
			logger.error(f"Error running diagnostic: {str(e)}")
			diagnostic_results['error'] = str(e)
		
		return diagnostic_results
	
	def _get_performance_trends(self) -> Dict[str, Any]:
		"""Get performance trends over the last 24 hours"""
		try:
			since = timezone.now() - timedelta(hours=24)
			
			# CPU usage trend
			cpu_metrics = SystemMetrics.objects.filter(
				metric_type='cpu_usage',
				timestamp__gte=since
			).order_by('timestamp')
			
			# Memory usage trend
			memory_metrics = SystemMetrics.objects.filter(
				metric_type='memory_usage',
				timestamp__gte=since
			).order_by('timestamp')
			
			trends = {
				'cpu_usage': [
					{
						'timestamp': metric.timestamp.isoformat(),
						'value': metric.metric_value
					}
					for metric in cpu_metrics
				],
				'memory_usage': [
					{
						'timestamp': metric.timestamp.isoformat(),
						'value': metric.metric_value
					}
					for metric in memory_metrics
				]
			}
			
			return trends
			
		except Exception as e:
			logger.error(f"Error getting performance trends: {str(e)}")
			return {'error': str(e)}
	
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
			
			# Cache recommendations
			if 'cache' in metrics and 'hit_rate' in metrics['cache']:
				hit_rate = metrics['cache']['hit_rate']
				if isinstance(hit_rate, (int, float)) and hit_rate < 70:
					recommendations.append(
						f"Low cache hit rate ({hit_rate:.1f}%). Consider optimizing cache configuration or increasing cache size."
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


# Global instances
system_monitor = SystemMonitor()
system_diagnostics = SystemDiagnostics()


# Celery tasks for background monitoring
@shared_task
def collect_system_metrics_task():
	"""Celery task to collect system metrics"""
	try:
		metrics = system_monitor.collect_system_metrics()
		system_monitor.store_metrics(metrics)
		system_monitor.check_thresholds(metrics)
		return "Metrics collected successfully"
	except Exception as e:
		logger.error(f"Error in metrics collection task: {str(e)}")
		return f"Error: {str(e)}"


@shared_task
def perform_health_checks_task():
	"""Celery task to perform health checks"""
	try:
		health_results = system_monitor.perform_health_checks()
		return health_results
	except Exception as e:
		logger.error(f"Error in health checks task: {str(e)}")
		return {'error': str(e)}


@shared_task
def cleanup_old_data_task():
	"""Celery task to clean up old monitoring data"""
	try:
		system_monitor._cleanup_old_data()
		return "Cleanup completed successfully"
	except Exception as e:
		logger.error(f"Error in cleanup task: {str(e)}")
		return f"Error: {str(e)}"