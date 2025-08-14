"""
Utility functions for user management
"""
import uuid
import hashlib
from django.utils import timezone
from django.contrib.gis.geoip2 import GeoIP2
from django.contrib.gis.geoip2.base import GeoIP2Exception
from .models import UserActivity, UserAPIUsage


def generate_api_key():
    """Generate a unique API key for user"""
    return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:32]


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Get user agent from request"""
    return request.META.get('HTTP_USER_AGENT', '')


def get_location_from_ip(ip_address):
    """Get location from IP address using GeoIP2"""
    try:
        g = GeoIP2()
        location = g.city(ip_address)
        return f"{location['city']}, {location['country_name']}"
    except (GeoIP2Exception, Exception):
        return ''


def track_user_activity(user, activity_type, description='', request=None, metadata=None):
    """Track user activity"""
    try:
        activity_data = {
            'user': user,
            'activity_type': activity_type,
            'description': description,
            'metadata': metadata or {}
        }
        
        if request:
            activity_data.update({
                'ip_address': get_client_ip(request),
                'user_agent': get_user_agent(request)
            })
        
        UserActivity.objects.create(**activity_data)
    except Exception as e:
        # Don't let activity tracking break the main functionality
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error tracking user activity: {e}')


def track_api_usage(user, endpoint, success=True):
    """Track API usage for rate limiting and analytics"""
    try:
        today = timezone.now().date()
        
        usage, created = UserAPIUsage.objects.get_or_create(
            user=user,
            date=today,
            endpoint=endpoint,
            defaults={
                'request_count': 0,
                'success_count': 0,
                'error_count': 0
            }
        )
        
        usage.request_count += 1
        if success:
            usage.success_count += 1
        else:
            usage.error_count += 1
        
        usage.save()
        
        # Update user's total API request count
        user.api_requests_count += 1
        user.save(update_fields=['api_requests_count'])
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error tracking API usage: {e}')


def check_rate_limit(user, endpoint=None):
    """Check if user has exceeded rate limit"""
    try:
        if user.is_staff or user.is_superuser:
            return True  # No rate limit for staff
        
        return user.can_make_api_request()
    except Exception:
        return True  # Allow request if check fails


def get_user_permissions_summary(user):
    """Get summary of user permissions"""
    permissions = {
        'is_active': user.is_active,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'groups': list(user.groups.values_list('name', flat=True)),
        'user_permissions': list(user.user_permissions.values_list('codename', flat=True)),
        'can_access_admin': user.is_staff or user.is_superuser,
        'api_rate_limit': user.api_rate_limit,
        'api_usage_today': user.get_api_usage_today()
    }
    
    return permissions


def cleanup_expired_sessions():
    """Clean up expired user sessions"""
    from .models import UserSession
    from datetime import timedelta
    
    expired_time = timezone.now() - timedelta(hours=24)
    expired_sessions = UserSession.objects.filter(
        last_activity__lt=expired_time,
        is_active=True
    )
    
    count = expired_sessions.count()
    expired_sessions.update(is_active=False)
    
    return count


def get_user_dashboard_data(user):
    """Get dashboard data for user"""
    from .models import UserActivity, UserSession
    from datetime import timedelta
    
    now = timezone.now()
    last_7d = now - timedelta(days=7)
    
    # Recent activities
    recent_activities = UserActivity.objects.filter(
        user=user,
        timestamp__gte=last_7d
    ).order_by('-timestamp')[:10]
    
    # Active sessions
    active_sessions = UserSession.objects.filter(
        user=user,
        is_active=True
    ).count()
    
    # API usage this week
    api_usage_week = UserAPIUsage.objects.filter(
        user=user,
        date__gte=last_7d.date()
    ).aggregate(
        total_requests=models.Sum('request_count'),
        total_errors=models.Sum('error_count')
    )
    
    dashboard_data = {
        'user_info': {
            'full_name': user.get_full_name(),
            'email': user.email,
            'member_since': user.date_joined,
            'last_activity': user.last_activity,
            'login_count': user.login_count,
            'is_verified': user.is_verified
        },
        'activity_summary': {
            'recent_activities': recent_activities,
            'active_sessions': active_sessions,
            'api_requests_week': api_usage_week['total_requests'] or 0,
            'api_errors_week': api_usage_week['total_errors'] or 0
        },
        'preferences': {
            'preferred_units': user.preferred_units,
            'timezone': user.timezone,
            'language': user.language
        }
    }
    
    return dashboard_data