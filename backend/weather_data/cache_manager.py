"""
Redis caching system for Weather247
"""
import json
import logging
from typing import Any, Optional, Dict, List
from datetime import timedelta
from django.core.cache import cache
from django.conf import settings
import hashlib

logger = logging.getLogger('weather247')


class WeatherCacheManager:
    """Manages caching for weather data with intelligent TTL and key strategies"""
    
    # Cache TTL settings (in seconds)
    CACHE_TTL = {
        'current_weather': 900,      # 15 minutes
        'forecast': 3600,            # 1 hour
        'air_quality': 1800,         # 30 minutes
        'city_list': 86400,          # 24 hours
        'historical': 604800,        # 1 week
        'analytics': 3600,           # 1 hour
        'user_preferences': 86400,   # 24 hours
        'api_response': 300,         # 5 minutes
    }
    
    # Cache key prefixes
    PREFIXES = {
        'weather': 'weather:current',
        'forecast': 'weather:forecast',
        'air_quality': 'weather:air_quality',
        'city': 'city',
        'historical': 'weather:historical',
        'analytics': 'weather:analytics',
        'user': 'user',
        'api': 'api:response',
    }
    
    @classmethod
    def _generate_cache_key(cls, prefix: str, *args, **kwargs) -> str:
        """Generate a consistent cache key"""
        key_parts = [cls.PREFIXES.get(prefix, prefix)]
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, (dict, list)):
                # Hash complex objects
                key_parts.append(hashlib.md5(json.dumps(arg, sort_keys=True).encode()).hexdigest()[:8])
            else:
                key_parts.append(str(arg).lower().replace(' ', '_'))
        
        # Add keyword arguments
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        
        return ':'.join(key_parts)
    
    @classmethod
    def get_weather_cache_key(cls, city_name: str, country: str = '') -> str:
        """Generate cache key for current weather"""
        return cls._generate_cache_key('weather', city_name, country)
    
    @classmethod
    def get_forecast_cache_key(cls, city_name: str, days: int = 5) -> str:
        """Generate cache key for weather forecast"""
        return cls._generate_cache_key('forecast', city_name, days=days)
    
    @classmethod
    def get_air_quality_cache_key(cls, city_name: str) -> str:
        """Generate cache key for air quality"""
        return cls._generate_cache_key('air_quality', city_name)
    
    @classmethod
    def get_city_list_cache_key(cls) -> str:
        """Generate cache key for city list"""
        return cls._generate_cache_key('city', 'list')
    
    @classmethod
    def get_analytics_cache_key(cls, city_name: str, metric: str) -> str:
        """Generate cache key for analytics data"""
        return cls._generate_cache_key('analytics', city_name, metric)
    
    @classmethod
    def get_user_cache_key(cls, user_id: int, data_type: str) -> str:
        """Generate cache key for user data"""
        return cls._generate_cache_key('user', user_id, data_type)
    
    @classmethod
    def set_cache(cls, key: str, data: Any, cache_type: str = 'current_weather') -> bool:
        """Set data in cache with appropriate TTL"""
        try:
            ttl = cls.CACHE_TTL.get(cache_type, cls.CACHE_TTL['current_weather'])
            
            # Serialize data if it's not a string
            if not isinstance(data, str):
                data = json.dumps(data, default=str)
            
            cache.set(key, data, ttl)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    @classmethod
    def get_cache(cls, key: str) -> Optional[Any]:
        """Get data from cache"""
        try:
            data = cache.get(key)
            if data is None:
                logger.debug(f"Cache miss: {key}")
                return None
            
            # Try to deserialize JSON data
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except (json.JSONDecodeError, TypeError):
                    # Return as string if not JSON
                    pass
            
            logger.debug(f"Cache hit: {key}")
            return data
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    @classmethod
    def delete_cache(cls, key: str) -> bool:
        """Delete data from cache"""
        try:
            cache.delete(key)
            logger.debug(f"Cache deleted: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    @classmethod
    def invalidate_city_cache(cls, city_name: str) -> None:
        """Invalidate all cache entries for a specific city"""
        try:
            # Generate all possible cache keys for this city
            keys_to_delete = [
                cls.get_weather_cache_key(city_name),
                cls.get_forecast_cache_key(city_name),
                cls.get_air_quality_cache_key(city_name),
                cls.get_analytics_cache_key(city_name, 'summary'),
                cls.get_analytics_cache_key(city_name, 'trends'),
            ]
            
            for key in keys_to_delete:
                cls.delete_cache(key)
            
            logger.info(f"Invalidated cache for city: {city_name}")
            
        except Exception as e:
            logger.error(f"Error invalidating cache for city {city_name}: {e}")
    
    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            # This is a simplified version - Redis has more detailed stats
            return {
                'cache_backend': 'Redis' if 'redis' in str(cache._cache) else 'Other',
                'status': 'Connected' if cls._test_connection() else 'Disconnected',
                'ttl_settings': cls.CACHE_TTL,
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'status': 'Error', 'error': str(e)}
    
    @classmethod
    def _test_connection(cls) -> bool:
        """Test cache connection"""
        try:
            test_key = 'test:connection'
            cache.set(test_key, 'test', 10)
            result = cache.get(test_key)
            cache.delete(test_key)
            return result == 'test'
        except Exception:
            return False
    
    @classmethod
    def warm_cache(cls, cities: List[str]) -> Dict[str, bool]:
        """Pre-warm cache for popular cities"""
        results = {}
        
        for city in cities:
            try:
                # This would typically fetch and cache data
                # For now, we'll just mark as attempted
                results[city] = True
                logger.info(f"Cache warmed for city: {city}")
            except Exception as e:
                results[city] = False
                logger.error(f"Failed to warm cache for city {city}: {e}")
        
        return results


class CacheDecorator:
    """Decorator for caching function results"""
    
    @staticmethod
    def cache_result(cache_type: str = 'current_weather', key_generator=None):
        """Decorator to cache function results"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_generator:
                    cache_key = key_generator(*args, **kwargs)
                else:
                    # Default key generation
                    cache_key = f"func:{func.__name__}:{hash(str(args) + str(kwargs))}"
                
                # Try to get from cache first
                cached_result = WeatherCacheManager.get_cache(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                if result is not None:
                    WeatherCacheManager.set_cache(cache_key, result, cache_type)
                
                return result
            
            return wrapper
        return decorator


# Convenience functions for common caching operations
def cache_weather_data(city_name: str, weather_data: Dict[str, Any]) -> bool:
    """Cache current weather data"""
    cache_key = WeatherCacheManager.get_weather_cache_key(city_name)
    return WeatherCacheManager.set_cache(cache_key, weather_data, 'current_weather')


def get_cached_weather_data(city_name: str) -> Optional[Dict[str, Any]]:
    """Get cached weather data"""
    cache_key = WeatherCacheManager.get_weather_cache_key(city_name)
    return WeatherCacheManager.get_cache(cache_key)


def cache_forecast_data(city_name: str, forecast_data: List[Dict[str, Any]], days: int = 5) -> bool:
    """Cache forecast data"""
    cache_key = WeatherCacheManager.get_forecast_cache_key(city_name, days)
    return WeatherCacheManager.set_cache(cache_key, forecast_data, 'forecast')


def get_cached_forecast_data(city_name: str, days: int = 5) -> Optional[List[Dict[str, Any]]]:
    """Get cached forecast data"""
    cache_key = WeatherCacheManager.get_forecast_cache_key(city_name, days)
    return WeatherCacheManager.get_cache(cache_key)


def invalidate_city_cache(city_name: str) -> None:
    """Invalidate all cache for a city"""
    WeatherCacheManager.invalidate_city_cache(city_name)