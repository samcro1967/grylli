const base = window.location.pathname.split('/')[1];  // gets 'grylli'
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register(`/${base}/static/sw.js`).catch(() => {});
}
