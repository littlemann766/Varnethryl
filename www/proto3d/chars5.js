// ================= batch 5 (enemies/creatures): Frost Troll Brute, Stone Troll, Ember Wyrmling, Hydrella, Hobgoblin Shieldwall, Ssylthar (basilisk), Wyvern Strafer, Vaelthryx (crystal cobra boss) =================
// Same kit as chars.js / chars3.js / chars4.js (named bones, rigid-parted nodes, flat palette, baked idle + walk). Serpents/dragons: "walk" clip = slither / swim / strafe.
import * as THREE from 'three';
import * as K from './chars_core.js';
import { pal, hold, rnd, noHead, bakeRig } from './chars3.js';
const { makeCtx, humanoid, belt, cape, tabard, skirt, emblem, finalize } = K;
const PI = Math.PI;
export const CHARS5 = {};
const S = Math.sin;

// ---------- shared helpers ----------
// limb hanging from bone origin (+y up, extends -y)
const limb = (c, p, len, r0, r1, m, sides = 7) => { const g = c.G.cyl(r0, r1, len, sides); g.translate(0, -len / 2, 0); c.add(p, g, m); };
// cone pointing along the direction given by rotation r
const spike = (c, par, m, x, y, z, r, rad, len, sides = 4, sc) => c.add(par, c.G.cone(rad, len, sides), m, x, y + 0, z, { r, s: sc });
// fur / spike ring hanging around a bone-local axis (cones pointing down)
const furRing = (c, par, n, rad, y, len, mats, o = {}) => { const r = rnd(o.seed ?? 5); for (let i = 0; i < n; i++) { const a = i / n * PI * 2 + (o.a0 ?? 0), L = len * (.7 + r() * .6); c.add(par, c.G.cone(o.w ?? .04, L, 4), mats[i % mats.length], Math.sin(a) * rad * (o.sx ?? 1), y - L / 2 + (r() - .5) * .02, Math.cos(a) * rad * (o.sz ?? 1), { r: [PI + Math.cos(a) * .35, 0, -Math.sin(a) * .35], s: [1, 1, .55] }); } };
// rocky chunk (low poly)
const rock = (c, par, m, x, y, z, s, sd = 1) => { const r = rnd(sd * 7 + 3); return c.add(par, c.G.oct(s), m, x, y, z, { r: [r() * 3, r() * 3, r() * 3], s: [1 + r() * .5, .8 + r() * .4, 1 + r() * .4] }); };
const moss = (c, par, n, rx, rz, cx, cy, cz, sz, seed = 3) => { const r = rnd(seed), cols = [0x4f7a2a, 0x6a8f32, 0x3f6a26]; for (let i = 0; i < n; i++) c.add(par, c.G.sph(sz * (.7 + r() * .7), 6, 4), c.M(cols[i % 3], { r: 1, n: 'moss' + (i % 3) }), cx + (r() - .5) * 2 * rx, cy + r() * sz, cz + (r() - .5) * 2 * rz, { s: [1, .5, 1] }); };
const rope = (c, b, y, r, col = 0x8a6a3a) => c.add(b, c.G.tor(r, .014, 4, 10), c.M(col, { r: .95, n: 'rope' }), 0, y, 0, { r: [PI / 2, 0, 0] });
const eyeM = (c, col, ei = 1) => c.M(col, { e: col, ei, r: .3, n: 'eye' + col });
// two-sided triangle-fan membrane in the local XY plane (fan origin = 0,0). pts = ordered boundary vertices
function membrane(pts, depth = 0) { const v = [0, 0, 0]; for (const p of pts) v.push(p[0], p[1], depth); const idx = []; for (let i = 1; i < pts.length; i++) idx.push(0, i, i + 1);
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(v, 3)); g.setIndex(idx); g.computeVertexNormals(); return g; }
// spar along a direction in the XY plane
function spar(c, grp, m, ang, len, r0, r1 = r0 * .5) { const g = c.G.cyl(r1, r0, len, 4); g.translate(0, len / 2, 0); c.add(grp, g, m, 0, 0, 0, { r: [0, 0, ang - PI / 2] }); }
// bat-style wing: bones wing_S (shoulder, flap about body z) -> wingTip_S (wrist). o.L1 arm, o.Lf finger lengths[], o.fa finger angles[]
function batWing(c, parent, k, o) {
  const { M, bone, add, G } = c, Sd = k > 0 ? 'L' : 'R', mem = M(o.mem, { r: .8, d: 1, n: 'membrane' }), memd = M(o.memd ?? o.mem, { r: .8, d: 1, n: 'membraneD' }), bn = M(o.bone, { r: .6, n: 'wingbone' }), claw = M(o.claw, { r: .5, n: 'claw' });
  const w = bone('wing_' + Sd, parent, k * o.x, o.y, o.z ?? 0), wt = bone('wingTip_' + Sd, w, k * o.L1, 0, 0);
  const tl = PI / 2 - (o.tilt ?? .75), g1 = new THREE.Group(); g1.rotation.x = tl; w.add(g1); const g2 = new THREE.Group(); g2.rotation.x = tl; wt.add(g2);
  const L1 = o.L1, f = (x, y) => [k * x, y];
  add(g1, membrane([f(L1, 0), f(L1 * .88, -L1 * .32), f(L1 * .55, -L1 * .5), f(L1 * .2, -L1 * .46), f(.02, -L1 * .3)], 0), mem); add(g1, membrane([f(L1, 0), f(L1 * .88, -L1 * .32), f(L1 * .55, -L1 * .5), f(L1 * .2, -L1 * .46), f(.02, -L1 * .3)], -.004), memd);
  { const g = G.cyl(o.r * .7, o.r, L1, 5); g.translate(0, L1 / 2, 0); add(g1, g, o.skin, 0, 0, 0, { r: [0, 0, -k * PI / 2] }); add(g1, G.sph(o.r * 1.3, 6, 5), o.skin, 0, 0, 0); add(g1, G.sph(o.r * 1.1, 6, 5), o.skin, k * L1, 0, 0); }
  const pts = []; const n = o.Lf.length;
  for (let i = 0; i < n; i++) { const a = o.fa[i], L = o.Lf[i], T = [L * Math.cos(a), L * Math.sin(a)]; pts.push(T); spar(c, g2, bn, k > 0 ? a : PI - a, L, o.r * .55); }
  const seq = []; for (let i = 0; i < n; i++) { seq.push(f(...pts[i])); if (i < n - 1) { const m = [(pts[i][0] + pts[i + 1][0]) * .5 * .62, (pts[i][1] + pts[i + 1][1]) * .5 * .62]; seq.push(f(...m)); } }
  seq.push(f(L1 * -.08, -L1 * .3));
  add(g2, membrane(seq, 0), mem); add(g2, membrane(seq, -.004), memd);
  add(g2, G.cone(o.r * 1.1, o.r * 4.5, 4), claw, k * o.r * .5, o.r * 2.2, 0, { r: [0, 0, -k * .5] });
  return { w, wt };
}
// body-length chain of bones along -z (tail), each tapering. returns bones. yaw curl via R in animation
function tailChain(c, par, n, x, y, z, len, r0, r1, mat, o = {}) {
  const { bone, add, G } = c; const out = []; let p = par;
  for (let i = 1; i <= n; i++) { const t = bone((o.name ?? 'tail_') + i, p, i === 1 ? x : 0, i === 1 ? y : 0, i === 1 ? z : -len);
    const ra = r0 + (r1 - r0) * (i - 1) / n, rb = r0 + (r1 - r0) * i / n; const g = G.cyl(ra, rb, len, o.sides ?? 7); g.rotateX(PI / 2); g.translate(0, 0, -len / 2); add(t, g, mat);
    if (o.belly) { add(t, G.box(ra * 1.3, .01, len * .9), o.belly, 0, -ra * .8, -len / 2, { r: [0, 0, 0] }); }
    if (o.spines) add(t, G.cone(ra * .6, ra * 2.2, 4), o.spines, 0, ra * .95, -len * .5, { r: [-1.1, 0, 0], s: [.5, 1, 1] });
    if (i === n && o.tip) o.tip(c, t, rb, len);
    out.push(t); p = t; }
  return out;
}
// tapering neck chain along +y with per-segment rest bend (rotation.x). returns bones.
function neckChain(c, par, n, x, y, z, len, r0, r1, curve, mat, o = {}) {
  const { bone, add, G } = c; const out = []; let p = par;
  for (let i = 1; i <= n; i++) { const t = bone((o.name ?? 'neck_') + i, p, i === 1 ? x : 0, i === 1 ? y : len, i === 1 ? z : 0); t.rotation.x = curve[i - 1] ?? 0;
    const ra = r0 + (r1 - r0) * (i - 1) / n, rb = r0 + (r1 - r0) * i / n; const g = G.cyl(rb, ra, len * 1.04, o.sides ?? 8); g.translate(0, len / 2, 0); add(t, g, mat);
    if (o.belly) add(t, G.box(ra * 1.1, len * .96, ra * .3), o.belly, 0, len / 2, ra * .8, { r: [-.04, 0, 0] });
    if (o.bands) for (let j = 0; j < 2; j++) add(t, G.box(ra * 1.15, .012, ra * .3), o.bands, 0, len * (.2 + j * .5), ra * .82);
    if (o.spines) add(t, G.cone(ra * .55, ra * 2.0, 4), o.spines, 0, len * .5, -ra * .92, { r: [-1.1, 0, 0], s: [.5, 1, 1] });
    if (o.side) for (const kk of [-1, 1]) add(t, G.cone(ra * .35, ra * 1.0, 4), o.side, kk * ra * .95, len * .5, -ra * .2, { r: [-.5, 0, -kk * 1.15], s: [.6, 1, 1] });
    out.push(t); p = t; }
  return out;
}
// dragon head (faces +z): bones head, jaw already created. o: skin, dark, tooth, horn, eye, hs (scale), horns n, crest
function dragonHead(c, head, jaw, o) {
  const { add, G, M } = c, hs = o.hs ?? 1, tooth = M(o.tooth ?? 0xf0e8d0, { r: .5, n: 'tooth' }), horn = M(o.horn, { r: .6, n: 'horn' });
  add(head, G.sph(.1 * hs, 8, 6), o.skin, 0, .01 * hs, 0, { s: [1, .9, 1.25] });
  { const g = G.cyl(.045 * hs, .085 * hs, .2 * hs, 6); g.rotateX(PI / 2); add(head, g, o.skin, 0, -.01 * hs, .17 * hs); }
  add(head, G.box(.09 * hs, .03 * hs, .16 * hs), o.dark, 0, .035 * hs, .15 * hs); // snout ridge
  { const g = G.cyl(.04 * hs, .075 * hs, .18 * hs, 6); g.rotateX(PI / 2); add(jaw, g, o.skin, 0, -.012 * hs, .09 * hs); }
  add(jaw, G.box(.07 * hs, .018 * hs, .15 * hs), o.belly ?? o.dark, 0, -.035 * hs, .09 * hs);
  for (let i = 0; i < 4; i++) for (const k of [-1, 1]) { add(head, G.cone(.008 * hs, .035 * hs, 4), tooth, k * .045 * hs, -.045 * hs, (.1 + i * .045) * hs, { r: [PI, 0, 0] }); add(jaw, G.cone(.007 * hs, .03 * hs, 4), tooth, k * .035 * hs, .0, (.05 + i * .04) * hs); }
  for (const k of [-1, 1]) { add(head, G.sph(.017 * hs, 6, 5), eyeM(c, o.eye, o.ei ?? 1), k * .07 * hs, .04 * hs, .08 * hs); add(head, G.box(.05 * hs, .014 * hs, .035 * hs), o.dark, k * .07 * hs, .065 * hs, .075 * hs, { r: [0, 0, -k * .35] });
    add(head, G.sph(.008 * hs, 4, 3), M(0x120804), k * .02 * hs, .035 * hs, .27 * hs);
    for (let i = 0; i < (o.horns ?? 2); i++) add(head, G.cone(.026 * hs, (.22 - i * .05) * hs, 5), horn, k * (.055 + i * .02) * hs, (.08 + i * .015) * hs, (-.04 - i * .05) * hs, { r: [-1.25 + i * .15, 0, k * (.3 + i * .15)] }); }
  if (o.fang) for (const k of [-1, 1]) { add(head, G.cone(.014 * hs, .12 * hs, 4), tooth, k * .035 * hs, -.1 * hs, .2 * hs, { r: [.1, 0, 0] }); add(head, G.cone(.014 * hs, .12 * hs, 4), tooth, k * .035 * hs, -.1 * hs, .2 * hs, { r: [PI, 0, 0] }); }
  if (o.cheek) for (const k of [-1, 1]) for (let i = 0; i < o.cheek; i++) add(head, G.cone(.02 * hs, .1 * hs, 4), o.cheekM ?? o.dark, k * .09 * hs, (.0 - i * .015) * hs, (-.03 - i * .045) * hs, { r: [-.2, 0, -k * (1.1 + i * .15)], s: [.6, 1, 1] });
  for (let i = 0; i < (o.crest ?? 3); i++) add(head, G.cone(.02 * hs, .08 * hs, 4), o.dark, 0, .1 * hs, (-.01 - i * .06) * hs, { r: [-.7, 0, 0], s: [.6, 1, 1] });
}
// forked tongue attached to jaw
const tongue = (c, jaw, hs, col = 0xc0304a) => { const m = c.M(col, { r: .6, n: 'tongue' }); c.add(jaw, c.G.box(.025 * hs, .006 * hs, .22 * hs), m, 0, -.005 * hs, .2 * hs); for (const k of [-1, 1]) c.add(jaw, c.G.cone(.007 * hs, .07 * hs, 3), m, k * .012 * hs, -.005 * hs, .35 * hs, { r: [PI / 2, 0, k * .0], s: [1, 1, .3] }); };

// =============================== FROST TROLL BRUTE ===============================
CHARS5.frosttroll = { name: 'Frost Troll Brute', sheetKey: 'frosttroll', build() {
  const skinC = 0x8fb4d8, c = makeCtx({ name: 'Frost_Troll_Brute', bulk: 2.25, sw: 1.7, skin: skinC, hair: 0xe8f0f8, under: skinC, pants: 0x5a4030, sleeve: skinC, glove: skinC, boot: 0x4a3426 });
  const h = humanoid(c), { gold, leather, dleather } = pal(c), { add, G, M, bones: B } = c;
  const SK = M(skinC, { r: .85, n: 'trollskin' }), SK2 = M(0x6f96bc, { r: .85, n: 'trollskin2' }), fur = M(0x4a3426, { r: 1, d: 1, n: 'furbrown' }), fur2 = M(0x6a4c38, { r: 1, d: 1, n: 'furbrown2' }), snow = M(0xf2f6fa, { r: 1, n: 'snow' }), whf = M(0xe6eef6, { r: 1, d: 1, n: 'furwhite' });
  const ice = M(0x9fd6f6, { r: .15, e: 0x4ab0ff, ei: .35, n: 'ice' }), ice2 = M(0xd8f0ff, { r: .12, e: 0x7ac8ff, ei: .25, n: 'ice2' }), bone = M(0xe6dcc0, { r: .6, n: 'bone' });
  const crystal = (par, x, y, z, s, rx = 0, rz = 0, m = ice) => { add(par, G.cone(.03 * s, .17 * s, 5), m, x, y + .085 * s, z, { r: [rx, 0, rz] }); };
  noHead(c); const hd = B.head; hd.scale.setScalar(1.35); hd.position.z += .05;
  add(hd, G.sph(.13, 9, 7), SK, 0, .09, 0, { s: [1.15, .95, 1.0] }); add(hd, G.box(.2, .1, .15), SK, 0, -.0, .06); add(hd, G.box(.22, .05, .1), SK2, 0, .13, .09, { r: [.2, 0, 0] });
  add(hd, G.sph(.04, 7, 5), M(0x6a96c4, { r: .8 }), 0, .06, .15, { s: [1.2, 1, 1] });
  for (const k of [-1, 1]) { add(hd, G.cone(.02, .1, 5), bone, k * .065, .005, .12, { r: [-.15, 0, k * .12] }); add(hd, G.sph(.015, 5, 4), eyeM(c, 0xbfe8ff, .9), k * .055, .115, .12); add(hd, G.cone(.04, .13, 4), SK, k * .15, .1, -.01, { r: [0, 0, -k * 1.35], s: [1, 1, .5] }); }
  // white shaggy mane + beard
  furRing(c, hd, 14, .12, .15, .13, [whf, snow], { seed: 2, w: .04, sz: .8 }); furRing(c, hd, 9, .09, .0, .2, [whf, snow], { seed: 4, w: .05, a0: 3.3, sz: 1.2 }); for (const k of [-1, 1]) add(hd, G.cone(.045, .18, 4), whf, k * .08, -.01, .12, { r: [PI + .2, 0, 0], s: [1, 1, .6] });
  crystal(hd, 0, .21, -.02, 1.6, -.2); crystal(hd, .07, .19, -.03, 1.1, -.1, -.4); crystal(hd, -.07, .19, -.03, 1.1, -.1, .4, ice2); crystal(hd, 0, .15, -.1, 1.0, -.8);
  // body mass
  add(B.spine, G.sph(.25, 9, 7), SK, 0, -.02, .06, { s: [1.2, 1.05, 1.0] }); add(B.chest, G.sph(.25, 9, 7), SK, 0, .06, .02, { s: [1.3, 1.0, .95] });
  // fur mantle, chest ruff, fur skirt (brown w/ snow dusting)
  for (const k of [-1, 1]) { const sh = B['shoulder_' + (k > 0 ? 'L' : 'R')]; add(sh, G.dome(.15, 8, 4), fur, k * .06, .0, 0, { s: [1.1, .65, 1.1] }); furRing(c, sh, 12, .13, .0, .22, [fur, fur2], { seed: 7 + k, w: .045 });
    add(sh, G.dome(.13, 7, 3), snow, k * .06, .06, 0, { s: [1, .35, 1] }); for (let i = 0; i < 4; i++) crystal(sh, k * (.04 + i * .035), .07, (i % 2 - .5) * .12, 1.3 - i * .15, 0, -k * (.3 + i * .2)); }
  furRing(c, B.chest, 16, .28, .2, .26, [fur, fur2, whf], { seed: 11, w: .05, sz: .8 }); furRing(c, B.hips, 16, .26, .02, .42, [fur2, fur], { seed: 13, w: .055, sz: .85 }); furRing(c, B.hips, 12, .22, .0, .32, [fur, fur2], { seed: 17, w: .05, sz: .85 });
  for (let i = 0; i < 9; i++) add(B.chest, G.dome(.05, 6, 3), snow, Math.sin(i * 1.7) * .26, .24, Math.cos(i * 1.7) * .22 - .02, { s: [1, .4, 1] });
  for (const [x, y, z, s] of [[.15, .3, -.15, 1.6], [-.12, .28, -.17, 1.4], [0, .34, -.2, 2], [.1, .2, -.24, 1.2]]) crystal(B.chest, x, y, z, s, -.7, x * 1.2);
  belt(c, M(0x4a3020, { r: .9 }), M(0x8a8a90, { m: .5, r: .4 }), .0, .17);
  // snowflake tabard + bone trophies
  tabard(c, { w: .25, len: .58, col: 0x2a4a8a, trim: 0xd8ecfa, emblem: 'snow', point: .1, z: .26, y: -.02 });
  for (let i = 0; i < 3; i++) add(B.hips, G.cone(.02, .1, 4), bone, -.14 + i * .05, -.1, .24, { r: [PI, 0, 0] }); add(B.hips, G.sph(.04, 6, 5), bone, .17, -.06, .23, { s: [1, 1.1, .9] });
  for (const Sd of ['L', 'R']) { for (let i = 0; i < 3; i++) { rope(c, B['foreArm_' + Sd], -.06 - i * .06, .085, 0x6a4a2c); rope(c, B['shin_' + Sd], -.1 - i * .07, .095, 0x6a4a2c); }
    furRing(c, B['foreArm_' + Sd], 8, .09, -.02, .12, [fur, whf], { seed: 20 }); furRing(c, B['shin_' + Sd], 8, .1, -.05, .14, [fur2, fur], { seed: 21 });
    crystal(B['foreArm_' + Sd], .08, -.1, 0, 1.1, 0, -1); crystal(B['shin_' + Sd], .09, -.18, .02, 1, 0, -1.2);
    add(B['foot_' + Sd], G.box(.17, .07, .3), SK, 0, -.01, .08); for (let i = -1; i <= 1; i++) { add(B['foot_' + Sd], G.sph(.035, 5, 4), SK, i * .055, -.01, .24, { s: [1, .8, 1] }); add(B['foot_' + Sd], G.cone(.014, .06, 4), bone, i * .055, -.01, .29, { r: [PI / 2, 0, 0] }); }
    add(B['thigh_' + Sd], G.sph(.15, 7, 5), SK, 0, -.05, 0);
    for (const i of [-1, 0, 1]) add(B['hand_' + Sd], G.cone(.012, .07, 4), bone, i * .03, -.1, .035, { r: [-.2, 0, 0] }); }
  // ice-encrusted club (R hand)
  const cb = new THREE.Group(), wood = M(0x5a3a22, { r: .8, n: 'clubwood' }), bind = M(0x3c2616, { r: .85, n: 'bind' });
  add(cb, G.cyl(.05, .08, 1.2, 7), wood, 0, .35, 0); add(cb, G.cyl(.14, .1, .62, 8), wood, 0, 1.0, 0);
  for (let i = 0; i < 6; i++) add(cb, G.tor(.12 + (i < 3 ? 0 : .01), .018, 4, 10), bind, 0, .76 + i * .1, 0, { r: [PI / 2, 0, i * .3] });
  for (let i = 0; i < 9; i++) { const a = i * 2.2, y = .75 + (i % 5) * .12; add(cb, G.cone(.045, .22 + (i % 3) * .06, 5), i % 2 ? ice : ice2, Math.sin(a) * .13, y, Math.cos(a) * .13, { r: [Math.cos(a) * 1.1, 0, -Math.sin(a) * 1.1] }); }
  add(cb, G.cone(.06, .3, 5), ice, 0, 1.43, 0); add(cb, G.dome(.1, 7, 3), snow, 0, 1.27, 0, { s: [1, .5, 1] });
  cb.scale.setScalar(.9); hold(c, h.hips, 'hand_R', cb, 0, -.07, 0, 1.5, 0, 0);
  const rig = finalize(c, h.root, { R: 1 }, Bn => { Bn.spine.rotation.set(.4, 0, 0); Bn.neck.rotation.set(-.35, 0, 0); Bn.upperArm_L.rotation.set(.2, 0, .45); Bn.upperArm_R.rotation.set(-.2, 0, -.3); Bn.foreArm_R.rotation.set(-.9, 0, 0); Bn.thigh_L.rotation.set(0, 0, -.1); Bn.thigh_R.rotation.set(0, 0, .1); });
  rig.root.scale.setScalar(1.05); return rig; } };

// =============================== STONE TROLL ===============================
CHARS5.stonetroll = { name: 'Stone Troll (Standard form)', sheetKey: 'stonetroll', build() {
  const skinC = 0x8c8474, c = makeCtx({ name: 'Stone_Troll', bulk: 2.3, sw: 1.75, skin: skinC, hair: 0x4a3524, under: skinC, pants: 0x6f6860, sleeve: skinC, glove: skinC, boot: 0x6f6860 });
  const h = humanoid(c), { add, G, M, bones: B } = c;
  const SK = M(0x7a7264, { r: 1, n: 'stoneskin' }), R1 = M(0x9a9282, { r: 1, n: 'rock1' }), R2 = M(0x6e6658, { r: 1, n: 'rock2' }), R3 = M(0xa8884e, { r: 1, n: 'rock3' }), hair = M(0x5a3c24, { r: 1, d: 1, n: 'trollhair' }), hair2 = M(0x3c2a1a, { r: 1, d: 1, n: 'trollhair2' }), red = 0x9a1c1c, tooth = M(0xf0e6c8, { r: .6, n: 'tooth' });
  noHead(c); const hd = B.head, jaw = c.bone('jaw', hd, 0, .02, .04); hd.scale.setScalar(1.35); hd.position.z += .05;
  add(hd, G.sph(.13, 9, 7), SK, 0, .1, 0, { s: [1.15, .95, 1.0] }); add(hd, G.box(.2, .06, .15), R2, 0, .17, .02, { s: [1, 1, 1], r: [.15, 0, 0] }); add(hd, G.box(.2, .06, .14), SK, 0, .03, .06);
  add(jaw, G.box(.18, .05, .13), SK, 0, -.03, .05); add(jaw, G.box(.15, .02, .1), M(0x8a2a2a, { r: .8, n: 'mouth' }), 0, -.0, .06);
  for (let i = 0; i < 4; i++) for (const k of [-1, 1]) { add(hd, G.cone(.012, .06, 4), tooth, k * (.02 + i * .026), .0, .125, { r: [PI, 0, 0] }); }
  for (const k of [-1, 1]) { add(jaw, G.cone(.02, .1, 5), tooth, k * .07, .03, .1, { r: [-.1, 0, k * .1] }); add(hd, G.sph(.014, 5, 4), eyeM(c, 0xf0c040, .4), k * .055, .12, .12); add(hd, G.cone(.04, .15, 4), SK, k * .15, .1, -.01, { r: [0, 0, -k * 1.35], s: [1, 1, .5] }); add(hd, G.box(.06, .02, .03), R2, k * .055, .15, .125, { r: [0, 0, -k * .35] }); }
  add(hd, G.sph(.04, 7, 5), M(0x7a7264, { r: 1 }), 0, .07, .15, { s: [1.2, 1, 1] });
  furRing(c, hd, 12, .12, .17, .14, [hair, hair2], { seed: 3, w: .04, sz: .8 }); furRing(c, hd, 7, .09, .02, .2, [hair, hair2], { seed: 8, w: .05, a0: 3.3, sz: 1.2 }); for (const k of [-1, 1]) add(hd, G.cone(.05, .2, 4), hair, k * .09, -.02, .12, { r: [PI + .2, 0, 0], s: [1, 1, .6] });
  rock(c, hd, R1, .08, .21, -.04, .05, 1); rock(c, hd, R2, -.09, .2, -.02, .045, 2); moss(c, hd, 4, .1, .06, 0, .19, -.03, .04, 3);
  // torso
  add(B.spine, G.sph(.25, 9, 7), SK, 0, -.02, .06, { s: [1.2, 1.05, 1.0] }); add(B.chest, G.sph(.26, 9, 7), SK, 0, .06, .02, { s: [1.3, 1.0, .95] });
  for (let i = 0; i < 14; i++) { const a = i * .9, mm = [R1, R2, R3][i % 3]; rock(c, B.chest, mm, Math.sin(a) * .26, .02 + (i % 4) * .08, -.18 - Math.abs(Math.cos(a)) * .08, .06 + (i % 3) * .015, i + 5); }
  for (let i = 0; i < 6; i++) rock(c, B.spine, [R2, R1][i % 2], Math.sin(i * 1.3) * .2, -.04 + (i % 3) * .06, -.2, .055, i + 40);
  moss(c, B.chest, 9, .26, .1, 0, .26, -.14, .06, 21);
  for (let i = 0; i < 12; i++) { const a = -1.2 + i * .22; rock(c, B.chest, [R1, R2, R3][i % 3], Math.sin(a) * .3, .0 + (i % 3) * .1, .2 + Math.cos(a) * .06, .07 + (i % 3) * .02, i + 120); }
  for (let i = 0; i < 6; i++) rock(c, B.spine, [R2, R1][i % 2], (i - 2.5) * .08, -.02 + (i % 2) * .06, .24, .06, i + 140);
  for (const Sd of ['L', 'R']) { const kk = Sd === 'L' ? 1 : -1; for (let i = 0; i < 5; i++) { rock(c, B['upperArm_' + Sd], [R1, R2, R3][i % 3], Math.sin(i * 2) * .1, -.05 - i * .04, Math.cos(i * 2) * .1, .07 + (i % 2) * .02, 150 + i + kk); rock(c, B['foreArm_' + Sd], [R2, R1, R3][i % 3], Math.sin(i * 2.3) * .1, -.03 - i * .04, Math.cos(i * 2.3) * .1, .075, 160 + i + kk); rock(c, B['thigh_' + Sd], [R1, R2][i % 2], Math.sin(i * 2) * .12, -.05 - i * .05, Math.cos(i * 2) * .12, .08, 170 + i + kk); rock(c, B['shin_' + Sd], [R2, R1][i % 2], Math.sin(i * 2.4) * .1, -.03 - i * .05, Math.cos(i * 2.4) * .1, .07, 180 + i + kk); } rock(c, B['hand_' + Sd], R1, 0, -.1, .02, .09, 190 + kk); }
  for (const k of [-1, 1]) { const sh = B['shoulder_' + (k > 0 ? 'L' : 'R')]; rock(c, sh, R1, k * .08, .07, 0, .13, 3); rock(c, sh, R2, k * .06, .0, .08, .09, 4); rock(c, sh, R3, k * .1, .1, -.08, .08, 5); rock(c, sh, R2, k * .12, -.05, 0, .09, 6); moss(c, sh, 6, .12, .1, k * .06, .15, 0, .05, 11 + k);
    furRing(c, sh, 8, .12, .02, .18, [hair, hair2], { seed: 30 + k, w: .04 }); }
  // loincloth: ragged red, rope belt, stone charm
  belt(c, M(0x7a5a30, { r: .95, n: 'ropebelt' }), M(0x8a8a82, { r: .9 }), .0, .17);
  skirt(c, { col: red, len: .3, top: .2, bot: .26, y: -.04, zs: .85, ragged: .14, segs: 12 }); tabard(c, { w: .2, len: .4, col: red, trim: 0x5a1010, point: .12, z: .26, y: -.02 });
  rock(c, B.hips, R1, .0, -.12, .27, .055, 77); add(B.hips, G.tor(.05, .012, 4, 8), M(0x8a6a3a, { r: .95 }), 0, -.12, .27);
  for (const Sd of ['L', 'R']) { const kk = Sd === 'L' ? 1 : -1; for (let i = 0; i < 3; i++) { rope(c, B['foreArm_' + Sd], -.06 - i * .06, .085); rope(c, B['shin_' + Sd], -.1 - i * .07, .095); }
    rock(c, B['foreArm_' + Sd], R2, kk * .06, -.1, .02, .08, 50 + kk); rock(c, B['foreArm_' + Sd], R1, kk * .05, -.2, -.04, .06, 52); moss(c, B['foreArm_' + Sd], 2, .04, .05, 0, -.1, 0, .05, 3 + Sd.length);
    rock(c, B['shin_' + Sd], R2, 0, -.05, .09, .08, 60 + kk); rock(c, B['thigh_' + Sd], R1, kk * .06, -.1, .08, .1, 70 + kk); moss(c, B['shin_' + Sd], 3, .06, .08, 0, -.2, 0, .055, 2);
    add(B['foot_' + Sd], G.box(.17, .07, .3), SK, 0, -.01, .08); for (let i = -1; i <= 1; i++) add(B['foot_' + Sd], G.sph(.04, 5, 4), R1, i * .055, -.01, .24, { s: [1, .8, 1] }); add(B['thigh_' + Sd], G.sph(.15, 7, 5), SK, 0, -.05, 0);
    add(B['hand_' + Sd], G.sph(.07, 6, 5), R2, 0, -.06, .0, { s: [1.1, 1, 1] }); for (const i of [-1, 0, 1]) add(B['hand_' + Sd], G.sph(.028, 5, 4), R1, i * .04, -.1, .05); }
  const rig = finalize(c, h.root, {}, Bn => { Bn.jaw.rotation.set(.32, 0, 0); Bn.spine.rotation.set(.45, 0, 0); Bn.neck.rotation.set(-.4, 0, 0); Bn.upperArm_L.rotation.set(.2, 0, .4); Bn.upperArm_R.rotation.set(.2, 0, -.4); Bn.foreArm_L.rotation.set(-.7, 0, 0); Bn.foreArm_R.rotation.set(-.7, 0, 0); Bn.thigh_L.rotation.set(0, 0, -.12); Bn.thigh_R.rotation.set(0, 0, .12); });
  rig.root.scale.setScalar(1.2); return rig; } };

// =============================== HOBGOBLIN SHIELDWALL ===============================
CHARS5.hobgoblin = { name: 'Hobgoblin Shieldwall', sheetKey: 'hobgoblin', build() {
  const skinC = 0x7f8c40, c = makeCtx({ name: 'Hobgoblin_Shieldwall', bulk: 1.5, sw: 1.25, skin: skinC, hair: 0x2a1a14, under: 0x5a5448, pants: 0x4a3a2c, sleeve: 0x5a6068, glove: 0x3a2a1c, boot: 0x4a3a2c });
  const h = humanoid(c), { gold, leather, dleather, brass } = pal(c), { add, G, M, bones: B } = c;
  const steel = M(0x9aa0aa, { m: .55, r: .38, n: 'ironplate' }), dsteel = M(0x6c727c, { m: .5, r: .45, n: 'ironplate2' }), red = M(0xa01c20, { r: .9, d: 1, n: 'crimson' }), dred = M(0x5a0c10, { r: .9, d: 1, n: 'dcrimson' }), mail = M(0x585e66, { m: .5, r: .6, n: 'chain' }), SK = M(skinC, { r: .85, n: 'hobskin' });
  noHead(c); const hd = B.head;
  add(hd, G.sph(.108, 9, 7), SK, 0, .1, 0, { s: [1.05, 1.1, 1.05] }); add(hd, G.box(.14, .08, .1), SK, 0, .03, .05); add(hd, G.box(.16, .035, .09), M(0x6a7634, { r: .9 }), 0, .15, .07, { r: [.25, 0, 0] });
  add(hd, G.sph(.032, 6, 5), M(0x6a7634, { r: .8 }), 0, .075, .12, { s: [1.2, 1, 1] });
  for (const k of [-1, 1]) { add(hd, G.cone(.04, .2, 4), SK, k * .115, .13, -.005, { r: [0, 0, -k * 1.3], s: [1, 1, .4] }); add(hd, G.sph(.014, 5, 4), eyeM(c, 0xf0c030, .5), k * .042, .125, .1); add(hd, G.cone(.012, .05, 4), M(0xf0e6c8), k * .04, .005, .095, { r: [PI, 0, 0] });
    for (let i = 0; i < 3; i++) add(hd, G.box(.012, .06, .006), M(0xc01c1c, { r: .7, n: 'warpaint' }), k * (.055 + i * .02), .11 - i * .01, .102, { r: [0, 0, -k * (.35 + i * .2)] }); }
  // topknot of dark hair
  for (let i = 0; i < 7; i++) add(hd, G.cone(.025, .16, 4), M(0x2a1a14, { r: 1, n: 'hobhair' }), (i - 3) * .028, .22, -.03 - Math.abs(i - 3) * .01, { r: [-.5 - (i % 2) * .2, 0, (i - 3) * .18] });
  // plate harness: breastplate, gorget, pauldrons, tassets, greaves, vambraces
  add(B.chest, G.cyl(.22, .16, .3, 8), steel, 0, .09, .01, { s: [1, 1, .72] }); add(B.chest, G.box(.2, .05, .02), dsteel, 0, .2, .15); for (let i = 0; i < 3; i++) add(B.spine, G.cyl(.15 + i * .005, .15 + i * .005, .06, 8), i % 2 ? dsteel : steel, 0, .08 - i * .06, 0, { s: [1, 1, .74] });
  add(B.neck, G.cyl(.075, .09, .06, 8), mail, 0, .01, 0);
  for (const k of [-1, 1]) { const sh = B['shoulder_' + (k > 0 ? 'L' : 'R')]; for (let i = 0; i < 3; i++) add(sh, G.dome(.14 - i * .015, 8, 3), i % 2 ? dsteel : steel, k * .05, .03 - i * .045, 0, { s: [1.15, .7, 1.1], r: [0, 0, -k * .28] }); add(sh, G.cone(.02, .06, 4), steel, k * .15, .08, 0, { r: [0, 0, -k * 1.2] }); }
  for (const Sd of ['L', 'R']) { const kk = Sd === 'L' ? 1 : -1; add(B['foreArm_' + Sd], G.cyl(.058, .052, .22, 8), steel, 0, -.15, 0); add(B['foreArm_' + Sd], G.cyl(.06, .06, .03, 8), brass, 0, -.04, 0); add(B['upperArm_' + Sd], G.cyl(.058, .056, .2, 8), mail, 0, -.12, 0);
    add(B['shin_' + Sd], G.cyl(.075, .062, .26, 8), steel, 0, -.3, 0); add(B['shin_' + Sd], G.sph(.07, 6, 5), dsteel, 0, -.0, .03, { s: [1, .8, 1] }); add(B['foot_' + Sd], G.box(.12, .06, .12), steel, 0, .02, .1); add(B['thigh_' + Sd], G.box(.15, .2, .17), dsteel, 0, -.18, .02, { r: [-.05, 0, 0] }); add(B['thigh_' + Sd], G.box(.15, .06, .17), steel, 0, -.3, .02); }
  belt(c, dleather, brass, .0, .17); add(B.chest, G.tor(.045, .014, 4, 8), brass, 0, .1, .155); strapX(c, leather, brass);
  // red tabard/tassets (ragged) and red cloak with sigil
  skirt(c, { col: 0xa01c20, trim: 0x6a1418, len: .52, top: .2, bot: .3, y: -.04, zs: .85, ragged: .18, segs: 12 }); tabard(c, { w: .24, len: .6, col: 0xa01c20, trim: 0xd8c8a8, emblem: 'ornate', point: .1, z: .22, y: -.03 });
  const cp = cape(c, { topW: .6, botW: .8, len: .75, col: 0x7a1418, trim: 0x4a1014, lining: 0x5a1014, waves: 9, ragged: .3, segs: 18, seed: 33, wrap: .12 }); cp.len = .75; emblem(c, cp.cb, 'ornate', .55, M(0xd8c8a8, { r: .7 }), 0, -.5, cp.z(.5) - .026, PI);
  add(B.chest, G.cyl(.23, .21, .08, 8, true), red, 0, .27, 0, { s: [1.0, 1, .8] }); // red scarf at neck
  K.pouch(c, B.hips, 0x4a3020, .22, -.07, .03, 1, gold);
  // round shield (L forearm) quartered red/black, iron boss + brass rim
  const sd = new THREE.Group(), blk = M(0x2a2428, { r: .8, n: 'shieldblack' }), srd = M(0xa01c20, { r: .8, n: 'shieldred' });
  add(sd, G.cyl(.4, .4, .045, 14), srd, 0, 0, 0, { r: [PI / 2, 0, 0] }); for (let i = 0; i < 4; i++) add(sd, G.box(.07, .78, .02), blk, 0, 0, .03, { r: [0, 0, i * PI / 4] }); for (let i = 0; i < 4; i++) add(sd, G.box(.03, .6, .02), M(0xd8c8a8, { r: .7, n: 'spokeTrim' }), 0, 0, .036, { r: [0, 0, i * PI / 4 + PI / 8] });
  add(sd, G.tor(.4, .03, 5, 18), brass, 0, 0, .0); add(sd, G.dome(.1, 8, 4), steel, 0, 0, .025, { r: [PI / 2, 0, 0], s: [1, 1, 1] }); for (let i = 0; i < 8; i++) { const a = i / 8 * PI * 2; add(sd, G.cone(.02, .08, 4), steel, Math.sin(a) * .2, Math.cos(a) * .2, .04, { r: [PI / 2, 0, 0] }); }
  
  B.foreArm_L.add(sd); sd.position.set(.12, -.1, .14); sd.rotation.set(0, .3, 0);
  // gladius (R hand)
  const gl = K.sword(c, { len: .62, guard: .16, gold: brass, blade: 0xc8d0d8, gem: 0xa01c20 }); hold(c, h.hips, 'hand_R', gl, 0, -.06, 0, 1.2, 0, 0);
  const rig = finalize(c, h.root, { R: 1, L: 1 }, Bn => { Bn.spine.rotation.set(.08, 0, 0); Bn.upperArm_L.rotation.set(-.2, 0, .1); Bn.foreArm_L.rotation.set(-1.0, 0, 0); Bn.upperArm_R.rotation.set(-.1, 0, -.25); Bn.foreArm_R.rotation.set(-.8, 0, 0); Bn.thigh_L.rotation.set(-.12, 0, -.06); Bn.thigh_R.rotation.set(.12, 0, .1); });
  return rig; } };
function strapX(c, mat, buckle) { const { add, G, bones: B } = c; for (const k of [1]) add(B.chest, G.box(.07, .5, .012), mat, 0, .07, .152, { r: [0, 0, .75] }); add(B.chest, G.cyl(.03, .03, .014, 8), buckle, 0, .07, .16, { r: [PI / 2, 0, 0] }); }

// =============================== generic DRAKE builder (Ember Wyrmling + Wyvern Strafer) ===============================
// facing +z. o.quad: four legs + wings on the back; else bipedal with wing-arms. All built in a ~1.1 unit-tall frame then root-scaled.
function drake(o) {
  const c = makeCtx({ name: o.name }), { M, bone, add, G, bones: B } = c, P = o.pal;
  const skin = M(P.skin, o.glowSkin ? { r: .75, e: 0xc02800, ei: .45, n: 'scale' } : { r: .75, n: 'scale' }), dark = M(P.dark, { r: .8, n: 'scaledark' }), belly = M(P.belly, { r: .8, n: 'belly' }), claw = M(P.claw, { r: .5, n: 'claw' }), alt = M(P.alt ?? P.skin, { r: .75, n: 'scalealt' });
  const R = o.R ?? .2, root = bone('root', null), hips = bone('hips', root, 0, o.hipH, -.18), spine = bone('spine', hips, 0, .02, .3), chest = bone('chest', spine, 0, .05, .3);
  if (o.rockBase) o.rockBase(c, root);
  add(hips, G.sph(R * .95, 9, 7), skin, 0, 0, 0, { s: [1, 1, 1.25] }); add(spine, G.sph(R, 9, 7), skin, 0, 0, 0, { s: [1, 1, 1.4] }); add(chest, G.sph(R * 1.08, 9, 7), skin, 0, .0, 0, { s: [1, 1.05, 1.2] });
  add(hips, G.sph(R * .8, 8, 6), belly, 0, -R * .35, .03, { s: [.85, .75, 1.1] }); add(spine, G.sph(R * .85, 8, 6), belly, 0, -R * .4, .0, { s: [.8, .7, 1.4] }); add(chest, G.sph(R * .9, 8, 6), belly, 0, -R * .3, .1, { s: [.8, .9, 1.1] });
  for (let i = 0; i < 7; i++) { const par = i < 2 ? hips : i < 5 ? spine : chest, z = [-.1, .1, -.15, .0, .15, -.1, .1][i]; add(par, G.cone(R * .22, R * (o.spk ?? .8), 4), dark, 0, R * 1.02, z, { r: [-.35, 0, 0], s: [.5, 1, 1] }); }
  // neck chain + head
  const nn = o.neckN ?? 4, nk = neckChain(c, chest, nn, 0, R * .55, R * .75, o.neckLen, R * .85, R * .55, o.curve, skin, { belly, spines: dark, sides: 7 });
  const head = bone('head', nk[nn - 1], 0, o.neckLen, 0), jaw = bone('jaw', head, 0, -.04 * o.hs, .05 * o.hs);
  dragonHead(c, head, jaw, { skin, dark, belly, horn: P.horn, eye: P.eye, ei: P.ei ?? 1, hs: o.hs, horns: o.horns ?? 2, crest: 3, tooth: 0xf0e6d0 });
  if (o.jawOpen) jaw.rotation.x = o.jawOpen;
  if (o.glowMouth) add(jaw, G.box(.05 * o.hs, .01, .12 * o.hs), eyeM(c, P.glow, 1.6), 0, .004, .1 * o.hs);
  // wings
  const W = o.wing, wingK = k => batWing(c, o.quad ? chest : chest, k, { mem: P.mem, memd: P.memd, bone: P.wbone, claw: P.claw, skin, r: W.r, L1: W.L1, Lf: W.Lf, fa: W.fa, tilt: W.tilt, x: W.x ?? .12, y: W.y ?? (o.quad ? .12 : .06), z: W.z ?? -.05 });
  for (const k of [-1, 1]) { const w = wingK(k); w.w.rotation.z = k * (W.up ?? .25); w.wt.rotation.z = k * (W.tipBend ?? -.1); }
  // legs
  for (const k of [-1, 1]) { const Sd = k > 0 ? 'L' : 'R', th = bone('thigh_' + Sd, hips, k * R * .85, -R * .2, -.02), sn = bone('shin_' + Sd, th, 0, -o.legU, 0), ft = bone('foot_' + Sd, sn, 0, -o.legL, 0);
    th.rotation.x = .55; sn.rotation.x = -1.15; ft.rotation.x = .65;
    const LT = o.legT ?? 1; add(th, G.sph(R * .72 * LT, 7, 5), skin, 0, 0, 0, { s: [.9, 1.15, 1.1] }); limb(c, th, o.legU, R * .5 * LT, R * .3 * LT, skin, 6); add(sn, G.sph(R * .3 * LT, 6, 5), skin, 0, 0, 0); limb(c, sn, o.legL, R * .3 * LT, R * .2 * LT, dark, 6);
    add(ft, G.box(R * .5, R * .16, R * .85), dark, 0, -R * .06, R * .3); for (let i = -1; i <= 1; i++) { add(ft, G.cone(R * .07, R * .45, 4), claw, i * R * .17, -R * .06, R * .8, { r: [PI / 2 + .35, 0, 0] }); } add(ft, G.cone(R * .07, R * .4, 4), claw, 0, 0, -R * .1, { r: [-PI / 2 - .5, 0, 0] });
    if (o.quad) { const ar = bone('arm_' + Sd, chest, k * R * .85, -R * .35, R * .45), fo = bone('forearm_' + Sd, ar, 0, -o.legU * .8, 0), ha = bone('hand_' + Sd, fo, 0, -o.legU * .75, 0); ar.rotation.x = .15; fo.rotation.x = -.35; ha.rotation.x = .3;
      add(ar, G.sph(R * .6, 7, 5), skin, 0, 0, 0, { s: [.9, 1.1, 1.1] }); limb(c, ar, o.legU * .8, R * .42, R * .28, skin, 6); limb(c, fo, o.legU * .75, R * .28, R * .22, dark, 6);
      add(ha, G.box(R * .45, R * .14, R * .6), dark, 0, -R * .05, R * .2); for (let i = -1; i <= 1; i++) add(ha, G.cone(R * .06, R * .4, 4), claw, i * R * .15, -R * .05, R * .55, { r: [PI / 2 + .35, 0, 0] }); } }
  // tail chain
  const tl = tailChain(c, hips, o.tailN ?? 6, 0, -.0, -R * .8, o.tailLen, R * .8, R * .08, skin, { belly, spines: dark, tip: o.tailTip });
  tl.forEach((t, i) => { t.rotation.x = i === 0 ? .25 : .05; });
  if (o.pose) { hips.rotation.x = o.pose[0]; spine.rotation.x = o.pose[1]; chest.rotation.x = o.pose[2]; }
  if (o.extra) o.extra(c, { hips, spine, chest, head, jaw, R });
  const upd = (t, mode, Rr, Bn) => { const ph = t * PI * 2, w = mode === 'walk';
    const w1 = mode === 'walk' ? 2 : 1;
    if (w) { Bn.hips.position.y += Math.abs(S(ph)) * .03 * (o.hop ?? 1); Rr('hips', 0, S(ph) * .08); Rr('spine', 0, -S(ph) * .1);
      for (const [Sd, s] of [['L', 0], ['R', PI]]) { const p = ph + s; Rr('thigh_' + Sd, -S(p) * .5); Rr('shin_' + Sd, Math.max(0, Math.cos(p)) * .6); Rr('foot_' + Sd, S(p) * .2); if (o.quad) { Rr('arm_' + Sd, S(p + PI) * .45); Rr('forearm_' + Sd, Math.max(0, Math.cos(p + PI)) * .4); } } }
    for (const Sd of ['L', 'R']) { const k = Sd === 'L' ? 1 : -1; const fl = w ? (o.flap ?? .5) : (o.idleFlap ?? .12); Rr('wing_' + Sd, 0, 0, k * (S(ph * (w ? 2 : 1)) * fl)); Rr('wingTip_' + Sd, 0, 0, k * (S(ph * (w ? 2 : 1) - 1) * fl * .9)); }
    for (let i = 1; i <= nn; i++) Rr('neck_' + i, S(ph - i * .5) * (w ? .06 : .035), S(ph * .5 - i * .4) * .05);
    Rr('head', S(ph * .5) * .04); Rr('jaw', Math.max(0, S(ph * (w ? 2 : .5))) * (w ? .12 : .18));
    for (let i = 1; i <= (o.tailN ?? 6); i++) Rr('tail_' + i, 0, S(ph - i * .7) * (w ? .16 : .09)); };
  return bakeRig(c, root, o.name, upd);
}

// =============================== EMBER WYRMLING ===============================
CHARS5.ember = { name: 'Ember Wyrmling', sheetKey: 'ember', build() {
  const rig = drake({ name: 'Ember_Wyrmling', hipH: .5, R: .2, neckLen: .13, neckN: 4, curve: [1.1, .7, -.2, -.55], pose: [-.1, -.55, -.5], legT: 1.2, legU: .22, legL: .2, hs: 2.7, horns: 3, hop: .6, flap: .55, glowSkin: 1, idleFlap: .1,
    pal: { skin: 0xc8381c, dark: 0x5a1a10, belly: 0xe8a040, claw: 0x2a1410, alt: 0xe05a1a, horn: 0x2a1a14, eye: 0xffc020, ei: 1.2, mem: 0xd8421c, memd: 0xe8761e, wbone: 0x4a1a10, glow: 0xff7a1a },
    wing: { r: .03, L1: .62, Lf: [.78, .82, .7, .52], fa: [1.0, .5, .05, -.4], up: .75, tilt: .35, tipBend: -.15 }, jawOpen: .25, glowMouth: true, tailN: 6, tailLen: .17,
    tailTip: (c, t, r, len) => { const fm = c.M(0xff7a1a, { e: 0xff5a10, ei: 1.2, n: 'tailflame' }); c.add(t, c.G.cone(.05, .17, 4), fm, 0, 0, -len - .06, { r: [-PI / 2, 0, 0] }); c.add(t, c.G.cone(.03, .12, 4), c.M(0xffc040, { e: 0xffb020, ei: 1.5, n: 'flameC' }), 0, .02, -len - .03, { r: [-PI / 2 - .3, 0, 0] }); },
    rockBase: (c, root) => { const { add, G, M } = c, blk = M(0x2a2420, { r: 1, n: 'volcanic' }), blk2 = M(0x3c322c, { r: 1, n: 'volcanic2' }), lava = M(0xff6a14, { e: 0xff5a08, ei: 1.3, n: 'lava' }), lava2 = M(0xffb830, { e: 0xffa020, ei: 1.5, n: 'lava2' });
      add(root, G.cyl(.58, .72, .2, 9), blk, 0, .1, -.05, { s: [1, 1, 1.1] }); for (let i = 0; i < 9; i++) { const a = i / 9 * PI * 2; rock(c, root, i % 2 ? blk : blk2, Math.sin(a) * .62, .16, Math.cos(a) * .66 - .05, .1 + (i % 3) * .02, i + 9); add(root, G.box(.025, .02, .22), i % 2 ? lava : lava2, Math.sin(a) * .38, .205, Math.cos(a) * .4 - .05, { r: [0, a, 0] }); }
      for (let i = 0; i < 6; i++) add(root, G.oct(.018), lava2, Math.sin(i * 1.9) * .5, .35 + i * .12, Math.cos(i * 1.9) * .4 - .1); } });
  rig.root.scale.setScalar(.85); return rig; } };

// =============================== WYVERN STRAFER ===============================
CHARS5.wyvern = { name: 'Wyvern Strafer', sheetKey: 'wyvern', build() {
  const rig = drake({ name: 'Wyvern_Strafer', hipH: .78, R: .27, neckLen: .2, neckN: 5, curve: [.25, .5, .3, -.5, -.55], legT: 1.35, legU: .36, legL: .36, hs: 2.7, horns: 2, hop: 1.2, flap: .45, idleFlap: .08, quad: false, spk: 1.1,
    pal: { skin: 0x5e6a3a, dark: 0x3c3224, belly: 0xb8a070, claw: 0x2a2018, horn: 0x3a3024, eye: 0xd8301c, ei: .8, mem: 0xc89868, memd: 0xa87850, wbone: 0x4a3c28 },
    wing: { r: .05, L1: .8, Lf: [1.05, 1.05, .88, .64], fa: [.8, .35, -.1, -.5], up: .7, tilt: .45, tipBend: -.15, y: .14, x: .13 }, jawOpen: .3, tailN: 7, tailLen: .32,
    tailTip: (c, t, r, len) => { const m = c.M(0x3c3224, { r: .8, n: 'scaledark' }); c.add(t, c.G.cone(.06, .3, 4), m, 0, 0, -len - .12, { r: [-PI / 2, 0, 0], s: [1, .5, 1] }); for (const k of [-1, 1]) c.add(t, c.G.cone(.04, .18, 4), m, k * .04, 0, -len - .02, { r: [-PI / 2 - .2, 0, k * .6], s: [1, .5, 1] }); } });
  rig.root.scale.setScalar(1.6); return rig; } };

// ---------- coiled serpent base: stacked flat tori with scale chevrons ----------
function coils(c, par, o) {
  const { add, G, M } = c, sk = M(o.skin, { r: .75, n: 'scale' }), sk2 = M(o.skin2, { r: .75, n: 'scale2' }), tr = o.trim && M(o.trim, { r: .4, m: .5, n: 'trim' });
  o.rings.forEach(([R, y, t, sx, dx = 0, dz = 0, tz = 0], j) => { const rg = new THREE.Group(); rg.position.set(dx, 0, dz); rg.rotation.z = tz; par.add(rg); const par0 = par; par = rg; add(par, G.tor(R, t, 7, 22), j % 2 ? sk2 : sk, 0, y, 0, { r: [PI / 2, 0, 0], s: [sx ?? 1, 1, 1] });
    const n = Math.round(R * 34); for (let i = 0; i < n; i++) { const a = i / n * PI * 2 + j * .4; add(par, G.cone(t * .5, t * 1.2, 4), i % 3 ? sk2 : (o.alt ? M(o.alt, { r: .7, n: 'scalealt' }) : sk), Math.sin(a) * R * (sx ?? 1) * 1.0, y + t * .75, Math.cos(a) * R, { r: [0, a, 0], s: [1.4, .6, .5] }); }
    if (tr) add(par, G.tor(R, t * .12, 4, 24), tr, 0, y + t * .35, 0, { r: [PI / 2, 0, 0], s: [sx ?? 1, 1, 1] }); par = par0; });
}

// =============================== HYDRELLA ===============================
CHARS5.hydrella = { name: 'Hydrella', sheetKey: 'hydrella', build() {
  const c = makeCtx({ name: 'Hydrella' }), { M, bone, add, G } = c;
  const teal = M(0x1f7d8e, { r: .7, n: 'hscale' }), navy = M(0x15385a, { r: .75, n: 'hscaleD' }), tan = M(0xd8c090, { r: .8, n: 'hbelly' }), fin = M(0x2a5ea0, { r: .6, d: 1, n: 'hfin' }), horn = M(0xe0d4ac, { r: .6, n: 'hhorn' });
  const rk = M(0x4a443c, { r: 1, n: 'rock1' }), rk2 = M(0x2e2a26, { r: 1, n: 'rock2' }), foam = M(0xf2fafc, { r: .6, a: .92, n: 'foam' }), foam2 = M(0xbfe6f0, { r: .5, a: .75, d: 1, n: 'foam2' }), barn = M(0xc8c0a8, { r: 1, n: 'barnacle' });
  const root = bone('root', null), hips = bone('hips', root, 0, .5, 0);
  // rock base with foam
  add(root, G.cyl(.62, .85, .3, 9), rk2, 0, .15, 0); for (let i = 0; i < 14; i++) { const a = i / 14 * PI * 2; rock(c, root, i % 3 ? rk : rk2, Math.sin(a) * .8, .14 + (i % 4) * .05, Math.cos(a) * .8, .17 + (i % 3) * .05, i + 3); } for (let i = 0; i < 6; i++) { const a = i * 1.1 + .3; rock(c, root, rk, Math.sin(a) * .45, .38 + (i % 3) * .06, Math.cos(a) * .45, .14, i + 30); }
  for (let i = 0; i < 12; i++) { const a = i / 12 * PI * 2 + .2, r = .95 + (i % 3) * .08; add(root, G.sph(.12 + (i % 3) * .03, 7, 5), i % 2 ? foam : foam2, Math.sin(a) * r, .1, Math.cos(a) * r, { s: [1.4, .5, 1.4] }); add(root, G.cone(.035, .16 + (i % 4) * .04, 4), foam, Math.sin(a) * (r - .15), .2, Math.cos(a) * (r - .15), { r: [Math.cos(a) * .4, 0, -Math.sin(a) * .4] }); }
  add(root, G.tor(1.05, .045, 5, 24), foam2, 0, .06, 0, { r: [PI / 2, 0, 0] }); for (let i = 0; i < 8; i++) add(root, G.oct(.02), foam, Math.sin(i * 2.3) * .7, .6 + (i % 4) * .12, Math.cos(i * 2.3) * .7);
  for (let i = 0; i < 8; i++) { const a = i * 1.4; add(root, G.cone(.02, .04, 5), barn, Math.sin(a) * .85, .28, Math.cos(a) * .85); }
  // coil/body
  add(hips, G.sph(.48, 10, 8), teal, 0, 0, 0, { s: [1.15, .9, 1.15] }); add(hips, G.sph(.3, 9, 7), navy, 0, .15, -.1, { s: [1, .9, 1] }); for (let i = 0; i < 8; i++) { const a = i * 2.1; add(hips, G.cone(.04, .12, 4), fin, Math.sin(a) * .3, .22, Math.cos(a) * .3 - .1, { r: [-.4, 0, 0], s: [.5, 1, 1] }); }
  const lens = [.2, .22, .25, .22, .2], leans = [.55, .35, .1, -.2, -.45], H = [];
  const base = [[-.36, .08, .05, -1.9], [-.2, .14, .15, -1.0], [0, .16, .1, 0], [.2, .14, .15, 1.0], [.36, .08, .05, 1.9]];
  const curves = [[.6, .25, .0, -.35, -.6, -.5], [.5, .1, -.05, -.25, -.5, -.3], [.1, .1, .05, -.1, -.1, -.2], [.5, .1, -.05, -.25, -.5, -.3], [.6, .25, .0, -.35, -.6, -.5]];
  const NS = 6;
  for (let h = 0; h < 5; h++) { const [x, y, z, yaw] = base[h]; const nb = bone('nbase_' + (h + 1), hips, x, y, z); nb.rotation.y = yaw * .6; const L = [.24, .26, .3, .26, .24][h];
    const nk = neckChain(c, nb, NS, 0, 0, 0, L, .28, .15, curves[h].map((v, i) => i === 0 ? v * (h === 2 ? .3 : 1) : v), teal, { name: `neck${h + 1}_`, belly: tan, spines: navy, side: fin, sides: 8 });
    const head = bone('head_' + (h + 1), nk[NS - 1], 0, L, 0), jaw = bone('jaw_' + (h + 1), head, 0, -.05, .05); jaw.rotation.x = .5;
    dragonHead(c, head, jaw, { skin: teal, dark: navy, belly: tan, horn: 0xe0d4ac, eye: 0xffb020, ei: 1, hs: 2.1, horns: 2, crest: 3, tooth: 0xf6f0dc, fang: true, cheek: 2, cheekM: fin }); tongue(c, jaw, 1.7, 0xb82a40); H.push(h + 1);
    add(head, G.cone(.03, .16, 4), fin, 0, .1, -.1, { r: [-.9, 0, 0], s: [.4, 1, 1] }); }
  const upd = (t, mode, R, B) => { const ph = t * PI * 2, w = mode === 'walk', a = w ? 1 : .5;
    B.hips.position.y += S(ph * (w ? 2 : 1)) * (w ? .03 : .015); R('hips', S(ph) * .02, w ? S(ph) * .15 : 0);
    for (let h = 1; h <= 5; h++) { const o = h * 1.3; for (let i = 1; i <= NS; i++) R(`neck${h}_${i}`, S(ph * (w ? 2 : 1) - i * .55 + o) * .09 * a, S(ph - i * .4 + o) * .08 * a, S(ph * (w ? 2 : 1) - i * .5 + o) * .05 * a);
      R('head_' + h, S(ph + o) * .08 * a); R('jaw_' + h, Math.max(0, S(ph * (w ? 3 : 1) + o * 2)) * .4 * (w ? .6 : 1)); } };
  return bakeRig(c, root, 'Hydrella', upd); } };

// ---------- shared serpent builder: coils + neck + head (+ extras) ----------
function serpent(o) {
  const c = makeCtx({ name: o.name }), { M, bone, add, G } = c, P = o.pal;
  const skin = M(P.skin, { r: .72, n: 'scale' }), dark = M(P.dark, { r: .75, n: 'scaledark' }), belly = M(P.belly, { r: .8, n: 'belly' }), trim = P.trim && M(P.trim, { r: .4, m: .5, n: 'trim' });
  const root = bone('root', null), hips = bone('hips', root, 0, o.y0 ?? .2, 0);
  if (o.ground) o.ground(c, root);
  coils(c, hips, { skin: P.skin, skin2: P.dark, alt: P.alt, trim: P.trim, rings: o.rings });
  const N = o.neckN, nk = neckChain(c, hips, N, 0, o.neckY, o.neckZ ?? 0, o.neckLen, o.r0, o.r1, o.curve, skin, { belly, bands: trim && o.bands ? trim : null, spines: P.spk ? M(P.spk, { r: .5, n: 'spine' }) : dark, side: o.sideS ? M(o.sideS, { r: .5, n: 'sidespine' }) : null, sides: 9 });
  const head = bone('head', nk[N - 1], 0, o.neckLen, 0), jaw = bone('jaw', head, 0, -.04 * o.hs, .05 * o.hs); jaw.rotation.x = o.jaw ?? .4;
  dragonHead(c, head, jaw, { skin, dark, belly, horn: P.horn ?? P.dark, eye: P.eye, ei: P.ei ?? 1, hs: o.hs, horns: 0, crest: o.crest ?? 4, tooth: 0xf6f0dc, fang: true, cheek: o.cheek ?? 2, cheekM: o.cheekM ? M(o.cheekM, { r: .4, n: 'cheek' }) : dark }); tongue(c, jaw, o.hs, P.tongue ?? 0xc0304a);
  if (o.extra) o.extra(c, { hips, root, nk, head, jaw, skin, dark, belly, trim, N });
  const tl = tailChain(c, hips, o.tailN, o.tail[0], o.tail[1], o.tail[2], o.tailLen, o.tail[3], .03, skin, { belly, spines: dark }); tl.forEach((t, i) => { t.rotation.y = (i ? .38 : .9) * (o.tail[4] ?? 1); });
  const upd = (t, mode, R, B) => { const ph = t * PI * 2, w = mode === 'walk';
    if (w) { R('hips', 0, S(ph) * .12); B.hips.position.y += Math.abs(S(ph * 2)) * .015; }
    for (let i = 1; i <= N; i++) { R('neck_' + i, S(ph * (w ? 2 : 1) - i * .55) * (w ? .13 : .06) * (i > 2 ? 1 : .5), S(ph - i * .45) * (w ? .16 : .07)); }
    R('head', S(ph * .5) * .05, S(ph - 3) * .08); R('jaw', Math.max(0, S(ph * (w ? 2 : .5))) * (w ? .18 : .3));
    for (let i = 1; i <= o.tailN; i++) R('tail_' + i, 0, S(ph * (w ? 2 : 1) - i * .7) * (w ? .18 : .1));
    if (o.anim) o.anim(t, mode, R, B); };
  return bakeRig(c, root, o.name, upd);
}
const ruinsP = (c, root, mossy = true) => { const { add, G, M } = c, st = M(0x8a8678, { r: 1, n: 'ruinstone' }), st2 = M(0x6a665a, { r: 1, n: 'ruinstone2' }), dirt = M(0x5a4a38, { r: 1, n: 'ruindirt' });
  add(root, G.cyl(.85, 1.0, .1, 10), dirt, 0, .05, 0);
  for (const [x, z, hh, w] of [[-.75, -.4, .75, .13], [.82, -.35, .55, .12], [-.35, -.85, .9, .14], [.45, -.8, .4, .12], [-.85, .35, .35, .12]]) { for (let i = 0; i < Math.round(hh / .17); i++) add(root, G.box(w * 2 + (i % 2) * .01, .17, w * 2), i % 2 ? st : st2, x, .1 + .085 + i * .17, z, { r: [0, i * .15, 0] }); rock(c, root, st2, x + .05, .1 + hh + .04, z, .08, x * 9 + 2); add(root, G.cyl(w * 1.3, w * 1.3, .05, 6), st, x, .1 + .025, z); }
  for (let i = 0; i < 12; i++) { const a = i / 12 * PI * 2 + .1; rock(c, root, i % 2 ? st : st2, Math.sin(a) * .88, .12, Math.cos(a) * .88, .1 + (i % 3) * .03, i + 60); }
  if (mossy) moss(c, root, 14, .7, .6, 0, .12, 0, .06, 9); };

// =============================== SSYLTHAR THE ANCIENT BASILISK ===============================
CHARS5.ssylthar = { name: 'Ssylthar the Ancient Basilisk', sheetKey: 'ssylthar', build() {
  const rig = serpent({ name: 'Ssylthar', y0: .13, neckN: 6, neckY: .62, neckZ: .05, neckLen: .17, r0: .36, r1: .22, curve: [.05, -.3, -.4, .0, .35, .5], hs: 3.0, jaw: .5, crest: 6, cheek: 3,
    pal: { skin: 0x7a5a30, dark: 0x3e2c1a, belly: 0xd2b27a, alt: 0xc8802e, eye: 0xff2a1a, ei: 1.4, tongue: 0xb82a3a, spk: 0x5a3a1c },
    rings: [[.62, .12, .23, 1.15], [.52, .34, .22, 1.0, .1, -.06, .1], [.42, .54, .2, 1.05, -.08, .05, -.12], [.32, .7, .18, 1.0, .03, -.03, .08]], tailN: 8, tailLen: .24, tail: [.62, .1, .15, .17, 1], ground: (c, root) => ruinsP(c, root),
    extra: (c, o) => { const { add, G, M } = c, claw = M(0x241a10, { r: .5, n: 'claw' });
      for (const k of [-1, 1]) { const Sd = k > 0 ? 'L' : 'R', ar = c.bone('arm_' + Sd, o.nk[0], k * .2, .12, .14), fa = c.bone('forearm_' + Sd, ar, 0, -.2, 0); ar.rotation.set(.6, 0, k * .5); fa.rotation.x = -.8;
        limb(c, ar, .2, .06, .045, o.skin, 6); limb(c, fa, .2, .045, .035, o.dark, 6); add(fa, G.sph(.05, 6, 5), o.dark, 0, -.2, 0, { s: [1, .6, 1.2] }); for (let i = -1; i <= 1; i++) add(fa, G.cone(.012, .14, 4), claw, i * .035, -.22, .06, { r: [PI / 2 + .8, 0, 0] }); }
      for (let i = 0; i < 6; i++) add(o.head, G.cone(.03, .13, 4), M(0xc8802e, { r: .6, n: 'orangespine' }), (i % 2 - .5) * .1, .1, -.06 - i * .03, { r: [-.9, 0, (i % 2 - .5) * .8], s: [.6, 1, 1] }); },
    anim: (t, m, R) => { const ph = t * PI * 2; for (const Sd of ['L', 'R']) { const k = Sd === 'L' ? 1 : -1; R('arm_' + Sd, S(ph * (m === 'walk' ? 2 : 1) + (k > 0 ? 0 : PI)) * (m === 'walk' ? .35 : .08)); } } });
  rig.root.scale.setScalar(1.3); return rig; } };

// =============================== VAELTHRYX THE CRYSTAL SOVEREIGN ===============================
CHARS5.vaelthryx = { name: 'Vaelthryx The Crystal Sovereign', sheetKey: 'vaelthryx', build() {
  const rig = serpent({ name: 'Vaelthryx', y0: .0, neckN: 6, neckY: .78, neckLen: .17, r0: .38, r1: .24, curve: [.05, -.3, -.3, -.05, .2, .1], hs: 3.2, jaw: .55, crest: 0, cheek: 0, bands: true, sideS: 0x4a6ae0,
    pal: { skin: 0x1c2452, dark: 0x0e1230, belly: 0xe8d6b0, trim: 0xd0a040, eye: 0x4ac8ff, ei: 1.6, tongue: 0x7a3ac8, spk: 0x3a5ad8 },
    rings: [[.74, .17, .26, 1.1], [.62, .42, .24, 1.0, .1, -.06, .1], [.5, .64, .22, 1.05, -.08, .05, -.12], [.38, .82, .19, 1.0, .03, -.03, .08]], tailN: 7, tailLen: .26, tail: [.76, .14, .1, .2, 1],
    ground: (c, root) => { const { add, G, M } = c, st = M(0x6a6a7a, { r: 1, n: 'ruinstone' }), st2 = M(0x4a4a58, { r: 1, n: 'ruinstone2' }); add(root, G.cyl(1.05, 1.15, .08, 12), st2, 0, .04, 0); for (let i = 0; i < 10; i++) { const a = i / 10 * PI * 2; rock(c, root, i % 2 ? st : st2, Math.sin(a) * 1.0, .1, Math.cos(a) * 1.0, .1 + (i % 3) * .03, i + 80); } },
    extra: (c, o) => { const { add, G, M, bones } = c, cr = M(0x4a6ae0, { r: .15, e: 0x3a58d0, ei: .6, n: 'crystal' }), cr2 = M(0x9ab8ff, { r: .12, e: 0x6a90ff, ei: .5, n: 'crystal2' }), gold = M(0xd0a040, { r: .35, m: .55, n: 'gold' }), nv = M(0x1c2452, { r: .7, d: 1, n: 'hood' });
      // crystal spines along coils and back
      for (let i = 0; i < 16; i++) { const a = i * 1.7, r = .7 - (i % 4) * .1, y = .3 + (i % 4) * .2; add(o.hips, G.cone(.04 + (i % 3) * .01, .2 + (i % 3) * .1, 5), i % 2 ? cr : cr2, Math.sin(a) * r, y + .15, Math.cos(a) * r, { r: [Math.cos(a) * .3, 0, -Math.sin(a) * .3] }); }
      // hood (flared cobra neck) on neck_6 w/ crystal rim
      const hn = o.nk[4]; const hood = new THREE.Group(); hood.position.set(0, .08, -.14); hood.scale.setScalar(1.6); hn.add(hood);
      add(hood, G.cyl(.34, .34, .035, 14), nv, 0, 0, 0, { r: [PI / 2, 0, 0], s: [1, 1, 1.45] }); add(hood, G.cyl(.25, .25, .036, 12), M(0xe8d6b0, { r: .8, n: 'belly' }), 0, 0, .03, { r: [PI / 2, 0, 0], s: [.9, 1, 1.35] }); add(hood, G.tor(.34, .018, 4, 20), gold, 0, 0, 0, { s: [1, 1.45, 1] });
      for (let i = 0; i < 11; i++) { const a = -PI * .5 + i / 10 * PI * 2 - PI * .5 * 0 - PI * .0; const aa = i / 10 * PI - PI / 2 + PI / 2; const ang = PI * (.05 + .9 * i / 10); add(hood, G.cone(.032, .14 + (i % 2) * .06, 5), i % 2 ? cr : cr2, Math.cos(ang) * .36, Math.sin(ang) * .5, 0, { r: [0, 0, ang - PI / 2] }); add(hood, G.cone(.032, .14 + (i % 2) * .06, 5), i % 2 ? cr : cr2, -Math.cos(ang) * .36, Math.sin(ang) * .5, 0, { r: [0, 0, -(ang - PI / 2)] }); }
      add(hood, G.oct(.06), cr2, 0, -.12, -.03, { s: [1, 2, .6] });
      // crystal crown on the head
      for (let i = 0; i < 9; i++) { const a = (i - 4) * .35; add(o.head, G.cone(.03, .2 + (4 - Math.abs(i - 4)) * .04, 5), i % 2 ? cr : cr2, Math.sin(a) * .13, .2 + Math.cos(a) * .02, -.04 - Math.abs(a) * .04, { r: [-.5, 0, -a * .9] }); }
      for (const k of [-1, 1]) for (let i = 0; i < 4; i++) add(o.head, G.cone(.026, .18 - i * .02, 5), i % 2 ? cr : cr2, k * (.15 + i * .01), .06 - i * .02, -.06 - i * .05, { r: [-.25, 0, -k * (1.15 + i * .1)] });
      add(o.head, G.box(.2, .02, .26), gold, 0, .115, .08, { r: [.05, 0, 0] });
      for (const k of [-1, 1]) add(o.head, G.box(.012, .03, .22), gold, k * .1, .07, .12);
      for (let i = 0; i < 9; i++) add(o.nk[1 + (i % 4)], G.cone(.035, .15, 5), i % 2 ? cr : cr2, (i % 3 - 1) * .05, .1, -.22, { r: [-.9, 0, (i % 3 - 1) * .3], s: [.8, 1, 1] }); } });
  rig.root.scale.setScalar(1.15); return rig; } };

export const ORDER5 = ['frosttroll', 'stonetroll', 'ember', 'hydrella', 'hobgoblin', 'ssylthar', 'wyvern', 'vaelthryx'];
