// 같은 출처 파일은 네트워크 우선(데이터 업데이트가 바로 반영됨), 오프라인이면 캐시를 쓴다.
const V = 'jp-pillgi-v4';
const ASSETS = ['./', 'index.html', 'poems.json', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(V).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(ks => Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k)))).then(() => self.clients.claim())
  );
});
self.addEventListener('fetch', e => {
  const r = e.request;
  if (r.method !== 'GET') return;
  const u = new URL(r.url);
  if (u.origin === location.origin) {
    e.respondWith(
      fetch(r).then(res => { const cp = res.clone(); caches.open(V).then(c => c.put(r, cp)); return res; })
        .catch(() => caches.match(r).then(m => m || caches.match('index.html')))
    );
  } else if (u.hostname.endsWith('googleapis.com') || u.hostname.endsWith('gstatic.com')) {
    // 글꼴은 한 번 받으면 캐시에서 쓴다
    e.respondWith(
      caches.match(r).then(m => m || fetch(r).then(res => { const cp = res.clone(); caches.open(V).then(c => c.put(r, cp)); return res; }))
    );
  }
});
