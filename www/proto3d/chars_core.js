// VARNETHRYL 3D prototype kit: procedural low-poly humanoid + props, named bone rig (rigid-parted nodes), idle/walk.
import * as THREE from 'three';
import { surface, decal, faceTex } from './texgen.js';
const PI = Math.PI;
export function makeCtx(spec) {
  const mats = new Map();
  const M = (color, o = {}) => {
    const k = color + JSON.stringify(o);
    if (!mats.has(k)) {
      const emis = o.e !== undefined, plain = !emis && o.a === undefined, met = (o.m ?? 0) >= .3, ro = o.r ?? .7;
      const t = o.t ?? (plain && met ? 'steel' : plain && !met && ro >= .85 && (!o.n || /^(under|pants|cape|lining|tabard|skirt|blue|hood|fur|magic)/.test(o.n)) ? 'cloth' : null);
      const mt = Object.assign(new THREE.MeshStandardMaterial({
        color, roughness: ro, metalness: o.m ?? 0, flatShading: !!o.f, side: o.d ? THREE.DoubleSide : THREE.FrontSide,
        emissive: o.e ?? 0x000000, emissiveIntensity: o.ei ?? 1, transparent: o.a !== undefined, opacity: o.a ?? 1 }), { name: o.n || ('m' + mats.size) });
      if (t) mt.map = surface(t);
      mats.set(k, mt);
    }
    return mats.get(k);
  };
  const bones = {};
  const bone = (name, parent, x = 0, y = 0, z = 0) => { const b = new THREE.Bone(); b.name = name; b.position.set(x, y, z); if (parent) parent.add(b); bones[name] = b; return b; };
  const add = (parent, geo, mat, x = 0, y = 0, z = 0, o = {}) => {
    const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z);
    if (o.r) m.rotation.set(...o.r); if (o.s) m.scale.set(...o.s); if (o.n) m.name = o.n; parent.add(m); return m; };
  const sm = n => n === 8 ? 16 : n === 7 ? 12 : n === 6 ? 8 : n;
  const G = {
    box: (x, y, z) => new THREE.BoxGeometry(x, y, z),
    cyl: (a, b, h, s = 8, open = false) => new THREE.CylinderGeometry(a, b, h, sm(s), 1, open),
    sph: (r, w = 8, h = 6) => new THREE.SphereGeometry(r, Math.round(w * 1.7), Math.round(h * 1.7)),
    dome: (r, w = 8, h = 4) => new THREE.SphereGeometry(r, sm(w), h * 2, 0, PI * 2, 0, PI / 2),
    cone: (r, h, s = 6) => new THREE.ConeGeometry(r, h, s),
    tor: (r, t, a = 6, b = 12) => new THREE.TorusGeometry(r, t, Math.max(a, 6), b * 2),
    oct: r => new THREE.OctahedronGeometry(r),
  };
  return { spec, M, bones, bone, add, G };
}

// ---------- emblems (thin gold geometry, face +z) ----------
export function emblem(c, parent, type, size, mat, x = 0, y = 0, z = 0, ry = 0) {
  const g = new THREE.Group(); g.position.set(x, y, z); g.rotation.y = ry; parent.add(g);
  const m = decalMat(c, type, mat); const pl = new THREE.Mesh(new THREE.PlaneGeometry(size, size), m); pl.position.z = .004; pl.name = 'emblem_' + type; g.add(pl); return g;
}
const dmCache = new Map();
function decalMat(c, type, mat) {
  const col = mat && mat.color ? mat.color.getHex() : 0xd2a43c, k = type + col; if (!dmCache.has(k)) dmCache.set(k, new THREE.MeshStandardMaterial({ map: decal(type), color: col, metalness: .45, roughness: .4, alphaTest: .5, name: 'emb_' + type + col.toString(16), polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2, side: THREE.DoubleSide }));
  return dmCache.get(k);
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
  const neck = bone('neck', chest, 0, .26, 0), head = bone('head', neck, 0, .03, 0);
  const B = c.bones, cloth = M(sp.under ?? 0x3a2f2a, { r: .9, n: 'under' }), pants = M(sp.pants ?? 0x2e2824, { r: .9, n: 'pants' });
  const waistR = (fem ? .105 : .125) * b, hipR = (fem ? .16 : .14) * b;
  add(hips, G.cyl(hipR, hipR * .92, .17, 8), pants, 0, 0, 0, { s: [1, 1, .72] });
  add(spine, G.cyl(waistR * 1.1, waistR, .2, 8), cloth, 0, .04, 0, { s: [1, 1, .72] });
  const chR = .2 * sw * (fem ? .88 : 1) * Math.sqrt(b);
  add(chest, G.cyl(chR, waistR * 1.25, .31, 8), cloth, 0, .08, 0, { s: [1, 1, .66] });
  if (fem && !sp.nobust) for (const k of [-1, 1]) add(chest, G.sph(.065 * b, 6, 5), cloth, k * .06, .06, .09);
  add(neck, G.cyl(.045, .05, .1, 6), skin, 0, .03, 0);
  // head: smooth sphere with painted face, chin, nose, ears
  const faceMat = new THREE.MeshStandardMaterial({ map: faceTex({ skin: sp.skin ?? 0xe3b68f, hair: sp.hair ?? 0x3a2a1a, eye: sp.eye ?? 0x4a78b8, fem, brow: sp.brow, scar: sp.scar, beard: sp.beard }), roughness: .75, name: 'face' });
  add(head, G.sph(.105, 14, 10), faceMat, 0, .1, 0, { s: [.95, 1.14, 1.04], n: 'head' });
  add(head, G.sph(.06, 8, 6), skin, 0, .045, .03, { s: [fem ? .95 : 1.15, .8, .95], n: 'jaw' });
  add(head, G.sph(.011, 5, 4), skin, 0, .09, .104, { s: [.9, 1.2, 1] }); // nose
  for (const k of [-1, 1]) { if (sp.elf) add(head, G.cone(.026, .13, 6), skin, k * .105, .12, -.005, { r: [0, 0, -k * 1.15], s: [1, 1, .35] }); else add(head, G.sph(.02, 5, 4), skin, k * .098, .098, -.005, { s: [.45, 1, .75] }); }
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
    add(ft, G.sph(.065, 8, 6), M(sp.boot ?? 0x3b2a1c, { r: .85, n: 'boot', t: 'leather' }), 0, -.015, .07, { s: [.95, .62, 2.1] }); add(sn, G.cyl(.065 * b, .06 * b, .26, 8), M(sp.boot ?? 0x3b2a1c, { r: .85, n: 'boot' }), 0, -.3, 0);
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
  { // layered fauld, breastplate ridge, gorget, gold bands (extra detail pass)
    const hipR = (fem ? .16 : .14) * b;
    for (let i = 0; i < 3; i++) add(B.hips, G.cyl(hipR * (1.12 + i * .03), hipR * (1.06 + i * .03), .06, 8, true), steel, 0, .0 - i * .045, 0, { s: [1, 1, .74] });
    add(B.hips, G.cyl(hipR * 1.14, hipR * 1.14, .014, 8), trim, 0, .03, 0, { s: [1, 1, .74] });
    add(B.chest, G.box(.022, .26, .03), trim, 0, .1, chR * .72 + .012, { r: [-.05, 0, 0] }); add(B.chest, G.cyl(chR * 1.12, chR * 1.1, .018, 8), trim, 0, -.02, 0, { s: [1, 1, .72] });
    add(B.chest, G.cyl(chR * .86, chR * 1.0, .035, 8), trim, 0, .23, 0, { s: [1, 1, .7] });
    add(B.neck, G.cyl(.082, .082, .018, 10), trim, 0, .045, 0);
    for (const k of [-1, 1]) { const S = k > 0 ? 'L' : 'R', sn = B['shin_' + S], ft = B['foot_' + S], th = B['thigh_' + S], hd = B['hand_' + S];
      add(sn, G.sph(.07 * b, 7, 5), steel, 0, 0, .035, { s: [1, .8, .8] }); add(sn, G.tor(.062 * b, .009, 4, 8), trim, 0, .02, 0, { r: [PI / 2, 0, 0] }); add(sn, G.tor(.05 * b, .009, 4, 8), trim, 0, -.3, 0, { r: [PI / 2, 0, 0] });
      add(ft, G.cone(.055, .13, 8), steel, 0, -.005, .2, { r: [PI / 2, 0, 0], s: [1.1, 1, .55] });
      add(th, G.tor(.082 * b, .009, 4, 8), trim, 0, -.31, 0, { r: [PI / 2, 0, 0] });
      for (let i = 0; i < 4; i++) add(hd, G.box(.012, .05, .016), steel, (i - 1.5) * .017, -.1, .02 - Math.abs(i - 1.5) * .006); }
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
// tapered tube along points (pts = array of [x,y,z]); radius r0->r1; flat = z-squash
export function taper(pts, r0, r1, seg = 10, rad = 7, flat = .55) {
  const cur = new THREE.CatmullRomCurve3(pts.map(p => new THREE.Vector3(...p))), pos = [], idx = [], fr = cur.computeFrenetFrames(seg, false);
  for (let i = 0; i <= seg; i++) { const t = i / seg, p = cur.getPoint(t), r = r0 + (r1 - r0) * Math.pow(t, .8); for (let j = 0; j < rad; j++) { const a = j / rad * PI * 2, n = fr.normals[i], b = fr.binormals[i];
      pos.push(p.x + (n.x * Math.cos(a) * r + b.x * Math.sin(a) * r * flat), p.y + (n.y * Math.cos(a) * r + b.y * Math.sin(a) * r * flat), p.z + (n.z * Math.cos(a) * r + b.z * Math.sin(a) * r * flat)); } }
  for (let i = 0; i < seg; i++) for (let j = 0; j < rad; j++) { const a = i * rad + j, b = i * rad + (j + 1) % rad, c2 = a + rad, d = b + rad; idx.push(a, b, c2, b, d, c2); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals();
  const uv = []; for (let i = 0; i <= seg; i++) for (let j = 0; j < rad; j++) uv.push(j / rad, i / seg); g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); return g;
}
function hairCap(r, front, back, rise = 0) { // hair cap with hairline: leaves the face open
  const g = new THREE.SphereGeometry(r, 28, 16, 0, PI * 2, 0, PI * .75), p = g.attributes.position, sm = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
  for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i), z = p.getZ(i), th = Math.acos(Math.max(-1, Math.min(1, y / r))), ph = Math.atan2(z, -x), fd = Math.abs(ph - PI / 2) / (PI * .46), lim = front + (back - front) * sm(.25, 1, fd), t = th / (PI * .75);
    const th2 = t * lim, rr = r; p.setXYZ(i, -Math.cos(ph) * Math.sin(th2) * rr, Math.cos(th2) * rr, Math.sin(ph) * Math.sin(th2) * rr); }
  g.computeVertexNormals(); return g;
}
export function hair(c, style, col, o = {}) {
  const { add, G, M, bones: B } = c, h = M(col, { r: .8, n: 'hair', t: 'hair', m: .08 }), hd = B.head;
  const cap = add(hd, hairCap(.112, PI * .385, PI * .64), h, 0, .1, -.004, { s: [.97, 1.17, 1.07], n: 'hair_cap' });
  const lock = (pts, r0, r1, seg = 9, flat = .55) => add(hd, taper(pts, r0, r1, seg, 7, flat), h);
  const tuft = (x, y, z, rx, rz, s = 1) => add(hd, G.cone(.03 * s, .1 * s, 6), h, x, y, z, { r: [rx, 0, rz], s: [1, 1, .6] });
  const front = (sweep = 1) => { for (const k of [-1, 1]) lock([[k * .02, .205, .075], [k * .06 * sweep, .205, .1], [k * .098, .165, .09], [k * .108, .13, .055]], .022, .006, 7, .5); lock([[0, .21, .06], [.03 * sweep, .222, .105], [.065 * sweep, .19, .115], [.08 * sweep, .16, .095]], .026, .006, 7, .5); };
  if (style === 'short') { front(.7); for (let i = 0; i < 6; i++) { const a = -.5 + i * .2; lock([[Math.sin(a) * .06, .225, Math.cos(a) * .02 - .03], [Math.sin(a) * .1, .235, -.01], [Math.sin(a) * .12, .19, -.06]], .02, .005, 6); } }
  if (style === 'swept') { front(1.6); lock([[-.02, .21, .07], [.0, .245, .09], [.05, .26, .07], [.09, .235, .03]], .03, .008, 8); lock([[-.05, .205, .07], [-.03, .24, .08], [.02, .255, .05]], .024, .006, 7); for (let i = 0; i < 5; i++) { const a = -.6 + i * .3; lock([[Math.sin(a) * .06, .22, -.03], [Math.sin(a) * .11, .215, -.06], [Math.sin(a) * .105, .15, -.1]], .024, .005, 6); } }
  if (style === 'messy') { front(.8); for (let i = 0; i < 9; i++) { const a = i / 9 * PI * 2, sa = Math.sin(a), ca = Math.cos(a); lock([[sa * .045, .222, ca * .05], [sa * .095, .232 + (i % 3) * .008, ca * .085], [sa * .13, .195 + (i % 2) * .02, ca * .1 - (ca < 0 ? .04 : 0)]], .03, .006, 6, .7); } }
  if (style === 'long' || style === 'wavy') {
    const L = o.len ?? .5, w = style === 'wavy' ? 1 : .3;
    for (let i = 0; i < 9; i++) { const a = -1.1 + i * .275, sa = Math.sin(a), ca = Math.cos(a), ph = i * 1.3;
      lock([[sa * .08, .2, -ca * .06 - .02], [sa * .115, .1, -ca * .095 - .02], [sa * .13 + Math.sin(ph) * .02 * w, .1 - L * .35, -.12 - ca * .02], [sa * .12 - Math.sin(ph) * .035 * w, .1 - L * .7, -.125], [sa * .1 + Math.sin(ph + 1) * .03 * w, .1 - L, -.12 - Math.abs(sa) * .02]], .034, .006, 12, .5); }
    for (const k of [-1, 1]) { lock([[k * .09, .17, .02], [k * .115, .07, .02], [k * .125 + k * .01 * w, .0 - L * .15, .045], [k * .13 - k * .02 * w, -.09 - L * .22, .08], [k * .11 + k * .02 * w, -.12 - L * .4, .09]], .028, .006, 12, .55); lock([[k * .1, .18, .0], [k * .122, .08, -.04], [k * .14, -.04 - L * .15, -.06], [k * .15 - k * .02 * w, -.1 - L * .4, -.05]], .026, .005, 10, .55); }
    front(1.1);
  }
  if (style === 'bun') { front(.8); lock([[-.09, .2, .0], [-.1, .13, -.07], [-.06, .1, -.12], [.0, .12, -.12]], .02, .006, 7); lock([[.09, .2, .0], [.1, .13, -.07], [.06, .1, -.12], [.0, .12, -.12]], .02, .006, 7); add(hd, G.sph(.065, 8, 6), h, 0, .245, -.1); add(hd, G.tor(.062, .014, 5, 10), h, 0, .245, -.1, { r: [.4, 0, 0] }); lock([[.0, .15, -.115], [.0, .08, -.15], [.01, .0, -.14]], .03, .01, 8); }
  if (style === 'curly') { front(.7); for (let i = 0; i < 16; i++) { const a = i / 16 * PI * 2 * 1.4 + .3, sa = Math.sin(a), ca = Math.cos(a); add(hd, G.sph(.04 + (i % 3) * .004, 6, 5), h, sa * .1, .17 + (i % 4) * .018, ca * .09 - .015 - (ca < 0 ? .03 : 0)); } for (let i = 0; i < 6; i++) { const k = i % 2 ? 1 : -1; add(hd, G.sph(.05, 6, 5), h, k * (.1 + (i > 3 ? .015 : 0)), .1 - (i >> 1) * .055, -.045, { s: [.8, 1.2, .9] }); } }
}
export function hood(c, mat, open = .7) {
  const { add, G, bones: B } = c;
  add(B.head, new THREE.SphereGeometry(.14, 10, 8, PI / 2 + open, PI * 2 - open * 2, 0, PI * .78), mat, 0, .08, -.015, { s: [1.02, 1.12, 1.15] });
  add(B.neck, G.cyl(.14, .19, .16, 8, true), mat, 0, -.02, -.01, { s: [1, 1, 1.05] });
}
export function furCollar(c, mat, r = .19, t = .065) { const { add, G, bones: B } = c; add(B.chest, G.tor(r * .88, t * .8, 6, 12), mat, 0, .2, 0, { r: [PI / 2 - .12, 0, 0], s: [1, 1.15, 1] }); }

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
  const decalOn = (type, size, mtl, f, uc = 0) => { // decal conforming to the cape surface (outer/back side)
    const w = o.topW + (o.botW - o.topW) * f, du = size / w, df = size / o.len, nu = 8, nv = 8, v = [], uv = [], idx = [], m = decalMat(c, type, mtl);
    for (let j = 0; j <= nv; j++) for (let i = 0; i <= nu; i++) { const a = i / nu, b = j / nv, p = pos(uc / w + (a - .5) * du, f + (b - .5) * df); v.push(p[0], p[1], p[2] - .008); uv.push(1 - a, 1 - b); }
    for (let j = 0; j < nv; j++) for (let i = 0; i < nu; i++) { const a = j * (nu + 1) + i, b2 = a + 1, c2 = a + nu + 1, d = c2 + 1; idx.push(a, b2, c2, b2, d, c2); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(v, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); g.setIndex(idx); g.computeVertexNormals(); const me = add(cb, g, m); me.name = 'cape_' + type; return me; };
  return { cb, backPos: (f) => pos(0, f), z: (f) => pos(0, f)[2], decal: decalOn };
}
export function tabard(c, o) { // flat pointed panel front/back
  const { add, M, bones: B } = c, W = o.w, L = o.len;
  const sh = new THREE.Shape(); sh.moveTo(-W / 2, 0); sh.lineTo(W / 2, 0); sh.lineTo(W / 2, -L); if (o.point) { sh.lineTo(0, -L - o.point); } sh.lineTo(-W / 2, -L); sh.closePath();
  const ex = { depth: .01, bevelEnabled: false }, mk = (mat, w = 1) => new THREE.ExtrudeGeometry(sh, ex);
  const mat = M(o.col, { r: .9, n: 'tabard' }), tm = o.trim.isMaterial ? o.trim : M(o.trim, { r: .45, m: .4, n: 'tabardtrim' });
  const g = new THREE.Group(); g.position.set(0, o.y ?? .05, o.z ?? .145); g.rotation.x = o.tilt ?? -.06; B.hips.add(g);
  add(g, mk(mat), mat, 0, 0, 0);
  for (const k of [-1, 1]) add(g, new THREE.BoxGeometry(.016, L + (o.point ?? 0) * .3, .014), tm, k * (W / 2 - .008), -L / 2 - (o.point ?? 0) * .15 + .01, .006);
  add(g, new THREE.BoxGeometry(W, .018, .014), tm, 0, -L + .01, .006);
  if (o.emblem) emblem(c, g, o.emblem, W * .62, tm, 0, -L * .32, .017);
  if (o.emblem2) emblem(c, g, o.emblem2, W * .38, tm, 0, -L * .74, .017);
  return g;
}
let skirtN = 0;
export function skirt(c, o) { // front & back panels on their own bones that follow the legs (no more legs through robes)
  const { add, M, bones: B, G, bone } = c; const mat = M(o.col, { r: .9, d: 1, n: 'skirt' }), n = skirtN++, segs = o.segs ?? 16, top = o.top ?? .17, bot = (o.bot ?? .34) * 1.08;
  const panel = (name, ts) => {
    const pv = bone('skirt' + name + n, B.hips, 0, o.y ?? -.02, 0); const g = new THREE.CylinderGeometry(top, bot, o.len, segs, 3, true, ts, PI); g.translate(0, -o.len / 2, 0);
    const p = g.attributes.position; for (let i = 0; i < p.count; i++) { const yy = p.getY(i), f = -yy / o.len, th = Math.atan2(p.getX(i), p.getZ(i)); if (o.ragged && f > .99) p.setY(i, yy - Math.abs(Math.sin(i * 2.7 + th * 5)) * o.ragged); const w = Math.sin(th * 5 + f * 3) * .012 * f; p.setX(i, p.getX(i) * (1 + w / bot)); p.setZ(i, p.getZ(i) * (1 + w / bot)); }
    g.computeVertexNormals(); add(pv, g, mat, 0, 0, 0, { s: [1, 1, o.zs ?? .92] });
    if (o.trim) add(pv, new THREE.CylinderGeometry(bot * 1.005, bot * 1.005, .04, segs, 1, true, ts, PI), M(o.trim, { r: .5, m: .5, d: 1, n: 'skirttrim' }), 0, -o.len + .015, 0, { s: [1, 1, o.zs ?? .92] });
    return pv; };
  panel('F', -PI / 2); panel('B', PI / 2); c.skirts = (c.skirts || 0) + 1;
  return B['skirtF' + n];
}
export function pouch(c, par, col, x, y, z, s = 1, gold) { const { add, G, M } = c; add(par, G.box(.09 * s, .1 * s, .045 * s), M(col, { r: .85 }), x, y, z); add(par, G.box(.095 * s, .035 * s, .05 * s), M(col, { r: .85 }), x, y + .045 * s, z); if (gold) add(par, G.box(.02 * s, .03 * s, .01), gold, x, y + .01 * s, z + .026 * s); }

// ---------- weapons & props (origin at grip, extends along +y) ----------
export function sword(c, o) {
  const { M, add, G } = c, g = new THREE.Group(), bl = M(o.blade ?? 0xcfd6dd, { r: .3, m: .4, e: o.glow ?? 0, ei: o.glow ? 1.4 : 1, n: 'blade' }), gold = o.gold;
  const L = o.len ?? .85; add(g, G.cyl(.016, .016, .13, 6), M(o.grip ?? 0x4a2b18), 0, -.02, 0); add(g, G.box(o.guard ?? .22, .028, .03), gold, 0, .055, 0);
  add(g, G.sph(.026, 6, 5), gold, 0, -.095, 0); add(g, G.sph(.015, 5, 4), M(o.gem ?? 0x2c6dff, { e: o.gem ?? 0x2c6dff, ei: .6 }), 0, .055, .02);
  const sh = new THREE.Shape(); const W = o.wide ?? 1; sh.moveTo(-.03 * W, 0); sh.lineTo(.03 * W, 0); sh.lineTo(.026 * W, L); sh.lineTo(0, L + .08); sh.lineTo(-.026 * W, L); sh.closePath();
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
export function bow(c, o) { // grip at origin, limbs along +-y, tips curve toward the archer (-z)
  const { add, G, M } = c, g = new THREE.Group(), wood = M(o.wood ?? 0x5a3520, { r: .6, t: 'leather', n: 'bowwood' }), gold = o.gold, L = o.len ?? .74, pts = [];
  for (let i = -5; i <= 5; i++) { const t = i / 5; pts.push([0, t * L, -.2 * t * t * t * t - .12 * t * t]); }
  add(g, taper(pts.slice(5), .016, .008, 12, 6, 1), wood); add(g, taper(pts.slice(0, 6).reverse(), .016, .008, 12, 6, 1), wood);
  add(g, G.cyl(.02, .02, .13, 8), M(0x3a2415, { r: .9, n: 'grip' }), 0, 0, 0);
  for (const k of [-1, 1]) { const t = k * .55, y = t * L, z = -.2 * t * t * t * t - .12 * t * t; add(g, G.tor(.022, .005, 4, 8), gold, 0, y, z, { r: [PI / 2, 0, 0] }); add(g, G.sph(.018, 5, 4), M(0x3fbf5a, { e: 0x2f9f45, ei: .4, n: 'gem' }), 0, y * .8, z * .78 + .01, { s: [1, 1.5, 1] }); add(g, G.sph(.012, 4, 3), gold, 0, k * L, -.32 * 0 + (-.2 - .12)); }
  const tz = -.32, sg = G.cyl(.0025, .0025, L * 2, 4); add(g, sg, M(0xe8e0c8, { n: 'string' }), 0, 0, tz); return g; }
export function quiver(c, o) { // tilted back quiver with arrows; origin at its centre
  const { add, G, M } = c, g = new THREE.Group(), lea = M(0x6a4326, { r: .8, t: 'leather', n: 'leather' }), gold = o.gold;
  add(g, G.cyl(.065, .055, .5, 10), lea, 0, 0, 0); add(g, G.tor(.066, .01, 4, 10), gold, 0, .2, 0, { r: [PI / 2, 0, 0] }); add(g, G.tor(.058, .01, 4, 10), gold, 0, -.2, 0, { r: [PI / 2, 0, 0] }); add(g, G.cone(.055, .06, 10), lea, 0, -.28, 0, { r: [PI, 0, 0] });
  add(g, G.cyl(.05, .05, .02, 10), M(0x2a1a10), 0, .25, 0);
  for (let i = 0; i < 7; i++) { const a = i / 7 * PI * 2, rx = Math.sin(a) * .03, rz = Math.cos(a) * .03, tilt = [Math.cos(a) * .08, 0, -Math.sin(a) * .08]; add(g, G.cyl(.005, .005, .3, 4), M(0x8a6a40, { n: 'arrow' }), rx, .33, rz, { r: tilt }); for (let f = 0; f < 3; f++) add(g, G.cone(.014, .08, 4), M(i % 2 ? 0xf2eee0 : 0x3f8f50, { d: 1, n: 'fletch' }), rx, .42 + f * .005, rz, { r: [tilt[0], f * 2.1, tilt[2]], s: [1, 1, .25] }); }
  return g; }
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
export const REG = {}; // per-character rework hooks (chars7.js): REG[spec.name] = c => add extra geometry before rig bake
export function finalize(c, root, hold = {}, poseFn) {
  if (REG[c.spec.name]) REG[c.spec.name](c);
  const grp = new THREE.Group(); grp.name = c.spec.name; grp.add(root);
  // rest pose
  const B = c.bones, a = (n, x, y, z) => B[n] && B[n].rotation.set(x, y, z);
  a('upperArm_L', 0, 0, .13); a('upperArm_R', 0, 0, -.13); a('foreArm_L', -.3, 0, 0); a('foreArm_R', -.3, 0, 0); if (poseFn) poseFn(B);
  for (const k in B) B[k].userData.rest = { r: B[k].rotation.clone(), p: B[k].position.clone() };
  const names = Object.keys(B);
  const update = (t, mode) => {
    for (const n of names) { const b = B[n], r = b.userData.rest; b.rotation.copy(r.r); b.position.copy(r.p); }
    const R = (n, x = 0, y = 0, z = 0) => { const b = B[n]; if (!b) return; b.rotation.x += x; b.rotation.y += y; b.rotation.z += z; };
    const skirtDrive = () => { const tl = B.thigh_L.rotation.x, tr = B.thigh_R.rotation.x, fw = Math.min(0, tl, tr), bk = Math.max(0, tl, tr), ky = Math.max(0, B.shin_L.rotation.x, B.shin_R.rotation.x);
      for (const n in B) { if (n.startsWith('skirtF')) B[n].rotation.x += fw * .95 - ky * .0; else if (n.startsWith('skirtB')) B[n].rotation.x += bk * .95; } };
    if (mode === 'walk') {
      const ph = t * PI * 2;
      for (const [S, s] of [['L', 0], ['R', PI]]) {
        const p = ph + s; R('thigh_' + S, -Math.sin(p) * .55); R('shin_' + S, Math.max(0, Math.cos(p)) * .85 + .05); R('foot_' + S, Math.sin(p) * .15 - .05);
        if (!hold[S]) { R('upperArm_' + S, Math.sin(p) * .42); R('foreArm_' + S, -Math.max(0, -Math.sin(p)) * .25); }
        else R('upperArm_' + S, Math.sin(p) * .05);
      }
      B.hips.position.y += Math.cos(ph * 2) * .02; R('hips', 0, Math.sin(ph) * .12, 0); R('spine', 0, -Math.sin(ph) * .1, Math.sin(ph) * .02); R('chest', .03, -Math.sin(ph) * .06, 0); R('head', 0, Math.sin(ph) * .05);
      R('cape', .12 + Math.sin(ph * 2 - 1) * .07, Math.sin(ph) * .03, Math.sin(ph) * .03); skirtDrive();
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

// ---------- batch 2 kit (bows, axes, lutes, fur, glyphs, wolf helpers) ----------
export function furMantle(c, fur, dark, r = .27, t = .1) {
  const { add, G, bones: B } = c; const b = c.spec.bulk ?? 1;
  add(B.chest, G.tor(r * .88, t, 6, 12), fur, 0, .2, 0, { r: [PI / 2 - .12, 0, 0], s: [1, 1.15, 1] });
  for (const k of [-1, 1]) { const sh = B['shoulder_' + (k > 0 ? 'L' : 'R')];
    add(sh, G.dome(.15 * b, 8, 4), fur, k * .05, .03, 0, { s: [1.25, .9, 1.25], r: [0, 0, -k * .25] });
    for (let i = 0; i < 7; i++) { const a = i / 7 * PI * 2; add(sh, G.cone(.04 * b, .1, 4), i % 2 ? dark : fur, k * .05 + Math.sin(a) * .15 * b, -.03, Math.cos(a) * .15 * b, { r: [Math.cos(a) * 2.5, 0, -Math.sin(a) * 2.5 + k * .3], s: [1, 1, .6] }); } }
  for (let i = 0; i < 9; i++) { const a = i / 9 * PI * 2; add(B.chest, G.cone(.045, .1, 4), i % 2 ? dark : fur, Math.sin(a) * r * 1.02, .15, Math.cos(a) * r * 1.0 * .8, { r: [PI + Math.cos(a) * .5, 0, -Math.sin(a) * .5], s: [1, 1, .6] }); }
}
export function furCuff(c, bone, fur, r, y, t = .035) { c.add(bone, c.G.tor(r, t, 5, 10), fur, 0, y, 0, { r: [PI / 2, 0, 0] }); }
export function quiver2(c, wood, gold, n = 5) {
  const { add, G, M, bones: B } = c; const g = new THREE.Group(); g.position.set(.08, .12, -.17); g.rotation.set(.15, 0, -.35); B.chest.add(g);
  add(g, G.cyl(.055, .045, .5, 8), wood, 0, 0, 0); add(g, G.cyl(.06, .06, .03, 8), gold, 0, .22, 0); add(g, G.cyl(.05, .05, .03, 8), gold, 0, -.2, 0);
  for (let i = 0; i < n; i++) { const a = i / n * PI * 2; const x = Math.sin(a) * .025, z = Math.cos(a) * .025;
    add(g, G.cyl(.004, .004, .22, 4), M(0x8a6a3a), x, .36, z, { r: [0, 0, -x * 2] }); add(g, G.cone(.02, .07, 3), M(i % 2 ? 0xf0ead8 : 0x3a7a42, { d: 1 }), x * 1.2, .46, z * 1.2, { s: [1, 1, .3] }); }
  return g; }
export function bow2(c, o) {
  const { add, G, M } = c, g = new THREE.Group(), r = o.r ?? .62, arc = o.arc ?? 1.9; const wood = o.wood, gold = o.gold;
  add(g, new THREE.TorusGeometry(r, .016, 5, 22, arc), wood, -r, 0, 0, { r: [0, 0, -arc / 2] });
  for (const k of [-1, 1]) { const a = k * arc / 2; add(g, G.cone(.018, .07, 4), gold, -r + Math.cos(a) * r, Math.sin(a) * r, 0, { r: [0, 0, a - PI / 2 * k + (k > 0 ? 0 : PI)] }); }
  const sy = Math.sin(arc / 2) * r, sx = -r + Math.cos(arc / 2) * r; add(g, G.cyl(.003, .003, sy * 2, 3), M(0xeee6d0), sx, 0, 0);
  add(g, G.cyl(.022, .022, .13, 6), M(0x3a2415), 0, 0, 0); add(g, G.cyl(.026, .026, .02, 6), gold, 0, .075, 0); add(g, G.cyl(.026, .026, .02, 6), gold, 0, -.075, 0);
  return g; }
export function axeHead(c, o) { // double-bit battle axe; origin at haft centre
  const { add, G, M } = c, g = new THREE.Group(); const iron = o.iron, gold = o.gold;
  const blade = k => { const s = new THREE.Shape(); s.moveTo(0, .1); s.quadraticCurveTo(k * .12, .32, k * .34, .36); s.quadraticCurveTo(k * .26, .1, k * .36, -.12); s.quadraticCurveTo(k * .14, -.18, 0, -.1); s.closePath(); return new THREE.ExtrudeGeometry(s, { depth: .028, bevelEnabled: false, curveSegments: 6 }); };
  for (const k of [-1, 1]) { const bg = blade(k); bg.translate(0, 0, -.014); add(g, bg, iron, k * .04, 0, 0); add(g, G.box(.18, .03, .034), M(0xcfd6dd, { m: .6, r: .3 }), k * .24, .03, 0, { r: [0, 0, 0] });
    add(g, G.box(.1, .02, .034), M(o.rune ?? 0xb02828, { e: o.rune ?? 0xb02828, ei: .5 }), k * .2, .12, 0, { r: [0, 0, -k * .5] }); }
  add(g, G.cyl(.075, .075, .07, 10), gold, 0, 0, 0, { r: [PI / 2, 0, 0] }); add(g, G.cyl(.04, .04, .09, 8), iron, 0, 0, 0, { r: [PI / 2, 0, 0] }); add(g, G.cone(.03, .12, 4), iron, 0, .24, 0);
  return g; }
export function lute(c, o) {
  const { add, G, M } = c, g = new THREE.Group(), wood = o.wood, dark = M(0x3a2415, { r: .8 }), gold = o.gold;
  add(g, G.sph(.17, 10, 8), wood, 0, 0, 0, { s: [1, 1.2, .55] }); add(g, G.cyl(.05, .05, .02, 8), dark, 0, .02, .09, { r: [PI / 2, 0, 0] });
  add(g, G.cyl(.052, .052, .012, 8), gold, 0, .02, .088, { r: [PI / 2, 0, 0] }); add(g, G.box(.1, .015, .02), dark, 0, -.1, .1);
  add(g, G.box(.05, .5, .03), M(0x5a3a22, { r: .7 }), 0, .5, 0); add(g, G.box(.058, .015, .036), gold, 0, .27, .0);
  const ph = new THREE.Group(); ph.position.set(0, .78, 0); ph.rotation.x = -.5; g.add(ph); add(ph, G.box(.06, .17, .03), M(0x5a3a22), 0, .06, 0);
  for (const k of [-1, 1]) for (let i = 0; i < 2; i++) add(ph, G.cyl(.01, .01, .05, 5), gold, k * .035, .02 + i * .06, 0, { r: [0, 0, PI / 2] });
  add(g, G.cyl(.002, .002, .9, 3), M(0xeee6d0), 0, .45, .02); add(g, G.cyl(.002, .002, .9, 3), M(0xeee6d0), .012, .45, .02);
  add(g, G.tor(.18, .012, 4, 14), gold, 0, 0, -.001, { s: [1, 1.2, .5] });
  return g; }
export function glyph(c, col, size = .09) { // floating square-rune plaque
  const { add, G, M } = c, g = new THREE.Group(), m = M(col, { e: col, ei: 1.5, d: 1 });
  add(g, new THREE.TorusGeometry(size, .008, 3, 4), m, 0, 0, 0, { r: [0, 0, PI / 4] });
  add(g, G.box(size * .09, size * 1.1, .008), m, 0, 0, 0); add(g, G.box(size * .8, size * .08, .008), m, 0, size * .15, 0);
  add(g, G.box(size * .5, size * .08, .008), m, 0, -size * .3, 0, { r: [0, 0, .4] });
  add(g, G.sph(size * .5, 6, 5), M(col, { e: col, ei: .5, a: .12 }), 0, 0, 0, { s: [1, 1, .1] });
  return g; }
export function flame(c, col1 = 0xff7a1a, col2 = 0xffd23a, s = 1) {
  const { add, G, M } = c, g = new THREE.Group(), a = M(col1, { e: col1, ei: 1.6, d: 1, n: 'flame' }), b = M(col2, { e: col2, ei: 1.8, d: 1, n: 'flame2' });
  add(g, G.sph(.06 * s, 7, 5), b, 0, 0, 0, { s: [1, 1.1, 1] }); add(g, G.sph(.09 * s, 7, 5), M(col1, { e: col1, ei: .6, a: .25 }), 0, 0, 0);
  for (let i = 0; i < 7; i++) { const an = i / 7 * PI * 2, rr = .05 * s; add(g, G.cone(.035 * s, (.16 + (i % 3) * .06) * s, 5), i % 2 ? a : b, Math.sin(an) * rr, .08 * s + (i % 3) * .01, Math.cos(an) * rr, { r: [Math.cos(an) * .5, 0, -Math.sin(an) * .5], s: [1, 1, .6] }); }
  return g; }
export function kiRing(c, hand, col = 0xffc84a, y = -.05) {
  const { add, G, M } = c, m = M(col, { e: col, ei: 1.6, a: .75, d: 1, n: 'ki' });
  for (let i = 0; i < 3; i++) add(hand, G.tor(.1 + i * .035, .008 + (i == 0) * .004, 4, 18), m, 0, y + (i - 1) * .02, 0, { r: [PI / 2 + i * .45 - .4, i * .6, 0] });
  add(hand, G.sph(.1, 8, 6), M(col, { e: col, ei: .5, a: .22, n: 'kiglow' }), 0, y, 0);
  for (let i = 0; i < 5; i++) { const an = i / 5 * PI * 2; add(hand, G.cone(.012, .07, 4), m, Math.sin(an) * .13, y + (i % 2) * .05, Math.cos(an) * .13, { r: [Math.cos(an) * 1.4, 0, -Math.sin(an) * 1.4] }); }
}
export function hat(c, col, trim, o = {}) { // soft bard cap with brim and plume mount
  const { add, G, M, bones: B } = c, m = M(col, { r: .9, n: 'hat' });
  add(B.head, G.cyl(.2, .2, .02, 12), m, 0, .205, 0, { r: [.12, 0, .06], s: [1, 1, 1.05] }); add(B.head, G.dome(.125, 10, 5), m, 0, .205, 0, { r: [.12, 0, .06], s: [1, .9, 1.1] });
  add(B.head, G.tor(.125, .012, 4, 14), M(trim, { m: .4, r: .4 }), 0, .215, 0, { r: [PI / 2 + .12, 0, .06] });
  add(B.head, G.cyl(.205, .205, .012, 12), M(trim, { m: .4, r: .4 }), 0, .205, 0, { r: [.12, 0, .06], s: [1.01, 1, 1.06] }); }
// wolf (own quadruped rig; clips baked like the heroes)
export function wolfRig() {
  const c = makeCtx({ name: 'Wolf' }); const { M, bone, add, G, bones: B } = c;
  const fur = M(0x9a8d78, { r: 1, n: 'fur', t: 'fur' }), dk = M(0x57493b, { r: 1, n: 'furdark', t: 'fur' }), lt = M(0xe0d4ba, { r: 1, n: 'furlight', t: 'fur' }), gold = M(0xd2a43c, { m: .4, r: .4, n: 'gold' });
  const root = bone('root', null), hips = bone('hips', root, 0, .47, -.3), spine = bone('spine', hips, 0, .02, .32), chest = bone('chest', spine, 0, .03, .3), neck = bone('neck', chest, 0, .08, .22), head = bone('head', neck, 0, .08, .12), jaw = bone('jaw', head, 0, -.04, .05);
  add(hips, G.sph(.2, 9, 7), fur, 0, 0, 0, { s: [.95, 1, 1.25] }); add(spine, G.sph(.19, 9, 7), fur, 0, .0, 0, { s: [.95, .95, 1.5] }); add(chest, G.sph(.23, 9, 7), fur, 0, .0, 0, { s: [.95, 1.15, 1.2] });
  add(spine, G.sph(.17, 8, 6), dk, 0, .08, 0, { s: [.9, .6, 1.5] }); add(chest, G.sph(.2, 8, 6), lt, 0, -.1, .08, { s: [.8, .8, 1.1] });
  add(neck, G.sph(.15, 8, 6), fur, 0, .02, .06, { s: [.9, 1, 1.4], r: [-.5, 0, 0] }); for (let i = 0; i < 6; i++) add(neck, G.cone(.05, .1, 4), lt, (i - 2.5) * .045, -.06, .14 + (i % 2) * .02, { r: [PI + .3, 0, 0] });
  add(head, G.sph(.1, 8, 6), fur, 0, 0, .0, { s: [.95, .9, 1.1] }); add(head, G.box(.08, .065, .17), fur, 0, -.02, .14); add(head, G.sph(.03, 5, 4), M(0x15100a), 0, .0, .235);
  add(head, G.box(.075, .02, .15), lt, 0, -.055, .13); add(jaw, G.box(.065, .025, .15), lt, 0, -.01, .1);
  for (const k of [-1, 1]) { add(head, G.cone(.04, .11, 4), dk, k * .065, .12, -.02, { s: [1, 1, .55], r: [0, 0, -k * .15] }); add(head, G.sph(.012, 4, 3), M(0xe8b030, { e: 0xe8b030, ei: .4 }), k * .05, .03, .105); add(jaw, G.cone(.008, .035, 4), M(0xf6f2e6), k * .028, .012, .16, { r: [PI, 0, 0] }); }
  for (const k of [-1, 1]) { add(head, G.cone(.05, .12, 5), lt, k * .085, -.03, .05, { r: [PI / 2 + .3, 0, -k * .9], s: [1, 1, .6] }); add(head, G.cone(.04, .1, 4), fur, k * .07, .09, .02, { r: [PI / 2 - .3, 0, -k * .5], s: [1, 1, .5] }); }
  for (let i = 0; i < 9; i++) { const a = i / 9 * PI * 2; add(neck, G.cone(.045, .13, 4), i % 3 ? fur : lt, Math.sin(a) * .13, Math.cos(a) * .1 + .0, .03 + (Math.cos(a) < 0 ? .0 : .02), { r: [PI / 2 + Math.cos(a) * .5, 0, -Math.sin(a) * .9] }); }
  add(chest, G.sph(.2, 7, 5), fur, 0, .12, .0, { s: [1.05, .5, 1.3] });
  for (let i = 0; i < 6; i++) add(hips, G.cone(.035, .11, 4), fur, (i - 2.5) * .06, -.1, 0 - .12 - (i % 2) * .03, { r: [PI, 0, 0] });
  const t1 = bone('tail_1', hips, 0, .02, -.2), t2 = bone('tail_2', t1, 0, 0, -.2); t1.rotation.x = -.5;
  add(t1, G.sph(.085, 7, 5), fur, 0, 0, -.1, { s: [1, 1, 2.2] }); add(t2, G.sph(.085, 7, 5), dk, 0, 0, -.1, { s: [1, 1, 2.4] }); add(t2, G.cone(.05, .12, 5), lt, 0, 0, -.27, { r: [-PI / 2, 0, 0] });
  for (const [fb, par, zz] of [['F', chest, .08], ['B', hips, -.02]]) for (const k of [-1, 1]) { const S = fb + (k > 0 ? 'L' : 'R');
    const th = bone('thigh_' + S, par, k * .14, -.1, zz), sn = bone('shin_' + S, th, 0, -.22, 0), pw = bone('paw_' + S, sn, 0, -.22, 0);
    const l = (p, len, r0, r1, m) => { const g = G.cyl(r0, r1, len, 7); g.translate(0, -len / 2, 0); add(p, g, m); };
    l(th, .22, fb === 'B' ? .085 : .07, .05, fur); add(th, G.sph(.085, 6, 5), fur, 0, 0, 0); l(sn, .22, .05, .035, fb === 'B' ? dk : fur); add(pw, G.box(.07, .04, .12), lt, 0, -.015, .035);
    if (fb === 'B') { th.rotation.x = .25; sn.rotation.x = -.4; } }
  // collar
  add(neck, G.tor(.12, .018, 4, 12), M(0x5a3720, { r: .85 }), 0, .03, .12, { r: [PI / 2 - .5, 0, 0] }); add(neck, G.cyl(.032, .032, .012, 8), gold, 0, -.07, .2, { r: [PI / 2 - .5, 0, 0] });
  add(neck, G.cone(.03, .08, 4), M(0x3f8f3a, { d: 1 }), 0, -.13, .22, { r: [PI, 0, 0], s: [1, 1, .3] });
  const names = Object.keys(B); for (const k in B) B[k].userData.rest = { r: B[k].rotation.clone(), p: B[k].position.clone() };
  const update = (t, mode) => {
    for (const n of names) { const b = B[n], r = b.userData.rest; b.rotation.copy(r.r); b.position.copy(r.p); }
    const R = (n, x = 0, y = 0, z = 0) => { const b = B[n]; b.rotation.x += x; b.rotation.y += y; b.rotation.z += z; }; const ph = t * PI * 2;
    if (mode === 'walk') { for (const [S, o] of [['FL', 0], ['BR', 0], ['FR', PI], ['BL', PI]]) { const p = ph + o; R('thigh_' + S, Math.sin(p) * .5); R('shin_' + S, Math.max(0, Math.cos(p)) * .7); R('paw_' + S, -Math.sin(p) * .2); }
      B.hips.position.y += Math.abs(Math.sin(ph)) * .015; R('spine', Math.sin(ph) * .02, Math.sin(ph) * .04); R('head', 0, -Math.sin(ph) * .04); R('tail_1', 0, Math.sin(ph) * .2); R('tail_2', 0, Math.sin(ph - 1) * .3); }
    else { R('chest', Math.sin(ph) * .01); R('head', Math.sin(ph * .5) * .03, Math.sin(ph * .5) * .1); R('jaw', Math.max(0, Math.sin(ph * 2)) * .05); R('tail_1', 0, Math.sin(ph) * .12); R('tail_2', 0, Math.sin(ph - 1) * .2); B.hips.position.y += Math.sin(ph) * .004; } };
  update(0, 'idle'); const grp = new THREE.Group(); grp.name = 'Wolf'; grp.add(root);
  const clip = (mode, dur, N) => { const times = [...Array(N)].map((_, i) => i * dur / N), rec = {}, hp = []; times.forEach(t => { update(t / dur, mode); for (const n of names) (rec[n] ??= []).push(...B[n].quaternion.toArray()); hp.push(...B.hips.position.toArray()); });
    const tracks = []; for (const n of names) { const q0 = new THREE.Quaternion().setFromEuler(B[n].userData.rest.r), a = rec[n]; let mv = false; for (let i = 0; i < N && !mv; i++) mv = Math.abs(a[i * 4] - q0.x) + Math.abs(a[i * 4 + 1] - q0.y) + Math.abs(a[i * 4 + 2] - q0.z) + Math.abs(a[i * 4 + 3] - q0.w) > 1e-4; if (mv) tracks.push(new THREE.QuaternionKeyframeTrack(n + '.quaternion', times, a)); }
    tracks.push(new THREE.VectorKeyframeTrack('hips.position', times, hp)); update(0, 'idle'); return new THREE.AnimationClip(mode, dur, tracks); };
  return { root: grp, bones: B, update, clips: () => [clip('idle', 3, 12), clip('walk', 1, 16)], hold: {} };
}
