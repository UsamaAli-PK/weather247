from django.db import models
from django.contrib.auth import get_user_model
import json

User = get_user_model()


class City(models.Model):
    """Model for cities with weather data"""
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    timezone = models.CharField(max_length=50, default='UTC')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['name', 'country']
        verbose_name_plural = 'Cities'

    def __str__(self):
        return f"{self.name}, {self.country}"


class WeatherData(models.Model):
    """Model for current weather data"""
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='weather_data')
    temperature = models.FloatField(help_text="Temperature in Celsius")
    feels_like = models.FloatField(help_text="Feels like temperature in Celsius")
    humidity = models.IntegerField(help_text="Humidity percentage")
    pressure = models.FloatField(help_text="Atmospheric pressure in hPa")
    visibility = models.FloatField(null=True, blank=True, help_text="Visibility in km")
    uv_index = models.FloatField(null=True, blank=True, help_text="UV index")
    wind_speed = models.FloatField(help_text="Wind speed in km/h")
    wind_direction = models.IntegerField(help_text="Wind direction in degrees")
    weather_condition = models.CharField(max_length=50, help_text="Main weather condition")
    weather_description = models.CharField(max_length=100, help_text="Weather description")
    weather_icon = models.CharField(max_length=10, help_text="Weather icon code")
    cloudiness = models.IntegerField(help_text="Cloudiness percentage")
    sunrise = models.DateTimeField(null=True, blank=True)
    sunset = models.DateTimeField(null=True, blank=True)
    data_source = models.CharField(max_length=50, default='openweathermap')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.city.name} - {self.temperature}°C - {self.timestamp}"


class AirQualityData(models.Model):
    """Model for air quality data"""
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='air_quality_data')
    aqi = models.IntegerField(help_text="Air Quality Index")
    co = models.FloatField(help_text="Carbon monoxide (μg/m³)")
    no = models.FloatField(help_text="Nitrogen monoxide (μg/m³)")
    no2 = models.FloatField(help_text="Nitrogen dioxide (μg/m³)")
    o3 = models.FloatField(help_text="Ozone (μg/m³)")
    so2 = models.FloatField(help_text="Sulphur dioxide (μg/m³)")
    pm2_5 = models.FloatField(help_text="Fine particles matter (μg/m³)")
    pm10 = models.FloatField(help_text="Coarse particulate matter (μg/m³)")
    nh3 = models.FloatField(help_text="Ammonia (μg/m³)")
    data_source = models.CharField(max_length=50, default='openweathermap')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.city.name} - AQI: {self.aqi} - {self.timestamp}"


class WeatherForecast(models.Model):
    """Model for weather forecast data"""
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='forecasts')
    forecast_date = models.DateTimeField()
    temperature_min = models.FloatField(help_text="Minimum temperature in Celsius")
    temperature_max = models.FloatField(help_text="Maximum temperature in Celsius")
    temperature_avg = models.FloatField(help_text="Average temperature in Celsius")
    humidity = models.IntegerField(help_text="Humidity percentage")
    pressure = models.FloatField(help_text="Atmospheric pressure in hPa")
    wind_speed = models.FloatField(help_text="Wind speed in km/h")
    wind_direction = models.IntegerField(help_text="Wind direction in degrees")
    weather_condition = models.CharField(max_length=50)
    weather_description = models.CharField(max_length=100)
    weather_icon = models.CharField(max_length=10)
    cloudiness = models.IntegerField(help_text="Cloudiness percentage")
    precipitation_probability = models.FloatField(default=0, help_text="Precipitation probability (0-1)")
    precipitation_amount = models.FloatField(default=0, help_text="Precipitation amount in mm")
    data_source = models.CharField(max_length=50, default='openweathermap')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['forecast_date']
        unique_together = ['city', 'forecast_date', 'data_source']

    def __str__(self):
        return f"{self.city.name} - {self.forecast_date.date()} - {self.temperature_avg}°C"


class HistoricalWeatherData(models.Model):
    """Model for historical weather data"""
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='historical_data')
    date = models.DateField()
    temperature_min = models.FloatField(help_text="Minimum temperature in Celsius")
    temperature_max = models.FloatField(help_text="Maximum temperature in Celsius")
    temperature_avg = models.FloatField(help_text="Average temperature in Celsius")
    humidity_avg = models.IntegerField(help_text="Average humidity percentage")
    pressure_avg = models.FloatField(help_text="Average atmospheric pressure in hPa")
    wind_speed_avg = models.FloatField(help_text="Average wind speed in km/h")
    precipitation_total = models.FloatField(default=0, help_text="Total precipitation in mm")
    weather_condition = models.CharField(max_length=50)
    data_source = models.CharField(max_length=50, default='openweathermap')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['city', 'date', 'data_source']

    def __str__(self):
        return f"{self.city.name} - {self.date} - {self.temperature_avg}°C"


class WeatherPrediction(models.Model):
    """Model for AI-generated weather predictions"""
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='predictions')
    prediction_date = models.DateTimeField()
    predicted_temperature = models.FloatField(help_text="Predicted temperature in Celsius")
    predicted_humidity = models.IntegerField(help_text="Predicted humidity percentage")
    predicted_pressure = models.FloatField(help_text="Predicted pressure in hPa")
    predicted_wind_speed = models.FloatField(help_text="Predicted wind speed in km/h")
    predicted_condition = models.CharField(max_length=50, help_text="Predicted weather condition")
    confidence_score = models.FloatField(help_text="Prediction confidence (0-1)")
    model_version = models.CharField(max_length=20, default='v1.0')
    features_used = models.JSONField(default=dict, help_text="Features used for prediction")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['prediction_date']
        unique_together = ['city', 'prediction_date', 'model_version']

    def __str__(self):
        return f"{self.city.name} - {self.prediction_date} - {self.predicted_temperature}°C (AI)"


class UserWeatherPreference(models.Model):
    """Model for user weather preferences and favorite cities"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weather_preferences')
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    is_favorite = models.BooleanField(default=False)
    alert_enabled = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Display order for user's cities")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'city']
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.user.email} - {self.city.name}"


class PushSubscription(models.Model):
    """Model to store push notification subscriptions"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.URLField(unique=True)
    p256dh_key = models.TextField()
    auth_key = models.TextField()
    user_agent = models.TextField(blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Notification preferences
    weather_alerts = models.BooleanField(default=True)
    severe_weather_alerts = models.BooleanField(default=True)
    daily_forecast = models.BooleanField(default=False)
    location_updates = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'push_subscriptions'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['endpoint']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Push subscription for {self.user.username}"
    
    @property
    def subscription_info(self):
        """Get subscription info in the format expected by pywebpush"""
        return {
            "endpoint": self.endpoint,
            "keys": {
                "p256dh": self.p256dh_key,
                "auth": self.auth_key
            }
        }
    
    def send_notification(self, title: str, body: str, data: dict = None, **kwargs):
        """Send a push notification to this subscription"""
        from .push_notifications import PushNotificationService
        return PushNotificationService.send_notification(
            subscription=self,
            title=title,
            body=body,
            data=data,
            **kwargs
        )
    
    def is_expired(self) -> bool:
        """Check if subscription might be expired (no activity for 30 days)"""
        from django.utils import timezone
        return (timezone.now() - self.last_used).days > 30


class NotificationLog(models.Model):
    """Log of sent notifications for analytics and debugging"""
    
    NOTIFICATION_TYPES = [
        ('weather_alert', 'Weather Alert'),
        ('severe_weather', 'Severe Weather Alert'),
        ('daily_forecast', 'Daily Forecast'),
        ('location_update', 'Location Update'),
        ('system', 'System Notification'),
        ('test', 'Test Notification'),
    ]
    
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('expired', 'Expired Subscription'),
        ('disabled', 'Notifications Disabled'),
    ]
    
    subscription = models.ForeignKey(PushSubscription, on_delete=models.CASCADE, related_name='notification_logs')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    body = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notification_logs'
        indexes = [
            models.Index(fields=['subscription', 'created_at']),
            models.Index(fields=['notification_type', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} - {self.status} - {self.created_at}"


class SystemMetrics(models.Model):
    """Model for storing system performance metrics"""
    
    METRIC_TYPES = [
        ('cpu_usage', 'CPU Usage'),
        ('memory_usage', 'Memory Usage'),
        ('disk_usage', 'Disk Usage'),
        ('database_connections', 'Database Connections'),
        ('cache_hit_rate', 'Cache Hit Rate'),
        ('response_time', 'Response Time'),
        ('error_rate', 'Error Rate'),
        ('active_users', 'Active Users'),
        ('api_requests', 'API Requests'),
        ('queue_size', 'Queue Size'),
    ]
    
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPES)
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField()
    metric_unit = models.CharField(max_length=20, default='')
    component = models.CharField(max_length=50, default='system')  # system, database, cache, api, etc.
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'system_metrics'
        indexes = [
            models.Index(fields=['metric_type', 'timestamp']),
            models.Index(fields=['component', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.metric_name}: {self.metric_value}{self.metric_unit} at {self.timestamp}"


class SystemAlert(models.Model):
    """Model for system alerts and notifications"""
    
    ALERT_TYPES = [
        ('performance', 'Performance Issue'),
        ('error', 'System Error'),
        ('security', 'Security Alert'),
        ('capacity', 'Capacity Warning'),
        ('api_failure', 'API Failure'),
        ('database', 'Database Issue'),
        ('cache', 'Cache Issue'),
        ('disk_space', 'Disk Space Warning'),
        ('memory', 'Memory Warning'),
        ('custom', 'Custom Alert'),
    ]
    
    SEVERITY_LEVELS = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
        ('emergency', 'Emergency'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('suppressed', 'Suppressed'),
    ]
    
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    component = models.CharField(max_length=50)
    
    # Alert details
    metric_value = models.FloatField(null=True, blank=True)
    threshold_value = models.FloatField(null=True, blank=True)
    error_details = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # User who acknowledged/resolved
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='acknowledged_alerts')
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alerts')
    
    # Notification tracking
    notifications_sent = models.JSONField(default=list, blank=True)
    
    class Meta:
        db_table = 'system_alerts'
        indexes = [
            models.Index(fields=['status', 'severity']),
            models.Index(fields=['alert_type', 'created_at']),
            models.Index(fields=['component', 'status']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.severity.upper()}: {self.title}"
    
    def acknowledge(self, user=None):
        """Acknowledge the alert"""
        self.status = 'acknowledged'
        self.acknowledged_at = timezone.now()
        self.acknowledged_by = user
        self.save()
    
    def resolve(self, user=None):
        """Resolve the alert"""
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.save()


class SystemHealthCheck(models.Model):
    """Model for system health check results"""
    
    CHECK_TYPES = [
        ('database', 'Database Health'),
        ('cache', 'Cache Health'),
        ('api_endpoints', 'API Endpoints'),
        ('external_apis', 'External APIs'),
        ('disk_space', 'Disk Space'),
        ('memory', 'Memory Usage'),
        ('cpu', 'CPU Usage'),
        ('services', 'Background Services'),
        ('ssl_certificates', 'SSL Certificates'),
        ('custom', 'Custom Check'),
    ]
    
    STATUS_CHOICES = [
        ('healthy', 'Healthy'),
        ('warning', 'Warning'),
        ('unhealthy', 'Unhealthy'),
        ('unknown', 'Unknown'),
    ]
    
    check_type = models.CharField(max_length=30, choices=CHECK_TYPES)
    check_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    response_time = models.FloatField(null=True, blank=True, help_text="Response time in milliseconds")
    error_message = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'system_health_checks'
        indexes = [
            models.Index(fields=['check_type', 'timestamp']),
            models.Index(fields=['status', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.check_name}: {self.status} at {self.timestamp}"


class PerformanceBaseline(models.Model):
    """Model for storing performance baselines for comparison"""
    
    metric_type = models.CharField(max_length=50)
    component = models.CharField(max_length=50)
    
    # Baseline values
    baseline_value = models.FloatField()
    warning_threshold = models.FloatField()
    critical_threshold = models.FloatField()
    
    # Statistical data
    min_value = models.FloatField()
    max_value = models.FloatField()
    avg_value = models.FloatField()
    std_deviation = models.FloatField(default=0)
    
    # Metadata
    sample_size = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'performance_baselines'
        unique_together = ['metric_type', 'component']
        indexes = [
            models.Index(fields=['metric_type', 'component']),
            models.Index(fields=['last_updated']),
        ]
    
    def __str__(self):
        return f"{self.metric_type} baseline for {self.component}"
    
    def is_above_warning(self, value):
        """Check if value is above warning threshold"""
        return value > self.warning_threshold
    
    def is_above_critical(self, value):
        """Check if value is above critical threshold"""
        return value > self.critical_threshold
