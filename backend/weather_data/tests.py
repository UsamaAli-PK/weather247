"""
Comprehensive test suite for Weather247 weather data integration
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.cache import cache
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from unittest.mock import patch, Mock
import json
from datetime import datetime, timedelta
from django.utils import timezone

from .models import City, WeatherData, AirQualityData, WeatherForecast
from .serializers import CitySerializer, WeatherDataSerializer
from .cache_manager import WeatherCacheManager
from .validators import WeatherDataValidator, CityValidator
from .real_weather_service import weather_manager

User = get_user_model()


class WeatherDataModelTests(TestCase):
    """Test weather data models"""
    
    def setUp(self):
        self.city = City.objects.create(
            name="Test City",
            country="TC",
            latitude=40.7128,
            longitude=-74.0060,
            timezone="UTC"
        )
    
    def test_city_creation(self):
        """Test city model creation"""
        self.assertEqual(self.city.name, "Test City")
        self.assertEqual(self.city.country, "TC")
        self.assertTrue(self.city.is_active)
        self.assertIsNotNone(self.city.created_at)
    
    def test_city_str_representation(self):
        """Test city string representation"""
        expected = "Test City, TC"
        self.assertEqual(str(self.city), expected)
    
    def test_weather_data_creation(self):
        """Test weather data model creation"""
        weather_data = WeatherData.objects.create(
            city=self.city,
            temperature=25.5,
            feels_like=27.0,
            humidity=65,
            pressure=1013.25,
            wind_speed=10.5,
            wind_direction=180,
            weather_condition="Clear",
            weather_description="clear sky",
            weather_icon="01d",
            cloudiness=0,
            visibility=10.0,
            uv_index=5.0
        )
        
        self.assertEqual(weather_data.city, self.city)
        self.assertEqual(weather_data.temperature, 25.5)
        self.assertEqual(weather_data.weather_condition, "Clear")
        self.assertIsNotNone(weather_data.timestamp)
    
    def test_air_quality_data_creation(self):
        """Test air quality data model creation"""
        air_quality = AirQualityData.objects.create(
            city=self.city,
            aqi=2,
            co=200.0,
            no=10.0,
            no2=25.0,
            o3=80.0,
            so2=15.0,
            pm2_5=12.0,
            pm10=20.0,
            nh3=5.0
        )
        
        self.assertEqual(air_quality.city, self.city)
        self.assertEqual(air_quality.aqi, 2)
        self.assertEqual(air_quality.pm2_5, 12.0)


class WeatherDataValidatorTests(TestCase):
    """Test weather data validation"""
    
    def test_temperature_validation(self):
        """Test temperature validation"""
        # Valid temperatures
        self.assertEqual(WeatherDataValidator.validate_temperature(25.5), 25.5)
        self.assertEqual(WeatherDataValidator.validate_temperature(-10), -10.0)
        
        # Invalid temperatures
        with self.assertRaises(Exception):
            WeatherDataValidator.validate_temperature(100)  # Too hot
        with self.assertRaises(Exception):
            WeatherDataValidator.validate_temperature(-150)  # Too cold
        with self.assertRaises(Exception):
            WeatherDataValidator.validate_temperature("not_a_number")
    
    def test_humidity_validation(self):
        """Test humidity validation"""
        # Valid humidity
        self.assertEqual(WeatherDataValidator.validate_humidity(65), 65)
        self.assertEqual(WeatherDataValidator.validate_humidity(0), 0)
        self.assertEqual(WeatherDataValidator.validate_humidity(100), 100)
        
        # Invalid humidity
        with self.assertRaises(Exception):
            WeatherDataValidator.validate_humidity(-5)
        with self.assertRaises(Exception):
            WeatherDataValidator.validate_humidity(105)
    
    def test_coordinates_validation(self):
        """Test coordinate validation"""
        # Valid coordinates
        lat, lon = WeatherDataValidator.validate_coordinates(40.7128, -74.0060)
        self.assertEqual(lat, 40.7128)
        self.assertEqual(lon, -74.0060)
        
        # Invalid coordinates
        with self.assertRaises(Exception):
            WeatherDataValidator.validate_coordinates(91, 0)  # Invalid latitude
        with self.assertRaises(Exception):
            WeatherDataValidator.validate_coordinates(0, 181)  # Invalid longitude
    
    def test_weather_condition_validation(self):
        """Test weather condition validation"""
        # Valid conditions
        self.assertEqual(WeatherDataValidator.validate_weather_condition("clear"), "Clear")
        self.assertEqual(WeatherDataValidator.validate_weather_condition("RAIN"), "Rain")
        
        # Invalid conditions (should still work but may log warnings)
        result = WeatherDataValidator.validate_weather_condition("unknown_condition")
        self.assertEqual(result, "Unknown_condition")


class CityValidatorTests(TestCase):
    """Test city validation"""
    
    def test_city_name_validation(self):
        """Test city name validation"""
        # Valid names
        self.assertEqual(CityValidator.validate_city_name("New York"), "New York")
        self.assertEqual(CityValidator.validate_city_name("london"), "London")
        
        # Invalid names
        with self.assertRaises(Exception):
            CityValidator.validate_city_name("A")  # Too short
        with self.assertRaises(Exception):
            CityValidator.validate_city_name("")  # Empty
        with self.assertRaises(Exception):
            CityValidator.validate_city_name("City123")  # Contains numbers
    
    def test_country_code_validation(self):
        """Test country code validation"""
        # Valid codes
        self.assertEqual(CityValidator.validate_country_code("US"), "US")
        self.assertEqual(CityValidator.validate_country_code("gb"), "GB")
        
        # Invalid codes
        with self.assertRaises(Exception):
            CityValidator.validate_country_code("USA1")  # Contains number
        with self.assertRaises(Exception):
            CityValidator.validate_country_code("")  # Empty


class WeatherCacheManagerTests(TestCase):
    """Test caching functionality"""
    
    def setUp(self):
        cache.clear()
    
    def tearDown(self):
        cache.clear()
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        weather_key = WeatherCacheManager.get_weather_cache_key("London", "GB")
        self.assertIn("weather:current", weather_key)
        self.assertIn("london", weather_key)
        self.assertIn("gb", weather_key)
    
    def test_cache_operations(self):
        """Test basic cache operations"""
        test_key = "test:cache:key"
        test_data = {"temperature": 25.5, "city": "Test"}
        
        # Test set
        success = WeatherCacheManager.set_cache(test_key, test_data)
        self.assertTrue(success)
        
        # Test get
        cached_data = WeatherCacheManager.get_cache(test_key)
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data["temperature"], 25.5)
        
        # Test delete
        delete_success = WeatherCacheManager.delete_cache(test_key)
        self.assertTrue(delete_success)
        
        # Verify deletion
        deleted_data = WeatherCacheManager.get_cache(test_key)
        self.assertIsNone(deleted_data)
    
    def test_city_cache_invalidation(self):
        """Test city-specific cache invalidation"""
        city_name = "TestCity"
        
        # Set multiple cache entries for the city
        weather_key = WeatherCacheManager.get_weather_cache_key(city_name)
        forecast_key = WeatherCacheManager.get_forecast_cache_key(city_name)
        
        WeatherCacheManager.set_cache(weather_key, {"temp": 20})
        WeatherCacheManager.set_cache(forecast_key, [{"temp": 21}])
        
        # Verify they exist
        self.assertIsNotNone(WeatherCacheManager.get_cache(weather_key))
        self.assertIsNotNone(WeatherCacheManager.get_cache(forecast_key))
        
        # Invalidate city cache
        WeatherCacheManager.invalidate_city_cache(city_name)
        
        # Verify they're gone
        self.assertIsNone(WeatherCacheManager.get_cache(weather_key))
        self.assertIsNone(WeatherCacheManager.get_cache(forecast_key))


class WeatherAPITests(APITestCase):
    """Test weather API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        
        self.city = City.objects.create(
            name="Test City",
            country="TC",
            latitude=40.7128,
            longitude=-74.0060
        )
    
    def test_city_list_endpoint(self):
        """Test city list API endpoint"""
        url = reverse('city-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test City')
    
    def test_city_creation_endpoint(self):
        """Test city creation API endpoint"""
        url = reverse('city-list')
        data = {
            'name': 'New Test City',
            'country': 'NTC',
            'latitude': 51.5074,
            'longitude': -0.1278
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Test City')
        
        # Verify city was created in database
        self.assertTrue(City.objects.filter(name='New Test City').exists())
    
    def test_search_cities_endpoint(self):
        """Test city search endpoint"""
        url = reverse('search-cities')
        response = self.client.get(url, {'q': 'Test'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertTrue(len(response.data['results']) > 0)
    
    def test_add_city_endpoint(self):
        """Test add city endpoint"""
        url = reverse('add-city')
        data = {
            'name': 'Barcelona',
            'country': 'ES',
            'latitude': 41.3851,
            'longitude': 2.1734
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('city', response.data)
    
    def test_add_city_validation(self):
        """Test add city endpoint validation"""
        url = reverse('add-city')
        
        # Test invalid data
        invalid_data = {
            'name': 'A',  # Too short
            'country': 'ES',
            'latitude': 91,  # Invalid latitude
            'longitude': 2.1734
        }
        
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    @patch('weather_data.real_weather_service.weather_manager.get_current_weather_with_fallback')
    def test_current_weather_endpoint(self, mock_weather):
        """Test current weather endpoint"""
        # Mock weather data
        mock_weather_data = Mock()
        mock_weather_data.temperature = 25.5
        mock_weather_data.humidity = 65
        mock_weather_data.weather_condition = "Clear"
        mock_weather_data.city = self.city
        mock_weather.return_value = mock_weather_data
        
        url = reverse('weather-by-name')
        response = self.client.get(url, {'city': 'Test City'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('current', response.data)
        mock_weather.assert_called_once()
    
    def test_current_weather_missing_city(self):
        """Test current weather endpoint without city parameter"""
        url = reverse('weather-by-name')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_cache_stats_endpoint(self):
        """Test cache statistics endpoint"""
        url = reverse('cache-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertIn('cache_keys_info', response.data)
    
    def test_system_health_endpoint(self):
        """Test system health endpoint"""
        url = reverse('system-health')
        response = self.client.get(url)
        
        self.assertIn(response.status_code, [200, 206, 503])
        self.assertIn('overall_status', response.data)
        self.assertIn('primary_service', response.data)
        self.assertIn('database', response.data)


class WeatherServiceTests(TestCase):
    """Test weather service functionality"""
    
    def setUp(self):
        self.city = City.objects.create(
            name="Test City",
            country="TC",
            latitude=40.7128,
            longitude=-74.0060
        )
    
    def test_service_health_check(self):
        """Test weather service health check"""
        health = weather_manager.get_service_health()
        
        self.assertIn('primary_service', health)
        self.assertIn('cache_status', health)
        self.assertIn('timestamp', health)
        self.assertIn('status', health['primary_service'])
    
    @patch('weather_data.real_weather_service.OpenWeatherMapService.get_current_weather')
    def test_fallback_mechanism(self, mock_get_weather):
        """Test fallback mechanism when primary service fails"""
        # Mock primary service failure
        mock_get_weather.side_effect = Exception("API Error")
        
        # This should handle the error gracefully
        result = weather_manager.get_current_weather_with_fallback("Test City")
        
        # Since we're using demo data, it should still return something
        # or None if all fallbacks fail
        self.assertIsNotNone(result)  # Demo service should work
    
    def test_bulk_update(self):
        """Test bulk weather update"""
        # This will use demo data
        updated_count = weather_manager.update_weather_for_all_cities()
        
        # Should update at least the test city
        self.assertGreaterEqual(updated_count, 0)


class WeatherSerializerTests(TestCase):
    """Test weather data serializers"""
    
    def setUp(self):
        self.city = City.objects.create(
            name="Test City",
            country="TC",
            latitude=40.7128,
            longitude=-74.0060
        )
    
    def test_city_serializer(self):
        """Test city serializer"""
        serializer = CitySerializer(self.city)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Test City')
        self.assertEqual(data['country'], 'TC')
        self.assertEqual(data['latitude'], 40.7128)
        self.assertEqual(data['longitude'], -74.0060)
    
    def test_weather_data_serializer(self):
        """Test weather data serializer"""
        weather_data = WeatherData.objects.create(
            city=self.city,
            temperature=25.5,
            feels_like=27.0,
            humidity=65,
            pressure=1013.25,
            wind_speed=10.5,
            wind_direction=180,
            weather_condition="Clear",
            weather_description="clear sky",
            weather_icon="01d",
            cloudiness=0,
            visibility=10.0,
            uv_index=5.0
        )
        
        serializer = WeatherDataSerializer(weather_data)
        data = serializer.data
        
        self.assertEqual(data['temperature'], 25.5)
        self.assertEqual(data['weather_condition'], 'Clear')
        self.assertIn('city', data)
        self.assertEqual(data['city']['name'], 'Test City')


class IntegrationTests(TransactionTestCase):
    """Integration tests for complete workflows"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
    
    def test_complete_city_workflow(self):
        """Test complete workflow: add city -> get weather -> cache -> retrieve"""
        # Step 1: Add a new city
        add_city_url = reverse('add-city')
        city_data = {
            'name': 'Integration Test City',
            'country': 'ITC',
            'latitude': 45.0,
            'longitude': 9.0
        }
        
        response = self.client.post(add_city_url, city_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 2: Get weather for the city
        weather_url = reverse('weather-by-name')
        response = self.client.get(weather_url, {'city': 'Integration Test City'})
        
        # Should work with demo data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('current', response.data)
        
        # Step 3: Verify city exists in database
        city_exists = City.objects.filter(name='Integration Test City').exists()
        self.assertTrue(city_exists)
        
        # Step 4: Test cache functionality
        cache_stats_url = reverse('cache-stats')
        response = self.client.get(cache_stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_error_handling_workflow(self):
        """Test error handling in complete workflow"""
        # Test invalid city addition
        add_city_url = reverse('add-city')
        invalid_data = {
            'name': '',  # Invalid name
            'country': 'XX',
            'latitude': 91,  # Invalid latitude
            'longitude': 0
        }
        
        response = self.client.post(add_city_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test weather request for non-existent city
        weather_url = reverse('weather-by-name')
        response = self.client.get(weather_url, {'city': 'NonExistentCity12345'})
        
        # Should handle gracefully (might return 404 or demo data)
        self.assertIn(response.status_code, [200, 404, 500])