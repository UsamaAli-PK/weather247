import React, { useState } from 'react';
import { 
  Smartphone, 
  Monitor, 
  Chrome, 
  Download, 
  Share, 
  MoreVertical,
  Plus,
  Home,
  ChevronRight,
  X
} from 'lucide-react';

const PWAInstallGuide = ({ isOpen, onClose }) => {
  const [selectedPlatform, setSelectedPlatform] = useState('android');

  const platforms = {
    android: {
      name: 'Android (Chrome)',
      icon: <Chrome className="h-6 w-6" />,
      steps: [
        {
          icon: <Chrome className="h-5 w-5" />,
          title: 'Open Chrome Browser',
          description: 'Navigate to Weather247 in Google Chrome'
        },
        {
          icon: <MoreVertical className="h-5 w-5" />,
          title: 'Tap Menu',
          description: 'Tap the three dots menu in the top right corner'
        },
        {
          icon: <Download className="h-5 w-5" />,
          title: 'Add to Home Screen',
          description: 'Select "Add to Home screen" from the menu'
        },
        {
          icon: <Plus className="h-5 w-5" />,
          title: 'Confirm Installation',
          description: 'Tap "Add" to install Weather247 on your home screen'
        }
      ]
    },
    ios: {
      name: 'iPhone/iPad (Safari)',
      icon: <Smartphone className="h-6 w-6" />,
      steps: [
        {
          icon: <Smartphone className="h-5 w-5" />,
          title: 'Open Safari',
          description: 'Navigate to Weather247 in Safari browser'
        },
        {
          icon: <Share className="h-5 w-5" />,
          title: 'Tap Share Button',
          description: 'Tap the share button at the bottom of the screen'
        },
        {
          icon: <Home className="h-5 w-5" />,
          title: 'Add to Home Screen',
          description: 'Scroll down and tap "Add to Home Screen"'
        },
        {
          icon: <Plus className="h-5 w-5" />,
          title: 'Confirm Installation',
          description: 'Tap "Add" to install Weather247 on your home screen'
        }
      ]
    },
    desktop: {
      name: 'Desktop (Chrome/Edge)',
      icon: <Monitor className="h-6 w-6" />,
      steps: [
        {
          icon: <Monitor className="h-5 w-5" />,
          title: 'Open Browser',
          description: 'Navigate to Weather247 in Chrome, Edge, or another supported browser'
        },
        {
          icon: <Download className="h-5 w-5" />,
          title: 'Look for Install Prompt',
          description: 'Click the install button in the address bar or wait for the install prompt'
        },
        {
          icon: <Plus className="h-5 w-5" />,
          title: 'Click Install',
          description: 'Click "Install" in the prompt to add Weather247 to your desktop'
        },
        {
          icon: <Smartphone className="h-5 w-5" />,
          title: 'Launch App',
          description: 'Weather247 will now appear in your applications and can be launched like a native app'
        }
      ]
    }
  };

  const benefits = [
    {
      icon: <Download className="h-5 w-5 text-blue-500" />,
      title: 'Faster Loading',
      description: 'Instant access with cached content'
    },
    {
      icon: <Smartphone className="h-5 w-5 text-green-500" />,
      title: 'Native Experience',
      description: 'App-like interface and navigation'
    },
    {
      icon: <Home className="h-5 w-5 text-purple-500" />,
      title: 'Home Screen Access',
      description: 'Quick access from your device home screen'
    },
    {
      icon: <Monitor className="h-5 w-5 text-orange-500" />,
      title: 'Offline Support',
      description: 'Access weather data even without internet'
    }
  ];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Install Weather247
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Get the full app experience on your device
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Benefits */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Why Install Weather247?
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {benefits.map((benefit, index) => (
              <div key={index} className="flex items-start space-x-3">
                <div className="flex-shrink-0 mt-1">
                  {benefit.icon}
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 dark:text-white">
                    {benefit.title}
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {benefit.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Platform Selection */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Choose Your Platform
          </h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(platforms).map(([key, platform]) => (
              <button
                key={key}
                onClick={() => setSelectedPlatform(key)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg border transition-colors ${
                  selectedPlatform === key
                    ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                    : 'bg-white dark:bg-gray-700 border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
                }`}
              >
                {platform.icon}
                <span className="text-sm font-medium">{platform.name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Installation Steps */}
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Installation Steps for {platforms[selectedPlatform].name}
          </h3>
          
          <div className="space-y-4">
            {platforms[selectedPlatform].steps.map((step, index) => (
              <div key={index} className="flex items-start space-x-4">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center w-8 h-8 bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-full text-sm font-semibold">
                    {index + 1}
                  </div>
                </div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    {step.icon}
                    <h4 className="font-medium text-gray-900 dark:text-white">
                      {step.title}
                    </h4>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {step.description}
                  </p>
                </div>
                {index < platforms[selectedPlatform].steps.length - 1 && (
                  <div className="flex-shrink-0 mt-4">
                    <ChevronRight className="h-4 w-4 text-gray-400" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 bg-gray-50 dark:bg-gray-700/50 rounded-b-lg">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Need help? Contact our support team
            </div>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md transition-colors"
            >
              Got it!
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PWAInstallGuide;