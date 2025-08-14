"""
Celery configuration for weather247_backend project
"""
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather247_backend.settings')

app = Celery('weather247_backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'refresh-all-cities-weather': {
        'task': 'weather_data.tasks.refresh_all_cities_weather',
        'schedule': 900.0,  # Every 15 minutes
        'options': {'expires': 600}  # Task expires after 10 minutes
    },
    'cleanup-old-weather-data': {
        'task': 'weather_data.tasks.cleanup_old_weather_data',
        'schedule': 86400.0,  # Every 24 hours
        'kwargs': {'days_to_keep': 30},
        'options': {'expires': 3600}  # Task expires after 1 hour
    },
    'warm-cache-popular-cities': {
        'task': 'weather_data.tasks.warm_cache_for_popular_cities',
        'schedule': 1800.0,  # Every 30 minutes
        'options': {'expires': 900}  # Task expires after 15 minutes
    },
    'monitor-api-quota': {
        'task': 'weather_data.tasks.monitor_api_quota',
        'schedule': 3600.0,  # Every hour
        'options': {'expires': 1800}  # Task expires after 30 minutes
    },
    'generate-weather-analytics': {
        'task': 'weather_data.tasks.generate_weather_analytics',
        'schedule': 7200.0,  # Every 2 hours
        'options': {'expires': 3600}  # Task expires after 1 hour
    },
    'generate-analytics-report': {
        'task': 'weather_data.tasks.generate_analytics_report',
        'schedule': 3600.0,  # Every hour
        'options': {'expires': 1800}  # Task expires after 30 minutes
    },
    'system-health-check': {
        'task': 'weather_data.tasks.system_health_check',
        'schedule': 1800.0,  # Every 30 minutes
        'options': {'expires': 900}  # Task expires after 15 minutes
    },
    'cleanup-analytics-cache': {
        'task': 'weather_data.tasks.cleanup_analytics_cache',
        'schedule': 21600.0,  # Every 6 hours
        'options': {'expires': 3600}  # Task expires after 1 hour
    },
    'optimize-system-performance': {
        'task': 'weather_data.tasks.optimize_system_performance',
        'schedule': 14400.0,  # Every 4 hours
        'options': {'expires': 7200}  # Task expires after 2 hours
    },
    'database-maintenance': {
        'task': 'weather_data.tasks.database_maintenance',
        'schedule': 43200.0,  # Every 12 hours
        'options': {'expires': 10800}  # Task expires after 3 hours
    },
}

# Celery timezone
app.conf.timezone = settings.TIME_ZONE

# Task routing
app.conf.task_routes = {
    'weather_data.tasks.refresh_city_weather': {'queue': 'weather_refresh'},
    'weather_data.tasks.refresh_all_cities_weather': {'queue': 'weather_refresh'},
    'weather_data.tasks.cleanup_old_weather_data': {'queue': 'maintenance'},
    'weather_data.tasks.warm_cache_for_popular_cities': {'queue': 'cache_warming'},
    'weather_data.tasks.monitor_api_quota': {'queue': 'monitoring'},
    'weather_data.tasks.generate_weather_analytics': {'queue': 'analytics'},
    'weather_data.tasks.generate_analytics_report': {'queue': 'analytics'},
    'weather_data.tasks.system_health_check': {'queue': 'monitoring'},
    'weather_data.tasks.cleanup_analytics_cache': {'queue': 'maintenance'},
    'weather_data.tasks.optimize_system_performance': {'queue': 'maintenance'},
    'weather_data.tasks.database_maintenance': {'queue': 'maintenance'},
}

# Task configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone=settings.TIME_ZONE,
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')