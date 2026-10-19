/* The Wilds (1.1.9): a second, larger map reached through the portal in town (and a portal back). Built from the scenery kit's low-poly variants,
   merged into spatial chunks (frustum-culled) so the whole map costs only a handful of draw calls: ground 1, water 1, hills 1, portals 2, plus ~2 per visible chunk. */
import * as THREE from './vendor/three.module.js';
import { makeVariant, makeDetailTexture, makeMaterials, Acc } from './scenery.js';
export const WILDS = { ox: 1000, oz: 0, half: 170 };            // centre + half extent of the walkable area (town is ~30 m half extent)
export const LAKE = { x: 48, z: -34, r: 21 };                    // relative to the Wilds centre
const CH = 64;                                                   // chunk size (m)
function rng(seed) { let s = seed >>> 0; return () => { s = (s + 0x6D2B79F5) | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
/* biome of a point relative to the centre */
export function biome(x, z) {
  if (Math.hypot(x - LAKE.x, z - LAKE.z) < LAKE.r + 7) return 'shore';
  if (x > 62 && z > 8) return 'snow';
  if (z > 58) return 'rock';
  if (x < -38) return 'forest';
  return 'meadow';
}
function paintGround(size, span) {
  const c = document.createElement('canvas'); c.width = c.height = size; const g = c.getContext('2d'), r = rng(11), k = size / span, X = x => (x + span / 2) * k, Z = z => (span / 2 - z) * k;   // texture v is flipped vs world z
  g.fillStyle = '#5ea443'; g.fillRect(0, 0, size, size);
  const blob = (x, z, rad, col, a) => { const gr = g.createRadialGradient(X(x), Z(z), 0, X(x), Z(z), rad * k); gr.addColorStop(0, col + a); gr.addColorStop(1, col + '00'); g.fillStyle = gr; g.fillRect(X(x) - rad * k, Z(z) - rad * k, rad * 2 * k, rad * 2 * k); };
  const hex = n => n.toString(16).padStart(2, '0');
  const reg = (fn, col, cnt, rad, a) => { for (let i = 0; i < cnt; i++) { const x = (r() - .5) * span, z = (r() - .5) * span; if (fn(x, z)) blob(x, z, rad * (.6 + r() * .8), col, hex(a)); } };
  reg((x, z) => biome(x, z) === 'meadow', '#7fc24f', 240, 14, 150); reg((x, z) => biome(x, z) === 'meadow', '#c2b25a', 40, 10, 90);
  reg((x, z) => biome(x, z) === 'forest', '#2f7a3c', 300, 12, 190); reg((x, z) => biome(x, z) === 'forest', '#5a4a2a', 60, 6, 110);
  reg((x, z) => biome(x, z) === 'rock', '#7c7e84', 300, 11, 210); reg((x, z) => biome(x, z) === 'rock', '#5a5c62', 60, 7, 150);
  reg((x, z) => biome(x, z) === 'snow', '#eef3f7', 300, 12, 230);
  for (let a = 0; a < 6.283; a += .2) for (let rr = LAKE.r - 2; rr < LAKE.r + 9; rr += 3) blob(LAKE.x + Math.cos(a) * rr, LAKE.z + Math.sin(a) * rr, 7, '#d8c690', hex(rr < LAKE.r + 4 ? 235 : 130));
  for (let t = 0; t <= 1; t += .02) { const x = -6 + t * (LAKE.x + 6), z = 4 + t * (LAKE.z - 4) + Math.sin(t * 9) * 5; blob(x, z, 3.2, '#9a7a4a', hex(220)); }       // dirt trail spawn -> lake
  for (let t = 0; t <= 1; t += .02) blob(-6 + Math.sin(t * 6) * 4, 4 + t * 90, 3, '#9a7a4a', hex(200));                                          // dirt trail north to the standing stones
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t;
}
export function makePortal(color) {
  const g = new THREE.Group(), ring = new THREE.Mesh(new THREE.TorusGeometry(1.5, 0.17, 8, 28), new THREE.MeshBasicMaterial({ color })),
    disc = new THREE.Mesh(new THREE.CircleGeometry(1.4, 24), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.42, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide })),
    base = new THREE.Mesh(new THREE.CylinderGeometry(1.9, 2.1, 0.25, 12), new THREE.MeshLambertMaterial({ color: 0x6a6f7a }));
  ring.position.y = disc.position.y = 1.9; base.position.y = 0.12; g.add(ring, disc, base);
  g.userData.update = t => { disc.rotation.z = t * 1.2; ring.rotation.z = -t * 0.6; disc.material.opacity = 0.35 + 0.12 * Math.sin(t * 3); };
  return g;
}
/* Stone gate (replaces the glowing portal): two pillars + lintel + a dark banner; walk through the opening to cross maps. 3 meshes. Same API as makePortal (position/visible/userData.update). */
export function makeGate(color) {
  const g = new THREE.Group(), stone = new THREE.MeshLambertMaterial({ color: 0x8a8578 }), cap = new THREE.MeshLambertMaterial({ color: 0x6d685c });
  const geos = [], put = (w, h, d, x, y, z, m) => { const q = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); q.position.set(x, y, z); return q; };
  const p1 = put(1.1, 4.4, 1.2, -1.9, 2.2, 0, stone), p2 = put(1.1, 4.4, 1.2, 1.9, 2.2, 0, stone), lin = put(5.2, 0.9, 1.4, 0, 4.85, 0, cap);
  const flag = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 1.6), new THREE.MeshBasicMaterial({ color, side: THREE.DoubleSide })); flag.position.set(0, 3.7, 0.05);
  /* glow so the exits can be found from far away: additive light beam + ground ring + pulsing banner (3 extra cheap meshes, no real lights) */
  const add = (o, op) => new THREE.MeshBasicMaterial({ color: o, transparent: true, opacity: op, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide });
  const beam = new THREE.Mesh(new THREE.CylinderGeometry(1.5, 2.2, 90, 14, 1, true), add(color, 0.2)); beam.position.y = 45;
  const halo = new THREE.Mesh(new THREE.CylinderGeometry(0.9, 0.9, 90, 10, 1, true), add(0xffffff, 0.12)); halo.position.y = 45;
  const ring = new THREE.Mesh(new THREE.RingGeometry(1.7, 2.5, 32), add(color, 0.5)); ring.rotation.x = -Math.PI / 2; ring.position.y = 0.08;
  g.add(p1, p2, lin, flag, beam, halo, ring); g.userData.update = t => { const k = 0.5 + 0.5 * Math.sin(t * 2.2); beam.material.opacity = 0.14 + 0.14 * k; halo.material.opacity = 0.08 + 0.08 * k; ring.material.opacity = 0.3 + 0.4 * k; ring.scale.setScalar(0.9 + 0.2 * k); flag.scale.setScalar(0.95 + 0.1 * k); }; g.userData.gate = true; g.userData.dispose = () => { g.traverse(o => { if (o.geometry) o.geometry.dispose(); if (o.material) o.material.dispose(); }); };
  return g;
}
export function buildWilds(env) {
  const { scene, HS } = env, { ox, oz, half } = WILDS, cols = [], rnd = rng(20261018), grp = new THREE.Group(); grp.name = 'wilds'; scene.add(grp);
  const map = makeDetailTexture(), mats = makeMaterials(map), cache = new Map(), chunks = new Map(), taken = [];
  const rp = a => a[Math.floor(rnd() * a.length) % a.length], rf = (a, b) => a + (b - a) * rnd();
  const variant = (kind, name, pal) => { const slot = Math.floor(rnd() * 2), key = kind + name + pal + slot; if (!cache.has(key)) cache.set(key, makeVariant(kind, name, pal, slot + 3, false)); return cache.get(key); };
  const acc = (layer, x, z) => { const key = layer + ':' + Math.floor(x / CH) + ':' + Math.floor(z / CH); let a = chunks.get(key); if (!a) chunks.set(key, a = { layer, acc: new Acc() }); return a.acc; };
  const put = (kind, name, pal, x, z, ry, s, layer) => { const v = variant(kind, name, pal); acc(layer || 'plain', x, z).add(v.geo, ox + x, 0, oz + z, ry, s); return v; };
  const circ = (x, z, r) => cols.push({ type: 'circle', x: ox + x, z: oz + z, r });
  const box = (x, z, w, d) => cols.push({ type: 'box', minX: ox + x - w / 2, maxX: ox + x + w / 2, minZ: oz + z - d / 2, maxZ: oz + z + d / 2 });
  const clear = (x, z, d) => { for (const t of taken) if (Math.hypot(t[0] - x, t[1] - z) < d + t[2]) return false; return true; };
  const claim = (x, z, r) => taken.push([x, z, r]);
  const inLake = (x, z, m) => Math.hypot(x - LAKE.x, z - LAKE.z) < LAKE.r + m;
  const onTrail = (x, z) => Math.hypot(x + 6, z - 4) < 9;                   // spawn clearing
  const rpos = (lim) => [(rnd() * 2 - 1) * (lim || half - 3), (rnd() * 2 - 1) * (lim || half - 3)];
  // spawn clearing + props
  claim(-6, 4, 9); claim(0, 85, 12);
  /* portal back sits at (-6, -2); lamps + signpost beside it */
  for (const [x, z] of [[-9.5, -3], [-2.5, -3]]) { put('props', 'lamp', 'oak', x, z, 0, 1, 'cast'); circ(x, z, .25); }
  put('props', 'signpost', 'oak', -9, 3, .3, 1, 'cast'); circ(-9, 3, .25);
  /* camp: logs, stumps, crates, barrels, haybale */
  { const cx = -26, cz = 22; for (let i = 0; i < 4; i++) { const a = i * 1.57 + .5; put('props', 'logs', 'oak', cx + Math.cos(a) * 3, cz + Math.sin(a) * 3, a + 1.57, 1, 'cast'); box(cx + Math.cos(a) * 3, cz + Math.sin(a) * 3, 1.4, 1.2); }
    put('props', 'stump', 'oak', cx, cz, 0, 1.3, 'cast'); circ(cx, cz, .7); put('props', 'crate', 'oak', cx + 5, cz + 4, .4, 1, 'cast'); box(cx + 5, cz + 4, 1, 1); put('props', 'barrel', 'oak', cx + 6.4, cz + 3.4, 0, 1, 'cast'); circ(cx + 6.4, cz + 3.4, .45);
    put('props', 'haybale', 'straw', cx - 5, cz + 3, .6, 1, 'cast'); circ(cx - 5, cz + 3, .8); claim(cx, cz, 8); }
  /* fenced pen */
  { const gx = 22, gz = 26, w = 12, d = 8; for (let i = 0; i * 1.2 < w; i++) { put('props', 'fence', 'oak', gx - w / 2 + i * 1.2, gz - d / 2, 0, 1, 'cast'); put('props', 'fence', 'oak', gx - w / 2 + i * 1.2, gz + d / 2, 0, 1, 'cast'); }
    for (let i = 0; i * 1.2 < d; i++) { put('props', 'fence', 'oak', gx - w / 2, gz - d / 2 + i * 1.2 + 1.2, -Math.PI / 2, 1, 'cast'); if (i < 5) put('props', 'fence', 'oak', gx + w / 2, gz - d / 2 + i * 1.2, Math.PI / 2, 1, 'cast'); }
    box(gx, gz - d / 2, w + 1, .3); box(gx, gz + d / 2, w + 1, .3); box(gx - w / 2, gz, .3, d); for (let i = 0; i < 4; i++) put('props', 'cabbages', 'patch', gx - 3 + i * 2, gz, 0, 1, 'cast'); claim(gx, gz, 9); }
  /* standing stones circle (north) */
  for (let i = 0; i < 9; i++) { const a = i / 9 * 6.283, x = Math.cos(a) * 9, z = 85 + Math.sin(a) * 9; put('rocks', 'standing', rp(['slate', 'grey', 'mossy']), x, z, a, rf(1.1, 1.6), 'plain'); circ(x, z, .6); }
  put('rocks', 'slab', 'slate', 0, 85, 0, 1.6, 'plain'); circ(0, 85, 1.3);
  /* trees by biome */
  const treeFor = (b) => { const r = rnd();
    if (b === 'forest') return r < .4 ? ['pine', rp(['deep', 'spruce', 'green'])] : r < .7 ? ['oak', rp(['deep', 'green', 'lime'])] : r < .9 ? ['birch', rp(['lime', 'yellow', 'green'])] : ['cypress', 'deep'];
    if (b === 'snow') return r < .8 ? ['pine', rp(['spruce', 'spruce', 'deep'])] : ['dead', rp(['grey', 'pale'])];
    if (b === 'rock') return r < .5 ? ['dead', rp(['dark', 'grey', 'pale'])] : r < .85 ? ['pine', rp(['deep', 'spruce'])] : ['cypress', 'spruce'];
    return r < .4 ? ['oak', rp(['green', 'lime', 'autumn', 'yellow'])] : r < .65 ? ['birch', rp(['lime', 'yellow', 'green'])] : r < .85 ? ['apple', rp(['green', 'blossom', 'autumn'])] : ['pine', 'green']; };
  const dens = { forest: 1, snow: .55, rock: .22, meadow: .2, shore: .08 };
  let n = 0, guard = 0;
  while (n < 900 && guard++ < 16000) {
    const [x, z] = rpos(half - 2), b = biome(x, z); if (rnd() > dens[b] || inLake(x, z, 2) || onTrail(x, z)) continue;
    const s = rf(.85, 1.5); if (!clear(x, z, 2.2 * s)) continue; const [sp, pal] = treeFor(b);
    put('trees', sp, pal, x, z, rnd() * 6.283, s, 'cast'); circ(x, z, .4 * s + .12); claim(x, z, 1.4 * s); n++;
  }
  /* bushes, rocks, flowers, grass, reeds at the shore */
  const place = (cnt, fn) => { let k = 0, g = 0; while (k < cnt && g++ < cnt * 40) { const [x, z] = rpos(half - 1); if (inLake(x, z, 0) || onTrail(x, z)) continue; if (fn(x, z, biome(x, z))) k++; } };
  place(300, (x, z, b) => { if (!clear(x, z, .9) || (b === 'snow' || b === 'rock') && rnd() < .7) return false; const nm = rp(['round', 'round', 'hedge', 'spiky']); put('bushes', nm, rp(['green', 'deep', 'lime']), x, z, rnd() * 6.283, rf(.8, 1.4), 'plain'); claim(x, z, .5); return true; });
  place(190, (x, z, b) => { if (!clear(x, z, 1)) return false; const hi = b === 'rock' || b === 'snow', r = rnd(), nm = hi ? (r < .35 ? 'boulder' : r < .6 ? 'cluster' : r < .85 ? 'stone' : 'slab') : (r < .15 ? 'boulder' : r < .6 ? 'stone' : 'cluster'), s = rf(.8, hi ? 2 : 1.4);
    put('rocks', nm, rp(['grey', 'warm', 'slate', 'mossy']), x, z, rnd() * 6.283, s, 'plain'); if (nm === 'boulder') circ(x, z, .95 * s); else if (nm === 'slab') circ(x, z, .7 * s); claim(x, z, .8); return true; });
  place(420, (x, z, b) => { if (b !== 'meadow' && b !== 'forest') return false; const nm = rp(['daisy', 'tulip', 'lavender', 'bellflower']); put('flowers', nm, rp(['white', 'yellow', 'pink', 'purple', 'blue', 'red', 'orange']), x, z, rnd() * 6.283, rf(.9, 1.4), 'plain'); return true; });
  place(1500, (x, z, b) => { if (b === 'snow' || b === 'rock' && rnd() < .7) return false; put('flowers', 'grass', rp(['green', 'lush', 'dry']), x, z, rnd() * 6.283, rf(.8, 1.6), 'plain'); return true; });
  for (let i = 0; i < 40; i++) { const a = rnd() * 6.283, rr = LAKE.r + rf(1, 3.5); put('bushes', 'reeds', rp(['green', 'lime']), LAKE.x + Math.cos(a) * rr, LAKE.z + Math.sin(a) * rr, rnd() * 6.283, rf(.9, 1.5), 'plain'); }
  /* lake: collider ring (circles) + water mesh */
  for (let a = 0; a < 6.283; a += .22) circ(LAKE.x + Math.cos(a) * (LAKE.r - 1.5), LAKE.z + Math.sin(a) * (LAKE.r - 1.5), 3.2); circ(LAKE.x, LAKE.z, LAKE.r - 3);
  /* meshes */
  const solid = mats.solid;
  const chunkMeshes = []; for (const { layer, acc: A } of chunks.values()) { const geo = A.geo(true); if (!geo) continue; const m = new THREE.Mesh(geo, solid); geo.computeBoundingSphere(); chunkMeshes.push(m); m.castShadow = layer === 'cast'; m.receiveShadow = true; m.matrixAutoUpdate = false; m.frustumCulled = true; grp.add(m); }
  for (const v of cache.values()) { v.geo.dispose(); if (v.glow) v.glow.dispose(); }
  const span = half * 2 + 100, ground = new THREE.Mesh(new THREE.PlaneGeometry(span, span), new THREE.MeshLambertMaterial({ map: paintGround(1536, span) }));
  ground.rotation.x = -Math.PI / 2; ground.position.set(ox, 0, oz); ground.receiveShadow = true; grp.add(ground);
  const water = new THREE.Mesh(new THREE.CircleGeometry(LAKE.r, 40), new THREE.MeshLambertMaterial({ color: 0x3f8fd0, transparent: true, opacity: 0.88 }));
  water.rotation.x = -Math.PI / 2; water.position.set(ox + LAKE.x, 0.06, oz + LAKE.z); grp.add(water);
  /* distant hills ring (visual only, one merged mesh) */
  { const hg = [], r2 = rng(5); const A = new Acc(); const base = new THREE.SphereGeometry(1, 10, 6, 0, Math.PI * 2, 0, Math.PI / 2);
    const col = new THREE.Float32BufferAttribute(base.attributes.position.count * 3, 3); base.setAttribute('color', col);
    for (let i = 0; i < 38; i++) { const a = i / 38 * 6.283 + r2() * .1, rad = half + 30 + r2() * 40, s = 18 + r2() * 26, h = 10 + r2() * 22, tint = new THREE.Color().setHSL(.28 + r2() * .06, .38, .26 + r2() * .1), snow = h > 24;
      const g = base.clone(); g.scale(s, h, s * (.8 + r2() * .5)); g.rotateY(r2() * 6); const p = g.attributes.position, c = g.attributes.color; for (let k = 0; k < p.count; k++) { const hh = p.getY(k) / h, cc = snow && hh > .7 ? new THREE.Color(0xeef3f7) : tint.clone().lerp(new THREE.Color(0x8a8a86), hh * .5); c.setXYZ(k, cc.r, cc.g, cc.b); }
      g.translate(ox + Math.cos(a) * rad, -1, oz + Math.sin(a) * rad); hg.push(g); }
    const total = hg.reduce((s, g) => s + g.index.count, 0), P = [], N = [], C = []; for (const g of hg) { const ix = g.index, pa = g.attributes.position, na = g.attributes.normal, ca = g.attributes.color; for (let i = 0; i < ix.count; i++) { const v = ix.getX(i); P.push(pa.getX(v), pa.getY(v), pa.getZ(v)); N.push(na.getX(v), na.getY(v), na.getZ(v)); C.push(ca.getX(v), ca.getY(v), ca.getZ(v)); } }
    const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.Float32BufferAttribute(P, 3)); geo.setAttribute('normal', new THREE.Float32BufferAttribute(N, 3)); geo.setAttribute('color', new THREE.Float32BufferAttribute(C, 3));
    const hills = new THREE.Mesh(geo, new THREE.MeshLambertMaterial({ vertexColors: true })); hills.frustumCulled = false; grp.add(hills); }
  grp.visible = false;
  /* distance culling: only chunks near the hero are drawn (keeps draw calls low on a big map) */
  const cull = (hx, hz) => { for (const m of chunkMeshes) { const s = m.geometry.boundingSphere, d = Math.hypot(s.center.x - hx, s.center.z - hz) - s.radius; m.visible = d < (m.castShadow ? 105 : 125); } };
  return { cull, group: grp, colliders: cols, spawn: { x: ox - 6, z: oz + 4 }, portal: { x: ox - 6, z: oz - 2 }, drawCalls: grp.children.length };
}
