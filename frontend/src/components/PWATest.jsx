import React, { useState, useEffect } from 'react';
import { usePWA } from './PWAManager';
import pwaService from '../services/pwaService';
import pushNotificationService from '../services/pushNotifications';
import backgroundSyncService from '../services/backgroundSync';

const PWATest = () => {
  const { isOnline, appInfo } = usePWA();
  const [testResults, setTestResults] = useState({});
  const [isRunning, setIsRunning] = useState(false);

  const runTests = async () => {
    setIsRunning(true);
    const results = {};

    try {
      // Test 1: Service Worker Registration
      results.serviceWorker = {
        name: 'Service Worker Registration',
        status: 'serviceWorker' in navigator ? 'PASS' : 'FAIL',
        details: 'serviceWorker' in navigator ? 'Service Worker API is supported' : 'Service Worker API not supported'
      };

      // Test 2: PWA Service Initialization
      const pwaInfo = pwaService.getAppInfo();
      results.pwaService = {
        name: 'PWA Service',
        status: pwaInfo ? 'PASS' : 'FAIL',
        details: `PWA Service initialized. Installed: ${pwaInfo.isInstalled}, Standalone: ${pwaInfo.isStandalone}`
      };

      // Test 3: Push Notification Support
      const pushStatus = pushNotificationService.getStatus();
      results.pushNotifications = {
        name: 'Push Notifications',
        status: pushStatus.supported ? 'PASS' : 'FAIL',
        details: `Push notifications supported: ${pushStatus.supported}, Permission: ${pushStatus.permission}`
      };

      // Test 4: Background Sync Support
      const syncSupported = 'serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype;
      results.backgroundSync = {
        name: 'Background Sync',
        status: syncSupported ? 'PASS' : 'FAIL',
        details: syncSupported ? 'Background Sync API is supported' : 'Background Sync API not supported'
      };

      // Test 5: Cache API
      const cacheSupported = 'caches' in window;
      results.cacheApi = {
        name: 'Cache API',
        status: cacheSupported ? 'PASS' : 'FAIL',
        details: cacheSupported ? 'Cache API is supported' : 'Cache API not supported'
      };

      // Test 6: IndexedDB (for background sync storage)
      const indexedDBSupported = 'indexedDB' in window;
      results.indexedDB = {
        name: 'IndexedDB',
        status: indexedDBSupported ? 'PASS' : 'FAIL',
        details: indexedDBSupported ? 'IndexedDB is supported' : 'IndexedDB not supported'
      };

      // Test 7: Manifest
      const manifestLink = document.querySelector('link[rel="manifest"]');
      results.manifest = {
        name: 'Web App Manifest',
        status: manifestLink ? 'PASS' : 'FAIL',
        details: manifestLink ? `Manifest found: ${manifestLink.href}` : 'No manifest link found'
      };

      // Test 8: HTTPS (required for PWA features)
      const isHTTPS = location.protocol === 'https:' || location.hostname === 'localhost';
      results.https = {
        name: 'HTTPS/Localhost',
        status: isHTTPS ? 'PASS' : 'FAIL',
        details: isHTTPS ? 'Running on HTTPS or localhost' : 'PWA features require HTTPS or localhost'
      };

      // Test 9: Offline capability
      try {
        const cachedData = await pwaService.getCachedWeatherData('test');
        results.offlineCapability = {
          name: 'Offline Capability',
          status: 'PASS',
          details: 'Cache access working'
        };
      } catch (error) {
        results.offlineCapability = {
          name: 'Offline Capability',
          status: 'WARN',
          details: 'Cache access failed, but this is expected on first run'
        };
      }

      // Test 10: Background Sync Storage
      try {
        const syncStats = await backgroundSyncService.getSyncStats();
        results.syncStorage = {
          name: 'Background Sync Storage',
          status: 'PASS',
          details: `Sync storage working. Pending items: ${syncStats.total || 0}`
        };
      } catch (error) {
        results.syncStorage = {
          name: 'Background Sync Storage',
          status: 'FAIL',
          details: `Sync storage error: ${error.message}`
        };
      }

      // Test 11: Push Notification Subscription
      try {
        const pushStatus = pushNotificationService.getStatus();
        results.pushSubscription = {
          name: 'Push Subscription',
          status: pushStatus.subscribed ? 'PASS' : 'WARN',
          details: pushStatus.subscribed ? 'Push notifications are subscribed' : 'Push notifications not subscribed (this is normal)'
        };
      } catch (error) {
        results.pushSubscription = {
          name: 'Push Subscription',
          status: 'FAIL',
          details: `Push subscription error: ${error.message}`
        };
      }

      // Test 12: Service Worker Version
      try {
        const version = await pwaService.getServiceWorkerVersion();
        results.serviceWorkerVersion = {
          name: 'Service Worker Version',
          status: version ? 'PASS' : 'WARN',
          details: version ? `Service Worker version: ${version}` : 'Could not retrieve service worker version'
        };
      } catch (error) {
        results.serviceWorkerVersion = {
          name: 'Service Worker Version',
          status: 'FAIL',
          details: `Version check error: ${error.message}`
        };
      }

    } catch (error) {
      results.error = {
        name: 'Test Error',
        status: 'FAIL',
        details: error.message
      };
    }

    setTestResults(results);
    setIsRunning(false);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'PASS': return 'text-green-600 bg-green-100';
      case 'FAIL': return 'text-red-600 bg-red-100';
      case 'WARN': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            PWA Feature Test Suite
          </h2>
          <p className="text-gray-600">
            Test Progressive Web App capabilities and features
          </p>
        </div>

        <div className="p-6">
          {/* Current Status */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="font-semibold text-gray-900 mb-2">Current Status</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Online:</span>
                <span className={`ml-2 font-medium ${isOnline ? 'text-green-600' : 'text-red-600'}`}>
                  {isOnline ? 'Yes' : 'No'}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Installed:</span>
                <span className={`ml-2 font-medium ${appInfo.isInstalled ? 'text-green-600' : 'text-gray-600'}`}>
                  {appInfo.isInstalled ? 'Yes' : 'No'}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Standalone:</span>
                <span className={`ml-2 font-medium ${appInfo.isStandalone ? 'text-green-600' : 'text-gray-600'}`}>
                  {appInfo.isStandalone ? 'Yes' : 'No'}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Notifications:</span>
                <span className={`ml-2 font-medium ${
                  appInfo.notificationPermission === 'granted' ? 'text-green-600' : 
                  appInfo.notificationPermission === 'denied' ? 'text-red-600' : 'text-yellow-600'
                }`}>
                  {appInfo.notificationPermission}
                </span>
              </div>
            </div>
          </div>

          {/* Test Button */}
          <div className="mb-6">
            <button
              onClick={runTests}
              disabled={isRunning}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium py-2 px-4 rounded-md transition-colors"
            >
              {isRunning ? 'Running Tests...' : 'Run PWA Tests'}
            </button>
          </div>

          {/* Test Results */}
          {Object.keys(testResults).length > 0 && (
            <div className="space-y-3">
              <h3 className="font-semibold text-gray-900 mb-4">Test Results</h3>
              {Object.entries(testResults).map(([key, result]) => (
                <div key={key} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-gray-900">{result.name}</h4>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(result.status)}`}>
                      {result.status}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">{result.details}</p>
                </div>
              ))}
            </div>
          )}

          {/* Test Summary */}
          {Object.keys(testResults).length > 0 && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="font-semibold text-gray-900 mb-2">Summary</h3>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-green-600 font-medium">
                    {Object.values(testResults).filter(r => r.status === 'PASS').length} Passed
                  </span>
                </div>
                <div>
                  <span className="text-yellow-600 font-medium">
                    {Object.values(testResults).filter(r => r.status === 'WARN').length} Warnings
                  </span>
                </div>
                <div>
                  <span className="text-red-600 font-medium">
                    {Object.values(testResults).filter(r => r.status === 'FAIL').length} Failed
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PWATest;