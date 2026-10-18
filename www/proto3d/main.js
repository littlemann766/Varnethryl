// Varnethryl 3D prototype: Liongate-style village. Standalone, does not touch the 2D game.
import * as THREE from './vendor/three.module.js';
import { makeAldricTextures, buildAldric } from './aldric.js';
import { makeHeroTextures, buildUmbral, buildSelene } from './heroes2.js';
import { makeEnterable } from './interiors.js';
import { GLTFLoader } from './vendor/jsm/loaders/GLTFLoader.js';

const canvas = document.getElementById('c');
const diag = (msg, bad) => { try { (window.__p3dDiag || (() => {}))(msg, bad); } catch (_) {} };
const COARSE = matchMedia('(pointer:coarse)').matches || /Android|iPhone|iPad/i.test(navigator.userAgent);
let renderer;
try { renderer = new THREE.WebGLRenderer({ canvas, antialias: !COARSE && (window.devicePixelRatio || 1) < 1.5, powerPreference: 'high-performance' }); }
catch (e) { diag('WebGL failed to start: ' + (e && e.message || e), true); throw e; }
diag('WebGL ok · ' + (renderer.capabilities.isWebGL2 ? 'WebGL2' : 'WebGL1') + ' · max tex ' + renderer.capabilities.maxTextureSize);
const DPR_CAP = 1.5;                       // cap pixel ratio: biggest single mobile perf lever
let prCeil = Math.min(window.devicePixelRatio || 1, DPR_CAP), pr = prCeil;   // pr adapts down (never above prCeil) if the GPU can't hold ~45 fps
renderer.setPixelRatio(pr);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;

const scene = new THREE.Scene();
const SKY_TOP = '#7fb2e6', SKY_HORIZON = '#f4e3c3';
{ // soft gradient sky
  const c = document.createElement('canvas'); c.width = 4; c.height = 256;
  const g = c.getContext('2d'), grd = g.createLinearGradient(0, 0, 0, 256);
  grd.addColorStop(0, SKY_TOP); grd.addColorStop(0.7, '#cfe2ee'); grd.addColorStop(1, SKY_HORIZON);
  g.fillStyle = grd; g.fillRect(0, 0, 4, 256);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  scene.background = t;
}
scene.fog = new THREE.Fog(0xdde8ee, 38, 90);

const camera = new THREE.PerspectiveCamera(50, 1, 0.5, 140);

// Lights: hemisphere fill + one shadow-casting sun that follows the hero
scene.add(new THREE.HemisphereLight(0xcfe6ff, 0x6a7a4a, 1.25));
const sun = new THREE.DirectionalLight(0xfff0d0, 2.2);
const SHADOW_SIZE = 1024, SHADOW_R = 15;
sun.castShadow = true;
sun.shadow.mapSize.set(SHADOW_SIZE, SHADOW_SIZE);
Object.assign(sun.shadow.camera, { left: -SHADOW_R, right: SHADOW_R, top: SHADOW_R, bottom: -SHADOW_R, near: 1, far: 70 });
sun.shadow.bias = -0.0006; sun.shadow.normalBias = 0.03;
const SUN_OFF = new THREE.Vector3(-18, 30, 14);
scene.add(sun, sun.target);

// ---------- helpers ----------
const mats = {};
const M = (name, color, extra) => (mats[name] = new THREE.MeshLambertMaterial(Object.assign({ color }, extra)));
M('wall', 0xe9dcc0); M('wallB', 0xd2c2a0); M('stone', 0x9aa0a8); M('stoneD', 0x6f757e); M('wood', 0x7a5232);
M('roofR', 0xb5452f); M('roofB', 0x3d6aa8); M('roofG', 0x4b7d4a); M('door', 0x5a3a22);
M('glass', 0xffe9a0, { emissive: 0x6a5420 }); M('water', 0x4fa8d8, { emissive: 0x103050 });
M('trunk', 0x6b4a2b); M('leaf', 0x3e8a3a); M('leaf2', 0x57a043); M('gold', 0xe0b040, { emissive: 0x302000 });
M('steel', 0xc7ccd6); M('armor', 0x9aa6bd); M('cloth', 0x2d55a8); M('skin', 0xf0c8a0); M('plume', 0xc8302a); M('dark', 0x333844);

function canvasTex(size, draw, repeat) {
  const c = document.createElement('canvas'); c.width = c.height = size;
  draw(c.getContext('2d'), size);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.anisotropy = 4; if (repeat) t.repeat.set(repeat, repeat);
  return t;
}
const rnd = (() => { let s = 1337; return () => (s = (s * 16807) % 2147483647) / 2147483647; })();

const colliders = []; // {type:'box',minX,maxX,minZ,maxZ} | {type:'circle',x,z,r}
const addBoxCol = (cx, cz, w, d) => colliders.push({ type: 'box', minX: cx - w / 2, maxX: cx + w / 2, minZ: cz - d / 2, maxZ: cz + d / 2 });
const addCircCol = (x, z, r) => colliders.push({ type: 'circle', x, z, r });

function mesh(geo, mat, x, y, z, parent, shadow = true) {
  const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z);
  m.castShadow = shadow; m.receiveShadow = true; (parent || scene).add(m); return m;
}

// ---------- world ----------
const WORLD = 32; // half extent
const grass = canvasTex(256, (g, s) => {
  g.fillStyle = '#5c9a45'; g.fillRect(0, 0, s, s);
  for (let i = 0; i < 2600; i++) { g.fillStyle = `hsl(${88 + rnd() * 30},${40 + rnd() * 20}%,${30 + rnd() * 18}%)`; g.fillRect(rnd() * s, rnd() * s, 2, 3); }
}, 22);
const cobble = canvasTex(256, (g, s) => {
  g.fillStyle = '#8d8579'; g.fillRect(0, 0, s, s);
  for (let y = 0; y < 8; y++) for (let x = 0; x < 8; x++) {
    const l = 52 + rnd() * 18; g.fillStyle = `hsl(35,10%,${l}%)`;
    g.fillRect(x * 32 + (y % 2) * 16 + 1, y * 32 + 1, 30, 30);
  }
}, 1);
const ground = mesh(new THREE.PlaneGeometry(WORLD * 4, WORLD * 4), new THREE.MeshLambertMaterial({ map: grass }), 0, 0, 0, null, false);
ground.rotation.x = -Math.PI / 2;
{ // plaza + paths (cobble)
  const cm = new THREE.MeshLambertMaterial({ map: cobble.clone() });
  cm.map.repeat.set(8, 8); cm.map.needsUpdate = true;
  const plaza = mesh(new THREE.CircleGeometry(9.5, 40), cm, 0, 0.02, 0, null, false); plaza.rotation.x = -Math.PI / 2;
  const pm = new THREE.MeshLambertMaterial({ map: cobble.clone() }); pm.map.repeat.set(1, 11); pm.map.needsUpdate = true;
  const p1 = mesh(new THREE.PlaneGeometry(5, 56), pm, 0, 0.03, 4, null, false); p1.rotation.x = -Math.PI / 2;
  const p2 = mesh(new THREE.PlaneGeometry(40, 4), pm, 0, 0.031, 0, null, false); p2.rotation.x = -Math.PI / 2; p2.material.map.repeat.set(8, 0.8);
}

// border: low stone wall around village with gate gap at south (z = +WORLD)
function wallSeg(x1, z1, x2, z2) {
  const len = Math.hypot(x2 - x1, z2 - z1), h = 2.2, t = 1.2;
  const horiz = Math.abs(z2 - z1) < 0.01;
  const m = mesh(new THREE.BoxGeometry(horiz ? len : t, h, horiz ? t : len), mats.stone, (x1 + x2) / 2, h / 2, (z1 + z2) / 2);
  addBoxCol((x1 + x2) / 2, (z1 + z2) / 2, horiz ? len : t, horiz ? t : len);
  // crenellations
  const n = Math.floor(len / 1.6);
  for (let i = 0; i < n; i++) {
    const f = (i + 0.5) / n, px = x1 + (x2 - x1) * f, pz = z1 + (z2 - z1) * f;
    mesh(new THREE.BoxGeometry(horiz ? 0.8 : t, 0.5, horiz ? t : 0.8), mats.stone, px, h + 0.25, pz);
  }
}
const GATE_W = 4;
wallSeg(-WORLD, -WORLD, WORLD, -WORLD);          // north
wallSeg(-WORLD, -WORLD, -WORLD, WORLD);          // west
wallSeg(WORLD, -WORLD, WORLD, WORLD);            // east
wallSeg(-WORLD, WORLD, -GATE_W - 3, WORLD);      // south left
wallSeg(GATE_W + 3, WORLD, WORLD, WORLD);        // south right

function tower(x, z, r = 2.6, h = 9) {
  mesh(new THREE.CylinderGeometry(r, r * 1.08, h, 12), mats.stone, x, h / 2, z);
  mesh(new THREE.CylinderGeometry(r * 1.2, r * 1.2, 0.6, 12), mats.stoneD, x, h + 0.3, z);
  mesh(new THREE.ConeGeometry(r * 1.3, 3.2, 12), mats.roofB, x, h + 2.2, z);
  addCircCol(x, z, r * 1.08);
}
tower(-GATE_W - 3, WORLD, 2.6); tower(GATE_W + 3, WORLD, 2.6);
// gate lintel + lion banner
mesh(new THREE.BoxGeometry(GATE_W * 2 + 2, 1.4, 1.6), mats.stone, 0, 7, WORLD);
mesh(new THREE.BoxGeometry(1.4, 2.6, 0.2), mats.plume, 0, 5.2, WORLD - 0.9);
mesh(new THREE.SphereGeometry(0.5, 10, 8), mats.gold, 0, 5.4, WORLD - 1.05);

// buildings
function building(cx, cz, w, d, h, opt = {}) {
  const g = new THREE.Group(); g.position.set(cx, 0, cz); scene.add(g);
  mesh(new THREE.BoxGeometry(w, h, d), opt.wall || mats.wall, 0, h / 2, 0, g);
  mesh(new THREE.BoxGeometry(w + 0.3, 0.5, d + 0.3), mats.stoneD, 0, 0.25, 0, g);      // plinth
  // timber beams (front face)
  for (const sx of [-1, 1]) mesh(new THREE.BoxGeometry(0.25, h, 0.25), mats.wood, sx * (w / 2), h / 2, d / 2, g);
  mesh(new THREE.BoxGeometry(w, 0.25, 0.25), mats.wood, 0, h * 0.62, d / 2 + 0.02, g);
  const roof = mesh(new THREE.ConeGeometry(1, opt.roofH || 3.4, 4), opt.roof || mats.roofR, 0, h + (opt.roofH || 3.4) / 2, 0, g);
  roof.rotation.y = Math.PI / 4; roof.scale.set(w * 0.78, 1, d * 0.78);
  // door + windows (front = +z)
  mesh(new THREE.BoxGeometry(1.3, 2.2, 0.2), mats.door, 0, 1.1 + 0.25, d / 2 + 0.05, g);
  for (const sx of [-1, 1]) { mesh(new THREE.BoxGeometry(1, 1, 0.12), mats.glass, sx * w * 0.3, h * 0.55, d / 2 + 0.05, g, false); }
  // chimney
  mesh(new THREE.BoxGeometry(0.9, 2.6, 0.9), mats.stoneD, w * 0.25, h + 1.6, -d * 0.2, g);
  if (opt.sign) mesh(new THREE.BoxGeometry(1.6, 0.8, 0.12), mats.gold, w * 0.0, h * 0.85, d / 2 + 0.15, g);
  addBoxCol(cx, cz, w + 0.3, d + 0.3);
  return g;
}
const enterables = [];
const ectx = { scene, mats, colliders };
enterables.push(makeEnterable(ectx, { id: 'inn', cx: -13, cz: -9, w: 9, d: 7, h: 4.6, sign: true, interior: 'inn' }));
enterables.push(makeEnterable(ectx, { id: 'smithy', cx: 13, cz: -10, w: 7.5, d: 6.5, h: 4.2, roof: mats.roofB, wall: mats.wallB, interior: 'smith', rug2: true }));
enterables.push(makeEnterable(ectx, { id: 'guildhall', cx: 0, cz: -19, w: 13, d: 7.5, h: 5.4, roof: mats.roofG, roofH: 4.2, sign: true, interior: 'hall' }));
enterables.push(makeEnterable(ectx, { id: 'house', cx: -15, cz: 9, w: 6.4, d: 6.4, h: 3.8, roof: mats.roofR, interior: 'house' }));
building(15, 10, 6, 5.5, 3.8, { roof: mats.roofB, wall: mats.wallB });
building(-21, -18, 5.5, 5.5, 3.6, { roof: mats.roofG });
building(21, -2, 5.5, 6, 3.6, { roof: mats.roofR, wall: mats.wallB });
tower(0, -26.5, 2.3, 7);                                              // keep tower behind guild hall

// fountain
const fountain = new THREE.Group(); scene.add(fountain);
mesh(new THREE.CylinderGeometry(3.2, 3.4, 0.9, 24), mats.stone, 0, 0.45, 0, fountain);
mesh(new THREE.CylinderGeometry(2.8, 2.8, 0.3, 24), mats.water, 0, 0.82, 0, fountain, false);
mesh(new THREE.CylinderGeometry(0.4, 0.55, 2.4, 10), mats.stone, 0, 1.6, 0, fountain);
mesh(new THREE.CylinderGeometry(1.3, 0.8, 0.4, 16), mats.stone, 0, 2.7, 0, fountain);
mesh(new THREE.CylinderGeometry(1.1, 1.1, 0.12, 16), mats.water, 0, 2.95, 0, fountain, false);
const drops = [];
let dropMade = 0;
for (let i = 0; i < 6; i++) { const m = mesh(new THREE.SphereGeometry(0.1, 6, 5), mats.water, 0, 3, 0, fountain, false); m.userData.keep = true; drops.push(m); }
addCircCol(0, 0, 3.5);

// trees (instanced: 2 draw calls for ~60 trees)
{
  const pts = [];
  const blocked = (x, z) => {
    if (Math.hypot(x, z) < 12) return true;
    if (Math.abs(x) < 3.5) return true;                   // main road
    if (Math.abs(z) < 3) return true;
    for (const c of colliders) {
      if (c.type === 'box' && x > c.minX - 2.5 && x < c.maxX + 2.5 && z > c.minZ - 2.5 && z < c.maxZ + 2.5) return true;
      if (c.type === 'circle' && Math.hypot(x - c.x, z - c.z) < c.r + 2.5) return true;
    }
    return false;
  };
  let guard = 0;
  while (pts.length < 56 && guard++ < 4000) {
    const x = (rnd() * 2 - 1) * (WORLD - 3), z = (rnd() * 2 - 1) * (WORLD - 3);
    if (!blocked(x, z) && !pts.some(p => Math.hypot(p.x - x, p.z - z) < 3)) pts.push({ x, z, s: 0.8 + rnd() * 0.7 });
  }
  const trunkG = new THREE.CylinderGeometry(0.22, 0.32, 1.8, 6), leafG = new THREE.ConeGeometry(1.5, 3.4, 7), leaf2G = new THREE.ConeGeometry(1.1, 2.6, 7);
  const IT = new THREE.InstancedMesh(trunkG, mats.trunk, pts.length), IL = new THREE.InstancedMesh(leafG, mats.leaf, pts.length), IL2 = new THREE.InstancedMesh(leaf2G, mats.leaf2, pts.length);
  const d = new THREE.Object3D();
  pts.forEach((p, i) => {
    d.rotation.set(0, rnd() * 6, 0); d.scale.setScalar(p.s);
    d.position.set(p.x, 0.9 * p.s, p.z); d.updateMatrix(); IT.setMatrixAt(i, d.matrix);
    d.position.set(p.x, (1.8 + 1.4) * p.s, p.z); d.updateMatrix(); IL.setMatrixAt(i, d.matrix);
    d.position.set(p.x, (1.8 + 3.0) * p.s, p.z); d.updateMatrix(); IL2.setMatrixAt(i, d.matrix);
    addCircCol(p.x, p.z, 0.45 * p.s + 0.15);
  });
  for (const m of [IT, IL, IL2]) { m.castShadow = true; m.receiveShadow = true; scene.add(m); }
  window.__treeCount = pts.length;
}
// a few crates/barrels (solid props)
for (const [x, z] of [[-8.2, -4.2], [-8.6, -3.2], [9.2, -5.8], [8.4, 6.6]]) {
  mesh(new THREE.BoxGeometry(1, 1, 1), mats.wood, x, 0.5, z); addBoxCol(x, z, 1, 1);
}


// ---------- static merge: collapse world meshes into one mesh per material (cuts draw calls ~6x) ----------
function mergeStatic() {
  scene.updateMatrixWorld(true);
  const buckets = new Map(), remove = [];
  scene.traverse(o => {
    if (!o.isMesh || o.isInstancedMesh || o.userData.keep) return;
    const key = o.material.uuid + (o.castShadow ? 'c' : '') + (o.receiveShadow ? 'r' : '');
    if (!buckets.has(key)) buckets.set(key, { mat: o.material, c: o.castShadow, r: o.receiveShadow, list: [] });
    buckets.get(key).list.push(o); remove.push(o);
  });
  for (const b of buckets.values()) {
    const parts = b.list.map(o => { const g = (o.geometry.index ? o.geometry.toNonIndexed() : o.geometry.clone()); g.applyMatrix4(o.matrixWorld); return g; });
    let n = 0; for (const g of parts) n += g.attributes.position.count;
    const pos = new Float32Array(n * 3), nor = new Float32Array(n * 3), uv = new Float32Array(n * 2); let o3 = 0, o2 = 0;
    for (const g of parts) {
      pos.set(g.attributes.position.array, o3); nor.set(g.attributes.normal.array, o3); uv.set(g.attributes.uv.array, o2);
      o3 += g.attributes.position.count * 3; o2 += g.attributes.position.count * 2; g.dispose();
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3)); geo.setAttribute('normal', new THREE.BufferAttribute(nor, 3)); geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    const m = new THREE.Mesh(geo, b.mat); m.castShadow = b.c; m.receiveShadow = b.r; scene.add(m);
  }
  for (const o of remove) { o.parent.remove(o); o.geometry.dispose(); }
}
mergeStatic();

// ---------- hero: Sir Aldric (see aldric.js) ----------
const ALDRIC_TEX = await makeAldricTextures();
const HT = await makeHeroTextures();
const HEROES = [buildAldric(ALDRIC_TEX), buildUmbral(HT), buildSelene(HT)];
const HERO_NAMES = ['Sir Aldric', 'Darius Umbral', 'Selene Frostveil'];
let hero = HEROES[0];
HEROES.forEach((h, i) => { h.position.set(0, 0, 14); h.visible = i === 0; scene.add(h); });
function setHero(i) { hero.visible = false; hero = HEROES[i]; hero.visible = true; hero.position.set(state.heroX, 0, state.heroZ); hero.rotation.y = state.yaw; document.querySelectorAll('#heroes button').forEach((b, k) => b.classList.toggle('on', k === i)); }
// ---------- GLB heroes: every model in models/, loaded lazily (procedural fallback for the first 3) ----------
const GLB_IDS = ['aldric', 'darius', 'selene', 'elira', 'orin', 'seraphine', 'talia', 'finn', 'brynn', 'mirelle', 'nyx', 'vesper', 'thorne', 'rook', 'asha', 'rowan', 'kael', 'cedric', 'morwen', 'garruk'];
const GLB_NAMES = ['Sir Aldric', 'Darius Umbral', 'Selene Frostveil', 'Lady Elira', 'Orin Ashlance', 'Dame Seraphine', 'Talia Stormcall', 'Finn Valecourt', 'Brynn Cogwright', 'Mirelle Thornroot', 'Nyx Varrin', 'Vesper Crowe', 'Brother Thorne', 'Rook Wildbane', 'Asha Ironfist', 'Rowan Firebrand', 'Kael Runebinder', 'Cedric Vale', 'Morwen Blackveil', 'Garruk Stonefist'];
const glbInfo = { loaded: [], failed: [], pending: [] };
const useGLB = new URLSearchParams(location.search).get('procedural') == null;
// perf: GLB heroes are ~130 rigid mesh parts glued to animated nodes = ~130 draw calls per pass (x2 with the shadow map).
// Bake all rigid parts into one SkinnedMesh per material (each part rigidly weighted to its parent node), so animation is unchanged.
function mergeRigidParts(root) {
  root.updateMatrixWorld(true);
  const inv = new THREE.Matrix4().copy(root.matrixWorld).invert(), buckets = new Map(), bones = [], boneIdx = new Map();
  root.traverse(o => {
    if (!o.isMesh || o.isSkinnedMesh || o.isInstancedMesh || !o.parent || o.geometry.morphAttributes.position || Array.isArray(o.material) || !o.geometry.attributes.normal) return;
    if (!buckets.has(o.material)) buckets.set(o.material, []);
    buckets.get(o.material).push(o);
  });
  if (!buckets.size) return 0;
  for (const list of buckets.values()) for (const o of list) if (!boneIdx.has(o.parent)) { boneIdx.set(o.parent, bones.length); bones.push(o.parent); }
  if (bones.length > 120) return 0;
  const skeleton = new THREE.Skeleton(bones); // inverses computed from the rest pose (root.matrixWorld is current)
  skeleton.calculateInverses();
  let removed = 0;
  for (const [mat, list] of buckets) {
    let n = 0; for (const o of list) n += (o.geometry.index ? o.geometry.index.count : o.geometry.attributes.position.count);
    const pos = new Float32Array(n * 3), nor = new Float32Array(n * 3), uv = new Float32Array(n * 2), si = new Uint16Array(n * 4), sw = new Float32Array(n * 4);
    let k = 0; const tmp = new THREE.Vector3(), nm = new THREE.Matrix3();
    for (const o of list) {
      const g = o.geometry, ix = g.index, cnt = ix ? ix.count : g.attributes.position.count, P = g.attributes.position, N = g.attributes.normal, U = g.attributes.uv;
      const mtx = new THREE.Matrix4().multiplyMatrices(inv, o.matrixWorld); nm.getNormalMatrix(mtx); const bi = boneIdx.get(o.parent);
      for (let i = 0; i < cnt; i++, k++) {
        const v = ix ? ix.getX(i) : i;
        tmp.fromBufferAttribute(P, v).applyMatrix4(mtx); pos[k * 3] = tmp.x; pos[k * 3 + 1] = tmp.y; pos[k * 3 + 2] = tmp.z;
        tmp.fromBufferAttribute(N, v).applyMatrix3(nm).normalize(); nor[k * 3] = tmp.x; nor[k * 3 + 1] = tmp.y; nor[k * 3 + 2] = tmp.z;
        if (U) { uv[k * 2] = U.getX(v); uv[k * 2 + 1] = U.getY(v); }
        si[k * 4] = bi; sw[k * 4] = 1;
      }
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3)); geo.setAttribute('normal', new THREE.BufferAttribute(nor, 3)); geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    geo.setAttribute('skinIndex', new THREE.BufferAttribute(si, 4)); geo.setAttribute('skinWeight', new THREE.BufferAttribute(sw, 4));
    const sm = new THREE.SkinnedMesh(geo, mat); sm.castShadow = true; sm.receiveShadow = false; sm.frustumCulled = false; sm.name = 'merged';
    root.add(sm); sm.updateMatrixWorld(true); sm.bind(skeleton, sm.matrixWorld);
    for (const o of list) { o.parent.remove(o); o.geometry.dispose(); removed++; }
  }
  return removed;
}
function wrapGLB(g) {
  const root = new THREE.Group(); const m = g.scene; root.add(m);
  m.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = false; } });
  if (new URLSearchParams(location.search).get('nomerge') == null) { m.updateMatrixWorld(true); mergeRigidParts(m); }
  const box = new THREE.Box3().setFromObject(m), hgt = box.max.y - box.min.y;
  if (hgt > 0.01) { const sc = 1.8 / hgt; m.scale.multiplyScalar(sc); m.position.y -= box.min.y * sc; }
  const mixer = new THREE.AnimationMixer(m), act = {};
  for (const c of g.animations) act[c.name] = mixer.clipAction(c);
  if (act.idle) act.idle.play(); if (act.walk) act.walk.play();
  root.userData = { glb: true, mixer, act, capeUpdate() {} };
  return root;
}
const gl = new GLTFLoader();
const glbPromise = {};
// Robust fetch: reports HTTP status / type / size / magic bytes, retries once with a cache-busting URL (bypasses a stale service-worker entry).
async function fetchGLB(id) {
  let lastErr = '';
  for (let attempt = 0; attempt < 2; attempt++) {
    const url = 'proto3d/models/' + id + '.glb' + (attempt ? '?r=' + Date.now() : '');
    try {
      const r = await fetch(url, attempt ? { cache: 'reload' } : undefined);
      if (!r.ok) { lastErr = 'HTTP ' + r.status; continue; }
      const buf = await r.arrayBuffer();
      const magic = new TextDecoder().decode(new Uint8Array(buf, 0, Math.min(4, buf.byteLength)));
      if (magic !== 'glTF') { lastErr = 'not a GLB (type ' + r.headers.get('content-type') + ', ' + buf.byteLength + ' bytes, starts "' + magic.replace(/[^\x20-\x7e]/g, '?') + '")'; continue; }
      return buf;
    } catch (e) { lastErr = 'fetch error: ' + (e && e.message || e); }
  }
  throw new Error(lastErr);
}
// slot gi: models 0-2 replace the procedural hero; others get a placeholder group until the GLB arrives
function loadHero(gi) {
  const id = GLB_IDS[gi];
  if (!useGLB || HEROES[gi] && HEROES[gi].userData.glb) return Promise.resolve(HEROES[gi]);
  if (glbPromise[gi]) return glbPromise[gi];
  glbInfo.pending.push(id); diag('loading ' + id + '.glb ...');
  const fail = (why) => { console.warn('GLB failed', id, why); glbInfo.failed.push(id); glbInfo.pending = glbInfo.pending.filter(x => x !== id); glbInfo.errors = glbInfo.errors || {}; glbInfo.errors[id] = String(why); diag('3D model "' + id + '" failed: ' + why + (HEROES[gi] && HEROES[gi].children.length ? ' - showing simple stand-in' : ''), true); delete glbPromise[gi]; return HEROES[gi]; };
  return glbPromise[gi] = fetchGLB(id).then(buf => new Promise(res => {
    gl.parse(buf, '', g => {
      try {
        const w = wrapGLB(g), old = HEROES[gi];
        w.visible = false; scene.add(w);
        if (old) { w.visible = old.visible; w.position.copy(old.position); w.rotation.copy(old.rotation); scene.remove(old); if (hero === old) hero = w; }
        HEROES[gi] = w; glbInfo.loaded.push(id);
        glbInfo.pending = glbInfo.pending.filter(x => x !== id); diag('3D model "' + id + '" loaded (' + Math.round(buf.byteLength / 1024) + ' KB)'); res(HEROES[gi]);
      } catch (e) { res(fail('wrap: ' + (e && e.message || e))); }
    }, err => res(fail('parse: ' + (err && err.message || err))));
  }), e => fail(e && e.message || e));
}
for (let i = HEROES.length; i < GLB_IDS.length; i++) { const ph = new THREE.Group(); ph.visible = false; scene.add(ph); HEROES.push(ph); HERO_NAMES.push(GLB_NAMES[i]); }
async function selectHero(i) { if (!HEROES[i].userData.glb && useGLB) await loadHero(i); if (!HEROES[i].children.length) return; setHero(i); }
{ const bar = document.getElementById('heroes'); HERO_NAMES.forEach((n, i) => { const b = document.createElement('button'); b.textContent = n.split(' ').pop(); b.title = n; b.className = i === 0 ? 'on' : ''; b.addEventListener('pointerdown', e => { e.stopPropagation(); selectHero(i); }); bar.appendChild(b); }); }
{ const q = new URLSearchParams(location.search).get('hero'); const qi = q != null && HEROES[+q] ? +q : 0; loadHero(qi).then(() => { if (qi && HEROES[qi].children.length) setHero(qi); }); }
// preload the first three quietly after first paint (they replace the procedural stand-ins)

// blob shadow is the real shadow map; no extra.
const marker = new THREE.Mesh(new THREE.RingGeometry(0.35, 0.55, 20), new THREE.MeshBasicMaterial({ color: 0xffe08a, transparent: true, opacity: 0.9, depthWrite: false }));
marker.rotation.x = -Math.PI / 2; marker.position.y = 0.06; marker.visible = false; scene.add(marker);

// ---------- input ----------
const state = { inside: null, zoom: 1, heroX: 0, heroZ: 14, moving: false, speed: 0, target: null, yaw: 0, camYaw: 0, blockedFrames: 0, collisions: 0 };
const keys = new Set();
addEventListener('keydown', e => keys.add(e.key.toLowerCase()));
addEventListener('keyup', e => keys.delete(e.key.toLowerCase()));

const stick = document.getElementById('stick'), knob = document.getElementById('knob');
const joy = { id: null, x: 0, y: 0 };
const STICK_R = 52;
function joyUpdate(e) {
  const r = stick.getBoundingClientRect();
  let dx = e.clientX - (r.left + r.width / 2), dy = e.clientY - (r.top + r.height / 2);
  const l = Math.hypot(dx, dy); if (l > STICK_R) { dx *= STICK_R / l; dy *= STICK_R / l; }
  joy.x = dx / STICK_R; joy.y = dy / STICK_R;
  knob.style.transform = `translate(${dx}px,${dy}px)`;
}
stick.addEventListener('pointerdown', e => { joy.id = e.pointerId; try { stick.setPointerCapture(e.pointerId); } catch (_) {} state.target = null; marker.visible = false; joyUpdate(e); e.preventDefault(); });
stick.addEventListener('pointermove', e => { if (e.pointerId === joy.id) joyUpdate(e); });
const joyEnd = e => { if (e.pointerId === joy.id) { joy.id = null; joy.x = joy.y = 0; knob.style.transform = ''; } };
stick.addEventListener('pointerup', joyEnd); stick.addEventListener('pointercancel', joyEnd);

// canvas: tap = move there, drag = rotate camera
const ray = new THREE.Raycaster(), ndc = new THREE.Vector2(), plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0), hit = new THREE.Vector3();
const touches = new Map();
function tapMoveTo(clientX, clientY) {
  ndc.set((clientX / innerWidth) * 2 - 1, -(clientY / innerHeight) * 2 + 1);
  ray.setFromCamera(ndc, camera);
  if (ray.ray.intersectPlane(plane, hit)) {
    const lim = WORLD - 1.5;
    state.target = { x: THREE.MathUtils.clamp(hit.x, -lim, lim), z: THREE.MathUtils.clamp(hit.z, -lim, lim) };
    marker.position.set(state.target.x, 0.06, state.target.z); marker.visible = true;
  }
}
canvas.addEventListener('pointerdown', e => { try { canvas.setPointerCapture(e.pointerId); } catch (_) {} touches.set(e.pointerId, { sx: e.clientX, sy: e.clientY, lx: e.clientX, drag: false }); });
canvas.addEventListener('pointermove', e => {
  const t = touches.get(e.pointerId); if (!t) return;
  if (!t.drag && Math.hypot(e.clientX - t.sx, e.clientY - t.sy) > 12) t.drag = true;
  if (t.drag) { state.camYaw -= (e.clientX - t.lx) * 0.006; }
  t.lx = e.clientX;
});
const canvasUp = e => { const t = touches.get(e.pointerId); touches.delete(e.pointerId); if (t && !t.drag && e.type === 'pointerup') tapMoveTo(e.clientX, e.clientY); };
canvas.addEventListener('pointerup', canvasUp); canvas.addEventListener('pointercancel', canvasUp);
addEventListener('contextmenu', e => e.preventDefault());

// ---------- movement + collision ----------
const HERO_R = 0.5, SPEED = 5.2;
function resolve(p) {
  let hitAny = false;
  for (const c of colliders) {
    if (c.type === 'box') {
      const qx = THREE.MathUtils.clamp(p.x, c.minX, c.maxX), qz = THREE.MathUtils.clamp(p.z, c.minZ, c.maxZ);
      let dx = p.x - qx, dz = p.z - qz, d2 = dx * dx + dz * dz;
      if (d2 < HERO_R * HERO_R) {
        hitAny = true;
        if (d2 > 1e-8) { const d = Math.sqrt(d2); p.x = qx + dx / d * HERO_R; p.z = qz + dz / d * HERO_R; }
        else { // centre inside box: push out via nearest face
          const l = p.x - c.minX, r = c.maxX - p.x, t = p.z - c.minZ, b = c.maxZ - p.z, m = Math.min(l, r, t, b);
          if (m === l) p.x = c.minX - HERO_R; else if (m === r) p.x = c.maxX + HERO_R; else if (m === t) p.z = c.minZ - HERO_R; else p.z = c.maxZ + HERO_R;
        }
      }
    } else {
      const dx = p.x - c.x, dz = p.z - c.z, d = Math.hypot(dx, dz), min = c.r + HERO_R;
      if (d < min) { hitAny = true; const k = d > 1e-6 ? 1 / d : 0; p.x = c.x + (k ? dx * k : 1) * min; p.z = c.z + (k ? dz * k : 0) * min; }
    }
  }
  const lim = WORLD - 1.3; p.x = THREE.MathUtils.clamp(p.x, -lim, lim);
  p.z = THREE.MathUtils.clamp(p.z, -lim, WORLD + 8); // can walk out the gate a bit
  return hitAny;
}

const tmp = { x: 0, z: 0 };
function updateHero(dt) {
  // input vector in screen space (x right, y up)
  let ix = joy.x, iy = -joy.y;
  if (keys.has('a') || keys.has('arrowleft')) ix -= 1;
  if (keys.has('d') || keys.has('arrowright')) ix += 1;
  if (keys.has('w') || keys.has('arrowup')) iy += 1;
  if (keys.has('s') || keys.has('arrowdown')) iy -= 1;
  let mag = Math.min(1, Math.hypot(ix, iy));
  let vx = 0, vz = 0;
  const sy = Math.sin(state.camYaw), cy = Math.cos(state.camYaw);
  if (mag > 0.12) {
    state.target = null; marker.visible = false;
    // forward = (-sin, -cos), right = (cos, -sin)
    vx = (-sy * iy + cy * ix); vz = (-cy * iy - sy * ix);
    const l = Math.hypot(vx, vz) || 1; vx /= l; vz /= l;
  } else if (state.target) {
    const dx = state.target.x - state.heroX, dz = state.target.z - state.heroZ, d = Math.hypot(dx, dz);
    if (d < 0.25 || state.blockedFrames > 25) { state.target = null; marker.visible = false; state.blockedFrames = 0; }
    else { vx = dx / d; vz = dz / d; mag = Math.min(1, d / 1.2 + 0.4); }
  }
  const moving = (vx || vz);
  if (moving) {
    const step = SPEED * mag * dt, n = Math.max(1, Math.ceil(step / 0.25)), px = state.heroX, pz = state.heroZ;
    tmp.x = state.heroX; tmp.z = state.heroZ; let blocked = false;
    for (let i = 0; i < n; i++) { tmp.x += vx * step / n; tmp.z += vz * step / n; if (resolve(tmp)) blocked = true; }
    state.heroX = tmp.x; state.heroZ = tmp.z;
    if (blocked) { state.collisions++; }
    const moved = Math.hypot(state.heroX - px, state.heroZ - pz);
    state.blockedFrames = (state.target && moved < step * 0.3) ? state.blockedFrames + 1 : 0;
    // face movement direction (use intended direction; slides along walls look natural)
    const want = Math.atan2(vx, vz);
    let da = want - state.yaw; da = Math.atan2(Math.sin(da), Math.cos(da));
    state.yaw += da * Math.min(1, dt * 12);
    state.speed = moved / dt;
  } else state.speed *= 0.8;
  state.moving = state.speed > 0.5;
  hero.position.set(state.heroX, 0, state.heroZ); hero.rotation.y = state.yaw;
  let ins = null; for (const e of enterables) if (e.update(state.heroX, state.heroZ)) ins = e.id; state.inside = ins;
  animateHero(dt);
}

let walkT = 0, idleT = 0, prevYaw = 0;
function animateHero(dt) {
  const u = hero.userData, w = Math.min(1, state.speed / SPEED);
  if (u.glb) { const wk = u.act.walk, id = u.act.idle; if (wk && id) { wk.setEffectiveWeight(w); id.setEffectiveWeight(1 - w); wk.timeScale = 0.6 + state.speed * 0.25; } u.mixer.update(dt); return; }
  walkT += dt * (4 + state.speed * 1.9); idleT += dt;
  const s = Math.sin(walkT) * 0.85 * w;
  u.legL.rotation.x = s; u.legR.rotation.x = -s;
  u.armL.rotation.x = -s * 0.6; u.armR.rotation.x = u.armRBase !== undefined ? u.armRBase + s * 0.08 : s * 0.45 - 0.1;
  const idle = 1 - w, br = Math.sin(idleT * 2);
  u.body.position.y = Math.abs(Math.cos(walkT)) * 0.07 * w + br * 0.012 * idle;
  u.armL.rotation.z = 0.1 + br * 0.02 * idle; u.armR.rotation.z = -0.1 - br * 0.02 * idle;
  u.head.rotation.y = Math.sin(idleT * 0.8) * 0.22 * idle;
  u.tab.rotation.x = -Math.abs(s) * (u.gown ? 0.12 : 0.35);
  if (u.hairBack) u.hairBack.rotation.x = 0.04 + w * 0.2 + Math.sin(idleT * 1.6) * 0.03 + Math.sin(walkT * 2) * 0.05 * w;
  if (u.glow) u.glow.opacity = 0.38 + 0.1 * Math.sin(idleT * 5);
  if (u.staff) u.staff.position.y = br * 0.01;
  let dy = state.yaw - prevYaw; dy = Math.atan2(Math.sin(dy), Math.cos(dy)); prevYaw = state.yaw;
  u.capeUpdate(idleT, w, THREE.MathUtils.clamp(-dy / Math.max(dt, 1e-3) * 0.06, -0.6, 0.6));
}

// ---------- camera ----------
const camPos = new THREE.Vector3(0, 8, 24), camLook = new THREE.Vector3(0, 1.5, 14);
const _want = new THREE.Vector3(), _look = new THREE.Vector3();
function updateCamera(dt, snap) {
  const portrait = innerHeight > innerWidth;
  const z = state.zoom || 1, close = z < 1, dist = close ? (portrait ? 7.0 : 6.0) * (z / 0.3) : (portrait ? 10.5 : 9), height = close ? 2.2 : (portrait ? 7.2 : 6.2);
  const want = _want.set(state.heroX + Math.sin(state.camYaw) * dist, height, state.heroZ + Math.cos(state.camYaw) * dist);
  const look = _look.set(state.heroX, close ? 1.05 : 1.6, state.heroZ);
  const k = snap ? 1 : 1 - Math.pow(0.0015, dt);
  camPos.lerp(want, k); camLook.lerp(look, k);
  camera.position.copy(camPos); camera.lookAt(camLook);
  sun.position.set(state.heroX + SUN_OFF.x, SUN_OFF.y, state.heroZ + SUN_OFF.z);
  sun.target.position.set(state.heroX, 0, state.heroZ);
}

function resize() {
  const w = innerWidth, h = innerHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / h; camera.fov = w / h < 1 ? 58 : 48; camera.updateProjectionMatrix();
}
addEventListener('resize', resize); addEventListener('orientationchange', () => setTimeout(resize, 150));
resize();

// ---------- loop ----------
const fpsEl = document.getElementById('fps');
let last = performance.now(), fpsAcc = 0, fpsFrames = 0, fps = 0, totalFrames = 0, simTime = 0;
let running = true;
document.addEventListener('visibilitychange', () => { running = !document.hidden; last = performance.now(); lastDraw = 0; adaptSkip = Math.max(adaptSkip, 30); });
// adaptive resolution: if frames average > 22 ms for ~1 s, shrink the render resolution (min 0.6x); never climb back above a level that failed.
let adaptT = 0, adaptN = 0, adaptSkip = 90;
function adaptRes(raw) {
  if (adaptSkip > 0) { adaptSkip--; return; }
  if (raw > 250) return;                       // tab switch / hitch, not load
  adaptT += raw; adaptN++;
  if (adaptT < 1000) return;
  const avg = adaptT / adaptN; adaptT = 0; adaptN = 0;
  if (avg > 22 && pr > 0.6) { prCeil = Math.max(0.6, pr * 0.98); pr = Math.max(0.6, pr * 0.82); renderer.setPixelRatio(pr); resize(); adaptSkip = 20; }
}
let lastDraw = 0;
function frame(now) {
  requestAnimationFrame(frame);
  if (!running) return;
  if (now - lastDraw < 11.5) return;            // cap at ~72 fps on 120/144 Hz monitors (75 Hz and below untouched)
  adaptRes(now - lastDraw); lastDraw = now;
  const dt = Math.min(0.05, (now - last) / 1000); last = now;
  updateHero(dt); updateCamera(dt, totalFrames === 0);
  simTime += dt;
  drops.forEach((m, i) => { const t = (simTime * 0.9 + i / drops.length) % 1; const a = i / drops.length * 6.28; m.position.set(Math.cos(a) * t * 1.6, 3.0 + Math.sin(t * 3.14) * 1.0 - t * 0.2, Math.sin(a) * t * 1.6); });
  renderer.render(scene, camera);
  totalFrames++; fpsAcc += dt; fpsFrames++;
  if (fpsAcc >= 0.5) { fps = fpsFrames / fpsAcc; fpsAcc = 0; fpsFrames = 0; fpsEl.textContent = fps.toFixed(0) + ' fps · ' + renderer.info.render.calls + ' calls'; }
  if (totalFrames === 2) { const l = document.getElementById('load'); l.style.opacity = 0; setTimeout(() => l.remove(), 500); setTimeout(() => { const h = document.getElementById('hint'); if (h) h.style.opacity = 0; }, 6000); }
}
requestAnimationFrame(frame);

window.__p3d = {
  state, glbInfo, colliders, get hero() { return hero; }, THREE, renderer, enterables,
  get fps() { return fps; }, get frames() { return totalFrames; },
  info: () => ({ calls: renderer.info.render.calls, triangles: renderer.info.render.triangles, geometries: renderer.info.memory.geometries, textures: renderer.info.memory.textures }),
  teleport(x, z) { state.heroX = x; state.heroZ = z; state.target = null; },
  setCamYaw(y) { state.camYaw = y; },
  setZoom(z) { state.zoom = z; },
  setHero, get heroIndex() { return HEROES.indexOf(hero); },
  tapAt: tapMoveTo,
};
