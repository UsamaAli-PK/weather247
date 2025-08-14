"""
Performance optimization middleware
"""
import gzip
import json
import time
import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from io import BytesIO

logger = logging.getLogger('weather247')


class ResponseCompressionMiddleware(MiddlewareMixin):
    """Middleware to compress API responses"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_response(self, request, response):
        # Only compress JSON responses
        if not isinstance(response, JsonResponse):
            return response
        
        # Only compress if client accepts gzip
        if 'gzip' not in request.META.get('HTTP_ACCEPT_ENCODING', ''):
            return response
        
        # Only compress responses larger than 1KB
        if len(response.content) < 1024:
            return response
        
        try:
            # Compress the response content
            buffer = BytesIO()
            with gzip.GzipFile(fileobj=buffer, mode='wb', compresslevel=6) as f:
                f.write(response.content)
            
            compressed_content = buffer.getvalue()
            
            # Only use compression if it reduces size by at least 10%
            if len(compressed_content) < len(response.content) * 0.9:
                response.content = compressed_content
                response['Content-Encoding'] = 'gzip'
                response['Content-Length'] = str(len(compressed_content))
                
                # Log compression ratio for monitoring
                ratio = len(compressed_content) / len(response.content)
                logger.debug(f'Response compressed: {ratio:.2f} ratio')
            
        except Exception as e:
            logger.error(f'Response compression error: {e}')
        
        return response


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """Middleware to monitor API performance"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            # Log slow requests (>1 second)
            if duration > 1.0:
                logger.warning(
                    f'Slow request: {request.method} {request.path} took {duration:.2f}s'
                )
            
            # Store performance metrics in cache for analytics
            try:
                cache_key = f'perf_metrics:{request.path.replace("/", "_")}'
                metrics = cache.get(cache_key, {'count': 0, 'total_time': 0, 'max_time': 0})
                
                metrics['count'] += 1
                metrics['total_time'] += duration
                metrics['max_time'] = max(metrics['max_time'], duration)
                metrics['avg_time'] = metrics['total_time'] / metrics['count']
                
                cache.set(cache_key, metrics, 3600)  # Store for 1 hour
                
            except Exception as e:
                logger.error(f'Performance metrics storage error: {e}')
        
        return response


class CacheControlMiddleware(MiddlewareMixin):
    """Middleware to add appropriate cache headers"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_response(self, request, response):
        # Add cache headers for weather data endpoints
        if request.path.startswith('/api/weather/'):
            if 'current' in request.path or 'weather-data' in request.path:
                # Weather data can be cached for 5 minutes
                response['Cache-Control'] = 'public, max-age=300'
            elif 'cities' in request.path:
                # City data can be cached for 1 hour
                response['Cache-Control'] = 'public, max-age=3600'
            elif 'analytics' in request.path:
                # Analytics data can be cached for 15 minutes
                response['Cache-Control'] = 'public, max-age=900'
            else:
                # Default: no cache for other endpoints
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        
        return response


class DatabaseQueryOptimizationMiddleware(MiddlewareMixin):
    """Middleware to monitor and optimize database queries"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        from django.db import connection
        request._queries_before = len(connection.queries)
        return None
    
    def process_response(self, request, response):
        if hasattr(request, '_queries_before'):
            from django.db import connection
            
            queries_count = len(connection.queries) - request._queries_before
            
            # Log requests with many database queries
            if queries_count > 10:
                logger.warning(
                    f'High DB query count: {request.method} {request.path} '
                    f'executed {queries_count} queries'
                )
                
                # Log slow queries for debugging
                for query in connection.queries[-queries_count:]:
                    if float(query['time']) > 0.1:  # Queries slower than 100ms
                        logger.warning(
                            f'Slow query ({query["time"]}s): {query["sql"][:200]}...'
                        )
        
        return response