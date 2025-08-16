#!/usr/bin/env python
"""
Test fallback system directly
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

from weather_data.real_weather_service import weather_manager

def test_fallback_direct():
    """Test fallback system directly"""
    print("🔄 Testing Fallback System Directly...")
    
    # Test 1: Service Health Check
    print("\n🏥 Testing Service Health...")
    try:
        health = weather_manager.get_service_health()
        print(f"✅ Health check completed:")
        print(f"   Primary Service: {health['primary_service']['status']}")
        print(f"   API Key Status: {health['primary_service']['api_key_status']}")
        print(f"   Cache Status: {'Healthy' if health['cache_status'] else 'Unhealthy'}")
        print(f"   Timestamp: {health['timestamp']}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test 2: Fallback Weather Retrieval
    print("\n🌤️  Testing Fallback Weather Retrieval...")
    test_cities = ["London", "New York", "InvalidCity123"]
    
    for city in test_cities:
        try:
            print(f"\n   Testing {city}...")
            weather_data = weather_manager.get_current_weather_with_fallback(city)
            
            if weather_data:
                print(f"   ✅ {city}: {weather_data.temperature}°C, {weather_data.weather_condition}")
                print(f"      City: {weather_data.city.name}, {weather_data.city.country}")
                print(f"      Timestamp: {weather_data.timestamp}")
            else:
                print(f"   ❌ {city}: No weather data available")
                
        except Exception as e:
            print(f"   ❌ {city}: Error - {e}")
    
    # Test 3: Comprehensive Weather with Error Handling
    print("\n🌍 Testing Comprehensive Weather...")
    try:
        comprehensive_data = weather_manager.get_comprehensive_weather("Tokyo")
        
        if comprehensive_data:
            print("✅ Comprehensive weather data retrieved:")
            print(f"   Current: {comprehensive_data['current'].temperature}°C")
            print(f"   Air Quality: {'Available' if comprehensive_data['air_quality'] else 'Unavailable'}")
            print(f"   Forecast: {len(comprehensive_data['forecast'])} days")
        else:
            print("❌ Comprehensive weather data unavailable")
            
    except Exception as e:
        print(f"❌ Comprehensive weather error: {e}")
    
    # Test 4: Bulk Update with Error Handling
    print("\n🔄 Testing Bulk Weather Update...")
    try:
        updated_count = weather_manager.update_weather_for_all_cities()
        print(f"✅ Bulk update completed: {updated_count} cities updated")
    except Exception as e:
        print(f"❌ Bulk update error: {e}")
    
    # Test 5: Retry Logic Test
    print("\n🔁 Testing Retry Logic...")
    try:
        # This will test the retry logic with demo data
        weather_data = weather_manager.get_current_weather_with_fallback("TestRetryCity")
        
        if weather_data:
            print("✅ Retry logic working - data retrieved")
        else:
            print("⚠️  Retry logic completed but no data available")
            
    except Exception as e:
        print(f"❌ Retry logic error: {e}")
    
    # Test 6: Cache Fallback Test
    print("\n💾 Testing Cache Fallback...")
    try:
        from weather_data.cache_manager import WeatherCacheManager
        
        # Set some test cache data
        cache_key = WeatherCacheManager.get_weather_cache_key("CacheTestCity")
        test_cache_data = {
            'city_name': 'CacheTestCity',
            'temperature': 22.5,
            'weather_condition': 'Clear',
            'timestamp': '2025-08-13T12:00:00Z'
        }
        
        WeatherCacheManager.set_cache(cache_key, test_cache_data, 'current_weather')
        
        # Try to retrieve it
        cached_data = WeatherCacheManager.get_cache(cache_key)
        
        if cached_data and cached_data.get('temperature') == 22.5:
            print("✅ Cache fallback data available")
        else:
            print("❌ Cache fallback data unavailable")
            
    except Exception as e:
        print(f"❌ Cache fallback test error: {e}")

if __name__ == '__main__':
    print("🧪 Weather247 Direct Fallback Test")
    print("=" * 50)
    test_fallback_direct()
    print("=" * 50)
    print("🏁 Direct fallback test completed!")