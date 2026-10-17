// VARNETHRYL 3D prototype kit: procedural low-poly humanoid + props, named bone rig (rigid-parted nodes), idle/walk.
import * as THREE from 'three';
const PI = Math.PI;
export function makeCtx(spec) {
  const mats = new Map();
  const M = (color, o = {}) => {
    const k = color + JSON.stringify(o);
    if (!mats.has(k)) mats.set(k, Object.assign(new THREE.MeshStandardMaterial({
      color, roughness: o.r ?? 0.7, metalness: o.m ?? 0, flatShading: true, side: o.d ? THREE.DoubleSide : THREE.FrontSide,
      emissive: o.e ?? 0x000000, emissiveIntensity: o.ei ?? 1, transparent: o.a !== undefined, opacity: o.a ?? 1 }), { name: o.n || ('m' + mats.size) }));
    return mats.get(k);
  };
  const bones = {};
  const bone = (name, parent, x = 0, y = 0, z = 0) => { const b = new THREE.Bone(); b.name = name; b.position.set(x, y, z); if (parent) parent.add(b); bones[name] = b; return b; };
  const add = (parent, geo, mat, x = 0, y = 0, z = 0, o = {}) => {
    const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z);
    if (o.r) m.rotation.set(...o.r); if (o.s) m.scale.set(...o.s); if (o.n) m.name = o.n; parent.add(m); return m; };
  const G = {
    box: (x, y, z) => new THREE.BoxGeometry(x, y, z),
    cyl: (a, b, h, s = 8, open = false) => new THREE.CylinderGeometry(a, b, h, s, 1, open),
    sph: (r, w = 8, h = 6) => new THREE.SphereGeometry(r, w, h),
    dome: (r, w = 8, h = 4) => new THREE.SphereGeometry(r, w, h, 0, PI * 2, 0, PI / 2),
    cone: (r, h, s = 6) => new THREE.ConeGeometry(r, h, s),
    tor: (r, t, a = 6, b = 12) => new THREE.TorusGeometry(r, t, a, b),
    oct: r => new THREE.OctahedronGeometry(r),
  };
  return { spec, M, bones, bone, add, G };
}

// ---------- emblems (thin gold geometry, face +z) ----------
export function emblem(c, parent, type, size, mat, x = 0, y = 0, z = 0, ry = 0) {
  const { add, G } = c; const g = new THREE.Group(); g.position.set(x, y, z); g.rotation.y = ry; parent.add(g); const s = size, d = 0.012;
  const bar = (w, h, px, py, r = 0) => add(g, G.box(w, h, d), mat, px, py, 0, { r: [0, 0, r] });
  const dia = (r, px, py) => add(g, G.cyl(r, r, d, 4), mat, px, py, 0, { r: [PI / 2, PI / 4, 0] });
  if (type === 'fleur') { bar(s * .13, s * .8, 0, 0); dia(s * .2, 0, s * .3); dia(s * .13, 0, -s * .38);
    for (const k of [-1, 1]) { add(g, G.cone(s * .1, s * .45, 4), mat, k * s * .24, -s * .02, 0, { r: [0, 0, -k * 0.5 + PI] , s: [1, 1, .15] }); add(g, G.sph(s * .08, 6, 4), mat, k * s * .31, -s * .22, 0, { s: [1, 1, .2] }); }
    bar(s * .6, s * .09, 0, -s * .12); }
  else if (type === 'cross') { bar(s * .1, s, 0, 0); bar(s * .6, s * .09, 0, s * .15); for (const [px, py] of [[0, .5], [0, -.5], [-.3, .15], [.3, .15]]) dia(s * .08, px * s, py * s); dia(s * .13, 0, s * .15); }
  else if (type === 'ornate') { bar(s * .12, s, 0, 0); bar(s * .7, s * .1, 0, s * .12); bar(s * .4, s * .08, 0, s * .36); for (const [px, py] of [[0, .52], [0, -.52], [-.37, .12], [.37, .12], [-.2, .36], [.2, .36]]) dia(s * .075, px * s, py * s); }
  else if (type === 'sun') { add(g, G.cyl(s * .26, s * .26, d, 12), mat, 0, 0, 0, { r: [PI / 2, 0, 0] }); for (let i = 0; i < 12; i++) { const a = i / 12 * PI * 2; add(g, G.cone(s * .06, s * .3, 4), mat, Math.sin(a) * s * .42, Math.cos(a) * s * .42, 0, { r: [0, 0, -a], s: [1, 1, .25] }); }
    add(g, G.box(s * .07, s * .34, d * 1.6), c.M(0x20306a), 0, 0, d * .5); add(g, G.box(s * .24, s * .06, d * 1.6), c.M(0x20306a), 0, s * .06, d * .5); }
  else if (type === 'snow') { for (let i = 0; i < 3; i++) add(g, G.box(s * .06, s * .95, d), mat, 0, 0, 0, { r: [0, 0, i * PI / 3] }); for (let i = 0; i < 6; i++) { const a = i * PI / 3; dia(s * .08, Math.sin(a) * s * .47, Math.cos(a) * s * .47); } add(g, G.cyl(s * .12, s * .12, d, 6), mat, 0, 0, 0, { r: [PI / 2, 0, 0] }); }
  else if (type === 'spiral') { add(g, G.tor(s * .3, s * .05, 5, 14), mat); add(g, G.tor(s * .16, s * .045, 5, 10), mat); add(g, G.cyl(s * .06, s * .06, d, 6), mat, 0, 0, 0, { r: [PI / 2, 0, 0] }); for (let i = 0; i < 8; i++) { const a = i / 8 * PI * 2; add(g, G.box(s * .05, s * .14, d), mat, Math.sin(a) * s * .42, Math.cos(a) * s * .42, 0, { r: [0, 0, -a] }); } }
  else if (type === 'gear') { add(g, G.tor(s * .28, s * .07, 5, 12), mat); add(g, G.cyl(s * .08, s * .08, d, 6), mat, 0, 0, 0, { r: [PI / 2, 0, 0] }); for (let i = 0; i < 8; i++) { const a = i / 8 * PI * 2; add(g, G.box(s * .12, s * .16, d), mat, Math.sin(a) * s * .4, Math.cos(a) * s * .4, 0, { r: [0, 0, -a] }); } for (let i = 0; i < 4; i++) bar(s * .05, s * .5, 0, 0, i * PI / 4); }
  else if (type === 'sprig') { bar(s * .05, s, 0, 0); for (let i = 0; i < 5; i++) for (const k of [-1, 1]) add(g, G.cone(s * .1, s * .28, 4), mat, k * s * .14, -s * .3 + i * s * .17, 0, { r: [0, 0, -k * 1.0], s: [1, 1, .2] }); add(g, G.cone(s * .1, s * .28, 4), mat, 0, s * .52, 0, { s: [1, 1, .2] }); }
  else if (type === 'lion') { // crude rampant lion
    add(g, G.sph(s * .2, 6, 5), mat, 0, 0, 0, { s: [.8, 1.3, .2] }); add(g, G.sph(s * .14, 6, 5), mat, s * .06, s * .3, 0, { s: [1, 1, .25] });
    add(g, G.tor(s * .14, s * .05, 4, 8), mat, s * .06, s * .3, 0, { s: [1, 1, .3] });
    for (const [px, py, r] of [[.22, .12, -.9], [.2, -.18, -.5], [-.16, -.28, .4], [.1, -.32, -.2]]) add(g, G.box(s * .07, s * .3, d), mat, px * s, py * s, 0, { r: [0, 0, r] });
    add(g, G.tor(s * .15, s * .035, 4, 8, PI), mat, -s * .26, -s * .12, 0, { s: [.8, 1.3, .3] }); }
  return g;
}
export function skull(c, parent, mat, size, x, y, z) {
  const g = new THREE.Group(); g.position.set(x, y, z); parent.add(g); const { add, G, M } = c;
  add(g, G.sph(size, 7, 5), mat, 0, size * .2, 0, { s: [1, 1, .9] }); add(g, G.box(size * 1.1, size * .5, size * .8), mat, 0, -size * .55, 0);
  for (const k of [-1, 1]) add(g, G.sph(size * .22, 5, 4), M(0x15100a), k * size * .38, size * .15, size * .8, { s: [1, 1.2, .5] });
  return g;
}

// ---------- humanoid base ----------
export function humanoid(c) {
  const sp = c.spec, { M, bone, add, G } = c; const b = sp.bulk ?? 1, sw = sp.sw ?? 1, fem = !!sp.fem;
  const skin = M(sp.skin ?? 0xe3b68f, { r: .8, n: 'skin' });
  const root = bone('root', null); const hips = bone('hips', root, 0, .95, 0), spine = bone('spine', hips, 0, .1, 0), chest = bone('chest', spine, 0, .17, 0);
  const neck = bone('neck', chest, 0, .26, 0), head = bone('head', neck, 0, .04, 0);
  const B = c.bones, cloth = M(sp.under ?? 0x3a2f2a, { r: .9, n: 'under' }), pants = M(sp.pants ?? 0x2e2824, { r: .9, n: 'pants' });
  const waistR = (fem ? .105 : .125) * b, hipR = (fem ? .16 : .14) * b;
  add(hips, G.cyl(hipR, hipR * .92, .17, 8), pants, 0, 0, 0, { s: [1, 1, .72] });
  add(spine, G.cyl(waistR * 1.1, waistR, .2, 8), cloth, 0, .04, 0, { s: [1, 1, .72] });
  const chR = .2 * sw * (fem ? .88 : 1) * Math.sqrt(b);
  add(chest, G.cyl(chR, waistR * 1.25, .31, 8), cloth, 0, .08, 0, { s: [1, 1, .66] });
  if (fem && !sp.nobust) for (const k of [-1, 1]) add(chest, G.sph(.065 * b, 6, 5), cloth, k * .06, .06, .09);
  add(neck, G.cyl(.045, .05, .1, 6), skin, 0, .03, 0);
  // head
  add(head, G.sph(.105, 10, 8), skin, 0, .1, 0, { s: [.98, 1.15, 1.06], n: 'head' }); add(head, G.box(.085, .07, .08), skin, 0, .03, .03);
  for (const k of [-1, 1]) { add(head, G.sph(.012, 4, 3), M(0x120c08), k * .036, .115, .097); add(head, G.box(.04, .008, .01), M(sp.hair ?? 0x3a2a1a), k * .036, .14, .098, { r: [0, 0, k * -.12] }); }
  add(head, G.box(.016, .03, .02), skin, 0, .09, .104);
  for (const k of [-1, 1]) {
    const S = k > 0 ? 'L' : 'R', sh = bone('shoulder_' + S, chest, k * .19 * sw * (fem ? .9 : 1), .22, 0), ua = bone('upperArm_' + S, sh, k * .05, 0, 0), fa = bone('foreArm_' + S, ua, 0, -.29, 0), hd = bone('hand_' + S, fa, 0, -.27, 0);
    const ar = .05 * b * (fem ? .88 : 1), slv = M(sp.sleeve ?? sp.under ?? 0x3a2f2a, { r: .9 });
    const lim = (par, len, r0, r1, mat, y0 = 0) => { const g = G.cyl(r0, r1, len, 8); g.translate(0, -len / 2 + y0, 0); add(par, g, mat); };
    lim(ua, .3, ar, ar * .85, slv); add(ua, G.sph(ar * 1.02, 6, 5), slv); lim(fa, .28, ar * .85, ar * .66, slv); add(fa, G.sph(ar * .85, 6, 5), slv);
    add(hd, G.sph(.045, 6, 5), M(sp.glove ?? sp.skin ?? 0x3a2a1a, { r: .8 }), 0, -.04, 0, { s: [1, 1.25, .85] });
    const th = bone('thigh_' + S, hips, k * .1 * (fem ? 1.15 : 1), -.03, 0), sn = bone('shin_' + S, th, 0, -.44, 0), ft = bone('foot_' + S, sn, 0, -.43, 0);
    const tr = .08 * b * (fem ? .95 : 1);
    const l2 = (par, len, r0, r1, mat) => { const g = G.cyl(r0, r1, len, 8); g.translate(0, -len / 2, 0); add(par, g, mat); };
    l2(th, .45, tr, tr * .74, pants); add(th, G.sph(tr * 1.0, 6, 5), pants); l2(sn, .44, tr * .74, tr * .55, pants);
    add(ft, G.box(.11, .07, .27), M(sp.boot ?? 0x3b2a1c, { r: .85, n: 'boot' }), 0, -.012, .05); add(sn, G.cyl(.065 * b, .06 * b, .26, 8), M(sp.boot ?? 0x3b2a1c, { r: .85, n: 'boot' }), 0, -.3, 0);
  }
  return { root, hips, spine, chest, neck, head, skin };
}

// ---------- armour & clothing kit ----------
export function platePack(c, o) { // o: steel, trim, pauld ('plate'|'spike'), cuirass color mat, greaves, tasset...
  const { M, bones: B, add, G } = c; const b = c.spec.bulk ?? 1, sw = c.spec.sw ?? 1, fem = !!c.spec.fem, steel = o.steel, trim = o.trim;
  const chR = .2 * sw * (fem ? .88 : 1) * Math.sqrt(b);
  add(B.chest, G.cyl(chR * 1.1, chR * .8, .27, 8), o.cuirass ?? steel, 0, .1, .005, { s: [1, 1, .72] });
  add(B.chest, G.cyl(chR * .78, chR * .66, .08, 8), steel, 0, -.07, 0, { s: [1, 1, .75] });
  add(B.neck, G.cyl(.075, .09, .08, 8), steel, 0, .0, 0);
  for (const k of [-1, 1]) {
    const S = k > 0 ? 'L' : 'R', sh = B['shoulder_' + S], ua = B['upperArm_' + S], fa = B['foreArm_' + S], hd = B['hand_' + S], th = B['thigh_' + S], sn = B['shin_' + S], ft = B['foot_' + S];
    const pr = .105 * b * (o.bigPauld ? 1.2 : 1);
    add(sh, G.dome(pr, 8, 4), steel, k * .05, .01, 0, { s: [1.15, .85, 1.1], r: [0, 0, -k * .3] });
    add(sh, G.dome(pr * .92, 8, 3), steel, k * .08, -.05, 0, { s: [1.1, .8, 1.05], r: [0, 0, -k * .35] }); add(sh, G.dome(pr * .8, 8, 3), trim, k * .1, -.1, 0, { s: [1.05, .7, 1], r: [0, 0, -k * .4] });
    if (o.pauld === 'spike') for (let i = 0; i < 4; i++) add(sh, G.cone(.022, .09 + i % 2 * .03, 4), steel, k * (.04 + i * .02), .07 - i * .005, (i - 1.5) * .045, { r: [(i - 1.5) * .35, 0, -k * (.5 + i * .12)] });
    if (o.bigPauld) add(sh, G.cyl(.012, .012, .12, 5), trim, k * .06, .06, 0, { r: [PI / 2, 0, 0] });
    add(ua, G.cyl(.058 * b, .052 * b, .17, 8), steel, 0, -.12, 0); add(ua, G.cyl(.052 * b, .05 * b, .02, 8), trim, 0, -.2, 0);
    add(fa, G.cyl(.055 * b, .045 * b, .2, 8), steel, 0, -.12, 0); add(fa, G.cyl(.058 * b, .056 * b, .02, 8), trim, 0, -.02, 0); add(fa, G.sph(.058 * b, 6, 5), steel, 0, 0, -.015, { s: [1, .7, 1] });
    if (!o.noGaunt) add(hd, G.box(.07, .09, .06), steel, 0, -.035, 0);
    if (o.cuisse !== false) add(th, G.cyl(.09 * b, .075 * b, .26, 8), steel, 0, -.18, 0);
    add(sn, G.cyl(.068 * b, .06 * b, .13, 8), steel, 0, -.02, 0, { s: [1, 1, .95] }); add(sn, G.cone(.045 * b, .06, 4), steel, 0, .0, .065, { r: [PI / 2, PI / 4, 0] });
    if (o.greaves !== false) add(sn, G.cyl(.062 * b, .05 * b, .3, 8), steel, 0, -.25, .006);
    add(sn, G.cyl(.064 * b, .064 * b, .02, 8), trim, 0, -.4, 0);
    add(ft, G.box(.11, .045, .21), steel, 0, .0, .07, { r: [-.1, 0, 0] });
  }
  if (o.tassets !== false) for (let i = -1; i <= 1; i++) add(B.hips, G.box(.1, .17, .02), steel, i * .105, -.14, .14 - Math.abs(i) * .035, { r: [-.18, -i * .35, 0] });
}
export function belt(c, mat, buckle, y = 0, z = .15) {
  const { add, G, bones: B } = c; const b = c.spec.bulk ?? 1, fem = c.spec.fem;
  add(B.spine, G.cyl(.14 * b * (fem ? .88 : 1), .145 * b, .055, 8), mat, 0, -.03 + y, 0, { s: [1, 1, .75] });
  add(B.spine, G.box(.05, .045, .02), buckle, 0, -.03 + y, .105 * b + .03);
}
export function strapX(c, mat, buckle) { // chest baldric
  const { add, G, bones: B } = c;
  add(B.chest, G.box(.05, .42, .02), mat, -.02, .1, .125, { r: [0, 0, .6] }); add(B.chest, G.box(.04, .04, .025), buckle, -.04, .0, .132);
}
export function hair(c, style, col, o = {}) {
  const { add, G, M, bones: B } = c, h = M(col, { r: .85, n: 'hair' }), hd = B.head;
  add(hd, new THREE.SphereGeometry(.113, 10, 8, 0, PI * 2, 0, PI * .56), h, 0, .105, -.005, { s: [.95, 1.1, 1.05] });
  const tuft = (x, y, z, rx, rz, s = 1) => add(hd, G.cone(.03 * s, .09 * s, 4), h, x, y, z, { r: [rx, 0, rz] });
  if (style === 'short' || style === 'swept') { tuft(.04, .2, .06, .9, -.3); tuft(-.02, .205, .07, .9, .2); tuft(.075, .17, .03, .6, -.8); tuft(-.07, .18, .05, .7, .7); if (style === 'swept') { tuft(0, .22, .02, .3, 0, 1.3); } }
  if (style === 'messy') { for (let i = 0; i < 7; i++) tuft(Math.sin(i * 1.3) * .07, .19 + (i % 3) * .01, Math.cos(i * 1.3) * .06, Math.sin(i) * .8, Math.cos(i * 2) * .8, 1.1); }
  if (style === 'long' || style === 'wavy') {
    const L = o.len ?? .5;
    add(hd, G.box(.2, L, .09), h, 0, .1 - L / 2 + .02, -.085, { s: [1, 1, 1] });
    for (let i = 0; i < 4; i++) for (const k of [-1, 1]) add(hd, G.sph(.045 + (style === 'wavy' ? .015 : 0), 6, 5), h, k * (.085 + (i % 2) * .02 * (style === 'wavy' ? 1 : 0)), .0 - i * L * .26, -.07, { s: [1, 2.4, 1] });
    for (const k of [-1, 1]) add(hd, G.box(.04, L * .7, .06), h, k * .1, .03 - L * .35, .005);
    tuft(0, .21, .08, 1.1, 0, 1.2); tuft(.07, .18, .08, .9, -.7); tuft(-.07, .18, .08, .9, .7);
  }
  if (style === 'bun') { tuft(.04, .2, .06, .9, -.3); tuft(-.04, .2, .06, .9, .3); add(hd, G.sph(.06, 7, 5), h, 0, .24, -.08); add(hd, G.sph(.045, 6, 5), h, .045, .21, -.1); }
  if (style === 'curly') { for (let i = 0; i < 9; i++) add(hd, G.sph(.045, 5, 4), h, Math.sin(i * 0.7) * .1, .19 + (i % 3) * .01, Math.cos(i * .7) * .08 - .01); }
}
export function hood(c, mat, open = .7) {
  const { add, G, bones: B } = c;
  add(B.head, new THREE.SphereGeometry(.14, 10, 8, PI / 2 + open, PI * 2 - open * 2, 0, PI * .78), mat, 0, .08, -.015, { s: [1.02, 1.12, 1.15] });
  add(B.neck, G.cyl(.14, .19, .16, 8, true), mat, 0, -.02, -.01, { s: [1, 1, 1.05] });
}
export function furCollar(c, mat, r = .19, t = .065) { const { add, G, bones: B } = c; add(B.chest, G.tor(r * .88, t, 6, 12), mat, 0, .2, 0, { r: [PI / 2 - .12, 0, 0], s: [1, 1.15, 1] }); }

// cape / cloak from curved patches (top pivot at chest bone 'cape')
export function cape(c, o) {
  const { add, M, bones: B, bone } = c; const cb = bone('cape', B.chest, 0, .25, 0);
  const CW = o.segs ?? 14, rnd = (i => () => (i = (i * 16807) % 2147483647) / 2147483647)(o.seed ?? 11);
  const teeth = Array.from({ length: CW + 1 }, () => rnd());
  const pos = (u, f) => {
    const w = o.topW + (o.botW - o.topW) * f, x = u * w, wave = Math.sin(u * (o.waves ?? 9) + f * 1.5) * (o.fold ?? .028) * f;
    let y = -f * o.len; if (o.ragged && f > .78) y -= (f - .78) / .22 * o.ragged * teeth[Math.round((u + .5) * CW)];
    const z = -(o.back ?? .12) - f * .07 - f * f * (o.flare ?? .12) + wave + (u * 2) ** 2 * (o.wrap ?? .1) * (1 - f * .6);
    return [x, y, z - Math.abs(u) * .02];
  };
  const patch = (f0, f1, u0, u1, nu, nv, mat, dz = 0) => {
    const v = [], idx = [];
    for (let j = 0; j <= nv; j++) for (let i = 0; i <= nu; i++) { const p = pos(u0 + (u1 - u0) * i / nu, f0 + (f1 - f0) * j / nv); v.push(p[0], p[1], p[2] - dz); }
    for (let j = 0; j < nv; j++) for (let i = 0; i < nu; i++) { const a = j * (nu + 1) + i, b2 = a + 1, c2 = a + nu + 1, d = c2 + 1; idx.push(a, c2, b2, b2, c2, d); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(v, 3)); g.setIndex(idx); g.computeVertexNormals(); add(cb, g, mat); };
  const mat = M(o.col, { r: .95, d: 1, n: 'cape' });
  patch(0, 1, -.5, .5, CW, 7, mat);
  if (o.trim) { const tm = M(o.trim, { r: .5, m: .5, d: 1, n: 'capetrim' }); if (o.ragged) { patch(.86, 1, -.5, .5, CW, 1, tm, .004); } else patch(.9, 1, -.5, .5, CW, 1, tm, .004);
    patch(0, 1, -.5, -.47, 1, 7, tm, .004); patch(0, 1, .47, .5, 1, 7, tm, .004); }
  if (o.lining) { /* inner lining visible through double side; second slightly offset patch */ patch(0, 1, -.5, .5, CW, 7, M(o.lining, { r: .95, d: 1, n: 'lining' }), -.006); }
  return { cb, backPos: (f) => pos(0, f), z: (f) => pos(0, f)[2] };
}
export function tabard(c, o) { // flat pointed panel front/back
  const { add, M, bones: B } = c, W = o.w, L = o.len;
  const sh = new THREE.Shape(); sh.moveTo(-W / 2, 0); sh.lineTo(W / 2, 0); sh.lineTo(W / 2, -L); if (o.point) { sh.lineTo(0, -L - o.point); } sh.lineTo(-W / 2, -L); sh.closePath();
  const ex = { depth: .01, bevelEnabled: false }, mk = (mat, w = 1) => new THREE.ExtrudeGeometry(sh, ex);
  const mat = M(o.col, { r: .9, n: 'tabard' }), tm = M(o.trim, { r: .45, m: .4, n: 'tabardtrim' });
  const g = new THREE.Group(); g.position.set(0, o.y ?? .05, o.z ?? .145); g.rotation.x = o.tilt ?? -.06; B.hips.add(g);
  add(g, mk(mat), mat, 0, 0, 0);
  for (const k of [-1, 1]) add(g, new THREE.BoxGeometry(.016, L + (o.point ?? 0) * .3, .014), tm, k * (W / 2 - .008), -L / 2 - (o.point ?? 0) * .15 + .01, .006);
  add(g, new THREE.BoxGeometry(W, .018, .014), tm, 0, -L + .01, .006);
  if (o.emblem) emblem(c, g, o.emblem, W * .62, tm, 0, -L * .32, .017);
  if (o.emblem2) emblem(c, g, o.emblem2, W * .38, tm, 0, -L * .74, .017);
  return g;
}
export function skirt(c, o) {
  const { add, M, bones: B, G } = c; const mat = M(o.col, { r: .9, d: 1, n: 'skirt' });
  const g = G.cyl(o.top ?? .17, o.bot ?? .34, o.len, o.segs ?? 14, true); g.translate(0, -o.len / 2, 0);
  if (o.ragged) { const p = g.attributes.position; for (let i = 0; i < p.count; i++) if (p.getY(i) < -o.len + .01) p.setY(i, p.getY(i) - Math.abs(Math.sin(i * 2.7)) * o.ragged); g.computeVertexNormals(); }
  const m = add(B.hips, g, mat, 0, o.y ?? -.02, 0, { s: [1, 1, o.zs ?? .92] });
  if (o.trim) add(B.hips, G.cyl((o.bot ?? .34) * 1.0, (o.bot ?? .34) * 1.0, .035, o.segs ?? 14, true), M(o.trim, { r: .5, m: .5, d: 1, n: 'skirttrim' }), 0, (o.y ?? -.02) - o.len + .02, 0, { s: [1, 1, o.zs ?? .92] });
  return m;
}
export function pouch(c, par, col, x, y, z, s = 1, gold) { const { add, G, M } = c; add(par, G.box(.09 * s, .1 * s, .045 * s), M(col, { r: .85 }), x, y, z); add(par, G.box(.095 * s, .035 * s, .05 * s), M(col, { r: .85 }), x, y + .045 * s, z); if (gold) add(par, G.box(.02 * s, .03 * s, .01), gold, x, y + .01 * s, z + .026 * s); }

// ---------- weapons & props (origin at grip, extends along +y) ----------
export function sword(c, o) {
  const { M, add, G } = c, g = new THREE.Group(), bl = M(o.blade ?? 0xcfd6dd, { r: .3, m: .4, e: o.glow ?? 0, ei: o.glow ? 1.4 : 1, n: 'blade' }), gold = o.gold;
  const L = o.len ?? .85; add(g, G.cyl(.016, .016, .13, 6), M(o.grip ?? 0x4a2b18), 0, -.02, 0); add(g, G.box(o.guard ?? .22, .028, .03), gold, 0, .055, 0);
  add(g, G.sph(.026, 6, 5), gold, 0, -.095, 0); add(g, G.sph(.015, 5, 4), M(o.gem ?? 0x2c6dff, { e: o.gem ?? 0x2c6dff, ei: .6 }), 0, .055, .02);
  const sh = new THREE.Shape(); sh.moveTo(-.03, 0); sh.lineTo(.03, 0); sh.lineTo(.026, L); sh.lineTo(0, L + .08); sh.lineTo(-.026, L); sh.closePath();
  const bg = new THREE.ExtrudeGeometry(sh, { depth: .012, bevelEnabled: false }); bg.translate(0, .07, -.006); add(g, bg, bl);
  return g; }
export function rapier(c, gold, len = 1.0) {
  const { M, add, G } = c, g = new THREE.Group(); add(g, G.cyl(.014, .014, .11, 6), M(0x3a2415), 0, -.03, 0); add(g, G.sph(.026, 6, 5), gold, 0, -.095, 0);
  add(g, G.tor(.055, .008, 4, 12), gold, 0, .05, 0, { r: [PI / 2, 0, 0] }); add(g, G.tor(.045, .007, 4, 10), gold, 0, .06, 0, { r: [0, PI / 2, 0], s: [1, 1.3, 1] }); add(g, G.box(.14, .012, .012), gold, 0, .07, 0);
  add(g, G.sph(.014, 5, 4), M(0x2c6dff, { e: 0x2c6dff, ei: .6 }), 0, .035, .03);
  add(g, G.cyl(.005, .011, len, 4), M(0xd5dce2, { r: .25, m: .9 }), 0, .09 + len / 2, 0); return g; }
export function dagger(c, gold) {
  const { M, add, G } = c, g = new THREE.Group(); add(g, G.cyl(.015, .015, .1, 6), M(0x5a3a22), 0, -.03, 0); add(g, G.box(.1, .022, .03), gold, 0, .035, 0); add(g, G.sph(.02, 5, 4), gold, 0, -.09, 0);
  add(g, G.cyl(.001, .028, .28, 4), M(0xaeb6bd, { r: .35, m: .4 }), 0, .18, 0, { s: [1, 1, .35] }); return g; }
export function mace(c, o) {
  const { M, add, G } = c, g = new THREE.Group(), gold = o.gold; add(g, G.cyl(.022, .022, .72, 6), M(0x4a2b18), 0, .22, 0);
  for (const y of [-.05, .45]) add(g, G.cyl(.03, .03, .05, 6), gold, 0, y, 0); add(g, G.sph(.035, 6, 5), gold, 0, -.15, 0);
  const hy = .62; add(g, G.sph(.085, 8, 6), gold, 0, hy, 0); add(g, G.cyl(.07, .07, .02, 8), M(0x20306a), 0, hy, .075, { r: [PI / 2, 0, 0] });
  for (let i = 0; i < 12; i++) { const a = i / 12 * PI * 2; add(g, G.cone(.026, .11, 4), gold, Math.sin(a) * .1, hy + Math.cos(a) * .1, 0, { r: [0, 0, -a] }); }
  add(g, G.cone(.026, .1, 4), gold, 0, hy, .11, { r: [PI / 2, 0, 0] }); add(g, G.cone(.026, .1, 4), gold, 0, hy, -.11, { r: [-PI / 2, 0, 0] }); return g; }
export function kiteShield(c, o) {
  const { M, add } = c, g = new THREE.Group(); const kite = k => { const s = new THREE.Shape(); const w = .22 * k, t = .3 * k; s.moveTo(-w, t); s.lineTo(w, t); s.lineTo(w, 0); s.quadraticCurveTo(w * .8, -.3 * k, 0, -.46 * k); s.quadraticCurveTo(-w * .8, -.3 * k, -w, 0); s.closePath(); return s; };
  add(g, new THREE.ExtrudeGeometry(kite(1.08), { depth: .02, bevelEnabled: false, curveSegments: 6 }), o.rim, 0, 0, -.012);
  add(g, new THREE.ExtrudeGeometry(kite(.93), { depth: .03, bevelEnabled: false, curveSegments: 6 }), o.face, 0, 0, .0);
  add(g, new THREE.ExtrudeGeometry(kite(.9), { depth: .02, bevelEnabled: false, curveSegments: 6 }), M(0x4a2b18, { r: .9 }), 0, 0, -.03);
  if (o.emblem) emblem(c, g, o.emblem, .36, o.rim, 0, .05, .033); if (o.studs) for (let i = 0; i < 8; i++) { const a = i / 8 * PI * 2; }
  return g; }
export function crossbow(c, o) {
  const { M, add, G } = c, g = new THREE.Group(), wood = M(o.wood ?? 0x5a3a22, { r: .85 }), met = o.metal, gold = o.gold;
  add(g, G.box(.06, .08, .62), wood, 0, 0, .12); add(g, G.box(.075, .06, .26), met, 0, .05, .28); add(g, G.cyl(.028, .028, .5, 6), met, 0, .08, .2, { r: [PI / 2, 0, 0] });
  add(g, G.box(.5, .025, .03), gold, 0, .01, .45, { r: [0, .0, 0] }); for (const k of [-1, 1]) add(g, G.box(.3, .022, .028), wood, k * .38, .01, .38, { r: [0, k * .35, 0] }); add(g, G.box(.01, .01, .02), M(0xe8e0c8), 0, .015, .3);
  add(g, G.tor(.045, .012, 5, 10), gold, 0, .06, .1, { r: [0, PI / 2, 0] }); add(g, G.box(.04, .12, .05), wood, 0, -.09, 0, { r: [.3, 0, 0] });
  add(g, G.cone(.012, .1, 4), M(0xd0d6dc, { m: .9, r: .3 }), 0, .09, .55, { r: [PI / 2, 0, 0] });
  if (o.gear) { add(g, G.tor(.05, .016, 5, 10), gold, .045, .02, .15, { r: [0, PI / 2, 0] }); for (let i = 0; i < 6; i++) { const a = i / 6 * PI * 2; add(g, G.box(.012, .02, .02), gold, .05, .02 + Math.cos(a) * .07, .15 + Math.sin(a) * .07); } add(g, G.cyl(.034, .034, .3, 8), M(0x8a6a3a, { m: .4, r: .4 }), .0, -.0, .33, { r: [PI / 2, 0, 0] }); }
  if (o.banner) { add(g, G.box(.02, .22, .16), M(o.banner, { r: .9, d: 1 }), 0, -.13, .36); emblem(c, g, 'cross', .1, gold, .012, -.13, .36, PI / 2); }
  return g; }
export function staffHead(c, type, o) {
  const { M, add, G } = c, g = new THREE.Group(), gold = o.gold, wood = o.wood;
  if (type === 'storm' || type === 'leaf') {
    const orbC = type === 'storm' ? 0x4aa8ff : 0x74ff62; const orb = M(orbC, { e: orbC, ei: 1.5, r: .2, n: 'orb' });
    add(g, G.sph(.07, 8, 6), orb, 0, .1, 0); add(g, G.sph(.1, 8, 6), M(orbC, { e: orbC, ei: .5, a: .22 }), 0, .1, 0);
    for (let i = 0; i < 7; i++) { const a = i / 7 * PI * 2; add(g, G.cyl(.012, .02, .26, 5), wood, Math.sin(a) * .09, .06, Math.cos(a) * .09, { r: [Math.cos(a) * .6, 0, -Math.sin(a) * .6] }); add(g, G.cone(.015, .1, 4), wood, Math.sin(a) * .18, .2, Math.cos(a) * .18, { r: [Math.cos(a) * .7, 0, -Math.sin(a) * .7] }); }
    if (type === 'leaf') for (let i = 0; i < 6; i++) { const a = i / 6 * PI * 2 + .3; add(g, G.cone(.03, .08, 4), M(0x3f8f3a), Math.sin(a) * .13, .04 + (i % 2) * .08, Math.cos(a) * .13, { r: [Math.cos(a) * 1.2, 0, -Math.sin(a) * 1.2], s: [1, 1, .3] }); }
    if (type === 'storm') for (let i = 0; i < 3; i++) { add(g, G.tor(.035, .008, 4, 8), gold, (i - 1) * .1, -.05 - i % 2 * .05, .0, { r: [0, 1.2, 0] }); add(g, G.cone(.012, .1, 4), M(i % 2 ? 0xf0ead8 : 0x2c5fa8, { d: 1 }), (i - 1) * .1, -.15 - i % 2 * .05, 0, { s: [1, 1, .3], r: [PI, 0, 0] }); } }
  if (type === 'crystal') { const cr = M(0x6ec8ff, { e: 0x3a9cff, ei: .9, r: .1, m: .1, n: 'crystal' });
    add(g, G.oct(.06), cr, 0, .15, 0, { s: [.7, 1.8, .7] }); add(g, G.tor(.08, .012, 4, 10), gold, 0, .08, 0, { r: [0, 0, 0] }); add(g, G.tor(.1, .012, 4, 10), gold, 0, .12, 0, { r: [0, PI / 2, 0], s: [.6, 1.6, 1] });
    for (const k of [-1, 1]) { add(g, G.oct(.035), cr, k * .12, .12, 0, { s: [.7, 1.8, .7] }); add(g, G.cone(.02, .12, 4), gold, k * .07, .04, 0, { r: [0, 0, -k * 1.0] }); add(g, G.oct(.03), cr, k * .13, -.1, 0, { s: [.7, 1.7, .7] }); } }
  if (type === 'star') { add(g, G.cyl(.075, .075, .03, 12), gold, 0, .13, 0, { r: [PI / 2, 0, 0] }); add(g, G.sph(.04, 7, 5), M(0xfff0b0, { e: 0xffd060, ei: .8 }), 0, .13, .02, { s: [1, 1, .7] });
    for (let i = 0; i < 16; i++) { const a = i / 16 * PI * 2, L = i % 2 ? .08 : .15; add(g, G.cone(.02, L, 4), gold, Math.sin(a) * (.08 + L / 2), .13 + Math.cos(a) * (.08 + L / 2), 0, { r: [0, 0, -a], s: [1, 1, .6] }); }
    add(g, G.box(.025, .2, .02), gold, 0, .13, 0); add(g, G.box(.2, .025, .02), gold, 0, .13, 0); }
  return g; }
export function staff(c, type, o) {
  const { M, add, G } = c, g = new THREE.Group(), wood = o.wood, L = o.len ?? 1.75, top = L * .5 - .05;
  if (o.twist) for (let i = 0; i < 6; i++) add(g, G.cyl(.026, .022, L / 6, 6), M(i % 2 ? o.wood2 ?? 0x6a4528 : 0x4a2f1a), 0, -L * .5 + .0 + (i + .5) * L / 6 - .17, 0, { r: [0, 0, (i % 2) * .08 - .04] });
  else add(g, G.cyl(.022, .026, L, 6), wood, 0, -.17, 0);
  add(g, G.cyl(.032, .032, .1, 6), o.gold, 0, -.0, 0); add(g, G.cone(.02, .08, 5), o.gold, 0, -.17 - L / 2 - .02, 0, { r: [PI, 0, 0] });
  const h = staffHead(c, type, o); h.position.y = top - .17 + .0; g.add(h); return { g, top: h };
}
export function book(c, cover, gold, w = .17, h = .23) {
  const { M, add, G } = c, g = new THREE.Group(); add(g, G.box(w, h, .05), M(cover, { r: .8 }), 0, 0, 0); add(g, G.box(w * .9, h * .96, .045), M(0xe9ddbc), .01, 0, 0); add(g, G.box(.025, h, .056), M(0x3a2415), -w / 2, 0, 0);
  add(g, G.box(w * 1.0, h * 1.0, .052), M(cover, { r: .8 }), 0, 0, 0, { s: [1, 1, .2] }); for (const [px, py] of [[1, 1], [-1, 1], [1, -1], [-1, -1]]) add(g, G.box(.03, .03, .056), gold, px * w * .46, py * h * .46, 0);
  return g; }
export function censer(c, gold) { const { add, G } = c, g = new THREE.Group(); add(g, G.sph(.045, 8, 6), gold, 0, -.18, 0); add(g, G.cone(.03, .05, 6), gold, 0, -.13, 0); add(g, G.cyl(.012, .012, .15, 4), gold, 0, -.05, 0); add(g, G.sph(.012, 4, 3), gold, 0, 0, 0);
  for (let i = 0; i < 6; i++) add(g, G.tor(.012, .004, 4, 6), gold, 0, -.01 - i * .03, 0, { r: [i % 2 * PI / 2, 0, 0] }); return g; }
export function vial(c, gold, liquid = 0xe0262e) { const { add, G, M } = c, g = new THREE.Group(); add(g, G.cyl(.016, .016, .07, 6), M(liquid, { e: liquid, ei: .5, a: .85 }), 0, 0, 0); add(g, G.cyl(.018, .018, .015, 6), gold, 0, .04, 0); add(g, G.cyl(.018, .018, .015, 6), gold, 0, -.04, 0); return g; }
export function lantern(c, gold) { const { add, G, M } = c, g = new THREE.Group(); add(g, G.cyl(.03, .03, .07, 6), M(0xffd27a, { e: 0xffb84a, ei: 1.2, a: .9 }), 0, 0, 0); add(g, G.cone(.04, .03, 6), gold, 0, .055, 0); add(g, G.cyl(.032, .032, .012, 6), gold, 0, -.04, 0); return g; }
export function goggles(c, gold, strap) { const { add, G, M, bones: B } = c; for (const k of [-1, 1]) { add(B.head, G.cyl(.04, .04, .03, 8), gold, k * .05, .225, .07, { r: [PI / 2 - .5, 0, 0] }); add(B.head, G.cyl(.03, .03, .035, 8), M(0x5ac8e0, { e: 0x2a8caf, ei: .5, r: .1, m: .3 }), k * .05, .228, .08, { r: [PI / 2 - .5, 0, 0] }); } add(B.head, G.tor(.115, .012, 4, 12), strap, 0, .19, -.005, { r: [PI / 2 - .1, 0, 0], s: [.95, 1.1, 1] }); }
export function feather(c, par, col, x, y, z, rot, len = .22) { const { add, G, M } = c; const f = add(par, G.cone(.026, len, 4), M(col, { r: .9, d: 1 }), x, y, z, { r: rot, s: [1, 1, .25] }); return f; }
export function rope(c, par, x, y, z, col = 0xb89868) { const { add, G, M } = c; for (let i = 0; i < 3; i++) add(par, G.tor(.07 - i * .004, .014, 4, 10), M(col, { r: .95 }), x, y - i * .025, z, { r: [PI / 2, 0, i * .4] }); }
export function leafCluster(c, par, n, rad, col, y0, z0 = 0, spread = 1) { const { add, G, M } = c; for (let i = 0; i < n; i++) { const a = i / n * PI * 2 * spread; add(par, G.cone(.04, .12, 4), M(i % 3 ? col : 0x4f9a3f, { r: .9, d: 1 }), Math.sin(a) * rad, y0 - (i % 3) * .025, z0 + Math.cos(a) * rad, { r: [Math.cos(a) * 1.6, 0, -Math.sin(a) * 1.6], s: [1, 1, .3] }); } }

// ---------- animation (procedural; also baked into GLB clips) ----------
export const HELD = { }; // per-rig flags in rig.hold
export function finalize(c, root, hold = {}, poseFn) {
  const grp = new THREE.Group(); grp.name = c.spec.name; grp.add(root);
  // rest pose
  const B = c.bones, a = (n, x, y, z) => B[n] && B[n].rotation.set(x, y, z);
  a('upperArm_L', 0, 0, .13); a('upperArm_R', 0, 0, -.13); a('foreArm_L', -.3, 0, 0); a('foreArm_R', -.3, 0, 0); if (poseFn) poseFn(B);
  for (const k in B) B[k].userData.rest = { r: B[k].rotation.clone(), p: B[k].position.clone() };
  const names = Object.keys(B);
  const update = (t, mode) => {
    for (const n of names) { const b = B[n], r = b.userData.rest; b.rotation.copy(r.r); b.position.copy(r.p); }
    const R = (n, x = 0, y = 0, z = 0) => { const b = B[n]; if (!b) return; b.rotation.x += x; b.rotation.y += y; b.rotation.z += z; };
    if (mode === 'walk') {
      const ph = t * PI * 2;
      for (const [S, s] of [['L', 0], ['R', PI]]) {
        const p = ph + s; R('thigh_' + S, -Math.sin(p) * .55); R('shin_' + S, Math.max(0, Math.cos(p)) * .85 + .05); R('foot_' + S, Math.sin(p) * .15 - .05);
        if (!hold[S]) { R('upperArm_' + S, Math.sin(p) * .42); R('foreArm_' + S, -Math.max(0, -Math.sin(p)) * .25); }
        else R('upperArm_' + S, Math.sin(p) * .05);
      }
      B.hips.position.y += Math.cos(ph * 2) * .02; R('hips', 0, Math.sin(ph) * .12, 0); R('spine', 0, -Math.sin(ph) * .1, Math.sin(ph) * .02); R('chest', .03, -Math.sin(ph) * .06, 0); R('head', 0, Math.sin(ph) * .05);
      R('cape', .12 + Math.sin(ph * 2 - 1) * .07, Math.sin(ph) * .03, Math.sin(ph) * .03);
      for (const n of ['tabard']) { }
    } else {
      const ph = t * PI * 2;
      R('chest', Math.sin(ph) * .012); R('spine', Math.sin(ph) * .008); R('head', Math.sin(ph * .5) * .02, Math.sin(ph * .5) * .05);
      if (!hold.L) R('upperArm_L', 0, 0, Math.sin(ph) * .015); if (!hold.R) R('upperArm_R', 0, 0, -Math.sin(ph) * .015);
      B.hips.position.y += Math.sin(ph) * .004; R('cape', .02 + Math.sin(ph + 1) * .02, 0, Math.sin(ph * .5) * .01);
    }
  };
  update(0, 'idle');
  const clip = (mode, dur, N) => {
    const times = [...Array(N)].map((_, i) => i * dur / N); const rec = {}; const hp = [];
    times.forEach(t => { update(mode === 'walk' ? t / dur : t / dur, mode); for (const n of names) { (rec[n] ??= []).push(...B[n].quaternion.toArray()); } hp.push(...B.hips.position.toArray()); });
    const tracks = [];
    for (const n of names) { const r = B[n].userData.rest, q0 = new THREE.Quaternion().setFromEuler(r.r), arr = rec[n]; let moved = false; for (let i = 0; i < N; i++) { const dq = Math.abs(arr[i * 4] - q0.x) + Math.abs(arr[i * 4 + 1] - q0.y) + Math.abs(arr[i * 4 + 2] - q0.z) + Math.abs(arr[i * 4 + 3] - q0.w); if (dq > 1e-4) { moved = true; break; } } if (moved) tracks.push(new THREE.QuaternionKeyframeTrack(n + '.quaternion', times, arr)); }
    tracks.push(new THREE.VectorKeyframeTrack('hips.position', times, hp)); update(0, 'idle');
    return new THREE.AnimationClip(mode, dur, tracks); };
  return { root: grp, bones: B, update, clips: () => [clip('idle', 3, 12), clip('walk', 1, 16)], hold };
}
