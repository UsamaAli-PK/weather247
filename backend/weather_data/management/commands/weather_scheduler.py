"""
Simple weather data scheduler using Django management commands
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
import time
import threading
import logging
from datetime import datetime, timedelta

logger = logging.getLogger('weather247')


class Command(BaseCommand):
    help = 'Run weather data refresh scheduler'

    def add_arguments(self, parser):
        parser.add_argument(
            '--refresh-interval',
            type=int,
            default=15,
            help='Weather refresh interval in minutes (default: 15)',
        )
        parser.add_argument(
            '--cleanup-interval',
            type=int,
            default=1440,  # 24 hours
            help='Cleanup interval in minutes (default: 1440 = 24 hours)',
        )
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Run as daemon (continuous mode)',
        )

    def handle(self, *args, **options):
        refresh_interval = options['refresh_interval']
        cleanup_interval = options['cleanup_interval']
        daemon_mode = options['daemon']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting weather scheduler')
        )
        self.stdout.write(f'Refresh interval: {refresh_interval} minutes')
        self.stdout.write(f'Cleanup interval: {cleanup_interval} minutes')
        
        if daemon_mode:
            self.stdout.write('Running in daemon mode (press Ctrl+C to stop)')
            self.run_daemon(refresh_interval, cleanup_interval)
        else:
            self.stdout.write('Running single refresh cycle')
            self.run_single_cycle()

    def run_single_cycle(self):
        """Run a single refresh cycle"""
        try:
            self.stdout.write('Running weather refresh...')
            call_command('refresh_weather')
            self.stdout.write(self.style.SUCCESS('Single cycle completed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error in single cycle: {e}'))
            logger.error(f'Weather scheduler single cycle error: {e}')

    def run_daemon(self, refresh_interval, cleanup_interval):
        """Run continuous daemon mode"""
        last_refresh = datetime.min
        last_cleanup = datetime.min
        
        try:
            while True:
                now = datetime.now()
                
                # Check if it's time for weather refresh
                if (now - last_refresh).total_seconds() >= refresh_interval * 60:
                    try:
                        self.stdout.write(f'[{now}] Running scheduled weather refresh...')
                        call_command('refresh_weather', max_age=refresh_interval)
                        last_refresh = now
                        self.stdout.write(self.style.SUCCESS('Weather refresh completed'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Weather refresh error: {e}'))
                        logger.error(f'Scheduled weather refresh error: {e}')
                
                # Check if it's time for cleanup
                if (now - last_cleanup).total_seconds() >= cleanup_interval * 60:
                    try:
                        self.stdout.write(f'[{now}] Running scheduled cleanup...')
                        call_command('cleanup_weather_data', days=30)
                        last_cleanup = now
                        self.stdout.write(self.style.SUCCESS('Cleanup completed'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Cleanup error: {e}'))
                        logger.error(f'Scheduled cleanup error: {e}')
                
                # Sleep for 1 minute before checking again
                time.sleep(60)
                
        except KeyboardInterrupt:
            self.stdout.write('\nScheduler stopped by user')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Scheduler error: {e}'))
            logger.error(f'Weather scheduler daemon error: {e}')


class WeatherSchedulerService:
    """Service class for managing weather data refresh in background"""
    
    def __init__(self):
        self.refresh_thread = None
        self.running = False
        self.refresh_interval = 15 * 60  # 15 minutes in seconds
        
    def start_background_refresh(self, interval_minutes=15):
        """Start background weather refresh"""
        if self.running:
            logger.warning('Background refresh already running')
            return False
            
        self.refresh_interval = interval_minutes * 60
        self.running = True
        
        self.refresh_thread = threading.Thread(
            target=self._refresh_loop,
            daemon=True
        )
        self.refresh_thread.start()
        
        logger.info(f'Background weather refresh started (interval: {interval_minutes} minutes)')
        return True
    
    def stop_background_refresh(self):
        """Stop background weather refresh"""
        self.running = False
        if self.refresh_thread:
            self.refresh_thread.join(timeout=5)
        logger.info('Background weather refresh stopped')
    
    def _refresh_loop(self):
        """Background refresh loop"""
        from weather_data.real_weather_service import weather_manager
        
        while self.running:
            try:
                logger.debug('Running background weather refresh')
                updated_count = weather_manager.update_weather_for_all_cities()
                logger.info(f'Background refresh completed: {updated_count} cities updated')
                
                # Sleep for the specified interval
                for _ in range(self.refresh_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f'Background refresh error: {e}')
                # Sleep for 5 minutes on error before retrying
                for _ in range(300):
                    if not self.running:
                        break
                    time.sleep(1)


# Global scheduler instance
weather_scheduler = WeatherSchedulerService()