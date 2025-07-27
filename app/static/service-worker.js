// ---------------------------------------------------------------------
// service-worker.js
// app/static/service-worker.js
// Dynamically caches static assets (CSS, JS, icons) for faster reloads
// ---------------------------------------------------------------------

const CACHE_NAME = "grylli-dynamic-v1";

// Activate event – clear old caches
self.addEventListener("activate", event => {
  console.log("[ServiceWorker] Activate");
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key)))
    )
  );
  self.clients.claim();
});

// Fetch event – cache matching static assets dynamically
self.addEventListener("fetch", event => {
  const req = event.request;
  const url = new URL(req.url);

  // Try to match static assets dynamically, without hardcoding /grylli
  if (url.pathname.includes("/static/")) {
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
