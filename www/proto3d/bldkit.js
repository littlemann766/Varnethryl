// Varnethryl 3D buildings: builder kit. One Builder per building: hollow walls with a real door gap, world-scaled UVs, per-building
// cutaway materials (walls go see-through and the roof hides when the hero is inside), furniture kit, and a merge pass that collapses every
// group into one mesh per material (phone-friendly). Local space: +z is the facade/door, y=0 is the ground.
import * as THREE from 'three';
import { tex, bannerTexture, signTexture } from './bldtex.js';
import { FX, fx } from './fx.js';

export const TILE = { stone: 3, stoneD: 3, stoneL: 3.2, rock: 4, plaster: 3, timber: 2.4, darkWood: 2, wood: 1.6, slate: 2.2, slateG: 2.2, hay: 2, floorPlank: 3, floorStone: 3, floorTile: 2, sand: 4, cobble: 3, pave: 3, carpet: 2, rug: 3, sigil: 6, marbleInlay: 3, awning: 1.6, glass: 1, stained: 1, door: 1, iron: 1, water: 4, parchment: 1, gold: 1, books: 1.2, grass: 4 };
// ===== living-world shader FX (one shared time + wind uniform, no per-frame JS allocation) =====
// kinds: 'flag' (cloth waves, pinned at the top uv.y=1), 'water' (scrolling two-layer flow + glints), 'flicker' (warm torch/lantern glow),
// 'tree' / 'grass' (wind sway of the world-space height; instanced or plain meshes). Every FX material is flagged noVC so it never merges into the flat-colour class.
export { FX, fx };
// expanding ripple rings (fountain basins): cheap ShaderMaterial on a flat disc, uv-radial
export function rippleMat(col = '#bfe4ff') { const c = new THREE.Color(col);
  return new THREE.ShaderMaterial({ transparent: true, depthWrite: false, side: THREE.DoubleSide, uniforms: { uTime: FX.uTime, uC: { value: c } },
    vertexShader: 'varying vec2 vU; void main(){ vU = uv - 0.5; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
    fragmentShader: 'uniform float uTime; uniform vec3 uC; varying vec2 vU; void main(){ float r = length(vU) * 2.0; if (r > 1.0) discard; float w = sin(r * 26.0 - uTime * 2.6) * 0.5 + 0.5; float a = smoothstep(0.78, 1.0, w) * (1.0 - r * 0.7) * 0.5; gl_FragColor = vec4(uC, a); }' }); }

const matCache = {};
export function M(key, extra) { // shared lit material by texture key (or flat colour with '#rrggbb')
  const id = key + (extra ? JSON.stringify(extra) : ''); if (matCache[id]) return matCache[id];
  const o = Object.assign({}, extra); if (key[0] === '#') o.color = new THREE.Color(key); else o.map = tex(key);
  const m = new THREE.MeshLambertMaterial(o); if (key === 'water') fx(m, 'water');
  return matCache[id] = m;
}
export const WM = (c, kind = 'grass') => { const v = parseInt(c.slice(1), 16), lum = ((v >> 16) & 255) * .3 + ((v >> 8) & 255) * .59 + (v & 255) * .11; return fx(M(lum > 118 ? '#55993f' : '#3f7a3a', { name: 'wind_' + kind }), kind); };   // two shared shades: fewer draw calls   // wind-swayed flat colour (bushes, tufts, potted plants)
export const GLOW = (c, k = 1) => { const m = M('#' + c, { emissive: new THREE.Color('#' + c), emissiveIntensity: k }); const r = parseInt(c.slice(0, 2), 16), b = parseInt(c.slice(4, 6), 16); if (r > b + 40) fx(m, 'flicker'); return m; };
export function uvScale(g, su, sv) { const uv = g.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) * su, uv.getY(i) * sv); return g; }
export function boxG(w, h, d, tile = 2) {
  const g = new THREE.BoxGeometry(w, h, d), uv = g.attributes.uv, dims = [[d, h], [d, h], [w, d], [w, d], [w, h], [w, h]];
  for (let f = 0; f < 6; f++) for (let v = 0; v < 4; v++) { const i = f * 4 + v; uv.setXY(i, uv.getX(i) * dims[f][0] / tile, uv.getY(i) * dims[f][1] / tile); }
  return g;
}
export function boxL(w, h, d, tile = 2) { // trim box without the underside and back (wall-facing) faces: 8 tris instead of 12
  const g = boxG(w, h, d, tile), idx = g.index.array, keep = []; for (let f = 0; f < 6; f++) if (f !== 3 && f !== 5) for (let k = 0; k < 6; k++) keep.push(idx[f * 6 + k]); g.setIndex(keep); return g; }
export function cylG(rt, rb, h, seg, tile = 3, open = false) { const g = new THREE.CylinderGeometry(rt, rb, h, seg, 1, open); const c = 2 * Math.PI * Math.max(rt, rb); return uvScale(g, c / tile, h / tile); }
export function gableG(W, L, rh, over, tile = 2.2) { // ridge along z; returns slopes (slate) geometry
  const hw = W / 2 + over, hl = L / 2 + over, s = Math.hypot(hw, rh), p = [], uv = [];
  const quad = (a, b, c, d, u0, u1) => { p.push(...a, ...b, ...c, ...a, ...c, ...d); uv.push(0, 0, u1, 0, u1, s / tile, 0, 0, u1, s / tile, 0, s / tile); };
  const u1 = 2 * hl / tile;
  quad([-hw, 0, -hl], [-hw, 0, hl], [0, rh, hl], [0, rh, -hl], 0, u1);
  quad([hw, 0, hl], [hw, 0, -hl], [0, rh, -hl], [0, rh, hl], 0, u1);
  // under-side so the eaves read as thick
  quad([-hw, -.12, hl], [-hw, -.12, -hl], [0, rh - .12, -hl], [0, rh - .12, hl], 0, u1);
  quad([hw, -.12, -hl], [hw, -.12, hl], [0, rh - .12, hl], [0, rh - .12, -hl], 0, u1);
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); g.computeVertexNormals(); return g;
}
export function triG(W, rh, z, flip, tile = 2.4) { // gable-end triangle at z
  const hw = W / 2, p = [-hw, 0, z, hw, 0, z, 0, rh, z], uv = [0, 0, W / tile, 0, W / 2 / tile, rh / tile];
  const g = new THREE.BufferGeometry(); if (flip) { p.splice(0, 6, hw, 0, z, -hw, 0, z); } g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); g.computeVertexNormals(); return g;
}
export function mergeGroup(grp) {
  grp.updateMatrix(); const buckets = new Map(), rm = [];
  for (const o of grp.children) { if (!o.isMesh || o.userData.keep) continue; o.updateMatrix(); const k = o.material.uuid + (o.castShadow ? 'c' : '') + (o.receiveShadow ? 'r' : ''); if (!buckets.has(k)) buckets.set(k, { m: o.material, c: o.castShadow, r: o.receiveShadow, l: [] }); buckets.get(k).l.push(o); rm.push(o); }
  for (const b of buckets.values()) {
    const parts = b.l.map(o => { let g = o.geometry.index ? o.geometry.toNonIndexed() : o.geometry.clone(); if (!g.attributes.uv) g.setAttribute('uv', new THREE.Float32BufferAttribute(new Float32Array(g.attributes.position.count * 2), 2)); if (!g.attributes.normal) g.computeVertexNormals(); g.applyMatrix4(o.matrix); return g; });
    let n = 0; for (const g of parts) n += g.attributes.position.count; const pos = new Float32Array(n * 3), nor = new Float32Array(n * 3), uv = new Float32Array(n * 2); let a = 0, c = 0;
    for (const g of parts) { pos.set(g.attributes.position.array, a); nor.set(g.attributes.normal.array, a); uv.set(g.attributes.uv.array, c); a += g.attributes.position.count * 3; c += g.attributes.position.count * 2; g.dispose(); }
    const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.BufferAttribute(pos, 3)); geo.setAttribute('normal', new THREE.BufferAttribute(nor, 3)); geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    const m = new THREE.Mesh(geo, b.m); m.castShadow = b.c; m.receiveShadow = b.r; m.userData.merged = true; m.userData.keep = true; grp.add(m);
  }
  for (const o of rm) { grp.remove(o); o.geometry.dispose(); }
}

const DOOR_MAXW = 2.2, DOOR_MAXH = 1.95;   // local units; x K = world: doors ~1.2x hero height (3.3 vs 2.7)
export class Builder {
  constructor(ctx, spec) {
    this.ctx = ctx; this.spec = spec; const { scene, colliders } = ctx; this.colliders = colliders;
    this.id = spec.id; this.cx = spec.cx; this.cz = spec.cz; this.rot = spec.rot || 0; this.cs = Math.cos(this.rot); this.sn = Math.sin(this.rot);
    this.root = new THREE.Group(); this.K = spec.K || 1; this.root.position.set(this.cx, 0, this.cz); this.root.rotation.y = this.rot; this.root.scale.setScalar(this.K); scene.add(this.root);
    this.G = {}; this.lvTag = 0; this.curUp = null; this.floors = []; this.ramps = []; for (const k of ['ext', 'walls', 'roof', 'frame', 'int']) { this.G[k] = new THREE.Group(); this.root.add(this.G[k]); }
    { let h = 0; for (const ch of String(spec.id)) h = (h * 31 + ch.charCodeAt(0)) | 0; this.shutKey = ['darkWood', '#2f56a8', '#3f6a3a', '#7a2a2a', '#9a7a2a', '#5a3a6a'][Math.abs(h >> 2) % 6]; }
    this.cut = []; this.cutCache = {}; this.dyn = []; this.T = 0.45; this.inside = false; this.colInfo = []; this.insideTest = null; this.footprint = null;
  }
  // ---- placement helpers ----
  toW(lx, lz) { const K = this.K; return [this.cx + (lx * this.cs + lz * this.sn) * K, this.cz + (-lx * this.sn + lz * this.cs) * K]; }
  toL(wx, wz) { const K = this.K, dx = (wx - this.cx) / K, dz = (wz - this.cz) / K; return [dx * this.cs - dz * this.sn, dx * this.sn + dz * this.cs]; }
  col(lx, lz, bw, bd) { // axis-aligned in local; world box when rot is a quarter turn, else a row of circles
    const q = Math.round(this.rot / (Math.PI / 2)); const [wx, wz] = this.toW(lx, lz);
    if (Math.abs(this.rot - q * Math.PI / 2) < 1e-3) { const K = this.K, odd = ((q % 2) + 2) % 2, W = (odd ? bd : bw) * K, D = (odd ? bw : bd) * K; this.colliders.push({ type: 'box', minX: wx - W / 2, maxX: wx + W / 2, minZ: wz - D / 2, maxZ: wz + D / 2, b: this.id, lv: this.lvTag }); }
    else { const n = Math.max(1, Math.ceil(Math.max(bw, bd) / Math.min(bw, bd) / 1)), r = (Math.min(bw, bd) / 2 + .05) * this.K; for (let i = 0; i < n; i++) { const f = n === 1 ? 0 : (i / (n - 1) - .5); const [x, z] = this.toW(lx + (bw >= bd ? f * (bw - bd) : 0), lz + (bw < bd ? f * (bd - bw) : 0)); this.colliders.push({ type: 'circle', x, z, r, b: this.id, lv: this.lvTag }); } }
  }
  ccol(lx, lz, r) { const [x, z] = this.toW(lx, lz); r *= this.K; this.colliders.push({ type: 'circle', x, z, r, b: this.id, lv: this.lvTag }); }
  // ---- mesh helpers ----
  add(geo, mat, x, y, z, grp, o = {}) { if (this.curUp && grp === this.G.int) { grp = this.curUp.group; y += this.curUp.y; } const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = o.shadow !== false; m.receiveShadow = o.recv !== false; if (o.keep) m.userData.keep = true; if (this._st) m.userData.stairPart = true; (grp || this.G.ext).add(m); return m; }
  bx(w, h, d, key, x, y, z, grp, o) { return this.add((o && o.lite ? boxL : boxG)(w, h, d, TILE[key] || 2), M(key, o && o.mat), x, y, z, grp, o); }
  cm(key) { return this.cutCache[key] || (this.cutCache[key] = (() => { const m = M(key).clone(); this.cut.push(m); return m; })()); } // per-building cutaway material
  wallBox(w, h, d, key, x, y, z, grp) { return this.add(boxG(w, h, d, TILE[key] || 2), this.cm(key), x, y, z, grp || this.G.walls); }
  cyl(rt, rb, h, key, x, y, z, grp, seg = 12, o) { return this.add(cylG(rt, rb, h, seg, TILE[key] || 2), M(key), x, y, z, grp, o); }
  ring(r, h, key, x, y, z, grp, seg = 14) { return this.add(cylG(r, r, h, seg, TILE[key] || 2, true), M(key, { side: THREE.DoubleSide }), x, y, z, grp || this.G.ext); }
  cone(r, h, key, x, y, z, grp, seg = 8, o) { const g = new THREE.ConeGeometry(r, h, seg); uvScale(g, 2 * Math.PI * r / (TILE[key] || 2), Math.hypot(r, h) / (TILE[key] || 2)); return this.add(g, M(key, { side: THREE.DoubleSide }), x, y + h / 2, z, grp, o); }
  gable(W, L, rh, x, y, z, key, grp, ridgeX = false, over = .5, endKey = 'timber') {
    const g = gableG(W, L, rh, over, TILE[key] || 2.2), m = this.add(g, M(key, { side: THREE.DoubleSide }), x, y, z, grp);
    const e1 = this.add(triG(W, rh, L / 2, false, TILE[endKey] || 2.4), M(endKey, { side: THREE.DoubleSide }), x, y, z, grp), e2 = this.add(triG(W, rh, -L / 2, true, TILE[endKey] || 2.4), M(endKey, { side: THREE.DoubleSide }), x, y, z, grp);
    if (ridgeX) for (const o of [m, e1, e2]) { o.geometry.rotateY(Math.PI / 2); }
    this.add(ridgeX ? boxG(L + over * 2 + .2, .16, .18, 1) : boxG(.18, .16, L + over * 2 + .2, 1), M('#2a2420'), x, y + rh, z, grp);   // ridge beam
    this.roofTrim(W, L, rh, over, x, y, z, key, grp, ridgeX, endKey);
    return m;
  }
  roofTrim(W, L, rh, over, x, y, z, key, grp, ridgeX, endKey) { // eave fascia + rafter tails, barge boards, ridge cap + finials, half-timber gable ends
    const hw = W / 2 + over, hl = L / 2 + over, al = Math.atan2(rh, hw), sl = Math.hypot(hw, rh), g = grp || this.G.roof;
    const P = (geo, mat, ox, oy, oz, rz = 0) => { const m = this.add(geo, mat, x + (ridgeX ? oz : ox), y + oy, z + (ridgeX ? -ox : oz), g, { shadow: false }); m.rotation.order = 'YXZ'; m.rotation.y = ridgeX ? Math.PI / 2 : 0; m.rotation.z = rz; return m; };
    const boxG = boxL, dk = M('darkWood'), n = Math.max(2, Math.round(2 * hl / 2.4)) * 2;
    for (const sd of [-1, 1]) { P(boxG(.1, .22, 2 * hl, 1.6), dk, sd * hw, -.09, 0);
}
    for (const e of [-1, 1]) for (const sd of [-1, 1]) P(boxG(sl + .1, .17, .09, 1.6), dk, sd * hw / 2, rh / 2 - .02, e * (hl + .02), -sd * al);
    P(boxG(.42, .1, 2 * hl + .1, 2), M(key === 'slateG' ? 'slateG' : 'slate'), 0, rh + .1, 0);
    for (const e of [-1, 1]) { P(new THREE.ConeGeometry(.13, .55, 4), M('iron'), 0, rh + .42, e * (hl + .08)); P(new THREE.SphereGeometry(.09, 5, 4), M('gold'), 0, rh + .72, e * (hl + .08)); }
    if (W > 4) { const gw = W / 2; for (const e of [-1, 1]) { const zz = e * (L / 2 + .06), gk = M('darkWood');   // gable-end timber frame
      P(boxG(.14, rh * .85, .08, 1.6), gk, 0, rh * .42, zz); P(boxG(W * .62, .12, .08, 1.6), gk, 0, rh * .32, zz);
      for (const sd of [-1, 1]) P(boxG(Math.hypot(gw * .3, rh * .3) + .1, .1, .08, 1.6), gk, sd * gw * .32, rh * .5, zz, -sd * Math.atan2(rh * .3, gw * .3)); } }
  }
  banner(x, y, z, ry = 0, w = 1, h = 2.2, grp) { const m = fx(M('#ffffff', { map: bannerTexture(), side: THREE.DoubleSide, alphaTest: .5 }), 'flag'); const p = this.add(new THREE.PlaneGeometry(w, h, 2, 6), m, x, y, z, grp || this.G.ext, { shadow: false }); p.rotation.y = ry;
    const rod = this.bx(w + .3, .06, .06, 'iron', x, y + h / 2 + .03, z, grp || this.G.ext, { shadow: false }); rod.rotation.y = ry; for (const s of [-1, 1]) { const k = this.add(new THREE.SphereGeometry(.06, 5, 4), M('gold'), x + Math.cos(ry) * s * (w / 2 + .15), y + h / 2 + .03, z - Math.sin(ry) * s * (w / 2 + .15), grp || this.G.ext, { shadow: false }); }
    return p; }
  win(x, y, z, ry = 0, w = .9, h = 1.2, key = 'glass', grp, shut = key === 'glass' && w < 1.4 && !this.noShutters) {
    if (shut) for (const s of [-1, 1]) { const sh = this.bx(w * .42, h, .06, this.shutKey, x + Math.cos(ry) * s * (w * .72), y, z - Math.sin(ry) * s * (w * .72) + Math.cos(ry) * .03, grp || this.G.ext); sh.rotation.y = ry; } const p = this.add(new THREE.PlaneGeometry(w, h), M('#ffffff', { map: tex(key), emissive: key === 'glass' ? new THREE.Color(0x70480f) : new THREE.Color(0x0a1840), side: THREE.DoubleSide }), x, y, z, grp || this.G.ext, { shadow: false }); p.rotation.y = ry;
    const f = this.bx(w + .2, .12, .2, 'darkWood', x + Math.sin(ry) * .02, y - h / 2 - .04, z + Math.cos(ry) * .02, grp || this.G.ext); f.rotation.y = ry;
    // frame (jambs + stone lintel with keystone) and glazing bars
    { const g = grp || this.G.ext, cr = Math.cos(ry), sr = Math.sin(ry), at = (bw, bh, bd, key, u, yy, v) => { const b = this.bx(bw, bh, bd, key, x + cr * u + sr * v, y + yy, z - sr * u + cr * v, g, { shadow: false, lite: true }); b.rotation.y = ry; return b; };
      for (const sd of [-1, 1]) at(.07, h + .06, .14, 'darkWood', sd * (w / 2 + .03), 0, .04);
      at(w + .42, .16, .22, 'stoneD', 0, h / 2 + .1, .05);
      at(.035, h, .05, 'darkWood', 0, 0, .03); if (shut) for (const sd of [-1, 1]) at(w * .26, h * .8, .03, 'wood', sd * w * .72, 0, .07); }
    return p; }
  sign(text, emblem, x, y, z, ry = 0) { // hanging shop sign on an iron bracket
    const t = signTexture(text, emblem), s = this.add(new THREE.PlaneGeometry(1.5, .75), new THREE.MeshLambertMaterial({ map: t, side: THREE.DoubleSide }), x, y, z, this.G.ext, { shadow: false, keep: true }); s.rotation.y = ry;
    const br = this.bx(.08, .08, 1.0, 'iron', x, y + .5, z - Math.cos(ry) * .5 * 0, this.G.ext); br.rotation.y = ry; return s; }
  chimney(x, y, z, h = 2.4, key = 'stoneD', w = .9) { { const [wx, wz] = this.toW(x, z); (this.ctx.smoke || (this.ctx.smoke = [])).push([wx, y + h + .6, wz]); } this.bx(w, h, w, key, x, y + h / 2, z, this.G.roof); this.bx(w + .25, .18, w + .25, key, x, y + h, z, this.G.roof); this.bx(w + .12, .14, w + .12, 'stoneL', x, y + h * .55, z, this.G.roof);
    for (const sx of [-1, 1]) { this.cyl(.12, .15, .38, 'iron', x + sx * w * .2, y + h + .27, z, this.G.roof, 6); this.cyl(.17, .12, .08, 'iron', x + sx * w * .2, y + h + .5, z, this.G.roof, 6); } }
  dormer(x, y, z, w = 1.4, h = 1.2) { this.bx(w, h, 1, 'timber', x, y + h / 2, z, this.G.roof); this.gable(w, 1.0, .8, x, y + h, z, 'slate', this.G.roof, false, .2); this.win(x, y + h / 2, z + .52, 0, .6, .7, 'glass', this.G.roof); }
  tower(x, z, r, h, o = {}) { // round stone tower with corbelled crenel ring and conical slate roof (roof in G.roof when o.roofGroup)
    const key = o.key || 'stone'; this.cyl(r, r * 1.06, h, key, x, h / 2, z, this.G.ext, 14);
    this.ring(r * 1.18, .5, 'stoneD', x, h + .25, z, this.G.ext, 14);
    for (let i = 0; i < 8; i++) { const a = i / 8 * 6.283; this.bx(.5, .5, .5, key, x + Math.cos(a) * r * 1.12, h + .75, z + Math.sin(a) * r * 1.12, this.G.ext); }
    if (o.cone !== false) this.cone(r * 1.3, o.coneH || r * 2.2, o.roofKey || 'slate', x, h + .5, z, o.roofGroup || this.G.ext, 14);
    if (o.flag !== false && o.cone !== false) this.flag(x, h + .5 + (o.coneH || r * 2.2) - .1, z, .9, o.roofGroup || this.G.ext);
    if (o.collide !== false) this.ccol(x, z, r * 1.08);
    if (o.windows) for (let i = 0; i < o.windows; i++) { const a = i / o.windows * 6.283 + (o.wa || .8); this.win(x + Math.cos(a) * (r * 1.05), h * .62, z + Math.sin(a) * (r * 1.05), Math.PI / 2 - a, .35, .8, 'glass'); }
  }
  // ---- standard rectangular shell: stone base + upper storey, hollow, door gap at +z ----
  rectShell(o) { const _lv = this.lvTag; this.lvTag = undefined; try { return this._rectShell(o); } finally { this.lvTag = _lv; } }
  _rectShell(o) {
    const { w, d, h } = o, T = this.T, DW = Math.min(o.DW || 2.2, DOOR_MAXW), DH = Math.min(o.DH || 2.6, DOOR_MAXH), hs = o.hs === undefined ? h * .42 : o.hs;
    const lo = o.lower || 'stone', up = o.upper || 'timber'; this.w = w; this.d = d; this.h = h; this.DW = DW;
    const seg = (bw, bh, bd, x, y, z) => { // stacked: stone base to hs, upper above
      if (hs > 0 && hs < y + bh / 2 + .01 && y - bh / 2 < hs - .01 && bh > .01) { /* split below */ }
      const yb = y - bh / 2, yt = y + bh / 2; const cuts = hs > yb + .01 && hs < yt - .01;
      if (!cuts) this.wallBox(bw, bh, bd, yt <= hs + .01 ? lo : up, x, y, z); else { this.wallBox(bw, hs - yb, bd, lo, x, yb + (hs - yb) / 2, z); this.wallBox(bw, yt - hs, bd, up, x, hs + (yt - hs) / 2, z); }
    };
    seg(w, h, T, 0, h / 2, -d / 2 + T / 2); this.col(0, -d / 2 + T / 2, w, T);
    seg(T, h, d, -w / 2 + T / 2, h / 2, 0); this.col(-w / 2 + T / 2, 0, T, d);
    seg(T, h, d, w / 2 - T / 2, h / 2, 0); this.col(w / 2 - T / 2, 0, T, d);
    const fw = (w - DW) / 2;
    for (const sx of [-1, 1]) { seg(fw, h, T, sx * (DW / 2 + fw / 2), h / 2, d / 2 - T / 2); this.col(sx * (DW / 2 + fw / 2), d / 2 - T / 2, fw, T); }
    seg(DW, h - DH, T, 0, DH + (h - DH) / 2, d / 2 - T / 2);
    // door frame, step, open leaf
    for (const sx of [-1, 1]) this.bx(.28, DH, .6, 'stoneD', sx * (DW / 2 + .1), DH / 2, d / 2 - T / 2, this.G.frame);
    this.bx(DW + .7, .3, .6, 'stoneD', 0, DH + .1, d / 2 - T / 2, this.G.frame);
    this.bx(DW + .8, .14, 1.1, 'stoneD', 0, .07, d / 2 + .3, this.G.ext); this.bx(DW + 1.0, .1, 1.5, 'stoneD', 0, .03, d / 2 + .55, this.G.ext, { shadow: false });
    this.bx(.3, .26, .5, 'stoneL', 0, DH + .36, d / 2 - T / 2, this.G.frame);   // keystone
    for (const sx of [-1, 1]) { this.bx(.12, .12, .12, 'iron', sx * (DW / 2 + .1), DH * .3, d / 2 + .03, this.G.ext, { shadow: false, lite: true }); this.bx(.12, .12, .12, 'iron', sx * (DW / 2 + .1), DH * .75, d / 2 + .03, this.G.ext, { shadow: false, lite: true }); }
    if (o.doorHood && (hs < 2.6 || (h - hs) <= 1.8)) { const hd = this.bx(DW + 1.2, .12, 1.15, 'slate', 0, DH + .72, d / 2 + .48, this.G.frame, { shadow: false, lite: true }); hd.rotation.x = .26; for (const sx of [-1, 1]) { const br = this.bx(.1, .1, .9, 'darkWood', sx * (DW / 2 + .5), DH + .45, d / 2 + .45, this.G.frame, { shadow: false, lite: true }); br.rotation.x = -.5; } this.bx(DW + 1.3, .1, .1, 'darkWood', 0, DH + .62, d / 2 + .98, this.G.frame, { shadow: false, lite: true }); }
    else if (o.doorHood && hs >= 2.6 && h - hs > 1.8) { const by = hs + .02, bw = DW + 1.8, bz = d / 2 + .6, g = this.G.frame;   // balcony over the door: slab, rail, balusters, brackets
      this.bx(bw, .16, 1.2, 'darkWood', 0, by, bz, g); this.bx(bw + .1, .08, 1.3, 'wood', 0, by + .1, bz, g, { shadow: false, lite: true });
      for (const [rx, rz, rw, rd] of [[0, bz + .55, bw, .07], [-bw / 2 + .03, bz, .07, 1.1], [bw / 2 - .03, bz, .07, 1.1]]) this.bx(rw, .08, rd, 'darkWood', rx, by + 1.0, rz, g, { shadow: false, lite: true });
      for (let i = 0; i <= 8; i++) this.bx(.06, .85, .06, 'darkWood', -bw / 2 + .06 + i * (bw - .12) / 8, by + .55, bz + .55, g, { shadow: false, lite: true });
      for (const sx of [-1, 1]) { this.bx(.07, .85, .07, 'darkWood', sx * (bw / 2 - .05), by + .55, bz, g, { shadow: false, lite: true }); const br = this.bx(.12, .12, .95, 'darkWood', sx * (bw / 2 - .25), by - .4, bz, g, { shadow: false, lite: true }); br.rotation.x = .75; } }
    const leaf = this.bx(1.0, DH - .1, .1, 'door', -DW / 2 + .05, DH / 2, d / 2 - T - .5, this.G.ext); leaf.rotation.y = Math.PI / 2;
    // plinth + corner posts
    { const pt = .18, ph = .28; // plinth: thin ring outside the walls so the interior floor stays visible
      this.bx(w + pt * 2, ph, pt, 'stoneD', 0, ph / 2, -d / 2 - pt / 2, this.G.ext); this.bx(pt, ph, d, 'stoneD', -w / 2 - pt / 2, ph / 2, 0, this.G.ext); this.bx(pt, ph, d, 'stoneD', w / 2 + pt / 2, ph / 2, 0, this.G.ext);
      for (const sx of [-1, 1]) this.bx((w - DW) / 2 + pt, ph, pt, 'stoneD', sx * (DW / 2 + (w - DW) / 4 - pt / 2 * 0 + 0), ph / 2, d / 2 + pt / 2, this.G.ext); }
    if (o.posts !== false) for (const sx of [-1, 1]) for (const sz of [-1, 1]) this.bx(.34, h, .34, o.postKey || (up === 'timber' || up === 'plaster' ? 'darkWood' : 'stoneD'), sx * w / 2, h / 2, sz * d / 2, this.G.ext);
    // floor
    const fk = o.floor || 'floorPlank'; this.add(boxG(w - T * 2, .06, d - T * 2, TILE[fk] || 3), M(fk), 0, .03, 0, this.G.int, { shadow: false });
    this.insideTest = (lx, lz) => Math.abs(lx) < w / 2 - T * .5 && Math.abs(lz) < d / 2 - T * .5; this.footprint = { w, d };
    this.iw = w / 2 - T; this.id_ = d / 2 - T;
  }
  roofGable(o) { // o: {rh, key, ridge:'z'|'x', over, endKey, y}
    const { w, d, h } = this, ridgeX = o.ridge === 'x', W = ridgeX ? d : w, L = ridgeX ? w : d, rh = o.rh || 3;
    this.gable(W, L, rh, 0, o.y === undefined ? h : o.y, 0, o.key || 'slate', this.G.roof, ridgeX, o.over === undefined ? .6 : o.over, o.endKey || 'timber');
    return rh;
  }
  // ---- furniture kit (interior, local coords, with colliders) ----
  table(x, z, r = .6) { this.cyl(r, r, .08, 'wood', x, .85, z, this.G.int, 14); this.cyl(.08, .1, .8, 'darkWood', x, .42, z, this.G.int, 8); this.ccol(x, z, r + .1); for (const a of [0, 2.1, 4.2]) this.cyl(.18, .18, .4, 'darkWood', x + Math.cos(a) * (r + .5), .2, z + Math.sin(a) * (r + .5), this.G.int, 8); this.cyl(.08, .08, .16, '#4a9a6a', x + .2, .97, z, this.G.int, 6); }
  tableR(x, z, w, d, key = 'wood') { this.bx(w, .1, d, key, x, .9, z, this.G.int); for (const sx of [-1, 1]) for (const sz of [-1, 1]) this.bx(.12, .85, .12, 'darkWood', x + sx * (w / 2 - .12), .43, z + sz * (d / 2 - .12), this.G.int); this.col(x, z, w, d);
    for (const sz of [-1, 1]) this.bx(w * .9, .12, .36, 'darkWood', x, .45, z + sz * (d / 2 + .35), this.G.int); }
  barrel(x, z, h = .85) { this.cyl(.38, .38, h, 'wood', x, h / 2, z, this.G.int, 10); for (const y of [.25, h - .25]) this.cyl(.4, .4, .06, 'iron', x, y, z, this.G.int, 10); this.ccol(x, z, .45); }
  crate(x, z, s = .9, y0 = 0) { this.bx(s, s, s, 'wood', x, y0 + s / 2, z, this.G.int); if (!y0) this.col(x, z, s, s); }
  sack(x, z) { const m = this.add(new THREE.SphereGeometry(.38, 8, 6), M('#b89a62'), x, .3, z, this.G.int); m.scale.set(1, .85, .8); this.ccol(x, z, .4); }
  hay(x, z, w = 1.4, d = 1, h = .9) { this.bx(w, h, d, 'hay', x, h / 2, z, this.G.int); this.col(x, z, w, d); }
  box(w, h, d, x, z, key = 'darkWood', y0 = 0) { this.bx(w, h, d, key, x, y0 + h / 2, z, this.G.int); this.col(x, z, w, d); }
  counter(x, z, w, d = .8, ry = 0) { const a = ry ? [d, w] : [w, d]; this.bx(a[0], 1.0, a[1], 'darkWood', x, .5, z, this.G.int); this.bx(a[0] + .15, .1, a[1] + .15, 'wood', x, 1.05, z, this.G.int); this.col(x, z, a[0], a[1]); }
  shelf(x, z, sw = 2.2, ry = 0, bottles = true) { const a = ry ? [.45, sw] : [sw, .45]; this.bx(a[0], 2.3, a[1], ry ? 'books' : 'books', x, 1.15, z, this.G.int); this.col(x, z, a[0], a[1]);
    if (bottles) for (let i = 0; i < 3; i++) for (let j = 0; j < 4; j++) { const t = (j + .5) / 4 - .5; this.cyl(.07, .07, .22, ['#4a9a6a', '#b5452f', '#2c4fa0', '#d8aa3a'][(i + j) % 4], ry ? x + (ry > 0 ? .25 : -.25) : x + t * (sw - .5), .55 + i * .6, ry ? z + t * (sw - .5) : z + .25, this.G.int, 6, { shadow: false }); } }
  bed(x, z, ry = 0) { const a = ry ? [2.2, 1.2] : [1.2, 2.2]; this.bx(a[0], .45, a[1], 'darkWood', x, .22, z, this.G.int); this.col(x, z, a[0], a[1]); const f = this.bx(ry ? 2.0 : 1.1, .2, ry ? 1.1 : 2.0, '#e8e2d0', x, .55, z, this.G.int); this.bx(ry ? 1.2 : 1.1, .12, ry ? 1.1 : 1.2, '#2c4fa0', x + (ry ? .4 : 0), .68, z + (ry ? 0 : .45), this.G.int); }
  hearth(x, z, ry = 0, wd = 1.9) { // ry: 0 faces +z, PI/2 faces +x, -PI/2 faces -x
    const g = this.G.int; const m = (geo, mat, px, py, pz, o) => { const mm = this.add(geo, mat, 0, py, 0, g, o); mm.position.set(x + px * Math.cos(ry) + pz * Math.sin(ry), py, z - px * Math.sin(ry) + pz * Math.cos(ry)); mm.rotation.y = ry; return mm; };
    m(boxG(wd, 2.6, .8, 3), M('stoneD'), 0, 1.3, 0); m(boxG(1.0, .9, .5, 1), GLOW('ff8a2a', 1.4), 0, .6, .22, { shadow: false }); m(boxG(.5, .3, .3, 1), GLOW('d8501f', 1.2), .1, .3, .26, { shadow: false });
    const [ex, ez] = [Math.abs(Math.sin(ry)) > .5 ? .8 : wd, Math.abs(Math.sin(ry)) > .5 ? wd : .8]; this.col(x, z, ex, ez); }
  anvil(x, z) { this.bx(.7, .55, .45, 'iron', x, .28, z, this.G.int); this.bx(1.1, .22, .4, 'iron', x, .66, z, this.G.int); this.col(x, z, .8, .5); }
  rack(x, z, n = 5, ry = 0) { for (let i = 0; i < n; i++) { const t = (i - (n - 1) / 2) * .55; const m = this.bx(.06, 1.6, .06, '#b6bcc8', ry ? x : x + t, 1.3, ry ? z + t : z, this.G.int, { shadow: false }); m.rotation.z = .04 * (i - 2); }
    this.bx(ry ? .12 : n * .6, .1, ry ? n * .6 : .12, 'darkWood', x, .55, z, this.G.int); this.bx(ry ? .12 : n * .6, .1, ry ? n * .6 : .12, 'darkWood', x, 1.9, z, this.G.int); }
  pillar(x, z, r = .4, h, key = 'stoneL') { h = h || this.h - .2; this.cyl(r, r, h, key, x, h / 2, z, this.G.int, 10); this.cyl(r * 1.4, r * 1.4, .25, key, x, .12, z, this.G.int, 10); this.cyl(r * 1.4, r * 1.4, .25, key, x, h - .1, z, this.G.int, 10); this.ccol(x, z, r + .1); }
  pew(x, z, w = 2.4) { this.bx(w, .45, .5, 'darkWood', x, .3, z, this.G.int); this.bx(w, .7, .12, 'darkWood', x, .75, z - .25, this.G.int); this.col(x, z, w, .5); }
  chest(x, z, s = 1) { this.bx(.9 * s, .55 * s, .6 * s, 'darkWood', x, .28 * s, z, this.G.int); this.bx(.95 * s, .1 * s, .65 * s, 'gold', x, .6 * s, z, this.G.int); this.col(x, z, .9 * s, .6 * s); }
  throne(x, z, ry = 0) { this.bx(2.4, .35, 2.0, 'stoneL', x, .18, z, this.G.int); this.bx(1.2, .5, .9, 'gold', x, .6, z, this.G.int); this.bx(1.2, 2.4, .25, 'gold', x, 1.8, z - .4, this.G.int); this.bx(1.4, .3, .3, 'carpet', x, 1.0, z - .1, this.G.int); this.col(x, z, 2.4, 2.0); }
  crystal(x, z, y = 1.3, c = '4fa0ff', s = .5) { const g = new THREE.OctahedronGeometry(s, 0); const m = this.add(g, GLOW(c, 1.6), x, y, z, this.G.int, { shadow: false }); m.scale.y = 1.6; this.bx(.5, .9, .5, 'stoneD', x, .45, z, this.G.int); this.ccol(x, z, .45); }
  lamp(x, y, z, grp) { this.add(new THREE.SphereGeometry(.14, 6, 5), GLOW('ffc060', 1.6), x, y, z, grp || this.G.int, { shadow: false }); this.bx(.03, .5, .03, 'iron', x, y + .3, z, grp || this.G.int, { shadow: false }); }
  rugAt(x, z, w, d, key = 'rug') { if (key === 'rug') { const R = this._rugs || (this._rugs = []); if (R.some(r => Math.abs(r[0] - x) < (r[2] + w) / 2 - .2 && Math.abs(r[1] - z) < (r[3] + d) / 2 - .2)) return; R.push([x, z, w, d]); } this.add(boxG(w, .02, d, TILE[key] || 3), M(key), x, .08, z, this.G.int, { shadow: false }); }
  // ---- finish ----
  finish() {
    if (this.K !== 1 && !this._rs) { this._rs = 1; if (this.radius) this.radius *= this.K; }
    if (this.footprint && !this.noDoorLane) this.clearZone({ cx: 0, cz: this.d / 2 - 2.6, ang: 0, len: 5.2, w: (this.DW || 2.2) + .8 }, 0, -2.6, 2.6, 0);   // keep the entrance lane free of props
    for (const z of this.stairZones || []) this.clearZone(z.m, z.level, z.du0, z.du1, z.fy);
    for (const c of [...this.G.frame.children]) this.G.roof.add(c);   // frame + roof always toggle together: one merged group
    for (const k of Object.keys(this.G)) {
      const interior = k === 'int' || k.startsWith('up');
      if (interior) this.G[k].children.forEach(o => { if (o.isMesh) o.castShadow = false; });   // interior casters only switched on while the hero is inside (setInside)
      mergeGroup(this.G[k]);
      if (interior) this.G[k].traverse(o => { if (o.isMesh) o.userData.interior = true; });
    }
    this.root.userData.bid = this.id; return this;
  }
  setInside(v) {
    this.inside = v; this.G.roof.visible = !v; this.G.frame.visible = !v;
    if (this.wallRanges) { this.G.walls.visible = v; for (const r of this.wallRanges) { const at = r.mesh.geometry.attributes.position, a = at.array; if (v) a.fill(0, r.start * 3, (r.start + r.count) * 3); else a.set(r.orig, r.start * 3); at.needsUpdate = true; } }   // walls: opaque copy lives in one world mesh per material; the cutaway (see-through) copy is only drawn while inside
    if (this.roofRanges) for (const r of this.roofRanges) { const at = r.mesh.geometry.attributes.position, a = at.array; if (v) a.fill(0, r.start * 3, (r.start + r.count) * 3); else a.set(r.orig, r.start * 3); at.needsUpdate = true; }   // roofs live in one world mesh per material: collapse/restore this building's slice
    for (const k of Object.keys(this.G)) if (k === 'int' || k.startsWith('up')) this.G[k].traverse(o => { if (o.isMesh && o.userData.interior) o.castShadow = v && !!o.material.map; });
    for (const m of this.cut) { m.transparent = v; m.opacity = v ? .2 : 1; m.depthWrite = !v; m.needsUpdate = true; }
    for (const m of this.G.walls.children) m.castShadow = !v;
  }
  update(hx, hz, dt, level = 0) {
    const [lx, lz] = this.toL(hx, hz), dist = Math.hypot(hx - this.cx, hz - this.cz), R = (this.radius || Math.max(this.w || 10, this.d || 10)) + 22;
    const vis = dist < R + 20; if (this.root.visible !== vis) this.root.visible = vis;
    const nearInt = this.inside || dist < (this.radius || 12) + 9; if (this.G.int.visible !== nearInt) this.G.int.visible = nearInt;   // interiors only drawn when close (fewer draw calls)
    const v = this.insideTest ? this.insideTest(lx, lz) : false; if (v !== this.inside) this.setInside(v);
    if (this.lvGroups) for (const l in this.lvGroups) { const g = this.lvGroups[l], sv = v && level >= +l; if (g.visible !== sv) g.visible = sv; }
    if (this.tick && vis) this.tick(dt || 0.016);
    return v;
  }
}

// ===== multi-level support: real walkable upper floors, stairs (ramps), partitions, railings =====
// Hero state: level (0 ground, 1.. upper) + y from surface(). Colliders carry lv (undefined = every level). Upper content lives in per-level groups that are
// only drawn while the hero is inside and on/above that level (dollhouse cutaway).
Builder.prototype.levelGroup = function (l) { this.lvGroups = this.lvGroups || {}; if (!this.lvGroups[l]) { const g = new THREE.Group(); g.visible = false; this.root.add(g); this.G['up' + l] = g; this.lvGroups[l] = g; (this.ctx.multi || (this.ctx.multi = [])).includes(this) || this.ctx.multi.push(this); } return this.lvGroups[l]; };
Builder.prototype.onFloor = function (level, y, fn) { // run fn with furniture helpers redirected to this upper level (coords stay local, y is relative to the floor)
  const sv = [this.curUp, this.lvTag]; this.curUp = level ? { level, y, group: this.levelGroup(level) } : null; this.lvTag = level; try { fn(this); } finally { [this.curUp, this.lvTag] = sv; } };
Builder.prototype.upperFloor = function (level, y, rects, o = {}) { // rects: [[x0,x1,z0,z1]] local; creates slab + registers walkable area
  const g = this.levelGroup(level), key = o.key || 'floorPlank';
  for (const [x0, x1, z0, z1] of rects) this.bx(x1 - x0, .22, z1 - z0, key, (x0 + x1) / 2, y - .11, (z0 + z1) / 2, g);
  this.floors.push({ level, y, rects }); if (o.rails !== false) this.autoRails(level, y, rects, o);
};
Builder.prototype.autoRails = function (level, y, rects, o = {}) {
  const g = this.levelGroup(level), R = this.radius || 0, round = !this.footprint, lim = round ? R - this.T : 0;
  const inside = (x, z, e = .12) => rects.some(r => x > r[0] - e && x < r[1] + e && z > r[2] - e && z < r[3] + e);
  const nearWall = (x, z) => round ? Math.hypot(x, z) > lim - .5 : (Math.abs(x) > this.iw - .35 || Math.abs(z) > this.id_ - .35);
  const nearRamp = (x, z) => this.ramps.some(m => { const [u, v] = this.rampUV(m, x, z); return Math.abs(u) < m.len / 2 + .5 && Math.abs(v) < m.w / 2 + .5; });
  for (const [x0, x1, z0, z1] of rects) for (const [ax, az, bx_, bz, nx, nz] of [[x0, z0, x1, z0, 0, -1], [x0, z1, x1, z1, 0, 1], [x0, z0, x0, z1, -1, 0], [x1, z0, x1, z1, 1, 0]]) {
    const len = Math.hypot(bx_ - ax, bz - az), n = Math.max(1, Math.round(len / .8)); let run = null;
    const flush = (t1) => { if (!run) return; const [sx, sz] = run, ex = ax + (bx_ - ax) * t1, ez = az + (bz - az) * t1, l = Math.hypot(ex - sx, ez - sz); if (l > .2) { this.bx(Math.abs(nx) ? .07 : l, .07, Math.abs(nx) ? l : .07, 'darkWood', (sx + ex) / 2, y + .95, (sz + ez) / 2, g); for (let k = 0; k <= Math.max(1, Math.round(l / 1.1)); k++) { const f = k / Math.max(1, Math.round(l / 1.1)); this.bx(.08, .95, .08, 'darkWood', sx + (ex - sx) * f, y + .48, sz + (ez - sz) * f, g); } } run = null; };
    for (let i = 0; i < n; i++) { const t = (i + .5) / n, px = ax + (bx_ - ax) * t, pz = az + (bz - az) * t, qx = px + nx * .3, qz = pz + nz * .3; const open = !inside(qx, qz) && !nearWall(px, pz) && !nearRamp(px + nx * .2, pz + nz * .2); if (open && !run) run = [ax + (bx_ - ax) * i / n, az + (bz - az) * i / n]; if (!open && run) flush(i / n); }
    flush(1);
  }
};
Builder.prototype.rampUV = function (m, lx, lz) { const dx = lx - m.cx, dz = lz - m.cz, s = Math.sin(m.ang), c = Math.cos(m.ang); return [dx * s + dz * c, dx * c - dz * s]; };
// straight flight: centre (cx,cz), direction angle ang (0 climbs toward +z), length, width, from level l0 (height y0) to level l1 (height y1)

// ---- exterior detail pass for the standard buildings: wall lanterns, door clutter, window shutters, hanging planters (all merged into ext) ----
Builder.prototype.details = function (o = {}) {
  const w = this.w, d = this.d, DW = this.DW || 2.2, g = this.G.ext, T = this.T; let hsh = 0; for (const ch of String(this.id)) hsh = (hsh * 31 + ch.charCodeAt(0)) | 0; const side = hsh & 1 ? 1 : -1, v = (hsh >> 1) & 3;
  for (const sx of [-1, 1]) { const x = sx * (DW / 2 + .85), z = d / 2 + .12; this.bx(.3, .06, .06, 'iron', x - sx * .12, 2.45, z, g, { shadow: false }); this.add(new THREE.SphereGeometry(.13, 6, 5), GLOW('ffc060', 1.7), x, 2.25, z + .08, g, { shadow: false }); this.bx(.05, .3, .05, 'iron', x, 2.35, z, g, { shadow: false }); }
  // clutter beside the door (collides lightly): barrels / crates / sacks
  const cx = side * (DW / 2 + 1.7), cz = d / 2 + .75;
  if (w > 7) { if (v === 0 || v === 3) { this.cyl(.38, .38, .85, 'wood', cx, .43, cz, g, 10); this.cyl(.4, .4, .06, 'iron', cx, .25, cz, g, 10); this.cyl(.4, .4, .06, 'iron', cx, .62, cz, g, 10); this.cyl(.38, .38, .85, 'wood', cx + side * .8, .43, cz + .1, g, 10); this.ccol(cx, cz, .42); this.ccol(cx + side * .8, cz + .1, .42); }
    if (v === 1 || v === 3) { this.bx(.8, .8, .8, 'wood', cx + side * .1, .4, cz + .1, g); this.bx(.6, .6, .6, 'wood', cx + side * .2, 1.1, cz + .1, g); this.col(cx + side * .1, cz + .1, .8, .8); }
    if (v === 2) { this.bx(1.6, .5, .5, 'darkWood', cx, .25, cz, g); this.bx(1.6, .08, .6, 'wood', cx, .52, cz, g); this.col(cx, cz, 1.6, .5); for (let i = 0; i < 4; i++) this.add(new THREE.SphereGeometry(.16, 5, 4), M(['#c8452d', '#e3b341', '#6fae45', '#c8452d'][i]), cx - .6 + i * .4, .72, cz, g, { shadow: false }); } }
  // shutters beside the front windows (lower storey)
  for (const x of frontXs(this)) for (const sx of [-1, 1]) this.bx(.34, 1.05, .06, this.shutKey, x + sx * .78, this.shutY || 1.7, d / 2 + .05, g, { shadow: false });
  this.details2(o);
  // corner stone quoins every ~1.2 m on the front corners
  for (const sx of [-1, 1]) for (let i = 0; i < 3; i++) this.bx(i % 2 ? .46 : .6, .38, .46, 'stoneD', sx * (w / 2 - .02), .55 + i * .9, d / 2 - .02, g, { shadow: false });
};
// second detail layer: storey band + timber studs, door-side bench, potted plants, wall tufts of swaying grass, hanging lantern bracket
Builder.prototype.details2 = function (o) {
  const w = this.w, d = this.d, DW = this.DW || 2.2, g = this.G.ext, hs = o.hs || 0, h = this.h, tim = o.upper === 'timber' || o.upper === 'plaster' || o.upper === 'darkWood'; let hh = 0; for (const ch of String(this.id)) hh = (hh * 17 + ch.charCodeAt(0)) | 0; const rnd = k => { const x = Math.sin(hh * 12.9898 + k * 78.233) * 43758.5453; return x - Math.floor(x); };
  if (hs > 1.2 && hs < h - 1) { const key = tim ? 'darkWood' : 'stoneL', th = tim ? .2 : .16;   // storey string course / jetty beam on all four sides
    this.bx(w + .16, th, .12, key, 0, hs, d / 2 + .05, g, { shadow: false, lite: true }); this.bx(w + .16, th, .12, key, 0, hs, -d / 2 - .05, g, { shadow: false, lite: true });
    for (const sx of [-1, 1]) this.bx(.12, th, d + .16, key, sx * (w / 2 + .05), hs, 0, g, { shadow: false, lite: true });
    if (tim) { for (const sx of [-1, 1]) for (const z of [-d / 2 + .9, 0, d / 2 - .9]) this.bx(.1, h - hs - .1, .1, 'darkWood', sx * (w / 2 + .03), hs + (h - hs) / 2, z, g, { shadow: false, lite: true });
      for (const x of [-w / 2 + .9, w / 2 - .9]) this.bx(.1, h - hs - .1, .1, 'darkWood', x, hs + (h - hs) / 2, d / 2 + .03, g, { shadow: false, lite: true });
      for (const sx of [-1, 1]) { const br = this.bx(.1, 1.5, .1, 'darkWood', sx * (w / 2 + .03), hs + .8, d / 2 - 1.5, g, { shadow: false, lite: true }); br.rotation.x = .75 * sx * 0 + .8; } } }
  const side = rnd(1) < .5 ? -1 : 1, bx = -side * (DW / 2 + 1.7), bz = d / 2 + .7;   // opposite side of the door clutter
  if (w > 7 && rnd(2) < .75) { this.bx(1.5, .1, .5, 'wood', bx, .5, bz, g); for (const sx of [-1, 1]) this.bx(.1, .5, .44, 'darkWood', bx + sx * .6, .25, bz, g, { shadow: false, lite: true }); this.bx(1.5, .5, .08, 'darkWood', bx, .85, bz - .24, g, { shadow: false, lite: true }); }
  for (const sx of [-1, 1]) { const x = sx * (DW / 2 + .75), z = d / 2 + 1.15; this.cyl(.2, .15, .3, '#a8573a', x, .15, z, g, 7, { shadow: false, lite: true }); this.add(new THREE.IcosahedronGeometry(.28, 1), WM(['#4f9a3e', '#3f7a3a', '#6aaa45'][(hh >> 3 & 3) % 3]), x, .5, z, g, { shadow: false, lite: true }); if (rnd(3 + sx) < .6) this.add(new THREE.SphereGeometry(.09, 5, 4), M(['#e8584a', '#f0d040', '#e88adf'][(hh >> 5 & 3) % 3]), x + .1, .72, z + .08, g, { shadow: false, lite: true }); }
  { const gm = WM(rnd(4) < .5 ? '#5f9d44' : '#4e8a3a'), cg = new THREE.ConeGeometry(.05, .5, 3, 1, true);   // grass tufts hugging the walls (wind-swayed, geometry merged into one batch)
    for (let i = 0; i < 18; i++) { const t = rnd(10 + i), e = i % 3, o2 = .35 + rnd(30 + i) * .3; let x, z; if (e === 0) { x = (t - .5) * (w + 2); z = d / 2 + o2 + .5; if (Math.abs(x) < DW / 2 + 1.3) continue; } else if (e === 1) { x = (t < .5 ? -1 : 1) * (w / 2 + o2); z = (rnd(50 + i) - .5) * d; } else { x = (t - .5) * w; z = -d / 2 - o2; }
      for (let k = 0; k < 2; k++) { const m = this.add(cg, gm, x + (k - 1) * .08, .22, z + (k % 2) * .07, g, { shadow: false, lite: true }); m.rotation.z = (k * 2 - 1) * .22; m.scale.y = .7 + rnd(70 + i + k) * .8; } } }
  { const x = side * (DW / 2 + .02), b = this.bx(.07, .07, .5, 'iron', x, 2.75, d / 2 + .28, g, { shadow: false, lite: true }); this.add(new THREE.SphereGeometry(.1, 6, 5), GLOW('ff9a3a', 1.8), x, 2.55, d / 2 + .45, g, { shadow: false, lite: true }); }
};
function frontXs(B) { const n = Math.max(1, Math.round((B.w - 4) / 4)); const out = []; for (let i = 0; i < n; i++) out.push(((i + .5) / n - .5) * (B.w - 3.2)); return out.filter(x => Math.abs(x) > B.DW / 2 + 1.1); }
// remove loose props (meshes + colliders) that sit in a stair's footprint / foot approach / top landing, so a flight can never be blocked by furniture
Builder.prototype.clearZone = function (m, level, du0, du1, floorY) {
  const s = Math.sin(m.ang), c = Math.cos(m.ang), hv = m.w / 2 + .5, inZ = (x, z, mg = 0) => { const dx = x - m.cx, dz = z - m.cz, du = dx * s + dz * c, dv = dx * c - dz * s; return du > du0 - mg && du < du1 + mg && Math.abs(dv) < hv + mg; };
  const grps = level ? [this.levelGroup(level)] : [this.G.int, this.G.ext];
  for (const g of grps) for (const ch of [...g.children]) { if (!ch.isMesh || ch.userData.merged || ch.userData.stairPart) continue; const gp = ch.geometry && ch.geometry.parameters; const hgt = gp && gp.height !== undefined ? gp.height : 1;
    const ry = ch.position.y - (level ? floorY : 0); if (ry < .12 || ry > 2.1 || hgt >= 2.4 || (gp && gp.depth !== undefined && Math.min(gp.width, gp.depth) < .13)) continue; if (inZ(ch.position.x, ch.position.z, gp && gp.width ? Math.min(.9, Math.max(gp.width, gp.depth || 0) * .45) : 0)) { g.remove(ch); ch.geometry.dispose(); } }
  const keepLv = c0 => c0.lv === undefined || c0.lv === level || (Array.isArray(c0.lv) && c0.lv.includes(level));
  this.colliders = this.colliders; for (let i = this.colliders.length - 1; i >= 0; i--) { const q = this.colliders[i]; if (q.b !== this.id || q.stair || q.npcOnly || !keepLv(q)) continue;
    let lx, lz, big; if (q.type === 'box') { [lx, lz] = this.toL((q.minX + q.maxX) / 2, (q.minZ + q.maxZ) / 2); const W = (q.maxX - q.minX) / this.K, D = (q.maxZ - q.minZ) / this.K; big = Math.max(W, D) > 4.2 || Math.min(W, D) < .5 && Math.max(W, D) > 2.4; } else { [lx, lz] = this.toL(q.x, q.z); big = false; }
    if (!big && inZ(lx, lz, q.type === 'circle' ? q.r / this.K * .5 : Math.min(1.1, Math.max(q.maxX - q.minX, q.maxZ - q.minZ) / this.K * .45))) this.colliders.splice(i, 1); }
};
Builder.prototype.stairs = function (o) {
  const { cx, cz, ang = 0, len, w = 1.8, l0 = 0, y0 = 0, l1, y1 } = o;
  (globalThis.__stairLog = globalThis.__stairLog || []).push({ n: this.name, len, w, rise: y1 - y0, deg: Math.round(Math.atan2(y1 - y0, len) * 180 / Math.PI) });
  { const mm = { cx, cz, ang, len, w }; (this.stairZones = this.stairZones || []).push({ m: mm, level: l0, du0: -len / 2 - 1.5, du1: len / 2, fy: y0 }, { m: mm, level: l1, du0: len / 2 - .3, du1: len / 2 + 1.5, fy: y1 }); for (const z of this.stairZones.slice(-2)) this.clearZone(z.m, z.level, z.du0, z.du1, z.fy); } const m = { cx, cz, ang, len, w, l0, y0, l1, y1, flipUp: o.flipUp }; this.ramps.push(m); this.levelGroup(l1);
  this._st = true;
  const n = Math.max(4, Math.ceil((y1 - y0) / .2)), s = Math.sin(ang), c = Math.cos(ang), grp = l0 ? this.levelGroup(l0) : this.G.int, key = o.key || 'wood';
  for (let i = 0; i < n; i++) { const u = -len / 2 + (i + .5) * len / n, top = y0 + (i + 1) * (y1 - y0) / n, hh = top - y0 + (l0 ? 0 : 0); const b = this.bx(w, hh, len / n + .01, key, 0, 0, 0, grp); b.position.set(cx + s * u, y0 + hh / 2, cz + c * u); b.rotation.y = ang; }
  for (const sd of [-1, 1]) { const px = cx + c * sd * (w / 2 + .05), pz = cz - s * sd * (w / 2 + .05); const b = this.bx(.1, .12, len + .3, 'darkWood', px, (y0 + y1) / 2 + .95, pz, grp); b.position.set(px + s * 0, (y0 + y1) / 2 + .95, pz); b.rotation.y = ang; b.rotation.x = 0;
    b.rotateX(-Math.atan2(y1 - y0, len)); // sloped handrail
    const k = Math.max(2, Math.round(len / 1.0)); for (let q = 0; q <= k; q++) { const u = -len / 2 + q * len / k, yy = y0 + (y1 - y0) * (q / k); this.bx(.07, .9, .07, 'darkWood', cx + s * u + c * sd * (w / 2 + .05), yy + .45, cz + c * u - s * sd * (w / 2 + .05), grp); }
    // side colliders (row of circles, all levels): hero cannot leave the flight sideways
    const ln = Math.max(.5, len - .9), nn = Math.ceil(ln / .3); for (let q = 0; q <= nn; q++) { const u = -len / 2 + q * ln / nn, lx = cx + s * u + c * sd * (w / 2 + .22), lz = cz + c * u - s * sd * (w / 2 + .22); const [wx, wz] = this.toW(lx, lz); this.colliders.push({ type: 'circle', x: wx, z: wz, r: .2, b: this.id, lv: u > len / 2 - 2.6 ? [l0] : [l0, l1], stair: 1 }); } }  // top 2.6 m: open to the upper floor (no rail barrier when stepping off/onto the flight sideways)
  // keep ground-level walkers from slipping past the top end underneath the slab
  { const lx = cx + s * (len / 2 + 1.1), lz = cz + c * (len / 2 + 1.1); const nn = Math.ceil(w / .35); for (let q = 0; q <= nn; q++) { const t = -w / 2 + q * w / nn; const [wx, wz] = this.toW(lx + c * t, lz - s * t); this.colliders.push({ type: 'circle', x: wx, z: wz, r: .2, b: this.id, lv: l0, stair: 1 }); } }
  this._st = false; return m;
};
// query: surface height for a local-frame hero position at the given level -> {y, ramp, t} or null if there is no floor there
Builder.prototype.surface = function (wx, wz, level) {
  const [lx, lz] = this.toL(wx, wz);
  for (const m of this.ramps) { if (m.l0 !== level && m.l1 !== level) continue; const [u, v] = this.rampUV(m, lx, lz); if (Math.abs(u) <= m.len / 2 && Math.abs(v) <= m.w / 2) { const t = (u + m.len / 2) / m.len; return { y: (m.y0 + (m.y1 - m.y0) * t) * this.K, ramp: m, t }; } }
  for (const f of this.floors) if (f.level === level && f.disc && Math.hypot(lx, lz) < f.disc - .1 && !f.holes.some(h => lx > h[0] - .02 && lx < h[1] + .02 && lz > h[2] - .02 && lz < h[3] + .02)) return { y: f.y * this.K };
  for (const f of this.floors) if (f.level === level && f.rects) for (const r of f.rects) if (lx > r[0] + .05 && lx < r[1] - .05 && lz > r[2] + .05 && lz < r[3] - .05) return { y: f.y * this.K };
  return null;
};
// axis-aligned partition wall with a door gap (gap = [centre, width] along the wall) at the current upper level
Builder.prototype.partition = function (x, z, len, axis, gap, h = 2.7, key = 'plaster') {
  const T = .16, gaps = !gap ? [] : (Array.isArray(gap[0]) ? gap : [gap]).slice().sort((a, b) => a[0] - b[0]), parts = []; let cur = -len / 2;
  for (const g of gaps) { parts.push([cur, g[0] - g[1] / 2]); cur = g[0] + g[1] / 2; } parts.push([cur, len / 2]);
  for (const [a, b] of parts) { if (b - a < .05) continue; const L = b - a, c = (a + b) / 2; const px = axis === 'x' ? x + c : x, pz = axis === 'x' ? z : z + c;
    this.add(boxG(axis === 'x' ? L : T, h, axis === 'x' ? T : L, TILE[key] || 2), M(key, { transparent: true, opacity: .5, depthWrite: false }), px, h / 2, pz, this.G.int); this.col(px, pz, axis === 'x' ? L : T, axis === 'x' ? T : L); }
  for (const g of gaps) this.bx(axis === 'x' ? g[1] + .2 : T + .06, .25, axis === 'x' ? T + .06 : g[1] + .2, 'darkWood', axis === 'x' ? x + g[0] : x, h - .12, axis === 'x' ? z : z + g[0], this.G.int);
};
// mezzanine / gallery along the back wall with a real stair run
Builder.prototype.gallery = function (o = {}) {
  const y = o.y || 3.1, iw = this.iw, id_ = this.id_, dp = Math.max(o.depth || 2.2, 3.0), rects = [[-iw, iw, -id_, -id_ + dp]]; if (o.side) rects.push(o.side > 0 ? [iw - dp, iw, -id_ + dp, id_ - 2.5] : [-iw, -iw + dp, -id_ + dp, id_ - 2.5]);
  const sx = o.stairX === undefined ? iw - 1.0 : o.stairX, len = Math.min(Math.max(o.run || 3.6, y / Math.tan((o.maxSlope || 26) * Math.PI / 180)), Math.max(3.6, id_ * 2 - dp - 3.0));
  this.stairs({ cx: sx, cz: -id_ + dp + len / 2, ang: Math.PI, len, w: 1.7, l0: 0, y0: 0, l1: 1, y1: y });
  this.upperFloor(1, y, rects, o);
  if (o.rooms) this.onFloor(1, y, o.rooms);
  this.col(0, -id_ + .4, iw * 2, .6);
};

// round hollow shell (towers, colosseum, windmill, lighthouse, observatory): N wall segments with a door gap at local +z
Builder.prototype.roundShell = function (o) { const _lv = this.lvTag; this.lvTag = undefined; try { return this._roundShell(o); } finally { this.lvTag = _lv; } };
Builder.prototype._roundShell = function (o) {
  const { r, h } = o, T = o.T || this.T, N = o.N || Math.max(12, Math.round(r * 2.6)), DW = Math.min(o.DW || 2.2, DOOR_MAXW), DH = Math.min(o.DH || 2.6, DOOR_MAXH), key = o.key || 'stone', seg = 2 * Math.PI * r / N;
  this.radius = r; this.w = this.d = r * 2; this.h = h; this.DW = DW; this.DHr = DH; this.iw = r - T; this.id_ = r - T;
  const doorA = Math.asin(Math.min(.95, (DW / 2 + seg * .35) / r));
  for (let i = 0; i < N; i++) {
    let a = i / N * 2 * Math.PI; if (a > Math.PI) a -= 2 * Math.PI; if (Math.abs(a) < doorA) continue;
    const x = Math.sin(a) * (r - T / 2), z = Math.cos(a) * (r - T / 2), m = this.wallBox(seg * 1.04, h, T, key, x, h / 2, z); m.rotation.y = a;
  }
  { const cr = Math.max(.25, T / 2 + .02), nC = Math.ceil(2 * Math.PI * (r - T / 2) / (cr * 1.4)); for (let i = 0; i < nC; i++) { let a = i / nC * 2 * Math.PI; if (a > Math.PI) a -= 2 * Math.PI; if (Math.abs(a) < doorA) continue; this.ccol(Math.sin(a) * (r - T / 2), Math.cos(a) * (r - T / 2), cr); } }
  const zd = Math.cos(doorA) * (r - T / 2);
  this.wallBox(DW + .6, h - DH, T, key, 0, DH + (h - DH) / 2, r - T / 2 - .05);
  for (const s of [-1, 1]) this.bx(.3, DH, .6, 'stoneD', s * (DW / 2 + .1), DH / 2, r - T / 2 - .05, this.G.frame);
  this.bx(DW + .7, .3, .6, 'stoneD', 0, DH + .1, r - T / 2 - .05, this.G.frame);
  const leaf = this.bx(1.0, DH - .1, .1, 'door', -DW / 2 + .05, DH / 2, r - T - .5, this.G.ext); leaf.rotation.y = Math.PI / 2;
  const fk = o.floor || 'floorStone'; const fg = new THREE.CylinderGeometry(r - T * .5, r - T * .5, .06, Math.max(16, N)); uvScale(fg, (2 * r) / (TILE[fk] || 3), (2 * r) / (TILE[fk] || 3));
  // cylinder cap uv is planar already (0..1); scaled above
  this.add(fg, M(fk), 0, .03, 0, this.G.int, { shadow: false });
  this.bx(DW + .8, .14, 1.1, 'stoneD', 0, .07, r + .3, this.G.ext);
  this.insideTest = (lx, lz) => Math.hypot(lx, lz) < r - T * .6;
};

// ---- quality-pass props ----
Builder.prototype.apron = function (w, d, zOff = 2) { this.bx(w + 3.4, .04, d + 3.4 + zOff, 'cobble', 0, .02, zOff / 2, this.G.ext, { shadow: false }); };
Builder.prototype.bush = function (x, z, s = .7, c = '#3f7a3a') { const m = this.add(new THREE.IcosahedronGeometry(s, 0), WM(c), x, s * .6, z, this.G.ext); m.scale.y = .8; return m; };
Builder.prototype.flowers = function (x, y, z, w, ry = 0) { // window flower box
  const f = this.bx(w, .22, .3, 'darkWood', x, y, z, this.G.ext); f.rotation.y = ry; const g = this.bx(w * .95, .12, .26, '#3f7a3a', x, y + .14, z, this.G.ext, { shadow: false }); g.rotation.y = ry;
  for (let i = 0; i < 5; i++) { const t = (i / 4 - .5) * w * .8; this.add(new THREE.SphereGeometry(.07, 5, 4), M(['#d84a5a', '#f0d040', '#e88adf', '#fff0f0'][i % 4]), x + Math.cos(ry) * t, y + .25, z - Math.sin(ry) * t + Math.cos(ry) * .05, this.G.ext, { shadow: false }); } };
Builder.prototype.lanternPost = function (x, z, h = 2.8) { this.cyl(.07, .1, h, 'iron', x, h / 2, z, this.G.ext, 6); this.bx(.5, .06, .06, 'iron', x + .2, h - .1, z, this.G.ext); this.add(new THREE.SphereGeometry(.17, 6, 5), GLOW('ffc060', 1.7), x + .4, h - .3, z, this.G.ext, { shadow: false }); this.ccol(x, z, .2); };
Builder.prototype.flag = function (x, y, z, s = 1, grp) { this.bx(.06, 1.6 * s, .06, 'iron', x, y + .8 * s, z, grp || this.G.ext, { shadow: false }); const fg = new THREE.PlaneGeometry(1.0 * s, .6 * s, 6, 2); { const uv = fg.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setY(i, 1 - uv.getX(i)); }   // pinned at the pole: sway grows toward the free end
  const f = this.add(fg, fx(M('#1f4a9a', { side: THREE.DoubleSide, name: 'flagcloth' }), 'flag'), x + .5 * s, y + 1.3 * s, z, grp || this.G.ext, { shadow: false }); f.rotation.y = .25; this.add(new THREE.CircleGeometry(.14 * s, 8), M('gold', { side: THREE.DoubleSide }), x + .45 * s, y + 1.3 * s, z + .01, grp || this.G.ext, { shadow: false }); };
Builder.prototype.guard = function (x, z, ry = 0) { const g = this.G.ext; this.cyl(.22, .26, .9, '#2f56a8', x, 1.0, z, g, 6); this.cyl(.1, .1, .45, '#444a58', x - .1, .3, z, g, 5); this.cyl(.1, .1, .45, '#444a58', x + .1, .3, z, g, 5);
  this.add(new THREE.SphereGeometry(.17, 6, 5), M('#e8c09a'), x, 1.65, z, g); this.add(new THREE.ConeGeometry(.2, .26, 6), M('#8a9099'), x, 1.85, z, g); this.bx(.05, 2.3, .05, 'darkWood', x + .35, 1.2, z, g, { shadow: false }); this.add(new THREE.ConeGeometry(.07, .3, 4), M('#b6bcc8'), x + .35, 2.45, z, g, { shadow: false }); this.ccol(x, z, .3);
  if (/^(gatehouse|guildhall|townhall)$/.test(this.id)) { const [wx, wz] = this.toW(x, z); (this.ctx.guardPosts || (this.ctx.guardPosts = [])).push({ x: wx, z: wz, at: this.id }); } };   // town guards: live posts (combat/guards.js)
Builder.prototype.rocks = function (pts, key = 'rock') { for (const [x, z, s, sy] of pts) { const m = this.add(new THREE.DodecahedronGeometry(s, 0), M(key), x, s * .4, z, this.G.ext); m.scale.y = sy || .75; m.rotation.y = x * 3.1 + z; } };
Builder.prototype.crossGable = function (x, W, rh, depth, key = 'slate', endKey = 'timber', y) { // front-facing cross gable over the facade
  const y0 = y === undefined ? this.h : y, d2 = this.d / 2;
  this.gable(W, depth, rh, x, y0, d2 - depth / 2, key, this.G.roof, false, 0, endKey); this.win(x, y0 + rh * .38, d2 + .02, 0, .6, .8, 'glass', this.G.roof, false); };
Builder.prototype.statue = function (x, z, s = 1, grp) { const g = grp || this.G.ext; this.bx(.7 * s, .6 * s, .7 * s, 'stoneL', x, .3 * s, z, g); this.cyl(.18 * s, .28 * s, 1.3 * s, 'stoneL', x, 1.25 * s, z, g, 6); this.add(new THREE.SphereGeometry(.2 * s, 6, 5), M('stoneL'), x, 2.05 * s, z, g); this.bx(.06 * s, 1.2 * s, .06 * s, 'iron', x + .35 * s, 1.5 * s, z, g, { shadow: false }); this.ccol(x, z, .45 * s); };

// ---- full upper storey: slab over rect minus the stair opening, one real flight, auto railings, optional rooms callback ----
function subRect(R, H) { const [x0, x1, z0, z1] = R, [a0, a1, b0, b1] = H, out = []; const add = r => { if (r[1] - r[0] > .06 && r[3] - r[2] > .06) out.push(r); };
  add([x0, Math.max(x0, a0), z0, z1]); add([Math.min(x1, a1), x1, z0, z1]); add([Math.max(x0, a0), Math.min(x1, a1), z0, Math.max(z0, b0)]); add([Math.max(x0, a0), Math.min(x1, a1), Math.min(z1, b1), z1]); return out; }
// o: {y, rect:[x0,x1,z0,z1] (default whole interior), stair:{cx,cz,dir:'-z'|'+z'|'-x'|'+x' (climb direction),len,w}, rooms(B), l0,level}
Builder.prototype.fullUpper = function (o) {
  const level = o.level || 1, l0 = o.l0 === undefined ? level - 1 : o.l0, y0 = o.y0 || 0, y = o.y, round = !this.footprint;
  const rect = o.rect || (round ? [-(this.radius - this.T - .1), this.radius - this.T - .1, -(this.radius - this.T - .1), this.radius - this.T - .1] : [-this.iw, this.iw, -this.id_, this.id_]);
  let rects = [rect], hole = null;
  if (o.stair) { const st0 = o.stair, ang = { '-z': Math.PI, '+z': 0, '-x': -Math.PI / 2, '+x': Math.PI / 2 }[st0.dir || '-z'], w = st0.w || 1.7, ax = Math.abs(Math.sin(ang)) > .5;
    // the foot of every flight needs a free approach: keep >= FOOT m of open floor behind it (shift the flight into the room, shorten only if the room is too small)
    const st = Object.assign({}, st0); const len0 = st0.len || 3.6; let len = round ? len0 : Math.max(len0, (y - y0) / Math.tan((o.maxSlope || 26) * Math.PI / 180));   // gentle: <= ~26 degrees where the room allows
    if (!round) { const k = ax ? 'cx' : 'cz', sg = (ax ? Math.sin(ang) : Math.cos(ang)) > 0 ? 1 : -1, lo = ax ? rect[0] : rect[2], hi = ax ? rect[1] : rect[3], FOOT = o.foot || 1.7;
      const foot0 = st[k] - sg * len0 / 2, nf = sg > 0 ? Math.max(foot0, lo + FOOT) : Math.min(foot0, hi - FOOT), far = sg > 0 ? hi - .5 : lo + .5; const nl = Math.min(len, Math.abs(far - nf)); st[k] = nf + sg * nl / 2; len = Math.max(nl, Math.min(len0, Math.abs(far - nf))); st[k] = nf + sg * len / 2; }
    hole = ax ? [st.cx - len / 2, st.cx + len / 2, st.cz - w / 2, st.cz + w / 2] : [st.cx - w / 2, st.cx + w / 2, st.cz - len / 2, st.cz + len / 2];
    { const sgn = (ax ? Math.sin(ang) : Math.cos(ang)) > 0 ? 1 : -1, ov = o.topOverlap === undefined ? .12 : o.topOverlap, hf = hole.slice();   // top end of the flight: the slab reaches .12 m into the ramp so there is never a gap between ramp and floor
      if (ax) { if (sgn > 0) hf[1] -= ov; else hf[0] += ov; } else { if (sgn > 0) hf[3] -= ov; else hf[2] += ov; } rects = subRect(rect, hf); }
    this.stairs({ cx: st.cx, cz: st.cz, ang, len, w, l0, y0, l1: level, y1: y });
    // low end of the opening: block + rail so an upstairs hero cannot step off the slab into the stairwell
    const s = Math.sin(ang), c = Math.cos(ang), lx = st.cx - s * (len / 2 + .15), lz = st.cz - c * (len / 2 + .15), nn = Math.ceil(w / .35);
    for (let q = 0; q <= nn; q++) { const t = -w / 2 + q * w / nn; const [wx, wz] = this.toW(lx + c * t, lz - s * t); this.colliders.push({ type: 'circle', x: wx, z: wz, r: .2, b: this.id, lv: level, stair: 1 }); }
    this._st = true; const g = this.levelGroup(level), rl = this.bx(ax ? .07 : w, .07, ax ? w : .07, 'darkWood', st.cx - s * (len / 2 + .02), y + .95, st.cz - c * (len / 2 + .02), g);
    for (let q = 0; q <= 3; q++) { const t = -w / 2 + q * w / 3; this.bx(.08, .95, .08, 'darkWood', st.cx - s * (len / 2 + .02) + c * t, y + .48, st.cz - c * (len / 2 + .02) - s * t, g); } this._st = false; }
  if (o.disc) { const g = this.levelGroup(level), r = o.disc, sh = new THREE.Shape(); sh.absarc(0, 0, r, 0, Math.PI * 2, false); if (hole) { const hp = new THREE.Path(); hp.moveTo(hole[0], -hole[2]); hp.lineTo(hole[1], -hole[2]); hp.lineTo(hole[1], -hole[3]); hp.lineTo(hole[0], -hole[3]); hp.closePath(); sh.holes.push(hp); }
    const eg = new THREE.ExtrudeGeometry(sh, { depth: .22, bevelEnabled: false, curveSegments: 20 }); eg.rotateX(-Math.PI / 2); uvScale(eg, 1 / (TILE[o.key || 'floorPlank'] || 3), 1 / (TILE[o.key || 'floorPlank'] || 3));
    const m = this.add(eg, M(o.key || 'floorPlank'), 0, y - .22, 0, g); this.floors.push({ level, y, disc: r, holes: hole ? [hole] : [] }); }
  else this.upperFloor(level, y, rects, Object.assign({}, o, { rails: o.rails }));
  if (o.rooms) this.onFloor(level, y, o.rooms);
  return rects;
};

// Cross-building static merge: bake every building's merged exterior meshes (world space) into per-zone meshes, one per material.
// Fewer draw calls (and fewer shadow-pass calls); frustum culling then works per zone chunk. Cutaway clone materials and animated parts stay put.
export function chunkStatics(builders, scene, cell = 40) {
  const zones = new Map(); let before = 0;
  for (const B of builders) { if (!B || !B.G || !B.G.ext) continue; B.root.updateMatrixWorld(true); const zk = Math.floor(B.cx / cell) + ',' + Math.floor(B.cz / cell); const cut = new Set(B.cut || []);
    for (const m of [...B.G.ext.children]) { if (!m.isMesh || !m.userData.merged || cut.has(m.material)) continue; m.updateMatrixWorld(true); before++;
      const k = zk + '|' + m.material.uuid + (m.castShadow ? 'c' : '') + (m.receiveShadow ? 'r' : ''); let z = zones.get(k); if (!z) zones.set(k, z = { mat: m.material, c: m.castShadow, r: m.receiveShadow, list: [] });
      const g = m.geometry.clone(); g.applyMatrix4(m.matrixWorld); z.list.push(g); B.G.ext.remove(m); m.geometry.dispose(); } }
  for (const z of zones.values()) { let n = 0; for (const g of z.list) n += g.attributes.position.count; const pos = new Float32Array(n * 3), nor = new Float32Array(n * 3), uv = new Float32Array(n * 2); let a = 0, c = 0;
    for (const g of z.list) { pos.set(g.attributes.position.array, a); nor.set(g.attributes.normal.array, a); uv.set(g.attributes.uv.array, c); a += g.attributes.position.count * 3; c += g.attributes.position.count * 2; g.dispose(); }
    const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.BufferAttribute(pos, 3)); geo.setAttribute('normal', new THREE.BufferAttribute(nor, 3)); geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    const m = new THREE.Mesh(geo, z.mat); m.castShadow = z.c; m.receiveShadow = z.r; m.userData.chunk = true; scene.add(m); }
  return { before, after: zones.size };
}

// Roofs: one world mesh per material (all buildings). A building's slice is collapsed to zero-area triangles while the hero is inside it (cutaway).
export function mergeRoofs(builders, scene) {
  const buckets = new Map(); let before = 0;
  for (const B of builders) { if (!B || !B.G || !B.G.roof) continue; B.root.updateMatrixWorld(true); B.roofRanges = [];
    for (const m of [...B.G.roof.children]) { if (!m.isMesh || !m.userData.merged) continue; m.updateMatrixWorld(true); before++;
      const cl = matClass(m.material), zk = zoneKey(B.cx, B.cz) + '|' + cl.key; let b = buckets.get(zk); if (!b) buckets.set(zk, b = { cl, list: [], n: 0, cv: 0 });
      const g = m.geometry.clone(); g.applyMatrix4(m.matrixWorld); const cnt = g.attributes.position.count; b.list.push({ g, B, color: m.material.color }); b.n += cnt; if (m.castShadow) b.cv += cnt; B.G.roof.remove(m); m.geometry.dispose(); } }
  for (const b of buckets.values()) { const pos = new Float32Array(b.n * 3), nor = new Float32Array(b.n * 3), uv = new Float32Array(b.n * 2), col = b.cl.vc ? new Float32Array(b.n * 3) : null; let a = 0, c = 0, vi = 0; const rec = [];
    for (const { g, B, color } of b.list) { const cnt = g.attributes.position.count; pos.set(g.attributes.position.array, a); nor.set(g.attributes.normal.array, a); uv.set(g.attributes.uv.array, c); if (col) colorFill(col, cnt, a, color); rec.push({ B, start: vi, count: cnt, orig: g.attributes.position.array.slice() }); a += cnt * 3; c += cnt * 2; vi += cnt; g.dispose(); }
    const geo = new THREE.BufferGeometry(); const pa = new THREE.BufferAttribute(pos, 3); pa.setUsage(THREE.DynamicDrawUsage); geo.setAttribute('position', pa); geo.setAttribute('normal', new THREE.BufferAttribute(nor, 3)); geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2)); if (col) geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
    const m = new THREE.Mesh(geo, b.cl.mat); m.castShadow = b.cv * 2 > b.n; m.receiveShadow = true; m.userData.keep = true; m.userData.roofWorld = true; scene.add(m);
    for (const r of rec) r.B.roofRanges.push({ mesh: m, start: r.start, count: r.count, orig: r.orig }); }
  return { before, after: buckets.size };
}

// Draw-call budget helpers: flat-colour lit materials share ONE vertex-coloured material; cast/receive flags are unified per material by majority.
export const VCMAT = new THREE.MeshLambertMaterial({ vertexColors: true });
export function matClass(m) { const flat = !m.map && !m.transparent && !m.alphaTest && m.side === THREE.FrontSide && m.isMeshLambertMaterial && m.emissive && m.emissive.getHex() === 0 && !m.userData.noVC; return flat ? { key: 'VC', mat: VCMAT, vc: true } : { key: m.uuid, mat: m, vc: false }; }
export function colorFill(arr, count, off, c) { for (let i = 0; i < count; i++) { arr[off + i * 3] = c.r; arr[off + i * 3 + 1] = c.g; arr[off + i * 3 + 2] = c.b; } }

// Walls: an opaque world-space copy per material (all buildings) replaces each building's own wall meshes, which are only shown while the hero is inside (cutaway).
export function mergeWalls(builders, scene) {
  const buckets = new Map(); let before = 0;
  for (const B of builders) { if (!B || !B.G || !B.G.walls) continue; B.root.updateMatrixWorld(true); B.wallRanges = [];
    for (const m of B.G.walls.children) { if (!m.isMesh || !m.userData.merged) continue; m.updateMatrixWorld(true); before++; const mt = m.material;
      const sig = mt.map ? 'M' + mt.map.uuid + mt.color.getHex() + mt.side + mt.opacity : 'C' + mt.color.getHex() + mt.side + mt.emissive.getHex(); let b = buckets.get(zoneKey(B.cx, B.cz) + sig);
      if (!b) { const cl = matClass(mt); buckets.set(zoneKey(B.cx, B.cz) + sig, b = { cl: cl.vc ? cl : { key: sig, mat: Object.assign(mt.clone(), { transparent: false, opacity: 1, depthWrite: true }), vc: false }, list: [], n: 0, cv: 0 }); }
      const g = m.geometry.clone(); g.applyMatrix4(m.matrixWorld); const cnt = g.attributes.position.count; b.list.push({ g, B, color: mt.color }); b.n += cnt; if (m.userData.castWas !== false) b.cv += cnt; } }
  for (const b of buckets.values()) { const pos = new Float32Array(b.n * 3), nor = new Float32Array(b.n * 3), uv = new Float32Array(b.n * 2), col = b.cl.vc ? new Float32Array(b.n * 3) : null; let a = 0, c = 0, vi = 0; const rec = [];
    for (const { g, B, color } of b.list) { const cnt = g.attributes.position.count; pos.set(g.attributes.position.array, a); nor.set(g.attributes.normal.array, a); uv.set(g.attributes.uv.array, c); if (col) colorFill(col, cnt, a, color); rec.push({ B, start: vi, count: cnt, orig: g.attributes.position.array.slice() }); a += cnt * 3; c += cnt * 2; vi += cnt; g.dispose(); }
    const geo = new THREE.BufferGeometry(); const pa = new THREE.BufferAttribute(pos, 3); pa.setUsage(THREE.DynamicDrawUsage); geo.setAttribute('position', pa); geo.setAttribute('normal', new THREE.BufferAttribute(nor, 3)); geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2)); if (col) geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
    const m = new THREE.Mesh(geo, b.cl.mat); m.castShadow = true; m.receiveShadow = true; m.userData.keep = true; m.userData.wallWorld = true; scene.add(m);
    for (const r of rec) r.B.wallRanges.push({ mesh: m, start: r.start, count: r.count, orig: r.orig }); }
  for (const B of builders) if (B && B.wallRanges) B.G.walls.visible = false;
  return { before, after: buckets.size };
}

export const ZONE = 1e5;   // one world zone: more zones cost more draw calls in the wide camera than they save by culling
export const zoneKey = (x, z) => Math.floor((x + 200) / ZONE) + ',' + Math.floor((z + 200) / ZONE);

// ---- room dressing: fill empty floor / walls of a ground-floor room so big (scaled) rooms read as lived-in, never blocking existing props
Builder.prototype.spotFree = function (lx, lz, r) {
  const [wx, wz] = this.toW(lx, lz), rr = r * this.K;
  for (const c of this.colliders) { if (c.b !== this.id) continue; if (c.lv !== undefined && c.lv !== 0 && !(Array.isArray(c.lv) && c.lv.includes(0))) continue;
    if (c.type === 'box') { if (wx > c.minX - rr && wx < c.maxX + rr && wz > c.minZ - rr && wz < c.maxZ + rr) return false; } else if (Math.hypot(wx - c.x, wz - c.z) < c.r + rr) return false; }
  return true;
};
Builder.prototype.dress = function (theme = 'tavern', o = {}) {
  const iw = this.iw, id_ = this.id_, hs = Math.min(this.hs || 3, 4.7), F = (x, z, r) => Math.abs(x) < iw - .3 && Math.abs(z) < id_ - .3 && this.spotFree(x, z, r);
  const lane = (x, z) => Math.abs(x) < (this.DW || 2.2) / 2 + 1.2 && z > id_ - 4.2;   // keep the door lane clear
  const wallL = [[-iw + .45, Math.PI / 2], [iw - .45, -Math.PI / 2]];
  if (theme === 'tavern') {
    for (const [wx] of wallL) for (let z = -id_ + 2.4; z < id_ - 3.2; z += 1.9) { if (!F(wx, z, .6) || lane(wx, z)) continue; (Math.round(z * 3) % 2 ? this.barrel(wx, z) : this.crate(wx, z, .8)); }
    for (let x = -iw + 2.6; x < iw - 2; x += 3.6) if (F(x, -id_ + .4, 1.3)) this.shelf(x, -id_ + .35, 2.8);
    for (let x = -iw + 3; x < iw - 2.4; x += 4.4) for (let z = -id_ + 4.2; z < id_ - 3.2; z += 3.8) { if (!F(x, z, 1.7) || lane(x, z)) continue; this.table(x, z, .75); this.rugAt(x, z, 2.8, 2.8); this.lamp(x, hs - .5, z); }
    for (let z = -id_ + 3; z < id_ - 3.4; z += 3.6) for (const [wx, ry] of wallL) if (!lane(wx, z)) this.banner(wx + (wx < 0 ? .1 : -.1), 2.0, z, ry, .9, 1.8);
  } else if (theme === 'hall') {
    const len = Math.max(4, id_ * 1.2);
    for (const sx of [-1, 1]) { const x = sx * Math.min(iw - 3, 5.2); if (F(x, -id_ * .1, 1.6) && this.spotFree(x, -id_ * .1 - len / 2, 1) !== false) { this.tableR(x, -id_ * .15, 1.2, len, 'darkWood'); this.col(x, -id_ * .15, 1.2, len); for (let z = -id_ * .15 - len / 2 + .8; z < -id_ * .15 + len / 2; z += 1.4) { this.bx(.4, .45, .4, 'wood', x - sx * 1.0, .23, z, this.G.int); this.bx(.4, .45, .4, 'wood', x + sx * 1.0, .23, z, this.G.int); } } }
    for (const [wx, ry] of wallL) for (let z = -id_ + 2.4; z < id_ - 3.2; z += 3.0) { if (lane(wx, z)) continue; this.banner(wx + (wx < 0 ? .1 : -.1), 3.2, z, ry, 1.1, 2.6); if (F(wx, z + 1.5, .8)) this.rack(wx + (wx < 0 ? .3 : -.3), z + 1.5, 4, 1); }
    for (let x = -iw + 2; x < iw - 1.5; x += 3.3) if (F(x, -id_ + .6, 1)) this.chest(x, -id_ + .6, 1.1);
    for (const sx of [-1, 1]) if (F(sx * (iw - 1.2), id_ - 3.6, .8)) { this.cyl(.35, .45, 1.1, 'iron', sx * (iw - 1.2), .55, id_ - 3.6, this.G.int, 8); this.ccol(sx * (iw - 1.2), id_ - 3.6, .5); this.add(new THREE.SphereGeometry(.28, 8, 6), GLOW('ff9a3c', 1.6), sx * (iw - 1.2), 1.3, id_ - 3.6, this.G.int, { shadow: false }); }
    for (let z = -id_ + 2; z < id_ - 3.5; z += 4) this.lamp(0, hs - .6, z);
  }
};

// ---- pass 2 interior props (per building kind): stools / chairs, bottles, forge tools, ovens, stalls, cauldrons; every spot is checked free (no new stuck spots) ----
Builder.prototype.props2 = function (kind) {
  const iw = this.iw, id_ = this.id_, G = this.G.int, DWh = (this.DW || 2.2) / 2 + 1.2, hs = Math.min(this.hs || 3, 4.7);
  const lane = (x, z) => Math.abs(x) < DWh && z > id_ - 4.4, F = (x, z, r) => Math.abs(x) < iw - .3 && Math.abs(z) < id_ - .3 && !lane(x, z) && this.spotFree(x, z, r);
  const stool = (x, z, h = .55) => { if (!F(x, z, .4)) return false; this.cyl(.2, .17, h, 'wood', x, h / 2, z, G, 8); this.cyl(.24, .24, .07, 'darkWood', x, h, z, G, 8); this.ccol(x, z, .26); return true; };
  const chair = (x, z, ry) => { if (!F(x, z, .4)) return; this.bx(.42, .07, .42, 'wood', x, .45, z, G, { lite: true }); for (const a of [-1, 1]) for (const b of [-1, 1]) this.bx(.05, .45, .05, 'darkWood', x + a * .17, .22, z + b * .17, G, { lite: true }); const bk = this.bx(.42, .5, .06, 'darkWood', x + Math.sin(ry) * .2, .75, z + Math.cos(ry) * .2, G, { lite: true }); bk.rotation.y = ry; };
  const bottles = (x, y, z, n, dx = .2, dz = 0) => { for (let i = 0; i < n; i++) this.cyl(.05, .06, .26, ['#2f6a3a', '#6a2a2a', '#b88a2a', '#2f4a8a'][i % 4], x + dx * i, y + .13, z + dz * i, G, 5, { shadow: false }); };
  const cauldron = (x, z, glow) => { if (!F(x, z, .8)) return; this.add(new THREE.SphereGeometry(.5, 8, 6, 0, 6.3, 0, 1.7), M('iron', { side: THREE.DoubleSide }), x, .62, z, G); for (const a of [0, 2.1, 4.2]) this.cyl(.05, .05, .25, 'iron', x + Math.cos(a) * .35, .12, z + Math.sin(a) * .35, G, 5, { shadow: false }); this.add(new THREE.CircleGeometry(.42, 8), GLOW(glow, 1.2), x, .85, z, G, { shadow: false }).rotation.x = -Math.PI / 2; this.ccol(x, z, .55); };
  const hang = (x, z, n) => { this.bx(1.6, .06, .06, 'iron', x, hs - .4, z, G, { shadow: false, lite: true }); for (let i = 0; i < n; i++) { this.cyl(.015, .015, .4, 'iron', x - .6 + i * .4, hs - .6, z, G, 3, { shadow: false }); this.cyl(.14, .1, .16, 'iron', x - .6 + i * .4, hs - .86, z, G, 6, { shadow: false }); } };
  if (kind === 'inn') { for (let i = 0; i < 4; i++) stool(.5 + i * .85, -id_ + 2.2); bottles(1.0, 1.0, -id_ + 1.1, 6, .5); hang(2.2, -id_ + 1.1, 4);
    for (const [x, z] of [[-1.8, .4], [-.2, 2.2], [-3.4, 2.4]]) for (const [dx, dz, ry] of [[.95, 0, -Math.PI / 2], [-.95, 0, Math.PI / 2], [0, .95, Math.PI], [0, -.95, 0]]) chair(x + dx, z + dz, ry);
    this.cyl(.28, .28, .5, 'wood', iw - 1.4, .25, -id_ + 1.2, G, 8); this.ccol(iw - 1.4, -id_ + 1.2, .4); cauldron(-iw + 1.5, -id_ + 1.4, 'ff8a2a'); }
  if (kind === 'smithy') { const x = iw - 1.2; this.bx(1.2, .5, .9, 'iron', x - 1.6, .25, -id_ + 1.4, G); this.add(boxG(1.0, .3, .7, 1), M('#4a90c0', { name: 'quench' }), x - 1.6, .52, -id_ + 1.4, G, { shadow: false }); this.ccol(x - 1.6, -id_ + 1.4, .7);
    const bw = this.bx(.5, .3, .7, 'darkWood', x - .1, .9, -id_ + 2.0, G, { lite: true }); this.cone(.18, .6, 'darkWood', x - .1, .98, -id_ + 2.5, G, 6).rotation.x = 1.5;
    for (let i = 0; i < 5; i++) { this.bx(.08, .5, .08, 'darkWood', -1.0 + i * .5, 2.0, -id_ + .12, G, { shadow: false, lite: true }); this.bx(.3, .12, .12, 'iron', -1.0 + i * .5, 2.28, -id_ + .12, G, { shadow: false, lite: true }); }
    if (F(-iw + 1.2, -id_ + 1.2, .8)) { this.cyl(.4, .4, .12, 'stone', -iw + 1.2, .9, -id_ + 1.2, G, 10); this.bx(.5, .9, .3, 'darkWood', -iw + 1.2, .45, -id_ + 1.2, G, { lite: true }); this.ccol(-iw + 1.2, -id_ + 1.2, .5); }
    for (let i = 0; i < 6; i++) this.add(new THREE.DodecahedronGeometry(.16, 0), M('#1c1c20'), iw - .5 + (i % 3) * .12 - .2, .14 + (i > 2 ? .2 : 0), -.6 + (i % 3) * .2, G, { shadow: false }); }
  if (kind === 'bakery') { bottles(-iw + .5, 1.0, -.8, 0); hang(0, -id_ + .7, 3); for (const [x, z] of [[-.6, -.4], [.8, -.4]]) stool(x, z + 1.2, .5);
    for (let i = 0; i < 5; i++) this.add(new THREE.SphereGeometry(.17, 6, 5), M('#d8a85a'), -1.2 + i * .45, 1.0, -.4 + (i % 2) * .3, G, { shadow: false }).scale.y = .6;
    this.bx(.08, 1.6, .08, 'darkWood', iw - 2.6, .8, -id_ + 1.4, G, { lite: true }); this.bx(.7, .06, .12, 'wood', iw - 2.6, 1.6, -id_ + 1.4, G, { lite: true });
    for (let i = 0; i < 3; i++) this.cyl(.34, .3, .5, '#b89a62', iw - .7, .25 + i * .0, id_ - 1.4 - i * .5, G, 7); }
  if (kind === 'market') { for (const sx of [-1, 1]) { const x = sx * (iw - 2.6), z = id_ - 2.4; if (!F(x, z, 1.2)) continue; for (const a of [-1, 1]) for (const b of [-1, 1]) this.bx(.08, 2.3, .08, 'darkWood', x + a * .9, 1.15, z + b * .55, G, { lite: true });
      const aw = this.bx(2.1, .06, 1.4, 'awning', x, 2.35, z, G, { shadow: false }); aw.rotation.x = .12; this.bx(1.8, .7, .9, 'wood', x, .35, z, G); this.col(x, z, 1.8, .9);
      for (let i = 0; i < 6; i++) this.add(new THREE.SphereGeometry(.12, 6, 5), M(['#c8452d', '#e3b341', '#6fae45'][i % 3]), x - .65 + i * .26, .8, z + (i % 2) * .15 - .08, G, { shadow: false }); }
    for (let i = 0; i < 6; i++) { this.bx(.04, .6, .04, 'iron', -2.5 + i * 1.0, hs - .7, -.5, G, { shadow: false, lite: true }); this.add(new THREE.SphereGeometry(.14, 5, 4), M('#d8aa3a'), -2.5 + i * 1.0, hs - 1.1, -.5, G, { shadow: false }); } }
  if (kind === 'apothecary') { cauldron(iw - 1.2, id_ - 1.6, '4fe08a'); bottles(-1.8, 1.0, -id_ + .9, 8, .45); for (let i = 0; i < 6; i++) this.cyl(.015, .015, .5 + (i % 2) * .2, '#5a8a3a', -2.4 + i * .95, hs - .5, .5, G, 3, { shadow: false }); stool(-iw + 1.6, id_ - 2.0, .6); if (F(-.8, .6, .4)) { this.cyl(.12, .09, .1, 'stoneL', -.8, 1.05, .6, G, 8, { shadow: false }); } }
  if (kind === 'house') { for (const [dx, dz, ry] of [[.8, .5, -Math.PI / 2], [-2.0, .5, Math.PI / 2]]) chair(dx - .6 + (dx < 0 ? .6 : 0), dz, ry); hang(0, -id_ + 1.2, 3); if (F(iw - 1.0, -id_ + 1.0, .6)) { this.cyl(.3, .3, .5, 'wood', iw - 1.0, .25, -id_ + 1.0, G, 8); this.ccol(iw - 1.0, -id_ + 1.0, .4); } }
  const ceil = Math.min(this.h || 6, ...this.floors.filter(f => f.level === 1).map(f => f.y)), chand = (x, y, z, r = .9) => { y = Math.min(y, ceil - .9); this.add(new THREE.TorusGeometry(r, .05, 4, 12), M('iron'), x, y, z, G, { shadow: false }).rotation.x = Math.PI / 2; this.cyl(.02, .02, Math.max(.3, ceil - y - .1), 'iron', x, y + Math.max(.3, ceil - y - .1) / 2, z, G, 3, { shadow: false });
    for (let i = 0; i < 6; i++) { const a = i / 6 * 6.283, cx = x + Math.cos(a) * r, cz = z + Math.sin(a) * r; this.cyl(.04, .04, .16, '#e8dcc0', cx, y + .1, cz, G, 4, { shadow: false }); this.add(new THREE.ConeGeometry(.045, .12, 4), GLOW('ffb040', 2.0), cx, y + .24, cz, G, { shadow: false }); } };
  const notes = (x, y, z, w, hgt) => { for (let i = 0; i < 9; i++) { const nx = x - w / 2 + .3 + (i % 3) * (w - .6) / 2 + Math.sin(i * 7.1) * .12, ny = y - hgt / 2 + .35 + Math.floor(i / 3) * (hgt - .7) / 2; this.bx(.42, .5, .02, i % 4 ? 'parchment' : '#d8c890', nx, ny, z, G, { shadow: false, lite: true }); this.bx(.05, .05, .03, '#8a2a2a', nx, ny + .2, z + .015, G, { shadow: false, lite: true }); } };
  if (kind === 'guildhall') { chand(0, 4.9, -.6, 1.1); chand(0, 4.9, -id_ + 2.6, .8); notes(-3.8, 2.0, -id_ + .43, 3.2, 2.2); notes(3.8, 2.0, -id_ + .43, 3.2, 2.2);
    for (const z of [-1.5, 1.5]) for (const sx of [-1, 1]) this.banner(sx * 1.6, 4.0, z, Math.PI / 2, .9, 2.0, G); }
  if (kind === 'hall') { const n = Math.max(1, Math.round(id_ / 4)); for (let i = 0; i < n; i++) chand(0, Math.min((this.h || 6) - 1.6, 5.2), -id_ + (i + .5) * (2 * id_) / n - .5, 1.0); }
  if (kind === 'inn') chand(-1.8, 2.45, 1.4, .7);
  if (kind === 'thieves') { for (let i = 0; i < 3; i++) stool(-2.6 + i * .9, 1.8, .5); bottles(-.8, 1.0, .6, 6, .45); hang(0, -.3, 3); }
};

// gothic pinnacles (cards: town hall, temple, library, mage academy): square shaft + 4-sided spire + gold knob, on the eave line; roof group (hidden with the roof)
Builder.prototype.pinnacle = function (x, y, z, s = 1) { const g = this.G.roof; this.bx(.36 * s, 1.0 * s, .36 * s, 'stoneL', x, y + .5 * s, z, g, { shadow: false }); this.cone(.3 * s, 1.5 * s, 'slate', x, y + 1.0 * s, z, g, 4, { shadow: false }); this.add(new THREE.SphereGeometry(.09 * s, 5, 4), M('gold'), x, y + 2.55 * s, z, g, { shadow: false }); };
Builder.prototype.cardSpires = function (o = {}) { const w = this.w, d = this.d, h = o.h || this.h, s = o.s || 1;
  for (const sx of [-1, 1]) { this.pinnacle(sx * w / 4, h, d / 2 + .05, s); this.pinnacle(sx * (w / 2 - .2), h, -d / 2 + .2, s); if (o.mid !== false) this.pinnacle(sx * (w / 2 + .05), h, 0, s * .85); } };

// birds: n small V-shapes circling over the village, all motion in the vertex shader (static buffers, one draw call, no per-frame JS)
export function birdFlock(n = 36, R = 100) {
  const pos = [], ctr = [], ph = []; let sd = 7; const r = () => (sd = (sd * 16807) % 2147483647) / 2147483647;
  for (let i = 0; i < n; i++) { const g = i % 4, cx = (g % 2 ? 1 : -1) * R * (.25 + r() * .35), cz = (g > 1 ? 1 : -1) * R * (.25 + r() * .35), rad = 8 + r() * 14, y = 22 + r() * 14, p0 = r() * 6.283, sp = .25 + r() * .2;
    for (const v of [[-1, 0], [0, 0], [0, .35], [1, 0], [0, 0], [0, .35]]) { pos.push(v[0], 0, v[1]); ctr.push(cx, y, cz); ph.push(p0, rad, sp); } }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('ctr', new THREE.Float32BufferAttribute(ctr, 3)); g.setAttribute('ph', new THREE.Float32BufferAttribute(ph, 3)); g.boundingSphere = new THREE.Sphere(new THREE.Vector3(0, 30, 0), 1e4);
  const m = new THREE.ShaderMaterial({ side: THREE.DoubleSide, uniforms: { uTime: FX.uTime },
    vertexShader: 'attribute vec3 ctr; attribute vec3 ph; uniform float uTime; void main(){ float a = ph.x + uTime * ph.z; vec3 c = ctr + vec3(cos(a) * ph.y, sin(uTime * .7 + ph.x) * 1.5, sin(a) * ph.y); vec3 fw = normalize(vec3(-sin(a), 0.0, cos(a))); vec3 rt = vec3(fw.z, 0.0, -fw.x);'
      + ' float flap = sin(uTime * 9.0 + ph.x * 5.0) * 0.45; vec3 p = c + rt * position.x * 0.55 + fw * position.z * 0.9 + vec3(0.0, abs(position.x) * flap, 0.0); gl_Position = projectionMatrix * viewMatrix * vec4(p, 1.0); }',
    fragmentShader: 'void main(){ gl_FragColor = vec4(0.12, 0.12, 0.14, 1.0); }' });
  const mesh = new THREE.Mesh(g, m); mesh.frustumCulled = false; mesh.userData.keep = true; mesh.name = 'birds'; return mesh;
}

// entrance dressing for the non-standard buildings (door at local +z): wall sconces with flickering flames, lantern posts, potted plants, doormat; spots checked free
Builder.prototype.entry = function (o = {}) { const DW = this.DW || 2.2, round = !this.footprint, r = this.d / 2, g = this.G.ext;
  const wallZ = x => round ? Math.sqrt(Math.max(0, r * r - x * x)) : r;
  for (const sx of [-1, 1]) { const x = sx * (DW / 2 + .55), z = wallZ(x) + .12, y = o.sconceY || 2.5; this.bx(.12, .35, .12, 'iron', x, y, z, g, { shadow: false, lite: true }); this.bx(.06, .06, .3, 'iron', x, y + .15, z + .12, g, { shadow: false, lite: true }); this.add(new THREE.ConeGeometry(.09, .3, 5), GLOW('ff9a3a', 2.0), x, y + .32, z + .25, g, { shadow: false });
    if (o.posts !== false) { const px = sx * (DW / 2 + 1.7), pz = wallZ(px) + 1.4; if (this.spotFree(px, pz, .5)) this.lanternPost(px, pz, 2.6); }
    const qx = sx * (DW / 2 + 1.0), qz = wallZ(qx) + .55; this.cyl(.22, .16, .34, '#a8573a', qx, .17, qz, g, 7, { shadow: false }); this.add(new THREE.IcosahedronGeometry(.3, 0), WM('#4f9a3e'), qx, .52, qz, g, { shadow: false }); }
  if (round && this.DHr) { const DH = this.DHr, z = wallZ(DW / 2) + .1; for (const sx of [-1, 1]) this.bx(.3, DH + .1, .3, 'stoneD', sx * (DW / 2 + .15), (DH + .1) / 2, z, this.G.frame, { lite: true }); this.bx(DW + .9, .34, .34, 'stoneD', 0, DH + .2, z, this.G.frame, { lite: true }); this.bx(.34, .42, .4, 'stoneL', 0, DH + .3, z + .04, this.G.frame, { lite: true }); }
  this.bx(DW * .8, .03, .9, 'rug', 0, .03, wallZ(0) + .7, g, { shadow: false, lite: true }); };

// butterflies fluttering over garden spots (pass 3 life): pts [[x,z]], 3 per spot, one draw call, motion in the vertex shader
export function butterflies(pts) {
  const pos = [], ctr = [], ph = [], col = []; let sd = 11; const r = () => (sd = (sd * 16807) % 2147483647) / 2147483647; const pal = [[1, .85, .2], [.95, .5, .8], [.6, .8, 1], [1, 1, 1]];
  for (const [x, z] of pts) for (let k = 0; k < 3; k++) { const p0 = r() * 6.283, c = pal[(r() * 4) | 0];
    for (const v of [[-1, 0], [0, -.2], [0, .25], [1, 0], [0, .25], [0, -.2]]) { pos.push(v[0], 0, v[1]); ctr.push(x + (r() - .5) * 2, .7 + r() * .8, z + (r() - .5) * 2); ph.push(p0, .6 + r() * .9, .5 + r() * .5); col.push(...c); } }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('ctr', new THREE.Float32BufferAttribute(ctr, 3)); g.setAttribute('ph', new THREE.Float32BufferAttribute(ph, 3)); g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  const m = new THREE.ShaderMaterial({ side: THREE.DoubleSide, uniforms: { uTime: FX.uTime },
    vertexShader: 'attribute vec3 ctr; attribute vec3 ph; attribute vec3 color; varying vec3 vC; uniform float uTime; void main(){ vC = color; float t = uTime * ph.z + ph.x; vec3 c = ctr + vec3(sin(t) * ph.y + sin(t * 2.3) * .3, sin(t * 3.1) * .25, cos(t * .8) * ph.y);'
      + ' float fl = abs(sin(uTime * 14.0 + ph.x * 3.0)); vec3 p = c + vec3(position.x * .13 * (0.25 + fl), abs(position.x) * .1 * fl, position.z * .13); gl_Position = projectionMatrix * viewMatrix * vec4(p, 1.0); }',
    fragmentShader: 'varying vec3 vC; void main(){ gl_FragColor = vec4(vC, 1.0); }' });
  g.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 1e4); const mesh = new THREE.Mesh(g, m); mesh.frustumCulled = false; mesh.userData.keep = true; mesh.name = 'butterflies'; return mesh;
}
// clothesline with waving laundry (flag shader), beside a house; poles collide only when the spot is free
Builder.prototype.laundry = function () { const g = this.G.ext, x = (this.w / 2 + 1.4), z0 = -this.d / 4, z1 = this.d / 4;
  if (!this.spotFree(x, z0, .4) || !this.spotFree(x, z1, .4)) return;
  for (const z of [z0, z1]) { this.cyl(.05, .06, 2.0, 'darkWood', x, 1.0, z, g, 5, { shadow: false }); this.ccol(x, z, .12); }
  this.bx(.02, .02, z1 - z0, 'iron', x, 1.92, (z0 + z1) / 2, g, { shadow: false, lite: true });
  const cols = ['#e8e2d0', '#3f5fa8']; const n = Math.max(2, Math.floor((z1 - z0) / .8));
  for (let i = 0; i < n; i++) { const z = z0 + (i + .5) * (z1 - z0) / n, p = this.add(new THREE.PlaneGeometry(.55, .7, 2, 4), fx(M(cols[i % 2], { side: THREE.DoubleSide, name: 'laundry' }), 'flag'), x, 1.55, z, g, { shadow: false }); p.rotation.y = Math.PI / 2; } };
