"""
Management command to set up initial API providers
"""
from django.core.management.base import BaseCommand
from weather_data.api_management import APIProvider


class Command(BaseCommand):
    help = 'Set up initial API providers for weather data'

    def handle(self, *args, **options):
        # OpenWeatherMap provider
        openweather, created = APIProvider.objects.get_or_create(
            name='openweathermap',
            defaults={
                'display_name': 'OpenWeatherMap',
                'base_url': 'https://api.openweathermap.org/data/2.5',
                'api_key': '',  # To be configured by admin
                'is_active': True,
                'is_primary': True,
                'priority': 1,
                'requests_per_minute': 60,
                'requests_per_day': 1000,
                'requests_per_month': 100000,
                'cost_per_request': 0.0001,
                'monthly_budget': 10.00,
                'supported_endpoints': [
                    'weather',
                    'forecast',
                    'air_pollution',
                    'onecall'
                ],
                'configuration': {
                    'default_params': {
                        'units': 'metric'
                    }
                }
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created OpenWeatherMap provider')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'OpenWeatherMap provider already exists')
            )

        # WeatherAPI provider
        weatherapi, created = APIProvider.objects.get_or_create(
            name='weatherapi',
            defaults={
                'display_name': 'WeatherAPI.com',
                'base_url': 'https://api.weatherapi.com/v1',
                'api_key': '',  # To be configured by admin
                'is_active': False,  # Disabled by default
                'is_primary': False,
                'priority': 2,
                'requests_per_minute': 100,
                'requests_per_day': 1000,
                'requests_per_month': 1000000,
                'cost_per_request': 0.0001,
                'monthly_budget': 20.00,
                'supported_endpoints': [
                    'current.json',
                    'forecast.json',
                    'history.json'
                ],
                'configuration': {
                    'default_params': {
                        'aqi': 'yes'
                    }
                }
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created WeatherAPI provider')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'WeatherAPI provider already exists')
            )

        # AccuWeather provider
        accuweather, created = APIProvider.objects.get_or_create(
            name='accuweather',
            defaults={
                'display_name': 'AccuWeather',
                'base_url': 'https://dataservice.accuweather.com',
                'api_key': '',  # To be configured by admin
                'is_active': False,  # Disabled by default
                'is_primary': False,
                'priority': 3,
                'requests_per_minute': 50,
                'requests_per_day': 50,
                'requests_per_month': 1000,
                'cost_per_request': 0.0,  # Free tier
                'monthly_budget': 0.00,
                'supported_endpoints': [
                    'currentconditions/v1',
                    'forecasts/v1/daily/1day',
                    'forecasts/v1/daily/5day'
                ],
                'configuration': {
                    'default_params': {
                        'details': 'true'
                    }
                }
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created AccuWeather provider')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'AccuWeather provider already exists')
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'API provider setup complete. '
                f'Total providers: {APIProvider.objects.count()}'
            )
        )