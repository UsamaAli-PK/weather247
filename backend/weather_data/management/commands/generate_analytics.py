"""
Management command to generate weather analytics reports
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
import json
import os
from pathlib import Path

from weather_data.analytics import weather_analytics, health_monitor


class Command(BaseCommand):
    help = 'Generate weather analytics reports'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='analytics_reports',
            help='Directory to save analytics reports (default: analytics_reports)',
        )
        parser.add_argument(
            '--format',
            choices=['json', 'txt'],
            default='json',
            help='Output format (default: json)',
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Hours for API usage analysis (default: 24)',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Days for weather trends analysis (default: 7)',
        )
        parser.add_argument(
            '--health-check',
            action='store_true',
            help='Include system health check in report',
        )

    def handle(self, *args, **options):
        output_dir = options['output_dir']
        output_format = options['format']
        hours = options['hours']
        days = options['days']
        include_health = options['health_check']
        
        # Create output directory
        Path(output_dir).mkdir(exist_ok=True)
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        
        self.stdout.write(
            self.style.SUCCESS(f'Generating analytics reports...')
        )
        
        # Generate reports
        reports = {}
        
        try:
            # API Usage Analytics
            self.stdout.write('Generating API usage analytics...')
            reports['api_usage'] = weather_analytics.get_api_usage_stats(hours)
            
            # Cache Performance
            self.stdout.write('Generating cache performance analytics...')
            reports['cache_performance'] = weather_analytics.get_cache_performance_stats()
            
            # Data Freshness
            self.stdout.write('Generating data freshness analytics...')
            reports['data_freshness'] = weather_analytics.get_data_freshness_stats()
            
            # Weather Trends
            self.stdout.write('Generating weather trends analytics...')
            reports['weather_trends'] = weather_analytics.get_weather_trends(days)
            
            # System Health (if requested)
            if include_health:
                self.stdout.write('Generating system health report...')
                reports['system_health'] = health_monitor.get_system_health_report()
            
            # Save reports
            if output_format == 'json':
                self._save_json_reports(reports, output_dir, timestamp)
            else:
                self._save_text_reports(reports, output_dir, timestamp)
            
            self.stdout.write(
                self.style.SUCCESS(f'Analytics reports generated successfully!')
            )
            self.stdout.write(f'Reports saved to: {output_dir}/')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating reports: {e}')
            )

    def _save_json_reports(self, reports, output_dir, timestamp):
        """Save reports in JSON format"""
        
        # Save combined report
        combined_file = os.path.join(output_dir, f'weather_analytics_{timestamp}.json')
        with open(combined_file, 'w') as f:
            json.dump(reports, f, indent=2, default=str)
        
        self.stdout.write(f'Combined report: {combined_file}')
        
        # Save individual reports
        for report_type, data in reports.items():
            individual_file = os.path.join(output_dir, f'{report_type}_{timestamp}.json')
            with open(individual_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            self.stdout.write(f'{report_type.title()} report: {individual_file}')

    def _save_text_reports(self, reports, output_dir, timestamp):
        """Save reports in text format"""
        
        combined_file = os.path.join(output_dir, f'weather_analytics_{timestamp}.txt')
        
        with open(combined_file, 'w') as f:
            f.write("WEATHER247 ANALYTICS REPORT\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # API Usage Report
            if 'api_usage' in reports:
                api_data = reports['api_usage']
                f.write("API USAGE ANALYTICS\n")
                f.write("-" * 30 + "\n")
                f.write(f"Period: {api_data.get('period', 'N/A')}\n")
                f.write(f"Total Requests: {api_data.get('total_requests', 0)}\n")
                f.write(f"Unique Cities: {api_data.get('unique_cities', 0)}\n")
                f.write(f"Avg Requests/Hour: {api_data.get('avg_requests_per_hour', 0):.2f}\n")
                
                if 'top_cities' in api_data:
                    f.write("\nTop Cities by Requests:\n")
                    for i, city in enumerate(api_data['top_cities'][:5], 1):
                        f.write(f"  {i}. {city.get('city__name', 'Unknown')}: {city.get('request_count', 0)} requests\n")
                f.write("\n")
            
            # Cache Performance Report
            if 'cache_performance' in reports:
                cache_data = reports['cache_performance']
                f.write("CACHE PERFORMANCE\n")
                f.write("-" * 30 + "\n")
                f.write(f"Estimated Hit Rate: {cache_data.get('estimated_hit_rate', 0)}%\n")
                f.write(f"Cache Efficiency: {cache_data.get('cache_efficiency', 'Unknown')}\n")
                f.write(f"Total Requests (24h): {cache_data.get('total_requests_24h', 0)}\n")
                
                if 'recommendations' in cache_data:
                    f.write("\nRecommendations:\n")
                    for rec in cache_data['recommendations']:
                        f.write(f"  • {rec}\n")
                f.write("\n")
            
            # Data Freshness Report
            if 'data_freshness' in reports:
                fresh_data = reports['data_freshness']
                f.write("DATA FRESHNESS\n")
                f.write("-" * 30 + "\n")
                f.write(f"Total Cities: {fresh_data.get('total_cities', 0)}\n")
                f.write(f"Health Score: {fresh_data.get('health_score', 0)}%\n")
                f.write(f"Health Status: {fresh_data.get('health_status', 'Unknown')}\n")
                
                if 'freshness_percentages' in fresh_data:
                    percentages = fresh_data['freshness_percentages']
                    f.write(f"\nFreshness Breakdown:\n")
                    f.write(f"  Very Fresh (<15min): {percentages.get('very_fresh', 0)}%\n")
                    f.write(f"  Fresh (15-30min): {percentages.get('fresh', 0)}%\n")
                    f.write(f"  Stale (30min-2h): {percentages.get('stale', 0)}%\n")
                    f.write(f"  Very Stale (2-6h): {percentages.get('very_stale', 0)}%\n")
                    f.write(f"  No Data (>6h): {percentages.get('no_data', 0)}%\n")
                f.write("\n")
            
            # Weather Trends Report
            if 'weather_trends' in reports:
                trends_data = reports['weather_trends']
                f.write("WEATHER TRENDS\n")
                f.write("-" * 30 + "\n")
                f.write(f"Period: {trends_data.get('period', 'N/A')}\n")
                f.write(f"Total Data Points: {trends_data.get('total_data_points', 0)}\n")
                
                if 'overall_stats' in trends_data:
                    stats = trends_data['overall_stats']
                    f.write(f"\nOverall Statistics:\n")
                    f.write(f"  Average Temperature: {stats.get('avg_temperature', 0)}°C\n")
                    f.write(f"  Max Temperature: {stats.get('max_temperature', 0)}°C\n")
                    f.write(f"  Min Temperature: {stats.get('min_temperature', 0)}°C\n")
                    f.write(f"  Average Humidity: {stats.get('avg_humidity', 0)}%\n")
                f.write("\n")
            
            # System Health Report
            if 'system_health' in reports:
                health_data = reports['system_health']
                f.write("SYSTEM HEALTH\n")
                f.write("-" * 30 + "\n")
                f.write(f"Overall Status: {health_data.get('overall_status', 'Unknown').upper()}\n")
                
                if 'alerts' in health_data and health_data['alerts']:
                    f.write(f"\nAlerts ({len(health_data['alerts'])}):\n")
                    for alert in health_data['alerts']:
                        f.write(f"  • [{alert.get('severity', 'unknown').upper()}] {alert.get('message', 'No message')}\n")
                
                if 'warnings' in health_data and health_data['warnings']:
                    f.write(f"\nWarnings ({len(health_data['warnings'])}):\n")
                    for warning in health_data['warnings']:
                        f.write(f"  • {warning.get('message', 'No message')}\n")
                f.write("\n")
        
        self.stdout.write(f'Text report: {combined_file}')