import React, { useState, useEffect } from 'react';
import { 
  Smartphone, 
  Bell, 
  Wifi, 
  Download, 
  Users, 
  Activity, 
  AlertCircle,
  CheckCircle,
  RefreshCw,
  Settings
} from 'lucide-react';
import { usePWA } from './PWAManager';
import pwaService from '../services/pwaService';
import pushNotificationService from '../services/pushNotifications';
import backgroundSyncService from '../services/backgroundSync';

const PWAStatusDashboard = ({ className = '' }) => {
  const { isOnline, appInfo } = usePWA();
  const [stats, setStats] = useState({
    serviceWorker: null,
    pushNotifications: null,
    backgroundSync: null,
    cacheStats: null
  });
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    loadStats();
    
    // Refresh stats every 30 seconds
    const interval = setInterval(loadStats, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const loadStats = async () => {
    setIsLoading(true);
    
    try {
      const [swVersion, pushStatus, syncStats, cacheStats] = await Promise.all([
        pwaService.getServiceWorkerVersion(),
        Promise.resolve(pushNotificationService.getStatus()),
        backgroundSyncService.getSyncStats(),
        getCacheStats()
      ]);

      setStats({
        serviceWorker: {
          version: swVersion,
          registered: !!pwaService.serviceWorker,
          supported: 'serviceWorker' in navigator
        },
        pushNotifications: pushStatus,
        backgroundSync: {
          ...syncStats,
          supported: 'serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype
        },
        cacheStats
      });

      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to load PWA stats:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getCacheStats = async () => {
    if (!('caches' in window)) {
      return { supported: false, caches: [] };
    }

    try {
      const cacheNames = await caches.keys();
      const cacheStats = await Promise.all(
        cacheNames.map(async (name) => {
          const cache = await caches.open(name);
          const keys = await cache.keys();
          return {
            name,
            size: keys.length,
            type: name.includes('static') ? 'static' : 
                  name.includes('dynamic') ? 'dynamic' : 'other'
          };
        })
      );

      return {
        supported: true,
        caches: cacheStats,
        totalCaches: cacheNames.length,
        totalItems: cacheStats.reduce((sum, cache) => sum + cache.size, 0)
      };
    } catch (error) {
      console.error('Error getting cache stats:', error);
      return { supported: true, caches: [], error: error.message };
    }
  };

  const clearAllCaches = async () => {
    if (!('caches' in window)) return;

    try {
      const cacheNames = await caches.keys();
      await Promise.all(cacheNames.map(name => caches.delete(name)));
      
      // Reload stats
      await loadStats();
      
      // Show success message
      window.dispatchEvent(new CustomEvent('pwa-cache-cleared'));
    } catch (error) {
      console.error('Error clearing caches:', error);
    }
  };

  const forceServiceWorkerUpdate = async () => {
    if (!pwaService.serviceWorker) return;

    try {
      await pwaService.serviceWorker.update();
      console.log('Service worker update check triggered');
    } catch (error) {
      console.error('Error updating service worker:', error);
    }
  };

  const getStatusIcon = (status, supported = true) => {
    if (!supported) return <AlertCircle className="h-5 w-5 text-gray-400" />;
    return status ? 
      <CheckCircle className="h-5 w-5 text-green-500" /> : 
      <AlertCircle className="h-5 w-5 text-red-500" />;
  };

  const getStatusColor = (status, supported = true) => {
    if (!supported) return 'text-gray-500 bg-gray-100';
    return status ? 'text-green-700 bg-green-100' : 'text-red-700 bg-red-100';
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            PWA Status Dashboard
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Monitor Progressive Web App features and performance
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={loadStats}
            disabled={isLoading}
            className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
            title="Refresh stats"
          >
            <RefreshCw className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          
          {lastUpdated && (
            <span className="text-xs text-gray-500">
              Updated {lastUpdated.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Connection Status */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                Connection
              </p>
              <p className={`text-xs mt-1 ${isOnline ? 'text-green-600' : 'text-red-600'}`}>
                {isOnline ? 'Online' : 'Offline'}
              </p>
            </div>
            <Wifi className={`h-8 w-8 ${isOnline ? 'text-green-500' : 'text-red-500'}`} />
          </div>
        </div>

        {/* Installation Status */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                Installation
              </p>
              <p className={`text-xs mt-1 ${appInfo.isInstalled ? 'text-green-600' : 'text-gray-600'}`}>
                {appInfo.isInstalled ? 'Installed' : 'Web Version'}
              </p>
            </div>
            <Smartphone className={`h-8 w-8 ${appInfo.isInstalled ? 'text-green-500' : 'text-gray-400'}`} />
          </div>
        </div>

        {/* Push Notifications */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                Notifications
              </p>
              <p className={`text-xs mt-1 capitalize ${
                stats.pushNotifications?.permission === 'granted' ? 'text-green-600' :
                stats.pushNotifications?.permission === 'denied' ? 'text-red-600' : 'text-yellow-600'
              }`}>
                {stats.pushNotifications?.permission || 'Unknown'}
              </p>
            </div>
            <Bell className={`h-8 w-8 ${
              stats.pushNotifications?.permission === 'granted' ? 'text-green-500' :
              stats.pushNotifications?.permission === 'denied' ? 'text-red-500' : 'text-yellow-500'
            }`} />
          </div>
        </div>

        {/* Background Sync */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                Background Sync
              </p>
              <p className="text-xs mt-1 text-gray-600 dark:text-gray-400">
                {stats.backgroundSync?.total || 0} pending
              </p>
            </div>
            <Activity className={`h-8 w-8 ${
              stats.backgroundSync?.supported ? 'text-blue-500' : 'text-gray-400'
            }`} />
          </div>
        </div>
      </div>

      {/* Detailed Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Service Worker Status */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Service Worker
            </h3>
            <button
              onClick={forceServiceWorkerUpdate}
              className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
            >
              Check for Updates
            </button>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Supported</span>
              <div className="flex items-center space-x-2">
                {getStatusIcon(stats.serviceWorker?.supported)}
                <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(stats.serviceWorker?.supported)}`}>
                  {stats.serviceWorker?.supported ? 'Yes' : 'No'}
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Registered</span>
              <div className="flex items-center space-x-2">
                {getStatusIcon(stats.serviceWorker?.registered, stats.serviceWorker?.supported)}
                <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(stats.serviceWorker?.registered, stats.serviceWorker?.supported)}`}>
                  {stats.serviceWorker?.registered ? 'Yes' : 'No'}
                </span>
              </div>
            </div>

            {stats.serviceWorker?.version && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Version</span>
                <span className="text-sm font-mono text-gray-900 dark:text-white">
                  {stats.serviceWorker.version}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Cache Status */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Cache Storage
            </h3>
            <button
              onClick={clearAllCaches}
              className="text-sm text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300"
            >
              Clear All
            </button>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Total Caches</span>
              <span className="text-sm font-semibold text-gray-900 dark:text-white">
                {stats.cacheStats?.totalCaches || 0}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Total Items</span>
              <span className="text-sm font-semibold text-gray-900 dark:text-white">
                {stats.cacheStats?.totalItems || 0}
              </span>
            </div>

            {stats.cacheStats?.caches && stats.cacheStats.caches.length > 0 && (
              <div className="mt-4">
                <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                  Cache Details
                </h4>
                <div className="space-y-2">
                  {stats.cacheStats.caches.map((cache, index) => (
                    <div key={index} className="flex items-center justify-between text-xs">
                      <span className="text-gray-600 dark:text-gray-400 truncate">
                        {cache.name}
                      </span>
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 rounded-full ${
                          cache.type === 'static' ? 'bg-blue-100 text-blue-700' :
                          cache.type === 'dynamic' ? 'bg-green-100 text-green-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {cache.type}
                        </span>
                        <span className="text-gray-900 dark:text-white font-medium">
                          {cache.size}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Background Sync Details */}
      {stats.backgroundSync && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Background Sync Status
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {stats.backgroundSync.weather || 0}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Weather Requests
              </div>
            </div>

            <div className="text-center">
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                {stats.backgroundSync.preferences || 0}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Preference Updates
              </div>
            </div>

            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                {stats.backgroundSync.alerts || 0}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Alert Subscriptions
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PWAStatusDashboard;