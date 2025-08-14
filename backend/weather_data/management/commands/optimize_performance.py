"""
Management command to optimize weather system performance
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone
import time

from weather_data.performance import (
    db_optimizer, cache_optimizer, performance_monitor
)


class Command(BaseCommand):
    help = 'Optimize weather system performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze-only',
            action='store_true',
            help='Only analyze performance, do not apply optimizations',
        )
        parser.add_argument(
            '--optimize-db',
            action='store_true',
            help='Optimize database queries and indexes',
        )
        parser.add_argument(
            '--optimize-cache',
            action='store_true',
            help='Optimize cache configuration and warming',
        )
        parser.add_argument(
            '--cleanup-old-data',
            action='store_true',
            help='Clean up old weather data',
        )
        parser.add_argument(
            '--days-to-keep',
            type=int,
            default=30,
            help='Days of data to keep during cleanup (default: 30)',
        )

    def handle(self, *args, **options):
        analyze_only = options['analyze_only']
        optimize_db = options['optimize_db']
        optimize_cache = options['optimize_cache']
        cleanup_data = options['cleanup_old_data']
        days_to_keep = options['days_to_keep']
        
        self.stdout.write(
            self.style.SUCCESS('Starting performance optimization...')
        )
        
        # Always perform analysis first
        self.analyze_performance()
        
        if analyze_only:
            self.stdout.write(
                self.style.SUCCESS('Analysis completed. Use specific flags to apply optimizations.')
            )
            return
        
        # Apply optimizations based on flags
        if optimize_db or not any([optimize_db, optimize_cache, cleanup_data]):
            self.optimize_database()
        
        if optimize_cache or not any([optimize_db, optimize_cache, cleanup_data]):
            self.optimize_cache_system()
        
        if cleanup_data:
            self.cleanup_old_data(days_to_keep)
        
        # Final performance check
        self.stdout.write('\n' + '='*50)
        self.stdout.write('Final performance analysis:')
        self.analyze_performance()
        
        self.stdout.write(
            self.style.SUCCESS('Performance optimization completed!')
        )

    def analyze_performance(self):
        """Analyze current performance"""
        self.stdout.write('\nAnalyzing performance...')
        
        try:
            # Get performance metrics
            metrics = performance_monitor.get_performance_metrics()
            
            self.stdout.write('Database Performance:')
            db_stats = metrics.get('database', {})
            self.stdout.write(f'  Total queries: {db_stats.get("total_queries", 0)}')
            self.stdout.write(f'  Slow queries: {len(db_stats.get("slow_queries", []))}')
            
            if db_stats.get('slow_queries'):
                self.stdout.write('  Slow query examples:')
                for query in db_stats['slow_queries'][:3]:
                    self.stdout.write(f'    {query["time"]}s: {query["sql"][:100]}...')
            
            # Analyze bottlenecks
            analysis = performance_monitor.analyze_performance_bottlenecks()
            
            bottlenecks = analysis.get('bottlenecks', [])
            if bottlenecks:
                self.stdout.write('\nPerformance Issues Found:')
                for bottleneck in bottlenecks:
                    severity_color = self.style.ERROR if bottleneck['severity'] == 'high' else self.style.WARNING
                    self.stdout.write(
                        severity_color(f'  [{bottleneck["severity"].upper()}] {bottleneck["issue"]}')
                    )
            else:
                self.stdout.write(self.style.SUCCESS('\nNo major performance issues detected'))
            
            recommendations = analysis.get('recommendations', [])
            if recommendations:
                self.stdout.write('\nRecommendations:')
                for rec in recommendations:
                    self.stdout.write(f'  • {rec}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error analyzing performance: {e}')
            )

    def optimize_database(self):
        """Optimize database performance"""
        self.stdout.write('\nOptimizing database...')
        
        try:
            # Check if indexes exist
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT indexname FROM pg_indexes 
                    WHERE tablename LIKE 'weather_data_%' 
                    AND indexname LIKE 'idx_%'
                """)
                indexes = cursor.fetchall()
                
                if indexes:
                    self.stdout.write(f'  Found {len(indexes)} performance indexes')
                else:
                    self.stdout.write('  No performance indexes found - run migrations to add them')
            
            # Analyze table statistics
            cursor.execute("ANALYZE;")
            self.stdout.write('  Database statistics updated')
            
            self.stdout.write(self.style.SUCCESS('  Database optimization completed'))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error optimizing database: {e}')
            )

    def optimize_cache_system(self):
        """Optimize cache system"""
        self.stdout.write('\nOptimizing cache system...')
        
        try:
            # Optimize cache keys
            key_optimization = cache_optimizer.optimize_cache_keys()
            self.stdout.write(f'  Analyzed {key_optimization["key_patterns_analyzed"]} cache key patterns')
            self.stdout.write(f'  Applied {key_optimization["optimizations_applied"]} optimizations')
            
            # Implement cache warming
            warming_result = cache_optimizer.implement_cache_warming_strategy()
            
            if 'error' not in warming_result:
                self.stdout.write(f'  Warmed cache for {warming_result["cities_warmed"]} cities')
                self.stdout.write(f'  Success rate: {warming_result["success_rate"]}')
            else:
                self.stdout.write(
                    self.style.WARNING(f'  Cache warming error: {warming_result["error"]}')
                )
            
            self.stdout.write(self.style.SUCCESS('  Cache optimization completed'))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error optimizing cache: {e}')
            )

    def cleanup_old_data(self, days_to_keep):
        """Clean up old weather data"""
        self.stdout.write(f'\nCleaning up data older than {days_to_keep} days...')
        
        try:
            start_time = time.time()
            
            # Use optimized cleanup
            deleted_count = db_optimizer.cleanup_old_data_optimized(
                days_to_keep=days_to_keep,
                batch_size=1000
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.stdout.write(f'  Deleted {deleted_count} old weather records')
            self.stdout.write(f'  Cleanup completed in {duration:.2f} seconds')
            
            self.stdout.write(self.style.SUCCESS('  Data cleanup completed'))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error cleaning up data: {e}')
            )

    def get_database_size_info(self):
        """Get database size information"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        attname,
                        n_distinct,
                        correlation
                    FROM pg_stats 
                    WHERE tablename LIKE 'weather_data_%'
                    ORDER BY tablename, attname;
                """)
                
                stats = cursor.fetchall()
                return stats
                
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Could not get database size info: {e}')
            )
            return []