/* Beth round 2 building exteriors (models/beth/buildings/bld_*.glb, metres, door at local +z).
   Swaps the textured exterior shell of 11 buildings for one GLB each (walls + roof, windmill also blades):
   the textured G.ext meshes and the G.roof / G.frame / G.walls children are removed, the GLB `roof` node goes into G.roof
   (so the inside view still fades it) and the rest is added at the building root. Colliders, floors, ladders and
   interiors are untouched, so walk-in and ladder routes behave as before. ?nobeth keeps the old shells.
   Night glow: the shared building atlas is painted without emissive, so window/glass tiles get an emissive mask built
   from the atlas itself (bright warm pixels of the b_window and b_glass tiles), restoring lit windows and the lighthouse lamp. */
import * as THREE from './vendor/three.module.js';
import { GLTFLoader } from './vendor/jsm/loaders/GLTFLoader.js';
export const BETH_BUILDINGS = { house1: 'bld_house1', house2: 'bld_house2', house3: 'bld_house3', house4: 'bld_house4', farmhouse: 'bld_farmhouse', barn: 'bld_barn', stables: 'bld_stables', windmill: 'bld_windmill', lighthouse: 'bld_lighthouse', gt0: 'bld_gate_tower', gt1: 'bld_gate_tower', thieves: 'bld_thieves' };
const GLOW_TILES = [8, 14];   // atlas.json tiles: b_window, b_glass (4x4 grid of 256 px)
function glowMask(img) {
  const S = img.width || 1024, T = S / 4, c = document.createElement('canvas'); c.width = c.height = S; const g = c.getContext('2d', { willReadFrequently: true });
  g.drawImage(img, 0, 0, S, S); const out = g.createImageData(S, S);
  for (const t of GLOW_TILES) { const tx = (t % 4) * T, ty = Math.floor(t / 4) * T, d = g.getImageData(tx, ty, T, T).data;
    for (let y = 0; y < T; y++) for (let x = 0; x < T; x++) { const i = (y * T + x) * 4, r = d[i], gg = d[i + 1], b = d[i + 2];
      if (r > 150 && r >= gg && gg > b && (r + gg) > 300) { const o = ((ty + y) * S + tx + x) * 4; out.data[o] = out.data[o + 1] = out.data[o + 2] = 255; out.data[o + 3] = 255; } } }
  g.putImageData(out, 0, 0); const tex = new THREE.CanvasTexture(c); tex.flipY = false; tex.colorSpace = THREE.SRGBColorSpace; return tex;
}
export async function applyBethExteriors(parts) {
  if (typeof location !== 'undefined' && /nobeth/.test(location.search)) return { n: 0, tick() {} };
  const L = new GLTFLoader(), cache = {}, glowed = new WeakSet(), blades = []; let n = 0;
  for (const s of parts) { const f = BETH_BUILDINGS[s.id]; if (!f || !s.G) continue;
    try { const g = await (cache[f] = cache[f] || L.loadAsync(new URL('./models/beth/buildings/' + f + '.glb', import.meta.url).href));
      for (const m of [...s.G.ext.children]) if (m.isMesh && m.material.map) s.G.ext.remove(m);
      for (const k of ['roof', 'frame', 'walls']) for (const m of [...(s.G[k]?.children || [])]) s.G[k].remove(m);
      for (const c of [...s.root.children]) if (!Object.values(s.G).includes(c)) c.visible = false;   // old procedural shell extras (e.g. the old windmill sails)
      const sc = g.scene.clone(true);
      for (const node of [...sc.children]) {
        node.traverse(o => { if (!o.isMesh) return; o.castShadow = o.receiveShadow = true; o.userData.keep = true; const mt = o.material;
          if (mt.map && !glowed.has(mt)) { glowed.add(mt); try { mt.emissiveMap = glowMask(mt.map.image); mt.emissive = new THREE.Color(0xffb054); mt.emissiveIntensity = s.id === 'lighthouse' ? 1.6 : 0.9; mt.needsUpdate = true; } catch (e) { /* no canvas (tests): keep unlit */ } } });
        node.scale.multiplyScalar(1 / s.K); node.position.multiplyScalar(1 / s.K);
        (node.name === 'roof' ? s.G.roof : s.root).add(node); if (node.name === 'blades') blades.push(node); }
      s.bethShell = f; n++;
    } catch (e) { console.warn('beth building', s.id, e); } }
  return { n, tick(dt) { for (const b of blades) b.rotation.z += dt * .5; } };
}
