#!/usr/bin/env python
"""
Test the WeatherManager directly
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
from weather_data.models import City, WeatherData

def test_weather_manager():
    """Test the weather manager directly"""
    print("🧪 Testing WeatherManager...")
    
    # Test cities
    test_cities = ['New York', 'London', 'Tokyo', 'Paris']
    
    for city_name in test_cities:
        print(f"\n🌤️  Testing {city_name}...")
        
        try:
            # Test comprehensive weather
            result = weather_manager.get_comprehensive_weather(city_name)
            
            if result:
                current = result['current']
                print(f"✅ Success! Temperature: {current.temperature}°C")
                print(f"   Condition: {current.weather_condition}")
                print(f"   City ID: {current.city.id}")
            else:
                print("❌ get_comprehensive_weather returned None")
                
                # Try direct OpenWeatherMap service
                direct_result = weather_manager.openweather.get_current_weather(city_name)
                if direct_result:
                    print(f"✅ Direct service works! Temperature: {direct_result.temperature}°C")
                else:
                    print("❌ Direct service also failed")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Check database
    print(f"\n📊 Database Status:")
    print(f"   Cities in DB: {City.objects.count()}")
    print(f"   Weather records: {WeatherData.objects.count()}")
    
    # Show recent weather data
    recent_weather = WeatherData.objects.order_by('-timestamp')[:5]
    print(f"\n🕒 Recent Weather Records:")
    for weather in recent_weather:
        print(f"   {weather.city.name}: {weather.temperature}°C at {weather.timestamp}")

if __name__ == '__main__':
    test_weather_manager()