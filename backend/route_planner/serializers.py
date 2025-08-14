from rest_framework import serializers
from .models import Route, RouteWeatherPoint, RouteAlert, TravelPlan


class RouteSerializer(serializers.ModelSerializer):
    """Serializer for Route model"""
    class Meta:
        model = Route
        fields = (
            'id', 'user', 'name', 'start_location', 'end_location',
            'start_latitude', 'start_longitude', 'end_latitude', 'end_longitude',
            'waypoints', 'distance_km', 'estimated_duration_minutes',
            'created_at', 'updated_at'
        )
        read_only_fields = ('user', 'created_at', 'updated_at')


class RouteWeatherPointSerializer(serializers.ModelSerializer):
    """Serializer for RouteWeatherPoint model"""
    class Meta:
        model = RouteWeatherPoint
        fields = (
            'id', 'route', 'latitude', 'longitude', 'location_name',
            'distance_from_start_km', 'temperature', 'humidity', 'wind_speed',
            'weather_condition', 'weather_description', 'weather_icon',
            'precipitation_probability', 'visibility', 'timestamp'
        )
        read_only_fields = ('route', 'timestamp')


class RouteAlertSerializer(serializers.ModelSerializer):
    """Serializer for RouteAlert model"""
    class Meta:
        model = RouteAlert
        fields = (
            'id', 'route', 'alert_type', 'severity', 'location_latitude',
            'location_longitude', 'location_name', 'distance_from_start_km',
            'message', 'is_active', 'created_at'
        )
        read_only_fields = ('route', 'created_at')


class TravelPlanSerializer(serializers.ModelSerializer):
    """Serializer for TravelPlan model"""
    route = RouteSerializer(read_only=True)

    class Meta:
        model = TravelPlan
        fields = (
            'id', 'user', 'route', 'planned_departure', 'planned_arrival',
            'vehicle_type', 'weather_preferences', 'alternative_routes',
            'weather_warnings', 'recommended_departure_time',
            'created_at', 'updated_at'
        )
        read_only_fields = ('user', 'created_at', 'updated_at')


class RouteWithWeatherSerializer(serializers.ModelSerializer):
    """Serializer for Route with weather points"""
    weather_points = RouteWeatherPointSerializer(many=True, read_only=True)
    alerts = RouteAlertSerializer(many=True, read_only=True)

    class Meta:
        model = Route
        fields = (
            'id', 'user', 'name', 'start_location', 'end_location',
            'start_latitude', 'start_longitude', 'end_latitude', 'end_longitude',
            'waypoints', 'distance_km', 'estimated_duration_minutes',
            'weather_points', 'alerts', 'created_at', 'updated_at'
        )
        read_only_fields = ('user', 'created_at', 'updated_at')

