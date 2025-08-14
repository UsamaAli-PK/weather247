"""
Weather data validation utilities
"""
import re
from typing import Dict, Any, Optional, List
from django.core.exceptions import ValidationError


class WeatherDataValidator:
    """Validator for weather data"""
    
    # Valid ranges for weather parameters
    TEMPERATURE_RANGE = (-100, 60)  # Celsius
    HUMIDITY_RANGE = (0, 100)  # Percentage
    PRESSURE_RANGE = (800, 1200)  # hPa
    WIND_SPEED_RANGE = (0, 500)  # km/h
    WIND_DIRECTION_RANGE = (0, 360)  # degrees
    VISIBILITY_RANGE = (0, 50)  # km
    UV_INDEX_RANGE = (0, 15)  # UV index
    CLOUDINESS_RANGE = (0, 100)  # percentage
    AQI_RANGE = (1, 5)  # Air Quality Index
    
    # Valid weather conditions
    VALID_CONDITIONS = {
        'clear', 'clouds', 'rain', 'drizzle', 'thunderstorm', 
        'snow', 'mist', 'fog', 'haze', 'dust', 'sand', 'ash', 'squall', 'tornado'
    }
    
    @classmethod
    def validate_temperature(cls, temperature: float) -> float:
        """Validate temperature value"""
        if not isinstance(temperature, (int, float)):
            raise ValidationError("Temperature must be a number")
        
        temp = float(temperature)
        if not (cls.TEMPERATURE_RANGE[0] <= temp <= cls.TEMPERATURE_RANGE[1]):
            raise ValidationError(
                f"Temperature must be between {cls.TEMPERATURE_RANGE[0]}°C and {cls.TEMPERATURE_RANGE[1]}°C"
            )
        
        return round(temp, 1)
    
    @classmethod
    def validate_humidity(cls, humidity: int) -> int:
        """Validate humidity value"""
        if not isinstance(humidity, (int, float)):
            raise ValidationError("Humidity must be a number")
        
        hum = int(humidity)
        if not (cls.HUMIDITY_RANGE[0] <= hum <= cls.HUMIDITY_RANGE[1]):
            raise ValidationError(
                f"Humidity must be between {cls.HUMIDITY_RANGE[0]}% and {cls.HUMIDITY_RANGE[1]}%"
            )
        
        return hum
    
    @classmethod
    def validate_pressure(cls, pressure: float) -> float:
        """Validate atmospheric pressure"""
        if not isinstance(pressure, (int, float)):
            raise ValidationError("Pressure must be a number")
        
        pres = float(pressure)
        if not (cls.PRESSURE_RANGE[0] <= pres <= cls.PRESSURE_RANGE[1]):
            raise ValidationError(
                f"Pressure must be between {cls.PRESSURE_RANGE[0]} and {cls.PRESSURE_RANGE[1]} hPa"
            )
        
        return round(pres, 1)
    
    @classmethod
    def validate_wind_speed(cls, wind_speed: float) -> float:
        """Validate wind speed"""
        if not isinstance(wind_speed, (int, float)):
            raise ValidationError("Wind speed must be a number")
        
        speed = float(wind_speed)
        if not (cls.WIND_SPEED_RANGE[0] <= speed <= cls.WIND_SPEED_RANGE[1]):
            raise ValidationError(
                f"Wind speed must be between {cls.WIND_SPEED_RANGE[0]} and {cls.WIND_SPEED_RANGE[1]} km/h"
            )
        
        return round(speed, 1)
    
    @classmethod
    def validate_wind_direction(cls, wind_direction: int) -> int:
        """Validate wind direction"""
        if not isinstance(wind_direction, (int, float)):
            raise ValidationError("Wind direction must be a number")
        
        direction = int(wind_direction)
        if not (cls.WIND_DIRECTION_RANGE[0] <= direction <= cls.WIND_DIRECTION_RANGE[1]):
            raise ValidationError(
                f"Wind direction must be between {cls.WIND_DIRECTION_RANGE[0]} and {cls.WIND_DIRECTION_RANGE[1]} degrees"
            )
        
        return direction
    
    @classmethod
    def validate_visibility(cls, visibility: Optional[float]) -> Optional[float]:
        """Validate visibility"""
        if visibility is None:
            return None
        
        if not isinstance(visibility, (int, float)):
            raise ValidationError("Visibility must be a number")
        
        vis = float(visibility)
        if not (cls.VISIBILITY_RANGE[0] <= vis <= cls.VISIBILITY_RANGE[1]):
            raise ValidationError(
                f"Visibility must be between {cls.VISIBILITY_RANGE[0]} and {cls.VISIBILITY_RANGE[1]} km"
            )
        
        return round(vis, 1)
    
    @classmethod
    def validate_uv_index(cls, uv_index: Optional[float]) -> Optional[float]:
        """Validate UV index"""
        if uv_index is None:
            return None
        
        if not isinstance(uv_index, (int, float)):
            raise ValidationError("UV index must be a number")
        
        uv = float(uv_index)
        if not (cls.UV_INDEX_RANGE[0] <= uv <= cls.UV_INDEX_RANGE[1]):
            raise ValidationError(
                f"UV index must be between {cls.UV_INDEX_RANGE[0]} and {cls.UV_INDEX_RANGE[1]}"
            )
        
        return round(uv, 1)
    
    @classmethod
    def validate_cloudiness(cls, cloudiness: int) -> int:
        """Validate cloudiness percentage"""
        if not isinstance(cloudiness, (int, float)):
            raise ValidationError("Cloudiness must be a number")
        
        cloud = int(cloudiness)
        if not (cls.CLOUDINESS_RANGE[0] <= cloud <= cls.CLOUDINESS_RANGE[1]):
            raise ValidationError(
                f"Cloudiness must be between {cls.CLOUDINESS_RANGE[0]}% and {cls.CLOUDINESS_RANGE[1]}%"
            )
        
        return cloud
    
    @classmethod
    def validate_weather_condition(cls, condition: str) -> str:
        """Validate weather condition"""
        if not isinstance(condition, str):
            raise ValidationError("Weather condition must be a string")
        
        condition = condition.strip().lower()
        if not condition:
            raise ValidationError("Weather condition cannot be empty")
        
        if condition not in cls.VALID_CONDITIONS:
            # Allow it but log a warning
            pass
        
        return condition.title()
    
    @classmethod
    def validate_weather_description(cls, description: str) -> str:
        """Validate weather description"""
        if not isinstance(description, str):
            raise ValidationError("Weather description must be a string")
        
        description = description.strip()
        if not description:
            raise ValidationError("Weather description cannot be empty")
        
        if len(description) > 200:
            raise ValidationError("Weather description too long (max 200 characters)")
        
        # Basic sanitization
        description = re.sub(r'[<>"\']', '', description)
        
        return description.lower()
    
    @classmethod
    def validate_aqi(cls, aqi: int) -> int:
        """Validate Air Quality Index"""
        if not isinstance(aqi, (int, float)):
            raise ValidationError("AQI must be a number")
        
        aqi_val = int(aqi)
        if not (cls.AQI_RANGE[0] <= aqi_val <= cls.AQI_RANGE[1]):
            raise ValidationError(
                f"AQI must be between {cls.AQI_RANGE[0]} and {cls.AQI_RANGE[1]}"
            )
        
        return aqi_val
    
    @classmethod
    def validate_coordinates(cls, latitude: float, longitude: float) -> tuple:
        """Validate geographic coordinates"""
        if not isinstance(latitude, (int, float)):
            raise ValidationError("Latitude must be a number")
        
        if not isinstance(longitude, (int, float)):
            raise ValidationError("Longitude must be a number")
        
        lat = float(latitude)
        lon = float(longitude)
        
        if not (-90 <= lat <= 90):
            raise ValidationError("Latitude must be between -90 and 90 degrees")
        
        if not (-180 <= lon <= 180):
            raise ValidationError("Longitude must be between -180 and 180 degrees")
        
        return round(lat, 6), round(lon, 6)
    
    @classmethod
    def validate_weather_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate complete weather data object"""
        validated_data = {}
        
        # Required fields
        required_fields = ['temperature', 'humidity', 'pressure', 'wind_speed', 'weather_condition']
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")
        
        # Validate each field
        validated_data['temperature'] = cls.validate_temperature(data['temperature'])
        validated_data['feels_like'] = cls.validate_temperature(data.get('feels_like', data['temperature']))
        validated_data['humidity'] = cls.validate_humidity(data['humidity'])
        validated_data['pressure'] = cls.validate_pressure(data['pressure'])
        validated_data['wind_speed'] = cls.validate_wind_speed(data['wind_speed'])
        validated_data['wind_direction'] = cls.validate_wind_direction(data.get('wind_direction', 0))
        validated_data['weather_condition'] = cls.validate_weather_condition(data['weather_condition'])
        validated_data['weather_description'] = cls.validate_weather_description(
            data.get('weather_description', data['weather_condition'])
        )
        validated_data['cloudiness'] = cls.validate_cloudiness(data.get('cloudiness', 0))
        validated_data['visibility'] = cls.validate_visibility(data.get('visibility'))
        validated_data['uv_index'] = cls.validate_uv_index(data.get('uv_index'))
        
        return validated_data


class CityValidator:
    """Validator for city data"""
    
    @classmethod
    def validate_city_name(cls, name: str) -> str:
        """Validate city name"""
        if not isinstance(name, str):
            raise ValidationError("City name must be a string")
        
        name = name.strip()
        if not name:
            raise ValidationError("City name cannot be empty")
        
        if len(name) < 2:
            raise ValidationError("City name must be at least 2 characters")
        
        if len(name) > 100:
            raise ValidationError("City name too long (max 100 characters)")
        
        # Basic sanitization - remove special characters but allow spaces, hyphens, apostrophes
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", name):
            raise ValidationError("City name contains invalid characters")
        
        return name.title()
    
    @classmethod
    def validate_country_code(cls, country: str) -> str:
        """Validate country code"""
        if not isinstance(country, str):
            raise ValidationError("Country code must be a string")
        
        country = country.strip().upper()
        if not country:
            raise ValidationError("Country code cannot be empty")
        
        if len(country) < 2 or len(country) > 3:
            raise ValidationError("Country code must be 2-3 characters")
        
        if not re.match(r"^[A-Z]+$", country):
            raise ValidationError("Country code must contain only letters")
        
        return country
    
    @classmethod
    def validate_city_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate complete city data"""
        validated_data = {}
        
        # Required fields
        if 'name' not in data:
            raise ValidationError("City name is required")
        
        validated_data['name'] = cls.validate_city_name(data['name'])
        validated_data['country'] = cls.validate_country_code(data.get('country', 'Unknown'))
        
        # Validate coordinates if provided
        if 'latitude' in data and 'longitude' in data:
            lat, lon = WeatherDataValidator.validate_coordinates(data['latitude'], data['longitude'])
            validated_data['latitude'] = lat
            validated_data['longitude'] = lon
        
        return validated_data