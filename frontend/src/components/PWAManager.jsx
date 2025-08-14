import React, { useState, useEffect } from 'react';
import { Wifi, WifiOff, Download, Bell, RefreshCw, AlertCircle } from 'lucide-react';
import PWAInstallPrompt from './PWAInstallPrompt';
import PWAUpdateNotification from './PWAUpdateNotification';
import PushNotificationManager from './PushNotificationManager';
import pwaService from '../services/pwaService';
import backgroundSyncService from '../services/backgroundSync';

const PWAManager = ({ children }) => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [showUpdatePrompt, setShowUpdatePrompt] = useState(false);
  const [syncStats, setSyncStats] = useState({ total: 0 });
  const [appInfo, setAppInfo] = useState(pwaService.getAppInfo());
  const [lastSyncTime, setLastSyncTime] = useState(null);

  useEffect(() => {
    // Online/offline status
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // PWA update available
    const handleUpdateAvailable = (event) => {
      setShowUpdatePrompt(true);
    };

    // Background sync completion
    const handleSyncComplete = (event) => {
      setLastSyncTime(new Date());
      updateSyncStats();
    };

    // Data sync events
    const handleDataSynced = (event) => {
      console.log('Data synced:', event.detail);
      updateSyncStats();
    };

    window.addEventListener('pwa-update-available', handleUpdateAvailable);
    window.addEventListener('background-sync-complete', handleSyncComplete);
    window.addEventListener('pwa-data-synced', handleDataSynced);

    // Initial sync stats
    updateSyncStats();

    // Update app info periodically
    const infoInterval = setInterval(() => {
      setAppInfo(pwaService.getAppInfo());
    }, 5000);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('pwa-update-available', handleUpdateAvailable);
      window.removeEventListener('background-sync-complete', handleSyncComplete);
      window.removeEventListener('pwa-data-synced', handleDataSynced);
      clearInterval(infoInterval);
    };
  }, []);

  const updateSyncStats = async () => {
    try {
      const stats = await backgroundSyncService.getSyncStats();
      setSyncStats(stats);
    } catch (error) {
      console.error('Failed to get sync stats:', error);
    }
  };

  const handleUpdateApp = () => {
    window.location.reload();
  };

  const handleDismissUpdate = () => {
    setShowUpdatePrompt(false);
  };

  const handleManualSync = async () => {
    if (!isOnline) {
      console.log('Cannot sync while offline');
      return;
    }

    try {
      await backgroundSyncService.syncAllPendingData();
      setLastSyncTime(new Date());
    } catch (error) {
      console.error('Manual sync failed:', error);
    }
  };

  return (
    <div className="relative">
      {/* Main App Content */}
      {children}

      {/* PWA Status Bar */}
      <div className="fixed top-0 left-0 right-0 z-40">
        {/* Offline Indicator */}
        {!isOnline && (
          <div className="bg-yellow-500 text-white px-4 py-2 text-sm text-center">
            <div className="flex items-center justify-center space-x-2">
              <WifiOff className="h-4 w-4" />
              <span>You're offline. Some features may be limited.</span>
              {syncStats.total > 0 && (
                <span className="bg-yellow-600 px-2 py-1 rounded text-xs">
                  {syncStats.total} items pending sync
                </span>
              )}
            </div>
          </div>
        )}

        {/* Update Available Prompt */}
        {showUpdatePrompt && (
          <div className="bg-blue-600 text-white px-4 py-2 text-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Download className="h-4 w-4" />
                <span>A new version of Weather247 is available!</span>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleUpdateApp}
                  className="bg-blue-700 hover:bg-blue-800 px-3 py-1 rounded text-xs font-medium transition-colors"
                >
                  Update
                </button>
                <button
                  onClick={handleDismissUpdate}
                  className="text-blue-200 hover:text-white px-2 py-1 text-xs transition-colors"
                >
                  Later
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* PWA Install Prompt */}
      <PWAInstallPrompt />

      {/* PWA Update Notification */}
      <PWAUpdateNotification />

      {/* PWA Status Panel (for debugging/admin) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="fixed bottom-20 right-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 shadow-lg max-w-sm text-xs">
          <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
            PWA Status
          </h4>
          
          <div className="space-y-1 text-gray-600 dark:text-gray-400">
            <div className="flex justify-between">
              <span>Online:</span>
              <span className={isOnline ? 'text-green-600' : 'text-red-600'}>
                {isOnline ? 'Yes' : 'No'}
              </span>
            </div>
            
            <div className="flex justify-between">
              <span>Installed:</span>
              <span className={appInfo.isInstalled ? 'text-green-600' : 'text-gray-400'}>
                {appInfo.isInstalled ? 'Yes' : 'No'}
              </span>
            </div>
            
            <div className="flex justify-between">
              <span>Standalone:</span>
              <span className={appInfo.isStandalone ? 'text-green-600' : 'text-gray-400'}>
                {appInfo.isStandalone ? 'Yes' : 'No'}
              </span>
            </div>
            
            <div className="flex justify-between">
              <span>Notifications:</span>
              <span className={
                appInfo.notificationPermission === 'granted' 
                  ? 'text-green-600' 
                  : appInfo.notificationPermission === 'denied'
                  ? 'text-red-600'
                  : 'text-yellow-600'
              }>
                {appInfo.notificationPermission}
              </span>
            </div>
            
            <div className="flex justify-between">
              <span>Pending Sync:</span>
              <span>{syncStats.total || 0}</span>
            </div>
            
            {lastSyncTime && (
              <div className="flex justify-between">
                <span>Last Sync:</span>
                <span>{lastSyncTime.toLocaleTimeString()}</span>
              </div>
            )}
          </div>

          {isOnline && syncStats.total > 0 && (
            <button
              onClick={handleManualSync}
              className="mt-2 w-full bg-blue-600 hover:bg-blue-700 text-white text-xs py-1 px-2 rounded transition-colors flex items-center justify-center space-x-1"
            >
              <RefreshCw className="h-3 w-3" />
              <span>Sync Now</span>
            </button>
          )}
        </div>
      )}

      {/* Connection Status Indicator */}
      <div className="fixed bottom-4 left-4 z-30">
        <div className={`flex items-center space-x-2 px-3 py-2 rounded-full text-xs font-medium transition-all duration-300 ${
          isOnline 
            ? 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-200 border border-green-200 dark:border-green-800'
            : 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-200 border border-red-200 dark:border-red-800'
        }`}>
          {isOnline ? (
            <>
              <Wifi className="h-3 w-3" />
              <span>Online</span>
            </>
          ) : (
            <>
              <WifiOff className="h-3 w-3" />
              <span>Offline</span>
            </>
          )}
          
          {syncStats.total > 0 && (
            <span className="bg-current text-white px-1.5 py-0.5 rounded-full text-xs">
              {syncStats.total}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

// Hook for using PWA features in components
export const usePWA = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [appInfo, setAppInfo] = useState(pwaService.getAppInfo());

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    const interval = setInterval(() => {
      setAppInfo(pwaService.getAppInfo());
    }, 5000);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(interval);
    };
  }, []);

  return {
    isOnline,
    appInfo,
    pwaService,
    backgroundSyncService,
    
    // Helper methods
    getCachedWeatherData: pwaService.getCachedWeatherData.bind(pwaService),
    queueWeatherSync: backgroundSyncService.queueWeatherSync.bind(backgroundSyncService),
    queuePreferencesSync: backgroundSyncService.queuePreferencesSync.bind(backgroundSyncService),
    requestNotificationPermission: pwaService.requestNotificationPermission.bind(pwaService)
  };
};

export default PWAManager;