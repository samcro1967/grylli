// static/js/register-sw.js

if ('serviceWorker' in navigator) {
  const basePath = window.location.pathname.split('/').slice(0, 2).join('/');
  navigator.serviceWorker.register(`${basePath}/service-worker.js`).catch(() => {});
}
