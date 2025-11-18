// src/entry-client.js
import { createApp } from './app'

function liveInternetHit() {
  try {
    var img = document.getElementById('licntE64E');
    if (!img) return;
    var s = window.screen;
    var doc = document;
    var url = String(location.pathname + location.search);
    var ref = doc.referrer || '';
    var title = (doc.title || '').substring(0, 150);
    var parts = [
      'https://counter.yadro.ru/hit?t44.15',
      ';r' + escape(ref),
      ';s' + s.width + '*' + s.height + '*' + (s.colorDepth ? s.colorDepth : s.pixelDepth),
      ';u' + escape(url),
      ';h' + escape(title),
      ';' + Math.random()
    ];
    img.src = parts.join('');
  } catch (_) { /* no-op */ }
}

const { app, router } = createApp(false)

// Track SPA navigations for LiveInternet
router.afterEach(() => {
  // Let title/meta updates settle
  setTimeout(liveInternetHit, 0);
});

router.isReady().then(() => {
  // Initial hit after hydration
  setTimeout(liveInternetHit, 0);
  app.mount('#app')
})
