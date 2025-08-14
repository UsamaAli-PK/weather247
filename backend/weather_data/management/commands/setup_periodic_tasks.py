"""
Management command to set up periodic tasks for weather data processing
"""
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
import json


class Command(BaseCommand):
    help = 'Set up periodic tasks for weather data processing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing periodic tasks before creating new ones',
        )

    def handle(self, *args, **options):
        if options['clear_existing']:
            self.stdout.write('Clearing existing periodic tasks...')
            PeriodicTask.objects.filter(
                name__startswith='weather_'
            ).delete()

        self.stdout.write('Setting up periodic tasks...')

        # Create interval schedules
        every_15_minutes, _ = IntervalSchedule.objects.get_or_create(
            every=15,
            period=IntervalSchedule.MINUTES,
        )

        every_30_minutes, _ = IntervalSchedule.objects.get_or_create(
            every=30,
            period=IntervalSchedule.MINUTES,
        )

        every_hour, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.HOURS,
        )

        every_2_hours, _ = IntervalSchedule.objects.get_or_create(
            every=2,
            period=IntervalSchedule.HOURS,
        )

        # Create crontab schedule for daily cleanup at 2 AM
        daily_2am, _ = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=2,
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )

        # Create periodic tasks
        tasks = [
            {
                'name': 'weather_refresh_all_cities',
                'task': 'weather_data.tasks.refresh_all_cities_weather',
                'schedule': every_15_minutes,
                'description': 'Refresh weather data for all active cities every 15 minutes',
                'enabled': True,
            },
            {
                'name': 'weather_warm_cache_popular_cities',
                'task': 'weather_data.tasks.warm_cache_for_popular_cities',
                'schedule': every_30_minutes,
                'description': 'Pre-warm cache for popular cities every 30 minutes',
                'enabled': True,
            },
            {
                'name': 'weather_monitor_api_quota',
                'task': 'weather_data.tasks.monitor_api_quota',
                'schedule': every_hour,
                'description': 'Monitor API quota usage every hour',
                'enabled': True,
            },
            {
                'name': 'weather_generate_analytics',
                'task': 'weather_data.tasks.generate_weather_analytics',
                'schedule': every_2_hours,
                'description': 'Generate weather analytics every 2 hours',
                'enabled': True,
            },
            {
                'name': 'weather_cleanup_old_data',
                'task': 'weather_data.tasks.cleanup_old_weather_data',
                'schedule': daily_2am,
                'description': 'Clean up old weather data daily at 2 AM',
                'kwargs': json.dumps({'days_to_keep': 30}),
                'enabled': True,
            },
        ]

        created_count = 0
        updated_count = 0

        for task_config in tasks:
            task, created = PeriodicTask.objects.get_or_create(
                name=task_config['name'],
                defaults={
                    'task': task_config['task'],
                    'interval': task_config.get('schedule') if hasattr(task_config.get('schedule'), 'every') else None,
                    'crontab': task_config.get('schedule') if hasattr(task_config.get('schedule'), 'minute') else None,
                    'kwargs': task_config.get('kwargs', '{}'),
                    'enabled': task_config['enabled'],
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created task: {task_config["name"]}')
                )
            else:
                # Update existing task
                task.task = task_config['task']
                if hasattr(task_config.get('schedule'), 'every'):
                    task.interval = task_config['schedule']
                    task.crontab = None
                else:
                    task.crontab = task_config['schedule']
                    task.interval = None
                task.kwargs = task_config.get('kwargs', '{}')
                task.enabled = task_config['enabled']
                task.save()
                
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated task: {task_config["name"]}')
                )

        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(f'Periodic tasks setup completed!')
        )
        self.stdout.write(f'Created: {created_count} tasks')
        self.stdout.write(f'Updated: {updated_count} tasks')
        self.stdout.write('\nScheduled tasks:')
        
        for task in PeriodicTask.objects.filter(name__startswith='weather_'):
            status = '✓ Enabled' if task.enabled else '✗ Disabled'
            if task.interval:
                schedule = f"Every {task.interval.every} {task.interval.period}"
            elif task.crontab:
                schedule = f"Crontab: {task.crontab}"
            else:
                schedule = "No schedule"
            
            self.stdout.write(f'  • {task.name}: {schedule} ({status})')

        self.stdout.write('\nTo start the scheduler, run:')
        self.stdout.write('  python manage.py celery beat --scheduler django_celery_beat.schedulers:DatabaseScheduler')
        self.stdout.write('\nOr use the provided script:')
        self.stdout.write('  python start_celery.py')