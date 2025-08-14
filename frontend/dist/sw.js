// Weather247 Service Worker
const CACHE_VERSION = '1.1.0';
const CACHE_NAME = `weather247-v${CACHE_VERSION}`;
const STATIC_CACHE_NAME = `weather247-static-v${CACHE_VERSION}`;
const DYNAMIC_CACHE_NAME = `weather247-dynamic-v${CACHE_VERSION}`;

// Static assets to cache
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/favicon.ico',
  // Add built assets - these will be updated during build
  '/assets/index.css',
  '/assets/index.js'
];

// API endpoints to cache
const API_CACHE_PATTERNS = [
  /\/api\/weather\//,
  /\/api\/cities\//,
  /\/api\/user\/preferences\//
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then((cache) => {
        console.log('Service Worker: Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('Service Worker: Static assets cached');
        // Don't skip waiting automatically - let the user decide
        console.log('Service Worker: Ready to activate');
      })
      .catch((error) => {
        console.error('Service Worker: Error caching static assets', error);
      })
  );
});



// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Handle API requests
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleAPIRequest(request));
    return;
  }

  // Handle static assets
  if (request.destination === 'document' || 
      request.destination === 'script' || 
      request.destination === 'style' ||
      request.destination === 'image') {
    event.respondWith(handleStaticRequest(request));
    return;
  }

  // Default: network first, then cache
  event.respondWith(
    fetch(request)
      .catch(() => caches.match(request))
  );
});

// Handle API requests with cache-first strategy for weather data
async function handleAPIRequest(request) {
  const url = new URL(request.url);
  
  // For weather data, use cache-first strategy
  if (API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname))) {
    try {
      const cache = await caches.open(DYNAMIC_CACHE_NAME);
      const cachedResponse = await cache.match(request);
      
      if (cachedResponse) {
        // Check if cached data is still fresh (within 10 minutes)
        const cachedDate = new Date(cachedResponse.headers.get('sw-cached-date'));
        const now = new Date();
        const isStale = (now - cachedDate) > (10 * 60 * 1000); // 10 minutes
        
        if (!isStale) {
          console.log('Service Worker: Serving from cache', request.url);
          return cachedResponse;
        }
      }
      
      // Fetch fresh data
      const networkResponse = await fetch(request);
      
      if (networkResponse.ok) {
        // Clone response and add timestamp
        const responseToCache = networkResponse.clone();
        const headers = new Headers(responseToCache.headers);
        headers.set('sw-cached-date', new Date().toISOString());
        
        const modifiedResponse = new Response(responseToCache.body, {
          status: responseToCache.status,
          statusText: responseToCache.statusText,
          headers: headers
        });
        
        // Cache the response
        cache.put(request, modifiedResponse.clone());
        console.log('Service Worker: Cached API response', request.url);
        
        return networkResponse;
      }
      
      // If network fails, return cached version if available
      if (cachedResponse) {
        console.log('Service Worker: Network failed, serving stale cache', request.url);
        return cachedResponse;
      }
      
      throw new Error('Network failed and no cache available');
      
    } catch (error) {
      console.error('Service Worker: API request failed', error);
      
      // Return offline response for weather data
      return new Response(JSON.stringify({
        error: 'Offline',
        message: 'Weather data unavailable offline',
        cached: false
      }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }
  
  // For other API requests, use network-first
  try {
    return await fetch(request);
  } catch (error) {
    const cache = await caches.open(DYNAMIC_CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      return cachedResponse;
    }
    
    throw error;
  }
}

// Handle static requests with cache-first strategy
async function handleStaticRequest(request) {
  try {
    const cache = await caches.open(STATIC_CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      console.log('Service Worker: Serving static asset from cache', request.url);
      return cachedResponse;
    }
    
    // Fetch from network and cache
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
      console.log('Service Worker: Cached static asset', request.url);
    }
    
    return networkResponse;
    
  } catch (error) {
    console.error('Service Worker: Static request failed', error);
    
    // For HTML requests, return a basic offline page
    if (request.destination === 'document') {
      return new Response(`
        <!DOCTYPE html>
        <html>
          <head>
            <title>Weather247 - Offline</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
              body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
              .offline { color: #666; }
            </style>
          </head>
          <body>
            <div class="offline">
              <h1>Weather247</h1>
              <p>You're currently offline. Please check your internet connection.</p>
              <p>Some cached weather data may still be available.</p>
            </div>
          </body>
        </html>
      `, {
        headers: { 'Content-Type': 'text/html' }
      });
    }
    
    throw error;
  }
}

// Background sync for when connectivity returns
self.addEventListener('sync', (event) => {
  console.log('Service Worker: Background sync triggered', event.tag);
  
  if (event.tag === 'weather-sync') {
    event.waitUntil(syncWeatherData());
  }
  
  if (event.tag === 'preferences-sync') {
    event.waitUntil(syncUserPreferences());
  }
});

// Sync weather data when online
async function syncWeatherData() {
  try {
    console.log('Service Worker: Syncing weather data...');
    
    // Get pending sync requests from IndexedDB
    const pendingRequests = await getPendingSyncRequests('weather');
    
    for (const request of pendingRequests) {
      try {
        const response = await fetch(request.url, request.options);
        if (response.ok) {
          // Update cache with fresh data
          const cache = await caches.open(DYNAMIC_CACHE_NAME);
          cache.put(request.url, response.clone());
          
          // Remove from pending sync
          await removePendingSyncRequest('weather', request.id);
          
          console.log('Service Worker: Synced weather data for', request.url);
        }
      } catch (error) {
        console.error('Service Worker: Failed to sync weather data', error);
      }
    }
    
    // Notify clients about sync completion
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
      client.postMessage({
        type: 'SYNC_COMPLETE',
        data: { syncType: 'weather' }
      });
    });
    
  } catch (error) {
    console.error('Service Worker: Weather sync failed', error);
  }
}

// Sync user preferences when online
async function syncUserPreferences() {
  try {
    console.log('Service Worker: Syncing user preferences...');
    
    const pendingRequests = await getPendingSyncRequests('preferences');
    
    for (const request of pendingRequests) {
      try {
        const response = await fetch(request.url, request.options);
        if (response.ok) {
          await removePendingSyncRequest('preferences', request.id);
          console.log('Service Worker: Synced preferences for', request.url);
        }
      } catch (error) {
        console.error('Service Worker: Failed to sync preferences', error);
      }
    }
    
  } catch (error) {
    console.error('Service Worker: Preferences sync failed', error);
  }
}

// Helper functions for IndexedDB operations
async function getPendingSyncRequests(type) {
  // This would typically use IndexedDB to store pending requests
  // For now, return empty array - will be implemented with background sync
  return [];
}

async function removePendingSyncRequest(type, id) {
  // Remove completed sync request from IndexedDB
  console.log(`Service Worker: Removing pending sync request ${type}:${id}`);
}

// Push notification handling
self.addEventListener('push', (event) => {
  console.log('Service Worker: Push notification received');
  
  const options = {
    body: 'Weather alert or update available',
    icon: '/favicon.ico',
    badge: '/favicon.ico',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'View Weather',
        icon: '/favicon.ico'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/favicon.ico'
      }
    ]
  };
  
  if (event.data) {
    const data = event.data.json();
    options.body = data.body || options.body;
    options.title = data.title || 'Weather247';
  }
  
  event.waitUntil(
    self.registration.showNotification('Weather247', options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  console.log('Service Worker: Notification clicked', event.action);
  
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Handle messages from the main thread
self.addEventListener('message', (event) => {
  console.log('Service Worker: Message received', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    console.log('Service Worker: Skipping waiting...');
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({ version: CACHE_VERSION });
  }
});

// Notify clients when a new service worker is ready
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating...');
  
  event.waitUntil(
    Promise.all([
      // Clean up old caches
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== STATIC_CACHE_NAME && 
                cacheName !== DYNAMIC_CACHE_NAME &&
                cacheName !== CACHE_NAME) {
              console.log('Service Worker: Deleting old cache', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      }),
      
      // Take control of all clients
      self.clients.claim()
    ]).then(() => {
      console.log('Service Worker: Activated');
      
      // Notify all clients that the service worker is ready
      return self.clients.matchAll();
    }).then((clients) => {
      clients.forEach(client => {
        client.postMessage({
          type: 'SW_ACTIVATED',
          version: CACHE_VERSION
        });
      });
    })
  );
});

console.log('Service Worker: Loaded', { version: CACHE_VERSION });