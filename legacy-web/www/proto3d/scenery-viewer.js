/* Scenery preview: pick any tree / bush / flower / rock / prop variant and colour set, compare all colour sets, or scatter a random mix. */
import * as THREE from './vendor/three.module.js';
import { CATALOG, KINDS, makeVariant, makeDetailTexture, makeMaterials, scatterWorld } from './scenery.js';
const Q = new URLSearchParams(location.search), bare = Q.get('bare') != null;
const canvas = document.getElementById('c'), ui = document.getElementById('ui'), info = document.getElementById('info');
if (bare) ui.style.display = 'none';
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true }); renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2)); renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFShadowMap;
const scene = new THREE.Scene(); scene.background = new THREE.Color(0xbcd4e8); scene.fog = new THREE.Fog(0xcfe0ec, 40, 120);
const camera = new THREE.PerspectiveCamera(42, 1, .1, 200);
scene.add(new THREE.HemisphereLight(0xcfe6ff, 0x6a7a4a, 1.25));
const sun = new THREE.DirectionalLight(0xfff0d0, 2.2); sun.position.set(-8, 14, 9); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -22, right: 22, top: 22, bottom: -22, near: 1, far: 60 }); sun.shadow.bias = -.0006; sun.shadow.normalBias = .03; scene.add(sun, sun.target);
const ground = new THREE.Mesh(new THREE.CircleGeometry(300, 48), new THREE.MeshLambertMaterial({ color: 0x5c9a45 })); ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
const tex = makeDetailTexture(), MAT = makeMaterials(tex);
let content = new THREE.Group(); scene.add(content);
const st = { kind: Q.get('c') || 'trees', name: Q.get('v') || null, pal: Q.get('p') || null, all: Q.get('all') != null, scatter: Q.get('scatter') != null, seed: +(Q.get('seed') || 1), yaw: +(Q.get('yaw') || .6), pitch: +(Q.get('pitch') || .3), dist: +(Q.get('dist') || 0), tx: 0, ty: 1.5, tz: 0 };
if (!CATALOG[st.kind]) st.kind = 'trees';
if (!st.name || !CATALOG[st.kind][st.name]) st.name = Object.keys(CATALOG[st.kind])[0];
function clearContent() { scene.remove(content); content.traverse(o => { if (o.geometry) o.geometry.dispose(); }); content = new THREE.Group(); scene.add(content); }
function addVariant(v, x, z, ry, sc) {
  const m = new THREE.Mesh(v.geo, MAT.solid); m.position.set(x, 0, z); m.rotation.y = ry; m.scale.setScalar(sc || 1); m.castShadow = m.receiveShadow = true; content.add(m);
  if (v.glow) { const g = new THREE.Mesh(v.glow, MAT.glow); g.position.copy(m.position); g.rotation.y = ry; g.scale.setScalar(sc || 1); content.add(g); }
}
let lastInfo = '';
function rebuild() {
  clearContent();
  let tris = 0, label;
  if (st.scatter) {
    let s = st.seed * 9301 + 49297; const rnd = () => (s = (s * 16807) % 2147483647) / 2147483647;
    const sc = scatterWorld({ world: 32, colliders: [], rnd, trees: 60, bushes: 50, rocks: 34, flowers: 70, grass: 260, forest: 60 });
    for (const [g, m, cast] of [[sc.cast, MAT.solid, true], [sc.plain, MAT.solid, false], [sc.glow, MAT.glow, false]]) if (g) { const me = new THREE.Mesh(g, m); me.castShadow = cast; me.receiveShadow = true; me.frustumCulled = false; content.add(me); }
    tris = sc.tris; label = 'scatter seed ' + st.seed + ' · ' + sc.variants + ' variants · ' + sc.stats.trees + ' trees, ' + sc.stats.bushes + ' bushes, ' + sc.stats.flowers + ' flowers, ' + sc.stats.rocks + ' rocks';
    st.ty = 1.5; st.fit = Math.max(12, +(Q.get('dist') || 26));
  } else {
    const e = CATALOG[st.kind][st.name], pals = st.all ? e.pals : [st.pal && e.pals.includes(st.pal) ? st.pal : e.pals[0]], gap = st.kind === 'trees' ? 4.2 : st.kind === 'props' ? 2.6 : st.kind === 'flowers' ? 1.2 : 1.8;
    let maxH = 1;
    pals.forEach((p, i) => { const v = makeVariant(st.kind, st.name, p, st.seed); tris += v.tris; maxH = Math.max(maxH, v.h); addVariant(v, (i - (pals.length - 1) / 2) * gap, 0, 0, 1); });
    label = st.kind + '/' + st.name + ' · ' + (st.all ? 'all ' + pals.length + ' colour sets' : pals[0]) + ' · ~' + Math.round(tris / pals.length) + ' triangles each · seed ' + st.seed;
    st.ty = maxH * .45; st.fit = Math.max(st.kind === 'flowers' ? 1.7 : 3.2, maxH * 2.3, pals.length * gap * .95);
  }
  if (!st.dist) st.dist = st.fit; else if (st.scatter) st.dist = st.fit;
  info.textContent = label; window.__sceneryInfo = { label, tris };
  refreshUI(); window.__ready = true;
}
function refreshUI() {
  if (bare) return; ui.innerHTML = '';
  const row = () => { const r = document.createElement('div'); r.className = 'row'; ui.appendChild(r); return r; };
  const btn = (r, t, on, fn) => { const b = document.createElement('button'); b.textContent = t; if (on) b.className = 'on'; b.onclick = fn; r.appendChild(b); };
  const r1 = row(); KINDS.forEach(k => btn(r1, k, !st.scatter && st.kind === k, () => { st.kind = k; st.name = Object.keys(CATALOG[k])[0]; st.pal = null; st.scatter = false; st.dist = 0; rebuild(); }));
  btn(r1, 'SCATTER mix', st.scatter, () => { st.scatter = true; st.dist = 26; rebuild(); });
  if (st.scatter) { const r = row(); btn(r, 'new random mix', false, () => { st.seed++; rebuild(); }); return; }
  const r2 = row(); Object.keys(CATALOG[st.kind]).forEach(n => btn(r2, n, st.name === n, () => { st.name = n; st.pal = null; st.dist = 0; rebuild(); }));
  const e = CATALOG[st.kind][st.name], r3 = row(); e.pals.forEach(p => btn(r3, p, !st.all && (st.pal || e.pals[0]) === p, () => { st.pal = p; st.all = false; rebuild(); }));
  btn(r3, 'compare all colours', st.all, () => { st.all = !st.all; st.dist = 0; rebuild(); }); btn(r3, 'reroll shape', false, () => { st.seed++; rebuild(); });
}
/* orbit: drag = rotate, wheel / pinch = zoom */
const ptr = new Map(); let pinch = 0;
canvas.addEventListener('pointerdown', e => { canvas.setPointerCapture(e.pointerId); ptr.set(e.pointerId, [e.clientX, e.clientY]); });
canvas.addEventListener('pointermove', e => {
  const p = ptr.get(e.pointerId); if (!p) return;
  if (ptr.size === 1) { st.yaw -= (e.clientX - p[0]) * .008; st.pitch = Math.max(-.1, Math.min(1.45, st.pitch + (e.clientY - p[1]) * .006)); }
  p[0] = e.clientX; p[1] = e.clientY;
  if (ptr.size === 2) { const [a, b] = [...ptr.values()], d = Math.hypot(a[0] - b[0], a[1] - b[1]); if (pinch) st.dist = Math.max(1.5, Math.min(90, st.dist * pinch / d)); pinch = d; }
});
const up = e => { ptr.delete(e.pointerId); pinch = 0; }; canvas.addEventListener('pointerup', up); canvas.addEventListener('pointercancel', up);
canvas.addEventListener('wheel', e => { e.preventDefault(); st.dist = Math.max(1.5, Math.min(90, st.dist * Math.exp(e.deltaY * .0012))); }, { passive: false });
function resize() { renderer.setSize(innerWidth, innerHeight, false); camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); }
addEventListener('resize', resize); resize();
const spin = Q.get('spin') != null ? +Q.get('spin') : 0;
function frame() {
  requestAnimationFrame(frame); if (spin) st.yaw += spin * .01;
  const d = st.dist || 6, portrait = innerHeight > innerWidth, dd = portrait ? d * 1.5 : d;
  camera.position.set(st.tx + Math.sin(st.yaw) * Math.cos(st.pitch) * dd, st.ty + Math.sin(st.pitch) * dd, st.tz + Math.cos(st.yaw) * Math.cos(st.pitch) * dd); camera.lookAt(st.tx, st.ty, st.tz);
  renderer.render(scene, camera);
}
rebuild(); frame();
window.__scenery = { st, rebuild, THREE };
