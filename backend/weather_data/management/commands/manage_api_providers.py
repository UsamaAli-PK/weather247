"""
Management command for API provider setup and management
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
import json

from weather_data.api_management import APIProvider, api_manager


class Command(BaseCommand):
    help = 'Manage API providers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--setup-defaults',
            action='store_true',
            help='Set up default API providers',
        )
        parser.add_argument(
            '--health-check',
            action='store_true',
            help='Perform health check on all providers',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all API providers',
        )
        parser.add_argument(
            '--provider',
            type=str,
            help='Specific provider name for operations',
        )
        parser.add_argument(
            '--activate',
            action='store_true',
            help='Activate specified provider',
        )
        parser.add_argument(
            '--deactivate',
            action='store_true',
            help='Deactivate specified provider',
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Test specified provider',
        )

    def handle(self, *args, **options):
        if options['setup_defaults']:
            self.setup_default_providers()
        
        if options['list']:
            self.list_providers()
        
        if options['health_check']:
            self.perform_health_checks()
        
        if options['provider']:
            provider_name = options['provider']
            
            if options['activate']:
                self.activate_provider(provider_name)
            elif options['deactivate']:
                self.deactivate_provider(provider_name)
            elif options['test']:
                self.test_provider(provider_name)

    def setup_default_providers(self):
        """Set up default API providers"""
        self.stdout.write('Setting up default API providers...')
        
        default_providers = [
            {
                'name': 'openweathermap',
                'display_name': 'OpenWeatherMap',
                'base_url': 'https://api.openweathermap.org/data/2.5',
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
            },
            {
                'name': 'weatherapi',
                'display_name': 'WeatherAPI.com',
                'base_url': 'https://api.weatherapi.com/v1',
                'is_primary': False,
                'priority': 2,
                'requests_per_minute': 100,
                'requests_per_day': 1000000,
                'requests_per_month': 1000000,
                'cost_per_request': 0.0,
                'monthly_budget': 0.00,
                'supported_endpoints': [
                    'current.json',
                    'forecast.json',
                    'history.json'
                ],
                'configuration': {
                    'default_params': {}
                }
            },
            {
                'name': 'openmeteo',
                'display_name': 'Open-Meteo',
                'base_url': 'https://api.open-meteo.com/v1',
                'is_primary': False,
                'priority': 3,
                'requests_per_minute': 10000,
                'requests_per_day': 10000,
                'requests_per_month': 10000,
                'cost_per_request': 0.0,
                'monthly_budget': 0.00,
                'supported_endpoints': [
                    'forecast',
                    'historical-weather'
                ],
                'configuration': {
                    'default_params': {
                        'temperature_unit': 'celsius'
                    }
                }
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for provider_data in default_providers:
            provider, created = APIProvider.objects.get_or_create(
                name=provider_data['name'],
                defaults=provider_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created provider: {provider_data["display_name"]}')
                )
            else:
                # Update existing provider
                for key, value in provider_data.items():
                    if key != 'name':
                        setattr(provider, key, value)
                provider.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated provider: {provider_data["display_name"]}')
                )
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(f'Default providers setup completed!')
        )
        self.stdout.write(f'Created: {created_count} providers')
        self.stdout.write(f'Updated: {updated_count} providers')

    def list_providers(self):
        """List all API providers"""
        providers = APIProvider.objects.all().order_by('priority')
        
        if not providers.exists():
            self.stdout.write(self.style.WARNING('No API providers found'))
            return
        
        self.stdout.write('\nAPI Providers:')
        self.stdout.write('=' * 80)
        
        for provider in providers:
            status_color = self.style.SUCCESS if provider.is_active else self.style.ERROR
            health_color = self.style.SUCCESS if provider.is_healthy else self.style.ERROR
            
            usage_today = provider.get_usage_today()
            usage_month = provider.get_usage_this_month()
            
            self.stdout.write(f'\n{provider.display_name} ({provider.name})')
            self.stdout.write(f'  Status: {status_color("Active" if provider.is_active else "Inactive")}')
            self.stdout.write(f'  Health: {health_color("Healthy" if provider.is_healthy else "Unhealthy")}')
            self.stdout.write(f'  Priority: {provider.priority}')
            self.stdout.write(f'  Success Rate: {provider.success_rate:.1f}%')
            self.stdout.write(f'  Usage Today: {usage_today} / {provider.requests_per_day}')
            self.stdout.write(f'  Cost This Month: ${usage_month.get("total_cost", 0):.4f}')
            self.stdout.write(f'  Supported Endpoints: {", ".join(provider.supported_endpoints)}')

    def perform_health_checks(self):
        """Perform health checks on all providers"""
        providers = APIProvider.objects.filter(is_active=True)
        
        if not providers.exists():
            self.stdout.write(self.style.WARNING('No active providers found'))
            return
        
        self.stdout.write('Performing health checks...')
        
        healthy_count = 0
        unhealthy_count = 0
        
        for provider in providers:
            try:
                self.stdout.write(f'  Checking {provider.display_name}...', ending='')
                
                health_result = api_manager.perform_health_check(provider)
                
                if health_result['healthy']:
                    self.stdout.write(
                        self.style.SUCCESS(f' ✓ Healthy ({health_result["response_time"]:.3f}s)')
                    )
                    healthy_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(f' ✗ Unhealthy: {health_result["error"]}')
                    )
                    unhealthy_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f' ✗ Error: {str(e)}')
                )
                unhealthy_count += 1
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'Health check completed:')
        self.stdout.write(self.style.SUCCESS(f'  Healthy: {healthy_count}'))
        self.stdout.write(self.style.ERROR(f'  Unhealthy: {unhealthy_count}'))

    def activate_provider(self, provider_name):
        """Activate a provider"""
        try:
            provider = APIProvider.objects.get(name=provider_name)
            provider.is_active = True
            provider.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Provider {provider.display_name} activated')
            )
            
        except APIProvider.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Provider {provider_name} not found')
            )

    def deactivate_provider(self, provider_name):
        """Deactivate a provider"""
        try:
            provider = APIProvider.objects.get(name=provider_name)
            
            # Check if this is the only active provider
            active_count = APIProvider.objects.filter(is_active=True).count()
            if provider.is_active and active_count <= 1:
                self.stdout.write(
                    self.style.ERROR('Cannot deactivate the only active provider')
                )
                return
            
            provider.is_active = False
            provider.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Provider {provider.display_name} deactivated')
            )
            
        except APIProvider.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Provider {provider_name} not found')
            )

    def test_provider(self, provider_name):
        """Test a provider"""
        try:
            provider = APIProvider.objects.get(name=provider_name)
            
            self.stdout.write(f'Testing {provider.display_name}...')
            
            # Test with a simple weather request
            test_params = {'q': 'London', 'appid': 'test'}
            result = api_manager.make_request('weather', test_params, provider)
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Test successful (Response time: {result["response_time"]:.3f}s)'
                    )
                )
                self.stdout.write(f'  Data sample: {str(result["data"])[:200]}...')
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ Test failed')
                )
                
        except APIProvider.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Provider {provider_name} not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Test failed: {str(e)}')
            )