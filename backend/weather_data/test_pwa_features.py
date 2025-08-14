"""
Test PWA Features - Push Notifications, Service Worker Integration, etc.
"""
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()
from rest_framework.test import APITestCase
from rest_framework import status

from .models import PushSubscription, NotificationLog
from .push_notifications import PushNotificationService


class PushNotificationServiceTest(TestCase):
    """Test the PushNotificationService class"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.subscription_data = {
            'subscription': {
                'endpoint': 'https://fcm.googleapis.com/fcm/send/test-endpoint',
                'keys': {
                    'p256dh': 'test-p256dh-key',
                    'auth': 'test-auth-key'
                }
            },
            'user_agent': 'Mozilla/5.0 Test Browser',
            'timezone': 'America/New_York'
        }
        
        self.preferences = {
            'weather_alerts': True,
            'severe_weather_alerts': True,
            'daily_forecast': False,
            'location_updates': False
        }

    def test_create_subscription(self):
        """Test creating a new push subscription"""
        subscription = PushNotificationService.create_subscription(
            user=self.user,
            subscription_data=self.subscription_data,
            preferences=self.preferences
        )
        
        self.assertIsInstance(subscription, PushSubscription)
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.endpoint, self.subscription_data['subscription']['endpoint'])
        self.assertEqual(subscription.p256dh_key, self.subscription_data['subscription']['keys']['p256dh'])
        self.assertEqual(subscription.auth_key, self.subscription_data['subscription']['keys']['auth'])
        self.assertTrue(subscription.weather_alerts)
        self.assertTrue(subscription.severe_weather_alerts)
        self.assertFalse(subscription.daily_forecast)
        self.assertTrue(subscription.is_active)

    def test_update_existing_subscription(self):
        """Test updating an existing subscription"""
        # Create initial subscription
        subscription1 = PushNotificationService.create_subscription(
            user=self.user,
            subscription_data=self.subscription_data,
            preferences={'weather_alerts': False}
        )
        
        # Update with new preferences
        subscription2 = PushNotificationService.create_subscription(
            user=self.user,
            subscription_data=self.subscription_data,
            preferences={'weather_alerts': True, 'daily_forecast': True}
        )
        
        # Should be the same subscription object, updated
        self.assertEqual(subscription1.id, subscription2.id)
        self.assertTrue(subscription2.weather_alerts)
        self.assertTrue(subscription2.daily_forecast)

    def test_remove_subscription(self):
        """Test removing a push subscription"""
        subscription = PushNotificationService.create_subscription(
            user=self.user,
            subscription_data=self.subscription_data
        )
        
        endpoint = subscription.endpoint
        
        # Remove subscription
        success = PushNotificationService.remove_subscription(endpoint)
        self.assertTrue(success)
        
        # Verify it's deleted
        self.assertFalse(PushSubscription.objects.filter(endpoint=endpoint).exists())

    def test_verify_subscription(self):
        """Test verifying a subscription exists and is active"""
        subscription = PushNotificationService.create_subscription(
            user=self.user,
            subscription_data=self.subscription_data
        )
        
        # Should verify successfully
        is_valid = PushNotificationService.verify_subscription(subscription.endpoint)
        self.assertTrue(is_valid)
        
        # Should fail for non-existent endpoint
        is_valid = PushNotificationService.verify_subscription('non-existent-endpoint')
        self.assertFalse(is_valid)

    def test_update_preferences(self):
        """Test updating notification preferences"""
        subscription = PushNotificationService.create_subscription(
            user=self.user,
            subscription_data=self.subscription_data,
            preferences={'weather_alerts': False}
        )
        
        # Update preferences
        new_preferences = {
            'weather_alerts': True,
            'daily_forecast': True,
            'location_updates': True
        }
        
        success = PushNotificationService.update_preferences(
            subscription.endpoint, 
            new_preferences
        )
        
        self.assertTrue(success)
        
        # Verify preferences were updated
        subscription.refresh_from_db()
        self.assertTrue(subscription.weather_alerts)
        self.assertTrue(subscription.daily_forecast)
        self.assertTrue(subscription.location_updates)

    @patch('weather_data.push_notifications.webpush')
    def test_send_notification(self, mock_webpush):
        """Test sending a push notification"""
        subscription = PushNotificationService.create_subscription(
            user=self.user,
            subscription_data=self.subscription_data
        )
        
        # Mock successful webpush call
        mock_webpush.return_value = None
        
        success = PushNotificationService.send_notification(
            subscription=subscription,
            title='Test Notification',
            body='This is a test notification',
            data={'test': True},
            notification_type='test'
        )
        
        self.assertTrue(success)
        mock_webpush.assert_called_once()
        
        # Verify notification was logged
        log_entry = NotificationLog.objects.filter(subscription=subscription).first()
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.title, 'Test Notification')
        self.assertEqual(log_entry.status, 'sent')

    @patch('weather_data.push_notifications.webpush')
    def test_send_notification_to_inactive_subscription(self, mock_webpush):
        """Test sending notification to inactive subscription"""
        subscription = PushNotificationService.create_subscription(
            user=self.user,
            subscription_data=self.subscription_data
        )
        
        # Deactivate subscription
        subscription.is_active = False
        subscription.save()
        
        success = PushNotificationService.send_notification(
            subscription=subscription,
            title='Test Notification',
            body='This is a test notification'
        )
        
        self.assertFalse(success)
        mock_webpush.assert_not_called()

    def test_get_subscription_stats(self):
        """Test getting subscription statistics"""
        # Create multiple subscriptions
        for i in range(3):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123'
            )
            
            subscription_data = self.subscription_data.copy()
            subscription_data['subscription']['endpoint'] = f'https://test.com/endpoint{i}'
            
            PushNotificationService.create_subscription(
                user=user,
                subscription_data=subscription_data,
                preferences={
                    'weather_alerts': i % 2 == 0,
                    'severe_weather_alerts': True,
                    'daily_forecast': i == 1
                }
            )
        
        stats = PushNotificationService.get_subscription_stats()
        
        self.assertEqual(stats['total_subscriptions'], 3)
        self.assertEqual(stats['active_subscriptions'], 3)
        self.assertEqual(stats['weather_alerts_enabled'], 2)  # users 0 and 2
        self.assertEqual(stats['severe_alerts_enabled'], 3)   # all users
        self.assertEqual(stats['daily_forecast_enabled'], 1)  # user 1 only


class PushNotificationAPITest(APITestCase):
    """Test the Push Notification API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.subscription_data = {
            'subscription': {
                'endpoint': 'https://fcm.googleapis.com/fcm/send/test-endpoint',
                'keys': {
                    'p256dh': 'test-p256dh-key',
                    'auth': 'test-auth-key'
                }
            },
            'preferences': {
                'weather_alerts': True,
                'severe_weather_alerts': True,
                'daily_forecast': False
            },
            'user_agent': 'Mozilla/5.0 Test Browser',
            'timezone': 'America/New_York'
        }

    def test_create_subscription_api(self):
        """Test creating subscription via API"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            '/api/push-subscription/',
            data=json.dumps(self.subscription_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])
        
        # Verify subscription was created
        subscription = PushSubscription.objects.get(
            endpoint=self.subscription_data['subscription']['endpoint']
        )
        self.assertEqual(subscription.user, self.user)

    def test_create_subscription_unauthenticated(self):
        """Test creating subscription without authentication"""
        response = self.client.post(
            '/api/push-subscription/',
            data=json.dumps(self.subscription_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)

    def test_verify_subscription_api(self):
        """Test verifying subscription via API"""
        # Create subscription first
        subscription = PushNotificationService.create_subscription(
            user=self.user,
            subscription_data=self.subscription_data
        )
        
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            '/api/push-subscription/verify/',
            data={'endpoint': subscription.endpoint}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['valid'])

    def test_update_preferences_api(self):
        """Test updating preferences via API"""
        # Create subscription first
        subscription = PushNotificationService.create_subscription(
            user=self.user,
            subscription_data=self.subscription_data
        )
        
        self.client.force_authenticate(user=self.user)
        
        new_preferences = {
            'weather_alerts': False,
            'daily_forecast': True
        }
        
        response = self.client.put(
            '/api/push-subscription/preferences/',
            data={
                'endpoint': subscription.endpoint,
                'preferences': new_preferences
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])
        
        # Verify preferences were updated
        subscription.refresh_from_db()
        self.assertFalse(subscription.weather_alerts)
        self.assertTrue(subscription.daily_forecast)

    @patch('weather_data.push_notifications.PushNotificationService.send_test_notification')
    def test_send_test_notification_api(self, mock_send_test):
        """Test sending test notification via API"""
        # Create subscription first
        subscription = PushNotificationService.create_subscription(
            user=self.user,
            subscription_data=self.subscription_data
        )
        
        mock_send_test.return_value = True
        
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            '/api/push-subscription/test/',
            data={'endpoint': subscription.endpoint}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])
        mock_send_test.assert_called_once_with(subscription.endpoint)

    def test_subscription_status_api(self):
        """Test getting subscription status via API"""
        # Create subscription first
        subscription = PushNotificationService.create_subscription(
            user=self.user,
            subscription_data=self.subscription_data
        )
        
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/push-subscription/status/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['total_subscriptions'], 1)
        self.assertTrue(data['has_active_subscription'])

    def test_admin_subscription_stats(self):
        """Test admin-only subscription stats endpoint"""
        # Create admin user
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
        
        self.client.force_authenticate(user=admin_user)
        
        response = self.client.get('/api/push-subscription/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])
        self.assertIn('stats', response.json())

    def test_admin_stats_non_admin_user(self):
        """Test that non-admin users cannot access stats"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/push-subscription/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PWAIntegrationTest(TestCase):
    """Test PWA integration features"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_manifest_json_accessible(self):
        """Test that manifest.json is accessible"""
        response = self.client.get('/manifest.json')
        self.assertEqual(response.status_code, 200)
        
        # Should be valid JSON
        try:
            manifest_data = json.loads(response.content)
            self.assertIn('name', manifest_data)
            self.assertIn('short_name', manifest_data)
            self.assertIn('icons', manifest_data)
        except json.JSONDecodeError:
            self.fail("manifest.json is not valid JSON")

    def test_service_worker_accessible(self):
        """Test that service worker is accessible"""
        response = self.client.get('/sw.js')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/javascript', response.get('Content-Type', ''))

    def test_pwa_meta_tags_in_html(self):
        """Test that PWA meta tags are present in HTML"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # Check for essential PWA meta tags
        self.assertIn('manifest.json', content)
        self.assertIn('theme-color', content)
        self.assertIn('apple-mobile-web-app-capable', content)
        self.assertIn('apple-touch-icon', content)

    def test_offline_page_fallback(self):
        """Test that there's a fallback for offline scenarios"""
        # This would typically test the service worker's offline handling
        # For now, we just verify the main page loads
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    import unittest
    unittest.main()