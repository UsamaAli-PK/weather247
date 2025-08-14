// Push Notifications Service for Weather247
class PushNotificationService {
  constructor() {
    this.subscription = null;
    this.isSupported = 'Notification' in window && 'serviceWorker' in navigator && 'PushManager' in window;
    this.permission = this.isSupported ? Notification.permission : 'not-supported';
    
    // VAPID public key - replace with your actual key
    this.vapidPublicKey = 'BEl62iUYgUivxIkv69yViEuiBIa40HI80NM9LdNnC_NNPJ6Ck96SUBBj2lOjHqyz2XJbdHiGhGWw5Ej5QmYSjMc';
    
    this.init();
  }

  async init() {
    if (!this.isSupported) {
      console.warn('Push notifications not supported');
      return;
    }

    // Check existing subscription
    await this.checkExistingSubscription();
    
    console.log('Push Notification Service initialized', {
      supported: this.isSupported,
      permission: this.permission,
      hasSubscription: !!this.subscription
    });
  }

  // Check if user already has a push subscription
  async checkExistingSubscription() {
    if (!this.isSupported) return null;

    try {
      const registration = await navigator.serviceWorker.ready;
      this.subscription = await registration.pushManager.getSubscription();
      
      if (this.subscription) {
        console.log('Existing push subscription found');
        // Verify subscription is still valid with server
        await this.verifySubscriptionWithServer();
      }
      
      return this.subscription;
    } catch (error) {
      console.error('Error checking existing subscription:', error);
      return null;
    }
  }

  // Request notification permission
  async requestPermission() {
    if (!this.isSupported) {
      return { success: false, error: 'Push notifications not supported' };
    }

    if (this.permission === 'granted') {
      return { success: true, permission: 'granted' };
    }

    if (this.permission === 'denied') {
      return { 
        success: false, 
        error: 'Notification permission denied. Please enable in browser settings.' 
      };
    }

    try {
      const permission = await Notification.requestPermission();
      this.permission = permission;
      
      console.log('Notification permission:', permission);
      
      if (permission === 'granted') {
        return { success: true, permission: 'granted' };
      } else {
        return { 
          success: false, 
          error: 'Notification permission not granted',
          permission 
        };
      }
    } catch (error) {
      console.error('Error requesting notification permission:', error);
      return { success: false, error: error.message };
    }
  }

  // Subscribe to push notifications
  async subscribe(options = {}) {
    if (!this.isSupported) {
      return { success: false, error: 'Push notifications not supported' };
    }

    // Request permission first
    const permissionResult = await this.requestPermission();
    if (!permissionResult.success) {
      return permissionResult;
    }

    try {
      const registration = await navigator.serviceWorker.ready;
      
      // Check if already subscribed
      const existingSubscription = await registration.pushManager.getSubscription();
      if (existingSubscription) {
        this.subscription = existingSubscription;
        console.log('Using existing push subscription');
        return { success: true, subscription: this.subscription };
      }

      // Create new subscription
      this.subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlBase64ToUint8Array(this.vapidPublicKey)
      });

      console.log('New push subscription created');

      // Send subscription to server
      const serverResult = await this.sendSubscriptionToServer(this.subscription, options);
      
      if (serverResult.success) {
        // Store subscription preferences locally
        this.storeSubscriptionPreferences(options);
        
        return { 
          success: true, 
          subscription: this.subscription,
          preferences: options 
        };
      } else {
        // If server registration fails, unsubscribe
        await this.unsubscribe();
        return { success: false, error: 'Failed to register with server' };
      }

    } catch (error) {
      console.error('Error subscribing to push notifications:', error);
      return { success: false, error: error.message };
    }
  }

  // Unsubscribe from push notifications
  async unsubscribe() {
    if (!this.subscription) {
      return { success: true, message: 'No active subscription' };
    }

    try {
      // Unsubscribe from browser
      const success = await this.subscription.unsubscribe();
      
      if (success) {
        // Remove from server
        await this.removeSubscriptionFromServer(this.subscription);
        
        this.subscription = null;
        this.clearSubscriptionPreferences();
        
        console.log('Push subscription removed');
        return { success: true };
      } else {
        return { success: false, error: 'Failed to unsubscribe' };
      }
    } catch (error) {
      console.error('Error unsubscribing from push notifications:', error);
      return { success: false, error: error.message };
    }
  }

  // Send subscription to server
  async sendSubscriptionToServer(subscription, preferences = {}) {
    try {
      const response = await fetch('/api/push-subscription/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken()
        },
        body: JSON.stringify({
          subscription: subscription.toJSON(),
          preferences: {
            weatherAlerts: preferences.weatherAlerts !== false,
            severeWeatherAlerts: preferences.severeWeatherAlerts !== false,
            dailyForecast: preferences.dailyForecast || false,
            locationUpdates: preferences.locationUpdates || false,
            ...preferences
          },
          user_agent: navigator.userAgent,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
        })
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Push subscription registered with server:', data);
        return { success: true, data };
      } else {
        const error = await response.text();
        console.error('Failed to register push subscription with server:', error);
        return { success: false, error };
      }
    } catch (error) {
      console.error('Error sending subscription to server:', error);
      return { success: false, error: error.message };
    }
  }

  // Remove subscription from server
  async removeSubscriptionFromServer(subscription) {
    try {
      const response = await fetch('/api/push-subscription/', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken()
        },
        body: JSON.stringify({
          endpoint: subscription.endpoint
        })
      });

      if (response.ok) {
        console.log('Push subscription removed from server');
        return { success: true };
      } else {
        console.error('Failed to remove push subscription from server');
        return { success: false };
      }
    } catch (error) {
      console.error('Error removing subscription from server:', error);
      return { success: false, error: error.message };
    }
  }

  // Verify subscription is still valid with server
  async verifySubscriptionWithServer() {
    if (!this.subscription) return false;

    try {
      const response = await fetch('/api/push-subscription/verify/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken()
        },
        body: JSON.stringify({
          endpoint: this.subscription.endpoint
        })
      });

      const isValid = response.ok;
      
      if (!isValid) {
        console.log('Push subscription is no longer valid, removing...');
        this.subscription = null;
        this.clearSubscriptionPreferences();
      }
      
      return isValid;
    } catch (error) {
      console.error('Error verifying subscription with server:', error);
      return false;
    }
  }

  // Update notification preferences
  async updatePreferences(preferences) {
    if (!this.subscription) {
      return { success: false, error: 'No active subscription' };
    }

    try {
      const response = await fetch('/api/push-subscription/preferences/', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken()
        },
        body: JSON.stringify({
          endpoint: this.subscription.endpoint,
          preferences: preferences
        })
      });

      if (response.ok) {
        this.storeSubscriptionPreferences(preferences);
        console.log('Push notification preferences updated');
        return { success: true, preferences };
      } else {
        const error = await response.text();
        console.error('Failed to update preferences:', error);
        return { success: false, error };
      }
    } catch (error) {
      console.error('Error updating preferences:', error);
      return { success: false, error: error.message };
    }
  }

  // Send test notification
  async sendTestNotification() {
    if (!this.subscription) {
      return { success: false, error: 'No active subscription' };
    }

    try {
      const response = await fetch('/api/push-subscription/test/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken()
        },
        body: JSON.stringify({
          endpoint: this.subscription.endpoint
        })
      });

      if (response.ok) {
        console.log('Test notification sent');
        return { success: true };
      } else {
        const error = await response.text();
        console.error('Failed to send test notification:', error);
        return { success: false, error };
      }
    } catch (error) {
      console.error('Error sending test notification:', error);
      return { success: false, error: error.message };
    }
  }

  // Show local notification (for testing)
  showLocalNotification(title, options = {}) {
    if (!this.isSupported || this.permission !== 'granted') {
      console.warn('Cannot show notification: not supported or permission denied');
      return false;
    }

    const notification = new Notification(title, {
      body: options.body || 'Weather247 notification',
      icon: options.icon || '/favicon.ico',
      badge: options.badge || '/favicon.ico',
      tag: options.tag || 'weather247',
      requireInteraction: options.requireInteraction || false,
      silent: options.silent || false,
      vibrate: options.vibrate || [100, 50, 100],
      data: options.data || {},
      ...options
    });

    // Handle notification click
    notification.onclick = (event) => {
      event.preventDefault();
      window.focus();
      notification.close();
      
      if (options.onClick) {
        options.onClick(event);
      }
    };

    return notification;
  }

  // Store subscription preferences locally
  storeSubscriptionPreferences(preferences) {
    localStorage.setItem('push-notification-preferences', JSON.stringify({
      ...preferences,
      timestamp: Date.now()
    }));
  }

  // Get stored subscription preferences
  getSubscriptionPreferences() {
    try {
      const stored = localStorage.getItem('push-notification-preferences');
      return stored ? JSON.parse(stored) : {};
    } catch (error) {
      console.error('Error getting subscription preferences:', error);
      return {};
    }
  }

  // Clear subscription preferences
  clearSubscriptionPreferences() {
    localStorage.removeItem('push-notification-preferences');
  }

  // Convert VAPID key from base64 to Uint8Array
  urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  // Get CSRF token for Django
  getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === 'csrftoken') {
        return value;
      }
    }
    return '';
  }

  // Get notification status
  getStatus() {
    return {
      supported: this.isSupported,
      permission: this.permission,
      subscribed: !!this.subscription,
      subscription: this.subscription,
      preferences: this.getSubscriptionPreferences()
    };
  }

  // Check if specific notification type is enabled
  isNotificationTypeEnabled(type) {
    const preferences = this.getSubscriptionPreferences();
    return preferences[type] !== false; // Default to true if not specified
  }
}

// Create singleton instance
const pushNotificationService = new PushNotificationService();

export default pushNotificationService;