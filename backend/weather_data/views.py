from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from .models import City, WeatherData, AirQualityData, WeatherForecast
from .serializers import (
    CitySerializer, WeatherDataSerializer, AirQualityDataSerializer,
    WeatherForecastSerializer
)
from .validators import WeatherDataValidator, CityValidator
from .cache_manager import WeatherCacheManager, invalidate_city_cache
from .real_weather_service import weather_manager, weather_aggregator, weather_processor
from .ai_predictions import ai_predictor, advanced_predictor
# from .alert_system import alert_engine, process_weather_alerts  # Temporarily disabled
from .push_views import (
    PushSubscriptionView, verify_subscription, update_preferences,
    send_test_notification, subscription_status, send_weather_alert,
    send_daily_forecast, subscription_stats, cleanup_subscriptions
)
import logging

logger = logging.getLogger('weather247')


class CityListCreateView(generics.ListCreateAPIView):
    """List all cities or create a new city"""
    queryset = City.objects.filter(is_active=True)
    serializer_class = CitySerializer
    permission_classes = [AllowAny]


class CityDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a city"""
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [AllowAny]


@api_view(['GET'])
@permission_classes([AllowAny])
def get_current_weather(request, city_id):
    """Get current weather for a specific city"""
    try:
        city = get_object_or_404(City, id=city_id)
        
        # Try to get recent weather data (within last 30 minutes)
        recent_weather = WeatherData.objects.filter(
            city=city,
            timestamp__gte=timezone.now() - timedelta(minutes=30)
        ).first()
        
        if recent_weather:
            serializer = WeatherDataSerializer(recent_weather)
            return Response(serializer.data)
        
        # Fetch new data from API
        weather_data = weather_manager.openweather.get_current_weather(
            city.name, city.country
        )
        
        if weather_data:
            serializer = WeatherDataSerializer(weather_data)
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'Unable to fetch weather data'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
            
    except Exception as e:
        logger.error(f"Error getting current weather: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_weather_by_city_name(request):
    """Get current weather by city name"""
    city_name = request.GET.get('city')
    country = request.GET.get('country', '')
    
    if not city_name:
        return Response(
            {'error': 'City name is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Get current weather data with fallback and error handling
        weather_data = weather_manager.get_current_weather_with_fallback(city_name, country)
        
        if weather_data:
            response_data = {
                'current': WeatherDataSerializer(weather_data).data,
                'air_quality': None,  # Temporarily disabled until fixed
                'forecast': []  # Temporarily disabled until fixed
            }
            return Response(response_data)
        else:
            return Response(
                {'error': 'Unable to fetch weather data for this city'},
                status=status.HTTP_404_NOT_FOUND
            )
            
    except Exception as e:
        logger.error(f"Error getting weather by city name: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_forecast(request, city_id):
    """Get weather forecast for a specific city"""
    try:
        city = get_object_or_404(City, id=city_id)
        days = int(request.GET.get('days', 5))
        
        # Get forecast data
        forecasts = weather_manager.openweather.get_forecast(
            city.name, city.country, days
        )
        
        serializer = WeatherForecastSerializer(forecasts, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error getting forecast: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_air_quality(request, city_id):
    """Get air quality data for a specific city"""
    try:
        city = get_object_or_404(City, id=city_id)
        
        # Get recent air quality data
        air_quality = AirQualityData.objects.filter(city=city).first()
        
        if not air_quality:
            # Fetch new data
            air_quality = weather_manager.openweather.get_air_quality(
                city.latitude, city.longitude
            )
        
        if air_quality:
            serializer = AirQualityDataSerializer(air_quality)
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'Unable to fetch air quality data'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
            
    except Exception as e:
        logger.error(f"Error getting air quality: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_multiple_cities_weather(request):
    """Get weather data for multiple cities"""
    city_names = request.GET.get('cities', '').split(',')
    city_names = [name.strip() for name in city_names if name.strip()]
    
    if not city_names:
        return Response(
            {'error': 'At least one city name is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        results = []
        for city_name in city_names[:10]:  # Limit to 10 cities
            weather_data = weather_manager.get_current_weather_with_fallback(city_name)
            if weather_data:
                results.append({
                    'city': city_name,
                    'current': WeatherDataSerializer(weather_data).data,
                    'air_quality': None  # Temporarily disabled
                })
        
        return Response({'cities': results})
        
    except Exception as e:
        logger.error(f"Error getting multiple cities weather: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_weather_data(request):
    """Manually refresh weather data for all cities"""
    try:
        updated_count = weather_manager.update_weather_for_all_cities()
        return Response({
            'message': f'Successfully updated weather data for {updated_count} cities'
        })
        
    except Exception as e:
        logger.error(f"Error refreshing weather data: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



@api_view(['GET'])
@permission_classes([AllowAny])
def get_ai_predictions(request):
    """Get AI-powered 24-hour weather predictions"""
    city_name = request.GET.get('city')
    
    if not city_name:
        return Response(
            {'error': 'City name is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Get city and current weather
        city = City.objects.filter(name__iexact=city_name).first()
        if not city:
            # Try to get weather data first to create city
            weather_data = weather_manager.get_comprehensive_weather(city_name)
            if not weather_data:
                return Response(
                    {'error': 'City not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            city = weather_data['current'].city
        
        # Get latest weather data
        current_weather = WeatherData.objects.filter(city=city).order_by('-timestamp').first()
        if not current_weather:
            # Get fresh weather data
            weather_data = weather_manager.get_comprehensive_weather(city_name)
            if weather_data:
                current_weather = weather_data['current']
            else:
                return Response(
                    {'error': 'Unable to get current weather data'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
        
        # Generate AI predictions using advanced predictor
        predictions = advanced_predictor.predict_advanced_24h(city, current_weather)
        
        return Response({
            'city': city.name,
            'current_weather': WeatherDataSerializer(current_weather).data,
            'predictions': predictions,
            'generated_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting AI predictions: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_historical_data(request):
    """Get historical weather data for trends analysis"""
    city_name = request.GET.get('city')
    days = int(request.GET.get('days', 30))
    
    if not city_name:
        return Response(
            {'error': 'City name is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        city = City.objects.filter(name__iexact=city_name).first()
        if not city:
            return Response(
                {'error': 'City not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get historical data
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        historical_data = WeatherData.objects.filter(
            city=city,
            timestamp__range=(start_date, end_date)
        ).order_by('timestamp')
        
        if not historical_data.exists():
            # Generate demo historical data
            historical_data = _generate_demo_historical_data(city, days)
        
        # Serialize data
        serialized_data = WeatherDataSerializer(historical_data, many=True).data
        
        # Calculate trends
        temps = [float(d['temperature']) for d in serialized_data]
        humidity = [float(d['humidity']) for d in serialized_data]
        
        trends = {
            'temperature': {
                'avg': round(sum(temps) / len(temps), 1) if temps else 0,
                'min': round(min(temps), 1) if temps else 0,
                'max': round(max(temps), 1) if temps else 0,
                'trend': 'stable'  # Could implement trend analysis
            },
            'humidity': {
                'avg': round(sum(humidity) / len(humidity), 1) if humidity else 0,
                'min': round(min(humidity), 1) if humidity else 0,
                'max': round(max(humidity), 1) if humidity else 0,
                'trend': 'stable'
            }
        }
        
        return Response({
            'city': city.name,
            'period': f'{days} days',
            'data': serialized_data,
            'trends': trends,
            'data_points': len(serialized_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _generate_demo_historical_data(city, days):
    """Generate demo historical data for demonstration"""
    import random
    
    historical_data = []
    base_date = timezone.now() - timedelta(days=days)
    
    for i in range(days * 4):  # 4 data points per day
        timestamp = base_date + timedelta(hours=i * 6)
        base_temp = 20 + random.uniform(-10, 10)
        
        weather_data = WeatherData.objects.create(
            city=city,
            temperature=round(base_temp, 1),
            feels_like=round(base_temp + random.uniform(-3, 3), 1),
            humidity=random.randint(30, 90),
            pressure=random.randint(1000, 1030),
            wind_speed=round(random.uniform(0, 25), 1),
            wind_direction=random.randint(0, 360),
            weather_condition=random.choice(['Clear', 'Clouds', 'Rain']),
            weather_description=random.choice(['clear sky', 'few clouds', 'light rain']),
            visibility=round(random.uniform(5, 15), 1),
            uv_index=random.randint(1, 11),
            timestamp=timestamp
        )
        historical_data.append(weather_data)
    
    return historical_data


@api_view(['GET'])
@permission_classes([AllowAny])
def compare_cities(request):
    """Compare weather data across multiple cities"""
    city_names = request.GET.get('cities', '').split(',')
    city_names = [name.strip() for name in city_names if name.strip()]
    
    if len(city_names) < 2:
        return Response(
            {'error': 'At least 2 cities are required for comparison'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        comparison_data = []
        
        for city_name in city_names[:6]:  # Limit to 6 cities
            weather_data = weather_manager.get_comprehensive_weather(city_name)
            if weather_data:
                city_data = {
                    'city': city_name,
                    'current': WeatherDataSerializer(weather_data['current']).data,
                    'air_quality': AirQualityDataSerializer(weather_data['air_quality']).data if weather_data['air_quality'] else None,
                    'forecast_summary': {
                        'avg_temp': sum([f.temperature_max + f.temperature_min for f in weather_data['forecast'][:3]]) / 6 if weather_data['forecast'] else 0,
                        'conditions': [f.weather_condition for f in weather_data['forecast'][:3]] if weather_data['forecast'] else []
                    }
                }
                comparison_data.append(city_data)
        
        # Generate comparison insights
        if len(comparison_data) >= 2:
            temps = [float(city['current']['temperature']) for city in comparison_data]
            insights = {
                'warmest_city': comparison_data[temps.index(max(temps))]['city'],
                'coolest_city': comparison_data[temps.index(min(temps))]['city'],
                'temperature_range': round(max(temps) - min(temps), 1),
                'average_temperature': round(sum(temps) / len(temps), 1)
            }
        else:
            insights = {}
        
        return Response({
            'cities': comparison_data,
            'insights': insights,
            'comparison_time': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error comparing cities: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_weather_alerts(request):
    """Manually trigger weather alert processing"""
    try:
        city_name = request.data.get('city')
        if not city_name:
            return Response(
                {'error': 'City name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        city = City.objects.filter(name__iexact=city_name).first()
        if not city:
            return Response(
                {'error': 'City not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Trigger alert processing
        alerts_sent = process_weather_alerts.delay(city.id)
        
        return Response({
            'message': f'Alert processing triggered for {city.name}',
            'task_id': alerts_sent.id
        })
        
    except Exception as e:
        logger.error(f"Error triggering alerts: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_weather_analytics(request):
    """Get comprehensive weather analytics for a city"""
    city_name = request.GET.get('city')
    days = int(request.GET.get('days', 7))
    
    if not city_name:
        return Response(
            {'error': 'City name is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        city = City.objects.filter(name__iexact=city_name).first()
        if not city:
            return Response(
                {'error': 'City not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get comprehensive weather data
        weather_data = weather_aggregator.get_comprehensive_weather_data(city_name)
        if not weather_data:
            return Response(
                {'error': 'Unable to fetch weather data'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Get historical data for analytics
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        historical_data = WeatherData.objects.filter(
            city=city,
            timestamp__range=(start_date, end_date)
        ).order_by('timestamp')
        
        # Calculate analytics
        analytics = {
            'current': WeatherDataSerializer(weather_data['current']).data,
            'air_quality': AirQualityDataSerializer(weather_data['air_quality']).data if weather_data['air_quality'] else None,
            'forecast': WeatherForecastSerializer(weather_data['forecast'], many=True).data,
            'historical_summary': _calculate_historical_summary(historical_data),
            'weather_patterns': _identify_weather_patterns(historical_data),
            'severity_score': weather_processor.get_weather_severity_score(weather_data['current']),
            'recommendations': _generate_weather_recommendations(weather_data['current'])
        }
        
        return Response(analytics)
        
    except Exception as e:
        logger.error(f"Error getting weather analytics: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _calculate_historical_summary(historical_data):
    """Calculate summary statistics from historical data"""
    if not historical_data.exists():
        return {}
    
    data = list(historical_data.values('temperature', 'humidity', 'pressure', 'wind_speed'))
    
    summary = {}
    for metric in ['temperature', 'humidity', 'pressure', 'wind_speed']:
        values = [d[metric] for d in data if d[metric] is not None]
        if values:
            summary[metric] = {
                'avg': round(sum(values) / len(values), 1),
                'min': round(min(values), 1),
                'max': round(max(values), 1),
                'trend': _calculate_trend(values)
            }
    
    return summary


def _calculate_trend(values):
    """Calculate trend direction for a series of values"""
    if len(values) < 2:
        return 'stable'
    
    first_half = values[:len(values)//2]
    second_half = values[len(values)//2:]
    
    first_avg = sum(first_half) / len(first_half)
    second_avg = sum(second_half) / len(second_half)
    
    change_percent = ((second_avg - first_avg) / first_avg) * 100
    
    if change_percent > 5:
        return 'increasing'
    elif change_percent < -5:
        return 'decreasing'
    else:
        return 'stable'


def _identify_weather_patterns(historical_data):
    """Identify weather patterns from historical data"""
    patterns = []
    
    if not historical_data.exists():
        return patterns
    
    # Temperature patterns
    temps = list(historical_data.values_list('temperature', flat=True))
    if temps:
        avg_temp = sum(temps) / len(temps)
        if avg_temp > 30:
            patterns.append({
                'type': 'heat_wave',
                'description': 'Sustained high temperatures detected',
                'confidence': 0.8
            })
        elif avg_temp < 5:
            patterns.append({
                'type': 'cold_spell',
                'description': 'Extended cold period detected',
                'confidence': 0.8
            })
    
    # Wind patterns
    wind_speeds = list(historical_data.values_list('wind_speed', flat=True))
    if wind_speeds:
        avg_wind = sum(wind_speeds) / len(wind_speeds)
        if avg_wind > 25:
            patterns.append({
                'type': 'windy_period',
                'description': 'Consistently high wind speeds',
                'confidence': 0.7
            })
    
    return patterns


def _generate_weather_recommendations(weather_data):
    """Generate weather-based recommendations"""
    recommendations = []
    
    # Temperature recommendations
    if weather_data.temperature > 35:
        recommendations.append({
            'type': 'health',
            'message': 'Extreme heat detected. Stay hydrated and avoid prolonged outdoor exposure.',
            'priority': 'high'
        })
    elif weather_data.temperature < -10:
        recommendations.append({
            'type': 'health',
            'message': 'Extreme cold detected. Dress warmly and limit outdoor activities.',
            'priority': 'high'
        })
    
    # Wind recommendations
    if weather_data.wind_speed > 50:
        recommendations.append({
            'type': 'safety',
            'message': 'High winds detected. Secure loose objects and avoid driving high-profile vehicles.',
            'priority': 'high'
        })
    
    # Visibility recommendations
    if weather_data.visibility < 2:
        recommendations.append({
            'type': 'travel',
            'message': 'Low visibility conditions. Drive slowly and use headlights.',
            'priority': 'medium'
        })
    
    # General recommendations
    if weather_data.humidity > 80:
        recommendations.append({
            'type': 'comfort',
            'message': 'High humidity levels. Consider using air conditioning or dehumidifiers.',
            'priority': 'low'
        })
    
    return recommendations


@api_view(['GET'])
@permission_classes([AllowAny])
def get_weather_map_data(request):
    """Get weather data formatted for map visualization"""
    try:
        cities = request.GET.get('cities', '').split(',')
        cities = [city.strip() for city in cities if city.strip()]
        
        if not cities:
            # Default cities for map
            cities = ['New York', 'London', 'Tokyo', 'Paris', 'Sydney', 'Dubai', 'Mumbai', 'Singapore']
        
        map_data = []
        
        for city_name in cities[:20]:  # Limit to 20 cities
            try:
                weather_data = weather_aggregator.get_comprehensive_weather_data(city_name)
                if weather_data and weather_data['current']:
                    current = weather_data['current']
                    
                    map_data.append({
                        'city': city_name,
                        'coordinates': {
                            'lat': float(current.city.latitude),
                            'lng': float(current.city.longitude)
                        },
                        'weather': {
                            'temperature': current.temperature,
                            'condition': current.weather_condition,
                            'description': current.weather_description,
                            'humidity': current.humidity,
                            'wind_speed': current.wind_speed,
                            'pressure': current.pressure
                        },
                        'air_quality': {
                            'aqi': weather_data['air_quality'].aqi if weather_data['air_quality'] else None
                        },
                        'severity_score': weather_processor.get_weather_severity_score(current),
                        'last_updated': current.timestamp.isoformat()
                    })
            except Exception as e:
                logger.error(f"Error getting map data for {city_name}: {e}")
                continue
        
        return Response({
            'map_data': map_data,
            'total_cities': len(map_data),
            'generated_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting weather map data: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def search_cities(request):
    """Search cities by name"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return Response(
            {'error': 'Search query is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(query) < 2:
        return Response(
            {'error': 'Search query must be at least 2 characters'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Search existing cities
        cities = City.objects.filter(
            name__icontains=query,
            is_active=True
        ).order_by('name')[:10]
        
        results = []
        for city in cities:
            results.append({
                'id': city.id,
                'name': city.name,
                'country': city.country,
                'latitude': city.latitude,
                'longitude': city.longitude,
                'exists': True
            })
        
        # If we have fewer than 5 results, suggest some common cities
        if len(results) < 5:
            suggestions = [
                {'name': 'New York', 'country': 'US', 'latitude': 40.7128, 'longitude': -74.0060},
                {'name': 'London', 'country': 'GB', 'latitude': 51.5074, 'longitude': -0.1278},
                {'name': 'Tokyo', 'country': 'JP', 'latitude': 35.6762, 'longitude': 139.6503},
                {'name': 'Paris', 'country': 'FR', 'latitude': 48.8566, 'longitude': 2.3522},
                {'name': 'Sydney', 'country': 'AU', 'latitude': -33.8688, 'longitude': 151.2093},
                {'name': 'Dubai', 'country': 'AE', 'latitude': 25.2048, 'longitude': 55.2708},
                {'name': 'Mumbai', 'country': 'IN', 'latitude': 19.0760, 'longitude': 72.8777},
                {'name': 'Singapore', 'country': 'SG', 'latitude': 1.3521, 'longitude': 103.8198},
            ]
            
            for suggestion in suggestions:
                if query.lower() in suggestion['name'].lower():
                    # Check if city already exists
                    existing = City.objects.filter(
                        name__iexact=suggestion['name']
                    ).first()
                    
                    if not existing and len(results) < 10:
                        results.append({
                            'id': None,
                            'name': suggestion['name'],
                            'country': suggestion['country'],
                            'latitude': suggestion['latitude'],
                            'longitude': suggestion['longitude'],
                            'exists': False
                        })
        
        return Response({'results': results})
        
    except Exception as e:
        logger.error(f"Error searching cities: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def add_city(request):
    """Add a new city to the database"""
    try:
        # Validate and sanitize input data
        city_data = {
            'name': request.data.get('name', ''),
            'country': request.data.get('country', ''),
            'latitude': request.data.get('latitude'),
            'longitude': request.data.get('longitude')
        }
        
        # Validate city data
        try:
            validated_data = CityValidator.validate_city_data(city_data)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if city already exists
        existing_city = City.objects.filter(
            name__iexact=validated_data['name'],
            country__iexact=validated_data['country']
        ).first()
        
        if existing_city:
            return Response({
                'message': 'City already exists',
                'city': CitySerializer(existing_city).data
            })
        
        # Create new city
        city = City.objects.create(
            name=validated_data['name'],
            country=validated_data['country'],
            latitude=validated_data.get('latitude', 0.0),
            longitude=validated_data.get('longitude', 0.0),
            timezone='UTC',
            is_active=True
        )
        
        # Try to get initial weather data
        try:
            weather_data = weather_manager.get_current_weather_with_fallback(
                validated_data['name'], 
                validated_data['country']
            )
            if weather_data:
                logger.info(f"Successfully added weather data for new city: {validated_data['name']}")
        except Exception as weather_error:
            logger.warning(f"Could not fetch initial weather data for {validated_data['name']}: {weather_error}")
        
        return Response({
            'message': 'City added successfully',
            'city': CitySerializer(city).data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error adding city: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cache_stats(request):
    """Get cache statistics and health"""
    try:
        stats = WeatherCacheManager.get_cache_stats()
        
        # Add some additional stats
        stats.update({
            'cache_keys_info': {
                'weather_ttl': WeatherCacheManager.CACHE_TTL['current_weather'],
                'forecast_ttl': WeatherCacheManager.CACHE_TTL['forecast'],
                'air_quality_ttl': WeatherCacheManager.CACHE_TTL['air_quality'],
            },
            'prefixes': WeatherCacheManager.PREFIXES
        })
        
        return Response(stats)
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_cache(request):
    """Clear cache for specific city or all cache"""
    try:
        city_name = request.data.get('city')
        clear_all = request.data.get('clear_all', False)
        
        if clear_all:
            # Clear all cache (admin only)
            if not request.user.is_staff:
                return Response(
                    {'error': 'Admin privileges required'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            cache.clear()
            return Response({'message': 'All cache cleared successfully'})
        
        elif city_name:
            # Clear cache for specific city
            invalidate_city_cache(city_name)
            return Response({'message': f'Cache cleared for {city_name}'})
        
        else:
            return Response(
                {'error': 'Specify city name or set clear_all=true'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
@api_view(['GET'])
@permission_classes([AllowAny])
def get_system_health(request):
    """Get system health status including API services and cache"""
    try:
        health_data = weather_manager.get_service_health()
        
        # Add database health
        try:
            city_count = City.objects.count()
            weather_count = WeatherData.objects.count()
            health_data['database'] = {
                'status': 'healthy',
                'cities_count': city_count,
                'weather_records_count': weather_count,
                'last_check': timezone.now().isoformat()
            }
        except Exception as db_error:
            health_data['database'] = {
                'status': 'unhealthy',
                'error': str(db_error),
                'last_check': timezone.now().isoformat()
            }
        
        # Determine overall health
        overall_status = 'healthy'
        if not health_data['cache_status']:
            overall_status = 'degraded'
        if health_data['primary_service']['status'] == 'unhealthy':
            overall_status = 'degraded'
        if health_data['database']['status'] == 'unhealthy':
            overall_status = 'unhealthy'
        
        health_data['overall_status'] = overall_status
        
        # Set appropriate HTTP status code
        status_code = status.HTTP_200_OK
        if overall_status == 'degraded':
            status_code = status.HTTP_206_PARTIAL_CONTENT
        elif overall_status == 'unhealthy':
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response(health_data, status=status_code)
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return Response({
            'overall_status': 'unhealthy',
            'error': 'Health check failed',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_background_refresh(request):
    """Start background weather refresh service"""
    try:
        if not request.user.is_staff:
            return Response(
                {'error': 'Admin privileges required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from .management.commands.weather_scheduler import weather_scheduler
        
        interval_minutes = request.data.get('interval_minutes', 15)
        
        if weather_scheduler.start_background_refresh(interval_minutes):
            return Response({
                'message': 'Background refresh started successfully',
                'interval_minutes': interval_minutes,
                'status': 'running'
            })
        else:
            return Response({
                'message': 'Background refresh already running',
                'status': 'already_running'
            })
        
    except Exception as e:
        logger.error(f"Error starting background refresh: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stop_background_refresh(request):
    """Stop background weather refresh service"""
    try:
        if not request.user.is_staff:
            return Response(
                {'error': 'Admin privileges required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from .management.commands.weather_scheduler import weather_scheduler
        
        weather_scheduler.stop_background_refresh()
        
        return Response({
            'message': 'Background refresh stopped successfully',
            'status': 'stopped'
        })
        
    except Exception as e:
        logger.error(f"Error stopping background refresh: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_scheduler_status(request):
    """Get background scheduler status"""
    try:
        from .management.commands.weather_scheduler import weather_scheduler
        
        status_data = {
            'running': weather_scheduler.running,
            'refresh_interval_seconds': weather_scheduler.refresh_interval,
            'refresh_interval_minutes': weather_scheduler.refresh_interval // 60,
            'thread_alive': weather_scheduler.refresh_thread.is_alive() if weather_scheduler.refresh_thread else False,
            'last_check': timezone.now().isoformat()
        }
        
        return Response(status_data)
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Background Task Monitoring and Management Views

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def task_monitoring_dashboard(request):
    """Get background task monitoring dashboard data"""
    try:
        from celery import current_app
        from django.db.models import Count, Avg
        
        # Get Celery app stats
        inspect = current_app.control.inspect()
        
        # Get active tasks
        active_tasks = inspect.active()
        scheduled_tasks = inspect.scheduled()
        
        # Get task statistics
        task_stats = {
            'active_tasks': len(active_tasks) if active_tasks else 0,
            'scheduled_tasks': len(scheduled_tasks) if scheduled_tasks else 0,
        }
        
        # Get weather data statistics
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_hour = now - timedelta(hours=1)
        
        weather_stats = {
            'total_cities': City.objects.filter(is_active=True).count(),
            'weather_records_24h': WeatherData.objects.filter(timestamp__gte=last_24h).count(),
            'weather_records_1h': WeatherData.objects.filter(timestamp__gte=last_hour).count(),
            'avg_temperature_24h': WeatherData.objects.filter(
                timestamp__gte=last_24h
            ).aggregate(Avg('temperature'))['temperature__avg'],
        }
        
        # Get cache statistics
        cache_stats = WeatherCacheManager.get_cache_stats()
        
        # Get API health
        api_health = weather_manager.get_service_health()
        
        dashboard_data = {
            'timestamp': now.isoformat(),
            'task_stats': task_stats,
            'weather_stats': weather_stats,
            'cache_stats': cache_stats,
            'api_health': api_health,
        }
        
        return Response(dashboard_data)
        
    except Exception as e:
        logger.error(f'Error getting task monitoring dashboard: {e}')
        return Response(
            {'error': 'Failed to get monitoring data'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_weather_refresh(request):
    """Manually trigger weather refresh for all cities or specific cities"""
    try:
        city_names = request.data.get('cities', [])
        
        if city_names:
            # Refresh specific cities
            tasks = []
            for city_name in city_names:
                try:
                    city = City.objects.get(name=city_name, is_active=True)
                    task = refresh_city_weather.delay(city.id)
                    tasks.append({
                        'city': city_name,
                        'task_id': task.id
                    })
                except City.DoesNotExist:
                    logger.warning(f'City not found: {city_name}')
            
            return Response({
                'message': f'Triggered refresh for {len(tasks)} cities',
                'tasks': tasks
            })
        else:
            # Refresh all cities
            task = refresh_all_cities_weather.delay()
            return Response({
                'message': 'Triggered refresh for all cities',
                'task_id': task.id
            })
            
    except Exception as e:
        logger.error(f'Error triggering weather refresh: {e}')
        return Response(
            {'error': 'Failed to trigger refresh'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def task_status(request, task_id):
    """Get status of a specific background task"""
    try:
        from celery.result import AsyncResult
        
        result = AsyncResult(task_id)
        
        task_info = {
            'task_id': task_id,
            'status': result.status,
            'result': result.result if result.ready() else None,
            'traceback': result.traceback if result.failed() else None,
        }
        
        return Response(task_info)
        
    except Exception as e:
        logger.error(f'Error getting task status: {e}')
        return Response(
            {'error': 'Failed to get task status'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_quota_status(request):
    """Get API quota usage and health status"""
    try:
        # Get service health which includes quota information
        health = weather_manager.get_service_health()
        
        # Add additional quota monitoring
        quota_info = {
            'timestamp': timezone.now().isoformat(),
            'services': health,
            'recommendations': []
        }
        
        # Add recommendations based on service status
        for service_name, service_info in health.items():
            if service_info.get('status') != 'healthy':
                quota_info['recommendations'].append(
                    f'Consider checking {service_name} service configuration'
                )
        
        return Response(quota_info)
        
    except Exception as e:
        logger.error(f'Error getting API quota status: {e}')
        return Response(
            {'error': 'Failed to get quota status'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_health(request):
    """Get overall system health including background tasks"""
    try:
        from celery import current_app
        
        # Check Celery connection
        try:
            inspect = current_app.control.inspect()
            stats = inspect.stats()
            celery_healthy = bool(stats)
        except Exception:
            celery_healthy = False
        
        # Check Redis connection
        try:
            cache.get('health_check')
            redis_healthy = True
        except Exception:
            redis_healthy = False
        
        # Check database
        try:
            City.objects.count()
            db_healthy = True
        except Exception:
            db_healthy = False
        
        # Check API services
        api_health = weather_manager.get_service_health()
        api_healthy = any(
            service.get('status') == 'healthy' 
            for service in api_health.values()
        )
        
        health_status = {
            'timestamp': timezone.now().isoformat(),
            'overall_healthy': all([celery_healthy, redis_healthy, db_healthy, api_healthy]),
            'components': {
                'celery': celery_healthy,
                'redis': redis_healthy,
                'database': db_healthy,
                'weather_apis': api_healthy,
            },
            'api_services': api_health
        }
        
        return Response(health_status)
        
    except Exception as e:
        logger.error(f'Error getting system health: {e}')
        return Response(
            {'error': 'Failed to get system health'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Weather Analytics and Monitoring Views

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_dashboard(request):
    """Get comprehensive analytics dashboard data"""
    try:
        from .analytics import weather_analytics
        
        # Get query parameters
        hours = int(request.GET.get('hours', 24))
        days = int(request.GET.get('days', 7))
        
        # Gather all analytics data
        dashboard_data = {
            'api_usage': weather_analytics.get_api_usage_stats(hours),
            'cache_performance': weather_analytics.get_cache_performance_stats(),
            'data_freshness': weather_analytics.get_data_freshness_stats(),
            'weather_trends': weather_analytics.get_weather_trends(days),
            'generated_at': timezone.now().isoformat()
        }
        
        return Response(dashboard_data)
        
    except Exception as e:
        logger.error(f'Error getting analytics dashboard: {e}')
        return Response(
            {'error': 'Failed to get analytics data'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_usage_analytics(request):
    """Get detailed API usage analytics"""
    try:
        from .analytics import weather_analytics
        
        hours = int(request.GET.get('hours', 24))
        usage_stats = weather_analytics.get_api_usage_stats(hours)
        
        return Response(usage_stats)
        
    except Exception as e:
        logger.error(f'Error getting API usage analytics: {e}')
        return Response(
            {'error': 'Failed to get API usage data'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cache_analytics(request):
    """Get cache performance analytics"""
    try:
        from .analytics import weather_analytics
        
        cache_stats = weather_analytics.get_cache_performance_stats()
        
        return Response(cache_stats)
        
    except Exception as e:
        logger.error(f'Error getting cache analytics: {e}')
        return Response(
            {'error': 'Failed to get cache analytics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def data_freshness_monitor(request):
    """Get data freshness monitoring information"""
    try:
        from .analytics import weather_analytics
        
        freshness_stats = weather_analytics.get_data_freshness_stats()
        
        return Response(freshness_stats)
        
    except Exception as e:
        logger.error(f'Error getting data freshness stats: {e}')
        return Response(
            {'error': 'Failed to get freshness data'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weather_trends_analytics(request):
    """Get weather trends and patterns"""
    try:
        from .analytics import weather_analytics
        
        days = int(request.GET.get('days', 7))
        trends = weather_analytics.get_weather_trends(days)
        
        return Response(trends)
        
    except Exception as e:
        logger.error(f'Error getting weather trends: {e}')
        return Response(
            {'error': 'Failed to get weather trends'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_health_report(request):
    """Get comprehensive system health report"""
    try:
        from .analytics import health_monitor
        
        health_report = health_monitor.get_system_health_report()
        
        return Response(health_report)
        
    except Exception as e:
        logger.error(f'Error getting system health report: {e}')
        return Response(
            {'error': 'Failed to get health report'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_health_check(request):
    """Manually trigger system health check and alerts"""
    try:
        from .analytics import health_monitor
        
        if not request.user.is_staff:
            return Response(
                {'error': 'Staff access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        health_report = health_monitor.check_and_send_alerts()
        
        return Response({
            'message': 'Health check completed',
            'report': health_report
        })
        
    except Exception as e:
        logger.error(f'Error triggering health check: {e}')
        return Response(
            {'error': 'Failed to trigger health check'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Performance Optimization Views

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def performance_metrics(request):
    """Get current performance metrics"""
    try:
        from .performance import performance_monitor
        
        metrics = performance_monitor.get_performance_metrics()
        
        return Response(metrics)
        
    except Exception as e:
        logger.error(f'Error getting performance metrics: {e}')
        return Response(
            {'error': 'Failed to get performance metrics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def performance_analysis(request):
    """Get performance bottleneck analysis"""
    try:
        from .performance import performance_monitor
        
        analysis = performance_monitor.analyze_performance_bottlenecks()
        
        return Response(analysis)
        
    except Exception as e:
        logger.error(f'Error analyzing performance: {e}')
        return Response(
            {'error': 'Failed to analyze performance'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def optimize_cache(request):
    """Trigger cache optimization"""
    try:
        from .performance import cache_optimizer
        
        if not request.user.is_staff:
            return Response(
                {'error': 'Staff access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Optimize cache keys
        key_optimization = cache_optimizer.optimize_cache_keys()
        
        # Implement cache warming
        warming_result = cache_optimizer.implement_cache_warming_strategy()
        
        return Response({
            'message': 'Cache optimization completed',
            'key_optimization': key_optimization,
            'cache_warming': warming_result,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f'Error optimizing cache: {e}')
        return Response(
            {'error': 'Failed to optimize cache'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def optimized_weather_data(request):
    """Get weather data with performance optimizations"""
    try:
        from .performance import db_optimizer, PaginationOptimizer
        
        # Get query parameters
        city_id = request.GET.get('city_id')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        use_cursor = request.GET.get('cursor') == 'true'
        cursor_value = request.GET.get('cursor_value')
        
        # Get optimized weather data
        if city_id:
            queryset = db_optimizer.get_optimized_weather_data(city_id=city_id, limit=1000)
        else:
            queryset = db_optimizer.get_optimized_weather_data(limit=1000)
        
        # Apply pagination
        if use_cursor:
            result = PaginationOptimizer.get_cursor_paginated_data(
                queryset, cursor_value=cursor_value, limit=page_size
            )
        else:
            result = PaginationOptimizer.get_optimized_paginated_data(
                queryset, page, page_size
            )
        
        # Use compression for large responses
        from .performance import ResponseCompressor
        
        if len(str(result)) > 10000:  # Compress responses larger than 10KB
            return ResponseCompressor.create_compressed_response(result)
        else:
            return Response(result)
        
    except Exception as e:
        logger.error(f'Error getting optimized weather data: {e}')
        return Response(
            {'error': 'Failed to get weather data'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def optimized_cities_list(request):
    """Get cities list with performance optimizations"""
    try:
        from .performance import db_optimizer
        
        # Get cities with latest weather using optimized query
        cities = db_optimizer.get_cities_with_latest_weather()
        
        # Format response data
        cities_data = []
        for city in cities:
            city_data = {
                'id': city.id,
                'name': city.name,
                'country': city.country,
                'latitude': city.latitude,
                'longitude': city.longitude,
                'latest_weather': None
            }
            
            # Add latest weather if available
            if hasattr(city, 'latest_weather') and city.latest_weather:
                latest = city.latest_weather[0]
                city_data['latest_weather'] = {
                    'temperature': latest.temperature,
                    'humidity': latest.humidity,
                    'weather_condition': latest.weather_condition,
                    'timestamp': latest.timestamp.isoformat()
                }
            
            cities_data.append(city_data)
        
        return Response({
            'cities': cities_data,
            'count': len(cities_data),
            'optimized': True
        })
        
    except Exception as e:
        logger.error(f'Error getting optimized cities list: {e}')
        return Response(
            {'error': 'Failed to get cities list'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_weather_update(request):
    """Bulk update weather data for better performance"""
    try:
        from .performance import db_optimizer
        
        if not request.user.is_staff:
            return Response(
                {'error': 'Staff access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        weather_updates = request.data.get('weather_updates', [])
        
        if not weather_updates:
            return Response(
                {'error': 'No weather updates provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Perform bulk update
        created_count = db_optimizer.bulk_update_weather_data(weather_updates)
        
        return Response({
            'message': 'Bulk weather update completed',
            'created_count': created_count,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f'Error performing bulk weather update: {e}')
        return Response(
            {'error': 'Failed to perform bulk update'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# API Integration Management Views

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_providers_list(request):
    """Get list of API providers"""
    try:
        from .api_management import APIProvider
        
        providers = APIProvider.objects.all().order_by('priority')
        
        providers_data = []
        for provider in providers:
            usage_today = provider.get_usage_today()
            usage_month = provider.get_usage_this_month()
            
            providers_data.append({
                'id': provider.id,
                'name': provider.name,
                'display_name': provider.display_name,
                'is_active': provider.is_active,
                'is_primary': provider.is_primary,
                'is_healthy': provider.is_healthy,
                'priority': provider.priority,
                'success_rate': provider.success_rate,
                'usage_today': usage_today,
                'usage_month': usage_month,
                'requests_per_day': provider.requests_per_day,
                'monthly_budget': float(provider.monthly_budget),
                'cost_per_request': float(provider.cost_per_request),
                'last_health_check': provider.last_health_check,
                'supported_endpoints': provider.supported_endpoints
            })
        
        return Response(providers_data)
        
    except Exception as e:
        logger.error(f'Error getting API providers: {e}')
        return Response(
            {'error': 'Failed to retrieve API providers'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'PUT'])
@permission_classes([IsAdminUser])
def api_provider_detail(request, provider_id):
    """Get or update API provider details"""
    try:
        from .api_management import APIProvider
        
        provider = APIProvider.objects.get(id=provider_id)
        
        if request.method == 'GET':
            from .api_management import api_manager
            stats = api_manager.get_provider_statistics(provider_id, days=30)
            return Response(stats)
        
        elif request.method == 'PUT':
            # Update provider configuration
            data = request.data
            
            # Update basic fields
            for field in ['display_name', 'base_url', 'api_key', 'is_active', 'is_primary', 'priority']:
                if field in data:
                    setattr(provider, field, data[field])
            
            # Update rate limits
            for field in ['requests_per_minute', 'requests_per_day', 'requests_per_month']:
                if field in data:
                    setattr(provider, field, data[field])
            
            # Update cost settings
            for field in ['cost_per_request', 'monthly_budget']:
                if field in data:
                    setattr(provider, field, data[field])
            
            # Update configuration
            if 'configuration' in data:
                provider.configuration = data['configuration']
            
            if 'supported_endpoints' in data:
                provider.supported_endpoints = data['supported_endpoints']
            
            provider.save()
            
            return Response({'message': 'Provider updated successfully'})
        
    except APIProvider.DoesNotExist:
        return Response(
            {'error': 'Provider not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f'Error handling API provider: {e}')
        return Response(
            {'error': 'Operation failed'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def api_provider_health_check(request, provider_id):
    """Perform health check on API provider"""
    try:
        from .api_management import APIProvider, api_manager
        
        provider = APIProvider.objects.get(id=provider_id)
        health_result = api_manager.perform_health_check(provider)
        
        return Response(health_result)
        
    except APIProvider.DoesNotExist:
        return Response(
            {'error': 'Provider not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f'Error performing health check: {e}')
        return Response(
            {'error': 'Health check failed'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_usage_analytics(request):
    """Get API usage analytics"""
    try:
        from .api_management import api_manager
        
        days = int(request.GET.get('days', 30))
        cost_analysis = api_manager.get_cost_analysis(days)
        
        return Response(cost_analysis)
        
    except Exception as e:
        logger.error(f'Error getting API usage analytics: {e}')
        return Response(
            {'error': 'Failed to retrieve usage analytics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_failover_events(request):
    """Get recent API failover events"""
    try:
        from .api_management import APIFailover
        
        days = int(request.GET.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        failovers = APIFailover.objects.filter(
            failed_at__gte=start_date
        ).select_related('primary_provider', 'fallback_provider').order_by('-failed_at')[:50]
        
        failover_data = []
        for failover in failovers:
            failover_data.append({
                'id': failover.id,
                'primary_provider': failover.primary_provider.display_name,
                'fallback_provider': failover.fallback_provider.display_name,
                'endpoint': failover.endpoint,
                'reason': failover.reason,
                'failed_at': failover.failed_at,
                'resolved_at': failover.resolved_at,
                'error_details': failover.error_details
            })
        
        return Response({
            'failover_events': failover_data,
            'period_days': days,
            'total_events': len(failover_data)
        })
        
    except Exception as e:
        logger.error(f'Error getting failover events: {e}')
        return Response(
            {'error': 'Failed to retrieve failover events'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def api_provider_create(request):
    """Create new API provider"""
    try:
        from .api_management import APIProvider
        
        data = request.data
        
        # Validate required fields
        required_fields = ['name', 'display_name', 'base_url']
        for field in required_fields:
            if field not in data:
                return Response(
                    {'error': f'{field} is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Check if provider already exists
        if APIProvider.objects.filter(name=data['name']).exists():
            return Response(
                {'error': 'Provider with this name already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create provider
        provider = APIProvider.objects.create(
            name=data['name'],
            display_name=data['display_name'],
            base_url=data['base_url'],
            api_key=data.get('api_key', ''),
            is_active=data.get('is_active', True),
            priority=data.get('priority', 1),
            requests_per_minute=data.get('requests_per_minute', 60),
            requests_per_day=data.get('requests_per_day', 1000),
            requests_per_month=data.get('requests_per_month', 100000),
            cost_per_request=data.get('cost_per_request', 0.0),
            monthly_budget=data.get('monthly_budget', 0.0),
            supported_endpoints=data.get('supported_endpoints', []),
            configuration=data.get('configuration', {})
        )
        
        return Response({
            'message': 'Provider created successfully',
            'provider_id': provider.id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f'Error creating API provider: {e}')
        return Response(
            {'error': 'Failed to create provider'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def api_provider_delete(request, provider_id):
    """Delete API provider"""
    try:
        from .api_management import APIProvider
        
        provider = APIProvider.objects.get(id=provider_id)
        
        # Don't delete if it's the only active provider
        active_providers = APIProvider.objects.filter(is_active=True).count()
        if provider.is_active and active_providers <= 1:
            return Response(
                {'error': 'Cannot delete the only active provider'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        provider_name = provider.display_name
        provider.delete()
        
        return Response({
            'message': f'Provider {provider_name} deleted successfully'
        })
        
    except APIProvider.DoesNotExist:
        return Response(
            {'error': 'Provider not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f'Error deleting API provider: {e}')
        return Response(
            {'error': 'Failed to delete provider'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def api_provider_test(request, provider_id):
    """Test API provider with sample request"""
    try:
        from .api_management import APIProvider, api_manager
        
        provider = APIProvider.objects.get(id=provider_id)
        endpoint = request.data.get('endpoint', 'weather')
        params = request.data.get('params', {})
        
        # Make test request
        result = api_manager.make_request(endpoint, params, provider)
        
        return Response({
            'success': result['success'],
            'provider': result['provider'],
            'response_time': result['response_time'],
            'data_sample': str(result['data'])[:500] + '...' if len(str(result['data'])) > 500 else result['data']
        })
        
    except APIProvider.DoesNotExist:
        return Response(
            {'error': 'Provider not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f'Error testing API provider: {e}')
        return Response(
            {'error': f'Test failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_dashboard_summary(request):
    """Get API management dashboard summary"""
    try:
        from .api_management import APIProvider, APIUsage, APIFailover
        
        # Get provider summary
        providers = APIProvider.objects.all()
        active_providers = providers.filter(is_active=True).count()
        healthy_providers = providers.filter(is_healthy=True).count()
        
        # Get today's usage
        today = timezone.now().date()
        today_usage = APIUsage.objects.filter(date=today).aggregate(
            total_requests=models.Sum('request_count'),
            total_cost=models.Sum('cost'),
            total_errors=models.Sum('error_count')
        )
        
        # Get recent failovers
        recent_failovers = APIFailover.objects.filter(
            failed_at__gte=timezone.now() - timedelta(hours=24)
        ).count()
        
        # Get top providers by usage
        top_providers = APIUsage.objects.filter(
            date__gte=timezone.now().date() - timedelta(days=7)
        ).values('provider__display_name').annotate(
            total_requests=models.Sum('request_count')
        ).order_by('-total_requests')[:5]
        
        summary = {
            'providers': {
                'total': providers.count(),
                'active': active_providers,
                'healthy': healthy_providers,
                'unhealthy': providers.filter(is_healthy=False).count()
            },
            'usage_today': {
                'total_requests': today_usage['total_requests'] or 0,
                'total_cost': float(today_usage['total_cost'] or 0),
                'total_errors': today_usage['total_errors'] or 0,
                'error_rate': (today_usage['total_errors'] or 0) / max(today_usage['total_requests'] or 1, 1) * 100
            },
            'failovers_24h': recent_failovers,
            'top_providers': list(top_providers),
            'timestamp': timezone.now().isoformat()
        }
        
        return Response(summary)
        
    except Exception as e:
        logger.error(f'Error getting API dashboard summary: {e}')
        return Response(
            {'error': 'Failed to retrieve dashboard summary'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def api_cost_analysis(request):
    """Get detailed API cost analysis"""
    try:
        from .api_management import api_manager
        
        days = int(request.GET.get('days', 30))
        cost_analysis = api_manager.get_cost_analysis(days)
        
        return Response(cost_analysis)
        
    except Exception as e:
        logger.error(f'Error getting cost analysis: {e}')
        return Response(
            {'error': 'Failed to retrieve cost analysis'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def api_system_health(request):
    """Get overall API system health status"""
    try:
        from .api_management import APIProvider, APIUsage, APIFailover
        
        providers = APIProvider.objects.filter(is_active=True)
        
        total_providers = providers.count()
        healthy_providers = providers.filter(is_healthy=True).count()
        
        # Recent failovers (last 24 hours)
        recent_failovers = APIFailover.objects.filter(
            failed_at__gte=timezone.now() - timedelta(hours=24)
        ).count()
        
        # Usage statistics for today
        today = timezone.now().date()
        today_usage = APIUsage.objects.filter(date=today).aggregate(
            total_requests=models.Sum('request_count'),
            total_errors=models.Sum('error_count'),
            total_cost=models.Sum('cost')
        )
        
        # Calculate health score
        health_score = 100
        if total_providers > 0:
            provider_health = (healthy_providers / total_providers) * 100
            health_score = min(health_score, provider_health)
        
        if today_usage['total_requests'] and today_usage['total_requests'] > 0:
            error_rate = (today_usage['total_errors'] or 0) / today_usage['total_requests']
            error_health = max(0, (1 - error_rate) * 100)
            health_score = min(health_score, error_health)
        
        # Determine overall status
        if health_score >= 95:
            status_text = 'Excellent'
            status_color = 'green'
        elif health_score >= 80:
            status_text = 'Good'
            status_color = 'green'
        elif health_score >= 60:
            status_text = 'Warning'
            status_color = 'orange'
        else:
            status_text = 'Critical'
            status_color = 'red'
        
        health_data = {
            'health_score': round(health_score, 1),
            'status': status_text,
            'status_color': status_color,
            'providers': {
                'total': total_providers,
                'healthy': healthy_providers,
                'unhealthy': total_providers - healthy_providers
            },
            'today_usage': {
                'requests': today_usage['total_requests'] or 0,
                'errors': today_usage['total_errors'] or 0,
                'cost': float(today_usage['total_cost'] or 0),
                'error_rate': (
                    (today_usage['total_errors'] or 0) / 
                    max(today_usage['total_requests'] or 1, 1)
                ) * 100
            },
            'recent_failovers': recent_failovers,
            'timestamp': timezone.now().isoformat()
        }
        
        return Response(health_data)
        
    except Exception as e:
        logger.error(f'Error getting system health: {e}')
        return Response(
            {'error': 'Failed to retrieve system health'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def api_failover_resolve(request, failover_id):
    """Mark a failover event as resolved"""
    try:
        from .api_management import APIFailover
        
        failover = APIFailover.objects.get(id=failover_id)
        
        if failover.resolved_at:
            return Response(
                {'error': 'Failover already resolved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        failover.resolved_at = timezone.now()
        failover.save()
        
        return Response({
            'message': 'Failover marked as resolved',
            'resolved_at': failover.resolved_at.isoformat()
        })
        
    except APIFailover.DoesNotExist:
        return Response(
            {'error': 'Failover event not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f'Error resolving failover: {e}')
        return Response(
            {'error': 'Failed to resolve failover'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def api_real_time_status(request):
    """Get real-time status of all API providers"""
    try:
        from .api_monitoring_realtime import real_time_monitor
        
        status_data = real_time_monitor.get_real_time_status()
        return Response(status_data)
        
    except Exception as e:
        logger.error(f'Error getting real-time status: {e}')
        return Response(
            {'error': 'Failed to get real-time status'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def api_latest_alerts(request):
    """Get latest system alerts"""
    try:
        from .api_monitoring_realtime import real_time_monitor
        
        limit = int(request.GET.get('limit', 10))
        alerts = real_time_monitor.get_latest_alerts(limit)
        
        return Response({
            'alerts': alerts,
            'count': len(alerts),
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f'Error getting latest alerts: {e}')
        return Response(
            {'error': 'Failed to get latest alerts'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def api_start_monitoring(request):
    """Start real-time API monitoring"""
    try:
        from .api_monitoring_realtime import real_time_monitor
        
        real_time_monitor.start_monitoring()
        
        return Response({
            'message': 'Real-time monitoring started',
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f'Error starting monitoring: {e}')
        return Response(
            {'error': 'Failed to start monitoring'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def api_bulk_health_check(request):
    """Perform health check on all active providers"""
    try:
        from .api_management import APIProvider, api_manager
        
        providers = APIProvider.objects.filter(is_active=True)
        results = []
        
        for provider in providers:
            try:
                health_result = api_manager.perform_health_check(provider)
                results.append({
                    'provider': provider.name,
                    'display_name': provider.display_name,
                    'healthy': health_result['healthy'],
                    'response_time': health_result.get('response_time', 0),
                    'error': health_result.get('error')
                })
            except Exception as e:
                results.append({
                    'provider': provider.name,
                    'display_name': provider.display_name,
                    'healthy': False,
                    'error': str(e)
                })
        
        return Response({
            'results': results,
            'total_checked': len(results),
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f'Error in bulk health check: {e}')
        return Response(
            {'error': 'Failed to perform bulk health check'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )