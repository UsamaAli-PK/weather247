"""
Management command to start system monitoring
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from weather_data.system_monitoring import system_monitor
from weather_data.celery_monitoring_tasks import initialize_system_monitoring


class Command(BaseCommand):
    help = 'Start system monitoring services'

    def add_arguments(self, parser):
        parser.add_argument(
            '--background',
            action='store_true',
            help='Run monitoring in background using Celery tasks',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Monitoring interval in seconds (default: 60)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting Weather247 System Monitoring...')
        )

        try:
            # Initialize monitoring
            self.stdout.write('Initializing system monitoring...')
            
            # Set monitoring interval
            system_monitor.monitoring_interval = options['interval']
            
            if options['background']:
                # Start background monitoring using Celery
                self.stdout.write('Starting background monitoring with Celery...')
                
                # Initialize monitoring
                result = initialize_system_monitoring.delay()
                self.stdout.write(f'Initialization task ID: {result.id}')
                
                # Schedule periodic tasks (this would typically be done in celery beat configuration)
                self.stdout.write('Background monitoring tasks will be handled by Celery Beat')
                self.stdout.write('Make sure Celery Beat is running with the following schedule:')
                self.stdout.write('- collect_system_metrics_periodic: every 1 minute')
                self.stdout.write('- perform_health_checks_periodic: every 5 minutes')
                self.stdout.write('- cleanup_old_monitoring_data: daily')
                self.stdout.write('- generate_system_health_report: daily')
                self.stdout.write('- alert_escalation_check: every 15 minutes')
                self.stdout.write('- system_performance_analysis: every 6 hours')
                
            else:
                # Start synchronous monitoring
                self.stdout.write('Starting synchronous monitoring...')
                
                # Perform initial health check
                self.stdout.write('Performing initial system health check...')
                health_results = system_monitor.perform_health_checks()
                
                for component, result in health_results.items():
                    status = result.get('status', 'unknown')
                    if status == 'healthy':
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ {component}: {status}')
                        )
                    elif status == 'warning':
                        self.stdout.write(
                            self.style.WARNING(f'⚠ {component}: {status}')
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'✗ {component}: {status}')
                        )
                
                # Collect initial metrics
                self.stdout.write('Collecting initial system metrics...')
                metrics = system_monitor.collect_system_metrics()
                
                # Display key metrics
                if 'cpu' in metrics:
                    cpu_usage = metrics['cpu']['usage_percent']
                    self.stdout.write(f'CPU Usage: {cpu_usage:.1f}%')
                
                if 'memory' in metrics:
                    memory_usage = metrics['memory']['usage_percent']
                    self.stdout.write(f'Memory Usage: {memory_usage:.1f}%')
                
                if 'disk' in metrics:
                    disk_usage = metrics['disk']['usage_percent']
                    self.stdout.write(f'Disk Usage: {disk_usage:.1f}%')
                
                # Store metrics
                system_monitor.store_metrics(metrics)
                
                # Check thresholds
                system_monitor.check_thresholds(metrics)
                
                self.stdout.write(
                    self.style.SUCCESS('System monitoring started successfully!')
                )
                
                self.stdout.write(
                    f'Monitoring interval: {options["interval"]} seconds'
                )
                
                # Start monitoring loop (this will run indefinitely)
                if not options['background']:
                    self.stdout.write('Starting monitoring loop (Ctrl+C to stop)...')
                    try:
                        import asyncio
                        asyncio.run(system_monitor._monitoring_loop())
                    except KeyboardInterrupt:
                        self.stdout.write(
                            self.style.WARNING('\nMonitoring stopped by user')
                        )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error starting system monitoring: {str(e)}')
            )
            raise

        self.stdout.write(
            self.style.SUCCESS('System monitoring setup completed!')
        )