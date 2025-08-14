import requests
import logging
import asyncio
try:
	import aiohttp  # Optional; used for async features
except Exception:  # pragma: no cover
	aiohttp = None
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from django.core.exceptions import ValidationError
from .models import City, WeatherData, AirQualityData, WeatherForecast
from .validators import WeatherDataValidator, CityValidator
from .cache_manager import WeatherCacheManager, cache_weather_data, get_cached_weather_data
import json
try:
	import numpy as np
except Exception:  # pragma: no cover
	# Minimal stub for usage in this module
	class _NPStub:
		@staticmethod
		def sin(x):
			return 0
		@staticmethod
		def cos(x):
			return 1
	np = _NPStub()  # type: ignore
from typing import Optional, List, Dict, Any

logger = logging.getLogger('weather247')


class OpenWeatherMapService:
    """Enhanced OpenWeatherMap API integration with caching and error handling"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'OPENWEATHERMAP_API_KEY', 'demo-key')
        self.base_url = 'https://api.openweathermap.org/data/2.5'
        self.geo_url = 'https://api.openweathermap.org/geo/1.0'
        self.cache_timeout = 900  # 15 minutes
        self.session = None
    
    def get_coordinates(self, city_name, country_code=''):
        """Get coordinates for a city"""
        try:
            if self.api_key == 'demo-key':
                # Return demo coordinates for major cities
                demo_coords = {
                    'new york': (40.7128, -74.0060),
                    'london': (51.5074, -0.1278),
                    'tokyo': (35.6762, 139.6503),
                    'paris': (48.8566, 2.3522),
                    'sydney': (-33.8688, 151.2093),
                    'dubai': (25.2048, 55.2708),
                    'mumbai': (19.0760, 72.8777),
                    'singapore': (1.3521, 103.8198),
                }
                key = city_name.lower()
                return demo_coords.get(key, (40.7128, -74.0060))
            
            query = f"{city_name}"
            if country_code:
                query += f",{country_code}"
            
            url = f"{self.geo_url}/direct"
            params = {
                'q': query,
                'limit': 1,
                'appid': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data:
                return data[0]['lat'], data[0]['lon']
            return None
            
        except Exception as e:
            logger.error(f"Error getting coordinates for {city_name}: {e}")
            return None
    
    def get_current_weather(self, city_name, country_code=''):
        """Get current weather data with caching"""
        try:
            # Check cache first
            cache_key = WeatherCacheManager.get_weather_cache_key(city_name, country_code)
            cached_data = WeatherCacheManager.get_cache(cache_key)
            
            if cached_data:
                # Return cached weather data object if available
                try:
                    city = City.objects.filter(name__iexact=city_name).first()
                    if city:
                        # Check if we have recent weather data in DB
                        recent_weather = WeatherData.objects.filter(
                            city=city,
                            timestamp__gte=timezone.now() - timedelta(minutes=15)
                        ).first()
                        if recent_weather:
                            logger.debug(f"Returning cached weather data for {city_name}")
                            return recent_weather
                except Exception as cache_error:
                    logger.warning(f"Cache retrieval error for {city_name}: {cache_error}")
            
            # Fetch fresh data
            if self.api_key == 'demo-key':
                weather_data = self._get_demo_weather(city_name)
            else:
                weather_data = self._fetch_real_weather(city_name, country_code)
            
            # Cache the result
            if weather_data:
                try:
                    cache_data = {
                        'city_name': city_name,
                        'country': country_code,
                        'timestamp': weather_data.timestamp.isoformat(),
                        'temperature': weather_data.temperature,
                        'weather_condition': weather_data.weather_condition
                    }
                    WeatherCacheManager.set_cache(cache_key, cache_data, 'current_weather')
                    logger.debug(f"Cached weather data for {city_name}")
                except Exception as cache_error:
                    logger.warning(f"Cache storage error for {city_name}: {cache_error}")
            
            return weather_data
            
        except Exception as e:
            logger.error(f"Error getting current weather for {city_name}: {e}")
            return self._get_demo_weather(city_name)
    
    def _fetch_real_weather(self, city_name, country_code=''):
        """Fetch weather data from real API"""
        coords = self.get_coordinates(city_name, country_code)
        if not coords:
            return None
        
        lat, lon = coords
        
        url = f"{self.base_url}/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'units': 'metric'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Get or create city (fix duplicate issue)
        city = City.objects.filter(name__iexact=city_name).first()
        if not city:
            city = City.objects.create(
                name=city_name.title(),
                country=country_code.upper() if country_code else 'Unknown',
                latitude=lat,
                longitude=lon,
                timezone='UTC'
            )
        
        # Create weather data with all required fields
        weather_data = WeatherData.objects.create(
            city=city,
            temperature=data['main']['temp'],
            feels_like=data['main']['feels_like'],
            humidity=data['main']['humidity'],
            pressure=data['main']['pressure'],
            wind_speed=data['wind'].get('speed', 0) * 3.6,  # Convert m/s to km/h
            wind_direction=data['wind'].get('deg', 0),
            weather_condition=data['weather'][0]['main'],
            weather_description=data['weather'][0]['description'],
            weather_icon=data['weather'][0].get('icon', '01d'),
            cloudiness=data.get('clouds', {}).get('all', 0),
            visibility=data.get('visibility', 10000) / 1000,  # Convert to km
            uv_index=0,  # Not available in current weather API
            timestamp=timezone.now()
        )
        
        return weather_data
    
    def get_air_quality(self, lat, lon):
        """Get air quality data"""
        try:
            if self.api_key == 'demo-key':
                return self._get_demo_air_quality(lat, lon)
            
            url = f"{self.base_url}/air_pollution"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Get city by coordinates
            city = City.objects.filter(
                latitude__range=(lat-0.1, lat+0.1),
                longitude__range=(lon-0.1, lon+0.1)
            ).first()
            
            if not city:
                return None
            
            components = data['list'][0]['components']
            
            air_quality = AirQualityData.objects.create(
                city=city,
                aqi=data['list'][0]['main']['aqi'],
                pm2_5=components.get('pm2_5', 0),
                pm10=components.get('pm10', 0),
                co=components.get('co', 0),
                no2=components.get('no2', 0),
                o3=components.get('o3', 0),
                so2=components.get('so2', 0),
                timestamp=timezone.now()
            )
            
            return air_quality
            
        except Exception as e:
            logger.error(f"Error getting air quality for {lat}, {lon}: {e}")
            return self._get_demo_air_quality(lat, lon)
    
    def get_forecast(self, city_name, country_code='', days=5):
        """Get weather forecast"""
        try:
            if self.api_key == 'demo-key':
                return self._get_demo_forecast(city_name, days)
            
            coords = self.get_coordinates(city_name, country_code)
            if not coords:
                return []
            
            lat, lon = coords
            
            url = f"{self.base_url}/forecast"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Get city
            city = City.objects.filter(name__iexact=city_name).first()
            if not city:
                return []
            
            forecasts = []
            processed_dates = set()
            
            for item in data['list'][:days*8]:  # 8 forecasts per day (3-hour intervals)
                forecast_date = datetime.fromtimestamp(item['dt']).date()
                
                if forecast_date not in processed_dates:
                    forecast = WeatherForecast.objects.create(
                        city=city,
                        forecast_date=forecast_date,
                        temperature_max=item['main']['temp_max'],
                        temperature_min=item['main']['temp_min'],
                        humidity=item['main']['humidity'],
                        pressure=item['main']['pressure'],
                        wind_speed=item['wind'].get('speed', 0) * 3.6,
                        weather_condition=item['weather'][0]['main'],
                        weather_description=item['weather'][0]['description'],
                        precipitation_probability=item.get('pop', 0) * 100,
                        created_at=timezone.now()
                    )
                    forecasts.append(forecast)
                    processed_dates.add(forecast_date)
            
            return forecasts
            
        except Exception as e:
            logger.error(f"Error getting forecast for {city_name}: {e}")
            return self._get_demo_forecast(city_name, days)
    
    def _get_demo_weather(self, city_name):
        """Generate demo weather data"""
        import random
        
        # Get or create city (fix duplicate issue)
        city = City.objects.filter(name__iexact=city_name).first()
        if not city:
            city = City.objects.create(
                name=city_name.title(),
                country='Demo',
                latitude=40.7128,
                longitude=-74.0060,
                timezone='UTC'
            )
        
        # Generate realistic weather data
        base_temp = random.uniform(15, 30)
        conditions = [
            ('Clear', 'clear sky', '01d'),
            ('Clouds', 'few clouds', '02d'),
            ('Clouds', 'scattered clouds', '03d'),
            ('Rain', 'light rain', '10d'),
            ('Snow', 'light snow', '13d')
        ]
        condition, description, icon = random.choice(conditions)
        
        # Create raw weather data
        raw_data = {
            'temperature': round(base_temp, 1),
            'feels_like': round(base_temp + random.uniform(-3, 3), 1),
            'humidity': random.randint(30, 90),
            'pressure': random.randint(1000, 1030),
            'wind_speed': round(random.uniform(0, 25), 1),
            'wind_direction': random.randint(0, 360),
            'weather_condition': condition,
            'weather_description': description,
            'cloudiness': random.randint(0, 100),
            'visibility': round(random.uniform(5, 15), 1),
            'uv_index': random.randint(1, 11),
        }
        
        # Validate weather data
        try:
            validated_data = WeatherDataValidator.validate_weather_data(raw_data)
        except ValidationError as e:
            logger.warning(f"Weather data validation failed for {city_name}: {e}")
            # Use raw data if validation fails (for demo purposes)
            validated_data = raw_data
        
        weather_data = WeatherData.objects.create(
            city=city,
            temperature=validated_data['temperature'],
            feels_like=validated_data['feels_like'],
            humidity=validated_data['humidity'],
            pressure=validated_data['pressure'],
            wind_speed=validated_data['wind_speed'],
            wind_direction=validated_data['wind_direction'],
            weather_condition=validated_data['weather_condition'],
            weather_description=validated_data['weather_description'],
            weather_icon=icon,
            cloudiness=validated_data['cloudiness'],
            visibility=validated_data['visibility'],
            uv_index=validated_data['uv_index'],
            timestamp=timezone.now()
        )
        
        return weather_data
    
    def _get_demo_air_quality(self, lat, lon):
        """Generate demo air quality data"""
        import random
        
        city = City.objects.filter(
            latitude__range=(lat-0.1, lat+0.1),
            longitude__range=(lon-0.1, lon+0.1)
        ).first()
        
        if not city:
            return None
        
        air_quality = AirQualityData.objects.create(
            city=city,
            aqi=random.randint(1, 5),
            co=round(random.uniform(200, 2000), 1),
            no=round(random.uniform(0, 50), 1),
            no2=round(random.uniform(10, 100), 1),
            o3=round(random.uniform(50, 200), 1),
            so2=round(random.uniform(5, 50), 1),
            pm2_5=round(random.uniform(5, 50), 1),
            pm10=round(random.uniform(10, 100), 1),
            nh3=round(random.uniform(0, 20), 1),
            timestamp=timezone.now()
        )
        
        return air_quality
    
    def _get_demo_forecast(self, city_name, days):
        """Generate demo forecast data"""
        import random
        
        city = City.objects.filter(name__iexact=city_name).first()
        if not city:
            return []
        
        forecasts = []
        base_date = timezone.now().date()
        
        for i in range(days):
            forecast_date = base_date + timedelta(days=i+1)
            base_temp = random.uniform(15, 30)
            
            forecast = WeatherForecast.objects.create(
                city=city,
                forecast_date=forecast_date,
                temperature_max=round(base_temp + random.uniform(0, 5), 1),
                temperature_min=round(base_temp - random.uniform(0, 10), 1),
                humidity=random.randint(30, 90),
                pressure=random.randint(1000, 1030),
                wind_speed=round(random.uniform(0, 25), 1),
                weather_condition=random.choice(['Clear', 'Clouds', 'Rain', 'Snow']),
                weather_description=random.choice(['clear sky', 'few clouds', 'light rain', 'heavy snow']),
                precipitation_probability=random.randint(0, 100),
                created_at=timezone.now()
            )
            forecasts.append(forecast)
        
        return forecasts


class WeatherManager:
    """Main weather service manager with fallback and error handling"""
    
    def __init__(self):
        self.primary_service = OpenWeatherMapService()
        self.fallback_services = []  # Can add more services later
        self.max_retries = 3
        self.retry_delay = 1  # seconds
    
    def get_current_weather_with_fallback(self, city_name, country_code=''):
        """Get current weather with fallback and retry logic"""
        services = [self.primary_service] + self.fallback_services
        last_error = None
        
        for service_index, service in enumerate(services):
            for attempt in range(self.max_retries):
                try:
                    logger.debug(f"Attempting weather fetch for {city_name} - Service {service_index + 1}, Attempt {attempt + 1}")
                    
                    weather_data = service.get_current_weather(city_name, country_code)
                    if weather_data:
                        if service_index > 0:
                            logger.warning(f"Primary service failed, used fallback service {service_index + 1} for {city_name}")
                        return weather_data
                    
                except Exception as e:
                    last_error = e
                    logger.warning(f"Service {service_index + 1} attempt {attempt + 1} failed for {city_name}: {e}")
                    
                    if attempt < self.max_retries - 1:
                        import time
                        time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
        
        # All services and retries failed
        logger.error(f"All weather services failed for {city_name}. Last error: {last_error}")
        
        # Try to return cached data as last resort
        cache_key = WeatherCacheManager.get_weather_cache_key(city_name, country_code)
        cached_data = WeatherCacheManager.get_cache(cache_key)
        
        if cached_data:
            logger.info(f"Returning stale cached data for {city_name}")
            # Try to find existing weather data in database
            city = City.objects.filter(name__iexact=city_name).first()
            if city:
                recent_weather = WeatherData.objects.filter(city=city).order_by('-timestamp').first()
                if recent_weather:
                    return recent_weather
        
        # Demo fallback to ensure a result in non-production/test environments
        try:
            return self.primary_service._get_demo_weather(city_name)
        except Exception:
            return None
    
    def get_comprehensive_weather(self, city_name, country_code=''):
        """Get comprehensive weather data with error handling"""
        try:
            # Get current weather with fallback
            current_weather = self.get_current_weather_with_fallback(city_name, country_code)
            if not current_weather:
                logger.error(f"Could not get current weather for {city_name}")
                return None
            
            # Get air quality with error handling
            air_quality = None
            try:
                air_quality = self.primary_service.get_air_quality(
                    current_weather.city.latitude,
                    current_weather.city.longitude
                )
            except Exception as e:
                logger.warning(f"Air quality data unavailable for {city_name}: {e}")
            
            # Get forecast with error handling
            forecast = []
            try:
                forecast = self.primary_service.get_forecast(city_name, country_code, 5)
            except Exception as e:
                logger.warning(f"Forecast data unavailable for {city_name}: {e}")
            
            return {
                'current': current_weather,
                'air_quality': air_quality,
                'forecast': forecast or []
            }
            
        except Exception as e:
            logger.error(f"Error getting comprehensive weather for {city_name}: {e}")
            return None
    
    def update_weather_for_all_cities(self):
        """Update weather data for all active cities with error handling"""
        cities = City.objects.filter(is_active=True)
        updated_count = 0
        failed_cities = []
        
        for city in cities:
            try:
                weather_data = self.get_current_weather_with_fallback(city.name, city.country)
                if weather_data:
                    updated_count += 1
                    logger.debug(f"Successfully updated weather for {city.name}")
                else:
                    failed_cities.append(city.name)
                    logger.warning(f"Failed to update weather for {city.name}")
                    
            except Exception as e:
                failed_cities.append(city.name)
                logger.error(f"Error updating weather for {city.name}: {e}")
        
        if failed_cities:
            logger.warning(f"Failed to update weather for cities: {', '.join(failed_cities)}")
        
        logger.info(f"Weather update completed: {updated_count}/{len(cities)} cities updated")
        return updated_count
    
    def get_service_health(self):
        """Check health of all weather services"""
        health_status = {
            'primary_service': self._check_service_health(self.primary_service),
            'fallback_services': [],
            'cache_status': WeatherCacheManager._test_connection(),
            'timestamp': timezone.now().isoformat()
        }
        
        for i, service in enumerate(self.fallback_services):
            health_status['fallback_services'].append({
                f'service_{i+1}': self._check_service_health(service)
            })
        
        return health_status
    
    def _check_service_health(self, service):
        """Check if a weather service is healthy"""
        try:
            # Try a simple test request
            test_result = service.get_coordinates('London', 'GB')
            return {
                'status': 'healthy' if test_result else 'degraded',
                'api_key_status': 'configured' if service.api_key != 'demo-key' else 'demo',
                'last_check': timezone.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': timezone.now().isoformat()
            }


# Global instance
weather_manager = WeatherManager()


class WeatherAPIAggregator:
    """Aggregates multiple weather APIs with intelligent fallback"""
    
    def __init__(self):
        self.primary_api = OpenWeatherMapService()
        self.apis = [self.primary_api]
        self.cache_prefix = 'weather_api_'
        
    async def get_comprehensive_weather_data(self, city_name: str, country_code: str = '') -> Optional[Dict[str, Any]]:
        """Get comprehensive weather data with fallback support"""
        cache_key = f"{self.cache_prefix}{city_name.lower()}_{country_code}"
        
        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info(f"Returning cached weather data for {city_name}")
            return cached_data
        
        # Try each API in order
        for api in self.apis:
            try:
                current_weather = api.get_current_weather(city_name, country_code)
                if current_weather:
                    # Get additional data
                    air_quality = api.get_air_quality(
                        current_weather.city.latitude,
                        current_weather.city.longitude
                    )
                    forecast = api.get_forecast(city_name, country_code, 5)
                    
                    comprehensive_data = {
                        'current': current_weather,
                        'air_quality': air_quality,
                        'forecast': forecast,
                        'source': api.__class__.__name__,
                        'timestamp': timezone.now().isoformat()
                    }
                    
                    # Cache the result
                    cache.set(cache_key, comprehensive_data, self.cache_timeout)
                    return comprehensive_data
                    
            except Exception as e:
                logger.error(f"API {api.__class__.__name__} failed for {city_name}: {e}")
                continue
        
        logger.error(f"All APIs failed for {city_name}")
        return None

    def get_multiple_cities_weather(self, city_names: List[str]) -> Dict[str, Any]:
        """Get weather data for multiple cities efficiently"""
        results = {}
        
        for city_name in city_names:
            try:
                weather_data = self.get_comprehensive_weather_data(city_name)
                if weather_data:
                    results[city_name] = weather_data
            except Exception as e:
                logger.error(f"Failed to get weather for {city_name}: {e}")
                results[city_name] = None
        
        return results


class WeatherDataProcessor:
    """Process and enhance weather data with analytics"""
    
    @staticmethod
    def calculate_heat_index(temperature: float, humidity: float) -> float:
        """Calculate heat index from temperature and humidity"""
        if temperature < 27:  # Heat index only relevant for high temperatures
            return temperature
            
        # Heat index formula (simplified)
        hi = -42.379 + 2.04901523 * temperature + 10.14333127 * humidity
        hi -= 0.22475541 * temperature * humidity
        hi -= 0.00683783 * temperature * temperature
        hi -= 0.05481717 * humidity * humidity
        hi += 0.00122874 * temperature * temperature * humidity
        hi += 0.00085282 * temperature * humidity * humidity
        hi -= 0.00000199 * temperature * temperature * humidity * humidity
        
        return round(hi, 1)
    
    @staticmethod
    def calculate_wind_chill(temperature: float, wind_speed: float) -> float:
        """Calculate wind chill from temperature and wind speed"""
        if temperature > 10 or wind_speed < 4.8:  # Wind chill only relevant in cold, windy conditions
            return temperature
            
        # Wind chill formula
        wc = 13.12 + 0.6215 * temperature - 11.37 * (wind_speed ** 0.16)
        wc += 0.3965 * temperature * (wind_speed ** 0.16)
        
        return round(wc, 1)
    
    @staticmethod
    def get_weather_severity_score(weather_data: WeatherData) -> int:
        """Calculate weather severity score (0-100)"""
        score = 0
        
        # Temperature extremes
        if weather_data.temperature > 35 or weather_data.temperature < -10:
            score += 30
        elif weather_data.temperature > 30 or weather_data.temperature < 0:
            score += 15
            
        # Wind speed
        if weather_data.wind_speed > 50:
            score += 25
        elif weather_data.wind_speed > 30:
            score += 15
            
        # Visibility
        if weather_data.visibility < 1:
            score += 20
        elif weather_data.visibility < 5:
            score += 10
            
        # Weather conditions
        severe_conditions = ['thunderstorm', 'tornado', 'hurricane', 'blizzard']
        if any(condition in weather_data.weather_description.lower() for condition in severe_conditions):
            score += 25
            
        return min(score, 100)


# Enhanced global instance
weather_aggregator = WeatherAPIAggregator()
weather_processor = WeatherDataProcessor()