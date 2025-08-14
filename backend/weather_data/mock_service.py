"""
Mock Weather Service for demo purposes when API keys are not available
"""
import random
from datetime import datetime, timedelta
from django.utils import timezone
from .models import City, WeatherData, AirQualityData, WeatherForecast
import logging

logger = logging.getLogger('weather247')


class MockWeatherService:
    """Mock weather service that generates realistic weather data"""
    
    def __init__(self):
        self.weather_conditions = [
            ('Clear', 'clear sky', '01d'),
            ('Clouds', 'few clouds', '02d'),
            ('Clouds', 'scattered clouds', '03d'),
            ('Clouds', 'broken clouds', '04d'),
            ('Rain', 'light rain', '10d'),
            ('Rain', 'moderate rain', '10d'),
            ('Snow', 'light snow', '13d'),
            ('Thunderstorm', 'thunderstorm', '11d'),
        ]
        
        self.city_base_temps = {
            'New York': 15,
            'London': 12,
            'Tokyo': 18,
            'Sydney': 20,
            'Paris': 14,
            'Berlin': 10,
            'Moscow': 5,
            'Mumbai': 28,
            'Cairo': 25,
            'Los Angeles': 22,
        }
    
    def get_current_weather(self, city_name, country_code=None):
        """Generate mock current weather data"""
        try:
            # Get or create city
            city, created = City.objects.get_or_create(
                name=city_name,
                country=country_code or 'Unknown',
                defaults={
                    'latitude': random.uniform(-90, 90),
                    'longitude': random.uniform(-180, 180),
                }
            )
            
            # Generate realistic weather data
            base_temp = self.city_base_temps.get(city_name, random.uniform(10, 25))
            temp_variation = random.uniform(-5, 5)
            temperature = base_temp + temp_variation
            
            condition, description, icon = random.choice(self.weather_conditions)
            
            # Create weather data
            weather_data = WeatherData.objects.create(
                city=city,
                temperature=round(temperature, 1),
                feels_like=round(temperature + random.uniform(-2, 2), 1),
                humidity=random.randint(30, 90),
                pressure=round(random.uniform(990, 1030), 2),
                visibility=round(random.uniform(5, 15), 1),
                wind_speed=round(random.uniform(0, 25), 1),
                wind_direction=random.randint(0, 360),
                weather_condition=condition,
                weather_description=description,
                weather_icon=icon,
                cloudiness=random.randint(0, 100),
                sunrise=timezone.now().replace(hour=6, minute=30),
                sunset=timezone.now().replace(hour=18, minute=45),
                data_source='mock_service'
            )
            
            logger.info(f"Generated mock weather data for {city.name}")
            return weather_data
            
        except Exception as e:
            logger.error(f"Error generating mock weather data: {e}")
            return None
    
    def get_forecast(self, city_name, country_code=None, days=5):
        """Generate mock forecast data"""
        try:
            city, created = City.objects.get_or_create(
                name=city_name,
                country=country_code or 'Unknown',
                defaults={
                    'latitude': random.uniform(-90, 90),
                    'longitude': random.uniform(-180, 180),
                }
            )
            
            forecasts = []
            base_temp = self.city_base_temps.get(city_name, random.uniform(10, 25))
            
            for day in range(days):
                for hour in range(0, 24, 3):  # Every 3 hours
                    forecast_date = timezone.now() + timedelta(days=day, hours=hour)
                    
                    # Add some variation to temperature
                    temp_variation = random.uniform(-3, 3)
                    temperature = base_temp + temp_variation
                    
                    condition, description, icon = random.choice(self.weather_conditions)
                    
                    forecast = WeatherForecast.objects.create(
                        city=city,
                        forecast_date=forecast_date,
                        temperature_min=round(temperature - 2, 1),
                        temperature_max=round(temperature + 2, 1),
                        temperature_avg=round(temperature, 1),
                        humidity=random.randint(30, 90),
                        pressure=round(random.uniform(990, 1030), 2),
                        wind_speed=round(random.uniform(0, 25), 1),
                        wind_direction=random.randint(0, 360),
                        weather_condition=condition,
                        weather_description=description,
                        weather_icon=icon,
                        cloudiness=random.randint(0, 100),
                        precipitation_probability=random.uniform(0, 1),
                        precipitation_amount=random.uniform(0, 5) if condition == 'Rain' else 0,
                        data_source='mock_service'
                    )
                    forecasts.append(forecast)
            
            logger.info(f"Generated mock forecast for {city.name}")
            return forecasts
            
        except Exception as e:
            logger.error(f"Error generating mock forecast: {e}")
            return []
    
    def get_air_quality(self, lat, lon):
        """Generate mock air quality data"""
        try:
            # Find city by coordinates (approximate)
            city = City.objects.filter(
                latitude__range=(lat - 1, lat + 1),
                longitude__range=(lon - 1, lon + 1)
            ).first()
            
            if not city:
                return None
            
            air_quality = AirQualityData.objects.create(
                city=city,
                aqi=random.randint(1, 5),  # 1-5 scale
                co=round(random.uniform(200, 400), 2),
                no=round(random.uniform(0, 50), 2),
                no2=round(random.uniform(10, 80), 2),
                o3=round(random.uniform(50, 150), 2),
                so2=round(random.uniform(0, 20), 2),
                pm2_5=round(random.uniform(5, 50), 2),
                pm10=round(random.uniform(10, 100), 2),
                nh3=round(random.uniform(0, 10), 2),
                data_source='mock_service'
            )
            
            logger.info(f"Generated mock air quality data for {city.name}")
            return air_quality
            
        except Exception as e:
            logger.error(f"Error generating mock air quality data: {e}")
            return None


class MockWeatherDataManager:
    """Manager for mock weather data"""
    
    def __init__(self):
        self.mock_service = MockWeatherService()
    
    def get_comprehensive_weather(self, city_name, country_code=None):
        """Get comprehensive mock weather data"""
        # Get primary data
        weather_data = self.mock_service.get_current_weather(city_name, country_code)
        
        if weather_data:
            # Get air quality data
            air_quality = self.mock_service.get_air_quality(
                weather_data.city.latitude,
                weather_data.city.longitude
            )
            
            # Get forecast data
            forecast = self.mock_service.get_forecast(city_name, country_code)
            
            result = {
                'current': weather_data,
                'air_quality': air_quality,
                'forecast': forecast
            }
            
            return result
        
        return None
    
    def update_weather_for_all_cities(self):
        """Update weather data for all active cities"""
        cities = City.objects.filter(is_active=True)
        updated_count = 0
        
        for city in cities:
            try:
                weather_data = self.mock_service.get_current_weather(city.name, city.country)
                if weather_data:
                    updated_count += 1
                    logger.info(f"Updated mock weather for {city.name}")
            except Exception as e:
                logger.error(f"Failed to update mock weather for {city.name}: {e}")
        
        logger.info(f"Updated mock weather data for {updated_count} cities")
        return updated_count


# Global mock instance
mock_weather_manager = MockWeatherDataManager()

