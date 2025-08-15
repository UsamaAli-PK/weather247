import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db import models
from accounts.models import User
# WeatherAlert now exists in weather_data.models
from .models import WeatherData, City, WeatherAlert
try:
	from celery import shared_task
except Exception:  # pragma: no cover
	def shared_task(func):
		return func
import requests
import json
from typing import List, Dict, Any, Optional

logger = logging.getLogger('weather247')


class WeatherAlertEngine:
	"""Intelligent weather alert system with ML optimization"""
	
	def __init__(self):
		self.alert_thresholds = {
			'temperature_high': 35.0,
			'temperature_low': -10.0,
			'wind_speed': 50.0,
			'precipitation': 10.0,
			'aqi': 4,
			'visibility': 1.0
		}
		self.severity_levels = {
			'low': 1,
			'medium': 2,
			'high': 3,
			'critical': 4,
			'emergency': 5
		}
	
	def evaluate_weather_conditions(self, weather_data: WeatherData) -> List[Dict[str, Any]]:
		"""Evaluate weather conditions and generate alerts"""
		alerts = []
		
		try:
			# Temperature alerts
			if weather_data.temperature >= self.alert_thresholds['temperature_high']:
				severity = 'critical' if weather_data.temperature >= 40 else 'high'
				alerts.append({
					'type': 'temperature_high',
					'severity': severity,
					'title': f'Extreme Heat Warning - {weather_data.city.name}',
					'message': f'Temperature has reached {weather_data.temperature}°C. Take precautions against heat-related illness.',
					'value': weather_data.temperature,
					'threshold': self.alert_thresholds['temperature_high']
				})
			
			elif weather_data.temperature <= self.alert_thresholds['temperature_low']:
				severity = 'critical' if weather_data.temperature <= -20 else 'high'
				alerts.append({
					'type': 'temperature_low',
					'severity': severity,
					'title': f'Extreme Cold Warning - {weather_data.city.name}',
					'message': f'Temperature has dropped to {weather_data.temperature}°C. Protect against frostbite and hypothermia.',
					'value': weather_data.temperature,
					'threshold': self.alert_thresholds['temperature_low']
				})
			
			# Wind speed alerts
			if weather_data.wind_speed >= self.alert_thresholds['wind_speed']:
				severity = 'emergency' if weather_data.wind_speed >= 80 else 'critical'
				alerts.append({
					'type': 'wind_speed',
					'severity': severity,
					'title': f'High Wind Alert - {weather_data.city.name}',
					'message': f'Wind speeds of {weather_data.wind_speed} km/h detected. Avoid outdoor activities and secure loose objects.',
					'value': weather_data.wind_speed,
					'threshold': self.alert_thresholds['wind_speed']
				})
			
			# Visibility alerts
			if weather_data.visibility <= self.alert_thresholds['visibility']:
				severity = 'critical' if weather_data.visibility <= 0.5 else 'high'
				alerts.append({
					'type': 'visibility',
					'severity': severity,
					'title': f'Low Visibility Alert - {weather_data.city.name}',
					'message': f'Visibility reduced to {weather_data.visibility} km. Exercise extreme caution when driving.',
					'value': weather_data.visibility,
					'threshold': self.alert_thresholds['visibility']
				})
			
			# Severe weather condition alerts
			severe_conditions = ['thunderstorm', 'tornado', 'hurricane', 'blizzard', 'hail']
			if any(condition in weather_data.weather_description.lower() for condition in severe_conditions):
				alerts.append({
					'type': 'severe_weather',
					'severity': 'emergency',
					'title': f'Severe Weather Alert - {weather_data.city.name}',
					'message': f'{weather_data.weather_description.title()} conditions detected. Seek immediate shelter.',
					'value': weather_data.weather_description,
					'threshold': 'severe_conditions'
				})
			
		except Exception as e:
			logger.error(f"Error evaluating weather conditions: {e}")
		
		return alerts
	
	def process_alerts_for_users(self, weather_data: WeatherData) -> int:
		"""Process and send alerts to relevant users"""
		alerts_sent = 0
		
		try:
			# Get potential alerts
			potential_alerts = self.evaluate_weather_conditions(weather_data)
			
			if not potential_alerts:
				return 0
			
			# Find users who should receive alerts for this city
			users_to_alert = User.objects.filter(
				profile__preferred_locations__contains=[weather_data.city.name]
			)
			
			for user in users_to_alert:
				for alert_data in potential_alerts:
					# Check if user wants this type of alert
					if self._should_send_alert(user, alert_data):
						alert = self._create_weather_alert(user, weather_data, alert_data)
						if self._send_alert_notification(user, alert):
							alerts_sent += 1
			
		except Exception as e:
			logger.error(f"Error processing alerts: {e}")
		
		return alerts_sent
	
	def _should_send_alert(self, user, alert_data) -> bool:
		"""Determine if alert should be sent to user based on preferences"""
		try:
			# Check if user has alerts enabled
			profile = getattr(user, 'profile', None)
			if not profile or not getattr(profile, 'receive_email_alerts', True):
				return False
			
			# Check quiet hours
			current_time = timezone.now().time()
			if hasattr(profile, 'quiet_hours_start') and hasattr(profile, 'quiet_hours_end'):
				if (profile.quiet_hours_start and profile.quiet_hours_end and
					profile.quiet_hours_start <= current_time <= profile.quiet_hours_end):
					# Only send emergency alerts during quiet hours
					return alert_data['severity'] == 'emergency'
			
			# Check if similar alert was sent recently (avoid spam)
			recent_alert = WeatherAlert.objects.filter(
				user=user,
				alert_type=alert_data['type'],
				created_at__gte=timezone.now() - timedelta(hours=2)
			).first()
			
			return recent_alert is None
			
		except Exception as e:
			logger.error(f"Error checking alert preferences: {e}")
			return False
	
	def _create_weather_alert(self, user, weather_data, alert_data):
		"""Create weather alert record"""
		try:
			alert = WeatherAlert.objects.create(
				user=user,
				city=weather_data.city,
				alert_type=alert_data['type'],
				severity=alert_data['severity'],
				title=alert_data['title'],
				message=alert_data['message'],
				weather_data={
					'temperature': getattr(weather_data, 'temperature', None),
					'humidity': getattr(weather_data, 'humidity', None),
					'wind_speed': getattr(weather_data, 'wind_speed', None),
					'weather_condition': getattr(weather_data, 'weather_condition', None),
					'timestamp': weather_data.timestamp.isoformat() if getattr(weather_data, 'timestamp', None) else None
				},
				is_emergency=alert_data['severity'] == 'emergency'
			)
			return alert
		except Exception as e:
			logger.error(f"Error creating weather alert: {e}")
			raise
	
	def _send_alert_notification(self, user, alert: WeatherAlert) -> bool:
		"""Send alert notification via email/SMS"""
		try:
			# Send email notification
			email_sent = self._send_email_alert(user, alert)
			
			# Send SMS if configured and it's high priority
			sms_sent = False
			if alert.severity in ['critical', 'emergency']:
				sms_sent = self._send_sms_alert(user, alert)
			
			# Update delivery status
			delivered_via = []
			if email_sent:
				delivered_via.append('email')
			if sms_sent:
				delivered_via.append('sms')
			
			alert.delivered_via = delivered_via
			alert.save(update_fields=['delivered_via'])
			
			return email_sent or sms_sent
			
		except Exception as e:
			logger.error(f"Error sending alert notification: {e}")
			return False
	
	def _send_email_alert(self, user, alert: WeatherAlert) -> bool:
		"""Send email alert"""
		try:
			subject = f"Weather247 Alert: {alert.title}"
			
			message = f"""
			Dear {user.first_name or user.username},
			
			{alert.message}
			
			Location: {alert.city.name}
			Severity: {alert.severity.upper()}
			Time: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}
			
			Current Conditions:
			- Temperature: {alert.weather_data.get('temperature', 'N/A')}°C
			- Humidity: {alert.weather_data.get('humidity', 'N/A')}%
			- Wind Speed: {alert.weather_data.get('wind_speed', 'N/A')} km/h
			- Condition: {alert.weather_data.get('weather_condition', 'N/A')}
			
			Stay safe!
			
			Weather247 Team
			"""
			
			send_mail(
				subject=subject,
				message=message,
				from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
				recipient_list=[user.email] if getattr(user, 'email', None) else [],
				fail_silently=True
			)
			
			logger.info(f"Email alert attempted for {getattr(user, 'email', 'unknown')} ({alert.city.name})")
			return True
			
		except Exception as e:
			logger.error(f"Error sending email alert: {e}")
			return False
	
	def _send_sms_alert(self, user, alert: WeatherAlert) -> bool:
		"""Send SMS alert using Twilio (optional)"""
		try:
			profile = getattr(user, 'profile', None)
			phone = getattr(profile, 'phone_number', None)
			if not phone:
				return False
			
			account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
			auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
			from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', '')
			
			if not all([account_sid, auth_token, from_number]):
				logger.warning("Twilio not configured, skipping SMS")
				return False
			
			# Prepare SMS message
			sms_message = f"Weather247 ALERT: {alert.title}\n{alert.message[:100]}..."
			
			url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
			data = {'From': from_number, 'To': phone, 'Body': sms_message}
			response = requests.post(url, data=data, auth=(account_sid, auth_token))
			if response.status_code in (200, 201):
				return True
			return False
		except Exception as e:
			logger.error(f"Error sending SMS alert: {e}")
			return False


class AlertMLOptimizer:
	"""Machine learning optimizer for alert relevance and timing"""
	
	def __init__(self):
		self.user_preferences = {}
		self.alert_effectiveness = {}
	
	def learn_from_user_response(self, user_id: int, alert_id: int, response: str):
		"""Learn from user responses to improve alert relevance"""
		try:
			if user_id not in self.user_preferences:
				self.user_preferences[user_id] = {
					'dismissed_alerts': [],
					'acknowledged_alerts': [],
					'preferred_times': [],
					'sensitivity_adjustments': {}
				}
			
			alert = WeatherAlert.objects.get(id=alert_id)
			
			if response == 'dismissed':
				self.user_preferences[user_id]['dismissed_alerts'].append({
					'alert_type': alert.alert_type,
					'severity': alert.severity,
					'time': alert.created_at.hour,
					'weather_data': alert.weather_data
				})
			elif response == 'acknowledged':
				self.user_preferences[user_id]['acknowledged_alerts'].append({
					'alert_type': alert.alert_type,
					'severity': alert.severity,
					'time': alert.created_at.hour,
					'weather_data': alert.weather_data
				})
			
			# Update alert effectiveness
			self._update_alert_effectiveness(alert, response)
			
		except Exception as e:
			logger.error(f"Error learning from user response: {e}")
	
	def _update_alert_effectiveness(self, alert: WeatherAlert, response: str):
		"""Update alert effectiveness metrics"""
		alert_key = f"{alert.alert_type}_{alert.severity}"
		
		if alert_key not in self.alert_effectiveness:
			self.alert_effectiveness[alert_key] = {
				'total_sent': 0,
				'acknowledged': 0,
				'dismissed': 0,
				'effectiveness_score': 0.5
			}
		
		self.alert_effectiveness[alert_key]['total_sent'] += 1
		
		if response == 'acknowledged':
			self.alert_effectiveness[alert_key]['acknowledged'] += 1
		elif response == 'dismissed':
			self.alert_effectiveness[alert_key]['dismissed'] += 1
		
		# Calculate effectiveness score
		total = self.alert_effectiveness[alert_key]['total_sent']
		acknowledged = self.alert_effectiveness[alert_key]['acknowledged']
		
		if total > 0:
			self.alert_effectiveness[alert_key]['effectiveness_score'] = acknowledged / total


# Celery tasks for background processing
@shared_task
def process_weather_alerts(city_id: int):
	"""Background task to process weather alerts for a city"""
	try:
		city = City.objects.get(id=city_id)
		latest_weather = WeatherData.objects.filter(city=city).order_by('-timestamp').first()
		
		if latest_weather:
			alert_engine = WeatherAlertEngine()
			alerts_sent = alert_engine.process_alerts_for_users(latest_weather)
			logger.info(f"Processed alerts for {city.name}: {alerts_sent} alerts sent")
			return alerts_sent
		
	except Exception as e:
		logger.error(f"Error in process_weather_alerts task: {e}")
		return 0


@shared_task
def cleanup_old_alerts():
	"""Clean up old alert records"""
	try:
		cutoff_date = timezone.now() - timedelta(days=30)
		deleted_count = WeatherAlert.objects.filter(created_at__lt=cutoff_date).delete()[0]
		logger.info(f"Cleaned up {deleted_count} old alerts")
		return deleted_count
	except Exception as e:
		logger.error(f"Error cleaning up alerts: {e}")
		return 0


# Global instances
alert_engine = WeatherAlertEngine()
alert_optimizer = AlertMLOptimizer()