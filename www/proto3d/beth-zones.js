/* Beth zone-kit placer (NEW FILE, art helper; Lucky owns wiring).
   placeZone(items, {heightAt, chunk, origin}) merges every placed kit piece into ONE mesh per chunk (shared atlas material),
   snapping each piece to heightAt(worldX, worldZ). Returns {group, meshes, cull(x,z,range)}.
   PLACEMENT_<zone>.json items: {file:'frost/ice_rock.glb', position:[x,y|null,z], rotation:[0,ry,0], scale:[s,s,s], replaces:'...'} */
import * as THREE from './vendor/three.module.js';
import { KIT } from './beth-kit.js';
const BASE = new URL('./models/beth/', import.meta.url).href;
export async function loadZonePlacement(zone) { try { const j = await (await fetch(BASE + 'PLACEMENT_' + zone + '.json')).json(); return j.items || j; } catch (e) { return []; } }
export function placeZone(items, { heightAt = () => 0, chunk = 64, origin = [0, 0], name = 'beth-zone', castShadow = true } = {}) {
  const group = new THREE.Group(); group.name = name; const accs = new Map(); let n = 0;
  if (!KIT.ready) return { group, meshes: [], cull() {}, count: 0 };
  for (const it of items) {
    const key = it.file.replace(/^.*\//, '').replace('.glb', ''), g = KIT.geo(key); if (!g) continue;
    const [x, y0, z] = it.position, wx = x + origin[0], wz = z + origin[1], y = (y0 == null ? heightAt(wx, wz) : y0) + (it.sink || -0.04);
    const ck = Math.floor(x / chunk) + ':' + Math.floor(z / chunk); if (!accs.has(ck)) accs.set(ck, new KIT.Acc());
    accs.get(ck).add(g, x, y, z, (it.rotation || [0, 0, 0])[1], (it.scale || [1])[0]); n++;
  }
  const meshes = [];
  for (const A of accs.values()) { const geo = A.geo(); if (!geo) continue; const m = new THREE.Mesh(geo, KIT.material); m.castShadow = castShadow; m.receiveShadow = true; m.userData.keep = true; group.add(m); meshes.push(m); }
  const cull = (x, z, range = 170) => { for (const m of meshes) { const s = m.geometry.boundingSphere; m.visible = Math.hypot(s.center.x + origin[0] - x, s.center.z + origin[1] - z) - s.radius < range; } };
  return { group, meshes, cull, count: n };
}
export function kitMesh(file) { const g = KIT.geo(file.replace(/^.*\//, '').replace('.glb', '')); if (!g) return null; const m = new THREE.Mesh(g, KIT.material); m.castShadow = m.receiveShadow = true; m.userData.keep = true; return m; }
/* Round 3: dressing + decals. Loads the GLBs listed in items (any atlas), keeps ONE material per atlas
   (buildings/atlas for dressing, decals/atlas for decals; alpha-cut, polygonOffset so decals don't z-fight),
   and merges per chunk per material. Same item format; y:null snaps to heightAt, explicit y is kept (wall pieces). */
import { GLTFLoader } from './vendor/jsm/loaders/GLTFLoader.js';
const _geo = new Map(), _mat = new Map();
async function _load(file) {
  if (_geo.has(file)) return _geo.get(file);
  const p = new GLTFLoader().loadAsync(BASE + file).then(g => { let geo = null, mat = null; g.scene.updateMatrixWorld(true);
    g.scene.traverse(o => { if (o.isMesh && !geo) { geo = o.geometry.clone().applyMatrix4(o.matrixWorld); mat = o.material; } });
    const key = mat.name || 'm'; if (!_mat.has(key)) { mat.metalness = 0; mat.vertexColors = true; if (/decal/.test(key)) { mat.polygonOffset = true; mat.polygonOffsetFactor = -2; mat.polygonOffsetUnits = -2; mat.depthWrite = false; mat.alphaTest = 0.5; mat.transparent = false; } _mat.set(key, mat); }
    return { geo, key }; }).catch(() => null);
  _geo.set(file, p); return p;
}
export async function placeDressing(items, { heightAt = () => 0, chunk = 96, origin = [0, 0], name = 'beth-dressing', castShadow = true } = {}) {
  const group = new THREE.Group(); group.name = name; const accs = new Map(); let n = 0;
  const L = await Promise.all([...new Set(items.map(i => i.file))].map(async f => [f, await _load(f)])); const G = new Map(L);
  for (const it of items) { const e = G.get(it.file); if (!e) continue;
    const [x, y0, z] = it.position, wx = x + origin[0], wz = z + origin[1], y = (y0 == null ? heightAt(wx, wz) + (it.sink || -0.04) : y0);
    const ck = e.key + '|' + Math.floor(x / chunk) + ':' + Math.floor(z / chunk); if (!accs.has(ck)) accs.set(ck, { key: e.key, A: new KIT.Acc() });
    accs.get(ck).A.add(e.geo, x, y, z, (it.rotation || [0, 0, 0])[1], (it.scale || [1])[0]); n++; }
  const meshes = [];
  for (const { key, A } of accs.values()) { const geo = A.geo(); if (!geo) continue; const m = new THREE.Mesh(geo, _mat.get(key)); const dec = /decal/.test(key);
    m.castShadow = castShadow && !dec; m.receiveShadow = true; m.renderOrder = dec ? 1 : 0; m.userData.keep = true; group.add(m); meshes.push(m); }
  const cull = (x, z, range = 200) => { for (const m of meshes) { const s = m.geometry.boundingSphere; m.visible = Math.hypot(s.center.x + origin[0] - x, s.center.z + origin[1] - z) - s.radius < range; } };
  return { group, meshes, cull, count: n };
}
