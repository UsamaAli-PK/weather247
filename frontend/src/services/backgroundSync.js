// Background Sync Service for offline data synchronization
class BackgroundSyncService {
  constructor() {
    this.dbName = 'weather247-sync';
    this.dbVersion = 1;
    this.db = null;
    
    this.init();
  }

  async init() {
    await this.initIndexedDB();
    this.setupOnlineListener();
    console.log('Background Sync Service initialized');
  }

  // Initialize IndexedDB for storing pending sync requests
  async initIndexedDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);

      request.onerror = () => {
        console.error('Failed to open IndexedDB:', request.error);
        reject(request.error);
      };

      request.onsuccess = () => {
        this.db = request.result;
        console.log('IndexedDB opened successfully');
        resolve(this.db);
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        // Create object stores for different types of sync data
        if (!db.objectStoreNames.contains('weatherSync')) {
          const weatherStore = db.createObjectStore('weatherSync', { 
            keyPath: 'id', 
            autoIncrement: true 
          });
          weatherStore.createIndex('timestamp', 'timestamp', { unique: false });
          weatherStore.createIndex('city', 'city', { unique: false });
        }

        if (!db.objectStoreNames.contains('preferencesSync')) {
          const prefsStore = db.createObjectStore('preferencesSync', { 
            keyPath: 'id', 
            autoIncrement: true 
          });
          prefsStore.createIndex('timestamp', 'timestamp', { unique: false });
          prefsStore.createIndex('userId', 'userId', { unique: false });
        }

        if (!db.objectStoreNames.contains('alertsSync')) {
          const alertsStore = db.createObjectStore('alertsSync', { 
            keyPath: 'id', 
            autoIncrement: true 
          });
          alertsStore.createIndex('timestamp', 'timestamp', { unique: false });
        }

        console.log('IndexedDB schema created/updated');
      };
    });
  }

  // Set up listener for online/offline events
  setupOnlineListener() {
    window.addEventListener('online', () => {
      console.log('Device came online - triggering sync');
      this.syncAllPendingData();
    });

    window.addEventListener('offline', () => {
      console.log('Device went offline');
    });
  }

  // Queue weather data request for background sync
  async queueWeatherSync(city, requestData = {}) {
    if (!this.db) {
      console.warn('IndexedDB not available for background sync');
      return false;
    }

    try {
      const transaction = this.db.transaction(['weatherSync'], 'readwrite');
      const store = transaction.objectStore('weatherSync');

      const syncRequest = {
        type: 'weather',
        city: city,
        url: `/api/weather/${city}/`,
        method: 'GET',
        data: requestData,
        timestamp: Date.now(),
        retryCount: 0,
        maxRetries: 3
      };

      await store.add(syncRequest);
      console.log('Weather sync request queued for:', city);

      // Try to register background sync with service worker
      if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
        const registration = await navigator.serviceWorker.ready;
        await registration.sync.register('weather-sync');
        console.log('Background sync registered for weather data');
      }

      return true;
    } catch (error) {
      console.error('Failed to queue weather sync:', error);
      return false;
    }
  }

  // Queue user preferences sync
  async queuePreferencesSync(userId, preferences) {
    if (!this.db) {
      console.warn('IndexedDB not available for preferences sync');
      return false;
    }

    try {
      const transaction = this.db.transaction(['preferencesSync'], 'readwrite');
      const store = transaction.objectStore('preferencesSync');

      const syncRequest = {
        type: 'preferences',
        userId: userId,
        url: `/api/user/preferences/`,
        method: 'PUT',
        data: preferences,
        timestamp: Date.now(),
        retryCount: 0,
        maxRetries: 3
      };

      await store.add(syncRequest);
      console.log('Preferences sync request queued for user:', userId);

      // Register background sync
      if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
        const registration = await navigator.serviceWorker.ready;
        await registration.sync.register('preferences-sync');
        console.log('Background sync registered for preferences');
      }

      return true;
    } catch (error) {
      console.error('Failed to queue preferences sync:', error);
      return false;
    }
  }

  // Queue alert subscription sync
  async queueAlertSync(alertData) {
    if (!this.db) {
      console.warn('IndexedDB not available for alert sync');
      return false;
    }

    try {
      const transaction = this.db.transaction(['alertsSync'], 'readwrite');
      const store = transaction.objectStore('alertsSync');

      const syncRequest = {
        type: 'alert',
        url: `/api/alerts/`,
        method: 'POST',
        data: alertData,
        timestamp: Date.now(),
        retryCount: 0,
        maxRetries: 3
      };

      await store.add(syncRequest);
      console.log('Alert sync request queued');

      return true;
    } catch (error) {
      console.error('Failed to queue alert sync:', error);
      return false;
    }
  }

  // Get all pending sync requests
  async getPendingSyncRequests(type = null) {
    if (!this.db) {
      return [];
    }

    try {
      const stores = type ? [type + 'Sync'] : ['weatherSync', 'preferencesSync', 'alertsSync'];
      const allRequests = [];

      for (const storeName of stores) {
        if (this.db.objectStoreNames.contains(storeName)) {
          const transaction = this.db.transaction([storeName], 'readonly');
          const store = transaction.objectStore('weatherSync');
          const requests = await this.getAllFromStore(store);
          allRequests.push(...requests);
        }
      }

      return allRequests.sort((a, b) => a.timestamp - b.timestamp);
    } catch (error) {
      console.error('Failed to get pending sync requests:', error);
      return [];
    }
  }

  // Helper to get all records from a store
  getAllFromStore(store) {
    return new Promise((resolve, reject) => {
      const request = store.getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  // Sync all pending data when online
  async syncAllPendingData() {
    if (!navigator.onLine) {
      console.log('Device is offline, skipping sync');
      return;
    }

    console.log('Starting background sync of all pending data...');

    try {
      await Promise.all([
        this.syncWeatherData(),
        this.syncPreferencesData(),
        this.syncAlertData()
      ]);

      console.log('Background sync completed');
      
      // Notify components about sync completion
      window.dispatchEvent(new CustomEvent('background-sync-complete', {
        detail: { timestamp: Date.now() }
      }));

    } catch (error) {
      console.error('Background sync failed:', error);
    }
  }

  // Sync weather data
  async syncWeatherData() {
    if (!this.db) return;

    try {
      const transaction = this.db.transaction(['weatherSync'], 'readwrite');
      const store = transaction.objectStore('weatherSync');
      const requests = await this.getAllFromStore(store);

      for (const request of requests) {
        try {
          const response = await fetch(request.url, {
            method: request.method,
            headers: {
              'Content-Type': 'application/json',
            },
            body: request.data ? JSON.stringify(request.data) : undefined
          });

          if (response.ok) {
            // Sync successful, remove from queue
            await store.delete(request.id);
            console.log('Weather data synced for:', request.city);
            
            // Update cache with fresh data
            if ('caches' in window) {
              const cache = await caches.open('weather247-dynamic-v1');
              cache.put(request.url, response.clone());
            }
          } else {
            // Increment retry count
            request.retryCount++;
            if (request.retryCount >= request.maxRetries) {
              // Max retries reached, remove from queue
              await store.delete(request.id);
              console.warn('Max retries reached for weather sync:', request.city);
            } else {
              // Update retry count
              await store.put(request);
              console.log(`Weather sync retry ${request.retryCount}/${request.maxRetries} for:`, request.city);
            }
          }
        } catch (error) {
          console.error('Weather sync request failed:', error);
          
          // Increment retry count
          request.retryCount++;
          if (request.retryCount >= request.maxRetries) {
            await store.delete(request.id);
          } else {
            await store.put(request);
          }
        }
      }
    } catch (error) {
      console.error('Weather data sync failed:', error);
    }
  }

  // Sync preferences data
  async syncPreferencesData() {
    if (!this.db) return;

    try {
      const transaction = this.db.transaction(['preferencesSync'], 'readwrite');
      const store = transaction.objectStore('preferencesSync');
      const requests = await this.getAllFromStore(store);

      for (const request of requests) {
        try {
          const response = await fetch(request.url, {
            method: request.method,
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify(request.data)
          });

          if (response.ok) {
            await store.delete(request.id);
            console.log('Preferences synced for user:', request.userId);
          } else {
            request.retryCount++;
            if (request.retryCount >= request.maxRetries) {
              await store.delete(request.id);
              console.warn('Max retries reached for preferences sync:', request.userId);
            } else {
              await store.put(request);
            }
          }
        } catch (error) {
          console.error('Preferences sync request failed:', error);
          request.retryCount++;
          if (request.retryCount >= request.maxRetries) {
            await store.delete(request.id);
          } else {
            await store.put(request);
          }
        }
      }
    } catch (error) {
      console.error('Preferences data sync failed:', error);
    }
  }

  // Sync alert data
  async syncAlertData() {
    if (!this.db) return;

    try {
      const transaction = this.db.transaction(['alertsSync'], 'readwrite');
      const store = transaction.objectStore('alertsSync');
      const requests = await this.getAllFromStore(store);

      for (const request of requests) {
        try {
          const response = await fetch(request.url, {
            method: request.method,
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify(request.data)
          });

          if (response.ok) {
            await store.delete(request.id);
            console.log('Alert data synced');
          } else {
            request.retryCount++;
            if (request.retryCount >= request.maxRetries) {
              await store.delete(request.id);
            } else {
              await store.put(request);
            }
          }
        } catch (error) {
          console.error('Alert sync request failed:', error);
          request.retryCount++;
          if (request.retryCount >= request.maxRetries) {
            await store.delete(request.id);
          } else {
            await store.put(request);
          }
        }
      }
    } catch (error) {
      console.error('Alert data sync failed:', error);
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

  // Clear all sync data (for testing or reset)
  async clearAllSyncData() {
    if (!this.db) return;

    try {
      const transaction = this.db.transaction(['weatherSync', 'preferencesSync', 'alertsSync'], 'readwrite');
      
      await Promise.all([
        transaction.objectStore('weatherSync').clear(),
        transaction.objectStore('preferencesSync').clear(),
        transaction.objectStore('alertsSync').clear()
      ]);

      console.log('All sync data cleared');
    } catch (error) {
      console.error('Failed to clear sync data:', error);
    }
  }

  // Get sync statistics
  async getSyncStats() {
    if (!this.db) {
      return { weather: 0, preferences: 0, alerts: 0 };
    }

    try {
      const transaction = this.db.transaction(['weatherSync', 'preferencesSync', 'alertsSync'], 'readonly');
      
      const weatherCount = await this.getStoreCount(transaction.objectStore('weatherSync'));
      const preferencesCount = await this.getStoreCount(transaction.objectStore('preferencesSync'));
      const alertsCount = await this.getStoreCount(transaction.objectStore('alertsSync'));

      return {
        weather: weatherCount,
        preferences: preferencesCount,
        alerts: alertsCount,
        total: weatherCount + preferencesCount + alertsCount
      };
    } catch (error) {
      console.error('Failed to get sync stats:', error);
      return { weather: 0, preferences: 0, alerts: 0, total: 0 };
    }
  }

  // Helper to get count from store
  getStoreCount(store) {
    return new Promise((resolve, reject) => {
      const request = store.count();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }
}

// Create singleton instance
const backgroundSyncService = new BackgroundSyncService();

export default backgroundSyncService;