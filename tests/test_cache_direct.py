#!/usr/bin/env python
"""
Test caching system directly
"""
import os
import sys
import django
from django.conf import settings

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather247_backend.settings')
django.setup()

from weather_data.cache_manager import WeatherCacheManager
from django.core.cache import cache

def test_cache_direct():
    """Test caching system directly"""
    print("🗄️  Testing Cache System Directly...")
    
    # Test 1: Basic cache operations
    print("\n🔧 Testing Basic Cache Operations...")
    
    test_key = "test:basic"
    test_data = {"temperature": 25.5, "city": "Test City", "timestamp": "2025-08-13T12:00:00Z"}
    
    # Set cache
    success = WeatherCacheManager.set_cache(test_key, test_data, 'current_weather')
    if success:
        print("✅ Cache set successful")
    else:
        print("❌ Cache set failed")
    
    # Get cache
    cached_data = WeatherCacheManager.get_cache(test_key)
    if cached_data:
        print(f"✅ Cache get successful: {cached_data}")
        if cached_data.get('temperature') == 25.5:
            print("✅ Data integrity verified")
        else:
            print("❌ Data integrity failed")
    else:
        print("❌ Cache get failed")
    
    # Delete cache
    delete_success = WeatherCacheManager.delete_cache(test_key)
    if delete_success:
        print("✅ Cache delete successful")
    else:
        print("❌ Cache delete failed")
    
    # Verify deletion
    deleted_data = WeatherCacheManager.get_cache(test_key)
    if deleted_data is None:
        print("✅ Cache deletion verified")
    else:
        print("❌ Cache deletion failed")
    
    # Test 2: Cache key generation
    print("\n🔑 Testing Cache Key Generation...")
    
    weather_key = WeatherCacheManager.get_weather_cache_key("London", "GB")
    forecast_key = WeatherCacheManager.get_forecast_cache_key("London", 5)
    air_quality_key = WeatherCacheManager.get_air_quality_cache_key("London")
    
    print(f"✅ Weather key: {weather_key}")
    print(f"✅ Forecast key: {forecast_key}")
    print(f"✅ Air quality key: {air_quality_key}")
    
    # Test 3: Cache statistics
    print("\n📊 Testing Cache Statistics...")
    
    stats = WeatherCacheManager.get_cache_stats()
    print(f"✅ Cache stats: {stats}")
    
    # Test 4: TTL settings
    print("\n⏰ Testing TTL Settings...")
    
    ttl_key = "test:ttl"
    WeatherCacheManager.set_cache(ttl_key, "test data", 'current_weather')
    
    # Check if data exists
    ttl_data = WeatherCacheManager.get_cache(ttl_key)
    if ttl_data:
        print("✅ TTL cache set and retrieved")
    else:
        print("❌ TTL cache failed")
    
    # Test 5: City cache invalidation
    print("\n🗑️  Testing City Cache Invalidation...")
    
    # Set multiple cache entries for a city
    city_name = "TestCity"
    WeatherCacheManager.set_cache(
        WeatherCacheManager.get_weather_cache_key(city_name), 
        {"temp": 20}, 
        'current_weather'
    )
    WeatherCacheManager.set_cache(
        WeatherCacheManager.get_forecast_cache_key(city_name), 
        [{"temp": 21}], 
        'forecast'
    )
    
    # Verify they exist
    weather_exists = WeatherCacheManager.get_cache(WeatherCacheManager.get_weather_cache_key(city_name))
    forecast_exists = WeatherCacheManager.get_cache(WeatherCacheManager.get_forecast_cache_key(city_name))
    
    if weather_exists and forecast_exists:
        print("✅ Multiple cache entries set for city")
        
        # Invalidate all cache for the city
        WeatherCacheManager.invalidate_city_cache(city_name)
        
        # Verify they're gone
        weather_after = WeatherCacheManager.get_cache(WeatherCacheManager.get_weather_cache_key(city_name))
        forecast_after = WeatherCacheManager.get_cache(WeatherCacheManager.get_forecast_cache_key(city_name))
        
        if weather_after is None and forecast_after is None:
            print("✅ City cache invalidation successful")
        else:
            print("❌ City cache invalidation failed")
    else:
        print("❌ Failed to set multiple cache entries")
    
    # Test 6: Cache backend test
    print("\n🔌 Testing Cache Backend Connection...")
    
    try:
        # Test direct Django cache
        cache.set('test_connection', 'working', 30)
        result = cache.get('test_connection')
        cache.delete('test_connection')
        
        if result == 'working':
            print("✅ Django cache backend working")
        else:
            print("❌ Django cache backend not working")
    except Exception as e:
        print(f"❌ Django cache backend error: {e}")

if __name__ == '__main__':
    print("🧪 Weather247 Direct Cache Test")
    print("=" * 50)
    test_cache_direct()
    print("=" * 50)
    print("🏁 Direct cache test completed!")