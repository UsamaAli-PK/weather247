"""
Management command to refresh weather data for all cities
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
import logging

from weather_data.models import City, WeatherData
from weather_data.real_weather_service import weather_manager
from weather_data.cache_manager import WeatherCacheManager

logger = logging.getLogger('weather247')


class Command(BaseCommand):
    help = 'Refresh weather data for all active cities'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cities',
            type=str,
            help='Comma-separated list of city names to refresh (default: all active cities)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force refresh even if data is recent',
        )
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Clear cache before refreshing',
        )
        parser.add_argument(
            '--max-age',
            type=int,
            default=15,
            help='Maximum age of weather data in minutes before refresh (default: 15)',
        )

    def handle(self, *args, **options):
        start_time = timezone.now()
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting weather refresh at {start_time}')
        )

        # Clear cache if requested
        if options['clear_cache']:
            self.stdout.write('Clearing weather cache...')
            # Clear all weather-related cache
            try:
                from django.core.cache import cache
                cache.clear()
                self.stdout.write(self.style.SUCCESS('Cache cleared successfully'))
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Failed to clear cache: {e}')
                )

        # Determine which cities to refresh
        if options['cities']:
            city_names = [name.strip() for name in options['cities'].split(',')]
            cities = City.objects.filter(name__in=city_names, is_active=True)
            if not cities.exists():
                raise CommandError(f'No active cities found matching: {", ".join(city_names)}')
        else:
            cities = City.objects.filter(is_active=True)

        if not cities.exists():
            self.stdout.write(self.style.WARNING('No active cities found'))
            return

        self.stdout.write(f'Found {cities.count()} cities to refresh')

        # Refresh weather data
        success_count = 0
        error_count = 0
        skipped_count = 0
        max_age_minutes = options['max_age']

        for city in cities:
            try:
                # Check if we need to refresh this city
                if not options['force']:
                    recent_data = WeatherData.objects.filter(
                        city=city,
                        timestamp__gte=timezone.now() - timedelta(minutes=max_age_minutes)
                    ).exists()
                    
                    if recent_data:
                        self.stdout.write(f'  Skipping {city.name} (recent data exists)')
                        skipped_count += 1
                        continue

                self.stdout.write(f'  Refreshing {city.name}...')
                
                # Get fresh weather data
                weather_data = weather_manager.get_current_weather_with_fallback(
                    city.name, city.country
                )
                
                if weather_data:
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'    ✓ {city.name}: {weather_data.temperature}°C')
                    )
                    
                    # Invalidate cache for this city
                    WeatherCacheManager.invalidate_city_cache(city.name)
                    
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'    ✗ {city.name}: Failed to get weather data')
                    )

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'    ✗ {city.name}: Error - {e}')
                )
                logger.error(f'Error refreshing weather for {city.name}: {e}')

        # Summary
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('Weather refresh completed'))
        self.stdout.write(f'Duration: {duration:.2f} seconds')
        self.stdout.write(f'Cities processed: {cities.count()}')
        self.stdout.write(self.style.SUCCESS(f'Successful: {success_count}'))
        self.stdout.write(self.style.WARNING(f'Skipped: {skipped_count}'))
        self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))
        
        if error_count > 0:
            self.stdout.write(
                self.style.WARNING(f'Check logs for error details')
            )

        # Log summary
        logger.info(
            f'Weather refresh completed: {success_count} successful, '
            f'{skipped_count} skipped, {error_count} errors in {duration:.2f}s'
        )