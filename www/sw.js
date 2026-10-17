/* Varnethryl v0.3.4+class-motion: complete offline asset precache for installation. */
const PREFIX = 'varnethryl-pwa-';
const CACHE = PREFIX + '0.3.4-class-motion1';
const PRECACHE = ["./assets/heroes/0.webp", "./assets/heroes/1.webp", "./assets/heroes/10.webp", "./assets/heroes/11.webp", "./assets/heroes/12.webp", "./assets/heroes/13.webp", "./assets/heroes/14.webp", "./assets/heroes/15.webp", "./assets/heroes/16.webp", "./assets/heroes/17.webp", "./assets/heroes/18.webp", "./assets/heroes/19.webp", "./assets/heroes/2.webp", "./assets/heroes/3.webp", "./assets/heroes/4.webp", "./assets/heroes/5.webp", "./assets/heroes/6.webp", "./assets/heroes/7.webp", "./assets/heroes/8.webp", "./assets/heroes/9.webp", "./assets/sprites/0.png", "./assets/sprites/1.png", "./assets/sprites/10.png", "./assets/sprites/11.png", "./assets/sprites/12.png", "./assets/sprites/13.png", "./assets/sprites/14.png", "./assets/sprites/15.png", "./assets/sprites/16.png", "./assets/sprites/17.png", "./assets/sprites/18.png", "./assets/sprites/19.png", "./assets/sprites/2.png", "./assets/sprites/3.png", "./assets/sprites/4.png", "./assets/sprites/5.png", "./assets/sprites/6.png", "./assets/sprites/7.png", "./assets/sprites/8.png", "./assets/sprites/9.png", "./assets/weapon-concepts/0.webp", "./assets/weapon-concepts/1.webp", "./assets/weapon-concepts/10.webp", "./assets/weapon-concepts/11.webp", "./assets/weapon-concepts/12.webp", "./assets/weapon-concepts/13.webp", "./assets/weapon-concepts/14.webp", "./assets/weapon-concepts/2.webp", "./assets/weapon-concepts/3.webp", "./assets/weapon-concepts/4.webp", "./assets/weapon-concepts/5.webp", "./assets/weapon-concepts/6.webp", "./assets/weapon-concepts/7.webp", "./assets/weapon-concepts/8.webp", "./assets/weapon-concepts/9.webp", "./assets/weapons/0.webp", "./assets/weapons/1.webp", "./assets/weapons/10.webp", "./assets/weapons/11.webp", "./assets/weapons/12.webp", "./assets/weapons/13.webp", "./assets/weapons/14.webp", "./assets/weapons/2.webp", "./assets/weapons/3.webp", "./assets/weapons/4.webp", "./assets/weapons/5.webp", "./assets/weapons/6.webp", "./assets/weapons/7.webp", "./assets/weapons/8.webp", "./assets/weapons/9.webp", "./controls.js", "./hud.js", "./hud-config.js", "./hud.css", "./fonts/Cinzel.woff", "./assets/hud/wordmark.png", "./data.js", "./game.js", "./icon-192.png", "./icon-512.png", "./icon-maskable-512.png", "./icon.svg", "./index.html", "./manifest.webmanifest", "./pwa.js", "./motion.js", "./classmotion.js", "./settings.js", "./skills.js", "./styles.css", "./sprites.js", "./assets/enemies/manifest.json", "./assets/enemies/ash-skeleton.png", "./assets/enemies/ashen-titan.png", "./assets/enemies/forest-raider.png", "./assets/enemies/frost-hound.png", "./assets/enemies/glacier-brute.png", "./assets/enemies/ice-wraith.png", "./assets/enemies/rune-sentinel.png", "./assets/enemies/vine-wraith.png", "./assets/enemies/wild-wolf.png"];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(PRECACHE)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(names => Promise.all(names.filter(name => (name.startsWith(PREFIX) && name !== CACHE) || name === 'varnethryl-v0.2.0').map(name => caches.delete(name)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin || !url.pathname.startsWith(new URL(self.registration.scope).pathname)) return;
  if (req.mode === 'navigate') {
    event.respondWith(fetch(req, {cache:'no-store'}).then(response => {
      if (response.ok) {const copy = response.clone(); caches.open(CACHE).then(cache => cache.put('./index.html',copy)).catch(() => {});}
      return response;
    }).catch(() => caches.match('./index.html')));
    return;
  }
  event.respondWith(caches.match(req).then(hit => hit || fetch(req).then(response => {
    if (response.ok && response.type === 'basic') {const copy = response.clone(); caches.open(CACHE).then(cache => cache.put(req,copy)).catch(() => {});}
    return response;
  })));
});
