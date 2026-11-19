// Service worker: nakon prvog učitavanja kuharica i igra rade bez interneta.
// Sve putanje su relativne pa radi i iz podmape na GitHub Pagesu.
const SPREMNIK = 'rucak-u-dva-v1';
const OSNOVA = [
  './', 'index.html', 'css/stil.css', 'manifest.webmanifest',
  'js/app.js', 'js/logika.js', 'js/pohrana.js', 'js/obitelj.js',
  'podaci/recepti.json', 'ikone/ikona.svg', 'ikone/ikona-180.png', 'ikone/ikona-512.png',
];

self.addEventListener('install', (ev) => {
  ev.waitUntil((async () => {
    const c = await caches.open(SPREMNIK);
    await c.addAll(OSNOVA);
    const recepti = await (await c.match('podaci/recepti.json')).json();
    await c.addAll(recepti.map((r) => `slike/${r.id}.svg`));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (ev) => {
  ev.waitUntil((async () => {
    for (const k of await caches.keys()) if (k !== SPREMNIK) await caches.delete(k);
    await self.clients.claim();
  })());
});

// Iz spremnika odmah, a u pozadini osvježi (stale-while-revalidate).
self.addEventListener('fetch', (ev) => {
  const req = ev.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== self.location.origin) return;
  ev.respondWith((async () => {
    const c = await caches.open(SPREMNIK);
    const kljuc = req.mode === 'navigate' ? new URL('index.html', self.registration.scope).href : req;
    const spremljeno = await c.match(kljuc, { ignoreSearch: true });
    const mreza = fetch(req).then((odg) => {
      if (odg && odg.ok && req.mode !== 'navigate') c.put(req, odg.clone());
      else if (odg && odg.ok) c.put(kljuc, odg.clone());
      return odg;
    }).catch(() => null);
    if (spremljeno) { ev.waitUntil(mreza); return spremljeno; }
    const odg = await mreza;
    return odg || new Response('Bez veze s internetom.', { status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
  })());
});
