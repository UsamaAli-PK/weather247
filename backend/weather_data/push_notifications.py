# Push Notifications Service for Weather247 Backend
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
try:
	from pywebpush import webpush, WebPushException
except Exception:  # pragma: no cover
	webpush = None
	class WebPushException(Exception):
		pass

from .models import PushSubscription, NotificationLog

logger = logging.getLogger(__name__)


class PushNotificationService:
	"""Service class for managing push notifications"""
	
	@staticmethod
	def create_subscription(user: User, subscription_data: Dict, preferences: Dict = None) -> PushSubscription:
		"""Create or update a push subscription"""
		try:
			subscription_info = subscription_data.get('subscription', subscription_data)
			keys = subscription_info.get('keys', {})
			
			# Create or update subscription
			subscription, created = PushSubscription.objects.update_or_create(
				endpoint=subscription_info['endpoint'],
				defaults={
					'user': user,
					'p256dh_key': keys.get('p256dh', ''),
					'auth_key': keys.get('auth', ''),
					'user_agent': subscription_data.get('user_agent', ''),
					'timezone': subscription_data.get('timezone', 'UTC'),
					'is_active': True,
					'last_used': timezone.now(),
				}
			)
			
			# Update preferences if provided
			if preferences:
				for key, value in preferences.items():
					if hasattr(subscription, key):
						setattr(subscription, key, value)
				subscription.save()
			
			logger.info(f"Push subscription {'created' if created else 'updated'} for user {user.username}")
			return subscription
			
		except Exception as e:
			logger.error(f"Failed to create push subscription: {e}")
			raise
	
	@staticmethod
	def remove_subscription(endpoint: str) -> bool:
		"""Remove a push subscription"""
		try:
			subscription = PushSubscription.objects.get(endpoint=endpoint)
			subscription.delete()
			logger.info(f"Push subscription removed: {endpoint}")
			return True
		except PushSubscription.DoesNotExist:
			logger.warning(f"Push subscription not found: {endpoint}")
			return False
		except Exception as e:
			logger.error(f"Failed to remove push subscription: {e}")
			return False
	
	@staticmethod
	def verify_subscription(endpoint: str) -> bool:
		"""Verify if a subscription exists and is active"""
		try:
			subscription = PushSubscription.objects.get(endpoint=endpoint, is_active=True)
			subscription.last_used = timezone.now()
			subscription.save()
			return True
		except PushSubscription.DoesNotExist:
			return False
	
	@staticmethod
	def update_preferences(endpoint: str, preferences: Dict) -> bool:
		"""Update notification preferences for a subscription"""
		try:
			subscription = PushSubscription.objects.get(endpoint=endpoint, is_active=True)
			
			for key, value in preferences.items():
				if hasattr(subscription, key):
					setattr(subscription, key, value)
			
			subscription.save()
			logger.info(f"Preferences updated for subscription: {endpoint}")
			return True
			
		except PushSubscription.DoesNotExist:
			logger.warning(f"Subscription not found for preferences update: {endpoint}")
			return False
		except Exception as e:
			logger.error(f"Failed to update preferences: {e}")
			return False
	
	@staticmethod
	def send_notification(
		subscription: PushSubscription,
		title: str,
		body: str,
		data: Dict = None,
		notification_type: str = 'system',
		**kwargs
	) -> bool:
		"""Send a push notification to a specific subscription"""
		
		if not subscription.is_active:
			PushNotificationService._log_notification(
				subscription, notification_type, title, body, data, 'disabled'
			)
			return False
		
		try:
			# Prepare notification payload
			payload = {
				'title': title,
				'body': body,
				'icon': kwargs.get('icon', '/favicon.ico'),
				'badge': kwargs.get('badge', '/favicon.ico'),
				'tag': kwargs.get('tag', 'weather247'),
				'requireInteraction': kwargs.get('require_interaction', False),
				'silent': kwargs.get('silent', False),
				'vibrate': kwargs.get('vibrate', [100, 50, 100]),
				'data': data or {},
				'actions': kwargs.get('actions', [])
			}
			
			# Send notification using pywebpush
			webpush(
				subscription_info=subscription.subscription_info,
				data=json.dumps(payload),
				vapid_private_key=settings.VAPID_PRIVATE_KEY,
				vapid_claims={
					"sub": f"mailto:{settings.VAPID_ADMIN_EMAIL}"
				}
			)
			
			# Update last used timestamp
			subscription.last_used = timezone.now()
			subscription.save()
			
			# Log successful notification
			PushNotificationService._log_notification(
				subscription, notification_type, title, body, data, 'sent'
			)
			
			logger.info(f"Push notification sent to {subscription.user.username}: {title}")
			return True
			
		except WebPushException as e:
			error_msg = str(e)
			logger.error(f"WebPush error for {subscription.user.username}: {error_msg}")
			
			# Handle expired subscriptions
			if e.response and e.response.status_code in [410, 413]:
				subscription.is_active = False
				subscription.save()
				status = 'expired'
			else:
				status = 'failed'
			
			PushNotificationService._log_notification(
				subscription, notification_type, title, body, data, status, error_msg
			)
			return False
			
		except Exception as e:
			error_msg = str(e)
			logger.error(f"Failed to send push notification: {error_msg}")
			
			PushNotificationService._log_notification(
				subscription, notification_type, title, body, data, 'failed', error_msg
			)
			return False
	
	@staticmethod
	def send_to_user(
		user: User,
		title: str,
		body: str,
		data: Dict = None,
		notification_type: str = 'system',
		**kwargs
	) -> int:
		"""Send notification to all active subscriptions for a user"""
		subscriptions = PushSubscription.objects.filter(user=user, is_active=True)
		sent_count = 0
		
		for subscription in subscriptions:
			if PushNotificationService.send_notification(
				subscription, title, body, data, notification_type, **kwargs
			):
				sent_count += 1
		
		return sent_count
	
	@staticmethod
	def send_weather_alert(
		users: List[User],
		alert_data: Dict,
		severity: str = 'moderate'
	) -> int:
		"""Send weather alert to multiple users"""
		notification_type = 'severe_weather' if severity == 'severe' else 'weather_alert'
		sent_count = 0
		
		for user in users:
			# Get user's active subscriptions with weather alerts enabled
			subscriptions = PushSubscription.objects.filter(
				user=user,
				is_active=True
			)
			
			if notification_type == 'severe_weather':
				subscriptions = subscriptions.filter(severe_weather_alerts=True)
			else:
				subscriptions = subscriptions.filter(weather_alerts=True)
			
			for subscription in subscriptions:
				if PushNotificationService.send_notification(
					subscription=subscription,
					title=alert_data.get('title', 'Weather Alert'),
					body=alert_data.get('body', 'Weather conditions have changed'),
					data=alert_data,
					notification_type=notification_type,
					require_interaction=severity == 'severe',
					vibrate=[200, 100, 200] if severity == 'severe' else [100, 50, 100]
				):
					sent_count += 1
		
		return sent_count
	
	@staticmethod
	def send_daily_forecast(users: List[User], forecast_data: Dict) -> int:
		"""Send daily forecast notification to users who have it enabled"""
		sent_count = 0
		
		for user in users:
			subscriptions = PushSubscription.objects.filter(
				user=user,
				is_active=True,
				daily_forecast=True
			)
			
			for subscription in subscriptions:
				if PushNotificationService.send_notification(
					subscription=subscription,
					title=forecast_data.get('title', 'Daily Weather Forecast'),
					body=forecast_data.get('body', 'Your daily weather update is ready'),
					data=forecast_data,
					notification_type='daily_forecast'
				):
					sent_count += 1
		
		return sent_count
	
	@staticmethod
	def send_test_notification(endpoint: str) -> bool:
		"""Send a test notification to verify the subscription works"""
		try:
			subscription = PushSubscription.objects.get(endpoint=endpoint, is_active=True)
			
			return PushNotificationService.send_notification(
				subscription=subscription,
				title='Weather247 Test',
				body='This is a test notification. Your push notifications are working!',
				data={'test': True, 'timestamp': timezone.now().isoformat()},
				notification_type='test',
				tag='test-notification'
			)
			
		except PushSubscription.DoesNotExist:
			logger.warning(f"Subscription not found for test: {endpoint}")
			return False
	
	@staticmethod
	def cleanup_expired_subscriptions() -> int:
		"""Remove expired and inactive subscriptions"""
		expired_date = timezone.now() - timedelta(days=30)
		
		# Mark subscriptions as inactive if not used for 30 days
		expired_count = PushSubscription.objects.filter(
			last_used__lt=expired_date,
			is_active=True
		).update(is_active=False)
		
		# Delete very old inactive subscriptions (90 days)
		very_old_date = timezone.now() - timedelta(days=90)
		deleted_count = PushSubscription.objects.filter(
			last_used__lt=very_old_date,
			is_active=False
		).delete()[0]
		
		logger.info(f"Cleaned up push subscriptions: {expired_count} expired, {deleted_count} deleted")
		return expired_count + deleted_count
	
	@staticmethod
	def get_subscription_stats() -> Dict:
		"""Get statistics about push subscriptions"""
		total = PushSubscription.objects.count()
		active = PushSubscription.objects.filter(is_active=True).count()
		
		# Preferences stats
		weather_alerts = PushSubscription.objects.filter(is_active=True, weather_alerts=True).count()
		severe_alerts = PushSubscription.objects.filter(is_active=True, severe_weather_alerts=True).count()
		daily_forecast = PushSubscription.objects.filter(is_active=True, daily_forecast=True).count()
		
		# Recent activity
		recent_date = timezone.now() - timedelta(days=7)
		recent_activity = PushSubscription.objects.filter(last_used__gte=recent_date).count()
		
		return {
			'total_subscriptions': total,
			'active_subscriptions': active,
			'weather_alerts_enabled': weather_alerts,
			'severe_alerts_enabled': severe_alerts,
			'daily_forecast_enabled': daily_forecast,
			'recent_activity': recent_activity,
			'inactive_subscriptions': total - active
		}
	
	@staticmethod
	def _log_notification(
		subscription: PushSubscription,
		notification_type: str,
		title: str,
		body: str,
		data: Dict,
		status: str,
		error_message: str = ''
	):
		"""Log notification attempt"""
		try:
			NotificationLog.objects.create(
				subscription=subscription,
				notification_type=notification_type,
				title=title,
				body=body,
				data=data or {},
				status=status,
				error_message=error_message
			)
		except Exception as e:
			logger.error(f"Failed to log notification: {e}")


# Celery tasks for background notification sending
try:
	from celery import shared_task
	
	@shared_task
	def send_weather_alert_task(user_ids: List[int], alert_data: Dict, severity: str = 'moderate'):
		"""Celery task to send weather alerts in background"""
		from django.contrib.auth.models import User
		
		users = User.objects.filter(id__in=user_ids)
		sent_count = PushNotificationService.send_weather_alert(users, alert_data, severity)
		
		logger.info(f"Weather alert sent to {sent_count} subscriptions")
		return sent_count
	
	@shared_task
	def send_daily_forecast_task(user_ids: List[int], forecast_data: Dict):
		"""Celery task to send daily forecasts in background"""
		from django.contrib.auth.models import User
		
		users = User.objects.filter(id__in=user_ids)
		sent_count = PushNotificationService.send_daily_forecast(users, forecast_data)
		
		logger.info(f"Daily forecast sent to {sent_count} subscriptions")
		return sent_count
	
	@shared_task
	def cleanup_expired_subscriptions_task():
		"""Celery task to cleanup expired subscriptions"""
		cleaned_count = PushNotificationService.cleanup_expired_subscriptions()
		logger.info(f"Cleaned up {cleaned_count} expired push subscriptions")
		return cleaned_count

except ImportError:
	# Celery not available, tasks will run synchronously
	logger.warning("Celery not available, push notification tasks will run synchronously")
	pass