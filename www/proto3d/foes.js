/* Low-poly enemy visuals for the combat core: each enemy is ONE merged, vertex-coloured mesh (1 draw call), pooled and reused.
 * Plus the ground telegraph plane (red disc + ring + warning icon baked into one canvas texture, 1 draw call, only visible while an enemy winds up). */
import * as THREE from './vendor/three.module.js';

const box = (w, h, d, x, y, z, col) => ({ w, h, d, x, y, z, col });
/* Parts are in metres for a 1.5-scale world; +Z is the front. */
const KINDS = {
  wolf: { top: 1.25, parts: [box(.5, .45, 1.1, 0, .62, 0, 0xad9987), box(.38, .36, .42, 0, .8, .72, 0xbcab98), box(.2, .16, .28, 0, .72, 1.05, 0x5b4a3c), box(.1, .16, .08, -.12, 1.05, .62, 0x8a7766), box(.1, .16, .08, .12, 1.05, .62, 0x8a7766),
    box(.12, .42, .12, -.17, .21, .38, 0x8a7766), box(.12, .42, .12, .17, .21, .38, 0x8a7766), box(.12, .42, .12, -.17, .21, -.38, 0x8a7766), box(.12, .42, .12, .17, .21, -.38, 0x8a7766), box(.12, .12, .55, 0, .75, -.78, 0x9b8a78),
    box(.06, .05, .03, -.1, .88, .94, 0xffd34a), box(.06, .05, .03, .1, .88, .94, 0xffd34a)] },
  raider: { top: 2.5, parts: [box(.22, .8, .24, -.15, .4, 0, 0x4a3a2c), box(.22, .8, .24, .15, .4, 0, 0x4a3a2c), box(.62, .75, .36, 0, 1.18, 0, 0xd59066), box(.4, .4, .4, 0, 1.78, 0, 0x7a9a4a), box(.2, .7, .2, -.42, 1.15, 0, 0xc08058), box(.2, .7, .2, .42, 1.15, 0, 0xc08058),
    box(.14, 1.0, .14, .5, 1.1, .35, 0x5a4026), box(.22, .26, .22, .5, 1.7, .35, 0x6b4a2b), box(.06, .05, .03, -.1, 1.82, .21, 0xffd34a), box(.06, .05, .03, .1, 1.82, .21, 0xffd34a)] },
  wraith: { top: 2.9, parts: [box(.7, 1.5, .5, 0, 1.0, 0, 0x4f8f78), box(.5, .5, .5, 0, 2.0, 0, 0x75bca1), box(.9, .3, .6, 0, 0.3, 0, 0x3d7664), box(.15, .9, .15, -.5, 1.2, .15, 0x75bca1), box(.15, .9, .15, .5, 1.2, .15, 0x75bca1),
    box(.1, .08, .03, -.12, 2.05, .26, 0xc8ffd8), box(.1, .08, .03, .12, 2.05, .26, 0xc8ffd8)] },
};
KINDS.skeleton = KINDS.raider;
/* Ashen Titan (placeholder primitives until Beth's model): raider-shaped but 3x scale, plus horns, shoulder plates and glowing eyes. */
KINDS.titan = { scale: 6.7, top: 2.5, parts: KINDS.raider.parts.concat([box(.9, .22, .5, 0, 1.58, 0, 0x6a5560), box(.28, .5, .28, -.2, 2.15, 0, 0xd9d0c4), box(.28, .5, .28, .2, 2.15, 0, 0xd9d0c4), box(.7, .2, .5, 0, .08, 0, 0x2a2228)]).map((q) => (q.col === 0x7a9a4a ? box(q.w, q.h, q.d, q.x, q.y, q.z, 0x9a4a4a) : q.col === 0xd59066 ? box(q.w, q.h, q.d, q.x, q.y, q.z, 0x7a4a58) : q)) };
/* SKIN SLOTS: enemy key -> model id registered in main.js EXTRA (file in proto3d/models-new/<name>.glb). Drop a GLB in by name here; no GLB / fetch failure = the placeholder blocks stay. */
export const SKIN_SLOTS = { titan: 'n:ashentitan_new' };
export const kindFor = (key) => (KINDS[key] ? key : 'raider');
const geoCache = {};
function buildGeo(kind, S) {
  const key = kind + S; S *= (KINDS[kind].scale || 1); if (geoCache[key]) return geoCache[key];
  const pos = [], nor = [], col = [], c = new THREE.Color();
  for (const p of KINDS[kind].parts) {
    const g = new THREE.BoxGeometry(p.w * S, p.h * S, p.d * S).toNonIndexed(); g.translate(p.x * S, p.y * S, p.z * S);
    const a = g.attributes.position, n = g.attributes.normal; c.setHex(p.col);
    for (let i = 0; i < a.count; i++) { pos.push(a.getX(i), a.getY(i), a.getZ(i)); nor.push(n.getX(i), n.getY(i), n.getZ(i)); const sh = 0.85 + 0.15 * Math.abs(n.getY(i)); col.push(c.r * sh, c.g * sh, c.b * sh); }
    g.dispose();
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); geo.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3)); geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  geo.computeBoundingSphere(); return (geoCache[key] = geo);
}
let teleTex = null;
export function telegraphTexture() {
  if (teleTex) return teleTex;
  const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d');
  g.fillStyle = 'rgba(255,40,40,0.55)'; g.beginPath(); g.arc(64, 64, 58, 0, 6.2832); g.fill();
  g.strokeStyle = 'rgba(255,90,70,1)'; g.lineWidth = 6; g.beginPath(); g.arc(64, 64, 58, 0, 6.2832); g.stroke();
  g.fillStyle = '#fff'; g.beginPath(); g.moveTo(64, 30); g.lineTo(94, 86); g.lineTo(34, 86); g.closePath(); g.fill();
  g.fillStyle = '#c01818'; g.fillRect(61, 46, 6, 22); g.fillRect(61, 73, 6, 6);
  teleTex = new THREE.CanvasTexture(c); teleTex.colorSpace = THREE.SRGBColorSpace; return teleTex;
}
/* One pooled visual: mesh (re-pointed at a kind's geometry) + telegraph plane. */
export function createFoe(scene, HS) {
  const mat = new THREE.MeshLambertMaterial({ vertexColors: true, emissive: 0x000000 });
  const mesh = new THREE.Mesh(buildGeo('wolf', HS / 1.5), mat); mesh.visible = false; mesh.castShadow = false; scene.add(mesh);
  const tele = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), new THREE.MeshBasicMaterial({ map: telegraphTexture(), transparent: true, depthWrite: false, opacity: 0.6 }));
  tele.rotation.x = -Math.PI / 2; tele.visible = false; tele.renderOrder = 6; scene.add(tele);
  const skinMats = [];
  return { mesh, mat, tele, kind: '', top: 2, busy: false, skin: null, skinReady: false,
    setSkin(root) { this.clearSkin(); this.skin = root; this.skinReady = true; mesh.add(root); mat.visible = false; skinMats.length = 0; root.traverse((o) => { if (o.isMesh) for (const m of (Array.isArray(o.material) ? o.material : [o.material])) if (m && m.emissive && !skinMats.includes(m)) skinMats.push(m); }); },
    clearSkin() { if (this.skin) { mesh.remove(this.skin); this.skin = null; } this.skinReady = false; mat.visible = true; skinMats.length = 0; },
    setEmissive(hex) { mat.emissive.setHex(hex); for (const m of skinMats) m.emissive.setHex(hex); },
    setKind(k) { const kind = kindFor(k); if (kind !== this.kind) { this.clearSkin(); this.kind = kind; mesh.geometry = buildGeo(kind, HS / 1.5); this.top = KINDS[kind].top * (KINDS[kind].scale || 1) * HS / 1.5; } }, hide() { mesh.visible = false; tele.visible = false; this.clearSkin(); } };
}
