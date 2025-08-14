# Push Notification API Views for Weather247
import logging
from typing import Dict

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .push_notifications import PushNotificationService, PushSubscription

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class PushSubscriptionView(View):
    """Handle push notification subscription management"""
    
    def post(self, request):
        """Create or update a push subscription"""
        try:
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            import json
            data = json.loads(request.body)
            
            subscription_data = data.get('subscription')
            preferences = data.get('preferences', {})
            
            if not subscription_data:
                return JsonResponse({'error': 'Subscription data required'}, status=400)
            
            # Create subscription
            subscription = PushNotificationService.create_subscription(
                user=request.user,
                subscription_data={
                    'subscription': subscription_data,
                    'user_agent': data.get('user_agent', ''),
                    'timezone': data.get('timezone', 'UTC')
                },
                preferences=preferences
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Push subscription created successfully',
                'subscription_id': subscription.id,
                'preferences': {
                    'weather_alerts': subscription.weather_alerts,
                    'severe_weather_alerts': subscription.severe_weather_alerts,
                    'daily_forecast': subscription.daily_forecast,
                    'location_updates': subscription.location_updates,
                }
            })
            
        except Exception as e:
            logger.error(f"Failed to create push subscription: {e}")
            return JsonResponse({'error': 'Failed to create subscription'}, status=500)
    
    def delete(self, request):
        """Remove a push subscription"""
        try:
            import json
            data = json.loads(request.body)
            
            endpoint = data.get('endpoint')
            if not endpoint:
                return JsonResponse({'error': 'Endpoint required'}, status=400)
            
            success = PushNotificationService.remove_subscription(endpoint)
            
            if success:
                return JsonResponse({'success': True, 'message': 'Subscription removed'})
            else:
                return JsonResponse({'error': 'Subscription not found'}, status=404)
                
        except Exception as e:
            logger.error(f"Failed to remove push subscription: {e}")
            return JsonResponse({'error': 'Failed to remove subscription'}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_subscription(request):
    """Verify if a push subscription is still valid"""
    try:
        endpoint = request.data.get('endpoint')
        if not endpoint:
            return Response({'error': 'Endpoint required'}, status=status.HTTP_400_BAD_REQUEST)
        
        is_valid = PushNotificationService.verify_subscription(endpoint)
        
        return Response({
            'valid': is_valid,
            'message': 'Subscription is valid' if is_valid else 'Subscription not found or inactive'
        })
        
    except Exception as e:
        logger.error(f"Failed to verify subscription: {e}")
        return Response({'error': 'Verification failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_preferences(request):
    """Update notification preferences for a subscription"""
    try:
        endpoint = request.data.get('endpoint')
        preferences = request.data.get('preferences', {})
        
        if not endpoint:
            return Response({'error': 'Endpoint required'}, status=status.HTTP_400_BAD_REQUEST)
        
        success = PushNotificationService.update_preferences(endpoint, preferences)
        
        if success:
            return Response({
                'success': True,
                'message': 'Preferences updated successfully',
                'preferences': preferences
            })
        else:
            return Response({'error': 'Subscription not found'}, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        logger.error(f"Failed to update preferences: {e}")
        return Response({'error': 'Failed to update preferences'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_test_notification(request):
    """Send a test notification to verify the subscription works"""
    try:
        endpoint = request.data.get('endpoint')
        if not endpoint:
            return Response({'error': 'Endpoint required'}, status=status.HTTP_400_BAD_REQUEST)
        
        success = PushNotificationService.send_test_notification(endpoint)
        
        if success:
            return Response({
                'success': True,
                'message': 'Test notification sent successfully'
            })
        else:
            return Response({'error': 'Failed to send test notification'}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Failed to send test notification: {e}")
        return Response({'error': 'Failed to send test notification'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_status(request):
    """Get user's push subscription status and preferences"""
    try:
        subscriptions = PushSubscription.objects.filter(
            user=request.user,
            is_active=True
        ).values(
            'id', 'endpoint', 'created_at', 'last_used',
            'weather_alerts', 'severe_weather_alerts',
            'daily_forecast', 'location_updates'
        )
        
        return Response({
            'subscriptions': list(subscriptions),
            'total_subscriptions': len(subscriptions),
            'has_active_subscription': len(subscriptions) > 0
        })
        
    except Exception as e:
        logger.error(f"Failed to get subscription status: {e}")
        return Response({'error': 'Failed to get subscription status'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_weather_alert(request):
    """Send weather alert to users (admin only)"""
    try:
        if not request.user.is_staff:
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
        
        alert_data = request.data.get('alert_data', {})
        user_ids = request.data.get('user_ids', [])
        severity = request.data.get('severity', 'moderate')
        
        if not alert_data or not user_ids:
            return Response({'error': 'Alert data and user IDs required'}, status=status.HTTP_400_BAD_REQUEST)
        
        from django.contrib.auth.models import User
        users = User.objects.filter(id__in=user_ids)
        
        sent_count = PushNotificationService.send_weather_alert(users, alert_data, severity)
        
        return Response({
            'success': True,
            'message': f'Weather alert sent to {sent_count} subscriptions',
            'sent_count': sent_count
        })
        
    except Exception as e:
        logger.error(f"Failed to send weather alert: {e}")
        return Response({'error': 'Failed to send weather alert'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_daily_forecast(request):
    """Send daily forecast to users (admin only)"""
    try:
        if not request.user.is_staff:
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
        
        forecast_data = request.data.get('forecast_data', {})
        user_ids = request.data.get('user_ids', [])
        
        if not forecast_data or not user_ids:
            return Response({'error': 'Forecast data and user IDs required'}, status=status.HTTP_400_BAD_REQUEST)
        
        from django.contrib.auth.models import User
        users = User.objects.filter(id__in=user_ids)
        
        sent_count = PushNotificationService.send_daily_forecast(users, forecast_data)
        
        return Response({
            'success': True,
            'message': f'Daily forecast sent to {sent_count} subscriptions',
            'sent_count': sent_count
        })
        
    except Exception as e:
        logger.error(f"Failed to send daily forecast: {e}")
        return Response({'error': 'Failed to send daily forecast'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_stats(request):
    """Get push notification statistics (admin only)"""
    try:
        if not request.user.is_staff:
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
        
        stats = PushNotificationService.get_subscription_stats()
        
        return Response({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Failed to get subscription stats: {e}")
        return Response({'error': 'Failed to get subscription stats'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cleanup_subscriptions(request):
    """Cleanup expired subscriptions (admin only)"""
    try:
        if not request.user.is_staff:
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
        
        cleaned_count = PushNotificationService.cleanup_expired_subscriptions()
        
        return Response({
            'success': True,
            'message': f'Cleaned up {cleaned_count} expired subscriptions',
            'cleaned_count': cleaned_count
        })
        
    except Exception as e:
        logger.error(f"Failed to cleanup subscriptions: {e}")
        return Response({'error': 'Failed to cleanup subscriptions'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Legacy function-based views for compatibility
@require_http_methods(["POST", "DELETE"])
@login_required
def push_subscription_legacy(request):
    """Legacy endpoint for push subscription management"""
    view = PushSubscriptionView()
    return view.dispatch(request)