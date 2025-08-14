# Weather247 Background Task System

This document explains how to use the Celery-based background task system for weather data processing.

## Overview

The background task system handles:
- Periodic weather data refresh for all cities
- Cache warming for popular cities
- API quota monitoring and health checks
- Data cleanup and maintenance
- Weather analytics generation

## Prerequisites

1. **Redis Server**: Required for Celery broker and result backend
   ```bash
   # Install Redis (Windows with Chocolatey)
   choco install redis-64
   
   # Start Redis server
   redis-server
   ```

2. **Python Dependencies**: Install required packages
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

### 1. Set up periodic tasks in database
```bash
python manage.py migrate
python manage.py setup_periodic_tasks
```

### 2. Start background services

**Option A: Use the provided script (Recommended)**
```bash
# Windows
start_celery.bat

# Or directly with Python
python start_celery.py
```

**Option B: Start services manually**
```bash
# Terminal 1: Start Celery worker
celery -A weather247_backend worker --loglevel=info --concurrency=4

# Terminal 2: Start Celery beat scheduler
celery -A weather247_backend beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Terminal 3: Start Flower monitoring (optional)
celery -A weather247_backend flower --port=5555
```

## Available Tasks

### Periodic Tasks (Automatic)

1. **Weather Refresh** (`refresh_all_cities_weather`)
   - Runs every 15 minutes
   - Updates weather data for all active cities
   - Uses API fallback mechanisms

2. **Cache Warming** (`warm_cache_for_popular_cities`)
   - Runs every 30 minutes
   - Pre-loads cache for top 20 most requested cities

3. **API Monitoring** (`monitor_api_quota`)
   - Runs every hour
   - Checks API health and quota usage
   - Logs warnings for unhealthy services

4. **Analytics Generation** (`generate_weather_analytics`)
   - Runs every 2 hours
   - Generates weather statistics and trends
   - Caches results for quick access

5. **Data Cleanup** (`cleanup_old_weather_data`)
   - Runs daily at 2 AM
   - Removes weather data older than 30 days
   - Cleans up forecasts and air quality data

### Manual Tasks (On-Demand)

You can trigger tasks manually through the API or Django admin:

```python
# Refresh specific city
from weather_data.tasks import refresh_city_weather
task = refresh_city_weather.delay(city_id=1)

# Refresh all cities
from weather_data.tasks import refresh_all_cities_weather
task = refresh_all_cities_weather.delay()

# Clean up old data
from weather_data.tasks import cleanup_old_weather_data
task = cleanup_old_weather_data.delay(days_to_keep=30)
```

## Monitoring and Management

### API Endpoints

1. **Task Monitoring Dashboard**
   ```
   GET /api/weather/monitoring/dashboard/
   ```
   Returns task statistics, weather stats, cache stats, and API health.

2. **Trigger Manual Refresh**
   ```
   POST /api/weather/monitoring/refresh/
   Body: {"cities": ["London", "New York"]}  # Optional
   ```

3. **Check Task Status**
   ```
   GET /api/weather/monitoring/task/{task_id}/
   ```

4. **API Quota Status**
   ```
   GET /api/weather/monitoring/quota/
   ```

5. **System Health Check**
   ```
   GET /api/weather/monitoring/health/
   ```

### Flower Web Interface

If Flower is running, you can monitor tasks at:
```
http://localhost:5555
```

Features:
- Real-time task monitoring
- Worker statistics
- Task history and results
- Queue management

## Configuration

### Task Queues

Tasks are organized into different queues for better resource management:

- `weather_refresh`: Weather data updates
- `maintenance`: Cleanup and maintenance tasks
- `cache_warming`: Cache pre-loading tasks
- `monitoring`: Health checks and monitoring
- `analytics`: Data analysis and reporting

### Task Settings

Key Celery settings in `settings.py`:

```python
# Task time limits
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes

# Worker settings
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Task routing
CELERY_TASK_ROUTES = {
    'weather_data.tasks.refresh_city_weather': {'queue': 'weather_refresh'},
    'weather_data.tasks.cleanup_old_weather_data': {'queue': 'maintenance'},
    # ... more routes
}
```

## Troubleshooting

### Common Issues

1. **Redis Connection Error**
   ```
   Error: Redis connection failed
   ```
   Solution: Ensure Redis server is running on `localhost:6379`

2. **Task Not Executing**
   - Check if Celery worker is running
   - Verify task is enabled in Django admin
   - Check worker logs for errors

3. **High Memory Usage**
   - Reduce `CELERY_WORKER_PREFETCH_MULTIPLIER`
   - Lower `CELERY_WORKER_MAX_TASKS_PER_CHILD`
   - Monitor task execution time

### Logging

Task execution is logged to:
- Console output (when running with `--loglevel=info`)
- Django log file: `weather247.log`
- Celery worker logs

### Performance Tuning

1. **Adjust Worker Concurrency**
   ```bash
   celery -A weather247_backend worker --concurrency=8
   ```

2. **Use Multiple Workers**
   ```bash
   # Start multiple workers with different queues
   celery -A weather247_backend worker --queues=weather_refresh --concurrency=4
   celery -A weather247_backend worker --queues=maintenance,monitoring --concurrency=2
   ```

3. **Monitor Resource Usage**
   - Use Flower for real-time monitoring
   - Check Redis memory usage
   - Monitor database connections

## Management Commands

### Setup and Maintenance

```bash
# Set up periodic tasks
python manage.py setup_periodic_tasks

# Clear existing tasks and recreate
python manage.py setup_periodic_tasks --clear-existing

# Manual weather refresh
python manage.py refresh_weather

# Manual cleanup
python manage.py cleanup_weather_data --days=30

# Start simple scheduler (alternative to Celery beat)
python manage.py weather_scheduler --daemon
```

## Production Deployment

For production deployment:

1. Use a process manager like Supervisor or systemd
2. Configure proper logging and monitoring
3. Set up Redis persistence
4. Use multiple worker processes
5. Monitor task execution and failures
6. Set up alerts for system health

Example Supervisor configuration:
```ini
[program:weather247_celery_worker]
command=/path/to/venv/bin/celery -A weather247_backend worker --loglevel=info
directory=/path/to/project
user=www-data
autostart=true
autorestart=true

[program:weather247_celery_beat]
command=/path/to/venv/bin/celery -A weather247_backend beat --scheduler django_celery_beat.schedulers:DatabaseScheduler
directory=/path/to/project
user=www-data
autostart=true
autorestart=true
```