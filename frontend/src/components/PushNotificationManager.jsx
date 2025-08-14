import React, { useState, useEffect } from 'react';
import { Bell, BellOff, Settings, Check, X, AlertTriangle } from 'lucide-react';
import pushNotificationService from '../services/pushNotifications';

const PushNotificationManager = ({ className = '' }) => {
  const [status, setStatus] = useState(pushNotificationService.getStatus());
  const [isLoading, setIsLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [preferences, setPreferences] = useState({
    weatherAlerts: true,
    severeWeatherAlerts: true,
    dailyForecast: false,
    locationUpdates: false
  });
  const [message, setMessage] = useState(null);

  useEffect(() => {
    // Load current preferences
    const currentPrefs = pushNotificationService.getSubscriptionPreferences();
    if (Object.keys(currentPrefs).length > 0) {
      setPreferences(prev => ({ ...prev, ...currentPrefs }));
    }

    // Update status
    setStatus(pushNotificationService.getStatus());
  }, []);

  const showMessage = (text, type = 'info') => {
    setMessage({ text, type });
    setTimeout(() => setMessage(null), 5000);
  };

  const handleSubscribe = async () => {
    setIsLoading(true);
    
    try {
      const result = await pushNotificationService.subscribe(preferences);
      
      if (result.success) {
        setStatus(pushNotificationService.getStatus());
        showMessage('Push notifications enabled successfully!', 'success');
      } else {
        showMessage(result.error || 'Failed to enable push notifications', 'error');
      }
    } catch (error) {
      showMessage('An error occurred while enabling notifications', 'error');
      console.error('Subscription error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUnsubscribe = async () => {
    setIsLoading(true);
    
    try {
      const result = await pushNotificationService.unsubscribe();
      
      if (result.success) {
        setStatus(pushNotificationService.getStatus());
        showMessage('Push notifications disabled', 'info');
      } else {
        showMessage(result.error || 'Failed to disable push notifications', 'error');
      }
    } catch (error) {
      showMessage('An error occurred while disabling notifications', 'error');
      console.error('Unsubscription error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePreferenceChange = (key, value) => {
    setPreferences(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSavePreferences = async () => {
    if (!status.subscribed) {
      // If not subscribed, just save locally and subscribe
      await handleSubscribe();
      return;
    }

    setIsLoading(true);
    
    try {
      const result = await pushNotificationService.updatePreferences(preferences);
      
      if (result.success) {
        showMessage('Notification preferences updated!', 'success');
        setShowSettings(false);
      } else {
        showMessage(result.error || 'Failed to update preferences', 'error');
      }
    } catch (error) {
      showMessage('An error occurred while updating preferences', 'error');
      console.error('Preferences update error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestNotification = async () => {
    if (!status.subscribed) {
      showMessage('Please enable notifications first', 'warning');
      return;
    }

    setIsLoading(true);
    
    try {
      const result = await pushNotificationService.sendTestNotification();
      
      if (result.success) {
        showMessage('Test notification sent! Check your notifications.', 'success');
      } else {
        showMessage(result.error || 'Failed to send test notification', 'error');
      }
    } catch (error) {
      showMessage('An error occurred while sending test notification', 'error');
      console.error('Test notification error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!status.supported) {
    return (
      <div className={`p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg ${className}`}>
        <div className="flex items-center space-x-2">
          <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
          <span className="text-sm text-yellow-800 dark:text-yellow-200">
            Push notifications are not supported in this browser
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Status and Main Controls */}
      <div className="flex items-center justify-between p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <div className="flex items-center space-x-3">
          {status.subscribed ? (
            <Bell className="h-5 w-5 text-green-600 dark:text-green-400" />
          ) : (
            <BellOff className="h-5 w-5 text-gray-400" />
          )}
          <div>
            <h3 className="font-medium text-gray-900 dark:text-white">
              Push Notifications
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {status.subscribed 
                ? 'Enabled - You\'ll receive weather alerts' 
                : 'Disabled - Enable to receive weather alerts'
              }
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {status.subscribed && (
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
              aria-label="Notification settings"
            >
              <Settings className="h-4 w-4" />
            </button>
          )}
          
          <button
            onClick={status.subscribed ? handleUnsubscribe : handleSubscribe}
            disabled={isLoading}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              status.subscribed
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {isLoading ? (
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                <span>Loading...</span>
              </div>
            ) : status.subscribed ? (
              'Disable'
            ) : (
              'Enable'
            )}
          </button>
        </div>
      </div>

      {/* Permission Status */}
      {status.permission === 'denied' && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="flex items-start space-x-2">
            <X className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" />
            <div>
              <h4 className="font-medium text-red-800 dark:text-red-200">
                Notifications Blocked
              </h4>
              <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                Please enable notifications in your browser settings to receive weather alerts.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Settings Panel */}
      {showSettings && status.subscribed && (
        <div className="p-4 bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg">
          <h4 className="font-medium text-gray-900 dark:text-white mb-4">
            Notification Preferences
          </h4>
          
          <div className="space-y-3">
            <label className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  Weather Alerts
                </span>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Get notified about weather changes
                </p>
              </div>
              <input
                type="checkbox"
                checked={preferences.weatherAlerts}
                onChange={(e) => handlePreferenceChange('weatherAlerts', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            </label>

            <label className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  Severe Weather Alerts
                </span>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Critical weather warnings and alerts
                </p>
              </div>
              <input
                type="checkbox"
                checked={preferences.severeWeatherAlerts}
                onChange={(e) => handlePreferenceChange('severeWeatherAlerts', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            </label>

            <label className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  Daily Forecast
                </span>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Daily weather summary notifications
                </p>
              </div>
              <input
                type="checkbox"
                checked={preferences.dailyForecast}
                onChange={(e) => handlePreferenceChange('dailyForecast', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            </label>

            <label className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  Location Updates
                </span>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Notifications when you change locations
                </p>
              </div>
              <input
                type="checkbox"
                checked={preferences.locationUpdates}
                onChange={(e) => handlePreferenceChange('locationUpdates', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            </label>
          </div>

          <div className="flex justify-between items-center mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={handleTestNotification}
              disabled={isLoading}
              className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 disabled:opacity-50"
            >
              Send Test Notification
            </button>
            
            <div className="flex space-x-2">
              <button
                onClick={() => setShowSettings(false)}
                className="px-3 py-1 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={handleSavePreferences}
                disabled={isLoading}
                className="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-md disabled:opacity-50"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Message Display */}
      {message && (
        <div className={`p-3 rounded-lg border ${
          message.type === 'success' 
            ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-800 dark:text-green-200'
            : message.type === 'error'
            ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-800 dark:text-red-200'
            : message.type === 'warning'
            ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800 text-yellow-800 dark:text-yellow-200'
            : 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-800 dark:text-blue-200'
        }`}>
          <div className="flex items-center space-x-2">
            {message.type === 'success' && <Check className="h-4 w-4" />}
            {message.type === 'error' && <X className="h-4 w-4" />}
            {message.type === 'warning' && <AlertTriangle className="h-4 w-4" />}
            <span className="text-sm">{message.text}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default PushNotificationManager;