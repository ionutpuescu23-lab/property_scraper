const CACHE_NAME = 'alphadeals-shell-v1';

// Deliberately no install-time pre-cache: the "/" route is a dynamic App
// Router page, and Cache API's internal fetch doesn't send the same headers
// a real browser navigation does, which tripped a Next.js RSC rendering
// error (500) here in testing. The fetch handler below builds the cache
// organically from real navigations instead, which also suits a live
// investor dashboard better than serving stale pre-cached HTML.
self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))
    )
  );
  self.clients.claim();
});

// Network-first for navigation/API calls (this is a live investor dashboard,
// not content that should go stale) - only fall back to cache when offline.
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});
