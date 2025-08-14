import React, { useState, useEffect } from 'react';
import { Download, X, RefreshCw } from 'lucide-react';

const PWAUpdateNotification = () => {
  const [showUpdate, setShowUpdate] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [newWorker, setNewWorker] = useState(null);

  useEffect(() => {
    // Listen for service worker updates
    const handleUpdateAvailable = (event) => {
      setNewWorker(event.detail.newWorker);
      setShowUpdate(true);
    };

    const handleUpdateReady = () => {
      setShowUpdate(true);
    };

    window.addEventListener('pwa-update-available', handleUpdateAvailable);
    window.addEventListener('pwa-update-ready', handleUpdateReady);

    // Check for existing service worker updates
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.getRegistration().then((registration) => {
        if (registration && registration.waiting) {
          setNewWorker(registration.waiting);
          setShowUpdate(true);
        }
      });
    }

    return () => {
      window.removeEventListener('pwa-update-available', handleUpdateAvailable);
      window.removeEventListener('pwa-update-ready', handleUpdateReady);
    };
  }, []);

  const handleUpdate = async () => {
    if (!newWorker) {
      // Fallback: reload the page
      window.location.reload();
      return;
    }

    setIsUpdating(true);

    try {
      // Tell the new service worker to skip waiting
      newWorker.postMessage({ type: 'SKIP_WAITING' });

      // Listen for the controlling service worker change
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        // Reload the page to get the new version
        window.location.reload();
      });

    } catch (error) {
      console.error('Error updating service worker:', error);
      // Fallback: reload the page
      window.location.reload();
    }
  };

  const handleDismiss = () => {
    setShowUpdate(false);
    // Remember dismissal for this session
    sessionStorage.setItem('pwa-update-dismissed', 'true');
  };

  const handleRemindLater = () => {
    setShowUpdate(false);
    // Show again after 1 hour
    setTimeout(() => {
      if (!sessionStorage.getItem('pwa-update-dismissed')) {
        setShowUpdate(true);
      }
    }, 60 * 60 * 1000); // 1 hour
  };

  if (!showUpdate) {
    return null;
  }

  return (
    <div className="fixed top-4 left-4 right-4 md:left-auto md:right-4 md:max-w-md z-50">
      <div className="bg-blue-600 text-white rounded-lg shadow-lg p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-2">
            <div className="bg-blue-700 p-2 rounded-lg">
              <Download className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-semibold text-sm">
                Update Available
              </h3>
              <p className="text-xs text-blue-100">
                A new version of Weather247 is ready
              </p>
            </div>
          </div>
          <button
            onClick={handleDismiss}
            className="text-blue-200 hover:text-white transition-colors"
            aria-label="Dismiss update notification"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-2 mb-4">
          <div className="flex items-center space-x-2 text-xs text-blue-100">
            <div className="w-1 h-1 bg-blue-300 rounded-full"></div>
            <span>Bug fixes and improvements</span>
          </div>
          <div className="flex items-center space-x-2 text-xs text-blue-100">
            <div className="w-1 h-1 bg-blue-300 rounded-full"></div>
            <span>Enhanced performance</span>
          </div>
          <div className="flex items-center space-x-2 text-xs text-blue-100">
            <div className="w-1 h-1 bg-blue-300 rounded-full"></div>
            <span>New features</span>
          </div>
        </div>

        <div className="flex space-x-2">
          <button
            onClick={handleUpdate}
            disabled={isUpdating}
            className="flex-1 bg-white hover:bg-blue-50 disabled:bg-blue-100 text-blue-600 text-sm font-medium py-2 px-3 rounded-md transition-colors flex items-center justify-center space-x-1"
          >
            {isUpdating ? (
              <>
                <RefreshCw className="h-3 w-3 animate-spin" />
                <span>Updating...</span>
              </>
            ) : (
              <>
                <Download className="h-3 w-3" />
                <span>Update Now</span>
              </>
            )}
          </button>
          <button
            onClick={handleRemindLater}
            className="px-3 py-2 text-sm text-blue-200 hover:text-white transition-colors"
          >
            Later
          </button>
        </div>
      </div>
    </div>
  );
};

export default PWAUpdateNotification;