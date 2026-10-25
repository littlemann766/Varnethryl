/* Beth world-art kit loader (NEW FILE, art helper — Lucky owns wiring; safe to rewrite).
   Loads the shared-atlas kit GLBs once (top-level await) and exposes:
     KIT.geo(name)            -> BufferGeometry (position, normal, uv, color) in metres, Y-up
     KIT.material             -> ONE MeshStandardMaterial (atlas, vertex colours, alphaTest, double-sided, wind sway)
     KIT.Acc                  -> merge accumulator that keeps uv (scenery.js Acc drops uv)
     KIT.forVariant(kind,name,pal,lod) -> kit geometry that replaces a scenery.js variant, or null
     KIT.placement            -> PLACEMENT.json entries (clusters for the empty land) or []            */
import * as THREE from './vendor/three.module.js';
import { fx } from './fx.js';
const BASE = new URL('./models/beth/', import.meta.url).href;
const geos = new Map(); let material = null, placement = [], index = [];
async function load() {
  try {
    index = await (await fetch(BASE + 'kit_index.json')).json();
    try { placement = await (await fetch(BASE + 'PLACEMENT.json')).json(); placement = placement.items || placement; } catch (e) { placement = []; }
    const { GLTFLoader } = await import('./vendor/jsm/loaders/GLTFLoader.js'); const L = new GLTFLoader();   // dynamic: node checks import townlands.js without a browser
    await Promise.all(index.map(async e => {
      const g = await L.loadAsync(BASE + e.file); let mesh = null; g.scene.traverse(o => { if (o.isMesh && !mesh) mesh = o; });
      if (!mesh) return; const geo = mesh.geometry; geo.computeBoundingBox(); geo.computeBoundingSphere();
      geos.set(e.file.split('/').pop().replace('.glb', ''), geo);
      if (!material) { const m = mesh.material; material = new THREE.MeshStandardMaterial({ map: m.map, vertexColors: true, alphaTest: 0.5, side: THREE.DoubleSide, metalness: 0, roughness: 0.85, name: 'beth_kit_atlas' }); fx(material, 'wild'); }
    }));
  } catch (e) { console.warn('beth kit unavailable, falling back to procedural scenery', e); }
}
if (typeof window !== 'undefined' && !/nokit/.test(location.search)) await load();   // browser only (node regression checks see KIT.ready === false)
class Acc { constructor() { this.p = []; this.n = []; this.u = []; this.c = []; }
  add(g, x, y, z, ry, s) { const P = g.attributes.position.array, N = g.attributes.normal.array, U = g.attributes.uv.array, C = g.attributes.color.array, I = g.index ? g.index.array : null, cs = Math.cos(ry), sn = Math.sin(ry);
    const cnt = I ? I.length : P.length / 3, cw = g.attributes.color.itemSize;
    for (let k = 0; k < cnt; k++) { const i = I ? I[k] : k, px = P[i * 3] * s, pz = P[i * 3 + 2] * s;
      this.p.push(px * cs + pz * sn + x, P[i * 3 + 1] * s + y, -px * sn + pz * cs + z); this.n.push(N[i * 3] * cs + N[i * 3 + 2] * sn, N[i * 3 + 1], -N[i * 3] * sn + N[i * 3 + 2] * cs);
      this.u.push(U[i * 2], U[i * 2 + 1]); this.c.push(C[i * cw], C[i * cw + 1], C[i * cw + 2]); } }
  geo() { if (!this.p.length) return null; const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(this.p, 3)); g.setAttribute('normal', new THREE.Float32BufferAttribute(this.n, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(this.u, 2)); g.setAttribute('color', new THREE.Float32BufferAttribute(this.c, 3)); g.computeBoundingBox(); g.computeBoundingSphere(); return g; } }
/* scenery.js variant -> kit asset. lod: 0 near, 1 mid, 2 far billboard */
const H = s => { let h = 0; for (const c of s) h = (h * 31 + c.charCodeAt(0)) | 0; return Math.abs(h); };
function forVariant(kind, name, pal, lod = 0, salt = 0) {
  if (!geos.size) return null; const sfx = lod === 2 ? '_bb' : lod === 1 ? '_lod1' : '', pickOf = a => a[H(name + pal + salt) % a.length];
  let k = null;
  if (kind === 'trees') {
    k = name === 'pine' ? pickOf(['tree_pine_a', 'tree_pine_b']) : name === 'cypress' ? 'tree_pine_b' : name === 'birch' ? 'tree_birch_a' : name === 'dead' ? 'tree_dead_a' :
      name === 'apple' ? (pal === 'blossom' ? 'tree_apple_blossom' : pal === 'autumn' ? 'tree_oak_red' : 'tree_oak_a') : (pal === 'autumn' ? 'tree_oak_autumn' : pal === 'red' ? 'tree_oak_red' : pal === 'yellow' ? 'tree_oak_yellow' : pal === 'deep' ? 'tree_oak_b' : pickOf(['tree_oak_a', 'tree_oak_a', 'tree_oak_autumn', 'tree_oak_b']));
    const want = k + sfx; return geos.get(want) || geos.get(k + '_lod1') || geos.get(k);
  }
  if (kind === 'bushes') k = pal === 'deep' ? 'bush_b' : 'bush_a';
  if (kind === 'rocks') k = { boulder: 'boulder', stone: pal === 'mossy' ? 'rock_mossy' : 'rock_small', cluster: 'rock_small', slab: 'rock_slab', standing: 'standing_stone' }[name];
  if (kind === 'flowers') k = name === 'grass' ? (pal === 'dry' ? 'grass_dry' : 'grass_a') : ({ white: 'flowers_white', yellow: 'flowers_yellow', pink: 'flowers_red', red: 'flowers_red', purple: 'flowers_purple', blue: 'flowers_blue' }[pal] || 'flowers_white');
  if (kind === 'props') k = { barrel: 'barrel', crate: 'crate', lamp: 'lamp_post', fence: 'fence_2m' }[name];
  return (k && geos.get(k)) || null;
}
export const KIT = { get ready() { return geos.size > 0; }, geo: n => geos.get(n), get material() { return material; }, Acc, forVariant, get placement() { return placement; }, index };
