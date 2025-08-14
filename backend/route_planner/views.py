from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .models import Route, RouteWeatherPoint, RouteAlert, TravelPlan
from .serializers import (
    RouteSerializer, RouteWeatherPointSerializer, RouteAlertSerializer,
    TravelPlanSerializer, RouteWithWeatherSerializer
)
from django.conf import settings
import requests
import math
from datetime import datetime, timedelta, timezone


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def get_route_from_osrm(start_lat, start_lon, end_lat, end_lon):
    """Get route from OSRM (Open Source Routing Machine) API"""
    url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data.get('code') == 'Ok' and data.get('routes'):
            route = data['routes'][0]
            coordinates = route['geometry']['coordinates']
            distance = route['distance'] / 1000  # Convert to km
            duration = route['duration'] / 60  # Convert to minutes
            
            # Convert coordinates to lat/lon format
            waypoints = [[coord[1], coord[0]] for coord in coordinates]
            
            return {
                'waypoints': waypoints,
                'distance_km': distance,
                'duration_minutes': duration
            }
    except Exception as e:
        print(f"Error fetching route from OSRM: {e}")
    
    return None


def get_weather_along_route(route_waypoints, num_points=10):
    """Get weather data for points along the route"""
    weather_points = []
    total_distance = 0
    
    # Calculate total distance
    for i in range(len(route_waypoints) - 1):
        lat1, lon1 = route_waypoints[i]
        lat2, lon2 = route_waypoints[i + 1]
        total_distance += calculate_distance(lat1, lon1, lat2, lon2)
    
    # Select evenly spaced points along the route
    interval = max(1, len(route_waypoints) // num_points)
    selected_points = route_waypoints[::interval]
    
    # Ensure we include the end point
    if route_waypoints[-1] not in selected_points:
        selected_points.append(route_waypoints[-1])
    
    distance_so_far = 0
    
    for i, (lat, lon) in enumerate(selected_points):
        if i > 0:
            prev_lat, prev_lon = selected_points[i-1]
            distance_so_far += calculate_distance(prev_lat, prev_lon, lat, lon)
        
        # Fetch weather data for this point
        weather_data = fetch_weather_for_point(lat, lon)
        if weather_data:
            weather_points.append({
                'latitude': lat,
                'longitude': lon,
                'distance_from_start_km': distance_so_far,
                'weather_data': weather_data
            })
    
    return weather_points


def fetch_weather_for_point(lat, lon):
    """Fetch weather data for a specific point"""
    url = f"{settings.OPENWEATHER_BASE_URL}/weather?lat={lat}&lon={lon}&appid={settings.OPENWEATHER_API_KEY}&units=metric"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data.get('cod') == 200:
            return {
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'wind_speed': data['wind']['speed'],
                'weather_condition': data['weather'][0]['main'],
                'weather_description': data['weather'][0]['description'],
                'weather_icon': data['weather'][0]['icon'],
                'precipitation_probability': 0,  # Not available in current weather
                'visibility': data.get('visibility', 0) / 1000 if data.get('visibility') else None  # Convert to km
            }
    except Exception as e:
        print(f"Error fetching weather for point ({lat}, {lon}): {e}")
    
    return None


def analyze_route_weather_conditions(weather_points):
    """Analyze weather conditions along the route and generate alerts"""
    alerts = []
    
    for point in weather_points:
        weather = point['weather_data']
        lat, lon = point['latitude'], point['longitude']
        distance = point['distance_from_start_km']
        
        # Check for various weather conditions that might affect travel
        if weather['temperature'] < 0:
            alerts.append({
                'alert_type': 'ice',
                'severity': 'high',
                'location_latitude': lat,
                'location_longitude': lon,
                'distance_from_start_km': distance,
                'message': f"Freezing temperature ({weather['temperature']}°C) detected. Risk of ice on roads."
            })
        
        if weather['temperature'] > 35:
            alerts.append({
                'alert_type': 'temperature',
                'severity': 'medium',
                'location_latitude': lat,
                'location_longitude': lon,
                'distance_from_start_km': distance,
                'message': f"High temperature ({weather['temperature']}°C) detected. Stay hydrated and check vehicle cooling."
            })
        
        if weather['wind_speed'] > 50:  # km/h
            alerts.append({
                'alert_type': 'wind',
                'severity': 'high',
                'location_latitude': lat,
                'location_longitude': lon,
                'distance_from_start_km': distance,
                'message': f"High wind speed ({weather['wind_speed']} km/h) detected. Drive carefully."
            })
        
        if weather['visibility'] and weather['visibility'] < 1:  # Less than 1 km
            alerts.append({
                'alert_type': 'fog',
                'severity': 'high',
                'location_latitude': lat,
                'location_longitude': lon,
                'distance_from_start_km': distance,
                'message': f"Low visibility ({weather['visibility']} km) detected. Reduce speed and use fog lights."
            })
        
        if 'rain' in weather['weather_condition'].lower() or 'drizzle' in weather['weather_condition'].lower():
            alerts.append({
                'alert_type': 'rain',
                'severity': 'medium',
                'location_latitude': lat,
                'location_longitude': lon,
                'distance_from_start_km': distance,
                'message': f"Rain detected ({weather['weather_description']}). Reduce speed and increase following distance."
            })
        
        if 'snow' in weather['weather_condition'].lower():
            alerts.append({
                'alert_type': 'snow',
                'severity': 'high',
                'location_latitude': lat,
                'location_longitude': lon,
                'distance_from_start_km': distance,
                'message': f"Snow detected ({weather['weather_description']}). Use winter tires and drive slowly."
            })
        
        if 'storm' in weather['weather_condition'].lower() or 'thunderstorm' in weather['weather_condition'].lower():
            alerts.append({
                'alert_type': 'storm',
                'severity': 'severe',
                'location_latitude': lat,
                'location_longitude': lon,
                'distance_from_start_km': distance,
                'message': f"Storm detected ({weather['weather_description']}). Consider delaying travel."
            })
    
    return alerts


# API Views
class RouteListCreateView(generics.ListCreateAPIView):
    serializer_class = RouteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Route.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RouteDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RouteWithWeatherSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Route.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_route_with_weather(request):
    """Create a route and fetch weather data along it"""
    start_location = request.data.get('start_location')
    end_location = request.data.get('end_location')
    start_lat = request.data.get('start_latitude')
    start_lon = request.data.get('start_longitude')
    end_lat = request.data.get('end_latitude')
    end_lon = request.data.get('end_longitude')
    route_name = request.data.get('name', f"{start_location} to {end_location}")

    if not all([start_location, end_location, start_lat, start_lon, end_lat, end_lon]):
        return Response({'error': 'Missing required route parameters'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Get route from OSRM
        route_data = get_route_from_osrm(start_lat, start_lon, end_lat, end_lon)
        if not route_data:
            return Response({'error': 'Could not calculate route'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Create route object
        route = Route.objects.create(
            user=request.user,
            name=route_name,
            start_location=start_location,
            end_location=end_location,
            start_latitude=start_lat,
            start_longitude=start_lon,
            end_latitude=end_lat,
            end_longitude=end_lon,
            waypoints=route_data['waypoints'],
            distance_km=route_data['distance_km'],
            estimated_duration_minutes=route_data['duration_minutes']
        )

        # Get weather data along the route
        weather_points = get_weather_along_route(route_data['waypoints'])
        
        # Create weather point objects
        for point in weather_points:
            weather = point['weather_data']
            RouteWeatherPoint.objects.create(
                route=route,
                latitude=point['latitude'],
                longitude=point['longitude'],
                distance_from_start_km=point['distance_from_start_km'],
                temperature=weather['temperature'],
                humidity=weather['humidity'],
                wind_speed=weather['wind_speed'],
                weather_condition=weather['weather_condition'],
                weather_description=weather['weather_description'],
                weather_icon=weather['weather_icon'],
                precipitation_probability=weather['precipitation_probability'],
                visibility=weather['visibility']
            )

        # Analyze weather conditions and create alerts
        alerts = analyze_route_weather_conditions(weather_points)
        for alert_data in alerts:
            RouteAlert.objects.create(
                route=route,
                **alert_data
            )

        # Return the created route with weather data
        serializer = RouteWithWeatherSerializer(route)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': f'Error creating route: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_route_weather(request, route_id):
    """Get current weather data for a specific route"""
    try:
        route = Route.objects.get(id=route_id, user=request.user)
    except Route.DoesNotExist:
        return Response({'error': 'Route not found'}, status=status.HTTP_404_NOT_FOUND)

    # Get fresh weather data along the route
    weather_points = get_weather_along_route(route.waypoints)
    
    # Update weather point objects
    RouteWeatherPoint.objects.filter(route=route).delete()  # Clear old data
    for point in weather_points:
        weather = point['weather_data']
        RouteWeatherPoint.objects.create(
            route=route,
            latitude=point['latitude'],
            longitude=point['longitude'],
            distance_from_start_km=point['distance_from_start_km'],
            temperature=weather['temperature'],
            humidity=weather['humidity'],
            wind_speed=weather['wind_speed'],
            weather_condition=weather['weather_condition'],
            weather_description=weather['weather_description'],
            weather_icon=weather['weather_icon'],
            precipitation_probability=weather['precipitation_probability'],
            visibility=weather['visibility']
        )

    # Update alerts
    RouteAlert.objects.filter(route=route).delete()  # Clear old alerts
    alerts = analyze_route_weather_conditions(weather_points)
    for alert_data in alerts:
        RouteAlert.objects.create(
            route=route,
            **alert_data
        )

    serializer = RouteWithWeatherSerializer(route)
    return Response(serializer.data)


class TravelPlanListCreateView(generics.ListCreateAPIView):
    serializer_class = TravelPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TravelPlan.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TravelPlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TravelPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TravelPlan.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def geocode_location(request):
    """Geocode a location name to get latitude and longitude"""
    location = request.data.get('location')
    if not location:
        return Response({'error': 'Location parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

    url = f"{settings.OPENWEATHER_BASE_URL}/weather?q={location}&appid={settings.OPENWEATHER_API_KEY}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data.get('cod') == 200:
            return Response({
                'location': location,
                'latitude': data['coord']['lat'],
                'longitude': data['coord']['lon'],
                'country': data['sys']['country']
            })
        else:
            return Response({'error': 'Location not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'Geocoding error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
