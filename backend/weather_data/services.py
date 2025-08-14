"""
Weather API Services for integrating with external weather providers
"""
import requests
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from .models import City, WeatherData, AirQualityData, WeatherForecast

logger = logging.getLogger('weather247')


class OpenWeatherMapService:
    """Service for integrating with OpenWeatherMap API"""
    
    def __init__(self):
        self.api_key = settings.OPENWEATHERMAP_API_KEY
        self.base_url = settings.OPENWEATHER_BASE_URL
        
    def get_current_weather(self, city_name, country_code=None):
        """Get current weather data for a city"""
        try:
            # Build query string
            query = city_name
            if country_code:
                query = f"{city_name},{country_code}"
                
            url = f"{self.base_url}/weather"
            params = {
                'q': query,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Get or create city
            city, created = City.objects.get_or_create(
                name=data['name'],
                country=data['sys']['country'],
                defaults={
                    'latitude': data['coord']['lat'],
                    'longitude': data['coord']['lon'],
                }
            )
            
            # Create weather data
            weather_data = WeatherData.objects.create(
                city=city,
                temperature=data['main']['temp'],
                feels_like=data['main']['feels_like'],
                humidity=data['main']['humidity'],
                pressure=data['main']['pressure'],
                visibility=data.get('visibility', 0) / 1000,  # Convert to km
                wind_speed=data['wind']['speed'] * 3.6,  # Convert m/s to km/h
                wind_direction=data['wind'].get('deg', 0),
                weather_condition=data['weather'][0]['main'],
                weather_description=data['weather'][0]['description'],
                weather_icon=data['weather'][0]['icon'],
                cloudiness=data['clouds']['all'],
                sunrise=datetime.fromtimestamp(data['sys']['sunrise']),
                sunset=datetime.fromtimestamp(data['sys']['sunset']),
                data_source='openweathermap'
            )
            
            logger.info(f"Successfully fetched weather data for {city.name}")
            return weather_data
            
        except requests.RequestException as e:
            logger.error(f"Error fetching weather data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    def get_forecast(self, city_name, country_code=None, days=5):
        """Get weather forecast for a city"""
        try:
            query = city_name
            if country_code:
                query = f"{city_name},{country_code}"
                
            url = f"{self.base_url}/forecast"
            params = {
                'q': query,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Get or create city
            city, created = City.objects.get_or_create(
                name=data['city']['name'],
                country=data['city']['country'],
                defaults={
                    'latitude': data['city']['coord']['lat'],
                    'longitude': data['city']['coord']['lon'],
                }
            )
            
            forecasts = []
            for item in data['list'][:days * 8]:  # 8 forecasts per day (3-hour intervals)
                forecast_date = datetime.fromtimestamp(item['dt'])
                
                forecast, created = WeatherForecast.objects.get_or_create(
                    city=city,
                    forecast_date=forecast_date,
                    data_source='openweathermap',
                    defaults={
                        'temperature_min': item['main']['temp_min'],
                        'temperature_max': item['main']['temp_max'],
                        'temperature_avg': item['main']['temp'],
                        'humidity': item['main']['humidity'],
                        'pressure': item['main']['pressure'],
                        'wind_speed': item['wind']['speed'] * 3.6,
                        'wind_direction': item['wind'].get('deg', 0),
                        'weather_condition': item['weather'][0]['main'],
                        'weather_description': item['weather'][0]['description'],
                        'weather_icon': item['weather'][0]['icon'],
                        'cloudiness': item['clouds']['all'],
                        'precipitation_probability': item.get('pop', 0),
                        'precipitation_amount': item.get('rain', {}).get('3h', 0),
                    }
                )
                forecasts.append(forecast)
            
            logger.info(f"Successfully fetched forecast for {city.name}")
            return forecasts
            
        except requests.RequestException as e:
            logger.error(f"Error fetching forecast data: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
    
    def get_air_quality(self, lat, lon):
        """Get air quality data for coordinates"""
        try:
            url = f"{self.base_url}/air_pollution"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Find city by coordinates
            city = City.objects.filter(
                latitude__range=(lat - 0.1, lat + 0.1),
                longitude__range=(lon - 0.1, lon + 0.1)
            ).first()
            
            if not city:
                return None
                
            components = data['list'][0]['components']
            air_quality = AirQualityData.objects.create(
                city=city,
                aqi=data['list'][0]['main']['aqi'],
                co=components['co'],
                no=components['no'],
                no2=components['no2'],
                o3=components['o3'],
                so2=components['so2'],
                pm2_5=components['pm2_5'],
                pm10=components['pm10'],
                nh3=components['nh3'],
                data_source='openweathermap'
            )
            
            logger.info(f"Successfully fetched air quality data for {city.name}")
            return air_quality
            
        except requests.RequestException as e:
            logger.error(f"Error fetching air quality data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None


class AccuWeatherService:
    """Service for integrating with AccuWeather API"""
    
    def __init__(self):
        self.api_key = settings.ACCUWEATHER_API_KEY
        self.base_url = settings.ACCUWEATHER_BASE_URL
        
    def get_location_key(self, city_name, country_code=None):
        """Get AccuWeather location key for a city"""
        try:
            url = f"{self.base_url}/locations/v1/cities/search"
            params = {
                'apikey': self.api_key,
                'q': city_name
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data:
                return data[0]['Key']
            return None
            
        except requests.RequestException as e:
            logger.error(f"Error getting location key: {e}")
            return None
    
    def get_current_conditions(self, location_key):
        """Get current weather conditions from AccuWeather"""
        try:
            url = f"{self.base_url}/currentconditions/v1/{location_key}"
            params = {
                'apikey': self.api_key,
                'details': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data:
                return data[0]
            return None
            
        except requests.RequestException as e:
            logger.error(f"Error fetching AccuWeather conditions: {e}")
            return None


class WeatherDataManager:
    """Manager for coordinating weather data from multiple sources"""
    
    def __init__(self):
        self.openweather = OpenWeatherMapService()
        self.accuweather = AccuWeatherService()
    
    def get_comprehensive_weather(self, city_name, country_code=None):
        """Get weather data from multiple sources"""
        cache_key = f"weather_{city_name}_{country_code}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        # Get primary data from OpenWeatherMap
        weather_data = self.openweather.get_current_weather(city_name, country_code)
        
        if weather_data:
            # Get air quality data
            air_quality = self.openweather.get_air_quality(
                weather_data.city.latitude,
                weather_data.city.longitude
            )
            
            # Get forecast data
            forecast = self.openweather.get_forecast(city_name, country_code)
            
            result = {
                'current': weather_data,
                'air_quality': air_quality,
                'forecast': forecast
            }
            
            # Cache for 10 minutes
            cache.set(cache_key, result, 600)
            return result
        
        return None
    
    def update_weather_for_all_cities(self):
        """Update weather data for all active cities"""
        cities = City.objects.filter(is_active=True)
        updated_count = 0
        
        for city in cities:
            try:
                weather_data = self.openweather.get_current_weather(city.name, city.country)
                if weather_data:
                    updated_count += 1
                    logger.info(f"Updated weather for {city.name}")
            except Exception as e:
                logger.error(f"Failed to update weather for {city.name}: {e}")
        
        logger.info(f"Updated weather data for {updated_count} cities")
        return updated_count


# Global instance
weather_manager = WeatherDataManager()

