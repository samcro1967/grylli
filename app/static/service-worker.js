// ---------------------------------------------------------------------
// service-worker.js
// app/static/service-worker.js
// Dynamically caches static assets (CSS, icons, etc.) — excludes JS
// ---------------------------------------------------------------------

const CACHE_VERSION = "v1.0.8"; // bump this on every deploy
const CACHE_NAME = `grylli-static-${CACHE_VERSION}`;

// Only cache non-JS assets
const shouldCache = url =>
  url.pathname.includes("/static/") &&
  !url.pathname.endsWith(".js") && // avoid caching JS
  !url.pathname.endsWith(".json"); // optional: skip import maps too

self.addEventListener("install", event => {
  console.log("[ServiceWorker] Install");
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  console.log("[ServiceWorker] Activate");
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", event => {
  const req = event.request;
  const url = new URL(req.url);

  // ✅ Only handle same-origin requests to avoid CSP connect-src violations
  if (url.origin !== location.origin) return;

  if (shouldCache(url)) {
    event.respondWith(
      caches.match(req).then(cached =>
        cached ||
        fetch(req).then(response => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(req, clone));
          return response;
        })
      )
    );
  } else {
    event.respondWith(fetch(req));
  }
});

