import React from 'react';
import { ArrowLeft, Smartphone, Bell, Wifi, Download } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import PushNotificationManager from '../components/PushNotificationManager';
import { usePWA } from '../components/PWAManager';

const PWASettings = () => {
  const navigate = useNavigate();
  const { isOnline, appInfo } = usePWA();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate(-1)}
              className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                App Settings
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Manage your Weather247 app experience
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="space-y-8">
          {/* App Status */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              App Status
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="flex items-center space-x-3 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div className={`p-2 rounded-lg ${
                  isOnline 
                    ? 'bg-green-100 dark:bg-green-900/20' 
                    : 'bg-red-100 dark:bg-red-900/20'
                }`}>
                  <Wifi className={`h-5 w-5 ${
                    isOnline 
                      ? 'text-green-600 dark:text-green-400' 
                      : 'text-red-600 dark:text-red-400'
                  }`} />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    Connection
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {isOnline ? 'Online' : 'Offline'}
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-3 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div className={`p-2 rounded-lg ${
                  appInfo.isInstalled 
                    ? 'bg-green-100 dark:bg-green-900/20' 
                    : 'bg-gray-100 dark:bg-gray-700'
                }`}>
                  <Smartphone className={`h-5 w-5 ${
                    appInfo.isInstalled 
                      ? 'text-green-600 dark:text-green-400' 
                      : 'text-gray-600 dark:text-gray-400'
                  }`} />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    Installation
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {appInfo.isInstalled ? 'Installed' : 'Web Version'}
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-3 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div className={`p-2 rounded-lg ${
                  appInfo.notificationPermission === 'granted'
                    ? 'bg-green-100 dark:bg-green-900/20' 
                    : appInfo.notificationPermission === 'denied'
                    ? 'bg-red-100 dark:bg-red-900/20'
                    : 'bg-yellow-100 dark:bg-yellow-900/20'
                }`}>
                  <Bell className={`h-5 w-5 ${
                    appInfo.notificationPermission === 'granted'
                      ? 'text-green-600 dark:text-green-400' 
                      : appInfo.notificationPermission === 'denied'
                      ? 'text-red-600 dark:text-red-400'
                      : 'text-yellow-600 dark:text-yellow-400'
                  }`} />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    Notifications
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400 capitalize">
                    {appInfo.notificationPermission}
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-3 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div className={`p-2 rounded-lg ${
                  appInfo.isStandalone 
                    ? 'bg-blue-100 dark:bg-blue-900/20' 
                    : 'bg-gray-100 dark:bg-gray-700'
                }`}>
                  <Download className={`h-5 w-5 ${
                    appInfo.isStandalone 
                      ? 'text-blue-600 dark:text-blue-400' 
                      : 'text-gray-600 dark:text-gray-400'
                  }`} />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    Mode
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {appInfo.isStandalone ? 'Standalone' : 'Browser'}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Push Notifications */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Push Notifications
            </h2>
            <PushNotificationManager />
          </div>

          {/* App Information */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              App Information
            </h2>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b border-gray-200 dark:border-gray-700">
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  Version
                </span>
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  1.0.0
                </span>
              </div>
              
              <div className="flex justify-between items-center py-2 border-b border-gray-200 dark:border-gray-700">
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  Service Worker
                </span>
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {appInfo.serviceWorkerSupported ? 'Supported' : 'Not Supported'}
                </span>
              </div>
              
              <div className="flex justify-between items-center py-2 border-b border-gray-200 dark:border-gray-700">
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  Offline Support
                </span>
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {appInfo.serviceWorkerSupported ? 'Available' : 'Limited'}
                </span>
              </div>
              
              <div className="flex justify-between items-center py-2">
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  Install Prompt
                </span>
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {appInfo.canInstall ? 'Available' : 'Not Available'}
                </span>
              </div>
            </div>
          </div>

          {/* PWA Features */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Progressive Web App Features
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3">
                <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                  Available Features
                </h3>
                <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                  <li className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span>Offline weather data access</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span>Background data synchronization</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span>Push notifications for weather alerts</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span>App-like experience when installed</span>
                  </li>
                </ul>
              </div>
              
              <div className="space-y-3">
                <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                  Benefits
                </h3>
                <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                  <li className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span>Faster loading times</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span>Works without internet connection</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span>Native app-like interface</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span>Automatic updates</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PWASettings;