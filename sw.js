// CineMaster TV - minimális service worker
//
// SZÁNDÉKOSAN nem gyorsítótároz semmit: ez egy élő TV alkalmazás, ahol a
// műsorrend (schedule JSON-ok) és a videólinkek folyamatosan változnak -
// egy agresszívan cache-elő service worker itt régi, lejárt adatokat
// szolgálna ki. Ennek a fájlnak csak annyi a szerepe, hogy a böngésző
// "telepíthetőnek" (PWA-nak) ismerje el az oldalt.

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
  // Egyszerű "network passthrough" - mindig a hálózatról kéri le, nincs cache.
  event.respondWith(fetch(event.request));
});
