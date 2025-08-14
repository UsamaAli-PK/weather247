"""
Management command to create sample API usage data for testing
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
import random

from weather_data.api_management import APIProvider, APIUsage, APIFailover
from django.db import models


class Command(BaseCommand):
    help = 'Create sample API usage data for testing the management interface'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days of sample data to create'
        )

    def handle(self, *args, **options):
        days = options['days']
        
        # Get existing providers
        providers = APIProvider.objects.all()
        if not providers.exists():
            self.stdout.write(
                self.style.ERROR('No API providers found. Run setup_api_providers first.')
            )
            return
        
        # Create sample usage data
        created_usage = 0
        created_failovers = 0
        
        for day_offset in range(days):
            current_date = date.today() - timedelta(days=day_offset)
            
            for provider in providers:
                if not provider.is_active:
                    continue
                
                # Create usage for different endpoints
                for endpoint in provider.supported_endpoints[:2]:  # Limit to 2 endpoints
                    # Generate realistic usage patterns
                    base_requests = random.randint(10, 100)
                    if day_offset < 7:  # More recent data has higher usage
                        base_requests = int(base_requests * 1.5)
                    
                    success_rate = random.uniform(0.85, 0.99)
                    success_count = int(base_requests * success_rate)
                    error_count = base_requests - success_count
                    
                    # Response times vary by provider
                    if 'openweather' in provider.name.lower():
                        avg_response_time = random.uniform(0.2, 0.8)
                    elif 'weatherapi' in provider.name.lower():
                        avg_response_time = random.uniform(0.3, 1.2)
                    else:
                        avg_response_time = random.uniform(0.5, 2.0)
                    
                    max_response_time = avg_response_time * random.uniform(2, 5)
                    cost = Decimal(str(base_requests * float(provider.cost_per_request)))
                    
                    usage, created = APIUsage.objects.get_or_create(
                        provider=provider,
                        date=current_date,
                        endpoint=endpoint,
                        defaults={
                            'request_count': base_requests,
                            'success_count': success_count,
                            'error_count': error_count,
                            'avg_response_time': avg_response_time,
                            'max_response_time': max_response_time,
                            'cost': cost
                        }
                    )
                    
                    if created:
                        created_usage += 1
        
        # Create some sample failover events
        primary_providers = providers.filter(priority__lte=2)
        fallback_providers = providers.filter(priority__gt=2)
        
        if primary_providers.exists() and fallback_providers.exists():
            for _ in range(random.randint(2, 8)):  # 2-8 failover events
                primary = random.choice(primary_providers)
                fallback = random.choice(fallback_providers)
                
                failed_time = timezone.now() - timedelta(
                    days=random.randint(0, days),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
                
                # Some failovers are resolved, some are not
                resolved_time = None
                if random.random() > 0.3:  # 70% chance of being resolved
                    resolved_time = failed_time + timedelta(
                        minutes=random.randint(5, 120)
                    )
                
                reasons = [
                    'Connection timeout',
                    'Rate limit exceeded',
                    'API key invalid',
                    'Service unavailable',
                    'Network error',
                    'HTTP 500 error'
                ]
                
                endpoints = primary.supported_endpoints
                
                failover = APIFailover.objects.create(
                    primary_provider=primary,
                    fallback_provider=fallback,
                    reason=random.choice(reasons),
                    endpoint=random.choice(endpoints) if endpoints else 'weather',
                    error_details=f'Error occurred at {failed_time.isoformat()}',
                    failed_at=failed_time,
                    resolved_at=resolved_time
                )
                
                created_failovers += 1
        
        # Update provider health based on recent usage
        for provider in providers:
            recent_usage = APIUsage.objects.filter(
                provider=provider,
                date__gte=date.today() - timedelta(days=7)
            ).aggregate(
                total_requests=models.Sum('request_count'),
                total_errors=models.Sum('error_count')
            )
            
            total_requests = recent_usage['total_requests'] or 0
            total_errors = recent_usage['total_errors'] or 0
            
            if total_requests > 0:
                success_rate = ((total_requests - total_errors) / total_requests) * 100
                provider.success_rate = success_rate
                provider.is_healthy = success_rate >= 80
                provider.error_count = total_errors
                provider.last_health_check = timezone.now()
                provider.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Created {created_usage} usage records and {created_failovers} failover events '
                f'for {days} days of sample data'
            )
        )