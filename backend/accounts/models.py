from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    """Extended user model with additional fields"""
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Profile fields
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Preferences
    preferred_units = models.CharField(
        max_length=10,
        choices=[('metric', 'Metric'), ('imperial', 'Imperial')],
        default='metric'
    )
    language = models.CharField(max_length=10, default='en')
    
    # Activity tracking
    last_activity = models.DateTimeField(null=True, blank=True)
    login_count = models.PositiveIntegerField(default=0)
    
    # Account status
    is_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # API access
    api_key = models.CharField(max_length=100, blank=True)
    api_requests_count = models.PositiveIntegerField(default=0)
    api_rate_limit = models.PositiveIntegerField(default=1000)  # requests per hour
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email
    
    def update_last_activity(self):
        """Update last activity timestamp"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])
    
    def increment_login_count(self):
        """Increment login counter"""
        self.login_count += 1
        self.save(update_fields=['login_count'])
    
    def is_active_recently(self, hours=24):
        """Check if user was active in the last N hours"""
        if not self.last_activity:
            return False
        return self.last_activity >= timezone.now() - timedelta(hours=hours)
    
    def get_api_usage_today(self):
        """Get API usage for today"""
        today = timezone.now().date()
        return UserAPIUsage.objects.filter(
            user=self,
            date=today
        ).aggregate(
            total_requests=models.Sum('request_count')
        )['total_requests'] or 0
    
    def can_make_api_request(self):
        """Check if user can make API request based on rate limit"""
        usage_today = self.get_api_usage_today()
        return usage_today < self.api_rate_limit


class UserRole(models.Model):
    """Custom user roles for fine-grained permissions"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'User Role'
        verbose_name_plural = 'User Roles'
    
    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """Extended user profile information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Dashboard preferences
    dashboard_layout = models.JSONField(default=dict, blank=True)
    favorite_cities = models.JSONField(default=list, blank=True)
    default_city = models.CharField(max_length=100, blank=True)
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)
    
    # Weather preferences
    show_air_quality = models.BooleanField(default=True)
    show_forecasts = models.BooleanField(default=True)
    forecast_days = models.PositiveIntegerField(default=5)
    
    # Privacy settings
    profile_visibility = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('private', 'Private'),
            ('friends', 'Friends Only')
        ],
        default='private'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.email} Profile"


class UserActivity(models.Model):
    """Track user activities for analytics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(
        max_length=50,
        choices=[
            ('login', 'Login'),
            ('logout', 'Logout'),
            ('api_request', 'API Request'),
            ('profile_update', 'Profile Update'),
            ('password_change', 'Password Change'),
            ('city_search', 'City Search'),
            ('weather_view', 'Weather View'),
            ('forecast_view', 'Forecast View'),
        ]
    )
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.email} - {self.activity_type} at {self.timestamp}"


class UserAPIUsage(models.Model):
    """Track API usage per user per day"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_usage')
    date = models.DateField()
    endpoint = models.CharField(max_length=200)
    request_count = models.PositiveIntegerField(default=0)
    success_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'API Usage'
        verbose_name_plural = 'API Usage Records'
        unique_together = ['user', 'date', 'endpoint']
    
    def __str__(self):
        return f"{self.user.email} - {self.endpoint} on {self.date}"


class UserSession(models.Model):
    """Track user sessions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    location = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.user.email} - {self.session_key[:8]}..."
    
    def is_expired(self, hours=24):
        """Check if session is expired"""
        return self.last_activity < timezone.now() - timedelta(hours=hours)


# Signal handlers to create profiles automatically
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create user profile when user is created"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save user profile when user is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()