/* Beth zone-kit placer (NEW FILE, art helper; Lucky owns wiring).
   placeZone(items, {heightAt, chunk, origin}) merges every placed kit piece into ONE mesh per chunk (shared atlas material),
   snapping each piece to heightAt(worldX, worldZ). Returns {group, meshes, cull(x,z,range)}.
   PLACEMENT_<zone>.json items: {file:'frost/ice_rock.glb', position:[x,y|null,z], rotation:[0,ry,0], scale:[s,s,s], replaces:'...'} */
import * as THREE from './vendor/three.module.js';
import { KIT } from './beth-kit.js';
const BASE = new URL('./models/beth/', import.meta.url).href;
export async function loadZonePlacement(zone) { try { const j = await (await fetch(BASE + 'PLACEMENT_' + zone + '.json')).json(); return j.items || j; } catch (e) { return []; } }
export function placeZone(items, { heightAt = () => 0, chunk = 64, origin = [0, 0], name = 'beth-zone', castShadow = true, sectors = null } = {}) {
  const group = new THREE.Group(); group.name = name; const accs = new Map(); let n = 0;
  if (!KIT.ready) return { group, meshes: [], cull() {}, count: 0 };
  for (const it of items) {
    const key = it.file.replace(/^.*\//, '').replace('.glb', ''), g = KIT.geo(key); if (!g) continue;
    const [x, y0, z] = it.position, wx = x + origin[0], wz = z + origin[1], y = (y0 == null ? heightAt(wx, wz) : y0) + (it.sink || -0.04);
    const ck = sectors ? 's' + Math.floor(((Math.atan2(wz - sectors.cz, wx - sectors.cx) + Math.PI) / (2 * Math.PI)) * (sectors.n || 8)) % (sectors.n || 8) : Math.floor(x / chunk) + ':' + Math.floor(z / chunk); /* sectors: ring-shaped zones (volcano) merge by angle around a centre instead of a square grid */ if (!accs.has(ck)) accs.set(ck, new KIT.Acc());
    accs.get(ck).add(g, x, y, z, (it.rotation || [0, 0, 0])[1], (it.scale || [1])[0]); n++;
  }
  const meshes = [];
  for (const A of accs.values()) { const geo = A.geo(); if (!geo) continue; const m = new THREE.Mesh(geo, KIT.material); m.castShadow = castShadow; m.receiveShadow = true; m.userData.keep = true; group.add(m); meshes.push(m); }
  const cull = (x, z, range = 170) => { for (const m of meshes) { const s = m.geometry.boundingSphere; m.visible = Math.hypot(s.center.x + origin[0] - x, s.center.z + origin[1] - z) - s.radius < range; } };
  return { group, meshes, cull, count: n };
}
export function kitMesh(file) { const g = KIT.geo(file.replace(/^.*\//, '').replace('.glb', '')); if (!g) return null; const m = new THREE.Mesh(g, KIT.material); m.castShadow = m.receiveShadow = true; m.userData.keep = true; return m; }
