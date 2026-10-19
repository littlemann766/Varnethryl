/* VARNETHRYL 3D scenery kit: low-poly trees, bushes, flowers, rocks and props with vertex colours.
   Every variant is ONE merged BufferGeometry (position, normal, colour, uv). Detail comes from shape, per-face colour variation,
   height gradients, moss/strata tinting and a small shared grain texture. scatterWorld() merges a whole village mix into 3 meshes. */
import * as THREE from './vendor/three.module.js';

const K = h => { const c = new THREE.Color(h); return [c.r, c.g, c.b]; };
let seedState = 1, LOD = 0;
const R = () => { seedState |= 0; seedState = seedState + 0x6D2B79F5 | 0; let t = Math.imul(seedState ^ seedState >>> 15, 1 | seedState); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
const setSeed = s => { seedState = (s * 2654435761) >>> 0 || 1; for (let i = 0; i < 4; i++) R(); };
const rr = (a, b) => a + (b - a) * R();
const pick = a => a[Math.floor(R() * a.length) % a.length];
const hash3 = (x, y, z, s) => { const v = Math.sin(x * 127.1 + y * 311.7 + z * 74.7 + s * 19.19) * 43758.5453; return v - Math.floor(v); };

/* ---------- palettes ---------- */
export const LEAF = {
  green: [0x4a9a3c, 0x7cc44f, 0x2f6e30], deep: [0x2f6f3a, 0x4f9150, 0x1d4a2c], lime: [0x8ab83a, 0xb5d85a, 0x5e8a2a],
  autumn: [0xd9792b, 0xf0a040, 0xa24a1c], red: [0xb8372e, 0xe0634a, 0x7e2020], yellow: [0xd9b92f, 0xf0dc5c, 0xa88a20],
  spruce: [0x3f7f7a, 0x6aa8a0, 0x285450], blossom: [0xe8a0b8, 0xf8d0dc, 0xc07090]
};
export const DOT = { none: null, red: 0xd8342a, blue: 0x3f6fd8, pink: 0xf08ab0, white: 0xf4f4ee, yellow: 0xf2d23a, purple: 0x9a58d0, orange: 0xf09030 };
export const BARK = { brown: [0x6b4a2b, 0x3e2a18], grey: [0x7a746a, 0x4a463f], dark: [0x4a3524, 0x261a10], pale: [0xb5a58c, 0x7a6a52], birch: [0xe8e4d8, 0x2c2a28] };
export const WOOD = { oak: [0x8a5a34, 0x5a3a20], pine: [0xc89a5c, 0x8a6a38], weathered: [0x8c8274, 0x5c554a], dark: [0x5a3a24, 0x34200f], red: [0x9a4a30, 0x5e281a] };
export const ROCK = { grey: [0x9a9ea6, 0x6b707a], warm: [0xb0a08a, 0x7c6e5a], slate: [0x62707e, 0x3e4854], mossy: [0x8a9088, 0x5a6a52] };
export const FLOWER = { red: 0xd8343a, yellow: 0xf2cc2a, purple: 0x8c4fcf, white: 0xf6f4ee, pink: 0xf07aa8, blue: 0x4a74e0, orange: 0xf08a28 };
export const GRASS = { green: [0x5fa845, 0x3f7e34], lush: [0x77c24a, 0x4e9a3a], dry: [0xc2b25a, 0x8a7a3a] };

/* ---------- merged builder ---------- */
class B {
  constructor() { this.p = []; this.n = []; this.c = []; }
  add(g, M, t) {
    const P = g.attributes.position.array, e = M.elements, q = new Float32Array(9), cnt = P.length / 9;
    const y1 = t.y1 === t.y0 ? t.y0 + 1 : t.y1;
    for (let i = 0; i < cnt; i++) {
      for (let k = 0; k < 3; k++) { const x = P[i * 9 + k * 3], y = P[i * 9 + k * 3 + 1], z = P[i * 9 + k * 3 + 2]; q[k * 3] = e[0] * x + e[4] * y + e[8] * z + e[12]; q[k * 3 + 1] = e[1] * x + e[5] * y + e[9] * z + e[13]; q[k * 3 + 2] = e[2] * x + e[6] * y + e[10] * z + e[14]; }
      const ux = q[3] - q[0], uy = q[4] - q[1], uz = q[5] - q[2], vx = q[6] - q[0], vy = q[7] - q[1], vz = q[8] - q[2];
      let nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx; const nl = Math.hypot(nx, ny, nz) || 1; nx /= nl; ny /= nl; nz /= nl;
      const cy = (q[1] + q[4] + q[7]) / 3;
      let r = t.c[0], gg = t.c[1], bl = t.c[2];
      if (t.c2 && t.mx) { const f = R() * t.mx; r += (t.c2[0] - r) * f; gg += (t.c2[1] - gg) * f; bl += (t.c2[2] - bl) * f; }
      let sh = 1 + (R() - .5) * 2 * t.j;
      if (t.band) sh *= 1 + t.band * Math.sin(cy * t.bf);
      let mm = 0;
      if (t.moss && ny > t.ma && R() > .25) mm = Math.min(1, (ny - t.ma) * 4);
      if (mm) { r += (t.moss[0] - r) * mm; gg += (t.moss[1] - gg) * mm; bl += (t.moss[2] - bl) * mm; }
      for (let k = 0; k < 3; k++) {
        const vf = t.a + (t.b - t.a) * Math.max(0, Math.min(1, (q[k * 3 + 1] - t.y0) / (y1 - t.y0))), s = sh * vf;
        this.p.push(q[k * 3], q[k * 3 + 1], q[k * 3 + 2]); this.n.push(nx, ny, nz); this.c.push(r * s, gg * s, bl * s);
      }
    }
  }
}
function tint(c, o) { const t = Object.assign({ c2: null, mx: 0, j: .08, a: .8, b: 1.12, y0: 0, y1: 1, moss: null, ma: .55, band: 0, bf: 8 }, o); t.c = Array.isArray(c) ? c : K(c); if (t.c2 != null && !Array.isArray(t.c2)) t.c2 = K(t.c2); if (t.moss != null && !Array.isArray(t.moss)) t.moss = K(t.moss); return t; }
const M4 = new THREE.Matrix4(), QQ = new THREE.Quaternion(), EE = new THREE.Euler(0, 0, 0, 'YXZ'), VP = new THREE.Vector3(), VS = new THREE.Vector3();
function put(b, geo, t, x, y, z, sx, sy, sz, rx, ry, rz, jit) {
  const g = geo.index ? geo.toNonIndexed() : geo;
  if (jit) { const P = g.attributes.position, sd = R() * 50; for (let i = 0; i < P.count; i++) { const px = P.getX(i), py = P.getY(i), pz = P.getZ(i), h = 1 + (hash3(Math.round(px * 90), Math.round(py * 90), Math.round(pz * 90), sd) - .5) * jit; P.setXYZ(i, px * h, py * h, pz * h); } }
  EE.set(rx || 0, ry || 0, rz || 0); QQ.setFromEuler(EE); M4.compose(VP.set(x, y, z), QQ, VS.set(sx, sy, sz)); b.add(g, M4, t); geo.dispose(); if (g !== geo) g.dispose();
}
const blob = (b, t, r, x, y, z, sx, sy, sz, det, jit) => put(b, new THREE.IcosahedronGeometry(r, LOD ? 0 : det), t, x, y, z, sx, sy, sz, 0, R() * 6.28, 0, jit);
function cyl(b, t, rt, rb, h, seg, x, y, z, rx, ry, rz, capped) { const g = new THREE.CylinderGeometry(rt, rb, h, seg, 1, !capped); g.translate(0, h / 2, 0); put(b, g, t, x, y, z, 1, 1, 1, rx, ry, rz, 0); }
function cone(b, t, r, h, seg, x, y, z, rx, ry, rz, jit) { const g = new THREE.ConeGeometry(r, h, seg, 1, true); g.translate(0, h / 2, 0); put(b, g, t, x, y, z, 1, 1, 1, rx, ry, rz, jit); }
const box = (b, t, w, h, d, x, y, z, rx, ry, rz) => put(b, new THREE.BoxGeometry(w, h, d), t, x, y, z, 1, 1, 1, rx, ry, rz, 0);
const IRON = 0x34363e;
const bump = (b, t, r, x, y, z, sx, sy, sz, jit) => put(b, new THREE.OctahedronGeometry(r, 0), t, x, y, z, sx, sy, sz, 0, R() * 6.28, 0, jit);
const nail = (b, t, x, y, z) => put(b, new THREE.TetrahedronGeometry(.035, 0), t, x, y, z, 1, 1, 1, R() * 3, R() * 3, 0, 0);

/* ---------- trees ---------- */
function roots(b, bark, n, r, y) { if (LOD) return; for (let i = 0; i < n; i++) { const a = i / n * 6.28 + R(); cone(b, tint(bark[0], { c2: bark[1], mx: .5, j: .15, a: .7, b: 1 }), r * rr(.25, .4), rr(.7, 1.1), 5, Math.sin(a) * r * .75, y + .35, Math.cos(a) * r * .75, 1.95 + R() * .3, a, 0, 0, 0, true); } }
function trunk(b, bark, r0, h, y0) {
  const t = tint(bark[0], { c2: bark[1], mx: .6, j: .14, a: .78, b: 1.05, y0, y1: y0 + h });
  cyl(b, t, r0 * .78, r0 * 1.12, h * .4, 7, 0, y0, 0); cyl(b, t, r0 * .55, r0 * .78, h * .6, 7, 0, y0 + h * .4, 0);
  const dk = tint(bark[1], { j: .1, a: .9, b: 1 });
  for (let i = 0; i < (LOD ? 0 : 3); i++) { const yy = y0 + h * rr(.12, .85); cyl(b, dk, r0 * (.8 - yy / h * .22) + .015, r0 * (.8 - yy / h * .22) + .015, .045, 7, 0, yy, 0); }
}
function clump(b, P, x, y, z, r, sy, det, bumps) {
  const L = LEAF[P] || LEAF.green, c = pick(L.concat([L[0], L[0]]));
  const t = tint(c, { c2: pick(L), mx: .7, j: .09, a: .7, b: 1.22, y0: y - r * sy, y1: y + r * sy });
  blob(b, t, r, x, y, z, 1, sy, 1, det, .28);
  for (let i = 0; i < (LOD ? 0 : bumps); i++) { const a = R() * 6.28, e = rr(-.2, 1) * 1.1, rad = r * .95; bump(b, tint(L[1], { c2: L[0], mx: .5, j: .1, a: .95, b: 1.1 }), r * .34, Math.cos(a) * Math.cos(e) * rad + x, y + Math.sin(e) * rad * sy, Math.sin(a) * Math.cos(e) * rad + z, 1, .8, 1, .3); }
}
function oak(b, P, bark) {
  trunk(b, bark, .38, 2.3, -.05); roots(b, bark, 4, .38, -.1);
  const tb = tint(bark[0], { c2: bark[1], mx: .5, j: .14 });
  for (const s of [-1, 1]) { cyl(b, tb, .07, .15, 1.5, 6, 0, 1.9, 0, 0, 0, s * .65); cyl(b, tb, .035, .06, .5, 5, s * .33, 1.25, .06, 0, 0, s * -1.0); }
  cyl(b, tb, .04, .07, .55, 5, 0, 1.25, .2, 1.1, 0, 0);
  clump(b, P, 0, 3.55, 0, 1.55, .85, 1, 8);
  for (let i = 0; i < 5; i++) { const a = i / 5 * 6.28 + .4; clump(b, P, Math.cos(a) * 1.15, 2.95 + R() * .7, Math.sin(a) * 1.15, rr(.85, 1.05), .85, 0, 2); }
  clump(b, P, .1, 4.5, 0, .95, .8, 0, 2);
}
function pine(b, P, bark) {
  trunk(b, bark, .26, 1.6, -.05); roots(b, bark, 3, .26, -.1);
  const L = LEAF[P] || LEAF.deep;
  for (let i = 0; i < 6; i++) {
    const r = 1.55 - i * .22, y = .85 + i * .78, t = tint(L[i % 2 ? 2 : 0], { c2: L[1], mx: .6, j: .1, a: .72, b: 1.28, y0: y, y1: y + 1.6 });
    cone(b, t, r, 1.5, 8, 0, y, 0, 0, R() * 6.28, 0, .14);
  }
  cone(b, tint(L[1], { j: .06, a: 1, b: 1.2 }), .2, .8, 6, 0, 5.2, 0, 0, 0, 0, 0);
  for (let i = 0; i < 3; i++) { const a = R() * 6.28; blob(b, tint(0x6a4528, { j: .15 }), .1, Math.cos(a) * 1.0, 1.15 + R() * 1.2, Math.sin(a) * 1.0, 1, 1.5, 1, 0, .2); }
}
function birch(b, P, bark) {
  const t = tint(0xe8e4d8, { c2: 0xb8b2a2, mx: .4, j: .06, a: .85, b: 1.05, y0: 0, y1: 4 });
  cyl(b, t, .1, .2, 2.0, 7, 0, -.05, 0); cyl(b, t, .06, .1, 1.9, 7, 0, 1.95, 0, .05, 0, -.06); roots(b, [0xcfc8b8, 0x6a6458], 3, .2, -.1);
  const dk = tint(0x2c2a28, { j: .05, a: 1, b: 1 });
  for (let i = 0; i < 9; i++) { const yy = rr(.1, 3.5), rd = .19 - yy * .035; box(b, dk, rd * 1.1, .05, rd * .6, 0, yy, rd * .7, 0, 0, 0); box(b, dk, rd * .6, .04, rd * 1.1, rd * .7, yy + .15, 0, 0, 0, 0); }
  const tb = tint(0xbab4a4, { j: .08 });
  cyl(b, tb, .03, .06, 1.2, 5, 0, 2.4, 0, 0, 0, .7); cyl(b, tb, .03, .06, 1.0, 5, 0, 2.7, 0, .6, 1.5, 0);
  clump(b, P, 0, 3.9, 0, .95, 1.35, 1, 4); clump(b, P, .6, 3.2, .3, .65, 1.1, 0, 2); clump(b, P, -.55, 3.4, -.3, .7, 1.2, 0, 2); clump(b, P, .1, 4.8, .1, .55, 1.2, 0, 1);
}
function dead(b, P, bark) {
  const t = tint(bark[0], { c2: bark[1], mx: .6, j: .16, a: .75, b: 1.05, y0: 0, y1: 4 });
  cyl(b, t, .16, .34, 1.3, 7, 0, -.05, 0); cyl(b, t, .1, .16, 1.2, 6, .02, 1.2, 0, .08, 0, -.08); cyl(b, t, .05, .1, 1.2, 6, .13, 2.35, .0, -.12, 0, -.1);
  roots(b, bark, 5, .34, -.1);
  for (let i = 0; i < 6; i++) {
    const yy = 1.0 + i * .45, az = i * 2.4 + R(), len = rr(1.0, 1.7), tl = rr(.7, 1.1), bx = Math.sin(az) * .1, bz = Math.cos(az) * .1;
    cyl(b, t, .025, .08, len, 5, bx, yy, bz, tl, az, 0);
    const ex = bx + Math.sin(az) * Math.sin(tl) * len * .7, ez = bz + Math.cos(az) * Math.sin(tl) * len * .7, ey = yy + Math.cos(tl) * len * .7;
    cyl(b, t, .012, .035, len * .45, 4, ex, ey, ez, tl + .5, az + .9, 0); cyl(b, t, .012, .03, len * .35, 4, ex, ey, ez, tl - .2, az - .8, 0);
  }
  blob(b, tint(0x1c1410, { j: .05 }), .09, .06, 1.0, .3, 1, 1.4, .5, 0, 0);
  blob(b, tint(0x6a8a4a, { c2: 0x3e5a2e, mx: .6, j: .1 }), .22, .18, .05, .18, 1.4, .5, 1.2, 0, .3);
}
function cypress(b, P, bark) {
  trunk(b, bark, .2, 1.2, -.05);
  const L = LEAF[P] || LEAF.deep;
  [[.95, 2.0, 1.1], [.85, 3.0, 1.3], [.7, 4.0, 1.4], [.5, 4.9, 1.4]].forEach(([r, y, s], i) => blob(b, tint(L[i % 3], { c2: L[1], mx: .6, j: .09, a: .7, b: 1.25, y0: y - r * s, y1: y + r * s }), r, (R() - .5) * .12, y, (R() - .5) * .12, 1, s, 1, i < 2 ? 1 : 0, .3));
  cone(b, tint(L[1], { a: 1, b: 1.2 }), .3, 1, 6, 0, 5.4, 0, 0, 0, 0, .1);
}
function apple(b, P, bark) {
  trunk(b, bark, .34, 1.7, -.05); roots(b, bark, 4, .34, -.1);
  const tb = tint(bark[0], { c2: bark[1], mx: .5, j: .14 });
  cyl(b, tb, .06, .12, 1.0, 5, 0, 1.4, 0, 0, 0, .9); cyl(b, tb, .06, .12, 1.0, 5, 0, 1.5, 0, 0, 0, -.9);
  clump(b, P, 0, 2.9, 0, 1.35, .8, 1, 6); for (let i = 0; i < 4; i++) { const a = i / 4 * 6.28 + .7; clump(b, P, Math.cos(a) * 1.2, 2.5 + R() * .4, Math.sin(a) * 1.2, .9, .8, 0, 2); }
  const fc = P === 'blossom' ? 0xfff2f6 : P === 'autumn' ? 0xe8b830 : 0xd8342a, ft = tint(fc, { j: .08, a: .9, b: 1.15 });
  for (let i = 0; i < 12; i++) { const a = R() * 6.28, e = rr(-.5, .7), rd = 1.45; bump(b, ft, .12, Math.cos(a) * Math.cos(e) * rd, 2.9 + Math.sin(e) * rd * .8, Math.sin(a) * Math.cos(e) * rd, 1, 1, 1, .1); }
}

/* ---------- bushes, mushrooms, reeds ---------- */
function dots(b, col, n, cx, cy, cz, rd, sy) { if (col == null) return; const t = tint(col, { j: .08, a: .95, b: 1.15 }); for (let i = 0; i < n; i++) { const a = R() * 6.28, e = rr(-.2, 1.1); const q = 1.25; bump(b, t, rr(.07, .1), cx + Math.cos(a) * Math.cos(e) * rd, cy + Math.sin(e) * rd * sy, cz + Math.sin(a) * Math.cos(e) * rd, 1, 1, 1, .1); } }
function bushRound(b, P, dot) {
  const L = LEAF[P] || LEAF.green, tw = tint(0x5a3d22, { j: .12 });
  for (let i = 0; i < 3; i++) cone(b, tw, .04, .5, 4, Math.cos(i * 2.1) * .2, 0, Math.sin(i * 2.1) * .2, .4, i * 2.1 + 3.14, 0, 0);
  const n = 4; for (let i = 0; i < n; i++) { const a = i / n * 6.28 + R(), rd = i ? .38 : 0, r = i ? rr(.38, .5) : .62, x = Math.cos(a) * rd, z = Math.sin(a) * rd; blob(b, tint(pick(L), { c2: L[1], mx: .6, j: .09, a: .7, b: 1.25, y0: 0, y1: 1.1 }), r, x, .38 + (i ? 0 : .12), z, 1, .8, 1, i ? 0 : 1, .3); }
  dots(b, DOT[dot], 9, 0, .5, 0, .7, .8);
}
function bushSpiky(b, P) {
  const L = LEAF[P] || LEAF.green;
  for (let i = 0; i < 11; i++) { const a = i / 11 * 6.28 + R() * .4, tl = rr(.5, 1.1), len = rr(.7, 1.15); cone(b, tint(pick(L), { c2: L[1], mx: .5, j: .08, a: .7, b: 1.3, y0: 0, y1: 1 }), .09, len, 4, Math.sin(a) * .08, .02, Math.cos(a) * .08, tl, a, 0, .1); }
  blob(b, tint(L[2], { j: .1, a: .8, b: 1 }), .22, 0, .18, 0, 1, .7, 1, 0, .2);
}
function bushHedge(b, P, dot) {
  const L = LEAF[P] || LEAF.green;
  for (let i = 0; i < 3; i++) blob(b, tint(pick(L), { c2: L[1], mx: .6, j: .1, a: .7, b: 1.25, y0: 0, y1: 1 }), .5, (i - 1) * .65, .45 + (i === 1 ? .1 : 0), rr(-.06, .06), 1.1, .85, .85, i === 1 ? 1 : 0, .3);
  blob(b, tint(L[1], { c2: L[0], mx: .5, j: .1 }), .3, 0, .95, 0, 1.6, .5, .8, 0, .3);
  dots(b, DOT[dot], 9, 0, .55, 0, .85, .6);
}
function reeds(b, P) {
  const L = LEAF[P] || LEAF.lime;
  for (let i = 0; i < 9; i++) { const a = R() * 6.28, d = R() * .22, h = rr(.9, 1.6); cone(b, tint(pick(L), { c2: L[1], mx: .5, j: .1, a: .7, b: 1.2, y0: 0, y1: 1.6 }), .03, h, 3, Math.cos(a) * d, 0, Math.sin(a) * d, rr(.05, .25), a, 0, 0, true); if (i % 3 == 0) cyl(b, tint(0x5a3a1e, { j: .1 }), .05, .05, .22, 5, Math.cos(a) * d + Math.sin(a) * h * .1, h * .9, Math.sin(a) * d, 0, 0, 0); }
}
function shroom(b, P) {
  const cap = { red: 0xcc3030, brown: 0x9a6a3c, orange: 0xe88a30, white: 0xe8e0d0 }[P] || 0xcc3030;
  for (let i = 0; i < 4; i++) {
    const s = i ? rr(.5, .85) : 1, a = i * 1.7 + .3, x = i ? Math.cos(a) * .3 : 0, z = i ? Math.sin(a) * .3 : 0;
    cyl(b, tint(0xefe6d2, { j: .06, a: .85, b: 1.1, y0: 0, y1: .3 }), .035 * s, .055 * s, .2 * s, 6, x, 0, z, 0, 0, 0);
    const g = new THREE.SphereGeometry(.17 * s, 7, 2, 0, 6.2832, 0, Math.PI / 2); put(b, g, tint(cap, { c2: 0x000000, mx: .12, j: .07, a: .8, b: 1.15, y0: .15, y1: .35 }), x, .17 * s, z, 1, .8, 1, 0, 0, 0, 0);
    if (P === 'red') for (let k = 0; k < 3; k++) { const aa = k * 2.1 + i, rd = .1 * s; bump(b, tint(0xfaf6ec, { j: .02, a: 1, b: 1 }), .03, x + Math.cos(aa) * rd, .17 * s + .1 * s * (k % 2 ? .6 : 1.0), z + Math.sin(aa) * rd, 1, .6, 1, 0); }
  }
  bump(b, tint(0x4f7a3a, { c2: 0x2e5a28, mx: .5, j: .1 }), .18, 0, 0, 0, 1.6, .25, 1.6, .3);
}

/* ---------- flowers & grass ---------- */
function flowerPatch(b, kind, col) {
  const lf = tint(0x3f8a38, { c2: 0x66b048, mx: .6, j: .1, a: .7, b: 1.2, y0: 0, y1: .5 });
  const n = kind === 'sunflower' ? 2 : 4;
  for (let i = 0; i < n; i++) {
    const a = R() * 6.28, d = R() * .38, x = Math.cos(a) * d, z = Math.sin(a) * d, h = (kind === 'sunflower' ? rr(.8, 1.1) : kind === 'lavender' ? rr(.4, .6) : rr(.3, .5)), lean = rr(-.15, .15);
    cyl(b, lf, .012, .02, h, 4, x, 0, z, lean, a, 0);
    const hx = x + Math.sin(a) * Math.sin(lean) * h * 0, hy = h * .98, c = tint(col, { j: .05, a: .95, b: 1.15 });
    if (kind === 'daisy') { cyl(b, tint(col, { j: .04, a: 1, b: 1.1 }), .11, .11, .018, 6, hx, hy, z, 0, R(), 0, true); blob(b, tint(0xf2c01c, { j: .05 }), .035, hx, hy + .02, z, 1, .8, 1, 0, 0); }
    else if (kind === 'tulip') { cone(b, c, .06, .14, 5, hx, hy - .12, z, Math.PI, 0, 0, .05, false); cone(b, c, .06, .06, 5, hx, hy - .02, z, 0, .5, 0, .05, false); }
    else if (kind === 'lavender') { for (let k = 0; k < 4; k++) cone(b, tint(col, { j: .08, a: .85, b: 1.2 }), .045 - k * .008, .11, 4, hx, hy - .22 + k * .09, z, 0, k, 0, 0); }
    else if (kind === 'bell') { for (let k = 0; k < 3; k++) cone(b, c, .05, .1, 5, hx + (k - 1) * .045, hy - .1 - k * .03, z, Math.PI * .95, k, 0, 0); }
    else { cyl(b, tint(col, { j: .05, a: 1, b: 1.1 }), .24, .24, .02, 8, hx, hy, z, .35, 0, 0, true); cyl(b, tint(0x5a3a1a, { c2: 0x2e1c0a, mx: .5, j: .08 }), .13, .13, .04, 8, hx, hy + .01, z + .01, .35, 0, 0, true); }
    if (i < 2) cone(b, lf, .05, .28, 3, x, .0, z, 1.0 + R() * .3, R() * 6, 0, .05, true);
  }
}
function grassTuft(b, P) {
  const G = GRASS[P] || GRASS.green;
  for (let i = 0; i < 5; i++) { const a = R() * 6.28, d = R() * .1; cone(b, tint(pick(G), { c2: G[1], mx: .5, j: .08, a: .7, b: 1.25, y0: 0, y1: .7 }), .035, rr(.3, .7), 3, Math.cos(a) * d, 0, Math.sin(a) * d, rr(.1, .5), a, 0, 0, true); }
}

/* ---------- rocks ---------- */
function boulder(b, P, big) {
  const C = ROCK[P] || ROCK.grey, r = big ? 1.05 : .7;
  const t = tint(C[0], { c2: C[1], mx: .5, j: .1, a: .72, b: 1.18, y0: 0, y1: r * 1.4, band: .07, bf: 11, moss: P === 'grey' || P === 'mossy' ? 0x5a8a3a : 0x6a8a46, ma: P === 'mossy' ? .25 : .55 });
  blob(b, t, r, 0, r * .45, 0, 1.1, .7, 1, 1, .4);
  blob(b, t, r * .55, r * .8, r * .2, r * .3, 1, .7, 1, 0, .4);
  const cr = tint(C[1], { j: .04, a: .5, b: .7 }); box(b, cr, .02, r * .5, r * .5, r * .2, r * .6, r * .1, .3, .6, .4);
  for (let i = 0; i < 3; i++) { const a = R() * 6.28; blob(b, tint(C[0], { c2: C[1], mx: .6, j: .1 }), rr(.1, .17), Math.cos(a) * r * 1.3, .06, Math.sin(a) * r * 1.3, 1, .6, 1, 0, .4); }
}
function rockCluster(b, P) {
  const C = ROCK[P] || ROCK.grey;
  [[0, 0, .55], [.65, .2, .38], [-.45, .45, .3]].forEach(([x, z, r]) => blob(b, tint(C[0], { c2: C[1], mx: .6, j: .1, a: .72, b: 1.2, y0: 0, y1: r * 1.4, band: .06, bf: 14, moss: 0x5a8a3a, ma: .6 }), r, x, r * .4, z, 1.1, .7, 1, 1, .4));
}
function slab(b, P) {
  const C = ROCK[P] || ROCK.grey, g = new THREE.BoxGeometry(1.6, .35, 1.1, 3, 1, 2);
  put(b, g, tint(C[0], { c2: C[1], mx: .5, j: .1, a: .75, b: 1.15, moss: 0x5a8a3a, ma: .5 }), 0, .17, 0, 1, 1, 1, .03, .3, .04, .3);
  blob(b, tint(C[0], { c2: C[1], mx: .6, j: .1 }), .3, .7, .12, .5, 1, .6, 1, 0, .4);
}
export const GLOWC = 0xffb347;
function standing(b, P) {
  const C = ROCK[P] || ROCK.slate, t = tint(C[0], { c2: C[1], mx: .5, j: .1, a: .7, b: 1.2, y0: 0, y1: 2.4, band: .06, bf: 9, moss: 0x5a8a3a, ma: .35 });
  cyl(b, t, .32, .55, 2.4, 5, 0, -.05, 0, .04, .5, -.03, true); put(b, new THREE.IcosahedronGeometry(.5, 0), t, .5, .25, .3, 1, .5, 1, 0, 0, 0, .3); put(b, new THREE.IcosahedronGeometry(.4, 0), t, -.55, .2, -.2, 1, .6, 1, 0, 0, 0, .3);
  return glowStrip;
}
function glowStrip(g) { const t = tint(0x7fe8d0, { j: 0, a: 1, b: 1 }); for (let i = 0; i < 4; i++) box(g, t, .12, .05, .04, 0, .6 + i * .35, .3 + i * -.02, 0, 0, 0); }

/* ---------- props ---------- */
function barrel(b, W) {
  const w = tint(W[0], { c2: W[1], mx: .6, j: .13, a: .78, b: 1.1, y0: 0, y1: .95 }), ir = tint(IRON, { j: .06, a: .9, b: 1.1 });
  cyl(b, w, .46, .36, .5, 12, 0, 0, 0); cyl(b, w, .36, .46, .5, 12, 0, .5, 0);
  for (const y of [.1, .42, .6, .9]) { const rd = y > .3 && y < .7 ? .48 : .39; cyl(b, ir, rd + (y === .42 || y === .6 ? 0 : 0), rd, .06, 12, 0, y - .03, 0); }
  cyl(b, tint(W[1], { j: .1, a: 1, b: 1.1 }), .36, .36, .04, 12, 0, 1.0, 0, 0, 0, 0, true);
  box(b, tint(W[0], { j: .1 }), .7, .02, .1, 0, 1.04, 0, 0, .4, 0); box(b, tint(W[0], { j: .1 }), .7, .02, .1, 0, 1.04, .15, 0, .4, 0);
  for (let i = 0; i < 4; i++) nail(b, ir, Math.cos(i * 1.57 + .8) * .3, 1.05, Math.sin(i * 1.57 + .8) * .3);
}
function crate(b, W, moss) {
  const f = tint(W[1], { j: .1, a: .85, b: 1.05 }), ir = tint(IRON, { j: .05, a: 1, b: 1 });
  box(b, tint(W[1], { j: .05, a: .6, b: .8 }), .94, .94, .94, 0, .5, 0, 0, 0, 0);
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) box(b, f, .13, 1.0, .13, sx * .47, .5, sz * .47, 0, 0, 0);
  for (let s = 0; s < 4; s++) { const a = s * Math.PI / 2, dx = Math.sin(a), dz = Math.cos(a);
    for (let i = 0; i < 3; i++) put(b, new THREE.BoxGeometry(.96, .28, .05), tint(W[0], { c2: W[1], mx: .5, j: .1, a: .85, b: 1.1 }), dx * .475, .2 + i * .3, dz * .475, 1, 1, 1, 0, a, 0, 0);
    if (s < 2) put(b, new THREE.BoxGeometry(.1, 1.1, .05), f, dx * .5, .5, dz * .5, 1, 1, 1, 0, a, Math.PI / 4 * (s ? -1 : 1) * .9, 0);
    if (s < 2) for (const px of [-.4, .4]) for (const py of [.1, .85]) nail(b, ir, dx * .52 + dz * px, py, dz * .52);
  }
  for (let i = 0; i < 3; i++) box(b, tint(W[0], { c2: W[1], mx: .5, j: .12, a: .95, b: 1.1 }), 1.0, .06, .3, 0, 1.0, (i - 1) * .33, 0, 0, 0);
  if (moss) { cyl(b, tint(0x5a8a3a, { c2: 0x3e6a2a, mx: .6, j: .15 }), .3, .32, .05, 6, .22, 1.03, .18, 0, 0, 0, true); blob(b, tint(0x4e7a32, { j: .1 }), .15, -.3, 1.0, -.2, 1.2, .3, 1, 0, .3); }
}
function lamp(b, W, g) {
  const ir = tint(IRON, { j: .06, a: .8, b: 1.15, y0: 0, y1: 4 });
  const st = tint(0x8a8d94, { c2: 0x5a5e66, mx: .5, j: .12, a: .8, b: 1.1, moss: 0x5a8a3a, ma: .7 });
  cyl(b, st, .22, .3, .5, 6, 0, 0, 0); cyl(b, st, .16, .22, .2, 6, 0, .5, 0, 0, 0, 0, true);
  cyl(b, ir, .05, .08, 2.9, 6, 0, .7, 0); cyl(b, ir, .11, .11, .08, 6, 0, 1.0, 0, 0, 0, 0, true); cyl(b, ir, .1, .1, .06, 6, 0, 3.0, 0, 0, 0, 0, true);
  cyl(b, ir, .03, .03, .6, 5, 0, 2.7, 0, 0, 0, Math.PI / 2 * 1.0); cyl(b, ir, .025, .025, .45, 5, .0, 2.55, 0, 0, 0, -.8);
  for (let i = 0; i < 2; i++) cyl(b, ir, .02, .02, .28, 5, .04, 2.0 + i * .3, 0, 0, 0, i ? .9 : -.9);
  const lx = .6;
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) box(b, ir, .03, .34, .03, lx + sx * .1, 2.62, sz * .1, 0, 0, 0);
  box(b, ir, .26, .04, .26, lx, 2.6, 0, 0, 0, 0); cone(b, ir, .22, .22, 4, lx, 2.95, 0, 0, Math.PI / 4, 0, 0); blob(b, ir, .04, lx, 3.2, 0, 1, 1, 1, 0, 0);
  if (g) { box(g, tint(GLOWC, { j: .03, a: 1, b: 1 }), .17, .26, .17, lx, 2.63, 0, 0, 0, 0); box(g, tint(0xfff0b0, { j: 0, a: 1, b: 1 }), .09, .14, .09, lx, 2.69, 0, 0, 0, 0); }
}
function well(b, W) {
  const st = tint(0x9a9ca2, { c2: 0x6a6e76, mx: .6, j: .16, a: .72, b: 1.15, y0: 0, y1: 1, moss: 0x5a8a3a, ma: .5 }), wd = tint(W[0], { c2: W[1], mx: .5, j: .1 });
  for (let i = 0; i < 2; i++) cyl(b, st, 1.0 - i * .02, 1.06, .45, 10, 0, i * .45, 0);
  cyl(b, tint(0xb0b2b8, { j: .12, a: 1, b: 1.1 }), 1.12, 1.12, .12, 10, 0, .9, 0, 0, 0, 0, true); cyl(b, tint(0x2a5a7a, { j: .04, a: 1, b: 1 }), .8, .8, .02, 10, 0, .72, 0, 0, 0, 0, true);
  for (let i = 0; i < 5; i++) { const a = i * 1.26 + .3; blob(b, tint(0x5a8a3a, { j: .12 }), .13, Math.cos(a) * 1.05, .1, Math.sin(a) * 1.05, 1.4, .4, 1.4, 0, .3); }
  for (const s of [-1, 1]) box(b, wd, .16, 2.2, .16, s * .95, 1.95, 0, 0, 0, 0);
  cyl(b, wd, .07, .07, 2.1, 6, -1.05, 2.15, 0, 0, 0, -Math.PI / 2); cyl(b, tint(IRON, {}), .02, .02, .35, 5, .98, 2.0, 0, 0, 0, 0.0);
  for (const s of [-1, 1]) put(b, new THREE.BoxGeometry(1.5, .08, 1.5), tint(0x9a4a30, { c2: 0x6a2c1e, mx: .5, j: .14, a: .8, b: 1.15 }), s * .5, 3.15, 0, 1, 1, 1, 0, 0, -s * .55, 0);
  box(b, wd, .08, .08, 1.5, 0, 3.55, 0, 0, 0, 0);
  cyl(b, tint(IRON, {}), .015, .015, .8, 4, 0, 1.55, 0, 0, 0, 0); cyl(b, tint(W[0], { c2: W[1], mx: .5, j: .1 }), .15, .12, .2, 8, 0, 1.3, 0); cyl(b, tint(IRON, {}), .16, .16, .03, 8, 0, 1.38, 0);
}
function sign(b, W) {
  const wd = tint(W[0], { c2: W[1], mx: .5, j: .1 }), ir = tint(IRON, {}), tx = tint(0x2a1a0c, { j: .03 });
  cyl(b, tint(W[1], { j: .12, a: .8, b: 1.1 }), .09, .12, 2.1, 6, 0, 0, 0); cone(b, wd, .1, .12, 6, 0, 2.1, 0, 0, 0, 0, 0);
  [[1.6, .5, .3], [1.2, -.5, 3.5]].forEach(([y, d, ry]) => { put(b, new THREE.BoxGeometry(.9, .26, .05), wd, d * .5, y, .1, 1, 1, 1, 0, ry * .1, 0, 0); box(b, wd, .2, .26, .05, d * .98, y, .1, 0, 0, Math.PI / 4); for (let i = 0; i < 3; i++) box(b, tx, .5 - i * .12, .03, .01, d * .45, y + (1 - i) * .06, .14, 0, 0, 0); box(b, ir, .03, .03, .03, d * .1, y, .14, 0, 0, 0); });
  blob(b, tint(0x5a8a3a, { j: .1 }), .12, .1, .03, .1, 1.5, .4, 1.5, 0, .3);
}
function noticeboard(b, W) {
  const wd = tint(W[0], { c2: W[1], mx: .5, j: .1 }), ir = tint(IRON, {});
  for (const s of [-1, 1]) cyl(b, tint(W[1], { j: .12 }), .08, .1, 2.0, 6, s * .75, 0, 0);
  box(b, wd, 1.7, 1.0, .08, 0, 1.3, 0, 0, 0, 0); box(b, tint(W[1], { j: .1 }), 1.9, .1, .14, 0, 1.85, 0, 0, 0, 0); put(b, new THREE.BoxGeometry(1.9, .08, .5), tint(0x9a4a30, { c2: 0x6a2c1e, mx: .5, j: .1 }), 0, 2.05, .02, 1, 1, 1, .4, 0, 0, 0);
  [[-.45, 1.45, .2], [.1, 1.4, -.1], [.5, 1.2, .15], [-.3, 1.05, -.2]].forEach(([x, y, r]) => { box(b, tint(0xf0e6c8, { c2: 0xd8c898, mx: .5, j: .04, a: 1, b: 1.05 }), .32, .4, .02, x, y, .06, 0, 0, r); box(b, ir, .03, .03, .02, x, y + .15, .08, 0, 0, 0); });
}
function fenceUnit(b, W) {
  const wd = tint(W[0], { c2: W[1], mx: .6, j: .13, a: .8, b: 1.1, y0: 0, y1: 1.2, moss: 0x5a8a3a, ma: .85 });
  box(b, wd, .13, 1.05, .13, 0, .52, 0, 0, 0, 0); cone(b, wd, .1, .18, 4, 0, 1.03, 0, 0, Math.PI / 4, 0, 0);
  for (const y of [.35, .75]) box(b, tint(W[0], { c2: W[1], mx: .6, j: .13 }), 1.2, .09, .05, .6, y + R() * .02, .02, 0, 0, (R() - .5) * .04);
  box(b, tint(IRON, {}), .03, .03, .03, .05, .35, .06, 0, 0, 0); box(b, tint(IRON, {}), .03, .03, .03, .05, .75, .06, 0, 0, 0);
}
function bench(b, W) {
  const wd = tint(W[0], { c2: W[1], mx: .5, j: .1 }), dk = tint(W[1], { j: .1 });
  for (let i = 0; i < 3; i++) box(b, wd, 1.5, .05, .14, 0, .5, (i - 1) * .16, 0, 0, 0);
  for (let i = 0; i < 2; i++) box(b, wd, 1.5, .09, .04, 0, .85 + i * .17, -.28, -.15, 0, 0);
  for (const s of [-1, 1]) { box(b, dk, .07, .5, .5, s * .65, .25, 0, 0, 0, 0); box(b, dk, .06, .55, .06, s * .65, .6, -.26, -.15, 0, 0); }
}
function hay(b) {
  const t = tint(0xd8b14a, { c2: 0xa88a2e, mx: .7, j: .12, a: .8, b: 1.15, y0: 0, y1: 1 });
  cyl(b, t, .5, .5, 1.0, 9, 0, .5, -.5, Math.PI / 2, 0, 0, true); const bd = tint(0x7a5a2a, { j: .08 });
  for (const z of [-.3, .3]) cyl(b, bd, .52, .52, .05, 9, 0, .5, z - .5, Math.PI / 2, 0, 0, true);
  for (let i = 0; i < 8; i++) { const a = R() * 6.28; cone(b, t, .02, .25, 3, Math.cos(a) * .48, .5 + Math.sin(a) * .48, rr(-.45, .45), Math.PI / 2 - a * 0 + 0, a, 0, 0, true); }
}
function logs(b, W) {
  const w = tint(W[0], { c2: W[1], mx: .6, j: .12, a: .8, b: 1.1 }), ring = tint(0xd8b078, { c2: 0xa88050, mx: .5, j: .06, a: 1, b: 1.1 });
  [[-.3, .2], [.3, .2], [0, .55]].forEach(([x, y], i) => { cyl(b, w, .2, .2, 1.4, 8, x, y, -.7, Math.PI / 2, 0, 0, true); cyl(b, ring, .17, .17, .02, 8, x, y, .705, Math.PI / 2, 0, 0, true); cyl(b, ring, .17, .17, .02, 8, x, y, -.715, Math.PI / 2, 0, 0, true); });
  cyl(b, tint(0x5a3a22, { j: .1 }), .03, .06, .35, 4, .1, .7, .1, 0, 0, .6);
}
function stump(b, W) {
  const w = tint(W[1], { c2: W[0], mx: .5, j: .13, a: .78, b: 1.05, y0: 0, y1: .7, moss: 0x5a8a3a, ma: .4 });
  cyl(b, w, .38, .5, .65, 8, 0, 0, 0); roots(b, [W[1], W[1]], 5, .5, -.1);
  for (let i = 0; i < 3; i++) cyl(b, tint(i % 2 ? 0xc89a60 : 0xa87a44, { j: .05, a: 1, b: 1.05 }), .36 - i * .11, .36 - i * .11, .03 + i * .004, 8, 0, .64 + i * .005, 0, 0, 0, 0, true);
  blob(b, tint(0x5a8a3a, { j: .1 }), .15, .3, .55, .2, 1.4, .4, 1.4, 0, .3);
  const g = tint(0xe8a040, { j: .05, a: 1, b: 1.1 }); cyl(b, tint(0xefe6d2, { j: .05 }), .02, .03, .12, 5, -.4, .3, .2, .3, 0, 0); put(b, new THREE.SphereGeometry(.07, 6, 3, 0, 6.28, 0, Math.PI / 2), g, -.4, .42, .2, 1, .8, 1, 0, 0, 0, 0);
}
function cabbages(b) {
  box(b, tint(0x5a4028, { c2: 0x3e2c1a, mx: .6, j: .15, a: .85, b: 1.05 }), 3.0, .14, .7, 0, .07, 0, 0, 0, 0);
  for (let i = 0; i < 5; i++) { const x = (i - 2) * .6; blob(b, tint(0x78b04a, { c2: 0xb8d878, mx: .7, j: .1, a: .8, b: 1.25, y0: .1, y1: .6 }), .26, x, .3, rr(-.06, .06), 1.2, .8, 1.2, 0, .3); bump(b, tint(0x4e8a38, { j: .1, a: .8, b: 1 }), .2, x, .22, 0, 1.6, .5, 1.6, .3); }
}

/* ---------- catalog ---------- */
const WP = Object.keys(WOOD), RP = Object.keys(ROCK), BP = Object.keys(BARK);
const barkOf = (p, def) => BARK[p] || BARK[def];
export const CATALOG = {
  trees: {
    oak: { pals: ['green', 'deep', 'lime', 'autumn', 'red', 'yellow'], fn: (b, p) => oak(b, p, BARK.brown) },
    pine: { pals: ['deep', 'spruce', 'green'], fn: (b, p) => pine(b, p, BARK.dark) },
    birch: { pals: ['lime', 'yellow', 'autumn', 'green'], fn: (b, p) => birch(b, p) },
    cypress: { pals: ['deep', 'green', 'spruce'], fn: (b, p) => cypress(b, p, BARK.dark) },
    apple: { pals: ['green', 'blossom', 'autumn'], fn: (b, p) => apple(b, p, BARK.brown) },
    dead: { pals: ['dark', 'grey', 'pale'], fn: (b, p) => dead(b, p, BARK[p]) }
  },
  bushes: {
    round: { pals: ['green:red', 'deep:blue', 'lime:pink', 'green:white', 'autumn:orange', 'deep:purple', 'yellow:yellow'], fn: (b, p) => { const [l, d] = p.split(':'); bushRound(b, l, d); } },
    hedge: { pals: ['deep:white', 'green:pink', 'lime:yellow', 'deep:none'], fn: (b, p) => { const [l, d] = p.split(':'); bushHedge(b, l, d); } },
    spiky: { pals: ['green', 'deep', 'lime', 'autumn', 'red'], fn: (b, p) => bushSpiky(b, p) },
    reeds: { pals: ['lime', 'green', 'yellow'], fn: (b, p) => reeds(b, p) },
    mushrooms: { pals: ['red', 'brown', 'orange', 'white'], fn: (b, p) => shroom(b, p) }
  },
  flowers: {
    daisy: { pals: ['white', 'pink', 'yellow'], fn: (b, p) => flowerPatch(b, 'daisy', FLOWER[p]) },
    tulip: { pals: ['red', 'yellow', 'pink', 'purple', 'orange'], fn: (b, p) => flowerPatch(b, 'tulip', FLOWER[p]) },
    lavender: { pals: ['purple', 'blue'], fn: (b, p) => flowerPatch(b, 'lavender', FLOWER[p]) },
    bellflower: { pals: ['blue', 'white', 'pink'], fn: (b, p) => flowerPatch(b, 'bell', FLOWER[p]) },
    sunflower: { pals: ['yellow', 'orange'], fn: (b, p) => flowerPatch(b, 'sunflower', FLOWER[p]) },
    grass: { pals: ['green', 'lush', 'dry'], fn: (b, p) => grassTuft(b, p) }
  },
  rocks: {
    boulder: { pals: RP, fn: (b, p) => boulder(b, p, true) },
    stone: { pals: RP, fn: (b, p) => boulder(b, p, false) },
    cluster: { pals: RP, fn: (b, p) => rockCluster(b, p) },
    slab: { pals: RP, fn: (b, p) => slab(b, p) },
    standing: { pals: ['slate', 'grey', 'mossy'], glow: true, fn: (b, p, g) => { standing(b, p); glowStrip(g); } }
  },
  props: {
    barrel: { pals: WP, fn: (b, p) => barrel(b, WOOD[p]) },
    crate: { pals: WP, fn: (b, p) => crate(b, WOOD[p], p === 'weathered' || p === 'dark') },
    lamp: { pals: ['oak', 'dark'], glow: true, fn: (b, p, g) => lamp(b, WOOD[p], g) },
    well: { pals: ['oak', 'pine', 'weathered'], fn: (b, p) => well(b, WOOD[p]) },
    signpost: { pals: ['oak', 'pine', 'weathered'], fn: (b, p) => sign(b, WOOD[p]) },
    noticeboard: { pals: ['oak', 'pine', 'dark'], fn: (b, p) => noticeboard(b, WOOD[p]) },
    fence: { pals: ['oak', 'pine', 'weathered', 'dark'], fn: (b, p) => fenceUnit(b, WOOD[p]) },
    bench: { pals: ['oak', 'pine', 'weathered'], fn: (b, p) => bench(b, WOOD[p]) },
    haybale: { pals: ['straw'], fn: (b) => hay(b) },
    logs: { pals: ['oak', 'pine', 'dark'], fn: (b, p) => logs(b, WOOD[p]) },
    stump: { pals: ['oak', 'dark', 'weathered'], fn: (b, p) => stump(b, WOOD[p]) },
    cabbages: { pals: ['patch'], fn: (b) => cabbages(b) }
  }
};
export const KINDS = Object.keys(CATALOG);

export function makeDetailTexture() {
  const S = 64, c = document.createElement('canvas'); c.width = c.height = S; const g = c.getContext('2d'); let s = 5; const r = () => (s = (s * 16807) % 2147483647) / 2147483647;
  g.fillStyle = '#ececec'; g.fillRect(0, 0, S, S);
  for (let i = 0; i < 300; i++) { const v = 170 + r() * 85 | 0; g.fillStyle = `rgba(${v},${v},${v},.5)`; g.fillRect(r() * S, r() * S, 1 + r() * 2, 1 + r() * 4); }
  for (let i = 0; i < 18; i++) { g.strokeStyle = `rgba(90,90,90,${.1 + r() * .14})`; g.lineWidth = 1; const x = r() * S; g.beginPath(); g.moveTo(x, 0); g.lineTo(x + r() * 3 - 1.5, S); g.stroke(); }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = 2; return t;
}
export function makeMaterials(map) { return { solid: new THREE.MeshLambertMaterial({ vertexColors: true, map }), glow: new THREE.MeshBasicMaterial({ vertexColors: true }) }; }

function finish(bld, uv) {
  if (!bld || !bld.p.length) return null;
  const g = new THREE.BufferGeometry(), n = bld.p.length / 3;
  g.setAttribute('position', new THREE.Float32BufferAttribute(bld.p, 3)); g.setAttribute('normal', new THREE.Float32BufferAttribute(bld.n, 3)); g.setAttribute('color', new THREE.Float32BufferAttribute(bld.c, 3));
  if (uv) { const u = new Float32Array(n * 2); for (let i = 0; i < n; i++) { u[i * 2] = (bld.p[i * 3] + bld.p[i * 3 + 2] * .7) * .8; u[i * 2 + 1] = bld.p[i * 3 + 1] * .8; } g.setAttribute('uv', new THREE.BufferAttribute(u, 2)); }
  g.computeBoundingBox(); g.computeBoundingSphere(); return g;
}
/* Build one variant. Returns { geo, glow, h, r, tris } */
export function makeVariant(kind, name, pal, seed, lod) {
  LOD = lod ? 1 : 0;
  const e = CATALOG[kind][name]; if (!e) throw new Error('no variant ' + kind + '/' + name);
  setSeed((seed || 1) * 977 + name.length * 31 + (pal || '').length * 7);
  const b = new B(), g = e.glow ? new B() : null; e.fn(b, pal || e.pals[0], g); LOD = 0;
  const geo = finish(b, true), glow = finish(g, false), bb = geo.boundingBox;
  return { geo, glow, h: bb.max.y, r: Math.max(bb.max.x - bb.min.x, bb.max.z - bb.min.z) / 2, tris: b.p.length / 9 + (g ? g.p.length / 9 : 0) };
}

/* ---------- scatter: merge a whole village mix into 3 meshes ---------- */
export class Acc { constructor() { this.p = []; this.n = []; this.c = []; }
  add(g, x, y, z, ry, s) {
    const P = g.attributes.position.array, N = g.attributes.normal.array, C = g.attributes.color.array, cs = Math.cos(ry), sn = Math.sin(ry);
    for (let i = 0; i < P.length; i += 3) { const px = P[i] * s, pz = P[i + 2] * s; this.p.push(px * cs + pz * sn + x, P[i + 1] * s + y, -px * sn + pz * cs + z); this.n.push(N[i] * cs + N[i + 2] * sn, N[i + 1], -N[i] * sn + N[i + 2] * cs); this.c.push(C[i], C[i + 1], C[i + 2]); }
  }
  geo(uv) { return finish(this, uv); }
}
export function scatterWorld(o) {
  const WORLD = o.world || 32, cols = o.colliders, rnd = o.rnd || Math.random, A = { cast: new Acc(), plain: new Acc(), glow: new Acc() };
  const cache = new Map(), stats = { trees: 0, bushes: 0, flowers: 0, rocks: 0, props: 0, kinds: {} };
  const rp = a => a[Math.floor(rnd() * a.length) % a.length], rf = (a, b) => a + (b - a) * rnd();
  function variant(kind, name, pal, lod) {
    const slot = Math.floor(rnd() * 2), key = kind + '/' + name + '/' + pal + '/' + slot + (lod ? 'L' : '');
    if (!cache.has(key)) cache.set(key, makeVariant(kind, name, pal, slot + 3, lod));
    return cache.get(key);
  }
  function place(kind, name, pal, x, z, ry, s, lay, lod) {
    const v = variant(kind, name, pal, lod), y = o.heightAt ? o.heightAt(x, z) : 0;
    A[lay].add(v.geo, x, y, z, ry, s); if (v.glow) A.glow.add(v.glow, x, y, z, ry, s);
    stats[kind]++; const k = kind + '/' + name + ':' + pal; stats.kinds[k] = (stats.kinds[k] || 0) + 1; return v;
  }
  const free = (x, z, m) => {
    for (const c of cols) { if (c.type === 'box') { if (x > c.minX - m && x < c.maxX + m && z > c.minZ - m && z < c.maxZ + m) return false; } else if (Math.hypot(x - c.x, z - c.z) < c.r + m) return false; }
    return true;
  };
  const onPath = (x, z, m) => Math.hypot(x, z) < 10.5 + m || Math.abs(x) < 3 + m || Math.abs(z) < 2.6 + m;
  const taken = [];
  const clear = (x, z, d) => { for (const t of taken) if (Math.hypot(t[0] - x, t[1] - z) < d + t[2]) return false; return true; };
  const claim = (x, z, r) => taken.push([x, z, r]);
  const circ = (x, z, r) => { cols.push({ type: 'circle', x, z, r }); };
  const boxc = (x, z, w, d) => { cols.push({ type: 'box', minX: x - w / 2, maxX: x + w / 2, minZ: z - d / 2, maxZ: z + d / 2 }); };

  /* fixed props: lamps, well, signs, benches, crates, barrels, garden */
  for (const [x, z] of [[3.2, 13], [-3.2, 13], [3.2, 22], [-3.2, 22], [3.2, -10], [-3.2, -10], [7.4, 7.4], [-7.4, 7.4], [7.4, -7.4], [-7.4, -7.4], [3.2, 29], [-3.2, 29]]) { if (free(x, z, .2)) { place('props', 'lamp', rp(['oak', 'dark']), x, z, x < 0 ? Math.PI : 0, 1, 'cast'); circ(x, z, .25); claim(x, z, .3); } }
  place('props', 'well', 'oak', -8.5, 17.5, 0.4, 1, 'cast'); circ(-8.5, 17.5, 1.25); claim(-8.5, 17.5, 1.6);
  place('props', 'signpost', 'oak', 3.9, 6.2, -0.2, 1, 'cast'); circ(3.9, 6.2, .25); claim(3.9, 6.2, .5);
  place('props', 'noticeboard', 'oak', -4.4, 10.6, 0, 1, 'cast'); boxc(-4.4, 10.6, 1.8, .4); claim(-4.4, 10.6, 1);
  place('props', 'bench', 'oak', 6.6, 0, -Math.PI / 2, 1, 'cast'); boxc(6.6, 0, .5, 1.5); place('props', 'bench', 'pine', -6.6, 0, Math.PI / 2, 1, 'cast'); boxc(-6.6, 0, .5, 1.5);
  for (const [x, z, r] of [[-8.2, -4.2, .3], [-9.4, -3.6, 1.1], [9.2, -5.8, .5], [10.4, -6.2, 2], [8.4, 6.6, .2], [-9.0, -2.4, 3]]) { const crateP = rp(['oak', 'pine', 'weathered', 'dark']); if (r < 1.5 || true) { if (rnd() < .5) place('props', 'crate', crateP, x, z, r, 1, 'cast'), boxc(x, z, 1.05, 1.05); else place('props', 'barrel', rp(['oak', 'dark', 'red']), x, z, r, 1, 'cast'), circ(x, z, .5); claim(x, z, .8); } }
  place('props', 'haybale', 'straw', 21.5, 18, .5, 1, 'cast'); circ(21.5, 18, .8); place('props', 'haybale', 'straw', 22.7, 19.2, 1.3, .9, 'cast'); circ(22.7, 19.2, .7);
  /* fenced garden at east */
  { const gx = 24, gz = 12, w = 6, d = 5; boxc(gx, gz, w, .3);
    for (let i = 0; i * 1.2 < w; i++) { place('props', 'fence', 'oak', gx - w / 2 + i * 1.2, gz - d / 2, 0, 1, 'cast'); if (i) place('props', 'fence', 'oak', gx - w / 2 + i * 1.2, gz + d / 2, 0, 1, 'cast'); }
    for (let i = 0; i * 1.2 < d; i++) { place('props', 'fence', 'oak', gx - w / 2, gz - d / 2 + i * 1.2 + 1.2, Math.PI / 2 * -1, 1, 'cast'); place('props', 'fence', 'oak', gx + w / 2, gz - d / 2 + i * 1.2, Math.PI / 2, 1, 'cast'); }
    boxc(gx, gz - d / 2, w + 1, .3); boxc(gx, gz + d / 2, w + 1, .3); boxc(gx - w / 2, gz, .3, d); boxc(gx + w / 2, gz, .3, d);
    for (let i = 0; i < 3; i++) place('props', 'cabbages', 'patch', gx, gz - 1.3 + i * 1.3, 0, 1, 'cast');
    for (let i = 0; i < 4; i++) place('flowers', 'sunflower', rp(['yellow', 'yellow', 'orange']), gx - 2.6 + i * 1.7, gz - d / 2 - .6, 0, 1.1, 'plain');
    claim(gx, gz, 5); }
  place('props', 'logs', 'oak', -22.5, 22, .5, 1, 'cast'); boxc(-22.5, 22, 1.4, 1.2); place('props', 'stump', 'oak', -19, 24, 0, 1, 'cast'); circ(-19, 24, .5); place('props', 'stump', 'dark', 17, -22, 1, 1.1, 'cast'); circ(17, -22, .55); claim(-22.5, 22, 1.2);

  /* trees: patchy palette by region, species by weights */
  const grove = (x, z) => { const h = hash3(Math.floor(x / 14), Math.floor(z / 14), 0, 3); return h; };
  const OAKP = ['green', 'deep', 'lime', 'autumn', 'red', 'yellow'];
  function treeAt(x, z, outer) {
    const h = grove(x, z), r = rnd();
    let sp, pal;
    if (r < .26) { sp = 'oak'; pal = rnd() < .55 ? (h < .33 ? 'green' : h < .55 ? 'deep' : h < .75 ? 'autumn' : 'yellow') : rp(OAKP); }
    else if (r < .5) { sp = 'pine'; pal = rp(['deep', 'deep', 'spruce', 'green']); }
    else if (r < .66) { sp = 'birch'; pal = rnd() < .5 ? (h < .5 ? 'lime' : 'yellow') : rp(['lime', 'yellow', 'autumn', 'green']); }
    else if (r < .78) { sp = 'cypress'; pal = rp(['deep', 'green', 'spruce']); }
    else if (r < .9) { sp = 'apple'; pal = outer ? 'green' : rp(['green', 'blossom', 'autumn']); }
    else { sp = 'dead'; pal = rp(['dark', 'grey', 'pale']); }
    return [sp, pal];
  }
  const trees = [];
  let guard = 0;
  while (trees.length < (o.trees || 56) && guard++ < 6000) {
    const x = (rnd() * 2 - 1) * (WORLD - 3), z = (rnd() * 2 - 1) * (WORLD - 3);
    if (onPath(x, z, .7) || !free(x, z, 2.2) || !clear(x, z, 2.6)) continue;
    const [sp, pal] = treeAt(x, z, false), s = rf(.8, 1.4) * (sp === 'dead' ? .9 : 1);
    place('trees', sp, pal, x, z, rnd() * 6.28, s, 'cast'); circ(x, z, .4 * s + .12); claim(x, z, 1.4 * s); trees.push([x, z]);
  }
  /* distant forest ring outside the wall (background depth) */
  let ring = 0; guard = 0;
  while (ring < (o.forest == null ? 110 : o.forest) && guard++ < 6000) {
    const px = (rnd() * 2 - 1) * (WORLD + 32), pz = (rnd() * 2 - 1) * (WORLD + 32);
    if (Math.abs(px) < WORLD + 3 && Math.abs(pz) < WORLD + 3) continue;
    if (Math.abs(px) < 7 && pz > 0) continue;
    if (!clear(px, pz, 2.6)) continue;
    const [sp, pal] = treeAt(px, pz, true), s = rf(1, 1.7);
    place('trees', sp, pal, px, pz, rnd() * 6.28, s, 'plain', true); claim(px, pz, 1.8 * s); ring++;
  }

  /* bushes & mushrooms: loose, avoid paths; some hug the walls */
  const bushPals = { round: CATALOG.bushes.round.pals, hedge: CATALOG.bushes.hedge.pals, spiky: CATALOG.bushes.spiky.pals, reeds: CATALOG.bushes.reeds.pals };
  let n = 0; guard = 0;
  while (n < (o.bushes || 60) && guard++ < 4000) {
    const x = (rnd() * 2 - 1) * (WORLD - 1.5), z = (rnd() * 2 - 1) * (WORLD - 1.5);
    if (onPath(x, z, .4) || !free(x, z, .8) || !clear(x, z, .9)) continue;
    const r = rnd(), nm = r < .4 ? 'round' : r < .6 ? 'hedge' : r < .85 ? 'spiky' : 'reeds', pal = rp(bushPals[nm]);
    place('bushes', nm, pal, x, z, rnd() * 6.28, rf(.8, 1.4), 'plain'); claim(x, z, .5); n++;
  }
  n = 0; guard = 0;
  while (n < 9 && guard++ < 800) { const x = (rnd() * 2 - 1) * (WORLD - 2), z = (rnd() * 2 - 1) * (WORLD - 2); if (onPath(x, z, .6) || !free(x, z, .6)) continue; if (!trees.some(t => Math.hypot(t[0] - x, t[1] - z) < 3)) continue; place('bushes', 'mushrooms', rp(['red', 'brown', 'orange', 'white']), x, z, rnd() * 6, rf(.9, 1.4), 'plain'); n++; }
  /* rocks */
  n = 0; guard = 0;
  while (n < (o.rocks || 40) && guard++ < 3000) {
    const x = (rnd() * 2 - 1) * (WORLD - 1.5), z = (rnd() * 2 - 1) * (WORLD - 1.5);
    if (onPath(x, z, .3) || !free(x, z, .9) || !clear(x, z, 1)) continue;
    const r = rnd(), nm = r < .22 ? 'boulder' : r < .5 ? 'stone' : r < .75 ? 'cluster' : r < .93 ? 'slab' : 'standing', s = rf(.7, 1.3);
    const pal = nm === 'standing' ? rp(['slate', 'grey', 'mossy']) : rp(RP); place('rocks', nm, pal, x, z, rnd() * 6.28, s, 'plain');
    if (nm === 'boulder') circ(x, z, .95 * s); else if (nm === 'standing') circ(x, z, .5 * s); else if (nm === 'slab') circ(x, z, .7 * s); claim(x, z, .8); n++;
  }
  /* flower patches, grass tufts */
  const FL = [['daisy', CATALOG.flowers.daisy.pals], ['tulip', CATALOG.flowers.tulip.pals], ['lavender', CATALOG.flowers.lavender.pals], ['bellflower', CATALOG.flowers.bellflower.pals]];
  n = 0; guard = 0;
  while (n < (o.flowers || 80) && guard++ < 4000) {
    const x = (rnd() * 2 - 1) * (WORLD - 1), z = (rnd() * 2 - 1) * (WORLD - 1);
    if (onPath(x, z, .3) || !free(x, z, .5)) continue;
    const [nm, ps] = rp(FL); place('flowers', nm, rp(ps), x, z, rnd() * 6.28, rf(.9, 1.4), 'plain'); n++;
  }
  n = 0; guard = 0;
  while (n < (o.grass || 420) && guard++ < 6000) {
    const x = (rnd() * 2 - 1) * (WORLD + 6), z = (rnd() * 2 - 1) * (WORLD + 6);
    if (Math.hypot(x, z) < 10 || Math.abs(x) < 2.6 && z > -26 || Math.abs(z) < 2.2 && Math.abs(x) < WORLD || !free(x, z, .4)) continue;
    place('flowers', 'grass', rp(['green', 'green', 'lush', 'dry']), x, z, rnd() * 6.28, rf(.8, 1.5), 'plain'); n++;
  }
  const out = { trees: trees.length, stats, cast: A.cast.geo(true), plain: A.plain.geo(true), glow: A.glow.geo(false), variants: cache.size };
  out.tris = (out.cast ? out.cast.attributes.position.count / 3 : 0) + (out.plain ? out.plain.attributes.position.count / 3 : 0) + (out.glow ? out.glow.attributes.position.count / 3 : 0);
  for (const v of cache.values()) { v.geo.dispose(); if (v.glow) v.glow.dispose(); }
  return out;
}
