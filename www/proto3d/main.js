// Varnethryl 3D prototype: Liongate-style village. Standalone, does not touch the 2D game.
import * as THREE from './vendor/three.module.js';
import { makeAldricTextures, buildAldric } from './aldric.js';
import { makeHeroTextures, buildUmbral, buildSelene } from './heroes2.js';
import { CHARS } from './chars.js';
import { preload as preloadChars } from './texgen.js';
import { makeEnterable } from './interiors.js';
import { buildVillage, buildWalls, BUILDING_DEFS, WORLD_B, PK, KB } from './buildings.js';
import { fx, zoneKey, chunkStatics, mergeRoofs, mergeWalls, matClass, colorFill } from './bldkit.js';
import { readSave, planFromState, createSaver } from './save3d.js';
import { SpringBones } from './spring_bones.js';
import { SpringBones as SpringBonesV2 } from './spring_bones_v2.js';
import { createBump, makeActor, styleFor, findNodes, restoreNodes, applyPose } from './bump.js';
import { createFlags, passesWalls, stepAltitude } from './cheatflags.js';
import { createCinderFlight, cinderAnimationWeights } from './cinderflight.js';
import { initCheatBoot } from './cheatboot.js';
import { createCamRig } from './camrig.js';
import { initSettings } from './settingsboot.js';
import { loadPrefs, savePrefs, qualityPlan, followYaw } from './camprefs.js';
import { worldProfile, loadScale } from './charscale.js';
import { buildTownOutskirts } from './townlands.js';
import { buildHobgoblinCamps } from './hobcamps.js';
import { CITY_HALF, FROST_PORTAL, FROST_SUMMIT, TITAN_CENTER, FROST_REALM, terrainBiome, onLava } from './bossregions.js';
import { buildFrostRealm, frostElevation, FROST_EXIT } from './frostreach.js';
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
scene.fog = new THREE.Fog(0xdde8ee, 70, 180);

const camera = new THREE.PerspectiveCamera(50, 1, 0.5, 320);

// Lights: hemisphere fill + one shadow-casting sun that follows the hero
scene.add(new THREE.HemisphereLight(0xcfe6ff, 0x6a7a4a, 1.25));
const sun = new THREE.DirectionalLight(0xfff0d0, 2.2);
const SHADOW_SIZE = COARSE ? 1024 : 1536, SHADOW_R = 32;
sun.castShadow = true;
sun.shadow.mapSize.set(SHADOW_SIZE, SHADOW_SIZE);
Object.assign(sun.shadow.camera, { left: -SHADOW_R, right: SHADOW_R, top: SHADOW_R, bottom: -SHADOW_R, near: 1, far: 110 });
sun.shadow.bias = -0.0006; sun.shadow.normalBias = 0.03;
const SUN_OFF = new THREE.Vector3(-41, 77, 35);
scene.add(sun, sun.target);

// ---------- helpers ----------
const mats = {};
const M = (name, color, extra) => (mats[name] = new THREE.MeshLambertMaterial(Object.assign({ color }, extra)));
M('wall', 0xe9dcc0); M('wallB', 0xd2c2a0); M('stone', 0x9aa0a8); M('stoneD', 0x6f757e); M('wood', 0x7a5232);
M('roofR', 0xb5452f); M('roofB', 0x3d6aa8); M('roofG', 0x4b7d4a); M('door', 0x5a3a22);
M('glass', 0xffe9a0, { emissive: 0x6a5420 }); M('water', 0x4fa8d8, { emissive: 0x103050 });
M('trunk', 0x6b4a2b); M('leaf', 0x3e8a3a); M('leaf2', 0x57a043); M('gold', 0xe0b040, { emissive: 0x302000 });
for (const k of ['trunk', 'leaf', 'leaf2']) fx(mats[k], 'tree');   // wind sway (shared shader uniform)
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
const HS = 1.5;                 // character scale (hero, party, NPCs) so people are in proportion with the grand doors
let CH = worldProfile('', HS);   // active character's real-size profile (charscale.js): collision radius, speed, camera, reach
let HERO_R = CH.radiusW;
/* giants see further: fog, camera far plane, shadow frustum and chunk culling scale with the profile's camera distance (capped for phone perf) */
let VIEWK = 1;
function applyView() { const kf = Math.max(1, Math.min(5, CH.camDist)), k2 = Math.min(2.2, kf), sk = Math.min(3, kf); VIEWK = k2; scene.fog.near = 70 * k2; scene.fog.far = 180 * k2; camera.far = 320 * k2 * (kf > 2.2 ? 1.5 : 1); camera.updateProjectionMatrix(); const R = 24 * sk; Object.assign(sun.shadow.camera, { left: -R, right: R, top: R, bottom: -R, far: 110 * sk }); sun.shadow.camera.updateProjectionMatrix(); SUNK = sk; }
let SUNK = 1;
function applyChar(id) { CH = worldProfile(id || '', HS); HERO_R = CH.radiusW; try { applyView(); } catch (e) {} try { camRig.setProfile(CH); } catch (e) {} try { if (typeof FIGHT !== 'undefined' && FIGHT && FIGHT.cc && FIGHT.cc.setScale) FIGHT.cc.setScale(CH); } catch (e) {} }
const ZONE = { name: 'town', cx: 0, cz: 0, half: 0 };   // current walkable zone (town or the Wilds); half is set once WORLD is known
const WORLD = WORLD_B; // half extent (village grew for the 3D buildings)
ZONE.half = WORLD;
const START_Z = 14 * PK;
const grass = canvasTex(256, (g, s) => {
  g.fillStyle = '#5c9a45'; g.fillRect(0, 0, s, s);
  for (let i = 0; i < 2600; i++) { g.fillStyle = `hsl(${88 + rnd() * 30},${40 + rnd() * 20}%,${30 + rnd() * 18}%)`; g.fillRect(rnd() * s, rnd() * s, 2, 3); }
}, Math.round(41 * WORLD / (60 * PK)));
const cobble = canvasTex(256, (g, s) => {
  g.fillStyle = '#8d8579'; g.fillRect(0, 0, s, s);
  for (let y = 0; y < 8; y++) for (let x = 0; x < 8; x++) {
    const l = 52 + rnd() * 18; g.fillStyle = `hsl(35,10%,${l}%)`;
    g.fillRect(x * 32 + (y % 2) * 16 + 1, y * 32 + 1, 30, 30);
  }
}, 1);
const ground = mesh(new THREE.PlaneGeometry(new URLSearchParams(location.search).has('oldvillage') ? WORLD * 4 : CITY_HALF * 2, new URLSearchParams(location.search).has('oldvillage') ? WORLD * 4 : CITY_HALF * 2), new THREE.MeshLambertMaterial({ map: grass }), 0, 0, 0, null, false);
ground.rotation.x = -Math.PI / 2;
{ // plaza + paths (cobble)
  const cm = new THREE.MeshLambertMaterial({ map: cobble.clone() });
  cm.map.repeat.set(11 * PK, 11 * PK); cm.map.needsUpdate = true;
  const plaza = mesh(new THREE.CircleGeometry(13 * PK, 64), cm, 0, 0.02, 0, null, false); plaza.rotation.x = -Math.PI / 2;
  const pm = new THREE.MeshLambertMaterial({ map: cobble.clone() }); pm.map.repeat.set(1, 22 * PK * 2 * WORLD / (60 * PK)); pm.map.needsUpdate = true;
  const p1 = mesh(new THREE.PlaneGeometry(5 * KB, CITY_HALF * 2), pm, 0, 0.03, 0, null, false); p1.rotation.x = -Math.PI / 2;
  const p2 = mesh(new THREE.PlaneGeometry(CITY_HALF * 2, 4 * KB), pm, 0, 0.031, 0, null, false); p2.rotation.x = -Math.PI / 2; p2.material.map.repeat.set(24 * PK * WORLD / (60 * PK), 0.8 * KB);
}

function wallSeg(x1, z1, x2, z2) {
  const len = Math.hypot(x2 - x1, z2 - z1), h = 2.2, t = 1.2;
  const horiz = Math.abs(z2 - z1) < 0.01;
  mesh(new THREE.BoxGeometry(horiz ? len : t, h, horiz ? t : len), mats.stone, (x1 + x2) / 2, h / 2, (z1 + z2) / 2);
  addBoxCol((x1 + x2) / 2, (z1 + z2) / 2, horiz ? len : t, horiz ? t : len);
  const n = Math.floor(len / 1.6);
  for (let i = 0; i < n; i++) {
    const f = (i + 0.5) / n, px = x1 + (x2 - x1) * f, pz = z1 + (z2 - z1) * f;
    mesh(new THREE.BoxGeometry(horiz ? 0.8 : t, 0.5, horiz ? t : 0.8), mats.stone, px, h + 0.25, pz);
  }
}
// border: textured stone walls + watchtowers (see buildings.js); the south gate is the 3D Gatehouse (walkable tunnel)
const GATE_W = 4;
function tower(x, z, r = 2.6, h = 9) {
  mesh(new THREE.CylinderGeometry(r, r * 1.08, h, 12), mats.stone, x, h / 2, z);
  mesh(new THREE.CylinderGeometry(r * 1.2, r * 1.2, 0.6, 12), mats.stoneD, x, h + 0.3, z);
  mesh(new THREE.ConeGeometry(r * 1.3, 3.2, 12), mats.roofB, x, h + 2.2, z);
  addCircCol(x, z, r * 1.08);
}
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
const ectx = { scene, mats, colliders, multi: [] };
let LAD = null;   // ladders (ladders.js), created after the key set exists
// 26 sheet-based 3D buildings (guild, inn, smithy, temple, colosseum, keep ... see docs/proto3d-buildings/README.md). ?oldvillage keeps the original blocky village.
const SKINS = [];
const BLD_ON = new URLSearchParams(location.search).get('oldvillage') == null;
const drops = []; let dropMade = 0;
if (BLD_ON) {
  enterables.push(buildWalls(ectx, CITY_HALF, GATE_W));
  for (const b of buildVillage(ectx)) enterables.push(b);
  if (new URLSearchParams(location.search).get('nochunk') == null) { try { const r = chunkStatics(enterables.flatMap(e => e.parts || [e]), scene, 64); diag('static chunks: ' + r.before + ' -> ' + r.after); const rr = mergeRoofs(enterables.flatMap(e => e.parts || [e]), scene); diag('roofs: ' + rr.before + ' -> ' + rr.after); const rw = mergeWalls(enterables.flatMap(e => e.parts || [e]), scene); diag('walls: ' + rw.before + ' -> ' + rw.after); } catch (e) { console.error('chunkStatics', e.message, e.stack); } }
} else {
  wallSeg(-WORLD, -WORLD, WORLD, -WORLD); wallSeg(-WORLD, -WORLD, -WORLD, WORLD); wallSeg(WORLD, -WORLD, WORLD, WORLD); wallSeg(-WORLD, WORLD, -GATE_W - 3, WORLD); wallSeg(GATE_W + 3, WORLD, WORLD, WORLD);
  tower(-GATE_W - 3, WORLD, 2.6); tower(GATE_W + 3, WORLD, 2.6);
  enterables.push(makeEnterable(ectx, { id: 'inn', cx: -13, cz: -9, w: 9, d: 7, h: 4.6, sign: true, interior: 'inn' }));
  enterables.push(makeEnterable(ectx, { id: 'smithy', cx: 13, cz: -10, w: 7.5, d: 6.5, h: 4.2, roof: mats.roofB, wall: mats.wallB, interior: 'smith', rug2: true }));
  enterables.push(makeEnterable(ectx, { id: 'guildhall', cx: 0, cz: -19, w: 13, d: 7.5, h: 5.4, roof: mats.roofG, roofH: 4.2, sign: true, interior: 'hall' }));
  enterables.push(makeEnterable(ectx, { id: 'house', cx: -15, cz: 9, w: 6.4, d: 6.4, h: 3.8, roof: mats.roofR, interior: 'house' }));
  const fountain = new THREE.Group(); scene.add(fountain);
  mesh(new THREE.CylinderGeometry(3.2, 3.4, 0.9, 24), mats.stone, 0, 0.45, 0, fountain);
  mesh(new THREE.CylinderGeometry(2.8, 2.8, 0.3, 24), mats.water, 0, 0.82, 0, fountain, false);
  mesh(new THREE.CylinderGeometry(0.4, 0.55, 2.4, 10), mats.stone, 0, 1.6, 0, fountain);
  mesh(new THREE.CylinderGeometry(1.3, 0.8, 0.4, 16), mats.stone, 0, 2.7, 0, fountain);
  mesh(new THREE.CylinderGeometry(1.1, 1.1, 0.12, 16), mats.water, 0, 2.95, 0, fountain, false);
  for (let i = 0; i < 6; i++) { const m = mesh(new THREE.SphereGeometry(0.1, 6, 5), mats.water, 0, 3, 0, fountain, false); m.userData.keep = true; drops.push(m); }
  addCircCol(0, 0, 3.5);
}

// Extra wall-to-wall landscape, orchards and fields use the Wilds' chunked scenery approach.
// Keep the original 29 buildings, save coordinates and town↔Wilds portal unchanged.
let TOWN_LANDS = null;
if (BLD_ON) {
  try { TOWN_LANDS = buildTownOutskirts({ scene, colliders, world: WORLD, buildings: BUILDING_DEFS, spacing: PK });
    diag('Town expanded to ' + WORLD * 2 + ' units wide · walkable hills, valleys, mountains · landscape chunks: ' + TOWN_LANDS.chunkCount); }
  catch (e) { console.warn('town outskirts failed', e); diag('Town landscape fallback: ' + (e && e.message || e), true); }
}
// Camps are intentionally beyond the protected village wall, avoiding the Titan and frost summit.
let HOB_CAMPS_WORLD=null;
if(BLD_ON){try{
  HOB_CAMPS_WORLD=buildHobgoblinCamps(scene,(x,z)=>TOWN_LANDS?.heightAt(x,z)??0);
  diag('Hobgoblin camps: '+HOB_CAMPS_WORLD.sites.length+' placed in the outer regions');
}catch(e){console.warn('hobgoblin camp scenery unavailable',e);}}
// Original trees stay in the historic village/inner grounds; outer forests are chunked independently.
{
  const pts = [];
  const blocked = (x, z) => {
    if (Math.hypot(x, z) < 12 * PK) return true;
    for (const bd of BUILDING_DEFS) { if (Math.hypot(x - bd.cx * PK, z - bd.cz * PK) < (bd.id === 'temple' ? 30 : 16)) return true; const fr = Math.hypot(x - (bd.cx * PK + Math.sin(bd.rot || 0) * 22), z - (bd.cz * PK + Math.cos(bd.rot || 0) * 22)); if (fr < 22) return true; }   // keep building fronts (and the camera spot behind a hero at the door) clear of trees
    if (Math.abs(x) < 3.5 * KB) return true;                   // main road
    if (Math.abs(z) < 3 * KB) return true;
    for (const c of colliders) {
      if (c.type === 'box' && x > c.minX - 9 && x < c.maxX + 9 && z > c.minZ - 9 && z < c.maxZ + 9) return true;
      if (c.type === 'circle' && Math.hypot(x - c.x, z - c.z) < c.r + 4) return true;
    }
    return false;
  };
  let guard = 0;
  while (pts.length < (BLD_ON ? 230 : 56) && guard++ < 6000) {
    const treeLimit = Math.min(WORLD - 3, 161); const x = (rnd() * 2 - 1) * treeLimit, z = (rnd() * 2 - 1) * treeLimit;
    if (!blocked(x, z) && !pts.some(p => Math.hypot(p.x - x, p.z - z) < 5)) pts.push({ x, z, s: (0.8 + rnd() * 0.7) * 1.6 });
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
for (const [x, z] of (BLD_ON ? [] : [[-8.2, -4.2], [-8.6, -3.2], [9.2, -5.8], [8.4, 6.6]])) {
  mesh(new THREE.BoxGeometry(1, 1, 1), mats.wood, x, 0.5, z); addBoxCol(x, z, 1, 1);
}


// ---------- static merge: collapse world meshes into one mesh per material (cuts draw calls ~6x) ----------
function mergeStatic() {
  scene.updateMatrixWorld(true);
  const buckets = new Map(), remove = [];
  scene.traverse(o => {
    if (!o.isMesh || o.isInstancedMesh || o.isSkinnedMesh || o.userData.keep) return;
    const cl = matClass(o.material); if (!o.geometry.boundingBox) o.geometry.computeBoundingBox(); const bb = o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld), zk = zoneKey((bb.min.x + bb.max.x) / 2, (bb.min.z + bb.max.z) / 2) + '|' + cl.key;
    if (!buckets.has(zk)) buckets.set(zk, { cl, list: [], n: 0, cv: 0 });
    const b = buckets.get(zk); b.list.push(o); remove.push(o);
  });
  for (const b of buckets.values()) {
    const parts = b.list.map(o => { const g = (o.geometry.index ? o.geometry.toNonIndexed() : o.geometry.clone()); g.applyMatrix4(o.matrixWorld); return g; });
    let n = 0, cv = 0; parts.forEach((g, i) => { const c = g.attributes.position.count; n += c; if (b.list[i].castShadow) cv += c; });
    const pos = new Float32Array(n * 3), nor = new Float32Array(n * 3), uv = new Float32Array(n * 2), col = b.cl.vc ? new Float32Array(n * 3) : null; let o3 = 0, o2 = 0;
    parts.forEach((g, i) => {
      const cnt = g.attributes.position.count; pos.set(g.attributes.position.array, o3); nor.set(g.attributes.normal.array, o3); if (g.attributes.uv) uv.set(g.attributes.uv.array, o2); if (col) colorFill(col, cnt, o3, b.list[i].material.color);
      o3 += cnt * 3; o2 += cnt * 2; g.dispose();
    });
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3)); geo.setAttribute('normal', new THREE.BufferAttribute(nor, 3)); geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2)); if (col) geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
    const m = new THREE.Mesh(geo, b.cl.mat); m.castShadow = cv * 2 > n; m.receiveShadow = true; scene.add(m);
  }
  for (const o of remove) { o.parent.remove(o); o.geometry.dispose(); }
}
mergeStatic();

// ---------- hero: Sir Aldric (see aldric.js) ----------
const ALDRIC_TEX = await makeAldricTextures();
const HT = await makeHeroTextures();
try { await preloadChars(); } catch (e) { console.warn('chars preload', e); }
const HEROES = [buildAldric(ALDRIC_TEX), buildUmbral(HT), buildSelene(HT)];
const HERO_NAMES = ['Sir Aldric', 'Darius Umbral', 'Selene Frostveil'];
let hero = HEROES[0];
let startHero = 0;
let saver;
HEROES.forEach((h, i) => { h.position.set(0, 0, START_Z); h.visible = i === 0; scene.add(h); });
function setHero(i) { applyChar(GLB_IDS[i]); { const st = styleFor(GLB_IDS[i]); playerAct.style = st; playerAct.str = st.str; } hero.visible = false; hero = HEROES[i]; hero.visible = true; hero.position.set(state.heroX, 0, state.heroZ); hero.rotation.y = state.yaw; if (typeof refreshSel === 'function') refreshSel(i); if (typeof saver !== 'undefined') saver.mark(); }
// ---------- GLB heroes: every model in models/, loaded lazily (procedural fallback for the first 3) ----------
const GLB_IDS = ['aldric', 'darius', 'selene', 'elira', 'orin', 'seraphine', 'talia', 'finn', 'brynn', 'mirelle', 'nyx', 'vesper', 'thorne', 'rook', 'asha', 'rowan', 'kael', 'cedric', 'morwen', 'garruk'];
const GLB_NAMES = ['Sir Aldric', 'Darius Umbral', 'Selene Frostveil', 'Lady Elira', 'Orin Ashlance', 'Dame Seraphine', 'Talia Stormcall', 'Finn Valecourt', 'Brynn Cogwright', 'Mirelle Thornroot', 'Nyx Varrin', 'Vesper Crowe', 'Brother Thorne', 'Rook Wildbane', 'Asha Ironfist', 'Rowan Firebrand', 'Kael Runebinder', 'Cedric Vale', 'Morwen Blackveil', 'Garruk Stonefist'];
const EXTRA = [["n:mortimer_new", "Mortimer (NEW)", "proto3d/models-new/mortimer_cl_arms.glb"], ["n:player_pikachu", "Player Pikachu (NEW)", "proto3d/models-new/player_pikachu_cl_arms.glb"], ["n:lunara_new", "Lunara (NEW)", "proto3d/models-new/lunara_cl_arms.glb"], ["n:marella_new", "Marella (NEW)", "proto3d/models-new/marella_cl_arms.glb"], ["n:vaelthryx_straight_rig", "Balthrix (10×)", "proto3d/models-new/vaelthryx_straight_rig.glb"], ["n:vaelthryx_new", "Balthrix (NEW)", "proto3d/models-new/vaelthryx_new.glb"], ["n:vaelthryx_new6", "Balthrix (NEW 6)", "proto3d/models-new/vaelthryx_new6.glb"], ["n:owner_pika1", "Owner (NEW)", "proto3d/models-new/owner_pika1.glb"], ["n:frosttroll_a", "Frost Troll (A)", "proto3d/models-new/frosttroll_a.glb"], ["n:frosttroll_b", "Frost Troll (B)", "proto3d/models-new/frosttroll_b.glb"], ["n:ssylthar_new", "Ssylthar (NEW)", "proto3d/models-new/ssylthar_new.glb"], ["n:ashentitan_new", "Ashentitan (NEW)", "proto3d/models-new/ashentitan_cl_arms.glb"], ["n:coral_new", "Coral (NEW)", "proto3d/models-new/coral_cl_arms.glb"], ["n:cinder_new", "Cinder (NEW)", "proto3d/models-new/cinder_new.glb"], ["n:snowy_new4", "Snowy (NEW)", "proto3d/models-new/snowy_cl_arms.glb"], ["n:zephyr_new2", "Zephyr (NEW)", "proto3d/models-new/zephyr_new2.glb"], ["n:garruk_new4", "Garruk (NEW)", "proto3d/models-new/garruk_new4.glb"], ["n:garruk_new5", "Garruk (NEW 5)", "proto3d/models-new/garruk_new5_arms.glb"], ["n:darius_new6", "Darius (NEW 6)", "proto3d/models-new/darius_new6_arms.glb"], ["n:pip_new2", "Pip (NEW 2)", "proto3d/models-new/pip_new2.glb"], ["n:owner", "Owner (NEW)", "proto3d/models-new/owner.glb"], ["n:asha_new3", "Asha (NEW)", "proto3d/models-new/asha_cl_arms.glb"], ["n:thrain_new4", "Thrain (NEW)", "proto3d/models-new/thrain_cl_arms.glb"], ["n:wren_new3", "Wren (NEW)", "proto3d/models-new/wren_cl_arms.glb"], ["n:ember_new3", "Ember (NEW)", "proto3d/models-new/ember_new3.glb"], ["p:aldric", "Aldric [PLACEHOLDER]", "proto3d/models-placeholder/aldric_new.glb"], ["p:briar", "Briar [PLACEHOLDER]", "proto3d/models-placeholder/briar_new.glb"], ["p:brynn", "Brynn [PLACEHOLDER]", "proto3d/models-placeholder/brynn_new.glb"], ["p:cedric", "Cedric [PLACEHOLDER]", "proto3d/models-placeholder/cedric_new.glb"], ["p:elira", "Elira [PLACEHOLDER]", "proto3d/models-placeholder/elira_new.glb"], ["p:finn", "Finn [PLACEHOLDER]", "proto3d/models-placeholder/finn_new.glb"], ["p:frosttroll", "Frosttroll [PLACEHOLDER]", "proto3d/models-placeholder/frosttroll_new.glb"], ["p:hearth", "Hearth [PLACEHOLDER]", "proto3d/models-placeholder/hearth_new.glb"], ["p:hobgoblin", "Hobgoblin [PLACEHOLDER]", "proto3d/models-placeholder/hobgoblin_new.glb"], ["p:hydrella", "Hydrella [PLACEHOLDER]", "proto3d/models-placeholder/hydrella_new.glb"], ["p:kael", "Kael [PLACEHOLDER]", "proto3d/models-placeholder/kael_new.glb"], ["p:kestrel", "Kestrel [PLACEHOLDER]", "proto3d/models-placeholder/kestrel_new.glb"], ["p:lorian", "Lorian [PLACEHOLDER]", "proto3d/models-placeholder/lorian_new.glb"], ["p:lunara", "Lunara [PLACEHOLDER]", "proto3d/models-placeholder/lunara_new.glb"], ["p:marella", "Marella [PLACEHOLDER]", "proto3d/models-placeholder/marella_new.glb"], ["p:mirelle", "Mirelle [PLACEHOLDER]", "proto3d/models-placeholder/mirelle_new.glb"], ["p:morwen", "Morwen [PLACEHOLDER]", "proto3d/models-placeholder/morwen_new.glb"], ["p:mossgut", "Mossgut [PLACEHOLDER]", "proto3d/models-placeholder/mossgut_new.glb"], ["p:neris", "Neris [PLACEHOLDER]", "proto3d/models-placeholder/neris_new.glb"], ["p:nyx", "Nyx [PLACEHOLDER]", "proto3d/models-placeholder/nyx_new.glb"], ["p:orin", "Orin [PLACEHOLDER]", "proto3d/models-placeholder/orin_new.glb"], ["p:pip", "Pip [PLACEHOLDER]", "proto3d/models-placeholder/pip_new.glb"], ["p:rook", "Rook [PLACEHOLDER]", "proto3d/models-placeholder/rook_new.glb"], ["p:rowan", "Rowan [PLACEHOLDER]", "proto3d/models-placeholder/rowan_new.glb"], ["p:seraphine", "Seraphine [PLACEHOLDER]", "proto3d/models-placeholder/seraphine_new.glb"], ["p:stonetroll", "Stonetroll [PLACEHOLDER]", "proto3d/models-placeholder/stonetroll_new.glb"], ["p:talia", "Talia [PLACEHOLDER]", "proto3d/models-placeholder/talia_new.glb"], ["p:thorne", "Thorne [PLACEHOLDER]", "proto3d/models-placeholder/thorne_new.glb"], ["p:valen", "Valen [PLACEHOLDER]", "proto3d/models-placeholder/valen_new.glb"], ["p:vesper", "Vesper [PLACEHOLDER]", "proto3d/models-placeholder/vesper_new.glb"], ["p:wyvern", "Wyvern [PLACEHOLDER]", "proto3d/models-placeholder/wyvern_new.glb"], ["p:zephyr", "Zephyr [PLACEHOLDER]", "proto3d/models-placeholder/zephyr_new.glb"], ["o:briar", "Briar", "proto3d/models-beth/briar.glb"], ["o:cinder", "Cinder", "proto3d/models-beth/cinder.glb"], ["o:coral", "Coral", "proto3d/models-beth/coral.glb"], ["o:ember", "Ember", "proto3d/models-beth/ember.glb"], ["o:frosttroll", "Frosttroll", "proto3d/models-beth/frosttroll.glb"], ["o:hawk", "Hawk", "proto3d/models-beth/hawk.glb"], ["o:hearth", "Hearth", "proto3d/models-beth/hearth.glb"], ["o:hobgoblin", "Hobgoblin", "proto3d/models-beth/hobgoblin.glb"], ["o:hydrella", "Hydrella", "proto3d/models-beth/hydrella.glb"], ["o:kestrel", "Kestrel", "proto3d/models-beth/kestrel.glb"], ["o:lorian", "Lorian", "proto3d/models-beth/lorian.glb"], ["o:lunara", "Lunara", "proto3d/models-beth/lunara.glb"], ["o:marella", "Marella", "proto3d/models-beth/marella.glb"], ["o:mortimer", "Mortimer", "proto3d/models-beth/mortimer.glb"], ["o:mossgut", "Mossgut", "proto3d/models-beth/mossgut.glb"], ["o:neris", "Neris", "proto3d/models-beth/neris.glb"], ["o:pip", "Pip", "proto3d/models-beth/pip.glb"], ["o:snowy", "Snowy", "proto3d/models-beth/snowy.glb"], ["o:ssylthar", "Ssylthar", "proto3d/models-beth/ssylthar.glb"], ["o:stonetroll", "Stonetroll", "proto3d/models-beth/stonetroll.glb"], ["o:thrain", "Thrain", "proto3d/models-beth/thrain.glb"], ["o:vaelthryx", "Balthrix", "proto3d/models-beth/vaelthryx.glb"], ["o:valen", "Valen", "proto3d/models-beth/valen.glb"], ["o:wren", "Wren", "proto3d/models-beth/wren.glb"], ["o:wyvern", "Wyvern", "proto3d/models-beth/wyvern.glb"], ["o:zephyr", "Zephyr", "proto3d/models-beth/zephyr.glb"], ["wolf", "Wolf", "proto3d/models/wolf.glb"]];   // [id, label, url]: every other model we have, playable as a hero via the selector (native metre scale)
// Owner: ONE stable file name. To swap in a newer rig (owner_new4...): tools/swap_owner.sh /workspace/rigged/owner_new5 (copies <name>.glb + <name>.cloth.json over models-new/owner.*)
const CLOTH = new Set(["n:ember_new3", "n:owner", "n:owner_pika1", "n:asha_new3", "n:ashentitan_new", "n:coral_new", "n:darius_new6", "n:lunara_new", "n:marella_new", "n:mortimer_new", "n:player_pikachu", "n:snowy_new4", "n:thrain_new4", "n:wren_new3"]);   // models shipped with <name>.cloth.json (runtime/spring_bones_v2.js)
const EXTRA_SCALE = {}; // lore-height normalization happens once, centrally in loadScale() for both Frost Troll brothers and Titan variants.
const SPEEDS = { 'n:owner': { walk: 1.486, run: 2.28, map:{walk:'Walking',run:'Running'} }, 'n:owner_pika1': { walk: 1.5, run: 3.2 }, 'n:garruk_new5': { walk: 1.1, run: 3.2 }, 'n:darius_new6': { walk: 1.1, run: 3.2 }, 'n:pip_new2': { walk: 0.26, trot: 0.76, run: 1.4 }, 'n:ashentitan_new': { walk: 5.156, run: 10.687 }, 'n:ember_new3': { walk: 0.533, trot: 1.012, run: 2.158 }, 'n:frosttroll_a': { walk: 4.212, run: 11.796 }, 'n:frosttroll_b': { walk: 4.5, run: 10.5 }, 'n:vaelthryx_new6': { walk: 9.57, run: 14.77 }, 'n:thrain_new4': { walk: 0.85, run: 1.8 }, 'n:wren_new3': { walk: 0.45, run: 1.23 }, 'n:cinder_new': { walk: 0.65, run: 1.95 } };   // per-clip ground speed (native m/s) from Beth's audit logs: drives clip blend + playback rate so feet don't slide
/* Beth's smoothed blocky models (_smooth.glb): extra 'Smooth' variant for characters that already exist; originals stay the default. Loaded on demand (only when picked). */
const SMOOTH_NAMES = ['aldric', 'briar', 'brynn', 'cedric', 'elira', 'finn', 'hawk', 'hearth', 'hobgoblin', 'hydrella', 'kael', 'kestrel', 'lorian', 'mirelle', 'morwen', 'mossgut', 'neris', 'nyx', 'orin', 'rook', 'rowan', 'seraphine', 'stonetroll', 'talia', 'thorne', 'valen', 'vesper', 'wolf', 'wyvern'];   // frosttroll_smooth intentionally not used (old 1.8 m base): frosttroll_a4 is the troll
{ const have = new Set(GLB_IDS.map(id => id.replace(/^[a-z]:/, ''))); for (const n of SMOOTH_NAMES) if (have.has(n)) EXTRA.push(['n:' + n + '_smooth', n + ' (SMOOTH)', 'proto3d/models-new/' + n + '_smooth.glb']); }
// APPEND AFTER all existing smooth variants: never shift saved character indices.
EXTRA.push(['n:vaelthryx_straight_rig_50', 'Balthrix (50×)', 'proto3d/models-new/vaelthryx_straight_rig.glb']);
EXTRA.push(['n:ashentitan_40', 'Ashen Titan (legacy slot · 15×)', 'proto3d/models-new/ashentitan_cl_arms.glb']);
EXTRA.push(['n:ashentitan_20', 'Ashen Titan (15×)', 'proto3d/models-new/ashentitan_cl_arms.glb']);
EXTRA.push(['n:ashentitan_60', 'Ashen Titan (60×)', 'proto3d/models-new/ashentitan_cl_arms.glb']);
const EXTRA_URL = {}; for (const [id, label, url] of EXTRA) { GLB_IDS.push(id); EXTRA_URL[id] = url; }
const glbInfo = { loaded: [], failed: [], pending: [], kb: {} };
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
      const mtx = new THREE.Matrix4().multiplyMatrices(inv, o.matrixWorld); nm.getNormalMatrix(mtx); const bi = boneIdx.get(o.parent); const flip = mtx.determinant() < 0;   // mirrored parts (negative scale) need their triangle winding reversed or the inside shows
      for (let i = 0; i < cnt; i++, k++) {
        const ii = flip ? (i % 3 === 1 ? i + 1 : i % 3 === 2 ? i - 1 : i) : i, v = ix ? ix.getX(ii) : ii;
        tmp.fromBufferAttribute(P, v).applyMatrix4(mtx); pos[k * 3] = tmp.x; pos[k * 3 + 1] = tmp.y; pos[k * 3 + 2] = tmp.z;
        tmp.fromBufferAttribute(N, v).applyMatrix3(nm).normalize(); nor[k * 3] = tmp.x; nor[k * 3 + 1] = tmp.y; nor[k * 3 + 2] = tmp.z;
        if (U) { uv[k * 2] = U.getX(v); uv[k * 2 + 1] = U.getY(v); }
        si[k * 4] = bi; sw[k * 4] = 1;
      }
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3)); geo.setAttribute('normal', new THREE.BufferAttribute(nor, 3)); geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    geo.setAttribute('skinIndex', new THREE.BufferAttribute(si, 4)); geo.setAttribute('skinWeight', new THREE.BufferAttribute(sw, 4));
    const sm = new THREE.SkinnedMesh(geo, mat); sm.castShadow = true; sm.receiveShadow = false; sm.frustumCulled = false; sm.name = 'merged'; SKINS.push(sm);
    root.add(sm); sm.updateMatrixWorld(true); sm.bind(skeleton, sm.matrixWorld);
    for (const o of list) { o.parent.remove(o); o.geometry.dispose(); removed++; }
  }
  return removed;
}
const CLOTHCFG = {};
let LOCO_FORCE = null;   // test hook: pretend the hero moves at this ground speed (world units/s)
// locomotion blend: models with per-clip speeds (SPEEDS) blend idle -> walk -> trot -> run by real ground speed and play each clip at speed/clipSpeed so feet stay planted; others use the legacy walk/idle blend
function locoAnim(u, sp) {
  const A = u.act, S = u.speeds;
  if (S && A.idle) {
    const v = sp / u.mscale, L = [['walk', S.walk], ['trot', S.trot], ['run', S.run]].filter(([k, c]) => A[k] && c);
    const wt = { idle: 0 }; for (const [k] of L) wt[k] = 0;
    if (v <= L[0][1]) { wt[L[0][0]] = v / L[0][1]; wt.idle = 1 - wt[L[0][0]]; }
    else { let i = 0; while (i < L.length - 1 && v > L[i + 1][1]) i++; if (i >= L.length - 1) wt[L[L.length - 1][0]] = 1; else { const t = (v - L[i][1]) / (L[i + 1][1] - L[i][1]); wt[L[i][0]] = 1 - t; wt[L[i + 1][0]] = t; } }
    const ov = 1 - (u.ovr || 0); A.idle.setEffectiveWeight(wt.idle * ov);
    for (const [k, c] of L) { A[k].setEffectiveWeight(wt[k] * ov); A[k].timeScale = Math.max(0.5, Math.min(2.4, v / c)); }
    return;
  }
  const wk = A.walk, id = A.idle; if (wk && id) { const w = Math.min(1, sp / SPEED); { const ov = 1 - (u.ovr || 0); wk.setEffectiveWeight(w * ov); id.setEffectiveWeight((1 - w) * ov); } wk.timeScale = 0.6 + sp * 0.25; }
}
// Low-cost phoenix embers follow Cinder's wing tips and tail (one Points draw call).
// No particles are attached to the bones; the original GLB and skinning remain unchanged.
function initCinderEmbers(root, model) {
  const names = ['wing3_L', 'wing3_R', 'tail'];
  const bones = names.map(name => model.getObjectByName(name));
  if (bones.some(b => !b)) return;
  const N = 27, data = new Float32Array(N * 3), colors = new Float32Array(N * 3);
  for (let i = 0; i < N; i++) { colors[i * 3] = 1; colors[i * 3 + 1] = 0.28 + (i % 4) * 0.16; colors[i * 3 + 2] = 0.035; }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(data, 3).setUsage(THREE.DynamicDrawUsage));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  const material = new THREE.PointsMaterial({ size: 0.095, transparent: true, opacity: 0.8, depthWrite: false, blending: THREE.AdditiveBlending, vertexColors: true });
  const embers = new THREE.Points(geometry, material); embers.frustumCulled = false; root.add(embers);
  const bases = bones.map(() => new THREE.Vector3()), p = new THREE.Vector3(); let t = 0;
  root.userData.cinderEmbers = { update(dt) {
    t += dt;
    root.updateWorldMatrix(true, true);
    bones.forEach((b, j) => { b.getWorldPosition(p); bases[j].copy(root.worldToLocal(p)); });
    for (let i = 0; i < N; i++) {
      const j = i % 3, phase = (t * (0.85 + (i % 5) * .08) + (i / N)) % 1, k = i * 3, q = bases[j];
      data[k] = q.x + Math.sin(i * 9.7 + t * 4) * phase * .12;
      data[k + 1] = q.y + phase * .28;
      data[k + 2] = q.z + Math.cos(i * 6.3 + t * 3) * phase * .10;
    }
    geometry.attributes.position.needsUpdate = true;
  } };
}
function wrapGLB(g, id, blocky) {
  const root = new THREE.Group(); const m = g.scene; root.add(m);
  m.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = false; } });
  m.updateMatrixWorld(true); const box = new THREE.Box3().setFromObject(m);   // measured BEFORE the rigid-part merge: the merged SkinnedMesh bounding box is NaN, which silently skipped scaling
  if (new URLSearchParams(location.search).get('nomerge') == null) { m.updateMatrixWorld(true); mergeRigidParts(m); }
  m.traverse(o => { if (o.isSkinnedMesh && o.name !== 'merged') { o.frustumCulled = false; if (!SKINS.includes(o)) SKINS.push(o); } });
  const hgt = box.max.y - box.min.y;
  if (hgt > 0.01) { const BK_H = { 'o:vaelthryx': 5.1 };   // blocky builders authored smaller than their GLB: match the GLB's in-game height so swapping doesn't jump
    const sc = (blocky && BK_H[id]) ? BK_H[id]/hgt : EXTRA_URL[id] ? 0.947*HS*(EXTRA_SCALE[id]||1)*loadScale(id,hgt) : worldProfile(id,HS).heightW/hgt;   // extra models are authored in metres (hero 1.9 m = 1.8 HS); the old 20 heroes are height-normalised
    m.scale.multiplyScalar(sc); m.position.y -= box.min.y * sc; }
  m.traverse(o => { if (o.isMesh) for (const mt of [].concat(o.material)) if (mt && mt.alphaTest > 0) { mt.transparent = false; mt.depthWrite = true; mt.needsUpdate = true; } });   // glTF alphaMode MASK (e.g. Garruk's cape): cut-out, sorted by depth, casts a cut-out shadow
  // Temporary Owner integration: attach the purple blade to the animated right-hand bone.
  // Keep the original rig/mesh untouched so cape skinning can be refined later.
  if (id === 'n:owner' && g.animations.some(c => c.name === 'Walking')) {
    const hand = m.getObjectByName('mixamorig:RightHand');
    if (hand) {
      const saber = new THREE.Group(); saber.name = 'OwnerPurpleSaber'; hand.add(saber);
      saber.position.set(0, .03, 0);
      const grip = new THREE.Mesh(new THREE.CylinderGeometry(.028, .035, .24, 12), new THREE.MeshStandardMaterial({color:0x999ba5,metalness:.85,roughness:.2}));
      grip.position.y=.12; saber.add(grip);
      const blade = new THREE.Mesh(new THREE.CylinderGeometry(.018,.018,.95,12), new THREE.MeshBasicMaterial({color:0xa685ff}));
      blade.position.y=.71; saber.add(blade);
      const glow = new THREE.PointLight(0x8b5cff,1.5,2); glow.position.y=.6; saber.add(glow);
    }
  }
  const mixer = new THREE.AnimationMixer(m), act = {}, spd = SPEEDS[id] || null, mscale = hgt > 0.01 ? (EXTRA_URL[id] ? 0.947*HS*(EXTRA_SCALE[id]||1)*loadScale(id,hgt) : worldProfile(id,HS).heightW/hgt) : 1;
  for (const c of g.animations) act[c.name] = mixer.clipAction(c);
  // Normalize animation names across imported Meshy/Mixamo models without editing their skeletons.
  // A missing rig is NOT magically rigged: leave it intact and report it for proper skinning.
  for (const clip of g.animations) {
    const n = clip.name.toLowerCase().replace(/[^a-z0-9]/g, '');
    const role = /idle|breath|stand|rest/.test(n) ? 'idle' :
      /run|sprint|gallop|charge/.test(n) ? 'run' :
      /walk|stride|trot|locomotion/.test(n) ? 'walk' : null;
    if (role && !act[role]) act[role] = act[clip.name];
  }
  if (EXTRA_URL[id] && !g.animations.length) diag('Model ' + id + ' has no animation clips; needs a real rig/animation pass.');
  if (spd && spd.map) for (const k in spd.map) if (act[spd.map[k]]) act[k] = act[spd.map[k]];   // e.g. serpent: walk/run = slither/slither_fast
  if (act.idle) act.idle.play(); if (act.walk) act.walk.play(); if (spd) for (const k of ['trot', 'run']) if (act[k]) { act[k].play(); act[k].setEffectiveWeight(0); }
  if (id === 'n:cinder_new') for (const k of ['hover', 'flap', 'glide', 'dive', 'land']) if (act[k]) { act[k].play(); act[k].setEffectiveWeight(0); }
  root.userData = { glb: true, mixer, act, all: Object.assign({}, act), capeUpdate() {}, speeds: spd, mscale, heightW: hgt > 0.01 ? hgt * mscale : 0 };
  // Cinder's authored wing and tail clips must NOT be re-aimed by spring physics.
  // The generic spring-bone family matches wing1/wing2/wing3 and creates rubbery, overlapping wing flaps.
  if (id !== 'n:cinder_new') try { const cfg = CLOTHCFG[id]; root.userData.sb = cfg ? new SpringBonesV2(m, { clips: g.animations, config: cfg }) : new SpringBones(m, { clips: g.animations }); } catch (e) { console.warn('spring bones', e); }
  if (id === 'n:cinder_new') initCinderEmbers(root, m);
  return root;
}
const ASSET_V = '1.2.3';   // stamped by tools/build_sw.py from package.json: busts any stale WebView/HTTP cache of the model files after an app update
const gl = new GLTFLoader();
const glbPromise = {};
// Robust fetch: reports HTTP status / type / size / magic bytes, retries once with a cache-busting URL (bypasses a stale service-worker entry).
async function fetchGLB(id) {
  let lastErr = '';
  // If the player's newer 18-bone / 4-clip Owner rig has been uploaded, use it.
  // Old Owner asset remains the automatic fallback: no broken saved characters.
  const rigV2 = id === 'n:owner' ? 'varnethryl-owner-test/owner-animated.glb' : null;
  for (let attempt = 0; attempt < 2; attempt++) {
    const url = (rigV2 && !attempt ? rigV2 : (EXTRA_URL[id] || 'proto3d/models/' + id + '.glb')) + '?v=' + ASSET_V + (attempt ? '&r=' + Date.now() : '');
    try {
      const r = await fetch(url, attempt ? { cache: 'reload' } : undefined);
      if (!r.ok) { lastErr = 'HTTP ' + r.status; continue; }
      const buf = await r.arrayBuffer();
      const magic = new TextDecoder().decode(new Uint8Array(buf, 0, Math.min(4, buf.byteLength)));
      if (magic !== 'glTF') { lastErr = 'not a GLB (type ' + r.headers.get('content-type') + ', ' + buf.byteLength + ' bytes, starts "' + magic.replace(/[^\x20-\x7e]/g, '?') + '")'; continue; }
      if (CLOTH.has(id) && !CLOTHCFG[id]) { try { const cr = await fetch(url.split('?')[0].replace(/\.glb$/, '.cloth.json') + '?v=' + ASSET_V); if (cr.ok) CLOTHCFG[id] = await cr.json(); } catch (_) {} }
      return buf;
    } catch (e) { lastErr = 'fetch error: ' + (e && e.message || e); }
  }
  throw new Error(lastErr);
}
// slot gi: models 0-2 replace the procedural hero; others get a placeholder group until the GLB arrives
function loadGlbHero(gi) {
  const id = GLB_IDS[gi];
  if (VAR[gi] && VAR[gi].glb) { showVariant(gi, VAR[gi].glb); return Promise.resolve(HEROES[gi]); }
  if (glbPromise[gi]) return glbPromise[gi];
  glbInfo.pending.push(id); diag('loading ' + id + '.glb ...');
  const fail = (why) => { console.warn('GLB failed', id, why); glbInfo.failed.push(id); glbInfo.pending = glbInfo.pending.filter(x => x !== id); glbInfo.errors = glbInfo.errors || {}; glbInfo.errors[id] = String(why); diag('3D model "' + id + '" failed: ' + why + (HEROES[gi] && HEROES[gi].children.length ? ' - showing simple stand-in' : ''), true); delete glbPromise[gi]; return HEROES[gi]; };
  return glbPromise[gi] = fetchGLB(id).then(buf => new Promise(res => {
    gl.parse(buf, '', g => {
      try {
        const w = wrapGLB(g, id), old = HEROES[gi];
        w.visible = false; scene.add(w);
        if (old) { w.visible = old.visible; w.position.copy(old.position); w.rotation.copy(old.rotation); scene.remove(old); if (hero === old) hero = w; }
        (VAR[gi] || (VAR[gi] = {})).glb = w; HEROES[gi] = w; glbInfo.loaded.push(id); glbInfo.kb[id] = Math.round(buf.byteLength / 1024);
        glbInfo.pending = glbInfo.pending.filter(x => x !== id); diag('3D model "' + id + '" loaded (' + Math.round(buf.byteLength / 1024) + ' KB, build ' + ASSET_V + ')'); res(HEROES[gi]);
      } catch (e) { res(fail('wrap: ' + (e && e.message || e))); }
    }, err => res(fail('parse: ' + (err && err.message || err))));
  }), e => fail(e && e.message || e));
}
// ---------- blocky (procedural, chars.js rigs) vs GLB model per character ----------
// Default is BLOCKY for every character that has a builder (CHARS: the 20 heroes + wolf); GLB models are an optional per-character / global toggle.
const DEFAULT_MODEL = 'blocky';
const VAR = {};   // slot -> { blocky, glb } cached variants (both kept so toggling never reloads or jumps)
const bk = id => CHARS[id] ? id : (id.startsWith('o:') && CHARS[id.slice(2)] ? id.slice(2) : null);   // blocky builder key for a model id
function modeFor(id) {
  if (!bk(id)) return 'glb';
  if (!useGLB) return 'blocky';
  const q = new URLSearchParams(location.search).get('model'); if (q === 'glb' || q === 'blocky') return q;
  try { const v = localStorage.getItem('vn_model_' + id) || localStorage.getItem('vn_model'); if (v === 'glb' || v === 'blocky') return v; } catch (_) {}
  return DEFAULT_MODEL;
}
function makeBlocky(id) { const rig = CHARS[bk(id)].build(); const w = wrapGLB({ scene: rig.root, animations: rig.clips() }, id, true); w.userData.blocky = true; return w; }
function showVariant(gi, w) {
  const old = HEROES[gi]; if (old === w) return;
  if (!w.parent) scene.add(w); w.visible = old.visible; w.position.copy(old.position); w.rotation.copy(old.rotation); old.visible = false;
  if (!old.userData.glb) scene.remove(old);                 // procedural stand-ins / empty placeholders are dropped, cached variants stay (hidden)
  if (hero === old) hero = w; HEROES[gi] = w;
}
function loadHero(gi) {
  const id = GLB_IDS[gi];
  if (modeFor(id) === 'blocky') {
    const v = VAR[gi] || (VAR[gi] = {});
    if (!v.blocky) { try { v.blocky = makeBlocky(id); v.blocky.visible = false; scene.add(v.blocky); glbInfo.blocky = (glbInfo.blocky || []).concat(id); } catch (e) { console.warn('blocky failed', id, e); diag('blocky "' + id + '" failed: ' + (e && e.message || e), true); (glbInfo.errors = glbInfo.errors || {})[id] = 'blocky: ' + (e && e.message || e); } }
    if (v.blocky) { showVariant(gi, v.blocky); return Promise.resolve(HEROES[gi]); }
  }
  if (!useGLB) return Promise.resolve(HEROES[gi]);
  return loadGlbHero(gi);
}
for (let i = HEROES.length; i < GLB_IDS.length; i++) { const ph = new THREE.Group(); ph.visible = false; scene.add(ph); HEROES.push(ph); HERO_NAMES.push(i < GLB_NAMES.length ? GLB_NAMES[i] : EXTRA[i - GLB_NAMES.length][1]); }
const heroKind = w => w.userData.blocky ? 'blocky' : w.userData.glb ? 'glb' : 'none';
async function selectHero(i) { if (heroKind(HEROES[i]) !== modeFor(GLB_IDS[i])) await loadHero(i); if (!HEROES[i].children.length) return; const prev = GLB_IDS[HEROES.indexOf(hero)]; setHero(i); if (typeof swapFollower === 'function') swapFollower(prev, GLB_IDS[i]); }
const qp0 = new URLSearchParams(location.search);
let savedPlan = null;
try { if (qp0.get('nosave') == null) { const r = readSave(localStorage); if (r.status === 'ok') savedPlan = planFromState(r.state, GLB_NAMES, 60); } } catch (e) { diag('save read failed: ' + (e && e.message || e)); }
const savedOn = qp0.get('nosave') == null;
if (!savedPlan) savedPlan = { party: [1, 2, 0], hero: 1, followers: [2, 0], pos: null };
/* test build 1.1.9: the Owner is the default playable character (first launch of this build; the dropdown still lists everyone and later picks are kept). Not applied in nosave test runs. */
const IS_OWNER_TOKEN = (() => { try { return !!localStorage.getItem('vn_owner_unlock_v1'); } catch (e) { return false; } })();   /* cheap local check; the real gate (ownergate.js) still decides cheats */
{ const oi = GLB_IDS.indexOf('n:owner'); let seen = null; try { seen = localStorage.getItem('p3d_owner_default_v119'); } catch (e) {}
  if (savedOn && qp0.get('hero') == null && oi > 0 && IS_OWNER_TOKEN && !seen) { savedPlan.hero = oi; savedPlan.pos = null; try { localStorage.setItem('p3d_owner_default_v119', '1'); } catch (e) {} }
  if (!IS_OWNER_TOKEN && savedPlan.hero === oi) savedPlan.hero = 1;   /* the Owner skin is for the owner account only */ }
{ const u = a => [...new Set(a)]; savedPlan.party = u([1, 2, ...savedPlan.party]); if (savedPlan.hero == null) savedPlan.hero = 1; savedPlan.followers = u([1, 2, ...(savedPlan.followers || [])]).filter(i => i !== savedPlan.hero).slice(0, 3); }  // Darius + Selene are always the visible/selectable heroes
if (savedPlan) diag('3D: loaded saved party (' + savedPlan.party.map(i => GLB_NAMES[i]).join(', ') + ')');
// ---------- character selector: ONE entry per character (all variants grouped), compact dropdown + variant switches ----------
const gkey = id => id.replace(/^[a-z]:/, '').replace(/_straight_rig(?:_50)?$/, '').replace(/_smooth$/, '').replace(/_new\d*$/, '').replace(/^owner_pika\d*$/, 'owner').replace(/^player_/, '');
const GROUPS = new Map(), SLOT_G = [], VRANK = { Blocky: 0, Old: 1, New: 2, 'New (straight)': 3, Placeholder: 4 };
GLB_IDS.forEach((id, i) => { const k = gkey(id); let g = GROUPS.get(k); if (!g) GROUPS.set(k, g = { key: k, name: '', nameRank: 9, vars: [], slots: [] }); g.slots.push(i); SLOT_G[i] = g;
  const px = id[1] === ':' ? id[0] : '', rank = px === '' ? 0 : px === 'o' ? 1 : px === 'n' ? 2 : 3;
  if (rank < g.nameRank) { g.nameRank = rank; g.name = HERO_NAMES[i].replace(/\s*(\(NEW\)|\(SMOOTH\)|\[PLACEHOLDER\]|\(OLD\))\s*$/i, '').replace(/ Straight Rig$/, ''); }
  if (px === 'n') g.vars.push({ slot: i, mode: 'glb', label: id === 'n:vaelthryx_straight_rig_50' ? '50×' : id === 'n:vaelthryx_straight_rig' ? '10×' : /_smooth$/.test(id) ? 'Smooth' : /pika/.test(id) ? 'Pikachu' : /straight/.test(id) ? 'New (straight)' : 'New' });
  else if (px === 'p') g.vars.push({ slot: i, mode: 'glb', label: 'Placeholder' });
  else { if (bk(id)) g.vars.push({ slot: i, mode: 'blocky', label: 'Blocky' }); g.vars.push({ slot: i, mode: 'glb', label: 'Old' }); } });
GROUPS.forEach(g => { const nv = g.vars.filter(v => v.label === 'New'); if (nv.length > 1) nv.forEach(v => { v.label = ('New ' + ((GLB_IDS[v.slot].match(/_new(\d+)/) || [0, ''])[1])).trim(); }); });
// Hide rejected versions only in the visible model chooser. Leave GLB_IDS, binary files,
// saved slots, and all model-loading fallback logic unchanged.
const APPROVED_DISPLAY=new Map([
 ['aldric',v=>v.label==='Old'||v.label==='Blocky'],
 ['darius',v=>v.label==='Blocky'],
 ['elira',v=>v.label==='Blocky'],
 ['asha',v=>v.label==='Old'||GLB_IDS[v.slot]==='n:asha_new3'],
 ['garruk',v=>v.label==='Old'||GLB_IDS[v.slot]==='n:garruk_new5'],
 ['owner',v=>GLB_IDS[v.slot]==='n:owner']
]);
for(const [key,accept] of APPROVED_DISPLAY){
 const group=GROUPS.get(key);if(!group)continue;
 const approved=group.vars.filter(accept);
 if(approved.length)group.vars=approved;
}

const vrank = l => l === 'Smooth' ? 3.5 : l === 'Pikachu' ? 3 : l === 'Blocky' ? 0 : l === 'Old' ? 1 : l === 'Placeholder' ? 9 : 2 + (parseInt(l.replace(/\D/g, '')) || 0) / 100 + (/straight/.test(l) ? .5 : 0);
GROUPS.forEach(g => g.vars.sort((a, b) => vrank(a.label) - vrank(b.label)));
// Sort the display rows only: never reorder GLB_IDS/HEROES because saves use their indices.
// Titles remain visible but are ignored for alphabetical placement (e.g. Sir Aldric is under A).
const rosterName = g => g.name.replace(/^(?:Sir|Lady|Dame|Brother|Captain|Queen|Elder)\s+/i, '').trim();
const compareRoster = (a, b) => rosterName(a).localeCompare(rosterName(b), 'en', { numeric: true, sensitivity: 'base' }) || a.name.localeCompare(b.name, 'en');
// Owner-approved 3D boss variants, displayed in their OWN roster tab.
 // Model IDs / saved slot indices stay unchanged so existing saves still work.
const APPROVED_BOSS_IDS = new Set([
  'n:vaelthryx_straight_rig', // Balthrix 10×
  'n:ashentitan_20',          // Ashen Titan 15×, stable legacy ID
  'n:frosttroll_a',           // 3.5×
  'n:frosttroll_b'            // 3.5×
]);
const bossVariant = g => g.vars.find(v => APPROVED_BOSS_IDS.has(GLB_IDS[v.slot]));
const BOSS_DISPLAY = new Map([
  ['n:vaelthryx_straight_rig','Balthrix (10×)'],
  ['n:ashentitan_20','Ashen Titan (15×)'],
  ['n:frosttroll_a','Frost Troll A (3.5×)'],
  ['n:frosttroll_b','Frost Troll B (3.5×)']
]);
const selV = {};   // group key -> chosen variant
function curVar(g) {
  if (selV[g.key]) return selV[g.key];
  let v = null; try { const r = localStorage.getItem('vn_var_' + g.key); if (r) v = g.vars.find(x => x.slot + '|' + x.mode === r); } catch (_) {}
  if (!v) { v = g.vars[0]; if (v.mode === 'blocky' && modeFor(GLB_IDS[v.slot]) === 'glb') v = g.vars.find(x => x.slot === v.slot && x.mode === 'glb') || v; }
  return selV[g.key] = v;
}
const fbtn = i => document.querySelector('#heroes button.fol[data-g="' + SLOT_G[i].key + '"]');
let selUI = null;
function refreshSel(i) {
  if (!selUI) return; const g = SLOT_G[i];
  if (i !== undefined) { const v = g.vars.find(x => x.slot === i && x.mode === modeFor(GLB_IDS[i])) || g.vars.find(x => x.slot === i); if (v) { selV[g.key] = v; try { localStorage.setItem('vn_var_' + g.key, v.slot + '|' + v.mode); } catch (_) {} } }
  const cur = curVar(g); selUI.cur.firstChild.textContent = g.name + ' '; 
  const visibleVariants=bossVariant(g)?g.vars.filter(v=>APPROVED_BOSS_IDS.has(GLB_IDS[v.slot])):g.vars;
  selUI.vars.textContent = ''; selUI.vars.style.display = visibleVariants.length > 1 ? 'flex' : 'none';
  visibleVariants.forEach(v => { const c = document.createElement('button'); c.className = 'vr' + (v === cur ? ' on' : ''); c.textContent = v.label; c.dataset.i = v.slot; c.dataset.m = v.mode; c.title = g.name + ': ' + v.label + ' version';
    c.addEventListener('pointerdown', e => e.stopPropagation()); c.addEventListener('click', e => { e.stopPropagation(); selectVariant(g, v); }); selUI.vars.appendChild(c); });
  selUI.rows.forEach(r => { const gg = r.g, v = r.approved ? bossVariant(gg) : curVar(gg); if(v)r.b.dataset.i = v.slot; r.b.classList.toggle('on', gg === g); });
}
async function selectVariant(g, v) {
  selV[g.key] = v; try { localStorage.setItem('vn_var_' + g.key, v.slot + '|' + v.mode); } catch (_) {}
  const id = GLB_IDS[v.slot]; if (bk(id) && modeFor(id) !== v.mode) await toggleModel(v.slot);
  await selectHero(v.slot); refreshSel(v.slot);
}
{ const bar = document.getElementById('heroes'); const seen = new Set(), gl = [];
  const OG = SLOT_G[GLB_IDS.indexOf('n:owner')];
  if (OG && !IS_OWNER_TOKEN) seen.add(OG);   /* hidden from everyone but the owner */
  HERO_NAMES.forEach((_, i) => { const g = SLOT_G[i]; if (g && !seen.has(g)) { seen.add(g); gl.push(g); } });
  gl.sort(compareRoster);
  const approvedGroups=gl.filter(g=>!!bossVariant(g));
  const standardGroups=gl.filter(g=>!bossVariant(g));
  const cur = document.createElement('button'); cur.id = 'hcur'; cur.className = 'cur'; cur.appendChild(document.createTextNode('')); const car = document.createElement('span'); car.textContent = '\u25be'; cur.appendChild(car); cur.title = 'choose character';
  const vars = document.createElement('div'); vars.id = 'hvars'; const list = document.createElement('div'); list.id = 'hlist';
  const tabs=document.createElement('div'); tabs.className='vn-roster-tabs';
  const rosterTab=document.createElement('button');rosterTab.type='button';rosterTab.textContent='Characters';
  const bossTab=document.createElement('button');bossTab.type='button';bossTab.textContent='New Boss Approved Models';
  tabs.append(rosterTab,bossTab);
  const normalList=document.createElement('div');normalList.className='vn-roster-list';
  const bossList=document.createElement('div');bossList.className='vn-roster-list';
  const showRosterTab=which=>{
    normalList.hidden=which!=='regular';bossList.hidden=which!=='boss';
    rosterTab.classList.toggle('on',which==='regular');bossTab.classList.toggle('on',which==='boss');
  };
  rosterTab.addEventListener('click',e=>{e.stopPropagation();showRosterTab('regular')});
  bossTab.addEventListener('click',e=>{e.stopPropagation();showRosterTab('boss')});
  const rows = [];
  const close = () => bar.classList.remove('open');
  cur.addEventListener('pointerdown', e => e.stopPropagation()); cur.addEventListener('click', e => { e.stopPropagation(); bar.classList.toggle('open'); });
  document.addEventListener('pointerdown', e => { if (!bar.contains(e.target)) close(); }, true);
  const mkRow = (g, approved=false) => { const item=approved?bossVariant(g):curVar(g); const n = approved?(BOSS_DISPLAY.get(GLB_IDS[item.slot])||g.name):g.name, row = document.createElement('div'); row.className = 'row'; const b = document.createElement('button'); b.className = g.slots.every(s => /^p:/.test(GLB_IDS[s])) ? 'ph' : ''; b.title = n; b.textContent = n; b.dataset.i = item.slot;
    if (!approved && g.vars.length > 1) { const sp = document.createElement('small'); sp.textContent = ' \u00b7' + g.vars.length; b.appendChild(sp); }
    b.addEventListener('pointerdown', e => e.stopPropagation()); b.addEventListener('click', e => { e.stopPropagation(); close(); selectVariant(g, approved?bossVariant(g):curVar(g)); });
    const f = document.createElement('button'); f.textContent = '+'; f.className = 'fol'; f.title = 'add/remove ' + n + ' as party follower'; f.dataset.f = item.slot; f.dataset.g = g.key; f.addEventListener('pointerdown', e => e.stopPropagation()); f.addEventListener('click', e => { e.stopPropagation(); f.dataset.f = approved?bossVariant(g).slot:curVar(g).slot; toggleFollower(+f.dataset.f); });
    row.appendChild(b); row.appendChild(f); return { row, b }; };
  const back= document.createElement('button');back.type='button';back.className='vn-picker-close';back.textContent='← Back to game';back.addEventListener('pointerdown',e=>e.stopPropagation());back.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();close();});list.appendChild(back);
  list.appendChild(tabs);
  list.appendChild(normalList);list.appendChild(bossList);
  showRosterTab('regular');
  standardGroups.forEach(g=>{const r=mkRow(g);normalList.appendChild(r.row);rows.push({g,b:r.b,approved:false});});
  approvedGroups.forEach(g=>{const r=mkRow(g,true);bossList.appendChild(r.row);rows.push({g,b:r.b,approved:true});});
  window.__openBossRoster=()=>{showRosterTab('boss');bar.classList.add('open')};
  window.__ownerRoster = () => {
    if (!OG || rows.some(r => r.g === OG)) return;
    const r = mkRow(OG);
    const before=rows.filter(x=>!x.approved).find(x=>compareRoster(OG,x.g)<0);
    if(before)normalList.insertBefore(r.row,before.b.parentElement);
    else normalList.appendChild(r.row);
    rows.push({g:OG,b:r.b,approved:false});
  };
  bar.appendChild(cur); bar.appendChild(vars); bar.appendChild(list); selUI = { cur, vars, rows }; refreshSel((() => { const q = qp0.get('hero'); return q != null && HEROES[+q] ? +q : savedPlan ? savedPlan.hero : 0; })()); }
async function toggleModel(i) {
  const id = GLB_IDS[i], next = modeFor(id) === 'blocky' ? 'glb' : 'blocky'; try { localStorage.setItem('vn_model_' + id, next); } catch (_) {}
  if (HEROES.indexOf(hero) === i) { await loadHero(i); }
  for (const r of crowd) if (r.a.id === id) { if (r.root) { scene.remove(r.root); r.root = null; r.nd = null; } loadActorModel(id).then(w => { if (!w || r.root) return; w.traverse(o => { if (o.isMesh) o.castShadow = false; }); const bl = new THREE.Mesh(BLOB_GEO, BLOB_MAT); bl.rotation.x = -Math.PI / 2; bl.position.y = 0.03; w.add(bl); r.root = w; r.nd = findNodes(w); w.rotation.order = 'YXZ'; w.position.set(r.a.x, 0, r.a.z); w.rotation.y = r.a.yaw; scene.add(w); }); }
}
function toggleFollower(i) {
  const id = GLB_IDS[i], cur = crowd.find(c => c.kind === 'party' && SLOT_G[GLB_IDS.indexOf(c.a.id)] === SLOT_G[i]), btn = fbtn(i);
  if (cur) { crowd.splice(crowd.indexOf(cur), 1); bumpSys.remove(cur.a); if (cur.root) scene.remove(cur.root); if (btn) btn.classList.remove('on'); return; }
  if (SLOT_G[HEROES.indexOf(hero)] === SLOT_G[i]) return;
  const pm = crowd.filter(c => c.kind === 'party'); if (pm.length >= 3) { const o = pm[0], oi = GLB_IDS.indexOf(o.a.id); crowd.splice(crowd.indexOf(o), 1); bumpSys.remove(o.a); if (o.root) scene.remove(o.root); const ob = fbtn(oi); if (ob) ob.classList.remove('on'); }
  spawnCrowd(id, 'party', state.heroX + (Math.random() - 0.5) * 2 * HS, state.heroZ + 2.2 * HS, (2.6 + pm.length * 0.5) * HS, 0); if (btn) btn.classList.add('on');
}
{ const q = qp0.get('hero'); const qi = q != null && HEROES[+q] ? +q : savedPlan ? savedPlan.hero : 0; startHero = qi; if (qi) HEROES[0].visible = false; loadHero(qi).then(() => { if (qi && HEROES[qi].children.length) setHero(qi); else HEROES[0].visible = true; }); }
// preload the first three quietly after first paint (they replace the procedural stand-ins)

// blob shadow is the real shadow map; no extra.
const marker = new THREE.Mesh(new THREE.RingGeometry(0.35, 0.55, 20), new THREE.MeshBasicMaterial({ color: 0xffe08a, transparent: true, opacity: 0.9, depthWrite: false }));
marker.rotation.x = -Math.PI / 2; marker.position.y = 0.06; marker.visible = false; scene.add(marker);

// ---------- input ----------
const state = { swimming:false, level: 0, heroY: 0, inside: null, zoom: 1, heroX: 0, heroZ: START_Z, moving: false, speed: 0, target: null, yaw: 0, camYaw: 0, blockedFrames: 0, collisions: 0, vx: 0, vz: 0 };
const posOk = (x, z) => { const r = 0.5 * HS + 0.3; for (const c of colliders) { if (c.type === 'box' ? (x > c.minX - r && x < c.maxX + r && z > c.minZ - r && z < c.maxZ + r) : Math.hypot(x - c.x, z - c.z) < c.r + r) return false; } return Math.abs(x) < WORLD - 3 && Math.abs(z) < WORLD - 3; };   // a save from the smaller village may sit inside a (now bigger) building
if (savedPlan && savedPlan.pos && qp0.get('hero') == null && posOk(savedPlan.pos.x, savedPlan.pos.z)) { state.heroX = savedPlan.pos.x; state.heroZ = savedPlan.pos.z; state.yaw = savedPlan.pos.yaw; }
const keys = new Set();
import('./ladders.js').then(m => { LAD = m.createLadders({ THREE, scene, colliders, state, keys, HS }); for (const d of LADDER_SITES) LAD.add(d); });
const LADDER_SITES = [{ id: 'watchtower', x: -18, z: 32, half: 1.8, H: 5.0 }, { id: 'lookout', x: -30, z: 14, half: 1.5, H: 3.2, roofed: false }, { id: 'belltower', x: -24, z: -16, half: 2.0, H: 7.0 }];
/* owner cheat flags (cheatflags.js): all defaults are no-ops; only the owner-gated panel ever changes them */
const cheat = createFlags();
// Separate from owner cheats. Cinder can take off without enabling cheat flight for other heroes.
const cinderFlight = createCinderFlight();
const isCinder = () => ['n:cinder_new', 'o:cinder'].includes(GLB_IDS[HEROES.indexOf(hero)]);
const flyControls = document.getElementById('cinderFlyControls');
const flyBtn = document.getElementById('cinderFlyBtn');
const flyUp = document.getElementById('cinderFlyUp'), flyDown = document.getElementById('cinderFlyDown');
const flyTouch = { up: false, down: false };
let wasCinder = false;
function syncCinderControls() {
  const selected = isCinder();
  if (wasCinder && !selected) { cinderFlight.reset(); flyTouch.up = flyTouch.down = false; }
  wasCinder = selected;
  if (flyControls) flyControls.style.display = selected ? 'flex' : 'none';
  if (flyBtn) flyBtn.textContent = cinderFlight.active ? 'Land' : 'Take off';
  if (flyUp) flyUp.style.display = cinderFlight.alt > 0 || cinderFlight.active ? '' : 'none';
  if (flyDown) flyDown.style.display = cinderFlight.alt > 0 || cinderFlight.active ? '' : 'none';
}
if (flyBtn) flyBtn.addEventListener('click', e => { e.stopPropagation(); if (isCinder()) cinderFlight.toggle(); syncCinderControls(); });
for (const [button, key] of [[flyUp, 'up'], [flyDown, 'down']]) if (button) {
  const stop = e => { if (e) e.preventDefault(); flyTouch[key] = false; };
  button.addEventListener('pointerdown', e => { e.preventDefault(); e.stopPropagation(); flyTouch[key] = true; try { button.setPointerCapture(e.pointerId); } catch (_) {} });
  button.addEventListener('pointerup', stop); button.addEventListener('pointercancel', stop); button.addEventListener('lostpointercapture', stop);
}
addEventListener('keydown', e => { if (e.repeat || !isCinder() || /input|textarea/i.test(e.target?.tagName || '')) return; if (e.key.toLowerCase() === 'f') { cinderFlight.toggle(); syncCinderControls(); } });

addEventListener('keydown', e => keys.add(e.key.toLowerCase()));
addEventListener('keyup', e => keys.delete(e.key.toLowerCase()));

const stick = document.getElementById('stick'), knob = document.getElementById('knob');
const joy = { id: null, x: 0, y: 0 };
const STICK_R = 39;
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
  // Raycast against the actual sculpted ground; the old y=0 plane failed on
  // volcano slopes, causing taps to send companions into raised terrain.
  const landHit=ZONE.name==='town'&&TOWN_LANDS?.terrain?ray.intersectObject(TOWN_LANDS.terrain,false)[0]:null;
  const found=landHit?(hit.copy(landHit.point),true):!!ray.ray.intersectPlane(plane,hit);
  if(found){
    const lim=ZONE.half-1.5;
    state.target={x:THREE.MathUtils.clamp(hit.x,ZONE.cx-lim,ZONE.cx+lim),z:THREE.MathUtils.clamp(hit.z,ZONE.cz-lim,ZONE.cz+lim)};
    const surface=surfaceAt(state.target.x,state.target.z,0);
    marker.position.set(state.target.x,(surface?.y||0)+.07,state.target.z);marker.visible=true;
  }
}
let prefStore = null; try { prefStore = localStorage; } catch (e) { prefStore = null; }
const camRig = createCamRig({ camera, canvas, colliders, HS, WORLD, prefs: loadPrefs(prefStore || { getItem() { return null; } }) });
camRig.setProfile(CH);
canvas.addEventListener('pointerdown', e => { try { canvas.setPointerCapture(e.pointerId); } catch (_) {} touches.set(e.pointerId, { sx: e.clientX, sy: e.clientY, lx: e.clientX, ly: e.clientY, drag: false }); });
canvas.addEventListener('pointermove', e => {
  const t = touches.get(e.pointerId); if (!t) return;
  if (!t.drag && Math.hypot(e.clientX - t.sx, e.clientY - t.sy) > 12) t.drag = true;
  if (t.drag && !camRig.pinching) { lastDragT = performance.now(); state.camYaw -= (e.clientX - t.lx) * 0.006 * camRig.prefs.lookSens; if (camRig.fp) camRig.look(0, -(e.clientY - t.ly) * 0.005 * camRig.prefs.lookSens); }
  t.lx = e.clientX; t.ly = e.clientY;
});
const canvasUp = e => { const t = touches.get(e.pointerId); touches.delete(e.pointerId); if (t && !t.drag && e.type === 'pointerup') tapMoveTo(e.clientX, e.clientY); };
canvas.addEventListener('pointerup', canvasUp); canvas.addEventListener('pointercancel', canvasUp);
addEventListener('contextmenu', e => e.preventDefault());

// ---------- movement + collision ----------
const SPEED = 5.2 * HS;
let travelRun=false;
const WALK_SPEED=.62, RUN_SPEED=1.24;
const travelScale=()=>travelRun?RUN_SPEED:WALK_SPEED;
// Full stamina covers roughly 290 world units of sustained running on normal ground
// (~30 seconds). Combat and world travel use the same SP pool when combat is active.
const STAMINA_MAX=100, STAMINA_PER_UNIT=.34, WALK_RECOVERY=8, IDLE_RECOVERY=13;
let worldStamina=STAMINA_MAX, previousCombatSp=null, exhausted=false;
function staminaResource(){const f=window.__p3d?.fight;return f?.on?f.cc.res:null;}
function staminaLevel(){const r=staminaResource();return r?r.sp/r.max.sp:worldStamina/STAMINA_MAX;}
function updateStamina(dt,ranDistance){
 const resource=staminaResource();
 if(resource&&!previousCombatSp){resource.sp=Math.min(resource.max.sp,worldStamina/STAMINA_MAX*resource.max.sp);}
 else if(!resource&&previousCombatSp){worldStamina=Math.min(STAMINA_MAX,previousCombatSp.sp/previousCombatSp.max.sp*STAMINA_MAX);}
 previousCombatSp=resource;
 if(resource?.unlimited){worldStamina=STAMINA_MAX;exhausted=false;}
 else if(travelRun&&ranDistance>0.01){
   const use=ranDistance*STAMINA_PER_UNIT;
   if(resource){resource.sp=Math.max(0,resource.sp-use/STAMINA_MAX*resource.max.sp);resource.spLock=Math.max(resource.spLock,.3);}
   else worldStamina=Math.max(0,worldStamina-use);
 } else if(!resource){
   worldStamina=Math.min(STAMINA_MAX,worldStamina+(ranDistance>.01?WALK_RECOVERY:IDLE_RECOVERY)*dt);
 }
 const pct=staminaLevel();
 if(travelRun&&pct<=.005){exhausted=true;setTravelRun(false);}
 if(exhausted&&pct>=.30)exhausted=false;
 const meter=document.getElementById('staminaMeter'),txt=document.getElementById('staminaValue');
 if(meter)meter.style.width=(100*pct).toFixed(1)+'%';
 if(txt)txt.textContent=Math.round(pct*100)+'%'+(exhausted?' · Recovering':'');
 const bar=document.getElementById('staminaHud');if(bar)bar.classList.toggle('exhausted',exhausted);
}
function setTravelRun(v){
 travelRun=!!v&&(!exhausted&&staminaLevel()>=.12||!!staminaResource()?.unlimited);
 const b=document.getElementById('runBtn');
 if(b){b.textContent=travelRun?'RUN':exhausted?'REST':'WALK';b.setAttribute('aria-pressed',String(travelRun));b.title=travelRun?'Running – tap to walk':exhausted?'Stamina depleted – recovering':'Walking – tap to run';}
}
document.getElementById('runBtn')?.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();setTravelRun(!travelRun);});
addEventListener('keydown',e=>{if(e.repeat||/INPUT|TEXTAREA|SELECT/.test(e.target?.tagName||''))return;if(e.key.toLowerCase()==='capslock'||e.key.toLowerCase()==='r'&&!window.__p3d?.fight?.on){setTravelRun(!travelRun);}});
let jumpVelocity=0,jumpHeight=0;
function jump(){if(jumpHeight>0||jumpVelocity>0||state.swimming||state.climbing||cheat.fly||isCinder()&&cinderFlight.active)return false;jumpVelocity=7.5*HS;return true;}
document.getElementById('jumpBtn')?.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();jump();});
addEventListener('keydown',e=>{if(e.repeat||/INPUT|TEXTAREA|SELECT/.test(e.target?.tagName||''))return;if(e.code==='Space'&&!cheat.fly&&!isCinder()&&!window.__p3d?.fight?.on){e.preventDefault();jump();}});
setTravelRun(false);
// buildings only playable characters may enter (companions, townsfolk and monsters are kept out by npcOnly door colliders)
const HERO_ONLY = new Set(['guildhall']), HO_WAIT = { id: null, x: 0, z: 0 };
function heroOnlyWait() { const id = state.inside; if (!id || !HERO_ONLY.has(id)) return null; if (HO_WAIT.id !== id) { const e = enterables.find(q => q.id === id); const b = e && (e.parts ? e.parts[0] : e); if (!b || !b.toW) return null; const [x, z] = b.toW(0, b.d / 2 + 3.2); HO_WAIT.id = id; HO_WAIT.x = x; HO_WAIT.z = z; } return HO_WAIT; }
window.__heroOnly = HERO_ONLY;
function resolve(p, ghost, who) {
  let hitAny = false;
  const LV = state.level;
  for (const c of colliders) {
    if (ghost) break;
    if (c.npcOnly && who !== 'npc') continue;   // door blockers for hero-only buildings (guild hall): only companions / townsfolk collide
    if (c.lv !== undefined && (Array.isArray(c.lv) ? !c.lv.includes(LV) : c.lv !== LV)) continue;
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
  const lim = ZONE.half - 1.3; p.x = THREE.MathUtils.clamp(p.x, ZONE.cx - lim, ZONE.cx + lim);
  p.z = THREE.MathUtils.clamp(p.z, ZONE.cz - lim, ZONE.cz + ZONE.half + (ZONE.name === 'town' ? 8 : -1.3)); // town: can walk out the gate a bit
  return hitAny;
}

const tmp = { x: 0, z: 0 };
// multi-level floors (buildings.js): the hero has a level + y; upper floors only walkable where a floor/stair exists
function surfaceAt(x, z, level) {
  for (const b of ectx.multi) { { const rc = (b.reach || 40) * (b.K || 1); if (Math.abs(x - b.cx) > rc || Math.abs(z - b.cz) > rc) continue; } const s = b.surface(x, z, level); if (s) return s; }
  if (LAD && level >= 10) { const ls = LAD.surface(x, z, level); if (ls) return ls; }
  return level === 0 ? { y: ZONE.name === 'frost' ? frostElevation(x,z) : ZONE.name === 'town' && TOWN_LANDS ? TOWN_LANDS.heightAt(x,z) : 0 } : null;
}
function updateLevel() {
  if (state.climbing) return;
  let s = surfaceAt(state.heroX, state.heroZ, state.level);
  if (!s && cheat.noclip) { state.level = 0; s = surfaceAt(state.heroX, state.heroZ, 0); }
  if (s && s.ramp) { const m = s.ramp; if (state.level === m.l0 && s.t > (m.flipUp || 0.93)) state.level = m.l1; else if (state.level === m.l1 && s.t < 0.25) state.level = m.l0; s = surfaceAt(state.heroX, state.heroZ, state.level) || s; }
  state.heroY = s ? s.y : 0;
}
// ---------- bump / stumble (bump.js): no blocking collisions between characters; walls still stop everyone ----------
const qp = new URLSearchParams(location.search);
const BUMP_ON = qp.get('nobump') == null;
const PARTY_N = BUMP_ON ? Math.max(0, Math.min(3, qp.get('party') != null ? +qp.get('party') || 0 : 2)) : 0;
const NPC_N = BUMP_ON ? (qp.get('npcs') != null ? Math.max(0, Math.min(2, +qp.get('npcs') || 0)) : 1) : 0;
const bumpSys = createBump({ contactR: 0.45 * HS, runSpeed: 0.92 * SPEED });   // only a full-speed head-on charge can bump
const playerAct = makeActor('aldric', { fixed: true, group: 'party' }); bumpSys.add(playerAct);
const crowd = []; // followers + NPCs: { a, root, kind, leash, home }
const tmp2 = { x: 0, z: 0 };
/* crowd members skip the shadow-map pass (halves their draw calls); one shared blob decal each instead */
const BLOB_GEO = new THREE.CircleGeometry(0.55 * HS, 14), BLOB_MAT = new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.28, depthWrite: false });
const HERO_GLB_ID = i => GLB_IDS[i] || 'aldric';
async function loadActorModel(id) {
  if (modeFor(id) === 'blocky') { try { return makeBlocky(id); } catch (e) { console.warn('blocky follower failed', id, e); } }
  try { const buf = await fetchGLB(id); return await new Promise(res => gl.parse(buf, '', g => { try { res(wrapGLB(g, id)); } catch (e) { res(null); } }, () => res(null))); }
  catch (e) { return null; }
}
function spawnCrowd(id, kind, x, z, leash, yaw) {
  const a = makeActor(id, { str: undefined, group: kind === 'party' ? 'party' : null }); a.x = x; a.z = z; a.yaw = yaw || 0;
  const rec = { id, a, root: null, nd: null, kind, leash, hx: x, hz: z, vxs: 0, vzs: 0, level: state.level, y: state.heroY || 0, ti: null, lvT: 0 };
  crowd.push(rec); bumpSys.add(a);
  loadActorModel(id).then(w => { if (!w) return; w.traverse(o => { if (o.isMesh) o.castShadow = false; }); const bl = new THREE.Mesh(BLOB_GEO, BLOB_MAT); bl.rotation.x = -Math.PI / 2; bl.position.y = 0.03; w.add(bl); rec.root = w; rec.nd = findNodes(w); w.rotation.order = 'YXZ'; w.position.set(a.x, 0, a.z); w.rotation.y = a.yaw; scene.add(w); });
  return rec;
}
{
  const startId = qp.get('hero') != null ? +qp.get('hero') || 0 : savedPlan ? savedPlan.hero : 0;
  const used = new Set([HERO_GLB_ID(startId)]);
  const fromSave = savedPlan && qp.get('hero') == null;
  const pick = fromSave ? savedPlan.followers.map(HERO_GLB_ID).filter(x => !used.has(x)) : ['elira', 'orin', 'seraphine', 'finn', 'brynn'].filter(x => !used.has(x));
  const nFol = !BUMP_ON ? 0 : fromSave && qp.get('party') == null ? Math.min(3, pick.length) : Math.min(PARTY_N, pick.length);
  const bx = state.heroX, bz = state.heroZ + 2.8 * HS;
  for (let i = 0; i < nFol; i++) spawnCrowd(pick[i], 'party', bx + (i - (nFol - 1) / 2) * 1.6 * HS, bz + i * 0.3 * HS, (2.6 + i * 0.5) * HS, 0);
  for (let i = 0; i < NPC_N; i++) spawnCrowd(['thorne', 'rook'][i], 'npc', (4.5 + i * 2.5) * HS, START_Z + (1.5 - i * 1.5) * HS, 0, Math.PI * 0.75);
}
function swapFollower(prevId, newId) {
  const r = crowd.find(c => c.kind === 'party' && c.a.id === newId); if (!r || !prevId || prevId === newId) return;
  r.a.id = prevId; r.a.style = styleFor(prevId); r.a.str = r.a.style.str;
  if (r.root) { scene.remove(r.root); r.root = null; r.nd = null; }
  loadActorModel(prevId).then(w => { if (!w || r.a.id !== prevId) return; w.traverse(o => { if (o.isMesh) o.castShadow = false; }); const bl = new THREE.Mesh(BLOB_GEO, BLOB_MAT); bl.rotation.x = -Math.PI / 2; bl.position.y = 0.03; w.add(bl); r.root = w; r.nd = findNodes(w); w.rotation.order = 'YXZ'; w.position.set(r.a.x, 0, r.a.z); w.rotation.y = r.a.yaw; scene.add(w); });
}
/* Followers on stairs: the hero leaves a breadcrumb trail (x, z, level). A follower on another floor walks that trail (which runs up/down the flight),
   adopting each point's level as it passes it, and once it reaches the end of the trail it is on the hero's floor. Fallback: teleport to the hero after 12 s. */
const TRAIL = []; let trailBase = 0;
function recordTrail() {
  const n = TRAIL.length, l = n ? TRAIL[n - 1] : null;
  if (!l || l.l !== state.level || Math.hypot(state.heroX - l.x, state.heroZ - l.z) > 0.5) { TRAIL.push({ x: state.heroX, z: state.heroZ, l: state.level }); if (TRAIL.length > 500) { TRAIL.shift(); trailBase++; } }
}
/* companions changing floor by a stair: when the trail leads onto a ramp and the companion is beside it (not on it), steer to the ramp's entry end first
   (foot going up, top going down) so it walks round the side rail instead of pressing into it. No allocation (one shared result object). */
const SE = { x: 0, z: 0 };
function stairEntry(r, a, t) {
  for (const b of ectx.multi) {
    if (!b.ramps || !b.ramps.length || !b.toL) continue; const [fx, fz] = b.toL(a.x, a.z); if (Math.abs(fx) > 40 || Math.abs(fz) > 40) continue;
    const [tx, tz] = b.toL(t.x, t.z);
    for (const m of b.ramps) {
      const up = m.l0 === r.level && state.level > r.level, dn = m.l1 === r.level && state.level < r.level; if (!up && !dn) continue;
      const [tu, tv] = b.rampUV(m, tx, tz); if (Math.abs(tu) > m.len / 2 + 1.2 || Math.abs(tv) > m.w / 2 + 0.8) continue;   // trail point is not on this ramp
      const [fu, fv] = b.rampUV(m, fx, fz); if (Math.abs(fu) <= m.len / 2 + 0.05 && Math.abs(fv) <= m.w / 2) return null;       // already on the ramp: follow the trail
      const ue = up ? -m.len / 2 - 0.6 : m.len / 2 + 0.6; if (Math.hypot(fu - ue, fv) < 0.6) return null;                     // at the entry: let the trail take over
      if (Math.abs(fu - ue) + Math.abs(fv) > 12) continue;
      const lx = m.cx + Math.sin(m.ang) * ue, lz = m.cz + Math.cos(m.ang) * ue, w = b.toW(lx, lz); SE.x = w[0]; SE.z = w[1]; r.ti = null; return SE;
    }
  }
  return null;
}
function trailTarget(r, a) {
  if (r.ti === null) {
    let best = -1, bd = 1e9; for (let i = TRAIL.length - 1; i >= 0; i--) { const p = TRAIL[i]; if (p.l !== r.level) continue; const d = Math.hypot(p.x - a.x, p.z - a.z); if (d < bd - 0.01) { bd = d; best = i; } }
    if (best < 0) return null; r.ti = best + trailBase;
  }
  if (r.ti < trailBase) r.ti = trailBase;
  for (let g = 0; g < 8; g++) {
    const i = r.ti - trailBase; if (i >= TRAIL.length) { r.level = state.level; r.ti = null; return undefined; }
    const p = TRAIL[i]; if (p.l !== r.level && (p.l >= 10 || r.level >= 10) && Math.hypot(p.x - a.x, p.z - a.z) < 1.6) r.level = p.l;   // stairs flip the level via the ramp surface (crowdSurface); only ladders adopt it from the trail
    if (Math.hypot(p.x - a.x, p.z - a.z) < 0.7) { r.ti++; continue; }
    return p;
  }
  return null;
}
function crowdSurface(r, a, dt) {
  let s = surfaceAt(a.x, a.z, r.level);
  if (s && s.ramp) { const m = s.ramp; if (r.level === m.l0 && s.t > (m.flipUp || 0.93)) r.level = m.l1; else if (r.level === m.l1 && s.t < 0.25) r.level = m.l0; s = surfaceAt(a.x, a.z, r.level) || s; }
  const ty = s ? s.y : (r.level >= 10 && LAD ? LAD.heightOf(r.level) : 0);
  // Outside buildings, ground and followers must share the exact height sampler.
  // Snap steep outdoor inclines immediately to avoid clipping under mountains.
  const outdoor=(r.level===0&&(ZONE.name==='frost'||ZONE.name==='town'&&(Math.abs(a.x)>CITY_HALF||Math.abs(a.z)>CITY_HALF)));
  const correction=outdoor?Math.max(45,Math.abs(ty-r.y)/Math.max(dt,.001)):r.level===0?22:7;
  r.y = Math.abs(ty-r.y)<.025?ty:r.y+Math.max(-correction*dt,Math.min(correction*dt,ty-r.y));
}
/* Downed state (Thunderstorm): companions/townsfolk can be killed but it never touches the hero (HP, death, respawn). Companions revive at the hero's side after a short delay, townsfolk back home. */
const REVIVE_PARTY = 4, REVIVE_NPC = 8;
function downAllies() { for (const r of crowd) { if (r.down > 0) continue; r.down = r.kind === 'party' ? REVIVE_PARTY : REVIVE_NPC; if (r.root) r.root.visible = false; r.vxs = r.vzs = 0; } }
function killCrowd(b) { const r = b && b.rec; if (!r || r.down > 0) return; r.down = r.kind === 'party' ? REVIVE_PARTY : REVIVE_NPC; if (r.root) r.root.visible = false; r.vxs = r.vzs = 0; }   // crowd 'death' = down then respawn (4 s party / 8 s NPC) so the world never empties
function bystanders() { const o = []; for (const r of crowd) if (!(r.down > 0)) o.push({ x: r.a.x, z: r.a.z, hp: 1, rec: r, kind: r.kind }); return o; }
function tickDown(r, dt) {
  r.down -= dt; if (r.down > 0) return; r.down = 0; const a = r.a;
  if (r.kind === 'party') { a.x = state.heroX + (Math.random() - 0.5) * 1.6; a.z = state.heroZ + (Math.random() - 0.5) * 1.6; r.level = state.level; r.y = state.heroY || 0; r.ti = null; r.lvT = 0; }
  else { a.x = r.hx; a.z = r.hz; r.level = 0; r.y = 0; }
  r.vxs = r.vzs = 0; if (r.root) r.root.visible = true;
}
function updateCrowd(dt) {
  recordTrail();
  const pa = playerAct;
  pa.x = state.heroX; pa.z = state.heroZ; pa.yaw = state.yaw; pa.vx = state.vx; pa.vz = state.vz;
  for (let i = 0; i < crowd.length; i++) {
    const r = crowd[i], a = r.a;
    if (r.kind === 'npc' && ZONE.name !== 'town') continue;   // townsfolk wait in town while the hero is in the Wilds
    if (r.down > 0) { tickDown(r, dt); if (r.down > 0) { r.vxs = r.vzs = 0; a.vx = a.vz = 0; continue; } }
    let tvx = 0, tvz = 0;
    if (r.kind === 'party') {
      let gx = state.heroX, gz = state.heroZ, far = false; const rw = heroOnlyWait();
      if (rw) { gx = rw.x; gz = rw.z; r.lvT = 0; }   // hero is inside a playable-characters-only building: companions wait by its door
      else if (r.level !== state.level) {
        r.lvT += dt; const t = trailTarget(r, a);
        if (t) { gx = t.x; gz = t.z; far = true; const se = stairEntry(r, a, t); if (se) { gx = se.x; gz = se.z; } }   // walk to the stair foot (or top) first, then up/down the ramp
        if ((r.lvT > 12 || t === null) && state.level === 0) { a.x = state.heroX + (Math.random() - 0.5) * 1.2; a.z = state.heroZ + (Math.random() - 0.5) * 1.2; r.level = state.level; r.y = state.heroY || 0; r.ti = null; r.lvT = 0; }
      } else {
        r.ti = null;   // same floor number but a long way off (other building / stuck behind walls): catch up after a few seconds instead of pushing straight into a wall
        if (Math.hypot(gx - a.x, gz - a.z) > 22) { r.lvT += dt; if (r.lvT > 6 && state.level === 0) { a.x = state.heroX + (Math.random() - 0.5) * 1.2; a.z = state.heroZ + (Math.random() - 0.5) * 1.2; r.level = state.level; r.y = state.heroY || 0; r.lvT = 0; } } else r.lvT = 0;
      }
      { const cg = FIGHT && FIGHT.on && FIGHT.companions && r.level === state.level ? FIGHT.companions.goal(r) : null; r.faceT = cg ? cg.face : null; if (cg) { gx = cg.x; gz = cg.z; far = true; } }   // companions engage nearby enemies (combat/companions.js); otherwise follow as before
      const dx = gx - a.x, dz = gz - a.z, d = Math.hypot(dx, dz);
      if (far && d > 0.3) { const sp = SPEED * travelScale() * Math.max(1, CH.speed) * Math.max(1, cheat.speedMul) * 1.18; tvx = dx / d * sp; tvz = dz / d * sp; }
      else if (!far && d > r.leash && d > 1e-4) { const sp = Math.min(SPEED * travelScale() * Math.max(1, CH.speed) * Math.max(1, cheat.speedMul) * 1.18, (d - r.leash) * 3 + 0.8); tvx = dx / d * sp; tvz = dz / d * sp; }
    }
    const k = Math.min(1, dt * 8); r.vxs += (tvx - r.vxs) * k; r.vzs += (tvz - r.vzs) * k;
    a.vx = r.vxs; a.vz = r.vzs;
  }
  bumpSys.update(dt);
  for (let i = 0; i < crowd.length; i++) {
    const r = crowd[i], a = r.a;
    if (r.kind === 'npc' && ZONE.name !== 'town') continue;
    if (r.down > 0) continue;
    let mx = r.vxs * a.slowMul * dt + a.dx, mz = r.vzs * a.slowMul * dt + a.dz;
    if (r.kind === 'npc' && !a.svx && !a.svz && !a.bT) { const hx = r.hx - a.x, hz = r.hz - a.z, hd = Math.hypot(hx, hz); if (hd > 0.02) { const st = Math.min(hd, 1.0 * dt); mx += hx / hd * st; mz += hz / hd * st; } }
    tmp2.x = a.x + mx; tmp2.z = a.z + mz; { const l0 = state.level; state.level = r.level; resolve(tmp2, false, 'npc'); state.level = l0; }
    const moved = Math.hypot(tmp2.x - a.x, tmp2.z - a.z); a.x = tmp2.x; a.z = tmp2.z; if (r.kind === 'party') crowdSurface(r, a, dt);
    if(r.kind==='party'&&ZONE.name==='town'&&TOWN_LANDS?.waterAt(a.x,a.z))r.y=Math.max(r.y,0.2)-.55*HS;
    const sp = Math.hypot(r.vxs, r.vzs);
    if (sp > 0.3) { let da = Math.atan2(r.vxs, r.vzs) - a.yaw; da = Math.atan2(Math.sin(da), Math.cos(da)); a.yaw += da * Math.min(1, dt * 10); }
    else if (r.faceT != null && r.faceT !== undefined) { let da = r.faceT - a.yaw; da = Math.atan2(Math.sin(da), Math.cos(da)); a.yaw += da * Math.min(1, dt * 10); }
    const w = r.root; if (!w) continue;
    w.position.set(a.x, r.kind === 'party' ? r.y : 0, a.z); const u = w.userData, ww = Math.min(1, sp / SPEED);
    restoreNodes(r.nd);
    if (u.glb) { locoAnim(u, sp); u.mixer.update(dt); if (u.sb) u.sb.update(dt); }
    applyPose(a, w, r.nd, a.yaw);
  }
}
// stair assist: touching a flight from the side or at an angle steers the hero toward its mouth (foot when on the lower floor, top end when on the upper floor)
// instead of grinding along the handrail; the mouth also gently centres the hero on the flight
const _g = { x: 0, z: 0 };
function stairGuide(vx, vz) {
  _g.x = vx; _g.z = vz; if (!vx && !vz) return _g;
  for (const b of ectx.multi) {
    const rc = (b.reach || 40) * (b.K || 1); if (Math.abs(state.heroX - b.cx) > rc || Math.abs(state.heroZ - b.cz) > rc) continue;
    for (const m of b.ramps) {
      const low = state.level === m.l0, up = state.level === m.l1; if (!low && !up) continue;
      const [lx, lz] = b.toL(state.heroX, state.heroZ), [u, v] = b.rampUV(m, lx, lz), hw = m.w / 2; if (Math.abs(v) > hw + 2.6) continue;
      const uEnd = low ? -m.len / 2 - 0.15 : m.len / 2 + 0.15, lo = low ? uEnd - 2.2 : -m.len / 2 + 0.3, hi = low ? m.len / 2 - 0.4 : uEnd + 2.2; if (u < lo || u > hi) continue;
      if (low && Math.abs(v) <= hw - 0.05 && u > -m.len / 2 + 0.2) continue;                      // already on the flight
      const sn = Math.sin(m.ang), cs = Math.cos(m.ang), dxl = vx * b.cs - vz * b.sn, dzl = vx * b.sn + vz * b.cs, du = dxl * sn + dzl * cs, dv = dxl * cs - dzl * sn;
      const toward = -Math.sign(v || 1) * dv, towardEnd = (uEnd - u) * du > 0;
      let gu = 0, gv = 0; const side = Math.abs(v) > hw - 0.1, pastEnd = low ? u < uEnd - 0.2 : u > uEnd + 0.2, near = Math.abs(u - uEnd) <= 2.0;
      if (side && toward > 0.15 && !pastEnd && (low ? du : -du) > 0.35 * (Math.hypot(du, dv) || 1)) { gu = Math.sign(uEnd - u) || -1; gv = 0; }                      // pressed against the side: slide along it to past the end of the flight
      else if (pastEnd && near && Math.abs(v) <= hw + 2.4 && (low ? du : -du) > 0.5 * (Math.hypot(du, dv) || 1)) { gu = 0; gv = -Math.sign(v || 1) * Math.min(1, Math.abs(v) * 1.2 + 0.2); if (Math.abs(v) < 0.1) continue; if (Math.abs(v) > hw - 0.05 && Math.abs(u - uEnd) < 0.9) gu = low ? -0.8 : 0.8; }   // beside the rail end: back off from the flight while sliding to the axis   // lined up with the mouth: centre on the axis
      else continue;
      const k = (gu || gv) ? Math.min(1, Math.hypot(gu, gv)) : 0; if (!k) continue;
      const nu = du * 0.45 + gu * 0.9, nv = dv * 0.45 + gv * 0.9, nl = Math.hypot(nu, nv) || 1, xl = (nu / nl) * sn + (nv / nl) * cs, zl = (nu / nl) * cs - (nv / nl) * sn;
      _g.x = xl * b.cs + zl * b.sn; _g.z = -xl * b.sn + zl * b.cs; return _g;
    }
  }
  return _g;
}
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
  if (LAD && LAD.update(dt, vx, vz)) { vx = 0; vz = 0; mag = 0; }
  if (!state.climbing) { const g = stairGuide(vx, vz); vx = g.x; vz = g.z; }
  const moving = (vx || vz);
  if (moving) {
    const ghost = passesWalls(cheat) || (isCinder() && cinderFlight.alt > 3.5), step = travelScale() * (state.swimming?0.62:1) * SPEED * CH.speed * cheat.speedMul * mag * playerAct.slowMul * (window.__fightMove ? window.__fightMove() : 1) * dt, n = Math.max(1, Math.ceil(step / 0.25)), px = state.heroX, pz = state.heroZ;
    tmp.x = state.heroX; tmp.z = state.heroZ; let blocked = false;
    for (let i = 0; i < n; i++) {
      const ox = tmp.x, oz = tmp.z; tmp.x += vx * step / n; tmp.z += vz * step / n; if (resolve(tmp, ghost)) blocked = true;
      if (!cheat.noclip && state.level > 0 && !surfaceAt(tmp.x, tmp.z, state.level)) { // edge of an upper floor: slide or stop
        if (surfaceAt(tmp.x, oz, state.level)) tmp.z = oz; else if (surfaceAt(ox, tmp.z, state.level)) tmp.x = ox; else { tmp.x = ox; tmp.z = oz; } blocked = true; }
      state.heroX = tmp.x; state.heroZ = tmp.z; updateLevel();
    }
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
  state.vx = moving ? vx * SPEED * travelScale() * CH.speed * cheat.speedMul * mag * playerAct.slowMul * (window.__fightMove ? window.__fightMove() : 1) : 0; state.vz = moving ? vz * SPEED * travelScale() * CH.speed * cheat.speedMul * mag * playerAct.slowMul * (window.__fightMove ? window.__fightMove() : 1) : 0;
  if (playerAct.dx || playerAct.dz) { tmp.x = state.heroX + playerAct.dx; tmp.z = state.heroZ + playerAct.dz; resolve(tmp, passesWalls(cheat)); state.heroX = tmp.x; state.heroZ = tmp.z; }
  state.moving = state.speed > 0.5;
  updateStamina(dt, Math.max(0,state.speed*dt));
  updateLevel();
  state.swimming=!!(ZONE.name==='town'&&TOWN_LANDS?.waterAt(state.heroX,state.heroZ)&&state.level===0);
  if(state.swimming)state.heroY=Math.max(state.heroY,.2);
  if (cheat.fly || cheat.alt > 0) stepAltitude(cheat, ((cheat.up || keys.has(' ') || keys.has('e')) ? 1 : 0) - ((cheat.down || keys.has('q') || keys.has('c') || keys.has('shift')) ? 1 : 0), dt);
  if (isCinder()) cinderFlight.step(dt, flyTouch.up || keys.has(' ') || keys.has('e'), flyTouch.down || keys.has('q') || keys.has('c'));
  else if (cinderFlight.active || cinderFlight.alt) cinderFlight.reset();
  syncCinderControls();
  if(jumpVelocity>0||jumpHeight>0){jumpHeight=Math.max(0,jumpHeight+jumpVelocity*dt);jumpVelocity-=20*HS*dt;if(jumpHeight===0)jumpVelocity=0;}
  state.dispY = state.dispY === undefined || Math.abs(state.heroY - state.dispY) > 3 ? state.heroY : state.dispY + (state.heroY - state.dispY) * Math.min(1, dt * 16);
  hero.position.set(state.heroX, state.dispY + jumpHeight + cheat.alt + cinderFlight.alt - (state.swimming?0.75*HS:0), state.heroZ); hero.rotation.y = state.yaw;
  let ins = null; for (const e of enterables) { const r = e.update(state.heroX, state.heroZ, dt, state.level); if (r) ins = typeof r === 'string' ? r : e.id; }
  if (ins !== state.inside) { state.inside = ins; const eq = enterables.find(e => e.id === ins), quest = eq && (eq.quest || (eq.parts && (eq.parts.find(p => p.quest) || {}).quest)) || null;
    try { dispatchEvent(new CustomEvent('p3d-enter', { detail: { id: ins, quest } })); if (ins && quest) dispatchEvent(new CustomEvent('p3d-quest', { detail: { id: ins, quest } })); } catch (_) {} }
  animateHero(dt); cullSkins(); heroGhost();
  { const bn = hero.userData.bumpNodes || (hero.userData.bumpNodes = findNodes(hero)); applyPose(playerAct, hero, bn, state.yaw); hero.position.y = state.dispY + jumpHeight + cheat.alt + cinderFlight.alt + playerAct.phop + (hero.userData.cinderHop || 0) + (state.swimming?-.75*HS+.07*Math.sin(simTime*3.5):0); }
}

const _sp = new THREE.Vector3();
function cullSkins() { // characters: skinned meshes skip frustum culling, so cull by distance + only the near ones cast shadows (shadow box is ~15 m)
  for (const sm of SKINS) { if (!sm.parent) continue; const root = sm.parent; root.getWorldPosition(_sp); const d = Math.hypot(_sp.x - state.heroX, _sp.z - state.heroZ);
    const v = d < 115 || sm === hero; if (sm.visible !== v) sm.visible = v; }
}

// x-ray: inside a building the hero is also drawn as a faint silhouette wherever banners, door leaves, rails or walls cover him
const GHOST_MAT = new THREE.MeshBasicMaterial({ color: 0xbfe0ff, transparent: true, opacity: 0.38, depthFunc: THREE.GreaterDepth, depthWrite: false });
function heroGhost() {
  const want = !!state.inside, u = hero.userData;
  if (!want && !u.ghosts) return;
  if (want) { const sk = []; hero.traverse(o => { if (o.isSkinnedMesh && !o.userData.isGhost) sk.push(o); });
    if (!u.ghosts || u.ghostN !== sk.length) { (u.ghosts || []).forEach(g => g.parent && g.parent.remove(g)); u.ghosts = sk.map(o => { const g = new THREE.SkinnedMesh(o.geometry, GHOST_MAT); g.userData.isGhost = true; g.frustumCulled = false; g.renderOrder = 20; g.position.copy(o.position); g.quaternion.copy(o.quaternion); g.scale.copy(o.scale); o.parent.add(g); g.bind(o.skeleton, o.bindMatrix); return g; }); u.ghostN = sk.length; } }
  if (u.ghosts) for (const g of u.ghosts) g.visible = want;
}
let walkT = 0, idleT = 0, prevYaw = 0;
function animateHero(dt) {
  const u = hero.userData, w = Math.min(1, state.speed / (SPEED * CH.speed));
  if (u.glb) {
    restoreNodes(u.bumpNodes);
    if (isCinder() && u.act.flap) {
      const targets = cinderAnimationWeights(cinderFlight, LOCO_FORCE !== null ? LOCO_FORCE : state.speed, u.mscale);
      const blend = Math.min(1, dt * 5);
      u.cinderWt ||= {};
      for (const k of ['idle', 'walk', 'run', 'hover', 'flap', 'glide', 'dive', 'land']) if (u.act[k]) {
        u.cinderWt[k] = (u.cinderWt[k] ?? (k === 'idle' ? 1 : 0)) + (targets[k] - (u.cinderWt[k] ?? (k === 'idle' ? 1 : 0))) * blend;
        u.act[k].setEffectiveWeight(u.cinderWt[k]);
      }
      u.cinderStep = (u.cinderStep || 0) + dt * (6 + state.speed * 0.8);
      u.cinderHop = cinderFlight.alt < 0.05 ? Math.max(0, Math.sin(u.cinderStep)) * 0.035 * Math.min(1, state.speed / 2) : 0;
    } else { u.cinderHop = 0; locoAnim(u, LOCO_FORCE !== null ? LOCO_FORCE : state.speed); }
    u.mixer.update(dt); if (u.sb) u.sb.update(dt); if (u.cinderEmbers) u.cinderEmbers.update(dt);
    return;
  }
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
const camPos = new THREE.Vector3(0, 8 * HS, START_Z + 10 * HS), camLook = new THREE.Vector3(0, 1.5 * HS, START_Z);
const _want = new THREE.Vector3(), _look = new THREE.Vector3();
const camIn = {}; let lastDragT = 0;
function updateCamera(dt, snap) {
  const ci = camIn; ci.heroX = state.heroX; ci.heroZ = state.heroZ; ci.hy = (state.heroY || 0) + cheat.alt + cinderFlight.alt; ci.dispY = state.dispY === undefined ? state.heroY || 0 : state.dispY; ci.alt = cheat.alt + cinderFlight.alt; ci.camYaw = state.camYaw; ci.legacyZoom = state.zoom; ci.portrait = innerHeight > innerWidth; ci.dt = dt; ci.snap = snap;
  if (camRig.prefs.camMode !== 'free' && !camRig.fp && !camRig.pinching && performance.now() - lastDragT > 1500) state.camYaw = followYaw(state.camYaw, state.vx, state.vz, dt);
  ci.zx = ZONE.cx; ci.zz = ZONE.cz; ci.zh = ZONE.half;
  camRig.update(ci);
  // Follow the actual elevated terrain on hills: don't let the third-person camera clip into a ridge.
  if (((ZONE.name === 'town' && TOWN_LANDS) || ZONE.name === 'frost') && !camRig.fp) {
    const floor = (ZONE.name === 'frost' ? frostElevation(camRig.pos.x,camRig.pos.z) : TOWN_LANDS.heightAt(camRig.pos.x,camRig.pos.z)) + 1.0 * HS;
    if (camRig.pos.y < floor) { camRig.pos.y = floor; camera.position.y = floor; camera.lookAt(camRig.look); }
  }
  camPos.copy(camRig.pos); camLook.copy(camRig.look);
  camRig.syncHero(hero);
  sun.position.set(state.heroX + SUN_OFF.x * SUNK, (ZONE.name !== 'wilds' ? state.heroY : 0) + SUN_OFF.y * SUNK, state.heroZ + SUN_OFF.z * SUNK);
  sun.target.position.set(state.heroX, ZONE.name !== 'wilds' ? state.heroY : 0, state.heroZ);
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
let adaptT = 0, adaptN = 0, adaptSkip = 90, adaptLock = false;
function setQuality(q) { const plan = qualityPlan(q, window.devicePixelRatio || 1); adaptLock = !plan.adaptive; prCeil = plan.ceil; pr = plan.ceil; renderer.setPixelRatio(pr); resize(); adaptSkip = 60; adaptT = 0; adaptN = 0; }
function adaptRes(raw) {
  if (adaptLock) return;
  if (adaptSkip > 0) { adaptSkip--; return; }
  if (raw > 250) return;                       // tab switch / hitch, not load
  adaptT += raw; adaptN++;
  if (adaptT < 1000) return;
  const avg = adaptT / adaptN; adaptT = 0; adaptN = 0;
  if (avg > 22 && pr > 0.6) { prCeil = Math.max(0.6, pr * 0.98); pr = Math.max(0.6, pr * 0.82); renderer.setPixelRatio(pr); resize(); adaptSkip = 20; }
}
let lastDraw = 0;
// chimney smoke: one Points draw call for the whole village (sources registered by Builder.chimney)
const SMOKE = (() => {
  const src = ectx.smoke || [], K = 7, n = src.length * K; if (!n) return null;
  const pos = new Float32Array(n * 3), ph = new Float32Array(n), geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3)); geo.setAttribute('phase', new THREE.BufferAttribute(ph, 1)); geo.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 1e5);
  const mat = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, uniforms: { uS: { value: 400 } },
    vertexShader: 'attribute float phase; varying float vA; uniform float uS; void main(){ vec4 mv = modelViewMatrix * vec4(position,1.0); gl_Position = projectionMatrix * mv; gl_PointSize = (0.55 + phase * 1.5) * uS / -mv.z; vA = (1.0 - phase) * smoothstep(0.0, 0.12, phase) * 0.42; }',
    fragmentShader: 'varying float vA; void main(){ vec2 c = gl_PointCoord - 0.5; float r = length(c) * 2.0; if (r > 1.0) discard; gl_FragColor = vec4(vec3(0.82,0.82,0.84), vA * (1.0 - r * r)); }' });
  const pts = new THREE.Points(geo, mat); pts.frustumCulled = false; pts.renderOrder = 5; scene.add(pts);
  return { update(t) { mat.uniforms.uS.value = innerHeight * 0.9;
    for (let i = 0; i < src.length; i++) for (let k = 0; k < K; k++) { const j = i * K + k, p = (t * 0.16 + k / K + i * 0.37) % 1, wob = Math.sin(t * .7 + j) * .25;
      pos[j * 3] = src[i][0] + p * p * 2.2 + wob * p; pos[j * 3 + 1] = src[i][1] + p * 4.6; pos[j * 3 + 2] = src[i][2] + p * 0.6 + wob * .5 * p; ph[j] = p; }
    geo.attributes.position.needsUpdate = true; geo.attributes.phase.needsUpdate = true; } };
})();
/* ---------- the Wilds (1.1.9): second map at x=1000, reached by the portal in town; a portal there leads back. Monsters spawn only there (fight layer, auto mode). ---------- */
const TOWN_PORTAL = { x: -6, z: 38 };
let WM = null, FM = null, wildsP = null, townCols = null, portalT = null, frostCave = null, zoneCd = 1.5, portalDwell = 0;
const wildsMod = import('./wilds.js').then(m => { portalT = m.makeGate(0x9a6bff); portalT.position.set(TOWN_PORTAL.x, 0, TOWN_PORTAL.z); scene.add(portalT);
  for (const dx of [-1.9, 1.9]) colliders.push({ type: 'circle', x: TOWN_PORTAL.x + dx, z: TOWN_PORTAL.z, r: .75 });   /* gate pillars; the opening between them is walkable */
  frostCave=m.makeGate(0x85d9ff);
  frostCave.position.set(FROST_PORTAL.x,TOWN_LANDS?TOWN_LANDS.heightAt(FROST_PORTAL.x,FROST_PORTAL.z):FROST_SUMMIT.height,FROST_PORTAL.z);
  scene.add(frostCave);return m; });
async function ensureWilds() { if (WM) return WM; const m = await wildsMod; WM = Object.assign({ mod: m }, m.buildWilds({ scene, HS })); WM.portalMesh = m.makeGate(0x4fd0ff); WM.portalMesh.position.set(WM.portal.x, 0, WM.portal.z); WM.portalMesh.visible = false; scene.add(WM.portalMesh); return WM; }
function snapFollowers() { TRAIL.length = 0; for (const r of crowd) if (r.kind === 'party') { r.level = 0; r.y = state.heroY || 0; r.ti = null; r.lvT = 0; r.a.x = state.heroX + (Math.random() - 0.5) * 3; r.a.z = state.heroZ + 2.5 * HS; r.vxs = r.vzs = 0; } }
/* Map unloading. Leaving town hides every static town node (no draw calls / shadow casters while away; geometry stays resident because the village is built once at boot).
   Leaving the Wilds fully DISPOSES it (geometry, materials, textures, enemies via FIGHT.stop) and it is rebuilt on the next visit. */
const townHidden = [];
function hideTown() {
  const keep = new Set([...HEROES, ...crowd.map(r => r.root), WM && WM.group, WM && WM.portalMesh, marker, sun, sun.target, camera, ...(FIGHT ? [] : [])]);
  for (const n of scene.children) { if (n.visible && !keep.has(n) && !n.isLight && !n.isCamera && !(FIGHT && n.userData && n.userData.fightFx) && Math.hypot(n.position.x - 1000, n.position.z) > 400 && !(n.userData && n.userData.keepAlways)) { n.visible = false; townHidden.push(n); } }
}
function unloadWilds() {
  if (!WM) return; const g = WM.group, pm = WM.portalMesh; scene.remove(g); scene.remove(pm);
  const seen = new Set(); const dis = (o) => { if (o.geometry) o.geometry.dispose(); const ms = Array.isArray(o.material) ? o.material : o.material ? [o.material] : []; for (const m of ms) { for (const k in m) { const v = m[k]; if (v && v.isTexture && !seen.has(v)) { seen.add(v); v.dispose(); } } m.dispose(); } };
  g.traverse(dis); pm.traverse(dis); window.__unloaded = (window.__unloaded || 0) + 1; WM = null;
}
async function setZone(name) {
  if (name === ZONE.name) return true;
  const lastZone=ZONE.name;
  if(FIGHT&&FIGHT.auto)FIGHT.stop();
  if (name === 'wilds') {
    await ensureWilds(); const W = WM.mod.WILDS; townCols = colliders.slice(); colliders.length = 0; for (const c of WM.colliders) colliders.push(c);
    ZONE.name = 'wilds'; ZONE.cx = W.ox; ZONE.cz = W.oz; ZONE.half = W.half; WM.group.visible = true; WM.portalMesh.visible = true; hideTown();
    state.heroX = WM.spawn.x; state.heroZ = WM.spawn.z; state.yaw = Math.PI;
  } else if (name === 'frost') {
    FM=buildFrostRealm({scene}); townCols=colliders.slice();
    colliders.length=0;for(const c of FM.colliders)colliders.push(c);
    ZONE.name='frost';ZONE.cx=FROST_REALM.cx;ZONE.cz=FROST_REALM.cz;ZONE.half=FROST_REALM.half;
    hideTown();FM.group.visible=true;if(portalT)portalT.visible=false;
    state.heroX=FM.spawn.x;state.heroZ=FM.spawn.z;state.yaw=Math.PI;
  } else {
    colliders.length = 0; for (const c of townCols) colliders.push(c); ZONE.name = 'town'; ZONE.cx = 0; ZONE.cz = 0; ZONE.half = WORLD;
    if (FIGHT && FIGHT.auto) FIGHT.stop();   /* enemies are disposed first */
    unloadWilds();
    if(FM){const old=FM;FM=null;scene.remove(old.group);old.group.traverse(o=>{if(o.geometry)o.geometry.dispose();if(o.material)for(const mat of [].concat(o.material))mat.dispose();});}
    for(const n of townHidden)n.visible=true;townHidden.length=0;
    if(portalT)portalT.visible=true;if(frostCave)frostCave.visible=true;
    state.heroX=lastZone==='frost'?FROST_PORTAL.x:TOWN_PORTAL.x;
    state.heroZ=lastZone==='frost'?FROST_PORTAL.z+6:TOWN_PORTAL.z+4;state.yaw=0;
  }
  state.level = 0; state.target = null; state.climbing = false; updateLevel(); snapFollowers(); zoneCd = 1.5; portalDwell = 0;
  if(name==='wilds'||name==='frost'){const f=await fightToggle(true);f.startAuto();if(name==='frost')f.startRegionBosses('frost');}
  return true;
}
let outdoorCombatStarting=false;
function updateZone(dt) {
  // Automatically enter PvE beyond the walls; town interiors remain protected.
  if(ZONE.name==='town' && (Math.abs(state.heroX)>CITY_HALF+14 || Math.abs(state.heroZ)>CITY_HALF+14) && !outdoorCombatStarting && (!FIGHT||!FIGHT.on)){
    outdoorCombatStarting=true;
    fightToggle(true).then(f=>{if(ZONE.name==='town')f.startAuto();}).finally(()=>{outdoorCombatStarting=false;});
  }
  if (ZONE.name === 'wilds' && WM && WM.cull) WM.cull(state.heroX, state.heroZ, VIEWK);
  const t=performance.now()/1000;
  if(portalT?.userData.update)portalT.userData.update(t);
  if(frostCave?.userData.update)frostCave.userData.update(t);
  if(WM?.portalMesh?.userData.update)WM.portalMesh.userData.update(t);
  if(FM)FM.update(t);
  zoneCd = Math.max(0, zoneCd - dt); if (zoneCd > 0 || state.level !== 0 || state.climbing) { portalDwell = 0; return; }
  const isFrostCave=ZONE.name==='town'&&Math.hypot(state.heroX-FROST_PORTAL.x,state.heroZ-FROST_PORTAL.z)<7;
  const p=ZONE.name==='town'?(isFrostCave?FROST_PORTAL:TOWN_PORTAL):ZONE.name==='frost'?FROST_EXIT:WM?{x:WM.portal.x,z:WM.portal.z}:null;
  if(!p)return;
  if(Math.hypot(state.heroX-p.x,state.heroZ-p.z)<1.7+Math.max(0,HERO_R-0.75)){
    portalDwell+=dt;if(portalDwell>.35){portalDwell=-99;setZone(ZONE.name==='town'?(isFrostCave?'frost':'wilds'):'town');}
  }else if(portalDwell>-50)portalDwell=0;
}

function frame(now) {
  requestAnimationFrame(frame);
  if (!running) return;
  if (now - lastDraw < 11.5) return;            // cap at ~72 fps on 120/144 Hz monitors (75 Hz and below untouched)
  adaptRes(now - lastDraw); lastDraw = now;
  const dt = Math.min(0.05, (now - last) / 1000); last = now;
  updateCrowd(dt); updateHero(dt); updateZone(dt); if (TOWN_LANDS && ZONE.name === 'town') TOWN_LANDS.cull(state.heroX, state.heroZ, VIEWK); if(HOB_CAMPS_WORLD){HOB_CAMPS_WORLD.group.visible=ZONE.name==='town';if(ZONE.name==='town')HOB_CAMPS_WORLD.cull(state.heroX,state.heroZ);} if (FIGHT) FIGHT.update(dt); if (GUARDS && FIGHT && FIGHT.on && ZONE.name === 'town') GUARDS.update(dt, FIGHT.cc); if (GB.visible && (GB.userData.t -= dt) <= 0) GB.visible = false; updateCamera(dt, totalFrames === 0); if (FIGHT && FIGHT.shake) FIGHT.shake(camera);
  simTime += dt; if (SMOKE) SMOKE.update(simTime); if(TOWN_LANDS&&ZONE.name==='town')TOWN_LANDS.updateWater?.(simTime);
  drops.forEach((m, i) => { const t = (simTime * 0.9 + i / drops.length) % 1; const a = i / drops.length * 6.28; m.position.set(Math.cos(a) * t * 1.6, 3.0 + Math.sin(t * 3.14) * 1.0 - t * 0.2, Math.sin(a) * t * 1.6); });
  renderer.render(scene, camera);
  totalFrames++; fpsAcc += dt; fpsFrames++;
  if (fpsAcc >= 0.5) { fps = fpsFrames / fpsAcc; fpsAcc = 0; fpsFrames = 0; fpsEl.textContent = fps.toFixed(0) + ' fps · ' + renderer.info.render.calls + ' calls'; }
  if (totalFrames === 2) {
    // Respect the cinematic loader: it closes after first real 3D paint and
    // the seven-second loading sequence, never before the engine is ready.
    if (window.__vnFinishLoading) window.__vnFinishLoading();
    else {const l=document.getElementById('load');if(l){l.style.opacity=0;setTimeout(()=>l.remove(),480);}}
    setTimeout(()=>{const h=document.getElementById('hint');if(h)h.style.opacity=0;},6000);
  }
}
requestAnimationFrame(frame);

// ---------- save bridge (save3d.js): shared guildbound_rpg_save_v1; only state.active and the p3d field are written ----------
const lastSave = { x: NaN, z: NaN, hero: -1 };
function snapNow() { return { x: state.heroX, z: state.heroZ, yaw: state.yaw, heroGlb: HEROES.indexOf(hero) }; }
if (savedOn) {
  let store = null; try { store = localStorage; } catch (e) {}
  if (store) {
    saver = createSaver(store, GLB_NAMES, snapNow);
    const watch = () => { if (state.inside) return; const dx = state.heroX - lastSave.x, dz = state.heroZ - lastSave.z; if (!(Math.abs(dx) < 0.5 && Math.abs(dz) < 0.5)) { lastSave.x = state.heroX; lastSave.z = state.heroZ; saver.mark(); } };
    setInterval(watch, 700);
    // Mark at shutdown: the interval may not have noticed the last small movement yet.
    const flushLatest = () => { if (!state.inside) saver.mark(); saver.flush(); };
    addEventListener('pagehide', flushLatest);
    document.addEventListener('visibilitychange', () => { if (document.hidden) flushLatest(); });
  }
}
/* ---------- owner cheat panel (hidden gesture; loads cheatpanel.js lazily; owner-gated, see ownergate.js and README) ---------- */
function entrySpot(d) {
  const lim = WORLD - 2, ok = (x, z) => Math.abs(x) < lim && Math.abs(z) < lim && window.__p3d.free(x, z, 0);
  // Registry positions are layout grid coordinates; gatehouse is anchored to the *new* outer wall.
  const bx = d.cx * PK, bz = d.id === 'gatehouse' ? CITY_HALF - 1.2 : d.cz * PK;
  const fx = bx + Math.sin(d.rot || 0) * 8, fz = bz + Math.cos(d.rot || 0) * 8;
  if (ok(fx, fz)) return { x: fx, z: fz };
  for (let r = 5; r <= 26; r += 1.5) for (let k = 0; k < 16; k++) { const a = k / 16 * 6.2832, x = bx + Math.cos(a) * r, z = bz + Math.sin(a) * r; if (ok(x, z)) return { x, z }; }
  return { x: THREE.MathUtils.clamp(bx, -lim, lim), z: THREE.MathUtils.clamp(bz, -lim, lim) };
}
/* ---------- fight test mode (1.1.8): lazy-loaded, owner-gated start (owner panel / HUD button it reveals) ---------- */
let FIGHT = null, GUARDS = null;
/* town guard strike: one reusable line (guard spear-tip -> monster), shown 0.15 s; no allocation per strike */
const GB = (() => { const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(6), 3)); const l = new THREE.Line(g, new THREE.LineBasicMaterial({ color: 0xfff1a8 })); l.visible = false; l.frustumCulled = false; l.userData.keep = true; l.userData.t = 0; scene.add(l); return l; })();
function guardBolt(g, e) { const a = GB.geometry.attributes.position; a.setXYZ(0, g.x, 2.4, g.z); a.setXYZ(1, e.x, 1.1, e.z); a.needsUpdate = true; GB.visible = true; GB.userData.t = 0.15; }
async function fightToggle(createOnly) {
  if (!FIGHT) {
    const mod = await import('./fight.js');
    FIGHT = mod.createFight({ THREE, scene, camera, state, HS, cheat, downAllies, followers: () => crowd.filter(r => r.kind === 'party'), bystanders, killCrowd, hero: () => hero, heroId: () => GLB_IDS[HEROES.indexOf(hero)] || '',
      selectOwner: async () => { const i = GLB_IDS.indexOf('n:owner'); if (i >= 0 && GLB_IDS[HEROES.indexOf(hero)] !== 'n:owner') await selectVariant(SLOT_G[i], curVar(SLOT_G[i])); },
      makeModel: async id => { try { return modeFor(id) === 'blocky' ? makeBlocky(id) : await loadActorModel(id); } catch (e) { return null; } },
      loco: locoAnim, resolve: p => resolve(p), resolveMob: p => resolve(p, false, 'npc'), free: (x, z) => window.__p3d.free(x, z, 0),
      zone: () => ZONE.name, inWilds:(x,z)=>
        (ZONE.name==='wilds' && Math.abs(x-ZONE.cx)<ZONE.half-4 && Math.abs(z-ZONE.cz)<ZONE.half-4) ||
        (ZONE.name==='town' && (Math.abs(x)>CITY_HALF+22||Math.abs(z)>CITY_HALF+22) && Math.max(Math.abs(x),Math.abs(z))<WORLD-18 && Math.hypot(x-TITAN_CENTER.x,z-TITAN_CENTER.z)>120 && Math.hypot(x-FROST_SUMMIT.x,z-FROST_SUMMIT.z)>92),
      biome: (x, z) => ZONE.name==='wilds'&&WM?WM.mod.biome(x - WM.mod.WILDS.ox,z - WM.mod.WILDS.oz):terrainBiome(x,z),
      groundY:(x,z)=>ZONE.name==='frost'?frostElevation(x,z):ZONE.name==='town'&&TOWN_LANDS?TOWN_LANDS.heightAt(x,z):0,
      loadGLTF: url => new Promise((res, rej) => gl.load(url, res, undefined, rej)),
      respawnPos:()=>ZONE.name==='wilds'&&WM?{x:WM.spawn.x,z:WM.spawn.z}:ZONE.name==='frost'?{x:FROST_REALM.cx-8,z:FROST_REALM.cz+155}:{x:0,z:60} });
  }
  if (!GUARDS) { const gm = await import('./combat/guards.js'); GUARDS = new gm.TownGuards(ectx.guardPosts || []); GUARDS.onStrike = guardBolt; }
  if (createOnly) return FIGHT;
  FIGHT.toggle(); return FIGHT;
}
{ const fb = document.getElementById('fightBtn'); if (fb) fb.addEventListener('click', e => { e.preventDefault(); fightToggle(); }); }
let ownerFlag = false;
let cheatStore = null; try { cheatStore = localStorage; } catch (e) { cheatStore = null; }
const cheatEnv = {
  flags: cheat, bumpSys, storage: cheatStore, zones: ['village', 'wilds'],
  hooks: { fightTest: () => fightToggle(),
    godPref: () => { try { return cheatStore.getItem('vn_owner_god_v1') !== '0'; } catch (e) { return true; } },
    unlimPref: () => { try { return cheatStore.getItem('vn_owner_unlim_v1') !== '0'; } catch (e) { return true; } },
    nocdPref: () => { try { return cheatStore.getItem('vn_owner_nocd_v1') !== '0'; } catch (e) { return true; } },
    nocdMode: (on) => { try { cheatStore.setItem('vn_owner_nocd_v1', on ? '1' : '0'); } catch (e) { /* ignore */ } return true; },
    unlimMode: (on) => { try { cheatStore.setItem('vn_owner_unlim_v1', on ? '1' : '0'); } catch (e) { /* ignore */ } return true; },
    godMode: (on) => { try { cheatStore.setItem('vn_owner_god_v1', on ? '1' : '0'); } catch (e) { /* ignore */ } return true; },
    healParty: () => !!(FIGHT && FIGHT.on && FIGHT.cheatHeal()),
    killEnemies: () => !!(FIGHT && FIGHT.on && FIGHT.cheatKill()),
    spawnEnemy: (k) => { if (FIGHT && FIGHT.on) return FIGHT.cheatSpawn(k); fightToggle().then(() => setTimeout(() => FIGHT && FIGHT.on && FIGHT.cheatSpawn(k), 900)); return true; },
    onOwner: () => { if (window.__ownerRoster) window.__ownerRoster(); const b = document.getElementById('fightBtn'); if (b) b.style.display = ''; } },   // owner-gated: only the owner panel calls these
  places: () => BUILDING_DEFS.map(d => { const p = entrySpot(d); return { id: d.id, name: d.name, x: p.x, z: p.z }; }),
  teleport: (x, z, zone) => { if (zone === 'wilds') { setZone('wilds'); return; } const go = () => { state.heroX = x; state.heroZ = z; state.level = 0; state.target = null; updateLevel(); }; if (ZONE.name !== 'town') setZone('town').then(go); else go(); },
  onReady: (c) => { window.__p3d.cheats = c; window.__p3d.owner = true; if (window.__ownerRoster) window.__ownerRoster(); settingsApi.ownerInit(); },
  onOwner: (c) => { window.__p3d.cheats = c; window.__p3d.owner = true; if (window.__ownerRoster) window.__ownerRoster(); },
};
const cheatBoot = initCheatBoot(cheatEnv);
async function setFight(on) { const f = await fightToggle(true); if (on !== f.on) f.toggle(); return !!f.on; }
const fpsEl2 = fpsEl;
const settingsApi = initSettings({ rig: camRig, prefs: camRig.prefs, storage: prefStore || { getItem() { return null; }, setItem() {} }, applyQuality: setQuality, setShadows: (on) => { sun.castShadow = !!on; }, fpsEl: fpsEl2, cheatEnv, openCheatPanel: () => cheatBoot.open(), setCombat: setFight, combatOn: () => !!(FIGHT && FIGHT.on) });
window.__p3d = { get stamina(){return {percent:Math.round(staminaLevel()*100),running:travelRun,exhausted};}, setRunning:setTravelRun, jump, get townLands() { return TOWN_LANDS; }, get frostRealm(){return FM;}, get bossRegions(){return {CITY_HALF,TITAN_CENTER,FROST_SUMMIT,FROST_PORTAL};},  killCrowd, bystanders, charScale: () => ({ id: GLB_IDS[HEROES.indexOf(hero)], CH, HERO_R, heroH: (() => { const b = new THREE.Box3().setFromObject(hero); return b.max.y - b.min.y; })(), dims: (() => { const b = new THREE.Box3().setFromObject(hero), v = new THREE.Vector3(); b.getSize(v); return [v.x, v.y, v.z]; })() }), downAllies, get crowd() { return crowd; }, camRig, settings: settingsApi, setQuality, get owner() { return ownerFlag; }, set owner(v) { ownerFlag = !!v; }, get zone() { return ZONE.name; }, setZone, get wilds() { return WM; }, ZONE, THREE, selectHero, get ladders() { return LAD; },
  teleportTo(x,z){if(!Number.isFinite(x)||!Number.isFinite(z))return false;state.heroX=x;state.heroZ=z;state.target=null;state.level=0;updateLevel();snapFollowers();saver?.mark();return true;},
  modelStatus() { const e = glbInfo.errors || {}; return { build: ASSET_V, loaded: glbInfo.loaded.length, failed: glbInfo.failed.length, models: GLB_IDS.map(id => ({ id, state: glbInfo.loaded.includes(id) ? 'loaded' : glbInfo.failed.includes(id) ? 'failed' : glbInfo.pending.includes(id) ? 'loading' : 'not loaded yet', kb: glbInfo.kb[id] || 0, mode: modeFor(id), error: e[id] || '' })) }; },
  cheat, fightToggle, get fight() { return FIGHT; }, get guards() { return GUARDS; },
  loco: v => { LOCO_FORCE = v; }, actState: () => { const u = hero.userData; return u.act ? Object.fromEntries(Object.entries(u.act).map(([k, a]) => [k, [+a.getEffectiveWeight().toFixed(2), +a.timeScale.toFixed(2)]])) : null; },
  toggleModel: i => toggleModel(i), groups: () => [...GROUPS.values()].map(g => ({ key: g.key, name: g.name, vars: g.vars.map(v => v.label) })),
  saver, flushSave: () => saver ? saver.flush() : false, savedPlan,
  state, glbInfo, colliders, multi: ectx.multi, get hero() { return hero; }, THREE, renderer, scene, enterables,
  enterables, get fps() { return fps; }, get frames() { return totalFrames; },
  info: () => ({ calls: renderer.info.render.calls, triangles: renderer.info.render.triangles, geometries: renderer.info.memory.geometries, textures: renderer.info.memory.textures }),
  onRamp(x, z, level = 0) { const s = surfaceAt(x, z, level); return !!(s && s.ramp); },
  free(x, z, level = 0) { const l0 = state.level; state.level = level; const q = { x, z }; resolve(q); state.level = l0; return !!surfaceAt(x, z, level) && Math.hypot(q.x - x, q.z - z) < 0.02; },
  teleport(x, z, level = 0) { state.heroX = x; state.heroZ = z; state.level = level; state.target = null; updateLevel(); },
  setCamYaw(y) { state.camYaw = y; },
  setZoom(z) { state.zoom = z; },
  bump: { sys: bumpSys, player: playerAct, crowd, on: BUMP_ON },
  setHero, get heroIndex() { return HEROES.indexOf(hero); },
  tapAt: tapMoveTo,
};
