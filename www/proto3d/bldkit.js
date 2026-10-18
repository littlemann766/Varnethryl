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
    this.G = {}; for (const k of ['ext', 'walls', 'roof', 'frame', 'int']) { this.G[k] = new THREE.Group(); this.root.add(this.G[k]); }
    this.cut = []; this.cutCache = {}; this.dyn = []; this.T = 0.45; this.inside = false; this.colInfo = []; this.insideTest = null; this.footprint = null;
  }
  // ---- placement helpers ----
  toW(lx, lz) { return [this.cx + lx * this.cs + lz * this.sn, this.cz - lx * this.sn + lz * this.cs]; }
  toL(wx, wz) { const dx = wx - this.cx, dz = wz - this.cz; return [dx * this.cs - dz * this.sn, dx * this.sn + dz * this.cs]; }
  col(lx, lz, bw, bd) { // axis-aligned in local; world box when rot is a quarter turn, else a row of circles
    const q = Math.round(this.rot / (Math.PI / 2)); const [wx, wz] = this.toW(lx, lz);
    if (Math.abs(this.rot - q * Math.PI / 2) < 1e-3) { const odd = ((q % 2) + 2) % 2, W = odd ? bd : bw, D = odd ? bw : bd; this.colliders.push({ type: 'box', minX: wx - W / 2, maxX: wx + W / 2, minZ: wz - D / 2, maxZ: wz + D / 2, b: this.id }); }
    else { const n = Math.max(1, Math.ceil(Math.max(bw, bd) / Math.min(bw, bd) / 1)), r = Math.min(bw, bd) / 2 + .05; for (let i = 0; i < n; i++) { const f = n === 1 ? 0 : (i / (n - 1) - .5); const [x, z] = this.toW(lx + (bw >= bd ? f * (bw - bd) : 0), lz + (bw < bd ? f * (bd - bw) : 0)); this.colliders.push({ type: 'circle', x, z, r, b: this.id }); } }
  }
  ccol(lx, lz, r) { const [x, z] = this.toW(lx, lz); this.colliders.push({ type: 'circle', x, z, r, b: this.id }); }
  // ---- mesh helpers ----
  add(geo, mat, x, y, z, grp, o = {}) { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = o.shadow !== false; m.receiveShadow = o.recv !== false; if (o.keep) m.userData.keep = true; (grp || this.G.ext).add(m); return m; }
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
  win(x, y, z, ry = 0, w = .9, h = 1.2, key = 'glass', grp) { const p = this.add(new THREE.PlaneGeometry(w, h), M('#ffffff', { map: tex(key), emissive: key === 'glass' ? new THREE.Color(0x70480f) : new THREE.Color(0x0a1840), side: THREE.DoubleSide }), x, y, z, grp || this.G.ext, { shadow: false }); p.rotation.y = ry;
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
    if (o.collide !== false) this.ccol(x, z, r * 1.08);
    if (o.windows) for (let i = 0; i < o.windows; i++) { const a = i / o.windows * 6.283 + (o.wa || .8); this.win(x + Math.cos(a) * (r * 1.05), h * .62, z + Math.sin(a) * (r * 1.05), Math.PI / 2 - a, .35, .8, 'glass'); }
  }
  // ---- standard rectangular shell: stone base + upper storey, hollow, door gap at +z ----
  rectShell(o) {
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
    for (const k of ['ext', 'walls', 'roof', 'frame', 'int']) mergeGroup(this.G[k]);
    this.root.userData.bid = this.id; return this;
  }
  setInside(v) {
    this.inside = v; this.G.roof.visible = !v; this.G.frame.visible = !v;
    for (const m of this.cut) { m.transparent = v; m.opacity = v ? .2 : 1; m.depthWrite = !v; m.needsUpdate = true; }
    for (const m of this.G.walls.children) m.castShadow = !v;
  }
  update(hx, hz, dt) {
    const [lx, lz] = this.toL(hx, hz), dist = Math.hypot(hx - this.cx, hz - this.cz), R = (this.radius || Math.max(this.w || 10, this.d || 10)) + 40;
    const vis = dist < R + 20; if (this.root.visible !== vis) this.root.visible = vis;
    const nearInt = dist < (this.radius || 12) + 22; if (this.G.int.visible !== nearInt) this.G.int.visible = nearInt;   // interiors only drawn when close (fewer draw calls)
    const v = this.insideTest ? this.insideTest(lx, lz) : false; if (v !== this.inside) this.setInside(v);
    if (this.tick && vis) this.tick(dt || 0.016);
    return v;
  }
}

// gallery / mezzanine (visual upper floor along the back and side walls) with a stair run and railing
Builder.prototype.gallery = function (o = {}) {
  const y = o.y || 3.1, iw = this.iw, id_ = this.id_, dp = o.depth || 2.2, side = o.side || 0;
  this.bx(iw * 2, .16, dp, 'floorPlank', 0, y, -id_ + dp / 2, this.G.int); if (side !== 0) this.bx(dp, .16, id_ * 2 - dp, 'floorPlank', side * (iw - dp / 2), y, dp / 2 * 0 + dp / 2 - (id_ * 2 - dp) / 2 * 0 + 0.0 + (dp - 0) / 2 * 0, this.G.int);
  this.bx(iw * 2, .9, .1, 'darkWood', 0, y + .55, -id_ + dp, this.G.int);
  for (let i = -3; i <= 3; i++) this.bx(.1, 1, .1, 'darkWood', i * iw / 3, y + .5, -id_ + dp, this.G.int);
  const sx = o.stairX === undefined ? iw - 1.0 : o.stairX, n = 9;   // stairs rise toward the back wall
  for (let i = 0; i < n; i++) { const sy = (i + 1) * y / n; this.bx(1.2, .2, .45, 'wood', sx, sy - .1, -id_ + dp + 3.6 - i * .4, this.G.int); }
  this.col(sx, -id_ + dp + 1.9, 1.2, 3.8); this.col(0, -id_ + .4, iw * 2, .6);
};

// round hollow shell (towers, colosseum, windmill, lighthouse, observatory): N wall segments with a door gap at local +z
Builder.prototype.roundShell = function (o) {
  const { r, h } = o, T = o.T || this.T, N = o.N || Math.max(12, Math.round(r * 2.6)), DW = o.DW || 2.2, DH = o.DH || 2.6, key = o.key || 'stone', seg = 2 * Math.PI * r / N;
  this.radius = r; this.w = this.d = r * 2; this.h = h; this.DW = DW; this.iw = r - T; this.id_ = r - T;
  const doorA = Math.asin(Math.min(.95, (DW / 2 + seg * .35) / r));
  for (let i = 0; i < N; i++) {
    let a = i / N * 2 * Math.PI; if (a > Math.PI) a -= 2 * Math.PI; if (Math.abs(a) < doorA) continue;
    const x = Math.sin(a) * (r - T / 2), z = Math.cos(a) * (r - T / 2), m = this.wallBox(seg * 1.04, h, T, key, x, h / 2, z); m.rotation.y = a;
    this.ccol(x, z, seg / 2 + .12);
  }
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
