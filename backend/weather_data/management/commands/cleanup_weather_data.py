"""
Management command to clean up old weather data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import logging

from weather_data.models import WeatherData, AirQualityData, WeatherForecast

logger = logging.getLogger('weather247')


class Command(BaseCommand):
    help = 'Clean up old weather data to manage database size'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Keep weather data newer than this many days (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of records to delete in each batch (default: 1000)',
        )

    def handle(self, *args, **options):
        days_to_keep = options['days']
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        self.stdout.write(
            self.style.SUCCESS(f'Cleaning up weather data older than {cutoff_date}')
        )
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No data will be deleted'))

        # Clean up weather data
        old_weather = WeatherData.objects.filter(timestamp__lt=cutoff_date)
        weather_count = old_weather.count()
        
        if weather_count > 0:
            self.stdout.write(f'Found {weather_count} old weather records')
            
            if not dry_run:
                deleted_count = 0
                while True:
                    batch = list(old_weather[:batch_size])
                    if not batch:
                        break
                    
                    batch_ids = [record.id for record in batch]
                    WeatherData.objects.filter(id__in=batch_ids).delete()
                    deleted_count += len(batch)
                    
                    self.stdout.write(f'  Deleted {deleted_count}/{weather_count} weather records')
                
                self.stdout.write(
                    self.style.SUCCESS(f'Deleted {deleted_count} weather records')
                )
            else:
                self.stdout.write(f'Would delete {weather_count} weather records')
        else:
            self.stdout.write('No old weather records found')

        # Clean up air quality data
        old_air_quality = AirQualityData.objects.filter(timestamp__lt=cutoff_date)
        air_quality_count = old_air_quality.count()
        
        if air_quality_count > 0:
            self.stdout.write(f'Found {air_quality_count} old air quality records')
            
            if not dry_run:
                deleted_count = 0
                while True:
                    batch = list(old_air_quality[:batch_size])
                    if not batch:
                        break
                    
                    batch_ids = [record.id for record in batch]
                    AirQualityData.objects.filter(id__in=batch_ids).delete()
                    deleted_count += len(batch)
                    
                    self.stdout.write(f'  Deleted {deleted_count}/{air_quality_count} air quality records')
                
                self.stdout.write(
                    self.style.SUCCESS(f'Deleted {deleted_count} air quality records')
                )
            else:
                self.stdout.write(f'Would delete {air_quality_count} air quality records')
        else:
            self.stdout.write('No old air quality records found')

        # Clean up old forecasts
        old_forecasts = WeatherForecast.objects.filter(
            forecast_date__lt=timezone.now().date() - timedelta(days=7)
        )
        forecast_count = old_forecasts.count()
        
        if forecast_count > 0:
            self.stdout.write(f'Found {forecast_count} old forecast records')
            
            if not dry_run:
                deleted_count = 0
                while True:
                    batch = list(old_forecasts[:batch_size])
                    if not batch:
                        break
                    
                    batch_ids = [record.id for record in batch]
                    WeatherForecast.objects.filter(id__in=batch_ids).delete()
                    deleted_count += len(batch)
                    
                    self.stdout.write(f'  Deleted {deleted_count}/{forecast_count} forecast records')
                
                self.stdout.write(
                    self.style.SUCCESS(f'Deleted {deleted_count} forecast records')
                )
            else:
                self.stdout.write(f'Would delete {forecast_count} forecast records')
        else:
            self.stdout.write('No old forecast records found')

        # Summary
        total_records = weather_count + air_quality_count + forecast_count
        
        if total_records > 0:
            if not dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f'Cleanup completed - removed {total_records} old records')
                )
                logger.info(f'Weather data cleanup completed: {total_records} records removed')
            else:
                self.stdout.write(
                    self.style.WARNING(f'Dry run completed - would remove {total_records} records')
                )
        else:
            self.stdout.write(self.style.SUCCESS('No cleanup needed - database is clean'))