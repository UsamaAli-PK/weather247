from rest_framework import serializers
from .models import City, WeatherData, AirQualityData, WeatherForecast, HistoricalWeatherData, WeatherPrediction, UserWeatherPreference
from .api_management import APIProvider, APIUsage, APIFailover


class CitySerializer(serializers.ModelSerializer):
    """Serializer for City model"""
    class Meta:
        model = City
        fields = (
            'id', 'name', 'country', 'latitude', 'longitude', 'timezone',
            'is_active', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'is_active', 'created_at', 'updated_at'
        )


class WeatherDataSerializer(serializers.ModelSerializer):
    """Serializer for WeatherData model"""
    city = CitySerializer(read_only=True)

    class Meta:
        model = WeatherData
        fields = (
            'id', 'city', 'temperature', 'feels_like', 'humidity', 'pressure',
            'visibility', 'uv_index', 'wind_speed', 'wind_direction',
            'weather_condition', 'weather_description', 'weather_icon',
            'cloudiness', 'sunrise', 'sunset', 'data_source', 'timestamp'
        )
        read_only_fields = (
            'city', 'data_source', 'timestamp'
        )


class AirQualityDataSerializer(serializers.ModelSerializer):
    """Serializer for AirQualityData model"""
    city = CitySerializer(read_only=True)

    class Meta:
        model = AirQualityData
        fields = (
            'id', 'city', 'aqi', 'co', 'no', 'no2', 'o3', 'so2', 'pm2_5', 'pm10', 'nh3',
            'data_source', 'timestamp'
        )
        read_only_fields = (
            'city', 'data_source', 'timestamp'
        )


class WeatherForecastSerializer(serializers.ModelSerializer):
    """Serializer for WeatherForecast model"""
    city = CitySerializer(read_only=True)

    class Meta:
        model = WeatherForecast
        fields = (
            'id', 'city', 'forecast_date', 'temperature_min', 'temperature_max',
            'temperature_avg', 'humidity', 'pressure', 'wind_speed', 'wind_direction',
            'weather_condition', 'weather_description', 'weather_icon', 'cloudiness',
            'precipitation_probability', 'precipitation_amount', 'data_source', 'created_at'
        )
        read_only_fields = (
            'city', 'data_source', 'created_at'
        )


class HistoricalWeatherDataSerializer(serializers.ModelSerializer):
    """Serializer for HistoricalWeatherData model"""
    city = CitySerializer(read_only=True)

    class Meta:
        model = HistoricalWeatherData
        fields = (
            'id', 'city', 'date', 'temperature_min', 'temperature_max',
            'temperature_avg', 'humidity_avg', 'pressure_avg', 'wind_speed_avg',
            'precipitation_total', 'weather_condition', 'data_source', 'created_at'
        )
        read_only_fields = (
            'city', 'data_source', 'created_at'
        )


class WeatherPredictionSerializer(serializers.ModelSerializer):
    """Serializer for WeatherPrediction model"""
    city = CitySerializer(read_only=True)

    class Meta:
        model = WeatherPrediction
        fields = (
            'id', 'city', 'prediction_date', 'predicted_temperature',
            'predicted_humidity', 'predicted_pressure', 'predicted_wind_speed',
            'predicted_condition', 'confidence_score', 'model_version', 'features_used', 'created_at'
        )
        read_only_fields = (
            'city', 'model_version', 'created_at'
        )


class UserWeatherPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for UserWeatherPreference model"""
    city = CitySerializer(read_only=True)

    class Meta:
        model = UserWeatherPreference
        fields = (
            'id', 'user', 'city', 'is_favorite', 'alert_enabled', 'order', 'created_at'
        )
        read_only_fields = (
            'user', 'created_at'
        )



class APIProviderSerializer(serializers.ModelSerializer):
    """Serializer for APIProvider model"""
    
    class Meta:
        model = APIProvider
        fields = (
            'id', 'name', 'display_name', 'base_url', 'api_key',
            'is_active', 'is_primary', 'priority', 'requests_per_minute',
            'requests_per_day', 'requests_per_month', 'cost_per_request',
            'monthly_budget', 'last_health_check', 'is_healthy', 'error_count',
            'success_rate', 'supported_endpoints', 'configuration',
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'last_health_check', 'is_healthy', 'error_count', 'success_rate',
            'created_at', 'updated_at'
        )
        extra_kwargs = {
            'api_key': {'write_only': True}
        }


class APIUsageSerializer(serializers.ModelSerializer):
    """Serializer for APIUsage model"""
    provider = APIProviderSerializer(read_only=True)
    
    class Meta:
        model = APIUsage
        fields = (
            'id', 'provider', 'date', 'endpoint', 'request_count',
            'success_count', 'error_count', 'avg_response_time',
            'max_response_time', 'cost', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'provider', 'created_at', 'updated_at'
        )


class APIFailoverSerializer(serializers.ModelSerializer):
    """Serializer for APIFailover model"""
    primary_provider = APIProviderSerializer(read_only=True)
    fallback_provider = APIProviderSerializer(read_only=True)
    
    class Meta:
        model = APIFailover
        fields = (
            'id', 'primary_provider', 'fallback_provider', 'reason',
            'endpoint', 'error_details', 'failed_at', 'resolved_at'
        )
        read_only_fields = (
            'primary_provider', 'fallback_provider', 'failed_at'
        )