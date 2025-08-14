// PWA Service for managing Progressive Web App features
class PWAService {
  constructor() {
    this.deferredPrompt = null;
    this.isInstalled = false;
    this.isStandalone = false;
    this.serviceWorker = null;
    
    this.init();
  }

  async init() {
    // Check if app is running in standalone mode
    this.isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
                       window.navigator.standalone === true;

    // Check if app is already installed
    this.isInstalled = this.isStandalone || 
                      localStorage.getItem('pwa-installed') === 'true';

    // Register service worker
    await this.registerServiceWorker();

    // Set up installation prompt handling
    this.setupInstallPrompt();

    // Set up service worker messaging
    this.setupServiceWorkerMessaging();

    console.log('PWA Service initialized', {
      isInstalled: this.isInstalled,
      isStandalone: this.isStandalone,
      serviceWorkerSupported: 'serviceWorker' in navigator
    });
  }

  async registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js', {
          scope: '/'
        });

        console.log('Service Worker registered successfully:', registration);

        // Handle service worker updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New service worker is available
              this.notifyUpdate(newWorker);
            }
          });
        });

        // Listen for service worker messages
        navigator.serviceWorker.addEventListener('message', (event) => {
          const { type, version } = event.data;
          
          if (type === 'SW_ACTIVATED') {
            console.log('PWA: Service worker activated', { version });
            window.dispatchEvent(new CustomEvent('pwa-sw-activated', {
              detail: { version }
            }));
          }
        });

        this.serviceWorker = registration;
        return registration;

      } catch (error) {
        console.error('Service Worker registration failed:', error);
        throw error;
      }
    } else {
      console.warn('Service Workers not supported');
      return null;
    }
  }

  setupInstallPrompt() {
    // Listen for the beforeinstallprompt event
    window.addEventListener('beforeinstallprompt', (event) => {
      console.log('PWA: Install prompt available');
      
      // Prevent the mini-infobar from appearing on mobile
      event.preventDefault();
      
      // Save the event so it can be triggered later
      this.deferredPrompt = event;
      
      // Show custom install button/banner
      this.showInstallPrompt();
    });

    // Listen for app installed event
    window.addEventListener('appinstalled', (event) => {
      console.log('PWA: App was installed');
      this.isInstalled = true;
      localStorage.setItem('pwa-installed', 'true');
      this.hideInstallPrompt();
      
      // Track installation
      this.trackInstallation();
    });
  }

  setupServiceWorkerMessaging() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('message', (event) => {
        const { type, data } = event.data;
        
        switch (type) {
          case 'SYNC_COMPLETE':
            console.log('PWA: Background sync completed', data);
            this.notifyDataSync(data);
            break;
            
          case 'CACHE_UPDATED':
            console.log('PWA: Cache updated', data);
            break;
            
          default:
            console.log('PWA: Service worker message', event.data);
        }
      });
    }
  }

  // Show custom install prompt
  showInstallPrompt() {
    if (this.isInstalled || !this.deferredPrompt) {
      return;
    }

    // Dispatch custom event for components to listen to
    window.dispatchEvent(new CustomEvent('pwa-install-available', {
      detail: {
        canInstall: true,
        install: () => this.promptInstall()
      }
    }));
  }

  // Hide install prompt
  hideInstallPrompt() {
    window.dispatchEvent(new CustomEvent('pwa-install-hidden'));
  }

  // Trigger installation prompt
  async promptInstall() {
    if (!this.deferredPrompt) {
      console.warn('PWA: No install prompt available');
      return false;
    }

    try {
      // Show the install prompt
      this.deferredPrompt.prompt();
      
      // Wait for the user to respond to the prompt
      const { outcome } = await this.deferredPrompt.userChoice;
      
      console.log('PWA: Install prompt outcome:', outcome);
      
      if (outcome === 'accepted') {
        console.log('PWA: User accepted the install prompt');
        return true;
      } else {
        console.log('PWA: User dismissed the install prompt');
        return false;
      }
      
    } catch (error) {
      console.error('PWA: Error showing install prompt:', error);
      return false;
    } finally {
      // Clear the deferredPrompt
      this.deferredPrompt = null;
    }
  }

  // Check if installation is available
  canInstall() {
    return !this.isInstalled && this.deferredPrompt !== null;
  }

  // Request background sync
  async requestBackgroundSync(tag) {
    if (this.serviceWorker && 'sync' in window.ServiceWorkerRegistration.prototype) {
      try {
        await this.serviceWorker.sync.register(tag);
        console.log('PWA: Background sync requested:', tag);
        return true;
      } catch (error) {
        console.error('PWA: Background sync request failed:', error);
        return false;
      }
    }
    return false;
  }

  // Request push notification permission
  async requestNotificationPermission() {
    if (!('Notification' in window)) {
      console.warn('PWA: Notifications not supported');
      return false;
    }

    if (Notification.permission === 'granted') {
      return true;
    }

    if (Notification.permission === 'denied') {
      console.warn('PWA: Notification permission denied');
      return false;
    }

    try {
      const permission = await Notification.requestPermission();
      console.log('PWA: Notification permission:', permission);
      
      if (permission === 'granted') {
        await this.subscribeToPushNotifications();
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('PWA: Error requesting notification permission:', error);
      return false;
    }
  }

  // Subscribe to push notifications
  async subscribeToPushNotifications() {
    if (!this.serviceWorker) {
      console.warn('PWA: Service worker not available for push notifications');
      return null;
    }

    try {
      // This would typically use your VAPID keys
      const subscription = await this.serviceWorker.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlBase64ToUint8Array(
          // Replace with your actual VAPID public key
          'BEl62iUYgUivxIkv69yViEuiBIa40HI80NM9LdNnC_NNPJ6Ck96SUBBj2lOjHqyz2XJbdHiGhGWw5Ej5QmYSjMc'
        )
      });

      console.log('PWA: Push subscription created:', subscription);
      
      // Send subscription to server
      await this.sendSubscriptionToServer(subscription);
      
      return subscription;
    } catch (error) {
      console.error('PWA: Error subscribing to push notifications:', error);
      return null;
    }
  }

  // Convert VAPID key
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

  // Send subscription to server
  async sendSubscriptionToServer(subscription) {
    try {
      const response = await fetch('/api/push-subscription/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken()
        },
        body: JSON.stringify({
          subscription: subscription.toJSON(),
          user_agent: navigator.userAgent
        })
      });

      if (response.ok) {
        console.log('PWA: Push subscription sent to server');
        return true;
      } else {
        console.error('PWA: Failed to send push subscription to server');
        return false;
      }
    } catch (error) {
      console.error('PWA: Error sending push subscription to server:', error);
      return false;
    }
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

  // Check if app is online
  isOnline() {
    return navigator.onLine;
  }

  // Get cached weather data
  async getCachedWeatherData(city) {
    if (!('caches' in window)) {
      return null;
    }

    try {
      const cache = await caches.open('weather247-dynamic-v1');
      const response = await cache.match(`/api/weather/${city}/`);
      
      if (response) {
        const data = await response.json();
        const cachedDate = new Date(response.headers.get('sw-cached-date'));
        
        return {
          ...data,
          cached: true,
          cachedAt: cachedDate.toISOString(),
          isStale: (Date.now() - cachedDate.getTime()) > (10 * 60 * 1000)
        };
      }
      
      return null;
    } catch (error) {
      console.error('PWA: Error getting cached weather data:', error);
      return null;
    }
  }

  // Notify about service worker update
  notifyUpdate(newWorker = null) {
    window.dispatchEvent(new CustomEvent('pwa-update-available', {
      detail: {
        newWorker,
        reload: () => window.location.reload()
      }
    }));
  }

  // Get service worker version
  async getServiceWorkerVersion() {
    if (!this.serviceWorker) return null;

    try {
      const messageChannel = new MessageChannel();
      
      return new Promise((resolve) => {
        messageChannel.port1.onmessage = (event) => {
          resolve(event.data.version);
        };

        navigator.serviceWorker.controller?.postMessage(
          { type: 'GET_VERSION' },
          [messageChannel.port2]
        );

        // Timeout after 1 second
        setTimeout(() => resolve(null), 1000);
      });
    } catch (error) {
      console.error('PWA: Error getting service worker version:', error);
      return null;
    }
  }

  // Notify about data sync
  notifyDataSync(data) {
    window.dispatchEvent(new CustomEvent('pwa-data-synced', {
      detail: data
    }));
  }

  // Track installation for analytics
  trackInstallation() {
    // This would typically send analytics data
    console.log('PWA: Installation tracked');
    
    // You could send this to your analytics service
    if (window.gtag) {
      window.gtag('event', 'pwa_install', {
        event_category: 'PWA',
        event_label: 'App Installed'
      });
    }
  }

  // Get app info
  getAppInfo() {
    return {
      isInstalled: this.isInstalled,
      isStandalone: this.isStandalone,
      canInstall: this.canInstall(),
      isOnline: this.isOnline(),
      notificationPermission: 'Notification' in window ? Notification.permission : 'not-supported',
      serviceWorkerSupported: 'serviceWorker' in navigator
    };
  }
}

// Create singleton instance
const pwaService = new PWAService();

export default pwaService;