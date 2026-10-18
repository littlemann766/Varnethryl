// Varnethryl 3D buildings: builder kit. One Builder per building: hollow walls with a real door gap, world-scaled UVs, per-building
// cutaway materials (walls go see-through and the roof hides when the hero is inside), furniture kit, and a merge pass that collapses every
// group into one mesh per material (phone-friendly). Local space: +z is the facade/door, y=0 is the ground.
import * as THREE from 'three';
import { tex, bannerTexture, signTexture } from './bldtex.js';

export const TILE = { stone: 3, stoneD: 3, stoneL: 3.2, rock: 4, plaster: 3, timber: 2.4, darkWood: 2, wood: 1.6, slate: 2.2, slateG: 2.2, hay: 2, floorPlank: 3, floorStone: 3, floorTile: 2, sand: 4, cobble: 3, pave: 3, carpet: 2, rug: 3, sigil: 6, marbleInlay: 3, awning: 1.6, glass: 1, stained: 1, door: 1, iron: 1, water: 4, parchment: 1, gold: 1, books: 1.2, grass: 4 };
const matCache = {};
export function M(key, extra) { // shared lit material by texture key (or flat colour with '#rrggbb')
  const id = key + (extra ? JSON.stringify(extra) : ''); if (matCache[id]) return matCache[id];
  const o = Object.assign({}, extra); if (key[0] === '#') o.color = new THREE.Color(key); else o.map = tex(key);
  return matCache[id] = new THREE.MeshLambertMaterial(o);
}
export const GLOW = (c, k = 1) => M('#' + c, { emissive: new THREE.Color('#' + c), emissiveIntensity: k });
export function uvScale(g, su, sv) { const uv = g.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) * su, uv.getY(i) * sv); return g; }
export function boxG(w, h, d, tile = 2) {
  const g = new THREE.BoxGeometry(w, h, d), uv = g.attributes.uv, dims = [[d, h], [d, h], [w, d], [w, d], [w, h], [w, h]];
  for (let f = 0; f < 6; f++) for (let v = 0; v < 4; v++) { const i = f * 4 + v; uv.setXY(i, uv.getX(i) * dims[f][0] / tile, uv.getY(i) * dims[f][1] / tile); }
  return g;
}
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

export class Builder {
  constructor(ctx, spec) {
    this.ctx = ctx; this.spec = spec; const { scene, colliders } = ctx; this.colliders = colliders;
    this.id = spec.id; this.cx = spec.cx; this.cz = spec.cz; this.rot = spec.rot || 0; this.cs = Math.cos(this.rot); this.sn = Math.sin(this.rot);
    this.root = new THREE.Group(); this.root.position.set(this.cx, 0, this.cz); this.root.rotation.y = this.rot; scene.add(this.root);
    this.G = {}; this.lvTag = 0; this.curUp = null; this.floors = []; this.ramps = []; for (const k of ['ext', 'walls', 'roof', 'frame', 'int']) { this.G[k] = new THREE.Group(); this.root.add(this.G[k]); }
    this.cut = []; this.cutCache = {}; this.dyn = []; this.T = 0.45; this.inside = false; this.colInfo = []; this.insideTest = null; this.footprint = null;
  }
  // ---- placement helpers ----
  toW(lx, lz) { return [this.cx + lx * this.cs + lz * this.sn, this.cz - lx * this.sn + lz * this.cs]; }
  toL(wx, wz) { const dx = wx - this.cx, dz = wz - this.cz; return [dx * this.cs - dz * this.sn, dx * this.sn + dz * this.cs]; }
  col(lx, lz, bw, bd) { // axis-aligned in local; world box when rot is a quarter turn, else a row of circles
    const q = Math.round(this.rot / (Math.PI / 2)); const [wx, wz] = this.toW(lx, lz);
    if (Math.abs(this.rot - q * Math.PI / 2) < 1e-3) { const odd = ((q % 2) + 2) % 2, W = odd ? bd : bw, D = odd ? bw : bd; this.colliders.push({ type: 'box', minX: wx - W / 2, maxX: wx + W / 2, minZ: wz - D / 2, maxZ: wz + D / 2, b: this.id, lv: this.lvTag }); }
    else { const n = Math.max(1, Math.ceil(Math.max(bw, bd) / Math.min(bw, bd) / 1)), r = Math.min(bw, bd) / 2 + .05; for (let i = 0; i < n; i++) { const f = n === 1 ? 0 : (i / (n - 1) - .5); const [x, z] = this.toW(lx + (bw >= bd ? f * (bw - bd) : 0), lz + (bw < bd ? f * (bd - bw) : 0)); this.colliders.push({ type: 'circle', x, z, r, b: this.id, lv: this.lvTag }); } }
  }
  ccol(lx, lz, r) { const [x, z] = this.toW(lx, lz); this.colliders.push({ type: 'circle', x, z, r, b: this.id, lv: this.lvTag }); }
  // ---- mesh helpers ----
  add(geo, mat, x, y, z, grp, o = {}) { if (this.curUp && grp === this.G.int) { grp = this.curUp.group; y += this.curUp.y; } const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = o.shadow !== false; m.receiveShadow = o.recv !== false; if (o.keep) m.userData.keep = true; (grp || this.G.ext).add(m); return m; }
  bx(w, h, d, key, x, y, z, grp, o) { return this.add(boxG(w, h, d, TILE[key] || 2), M(key, o && o.mat), x, y, z, grp, o); }
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
    return m;
  }
  banner(x, y, z, ry = 0, w = 1, h = 2.2, grp) { const m = M('#ffffff', { map: bannerTexture(), side: THREE.DoubleSide }); const p = this.add(new THREE.PlaneGeometry(w, h), m, x, y, z, grp || this.G.ext, { shadow: false }); p.rotation.y = ry; return p; }
  win(x, y, z, ry = 0, w = .9, h = 1.2, key = 'glass', grp, shut = key === 'glass' && w < 1.4 && !this.noShutters) {
    if (shut) for (const s of [-1, 1]) { const sh = this.bx(w * .42, h, .06, 'darkWood', x + Math.cos(ry) * s * (w * .72), y, z - Math.sin(ry) * s * (w * .72) + Math.cos(ry) * .03, grp || this.G.ext); sh.rotation.y = ry; } const p = this.add(new THREE.PlaneGeometry(w, h), M('#ffffff', { map: tex(key), emissive: key === 'glass' ? new THREE.Color(0x70480f) : new THREE.Color(0x0a1840), side: THREE.DoubleSide }), x, y, z, grp || this.G.ext, { shadow: false }); p.rotation.y = ry;
    const f = this.bx(w + .2, .12, .2, 'darkWood', x + Math.sin(ry) * .02, y - h / 2 - .04, z + Math.cos(ry) * .02, grp || this.G.ext); f.rotation.y = ry; return p; }
  sign(text, emblem, x, y, z, ry = 0) { // hanging shop sign on an iron bracket
    const t = signTexture(text, emblem), s = this.add(new THREE.PlaneGeometry(1.5, .75), new THREE.MeshLambertMaterial({ map: t, side: THREE.DoubleSide }), x, y, z, this.G.ext, { shadow: false, keep: true }); s.rotation.y = ry;
    const br = this.bx(.08, .08, 1.0, 'iron', x, y + .5, z - Math.cos(ry) * .5 * 0, this.G.ext); br.rotation.y = ry; return s; }
  chimney(x, y, z, h = 2.4, key = 'stoneD', w = .9) { this.bx(w, h, w, key, x, y + h / 2, z, this.G.roof); this.bx(w + .25, .18, w + .25, key, x, y + h, z, this.G.roof); }
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
    const { w, d, h } = o, T = this.T, DW = o.DW || 2.2, DH = o.DH || 2.6, hs = o.hs === undefined ? h * .42 : o.hs;
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
    this.bx(DW + .8, .14, 1.1, 'stoneD', 0, .07, d / 2 + .3, this.G.ext);
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
  rugAt(x, z, w, d, key = 'rug') { this.add(boxG(w, .02, d, TILE[key] || 3), M(key), x, .08, z, this.G.int, { shadow: false }); }
  // ---- finish ----
  finish() {
    for (const k of Object.keys(this.G)) mergeGroup(this.G[k]);
    this.root.userData.bid = this.id; return this;
  }
  setInside(v) {
    this.inside = v; this.G.roof.visible = !v; this.G.frame.visible = !v;
    for (const m of this.cut) { m.transparent = v; m.opacity = v ? .2 : 1; m.depthWrite = !v; m.needsUpdate = true; }
    for (const m of this.G.walls.children) m.castShadow = !v;
  }
  update(hx, hz, dt, level = 0) {
    const [lx, lz] = this.toL(hx, hz), dist = Math.hypot(hx - this.cx, hz - this.cz), R = (this.radius || Math.max(this.w || 10, this.d || 10)) + 40;
    const vis = dist < R + 20; if (this.root.visible !== vis) this.root.visible = vis;
    const nearInt = dist < (this.radius || 12) + 22; if (this.G.int.visible !== nearInt) this.G.int.visible = nearInt;   // interiors only drawn when close (fewer draw calls)
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
Builder.prototype.stairs = function (o) {
  const { cx, cz, ang = 0, len, w = 1.8, l0 = 0, y0 = 0, l1, y1 } = o; const m = { cx, cz, ang, len, w, l0, y0, l1, y1 }; this.ramps.push(m); this.levelGroup(l1);
  const n = Math.max(3, Math.round((y1 - y0) / .3)), s = Math.sin(ang), c = Math.cos(ang), grp = l0 ? this.levelGroup(l0) : this.G.int, key = o.key || 'wood';
  for (let i = 0; i < n; i++) { const u = -len / 2 + (i + .5) * len / n, top = y0 + (i + 1) * (y1 - y0) / n, hh = top - y0 + (l0 ? 0 : 0); const b = this.bx(w, hh, len / n + .01, key, 0, 0, 0, grp); b.position.set(cx + s * u, y0 + hh / 2, cz + c * u); b.rotation.y = ang; }
  for (const sd of [-1, 1]) { const px = cx + c * sd * (w / 2 + .05), pz = cz - s * sd * (w / 2 + .05); const b = this.bx(.1, .12, len + .3, 'darkWood', px, (y0 + y1) / 2 + .95, pz, grp); b.position.set(px + s * 0, (y0 + y1) / 2 + .95, pz); b.rotation.y = ang; b.rotation.x = 0;
    b.rotateX(-Math.atan2(y1 - y0, len)); // sloped handrail
    const k = Math.max(2, Math.round(len / 1.0)); for (let q = 0; q <= k; q++) { const u = -len / 2 + q * len / k, yy = y0 + (y1 - y0) * (q / k); this.bx(.07, .9, .07, 'darkWood', cx + s * u + c * sd * (w / 2 + .05), yy + .45, cz + c * u - s * sd * (w / 2 + .05), grp); }
    // side colliders (row of circles, all levels): hero cannot leave the flight sideways
    const ln = Math.max(.5, len - .9), nn = Math.ceil(ln / .3); for (let q = 0; q <= nn; q++) { const u = -len / 2 + q * ln / nn, lx = cx + s * u + c * sd * (w / 2 + .22), lz = cz + c * u - s * sd * (w / 2 + .22); const [wx, wz] = this.toW(lx, lz); this.colliders.push({ type: 'circle', x: wx, z: wz, r: .2, b: this.id, lv: [l0, l1], stair: 1 }); } }
  // keep ground-level walkers from slipping past the top end underneath the slab
  { const lx = cx + s * (len / 2 + 1.1), lz = cz + c * (len / 2 + 1.1); const nn = Math.ceil(w / .35); for (let q = 0; q <= nn; q++) { const t = -w / 2 + q * w / nn; const [wx, wz] = this.toW(lx + c * t, lz - s * t); this.colliders.push({ type: 'circle', x: wx, z: wz, r: .2, b: this.id, lv: l0, stair: 1 }); } }
  return m;
};
// query: surface height for a local-frame hero position at the given level -> {y, ramp, t} or null if there is no floor there
Builder.prototype.surface = function (wx, wz, level) {
  const [lx, lz] = this.toL(wx, wz);
  for (const m of this.ramps) { if (m.l0 !== level && m.l1 !== level) continue; const [u, v] = this.rampUV(m, lx, lz); if (Math.abs(u) <= m.len / 2 && Math.abs(v) <= m.w / 2) { const t = (u + m.len / 2) / m.len; return { y: m.y0 + (m.y1 - m.y0) * t, ramp: m, t }; } }
  for (const f of this.floors) if (f.level === level && f.disc && Math.hypot(lx, lz) < f.disc - .1 && !f.holes.some(h => lx > h[0] - .02 && lx < h[1] + .02 && lz > h[2] - .02 && lz < h[3] + .02)) return { y: f.y };
  for (const f of this.floors) if (f.level === level && f.rects) for (const r of f.rects) if (lx > r[0] + .05 && lx < r[1] - .05 && lz > r[2] + .05 && lz < r[3] - .05) return { y: f.y };
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
  const y = o.y || 3.1, iw = this.iw, id_ = this.id_, dp = o.depth || 2.2, rects = [[-iw, iw, -id_, -id_ + dp]]; if (o.side) rects.push(o.side > 0 ? [iw - dp, iw, -id_ + dp, id_ - 2.5] : [-iw, -iw + dp, -id_ + dp, id_ - 2.5]);
  const sx = o.stairX === undefined ? iw - 1.0 : o.stairX, len = Math.min(o.run || 3.6, id_ * 2 - dp - .7);
  this.stairs({ cx: sx, cz: -id_ + dp + len / 2, ang: Math.PI, len, w: 1.7, l0: 0, y0: 0, l1: 1, y1: y });
  this.upperFloor(1, y, rects, o);
  if (o.rooms) this.onFloor(1, y, o.rooms);
  this.col(0, -id_ + .4, iw * 2, .6);
};

// round hollow shell (towers, colosseum, windmill, lighthouse, observatory): N wall segments with a door gap at local +z
Builder.prototype.roundShell = function (o) { const _lv = this.lvTag; this.lvTag = undefined; try { return this._roundShell(o); } finally { this.lvTag = _lv; } };
Builder.prototype._roundShell = function (o) {
  const { r, h } = o, T = o.T || this.T, N = o.N || Math.max(12, Math.round(r * 2.6)), DW = o.DW || 2.2, DH = o.DH || 2.6, key = o.key || 'stone', seg = 2 * Math.PI * r / N;
  this.radius = r; this.w = this.d = r * 2; this.h = h; this.DW = DW; this.iw = r - T; this.id_ = r - T;
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
Builder.prototype.apron = function (w, d, zOff = 2) { this.bx(w + 3.4, .08, d + 3.4 + zOff, 'cobble', 0, .04, zOff / 2, this.G.ext, { shadow: false }); };
Builder.prototype.bush = function (x, z, s = .7, c = '#3f7a3a') { const m = this.add(new THREE.IcosahedronGeometry(s, 0), M(c), x, s * .6, z, this.G.ext); m.scale.y = .8; return m; };
Builder.prototype.flowers = function (x, y, z, w, ry = 0) { // window flower box
  const f = this.bx(w, .22, .3, 'darkWood', x, y, z, this.G.ext); f.rotation.y = ry; const g = this.bx(w * .95, .12, .26, '#3f7a3a', x, y + .14, z, this.G.ext, { shadow: false }); g.rotation.y = ry;
  for (let i = 0; i < 5; i++) { const t = (i / 4 - .5) * w * .8; this.add(new THREE.SphereGeometry(.07, 5, 4), M(['#d84a5a', '#f0d040', '#e88adf', '#fff0f0'][i % 4]), x + Math.cos(ry) * t, y + .25, z - Math.sin(ry) * t + Math.cos(ry) * .05, this.G.ext, { shadow: false }); } };
Builder.prototype.lanternPost = function (x, z, h = 2.8) { this.cyl(.07, .1, h, 'iron', x, h / 2, z, this.G.ext, 6); this.bx(.5, .06, .06, 'iron', x + .2, h - .1, z, this.G.ext); this.add(new THREE.SphereGeometry(.17, 6, 5), GLOW('ffc060', 1.7), x + .4, h - .3, z, this.G.ext, { shadow: false }); this.ccol(x, z, .2); };
Builder.prototype.flag = function (x, y, z, s = 1, grp) { this.bx(.06, 1.6 * s, .06, 'iron', x, y + .8 * s, z, grp || this.G.ext, { shadow: false }); const f = this.add(new THREE.PlaneGeometry(1.0 * s, .6 * s), M('#1f4a9a', { side: THREE.DoubleSide }), x + .5 * s, y + 1.3 * s, z, grp || this.G.ext, { shadow: false }); f.rotation.y = .25; this.add(new THREE.CircleGeometry(.14 * s, 8), M('gold', { side: THREE.DoubleSide }), x + .45 * s, y + 1.3 * s, z + .01, grp || this.G.ext, { shadow: false }); };
Builder.prototype.guard = function (x, z, ry = 0) { const g = this.G.ext; this.cyl(.22, .26, .9, '#2f56a8', x, 1.0, z, g, 6); this.cyl(.1, .1, .45, '#444a58', x - .1, .3, z, g, 5); this.cyl(.1, .1, .45, '#444a58', x + .1, .3, z, g, 5);
  this.add(new THREE.SphereGeometry(.17, 6, 5), M('#e8c09a'), x, 1.65, z, g); this.add(new THREE.ConeGeometry(.2, .26, 6), M('#8a9099'), x, 1.85, z, g); this.bx(.05, 2.3, .05, 'darkWood', x + .35, 1.2, z, g, { shadow: false }); this.add(new THREE.ConeGeometry(.07, .3, 4), M('#b6bcc8'), x + .35, 2.45, z, g, { shadow: false }); this.ccol(x, z, .3); };
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
  if (o.stair) { const st = o.stair, ang = { '-z': Math.PI, '+z': 0, '-x': -Math.PI / 2, '+x': Math.PI / 2 }[st.dir || '-z'], len = st.len || 3.6, w = st.w || 1.7, ax = Math.abs(Math.sin(ang)) > .5;
    hole = ax ? [st.cx - len / 2, st.cx + len / 2, st.cz - w / 2, st.cz + w / 2] : [st.cx - w / 2, st.cx + w / 2, st.cz - len / 2, st.cz + len / 2];
    rects = subRect(rect, hole); this.stairs({ cx: st.cx, cz: st.cz, ang, len, w, l0, y0, l1: level, y1: y });
    // low end of the opening: block + rail so an upstairs hero cannot step off the slab into the stairwell
    const s = Math.sin(ang), c = Math.cos(ang), lx = st.cx - s * (len / 2 + .15), lz = st.cz - c * (len / 2 + .15), nn = Math.ceil(w / .35);
    for (let q = 0; q <= nn; q++) { const t = -w / 2 + q * w / nn; const [wx, wz] = this.toW(lx + c * t, lz - s * t); this.colliders.push({ type: 'circle', x: wx, z: wz, r: .2, b: this.id, lv: level, stair: 1 }); }
    const g = this.levelGroup(level), rl = this.bx(ax ? .07 : w, .07, ax ? w : .07, 'darkWood', st.cx - s * (len / 2 + .02), y + .95, st.cz - c * (len / 2 + .02), g);
    for (let q = 0; q <= 3; q++) { const t = -w / 2 + q * w / 3; this.bx(.08, .95, .08, 'darkWood', st.cx - s * (len / 2 + .02) + c * t, y + .48, st.cz - c * (len / 2 + .02) - s * t, g); } }
  if (o.disc) { const g = this.levelGroup(level), r = o.disc, sh = new THREE.Shape(); sh.absarc(0, 0, r, 0, Math.PI * 2, false); if (hole) { const hp = new THREE.Path(); hp.moveTo(hole[0], -hole[2]); hp.lineTo(hole[1], -hole[2]); hp.lineTo(hole[1], -hole[3]); hp.lineTo(hole[0], -hole[3]); hp.closePath(); sh.holes.push(hp); }
    const eg = new THREE.ExtrudeGeometry(sh, { depth: .22, bevelEnabled: false, curveSegments: 20 }); eg.rotateX(-Math.PI / 2); uvScale(eg, 1 / (TILE[o.key || 'floorPlank'] || 3), 1 / (TILE[o.key || 'floorPlank'] || 3));
    const m = this.add(eg, M(o.key || 'floorPlank'), 0, y - .22, 0, g); this.floors.push({ level, y, disc: r, holes: hole ? [hole] : [] }); }
  else this.upperFloor(level, y, rects, Object.assign({}, o, { rails: o.rails }));
  if (o.rooms) this.onFloor(level, y, o.rooms);
  return rects;
};
