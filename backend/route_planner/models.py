from django.db import models
from django.contrib.auth import get_user_model
from weather_data.models import City

User = get_user_model()


class Route(models.Model):
    """Model for saved routes"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='routes')
    name = models.CharField(max_length=200, help_text="User-defined name for the route")
    start_location = models.CharField(max_length=200, help_text="Starting location")
    end_location = models.CharField(max_length=200, help_text="Destination location")
    start_latitude = models.FloatField()
    start_longitude = models.FloatField()
    end_latitude = models.FloatField()
    end_longitude = models.FloatField()
    waypoints = models.JSONField(default=list, help_text="List of waypoints with lat/lon coordinates")
    distance_km = models.FloatField(null=True, blank=True, help_text="Total route distance in kilometers")
    estimated_duration_minutes = models.IntegerField(null=True, blank=True, help_text="Estimated travel time in minutes")
    # Hazard scoring
    hazard_score = models.FloatField(null=True, blank=True, help_text="Overall route hazard score (0-100)")
    risk_level = models.CharField(max_length=20, default='unknown', help_text="Overall risk level label")
    hazard_summary = models.JSONField(default=dict, blank=True, help_text="Aggregated alert counts and metrics")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.start_location} → {self.end_location})"


class RouteWeatherPoint(models.Model):
    """Model for weather data along a route"""
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='weather_points')
    latitude = models.FloatField()
    longitude = models.FloatField()
    location_name = models.CharField(max_length=200, blank=True)
    distance_from_start_km = models.FloatField(help_text="Distance from route start in kilometers")
    temperature = models.FloatField(help_text="Temperature in Celsius")
    humidity = models.IntegerField(help_text="Humidity percentage")
    wind_speed = models.FloatField(help_text="Wind speed in km/h")
    weather_condition = models.CharField(max_length=50)
    weather_description = models.CharField(max_length=100)
    weather_icon = models.CharField(max_length=10)
    precipitation_probability = models.FloatField(default=0, help_text="Precipitation probability (0-1)")
    visibility = models.FloatField(null=True, blank=True, help_text="Visibility in km")
    # Hazard scoring
    hazard_score = models.FloatField(null=True, blank=True, help_text="Point hazard score (0-100)")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['distance_from_start_km']

    def __str__(self):
        return f"{self.route.name} - {self.distance_from_start_km}km - {self.temperature}°C"


class RouteAlert(models.Model):
    """Model for route-specific weather alerts"""
    ALERT_TYPES = [
        ('rain', 'Rain'),
        ('snow', 'Snow'),
        ('fog', 'Fog'),
        ('wind', 'High Wind'),
        ('temperature', 'Extreme Temperature'),
        ('storm', 'Storm'),
        ('ice', 'Ice/Freezing'),
    ]

    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('severe', 'Severe'),
    ]

    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='medium')
    location_latitude = models.FloatField()
    location_longitude = models.FloatField()
    location_name = models.CharField(max_length=200, blank=True)
    distance_from_start_km = models.FloatField()
    message = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['distance_from_start_km', '-created_at']

    def __str__(self):
        return f"{self.route.name} - {self.alert_type} alert at {self.distance_from_start_km}km"


class TravelPlan(models.Model):
    """Model for travel plans with weather considerations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='travel_plans')
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='travel_plans')
    planned_departure = models.DateTimeField()
    planned_arrival = models.DateTimeField()
    vehicle_type = models.CharField(max_length=50, default='car', help_text="Type of vehicle (car, motorcycle, bicycle, walking)")
    weather_preferences = models.JSONField(default=dict, help_text="User preferences for weather conditions")
    alternative_routes = models.JSONField(default=list, help_text="Alternative route suggestions")
    weather_warnings = models.JSONField(default=list, help_text="Weather-related warnings for the journey")
    recommended_departure_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Travel plan for {self.route.name} on {self.planned_departure.date()}"
