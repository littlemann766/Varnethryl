// ================= batch 4: Cinder (phoenix), Neris Wavefist, Briar Fleetstride (centaur), Zephyr (hippogriff), Coral (mermaid), Mortimer the Archivist, Pip (fox) =================
// Same kit as chars.js / chars3.js (named bones, rigid-parted nodes, flat palette, baked idle + walk).
import * as THREE from 'three';
import * as K from './chars_core.js';
import { pal, hold, tassel, gemM, rnd, bakeRig } from './chars3.js';
const { makeCtx, humanoid, belt, strapX, hair, cape, skirt, emblem, finalize } = K;
const PI = Math.PI;
export const CHARS4 = {};

// fan of flat feathers radiating from a pivot in the local xy plane (0 = along -y). mats cycled.
function fan(c, par, k, o) {
  const { add, G } = c, n = o.n;
  for (let i = 0; i < n; i++) { const t = n > 1 ? i / (n - 1) : 0, L = o.l0 + (o.l1 - o.l0) * t, g = G.cone(o.w ?? .03, L, o.sides ?? 4); g.rotateX(PI); g.translate(0, -L / 2, 0);
    add(par, g, o.mats[i % o.mats.length], 0, o.y ?? 0, (o.z ?? 0) + (i % 2) * .004, { r: [0, 0, k * (o.a0 + t * o.spread)], s: [1, 1, o.flat ?? .22] }); }
}
// tapering limb segment hanging from the bone origin
const limb = (c, p, len, r0, r1, m, sides = 7) => { const g = c.G.cyl(r0, r1, len, sides); g.translate(0, -len / 2, 0); c.add(p, g, m); };
const ear = (c, par, k, x, y, z, s, col, rz = .3, rx = -.2) => c.add(par, c.G.cone(.04 * s, .12 * s, 4), col, x, y, z, { r: [rx, 0, -k * rz], s: [1, 1, .5] });

// ====================================== CINDER (phoenix hatchling) ======================================
CHARS4.cinder = { name: 'Cinder (phoenix hatchling)', sheetKey: 'cinder', build() {
  const c = makeCtx({ name: 'Cinder' }), { add, G, M, bone } = c;
  const red = M(0xd8321a, { r: .8, n: 'fred' }), org = M(0xf0661a, { r: .8, n: 'forg' }), yel = M(0xffb830, { r: .7, n: 'fyel' }), cream = M(0xffd890, { r: .9, n: 'fcream' }),
    flA = M(0xff5a14, { e: 0xff4a08, ei: 1.3, d: 1, n: 'flameA' }), flB = M(0xffa626, { e: 0xff9a10, ei: 1.5, d: 1, n: 'flameB' }), flC = M(0xffe070, { e: 0xffd040, ei: 1.6, d: 1, n: 'flameC' }),
    beak = M(0xe8b030, { r: .5, n: 'beak' }), tal = M(0x6a4a1a, { r: .6, n: 'talon' }), leg = M(0xb8862a, { m: .3, r: .5, n: 'cleg' });
  const root = bone('root', null), hips = bone('hips', root, 0, .27, 0), neck = bone('neck', hips, 0, .1, .05), head = bone('head', neck, 0, .09, .04);
  add(hips, G.sph(.1, 8, 6), org, 0, 0, 0, { s: [.95, 1.3, 1.05], r: [.25, 0, 0] }); add(hips, G.sph(.085, 8, 6), cream, 0, -.01, .045, { s: [.85, 1.25, .7], r: [.25, 0, 0] });
  for (let r = 0; r < 3; r++) for (let i = 0; i < 5; i++) add(hips, G.cone(.03, .07, 4), [red, org, yel][(i + r) % 3], (i - 2) * .036, .03 - r * .055, .085 - r * .005, { r: [PI + .1, 0, 0], s: [1, 1, .4] });
  add(neck, G.sph(.055, 7, 5), org, 0, .0, 0, { s: [1, 1.3, 1] }); for (let i = 0; i < 5; i++) add(neck, G.cone(.025, .06, 4), [yel, cream][i % 2], (i - 2) * .025, -.02, .05, { r: [PI + .3, 0, 0], s: [1, 1, .4] });
  add(head, G.sph(.062, 8, 6), org, 0, .02, 0, { s: [.95, 1, 1.05] }); add(head, G.sph(.045, 6, 5), cream, 0, -.005, .03);
  add(head, G.cone(.03, .08, 5), beak, 0, -.0, .07, { r: [PI / 2, 0, 0] }); add(head, G.cone(.016, .035, 4), beak, 0, -.02, .1, { r: [PI / 2 + .9, 0, 0] });
  for (const k of [-1, 1]) { add(head, G.sph(.014, 5, 4), M(0xffb000, { e: 0xffa000, ei: .5, n: 'eye' }), k * .042, .04, .04); add(head, G.sph(.007, 4, 3), M(0x1a0a05), k * .048, .04, .05); add(head, G.box(.04, .008, .016), red, k * .04, .06, .04, { r: [0, 0, k * -.3] }); }
  const crest = [[0, .09, -.03, -.5, 0, 1.2, flB], [.03, .08, -.02, -.3, -.4, 1, flA], [-.03, .08, -.02, -.3, .4, 1, flA], [.05, .06, 0, -.1, -.9, .8, flC], [-.05, .06, 0, -.1, .9, .8, flC], [0, .07, -.07, -.9, 0, 1.1, flC]];
  for (const [x, y, z, rx, rz, s, m] of crest) add(head, G.cone(.026 * s, .14 * s, 4), m, x, y + .07 * s, z, { r: [rx, 0, rz] });
  // wings
  for (const k of [-1, 1]) { const S = k > 0 ? 'L' : 'R', w = bone('wing_' + S, hips, k * .085, .06, -.01), wt = bone('wingTip_' + S, w, 0, -.13, 0); w.rotation.z = k * 2.25;
    add(w, G.sph(.04, 6, 5), org, k * .005, -.05, 0, { s: [.6, 2, 1] });
    fan(c, w, k, { n: 6, l0: .12, l1: .2, a0: -.3, spread: -.5, mats: [red, org], w: .035, z: .004 }); fan(c, w, k, { n: 5, l0: .22, l1: .16, a0: .15, spread: .55, mats: [org, yel], w: .034, z: -.004 });
    fan(c, wt, k, { n: 7, l0: .2, l1: .3, a0: -.15, spread: .8, mats: [flA, flB, flC], w: .03 }); fan(c, wt, k, { n: 5, l0: .15, l1: .1, a0: -.5, spread: -.3, mats: [red, org], w: .03, z: .006 }); }
  // legs
  for (const k of [-1, 1]) { const S = k > 0 ? 'L' : 'R', th = bone('leg_' + S, hips, k * .045, -.09, .01), ft = bone('foot_' + S, th, 0, -.1, 0);
    add(th, G.sph(.05, 6, 5), org, 0, .0, 0, { s: [.9, 1.2, 1] }); limb(c, th, .1, .018, .014, leg, 6); add(ft, G.cyl(.016, .016, .06, 5), leg, 0, -.03, 0);
    for (let i = -1; i <= 1; i++) add(ft, G.cone(.008, .055, 4), tal, i * .02, -.065, .03, { r: [PI / 2 + .5, 0, 0] }); add(ft, G.cone(.008, .045, 4), tal, 0, -.06, -.025, { r: [-PI / 2 - .5, 0, 0] }); }
  // flame tail: 4 chained plumes
  { let par = hips, y = -.1, z = -.06; for (let i = 1; i <= 4; i++) { const t = bone('tail_' + i, par, 0, y, z); t.rotation.x = i === 1 ? .95 : .3; const L = .2 - i * .015;
      add(t, G.sph(.05 - i * .007, 6, 5), i < 3 ? org : flB, 0, -L * .4, 0, { s: [1, 2.2, 1] });
      for (let j = 0; j < 7; j++) { const a = (j - 3) * .32, Lc = (.22 + (j % 3) * .06) * (1 + i * .1); const g = G.cone(.03, Lc, 4); g.rotateX(PI); g.translate(0, -Lc / 2, 0); add(t, g, [flA, flB, flC, org, red][(j + i) % 5], 0, 0, (j % 2) * .01, { r: [((j % 3) - 1) * .12, 0, a], s: [1, 1, .5] }); }
      par = t; y = -L; z = 0; } }
  for (let i = 0; i < 6; i++) { const a = i * 1.1; add(hips, G.oct(.012), flC, Math.sin(a) * .18, .05 + i * .08, Math.cos(a) * .15 - .05); }
  const upd = (t, mode, R, B) => { const ph = t * PI * 2;
    if (mode === 'walk') { B.hips.position.y += Math.abs(Math.sin(ph)) * .02; R('hips', 0, Math.sin(ph) * .1); R('leg_L', Math.sin(ph) * .6); R('leg_R', -Math.sin(ph) * .6); R('foot_L', Math.max(0, Math.cos(ph)) * .5); R('foot_R', Math.max(0, -Math.cos(ph)) * .5); R('head', Math.sin(ph * 2) * .08, -Math.sin(ph) * .1);
      for (const S of ['L', 'R']) { const k = S === 'L' ? 1 : -1; R('wing_' + S, 0, 0, k * (-.15 + Math.sin(ph * 2) * .3)); R('wingTip_' + S, 0, 0, k * (Math.sin(ph * 2 - .8) * .3)); } for (let i = 1; i <= 4; i++) R('tail_' + i, Math.sin(ph * 2 - i * .8) * .08, 0, Math.sin(ph - i * .7) * .15); }
    else { R('head', Math.sin(ph * .5) * .05, Math.sin(ph) * .35 * Math.max(0, Math.sin(ph * .5))); R('hips', Math.sin(ph) * .015); B.hips.position.y += Math.sin(ph) * .004; for (const S of ['L', 'R']) { const k = S === 'L' ? 1 : -1; R('wing_' + S, 0, 0, k * (-.08 + Math.sin(ph * 2) * .06)); R('wingTip_' + S, 0, 0, k * Math.sin(ph * 2 - 1) * .08); }
      for (let i = 1; i <= 4; i++) R('tail_' + i, Math.sin(ph - i * .6) * .07, 0, Math.sin(ph * 2 - i * .8) * .08); } };
  return bakeRig(c, root, 'Cinder', upd); } };

// ====================================== PIP (fox companion) ======================================
CHARS4.pip = { name: 'Pip (fox companion)', sheetKey: 'pip', build() {
  const c = makeCtx({ name: 'Pip' }), { M, bone, add, G, bones: B } = c, { gold } = pal(c);
  const fur = M(0xe0702a, { r: 1, n: 'foxfur' }), lt = M(0xf6eee0, { r: 1, n: 'foxwhite' }), dk = M(0x3a2418, { r: 1, n: 'foxdark' }), navy = M(0x2a3a78, { r: .9, d: 1, n: 'scarf' }), leather = M(0x6a3a1c, { r: .85, n: 'bag' }), dl = M(0x3c2616, { r: .85, n: 'dbag' });
  const root = bone('root', null), hips = bone('hips', root, 0, .8, -.22), spine = bone('spine', hips, 0, .03, .26), chest = bone('chest', spine, 0, .04, .24), neck = bone('neck', chest, 0, .17, .15), head = bone('head', neck, 0, .13, .1), jaw = bone('jaw', head, 0, -.05, .06);
  add(hips, G.sph(.2, 9, 7), fur, 0, 0, 0, { s: [.95, 1, 1.15] }); add(spine, G.sph(.2, 9, 7), fur, 0, 0, 0, { s: [.95, .95, 1.4] }); add(chest, G.sph(.23, 9, 7), fur, 0, 0, 0, { s: [.95, 1.12, 1.1] });
  add(chest, G.sph(.15, 8, 6), lt, 0, -.04, .09, { s: [.8, 1, .9] }); add(spine, G.sph(.12, 8, 6), lt, 0, -.07, .03, { s: [.8, .7, 1.2] });
  add(neck, G.sph(.12, 8, 6), fur, 0, .0, .04, { s: [.9, 1.1, 1.1] }); for (let i = 0; i < 7; i++) add(neck, G.cone(.04, .1, 4), lt, (i - 3) * .035, -.07, .1 + (i % 2) * .02, { r: [PI + .35, 0, 0], s: [1, 1, .6] });
  add(head, G.sph(.1, 8, 6), fur, 0, .0, 0, { s: [1.08, .92, 1] }); add(head, G.cone(.06, .17, 5), fur, 0, -.02, .13, { r: [PI / 2, 0, 0], s: [1, 1, .85] }); add(head, G.sph(.026, 5, 4), M(0x15100a, { r: .4 }), 0, -.01, .22); add(head, G.box(.1, .03, .1), lt, 0, -.055, .1);
  for (const k of [-1, 1]) { add(head, G.sph(.04, 6, 5), lt, k * .075, -.04, .08, { s: [.8, .7, 1] }); add(head, G.sph(.017, 5, 4), M(0xe8a020, { e: 0xe8a020, ei: .4, n: 'foxeye' }), k * .055, .035, .08); add(head, G.sph(.009, 4, 3), M(0x100804), k * .06, .035, .092);
    add(head, G.box(.04, .012, .02), dk, k * .055, .065, .085, { r: [0, 0, k * -.25] }); add(jaw, G.cone(.007, .03, 4), lt, k * .024, .012, .12, { r: [PI, 0, 0] }); }
  add(jaw, G.box(.055, .02, .12), lt, 0, -.005, .075);
  for (const k of [-1, 1]) { const S = k > 0 ? 'L' : 'R', e = bone('ear_' + S, head, k * .06, .08, -.02); e.rotation.z = -k * .12; add(e, G.cone(.085, .26, 4), fur, 0, .1, 0, { s: [1, 1, .4] }); add(e, G.cone(.045, .17, 4), lt, 0, .09, .012, { s: [1, 1, .3] }); add(e, G.cone(.07, .09, 4), dk, 0, .21, 0, { s: [1, 1, .38] }); }
  // bushy tail: 3 chained fluffs, white tip
  { let par = hips, y = .0, z = -.14; for (let i = 1; i <= 3; i++) { const t = bone('tail_' + i, par, 0, y, z); t.rotation.x = i === 1 ? -.55 : -.3; const L = [.3, .3, .24][i - 1], r = [.075, .1, .08][i - 1];
      add(t, G.sph(r, 8, 6), i === 3 ? lt : fur, 0, 0, -L * .5, { s: [1, 1, 1.9] }); if (i < 3) add(t, G.sph(r * .8, 7, 5), lt, 0, -r * .35, -L * .5, { s: [.9, .7, 1.5] });
      if (i === 3) add(t, G.cone(.07, .16, 6), lt, 0, 0, -L - .08, { r: [-PI / 2, 0, 0] }); par = t; y = 0; z = -L; } }
  for (const [fb, par, zz] of [['F', chest, .06], ['B', hips, -.02]]) for (const k of [-1, 1]) { const S = fb + (k > 0 ? 'L' : 'R'), th = bone('thigh_' + S, par, k * .11, -.1, zz), sn = bone('shin_' + S, th, 0, -.33, 0), pw = bone('paw_' + S, sn, 0, -.34, 0);
    limb(c, th, .33, fb === 'B' ? .08 : .065, .045, fur, 7); add(th, G.sph(.08, 6, 5), fur, 0, 0, 0); limb(c, sn, .34, .04, .03, dk, 6); add(pw, G.box(.065, .04, .11), dk, 0, -.012, .03); add(pw, G.box(.05, .02, .03), lt, 0, -.01, .09);
    if (fb === 'B') { th.rotation.x = .3; sn.rotation.x = -.5; } }
  // navy fleur scarf, medallion, tassels, saddlebag
  add(neck, G.tor(.12, .03, 5, 12), navy, 0, .0, .05, { r: [PI / 2 - .4, 0, 0] });
  { const sc = new THREE.Group(); sc.position.set(.1, .04, .0); sc.rotation.set(0, 0, 0); neck.add(sc); for (let i = 0; i < 3; i++) add(sc, G.box(.13, .015, .1 - i * .02), navy, .06 + i * .07, -.0 - i * .015, -.06, { r: [0, 0, -.25 - i * .25] }); tassel(c, sc, 0xd2a43c, .3, -.1, -.06, .9);
    for (let i = 0; i < 4; i++) add(sc, G.cyl(.012, .012, .006, 4), gold, .04 + i * .06, .02 - i * .018, -.056, { r: [PI / 2, 0, 0] }); }
  add(neck, G.cyl(.032, .032, .012, 8), gold, 0, -.12, .17, { r: [PI / 2 - .5, 0, 0] }); add(neck, G.sph(.025, 6, 5), M(0x5aa8d8, { e: 0x2a6caf, ei: .4, n: 'pgem' }), 0, -.17, .2); tassel(c, neck, 0x2a3a78, 0, -.2, .2, .8);
  for (const k of [-1, 1]) { add(spine, G.box(.07, .14, .17), leather, k * .15, .0, -.02, { r: [0, 0, k * .12] }); add(spine, G.box(.074, .05, .18), dl, k * .152, .07, -.02, { r: [0, 0, k * .12] }); add(spine, G.cyl(.012, .012, .008, 6), gold, k * .19, .035, .03, { r: [0, 0, PI / 2] }); }
  add(spine, G.box(.28, .02, .06), dl, 0, .12, 0); add(spine, G.box(.28, .02, .05), dl, 0, .0, .06);
  const upd = (t, mode, R, Bn) => { const ph = t * PI * 2;
    if (mode === 'walk') { for (const [S, o] of [['FL', 0], ['BR', 0], ['FR', PI], ['BL', PI]]) { const p = ph + o; R('thigh_' + S, Math.sin(p) * .55); R('shin_' + S, Math.max(0, Math.cos(p)) * .75); R('paw_' + S, -Math.sin(p) * .2); }
      Bn.hips.position.y += Math.abs(Math.sin(ph)) * .02; R('spine', Math.sin(ph) * .03, Math.sin(ph) * .05); R('head', 0, -Math.sin(ph) * .05); R('tail_1', 0, Math.sin(ph) * .25); R('tail_2', 0, Math.sin(ph - 1) * .3); R('tail_3', 0, Math.sin(ph - 2) * .3); R('ear_L', 0, 0, Math.sin(ph * 2) * .06); R('ear_R', 0, 0, -Math.sin(ph * 2) * .06); }
    else { R('chest', Math.sin(ph) * .01); R('head', Math.sin(ph * .5) * .03, Math.sin(ph * .5) * .22); R('jaw', Math.max(0, Math.sin(ph * 2)) * .04); R('tail_1', 0, Math.sin(ph) * .15); R('tail_2', 0, Math.sin(ph - 1) * .22); R('tail_3', 0, Math.sin(ph - 2) * .25); R('ear_L', 0, 0, Math.max(0, Math.sin(ph * 2)) * .15); R('ear_R', 0, 0, -Math.max(0, Math.sin(ph * 2 + 2)) * .1); Bn.hips.position.y += Math.sin(ph) * .004; } };
  const rig = bakeRig(c, root, 'Pip', upd); rig.root.scale.setScalar(.62); return rig; } };

// ====================================== NERIS WAVEFIST (tidefolk healer) ======================================
CHARS4.neris = { name: 'Neris Wavefist', sheetKey: 'neris', build() {
  const bl = 0x6a8fb4, c = makeCtx({ name: 'Neris_Wavefist', fem: true, nobust: true, bulk: .92, sw: .95, skin: bl, hair: 0xeeeef4, under: 0x2f58a8, pants: bl, sleeve: 0xf2f0ea, glove: bl, boot: bl });
  const h = humanoid(c), { gold, leather, dleather } = pal(c), { add, G, M, bones: B } = c, blue = 0x2a58b0, white = 0xf2f0ea, coral = M(0xd2503c, { r: .7, n: 'coral' }), orbm = M(0x6ad0ff, { e: 0x3ab0ff, ei: 1.3, r: .1, n: 'orb' }), wat = M(0x8adcff, { e: 0x4ab8ff, ei: 1, a: .55, d: 1, n: 'water' });
  // sash bodice, belt, gold sun-wave medallion
  add(B.chest, G.cyl(.17, .12, .26, 8), M(blue, { r: .85, n: 'bodice' }), 0, .1, .006, { s: [1, 1, .72] }); belt(c, M(0x7a5028, { r: .8 }), gold); strapX(c, M(white, { r: .9 }), gold);
  add(B.chest, G.box(.2, .2, .02), M(0xe8e4dc, { r: .9, n: 'wrap' }), 0, .12, .125, { r: [0, 0, 0] }); emblem(c, B.chest, 'sun', .1, gold, 0, .06, .136); K.pouch(c, B.hips, 0x6a4126, -.2, -.06, .02, 1, gold); K.pouch(c, B.hips, 0x6a4126, .2, -.07, .02, .8, gold);
  for (let i = 0; i < 9; i++) { const a = i / 8 * PI * .9 - PI * .45; add(B.chest, G.sph(.014, 5, 4), M(0xf6f2ea, { r: .2, n: 'pearl' }), Math.sin(a) * .15, .2 - Math.cos(a * 1.4) * .06, .12 + Math.cos(a) * .02); }
  for (let i = 0; i < 3; i++) add(B.chest, G.cone(.025, .05, 5), M(0xeadfc8, { r: .5, n: 'shellc' }), (i - 1) * .06, .08 - Math.abs(i - 1) * .02, .14, { r: [PI, 0, 0], s: [1, 1, .5] });
  // layered tide skirt (white over blue) with tassels
  skirt(c, { col: blue, trim: 0xd2a43c, len: .78, top: .16, bot: .33, y: -.04, zs: .85, ragged: .1, segs: 16 }); skirt(c, { col: white, trim: 0x7ab0e8, len: .62, top: .17, bot: .36, y: -.02, zs: .88, ragged: .12, segs: 14 });
  for (let i = 0; i < 6; i++) { const a = i / 6 * PI * 2 + .2; add(B.hips, G.cone(.02, .09, 4), M(blue, { r: .9, n: 'tassel' }), Math.sin(a) * .3, -.78, Math.cos(a) * .28 + .0, { r: [PI, 0, 0] }); }
  const cp = cape(c, { topW: .62, botW: 1.25, len: 1.05, col: white, trim: 0x2a58b0, lining: blue, waves: 9, segs: 16, seed: 23, wrap: .14, ragged: .12 }); cp.len = 1.05;
  for (const k of [-1, 0, 1]) emblem(c, cp.cb, 'sun', .14, M(0x7ab0e8, { r: .5, n: 'swirl' }), k * .26, -.78, cp.z(.8) - .026, PI);
  for (const S of ['L', 'R']) { const k = S === 'L' ? 1 : -1, fa = B['foreArm_' + S]; add(fa, G.cyl(.06, .11, .3, 8, true), M(white, { r: .9, d: 1, n: 'bellsleeve' }), 0, -.15, 0); add(fa, G.cyl(.11, .11, .02, 8, true), M(blue, { r: .9, d: 1, n: 'sleeveblue' }), 0, -.3, 0);
    add(fa, G.cyl(.056, .052, .06, 8), gold, 0, -.02, 0); add(B['upperArm_' + S], G.sph(.05, 5, 4), M(0x7ab0e8, { r: .6, n: 'tattoo' }), 0, -.1, .045 * k * 0, { s: [1, 1, .3] });
    add(B['shin_' + S], G.box(.115, .02, .27), M(0x6a4126, { r: .8, n: 'sandal' }), 0, -.4, .05); for (let i = 0; i < 3; i++) add(B['shin_' + S], G.tor(.06, .008, 4, 8), M(0x6a4126, { r: .8 }), 0, -.16 - i * .08, 0, { r: [PI / 2, 0, 0] }); }
  // hair + fin ears + shell comb
  hair(c, 'wavy', 0xeeeef4, { len: 1.05 }); hair(c, 'swept', 0xeeeef4); for (const k of [-1, 1]) { add(B.head, G.box(.07, .6, .1), M(0xeeeef4, { r: .85, n: 'hairw' }), k * .13, -.28, -.04); add(B.chest, G.box(.08, .5, .1), M(0xeeeef4, { r: .85 }), k * .2, .0, -.1);
    add(B.head, G.cone(.04, .15, 4), M(bl, { r: .8 }), k * .115, .115, 0, { r: [0, 0, -k * 1.2], s: [1, 1, .4] }); add(B.head, G.cone(.02, .08, 4), M(0x8ab0d0, { r: .8, d: 1 }), k * .14, .09, 0, { r: [0, 0, -k * 1.9], s: [1, 1, .3] }); }
  add(B.head, G.tor(.12, .012, 4, 14), gold, 0, .19, .0, { r: [PI / 2 - .1, 0, 0] }); for (let i = 0; i < 3; i++) add(B.head, G.cone(.02, .09 + i % 2 * .03, 4), coral, (i - 1) * .05, .24, .09, { r: [.4, 0, (i - 1) * .3] });
  add(B.head, G.sph(.016, 5, 4), M(0x6ad0ff, { e: 0x3ab0ff, ei: .8 }), 0, .185, .115);
  // tide staff (R hand): gold shaft, coral crown, glowing orb, tassels
  const stf = new THREE.Group(), gw = M(0xb8903a, { m: .5, r: .4, n: 'tstaff' }); add(stf, G.cyl(.02, .024, 1.9, 6), gw, 0, .2, 0); for (let i = 0; i < 9; i++) add(stf, G.tor(.026, .008, 4, 8), gold, 0, -.6 + i * .19, 0, { r: [PI / 2, 0, 0] });
  add(stf, G.sph(.085, 9, 7), orbm, 0, 1.28, 0); add(stf, G.sph(.12, 8, 6), M(0x6ad0ff, { e: 0x3ab0ff, ei: .5, a: .25, d: 1, n: 'orbglow' }), 0, 1.28, 0); add(stf, G.tor(.13, .012, 4, 16), gold, 0, 1.28, 0, { r: [PI / 2 - .3, 0, 0] });
  for (let i = 0; i < 6; i++) { const a = i / 6 * PI * 2; add(stf, G.cone(.016, .24 + (i % 2) * .08, 4), i % 3 ? gold : coral, Math.sin(a) * .06, 1.12, Math.cos(a) * .06, { r: [Math.cos(a) * .7, 0, -Math.sin(a) * .7] }); }
  add(stf, G.cone(.016, .12, 4), coral, -.08, 1.36, 0, { r: [0, 0, .9] }); for (let i = 0; i < 3; i++) { add(stf, G.cyl(.006, .006, .08 + i * .03, 3), M(blue), (i - 1) * .03, 1.0 - i * .02, .03); tassel(c, stf, blue, (i - 1) * .04, .96 - i * .06, .03, .9); }
  for (let i = 0; i < 3; i++) add(stf, G.cone(.02, .05, 5), M(0xeadfc8, { r: .5 }), .04, 1.04 - i * .1, .02, { r: [PI, 0, 0], s: [1, 1, .5] });
  hold(c, h.hips, 'hand_R', stf, 0, -.05, 0, .12);
  const sw = new THREE.Group(); for (let i = 0; i < 3; i++) add(sw, G.tor(.1 + i * .035, .008, 4, 18), wat, 0, (i - 1) * .025, 0, { r: [PI / 2 + i * .5 - .4, i * .6, 0] }); add(sw, G.sph(.09, 8, 6), M(0x6ad0ff, { e: 0x3ab0ff, ei: .4, a: .2, d: 1 }), 0, 0, 0); hold(c, h.hips, 'hand_L', sw, 0, -.12, .03);
  return finalize(c, h.root, { R: 1, L: 1 }, Bn => { Bn.upperArm_L.rotation.set(-.5, 0, .5); Bn.foreArm_L.rotation.set(-.9, 0, 0); }); } };

// ====================================== MORTIMER THE ARCHIVIST (vampire librarian) ======================================
CHARS4.mortimer = { name: 'Mortimer the Archivist', sheetKey: 'mortimer', build() {
  const c = makeCtx({ name: 'Mortimer_Archivist', bulk: .9, sw: .98, skin: 0xe8ddd6, hair: 0xd8d6dc, under: 0x1c1a20, pants: 0x1c1a20, sleeve: 0x1c1a20, glove: 0xe8ddd6, boot: 0x2a1c14 });
  const h = humanoid(c), { gold, leather, dleather, brass } = pal(c), { add, G, M, bones: B, bone } = c, black = 0x1c1a20, crim = 0x8a1424, dcrim = 0x5a0c18, lace = M(0xf2ece0, { r: .9, n: 'lace' }), bk = M(black, { r: .9, d: 1, n: 'robe' }), cr = M(crim, { r: .9, d: 1, n: 'crimson' }), tm = M(0xd2a43c, { m: .45, r: .4, n: 'trim' });
  add(B.chest, G.cyl(.18, .13, .28, 8), M(0x2a2024, { r: .8, n: 'waistcoat' }), 0, .1, .006, { s: [1, 1, .72] }); add(B.chest, G.box(.1, .2, .02), cr, 0, .12, .12); belt(c, dleather, tm); strapX(c, leather, tm); emblem(c, B.chest, 'sun', .08, tm, 0, .16, .134);
  // jabot + high crimson collar
  for (let i = 0; i < 5; i++) add(B.chest, G.cone(.03, .1, 4), lace, (i - 2) * .03, .22 - Math.abs(i - 2) * .02, .13, { r: [PI + .1, 0, 0], s: [1, 1, .4] });
  for (const k of [-1, 1]) add(B.neck, G.box(.012, .13, .1), cr, k * .09, .07, -.02, { r: [-.1, 0, k * .3] }); add(B.neck, G.box(.18, .1, .012), cr, 0, .07, -.09);
  // long black robe w/ gold filigree & crimson panels
  skirt(c, { col: black, trim: 0xd2a43c, len: .98, top: .17, bot: .36, y: -.04, zs: .85, ragged: .06, segs: 16 }); skirt(c, { col: crim, trim: 0xd2a43c, len: .8, top: .165, bot: .3, y: -.05, zs: .8, ragged: .1, segs: 12 });
  { const sh = new THREE.Shape(); sh.moveTo(-.1, 0); sh.lineTo(.1, 0); sh.lineTo(.12, -.95); sh.lineTo(0, -1.02); sh.lineTo(-.12, -.95); sh.closePath(); const g = new THREE.Group(); g.position.set(0, .05, .17); g.rotation.x = -.04; B.hips.add(g); add(g, new THREE.ExtrudeGeometry(sh, { depth: .01, bevelEnabled: false }), M(black, { r: .9, n: 'panel' }), 0, 0, 0);
    for (const k of [-1, 1]) add(g, G.box(.02, .98, .014), tm, k * .1, -.5, .008); emblem(c, g, 'fleur', .16, tm, 0, -.45, .02); emblem(c, g, 'fleur', .1, tm, 0, -.8, .02); }
  // bat-wing cape: crimson-lined cloak + membrane wings on the back
  const cp = cape(c, { topW: .6, botW: 1.3, len: 1.2, col: black, trim: 0xd2a43c, lining: crim, waves: 9, segs: 18, seed: 31, wrap: .16, ragged: .12 }); cp.len = 1.2; K.emblem(c, cp.cb, 'fleur', .38, tm, 0, -.55, cp.z(.46) - .026, PI);
  const mem = M(0x8a1424, { r: .8, d: 1, n: 'membrane' }), memd = M(0x4a0c14, { r: .8, d: 1, n: 'membraned' }), bonem = M(0x241418, { r: .7, n: 'wingbone' });
  for (const k of [-1, 1]) { const S = k > 0 ? 'L' : 'R', bw = bone('batWing_' + S, B.chest, k * .16, .22, -.17); bw.rotation.set(.1, k * -.35, k * -.5);
    const sh = new THREE.Shape(); sh.moveTo(0, 0); sh.lineTo(k * .38, .16); sh.lineTo(k * .62, .1); sh.lineTo(k * .5, -.22); sh.lineTo(k * .4, -.1); sh.lineTo(k * .36, -.4); sh.lineTo(k * .24, -.2); sh.lineTo(k * .16, -.5); sh.lineTo(k * .08, -.2); sh.lineTo(0, -.3); sh.closePath();
    const g = new THREE.ExtrudeGeometry(sh, { depth: .008, bevelEnabled: false }); add(bw, g, mem, 0, 0, 0); add(bw, new THREE.ExtrudeGeometry(sh, { depth: .004, bevelEnabled: false }), memd, 0, 0, -.006, { s: [.96, .96, 1] });
    for (const [x, y] of [[.62, .1], [.5, -.22], [.36, -.4], [.16, -.5]]) { const L = Math.hypot(x, y), g = G.cyl(.008, .004, L, 4); g.translate(0, -L / 2, 0); add(bw, g, bonem, 0, 0, .005, { r: [0, 0, Math.atan2(k * x, -y) * 1 - PI + PI] }); }
    add(bw, G.cone(.02, .08, 4), bonem, k * .62, .12, 0, { r: [0, 0, -k * .6] }); }
  // frilly sleeves, cuffs, bracers, scroll cases, keys
  for (const S of ['L', 'R']) { const fa = B['foreArm_' + S]; add(fa, G.cyl(.075, .1, .1, 8, true), lace, 0, -.25, 0); add(fa, G.cyl(.058, .052, .16, 8), M(black, { r: .8 }), 0, -.1, 0); add(fa, G.cyl(.06, .06, .02, 8), tm, 0, -.03, 0);
    add(B['upperArm_' + S], G.cyl(.065, .06, .1, 8), tm, 0, -.2, 0); for (const y of [-.2, -.28]) add(B['shin_' + S], G.tor(.058, .008, 4, 8), M(0xb89a50, { m: .4, r: .4 }), 0, y, 0, { r: [PI / 2, 0, 0] }); add(B['shin_' + S], G.cyl(.07, .062, .2, 8), M(0x2a1c14, { r: .7, n: 'bootb' }), 0, -.22, 0); add(B['shin_' + S], G.cone(.05, .08, 4), tm, 0, -.4, .06, { r: [PI / 2, PI / 4, 0] }); }
  for (let i = 0; i < 4; i++) { add(B.hips, G.cyl(.026, .026, .2, 6), M(0xe0cfa0, { r: .7, n: 'scrollc' }), -.15 - i * .05, -.1 - (i % 2) * .02, .09 - i * .035, { r: [.3, 0, .15] }); add(B.hips, G.cyl(.028, .028, .016, 6), tm, -.15 - i * .05, -.02 - (i % 2) * .02, .09 - i * .035, { r: [.3, 0, .15] }); }
  for (let i = 0; i < 3; i++) { add(B.hips, G.tor(.02, .005, 4, 8), tm, .17 + i * .03, -.1 - i * .03, .1, { r: [PI / 2, 0, 0] }); add(B.hips, G.box(.006, .06, .006), tm, .17 + i * .03, -.17 - i * .03, .1); }
  K.pouch(c, B.hips, 0x3a2a24, .2, -.06, .03, 1, tm);
  // head: long silver hair, round spectacles, fangs
  hair(c, 'long', 0xd8d6dc, { len: .85 }); hair(c, 'swept', 0xd8d6dc); for (const k of [-1, 1]) { add(B.head, G.box(.06, .6, .1), M(0xd8d6dc, { r: .85, n: 'hairs' }), k * .12, -.25, -.05); add(B.head, G.tor(.03, .004, 4, 10), tm, k * .036, .115, .108); add(B.head, G.cone(.007, .028, 4), M(0xf8f4ec, { r: .3 }), k * .014, .02, .1, { r: [PI, 0, 0] }); add(B.head, G.cone(.04, .1, 4), M(0xe8ddd6, { r: .8 }), k * .11, .12, 0, { r: [0, 0, -k * 1.1], s: [1, 1, .4] }); }
  add(B.head, G.box(.04, .005, .005), tm, 0, .118, .108); add(B.head, G.box(.008, .008, .12), tm, .1, .12, .04); add(B.head, G.box(.008, .008, .12), tm, -.1, .12, .04);
  // tome (L hand) + scroll w/ red seal (R hand)
  const bk2 = K.book(c, 0x6a1420, tm, .22, .3); hold(c, h.hips, 'hand_L', bk2, 0, -.04, .06, -.2, 0, 0);
  const sc = new THREE.Group(); add(sc, G.cyl(.022, .022, .24, 6), M(0xe0cfa0, { r: .7 }), 0, 0, 0); add(sc, G.sph(.02, 5, 4), M(0xa01828, { r: .4, n: 'seal' }), 0, -.13, .02); add(sc, G.cyl(.004, .004, .1, 3), cr, 0, -.17, .02); hold(c, h.hips, 'hand_R', sc, 0, -.07, .0, 0, 0, 0);
  const rig = finalize(c, h.root, { L: 1, R: 1 }, Bn => { Bn.upperArm_L.rotation.set(-.5, 0, .25); Bn.foreArm_L.rotation.set(-1.1, 0, 0); Bn.upperArm_R.rotation.set(-.2, 0, -.3); Bn.foreArm_R.rotation.set(-.7, 0, 0); }); rig.root.scale.setScalar(1.03); return rig; } };

// ====================================== CORAL (mermaid) ======================================
CHARS4.coral = { name: 'Coral', sheetKey: 'coral', build() {
  const c = makeCtx({ name: 'Coral', fem: true, nobust: true, bulk: .86, sw: .92, skin: 0xf2c0a0, hair: 0xe0601c, under: 0xf4ecdc, pants: 0xe66a1e, sleeve: 0x2c8a94, glove: 0xf2c0a0, boot: 0xe66a1e });
  const h = humanoid(c), { gold } = pal(c), { add, G, M, bones: B, bone } = c;
  for (const S of ['L', 'R']) for (const n of ['thigh_', 'shin_', 'foot_']) { const b = B[n + S]; [...b.children].forEach(m => { if (m.isMesh) b.remove(m); }); }
  const sc1 = M(0xf07a24, { r: .5, m: .1, n: 'cscale1' }), sc2 = M(0xd8561a, { r: .5, m: .1, n: 'cscale2' }), fin = M(0xf8c890, { r: .6, d: 1, n: 'cfin' }), fin2 = M(0xffe8cc, { r: .6, d: 1, n: 'cfin2' }), belly = M(0xfbe6cc, { r: .7, n: 'cbelly' }), teal = M(0x2c8a94, { r: .8, d: 1, n: 'ctealsilk' }), shell = M(0xf4e4d0, { r: .5, n: 'cshell' }), pearl = M(0xffffff, { r: .2, n: 'cpearl' }), coralc = M(0xe8503c, { r: .7, n: 'ccoral' });
  const tl = [[.36, .17, .13, 0], [.36, .13, .1, .3], [.34, .1, .07, .45], [.26, .07, .045, .5]]; let par = B.hips, y0 = -.02;
  tl.forEach(([len, r0, r1, rot], i) => { const t = bone('tail_' + (i + 1), par, 0, y0, 0); t.rotation.x = rot; const g = G.cyl(r0, r1, len, 9); g.translate(0, -len / 2, 0); add(t, g, i % 2 ? sc2 : sc1, 0, 0, 0, { s: [1, 1, .8] });
    add(t, G.cyl(r0 * 1.02, r0 * 1.02, .025, 9), sc2, 0, -.01, 0, { s: [1, 1, .82] }); add(t, G.box(r0 * 1.0, len * .85, .03), belly, 0, -len / 2, r0 * .62 - .01); par = t; y0 = -len; });
  const tipB = bone('tail_5', par, 0, -.2, 0); tipB.rotation.x = .5; { const fs = new THREE.Shape(); fs.moveTo(0, 0); fs.quadraticCurveTo(.34, -.02, .44, -.34); fs.quadraticCurveTo(.2, -.26, .06, -.4); fs.lineTo(0, -.3); fs.lineTo(-.06, -.4); fs.quadraticCurveTo(-.2, -.26, -.44, -.34); fs.quadraticCurveTo(-.34, -.02, 0, 0);
    const fg = new THREE.ExtrudeGeometry(fs, { depth: .014, bevelEnabled: false, curveSegments: 6 }); fg.translate(0, 0, -.007); add(tipB, fg, fin, 0, 0, 0); add(tipB, fg, fin2, 0, -.04, .012, { s: [.7, .7, 1] }); for (const a of [-.55, -.25, 0, .25, .55]) add(tipB, G.box(.01, .3, .018), sc2, Math.sin(a) * .1, -.16, 0, { r: [0, 0, a] }); }
  add(B.hips, G.sph(.15, 8, 6), sc1, 0, -.03, 0, { s: [1, 1, .85] });
  for (const k of [-1, 1]) { const g = new THREE.Shape(); g.moveTo(0, 0); g.quadraticCurveTo(k * .2, -.05, k * .26, -.3); g.quadraticCurveTo(k * .12, -.2, 0, -.22); const fg = new THREE.ExtrudeGeometry(g, { depth: .012, bevelEnabled: false }); add(B.hips, fg, fin, k * .1, -.12, -.04); }
  // shell bra, pearl strings, sheer teal shawl/sleeves, coral/shell belt
  for (const k of [-1, 1]) { add(B.chest, G.dome(.085, 8, 4), shell, k * .065, .13, .1, { r: [PI / 2 - .2, 0, 0], s: [1, 1, .8] }); add(B.chest, G.cone(.02, .05, 5), coralc, k * .065, .12, .17, { r: [PI / 2, 0, 0] }); }
  add(B.chest, G.cyl(.16, .115, .12, 8), M(0xf4ecdc, { r: .85, n: 'cwrap' }), 0, .0, .005, { s: [1, 1, .72] });
  for (let i = 0; i < 9; i++) { const a = i / 8 * PI - PI * .5; add(B.chest, G.sph(.011, 5, 4), pearl, Math.sin(a) * .17, .05 - Math.cos(a * 1.5) * .06, .125 + Math.cos(a) * .02); }
  add(B.hips, G.cyl(.15, .17, .07, 10), M(0xe8503c, { r: .7, n: 'cbelt' }), 0, .0, 0, { s: [1, 1, .85] }); for (let i = 0; i < 7; i++) { const a = (i / 7 - .5) * PI * 1.1; add(B.hips, G.cone(.02, .09 + (i % 3) * .03, 4), coralc, Math.sin(a) * .16, .06, Math.cos(a) * .15, { r: [Math.cos(a) * .4, 0, -Math.sin(a) * .4] }); }
  add(B.hips, G.dome(.06, 7, 3), shell, 0, .0, .15, { r: [PI / 2, 0, 0] }); for (let i = 0; i < 3; i++) { add(B.hips, G.cone(.02, .05, 5), M(0xeadfc8, { r: .5 }), -.1 + i * .1, -.04, .14, { r: [PI, 0, 0], s: [1, 1, .5] }); }
  { const cp = cape(c, { topW: .4, botW: .7, len: .5, col: 0x2c8a94, trim: 0x2c8a94, lining: 0x1c6a74, waves: 11, segs: 16, seed: 17, wrap: .22, back: .14, ragged: .2 }); cp.len = .5; }
  for (const S of ['L', 'R']) { const k = S === 'L' ? 1 : -1, ua = B['upperArm_' + S], fa = B['foreArm_' + S]; add(ua, G.cyl(.075, .09, .18, 8, true), M(0xf4ecdc, { r: .9, d: 1, n: 'csleeve' }), 0, -.08, 0); add(fa, G.cyl(.06, .08, .2, 8, true), teal, 0, -.12, 0);
    for (let i = 0; i < 3; i++) add(fa, G.tor(.05, .008, 4, 8), M(i % 2 ? 0xffffff : 0x3aa8a8, { r: .3, n: 'bangle' + (i % 2) }), 0, -.02 - i * .018, 0, { r: [PI / 2, 0, 0] }); }
  // orange waves + starfish & shell hair ornaments
  hair(c, 'wavy', 0xe0601c, { len: 1.0 }); hair(c, 'swept', 0xe0601c); for (const k of [-1, 1]) { add(B.head, G.box(.07, .55, .1), M(0xe0601c, { r: .85, n: 'hairo' }), k * .13, -.25, -.04); add(B.chest, G.box(.08, .45, .1), M(0xe0601c, { r: .85 }), k * .2, .02, -.1); for (let i = 0; i < 3; i++) add(B.head, G.sph(.06, 5, 4), M(0xe0601c), k * (.15 + i % 2 * .03), -.05 - i * .15, .0, { s: [1, 1.7, 1] }); }
  { const st = new THREE.Group(); st.position.set(.1, .21, .08); B.head.add(st); for (let i = 0; i < 5; i++) { const a = i / 5 * PI * 2; add(st, G.cone(.02, .07, 4), M(0xf8d8c0, { r: .6, n: 'starfish' }), Math.sin(a) * .035, Math.cos(a) * .035, 0, { r: [0, 0, -a], s: [1, 1, .4] }); } }
  add(B.head, G.dome(.04, 7, 3), shell, -.1, .2, .06, { r: [PI / 2, 0, .3] }); add(B.head, G.sph(.015, 5, 4), pearl, -.09, .17, .09);
  add(B.neck, G.tor(.07, .01, 4, 10), pearl, 0, -.02, .02, { r: [PI / 2, 0, 0] });
  const rig = finalize(c, h.root, {}, Bn => { Bn.hips.position.y = 1.3; Bn.upperArm_L.rotation.set(-.2, 0, .75); Bn.foreArm_L.rotation.set(-.35, 0, 0); Bn.upperArm_R.rotation.set(-.15, 0, -.55); Bn.foreArm_R.rotation.set(-.5, 0, 0); Bn.thigh_L.rotation.set(0, 0, 0); });
  return rig; } };

// ============ shared horse-body kit (used by Briar's centaur + Zephyr's hippogriff rear) ============
function horseBody(c, root, o) {
  const { add, G, M, bone } = c, coat = M(o.coat, { r: .95, n: 'coat' }), dcoat = M(o.dcoat, { r: .95, n: 'coatdark' }), hoof = M(0x2a2018, { r: .6, n: 'hoof' }), sock = M(o.sock, { r: 1, n: 'sock' }), tailm = M(o.tail, { r: 1, d: 1, n: 'tailhair' });
  const hips = bone('hips', root, 0, o.y ?? .98, -.45), hSpine = bone('hSpine', hips, 0, .02, .45), hChest = bone('hChest', hSpine, 0, .05, .42);
  add(hips, G.sph(.31, 10, 8), coat, 0, 0, 0, { s: [.92, 1.0, 1.1] }); add(hSpine, G.sph(.3, 10, 8), coat, 0, 0, 0, { s: [.95, .95, 1.6] }); add(hChest, G.sph(.32, 10, 8), o.chestMat ?? coat, 0, 0, 0, { s: [.95, 1.05, 1.1] });
  for (const [fb, par, zz] of [['F', hChest, .08], ['B', hips, -.04]]) for (const k of [-1, 1]) { const S = fb + (k > 0 ? 'L' : 'R'), th = bone('thigh_' + S, par, k * .15, -.18, zz), sn = bone('shin_' + S, th, 0, -.44, 0), pw = bone('paw_' + S, sn, 0, -.44, 0), isB = fb === 'B';
    if (o.eagle && !isB) { const yl = M(0xd9a838, { m: .3, r: .5, n: 'scaleleg' }), tl = M(0x2a2018, { r: .5, n: 'claw' });
      limb(c, th, .44, .1, .06, o.eagleFeather, 8); add(th, G.sph(.13, 7, 5), o.eagleFeather, 0, -.05, 0, { s: [1, 1.3, 1.1] }); for (let i = 0; i < 5; i++) add(th, G.cone(.04, .12, 4), o.eagleGold, (i - 2) * .04, -.2 - (i % 2) * .05, .08, { r: [PI + .2, 0, 0], s: [1, 1, .4] });
      limb(c, sn, .44, .045, .035, yl, 6); add(sn, G.sph(.055, 6, 5), yl, 0, 0, 0); for (let i = 0; i < 3; i++) add(sn, G.tor(.045, .008, 4, 8), M(0xb88a22, { m: .3, r: .5 }), 0, -.1 - i * .1, 0, { r: [PI / 2, 0, 0] });
      add(pw, G.sph(.06, 6, 5), yl, 0, -.0, .02, { s: [1, .7, 1.4] }); for (let i = -1; i <= 1; i++) { add(pw, G.cone(.022, .15, 4), yl, i * .05, -.03, .1, { r: [PI / 2 + .35, 0, i * .08] }); add(pw, G.cone(.014, .07, 4), tl, i * .05, -.09, .19, { r: [PI / 2 + 1.0, 0, 0] }); } add(pw, G.cone(.02, .1, 4), yl, 0, -.03, -.07, { r: [-PI / 2 - .4, 0, 0] }); add(pw, G.cone(.012, .06, 4), tl, 0, -.08, -.1, { r: [-PI / 2 - 1.1, 0, 0] });
      continue; }
    limb(c, th, .44, isB ? .11 : .09, .06, coat, 8); add(th, G.sph(isB ? .12 : .1, 7, 5), coat, 0, 0, 0); limb(c, sn, .44, .055, .045, dcoat, 8); add(sn, G.sph(.06, 6, 5), dcoat, 0, 0, 0);
    add(sn, G.cyl(.08, .09, .14, 8), sock, 0, -.34, 0); for (let i = 0; i < 6; i++) { const a = i / 6 * PI * 2; add(sn, G.cone(.025, .09, 4), sock, Math.sin(a) * .07, -.36, Math.cos(a) * .07, { r: [PI + Math.cos(a) * .5, 0, -Math.sin(a) * .5], s: [1, 1, .6] }); }
    add(pw, G.cyl(.065, .075, .08, 8), hoof, 0, -.02, 0); if (isB) { th.rotation.x = .25; sn.rotation.x = -.45; } }
  { let par = hips, y = .06, z = -.3; for (let i = 1; i <= 3; i++) { const t = bone('tail_' + i, par, 0, y, z); t.rotation.x = i === 1 ? -.35 : .05; const gg = G.cyl(.08 - i * .014, .055 - i * .012, .34, 7); gg.translate(0, -.17, 0); add(t, gg, tailm, 0, 0, 0, { s: [1, 1, .6] }); add(t, G.cone(.055, .14, 5), tailm, 0, -.38, 0, { r: [PI, 0, 0], s: [1, 1, .6] }); par = t; y = -.34; z = 0; } }
  return { hips, hSpine, hChest };
}
const horseUpd = (t, mode, R, Bn, extra) => { const ph = t * PI * 2;
  if (mode === 'walk') { for (const [S, o] of [['FL', 0], ['BR', 0], ['FR', PI], ['BL', PI]]) { const p = ph + o; R('thigh_' + S, Math.sin(p) * .5); R('shin_' + S, Math.max(0, Math.cos(p)) * .75); R('paw_' + S, -Math.sin(p) * .15); }
    Bn.hips.position.y += Math.abs(Math.sin(ph)) * .02; R('hSpine', Math.sin(ph) * .015, Math.sin(ph) * .035); R('hChest', 0, -Math.sin(ph) * .03); for (let i = 1; i <= 3; i++) R('tail_' + i, Math.sin(ph - i * .7) * .08, 0, Math.sin(ph - i * .7) * .12); }
  else { R('hChest', Math.sin(ph) * .008); Bn.hips.position.y += Math.sin(ph) * .004; for (let i = 1; i <= 3; i++) R('tail_' + i, Math.sin(ph - i * .6) * .04, 0, Math.sin(ph - i * .6) * .06); R('thigh_FR', Math.max(0, Math.sin(ph * .5 - 1.2)) * .12); }
  extra(ph, mode); };

// ====================================== BRIAR FLEETSTRIDE (centaur ranger; Valen's rig, chestnut coat) ======================================
CHARS4.briar = { name: 'Briar Fleetstride', sheetKey: 'briar', build() {
  const c = makeCtx({ name: 'Briar_Fleetstride', hd: true, eye: 0x4a7a3a, fem: true, bulk: .98, sw: .98, skin: 0xe8b898, hair: 0xa8441e, under: 0x3f6a34, pants: 0x3f6a34, sleeve: 0x3f6a34, glove: 0x6a4126, boot: 0x6a4126 });
  const h = humanoid(c), { gold, leather, dleather } = pal(c), { add, G, M, bones: B, bone } = c, root = h.root, green = 0x3f6a34, dgreen = 0x2a4a28;
  for (const S of ['L', 'R']) { const th = B['thigh_' + S]; th.parent.remove(th); for (const n of ['thigh_', 'shin_', 'foot_']) delete B[n + S]; }
  const waist = B.hips; waist.name = 'waist'; B.waist = waist; delete B.hips;
  const hb = horseBody(c, root, { coat: 0x8a4a28, dcoat: 0x5a2e1a, sock: 0xf2ece0, tail: 0xa8441e }), { hips, hSpine, hChest } = hb; hChest.add(waist); waist.position.set(0, .2, .12);
  const gm = M(green, { r: .9, d: 1, n: 'gcloth' }), gt = M(0xd2a43c, { m: .4, r: .4, n: 'trim' }), br = M(0x6a4126, { r: .85, n: 'bleather' }), dbr = M(0x3c2616, { r: .85, n: 'dbleather' }), leaf = M(0x4f8a3a, { r: .9, d: 1, n: 'leafg' }), flower = M(0xf6f2e6, { r: .6, n: 'flower' });
  add(hSpine, G.box(.5, .035, .62), gm, 0, .3, 0); add(hSpine, G.box(.52, .03, .035), gt, 0, .3, .31); add(hSpine, G.box(.52, .03, .035), gt, 0, .3, -.31); add(hSpine, G.box(.2, .036, .4), M(0xd2a43c, { r: .5, n: 'blankgold' }), 0, .32, 0);
  for (const k of [-1, 1]) { add(hSpine, G.box(.03, .4, .55), gm, k * .3, .12, 0, { r: [0, 0, k * .1] }); add(hSpine, G.box(.034, .03, .55), gt, k * .32, -.08, 0, { r: [0, 0, k * .1] }); emblem(c, hSpine, 'fleur', .18, gt, k * .325, .08, 0, k * PI / 2);
    add(hips, G.box(.12, .17, .2), br, k * .34, -.0, -.0, { r: [0, 0, k * .1] }); add(hips, G.box(.125, .05, .21), dbr, k * .34, .1, 0, { r: [0, 0, k * .1] }); add(hips, G.cyl(.014, .014, .01, 6), gt, k * .405, .05, .05, { r: [0, 0, PI / 2] }); }
  add(hSpine, G.cyl(.07, .07, .5, 8), M(0x3f6a34, { r: .9, n: 'bedroll' }), 0, .38, -.28, { r: [0, 0, PI / 2] }); add(hSpine, G.cyl(.072, .072, .03, 8), br, .12, .38, -.28, { r: [0, 0, PI / 2] }); add(hSpine, G.cyl(.072, .072, .03, 8), br, -.12, .38, -.28, { r: [0, 0, PI / 2] });
  { const hn = add(hChest, G.cone(.04, .22, 6), M(0xf0e4c8, { r: .6, n: 'horn' }), -.3, .0, .2, { r: [0, 0, 1.2] }); add(hChest, G.tor(.045, .008, 4, 8), gt, -.28, .0, .2, { r: [0, PI / 2, 0] }); }
  // leafy vines + flowers on tail & flank
  for (let i = 1; i <= 3; i++) for (let j = 0; j < 3; j++) { add(c.bones['tail_' + i], G.cone(.02, .07, 4), leaf, (j - 1) * .04, -.1 - j * .08, .04, { r: [PI + .2, 0, (j - 1) * .5], s: [1, 1, .3] }); if (j === 1) add(c.bones['tail_' + i], G.sph(.015, 5, 4), flower, 0, -.12, .06); }
  // human torso: green leather bodice w/ gold leaf trim, brown bracers, green cloak
  add(B.chest, G.cyl(.18, .13, .28, 8), M(green, { r: .85, n: 'bodice' }), 0, .1, .006, { s: [1, 1, .72] }); add(B.chest, G.box(.16, .3, .02), M(0x7a5028, { r: .8 }), 0, .1, .125); add(B.spine, G.cyl(.14, .15, .14, 8), dbr, 0, .0, 0, { s: [1, 1, .75] }); belt(c, dbr, gt, 0, .15); strapX(c, br, gt);
  for (let i = 0; i < 5; i++) add(B.chest, G.cone(.02, .07, 4), leaf, (i - 2) * .06, .22, .125, { r: [PI, 0, 0], s: [1, 1, .3] });
  for (const S of ['L', 'R']) { const k = S === 'L' ? 1 : -1, fa = B['foreArm_' + S]; add(fa, G.cyl(.054, .048, .2, 8), dbr, 0, -.15, 0); add(fa, G.cyl(.056, .056, .02, 8), gt, 0, -.05, 0); add(B['upperArm_' + S], G.cyl(.06, .056, .12, 8), br, 0, -.2, 0); add(B['shoulder_' + S], G.dome(.1, 8, 4), M(dgreen, { r: .9, n: 'mantle' }), k * .06, .01, 0, { s: [1.2, .7, 1.1], r: [0, 0, -k * .3] }); }
  const cp = cape(c, { topW: .6, botW: 1.3, len: .9, col: green, trim: 0xd2a43c, lining: dgreen, waves: 9, segs: 18, seed: 51, wrap: .15, ragged: .22 }); cp.len = .9;
  for (const k of [-1, 0, 1]) emblem(c, cp.cb, 'fleur', .13, gt, k * .28, -.62, cp.z(.7) - .026, PI);
  K.leafCluster(c, B.neck, 9, .1, 0x3f7a35, .02, .0);
  // long auburn hair w/ leaves & white flowers, pointed ears
  hair(c, 'wavy', 0xa8441e, { len: 1.1 }); hair(c, 'swept', 0xa8441e); for (const k of [-1, 1]) { add(B.head, G.box(.08, .7, .1), M(0xa8441e, { r: .85, n: 'hairb' }), k * .13, -.33, -.04); add(B.chest, G.box(.09, .6, .1), M(0xa8441e, { r: .85 }), k * .2, -.02, -.1); add(B.head, G.cone(.035, .15, 4), M(0xe8b898, { r: .8 }), k * .12, .12, -.01, { r: [0, 0, -k * 1.15], s: [1, 1, .4] }); add(B.head, G.cone(.025, .08, 4), leaf, k * .1, .2, .06, { r: [.4, 0, -k * .7], s: [1, 1, .3] }); add(B.head, G.sph(.014, 5, 4), flower, k * .09, .18, .1); }
  for (let i = 0; i < 4; i++) add(B.head, G.sph(.014, 5, 4), flower, -.1 + i * .04, .02 - i * .12, -.12);
  // bow (L hand) + quiver of arrows
  K.quiver(c, M(0x5a3a22, { r: .8, n: 'quiverw' }), gt, 6);
  const bw = K.bow(c, { wood: M(0x7a5028, { r: .6, n: 'bowwood' }), gold: gt, r: .7 }); for (let i = 0; i < 4; i++) add(bw, G.cone(.03, .1, 4), leaf, -.7 + .08, .66 - i * .08, .0, { r: [0, 0, 1 + i], s: [1, 1, .3] }); hold(c, waist, 'hand_L', bw, 0, -.05, 0, 0, -PI / 2, 0);
  const ar = new THREE.Group(); add(ar, G.cyl(.005, .005, .62, 4), M(0x8a6a3a), 0, 0, 0); add(ar, G.cone(.014, .05, 4), M(0xc6cdd4, { m: .6, r: .4 }), 0, -.33, 0, { r: [PI, 0, 0] }); add(ar, G.cone(.02, .05, 3), M(0xf0ead8, { d: 1 }), 0, .27, 0, { s: [1, 1, .3] }); hold(c, waist, 'hand_R', ar, 0, -.04, 0, PI / 2 + .1, 0, 0);
  B.upperArm_L.rotation.set(-.5, 0, .2); B.foreArm_L.rotation.set(-.7, 0, 0); B.upperArm_R.rotation.set(-.4, 0, -.2); B.foreArm_R.rotation.set(-.9, 0, 0);
  const upd = (t, mode, R, Bn) => horseUpd(t, mode, R, Bn, (ph, m) => { if (m === 'walk') { R('waist', 0, Math.sin(ph) * .03); R('head', 0, Math.sin(ph) * .03); R('cape', .1 + Math.sin(ph * 2 - 1) * .05, 0, Math.sin(ph) * .03); R('upperArm_R', Math.sin(ph) * .05); } else { R('waist', 0, Math.sin(ph * .5) * .03); R('head', Math.sin(ph * .5) * .02, Math.sin(ph * .5) * .08); R('cape', .02 + Math.sin(ph + 1) * .02); } });
  return bakeRig(c, root, 'Briar_Fleetstride', upd, { L: 1, R: 1 }); } };

// ====================================== ZEPHYR (hippogriff: eagle fore, horse hind) ======================================
CHARS4.zephyr = { name: 'Zephyr (hippogriff)', sheetKey: 'zephyr', build() {
  const c = makeCtx({ name: 'Zephyr' }), { add, G, M, bone } = c, { gold, leather, dleather, brass } = pal(c);
  const cream = M(0xf0e4c4, { r: 1, n: 'zcream' }), gf = M(0xe0b050, { r: .9, n: 'zgold' }), gf2 = M(0xc8903a, { r: .9, n: 'zgold2' }), wh = M(0xfaf2de, { r: 1, n: 'zwhite' }), yl = M(0xe0a830, { r: .5, n: 'zbeak' }), blue = M(0x24429a, { r: .9, d: 1, n: 'blue' }), tm = M(0xd2a43c, { m: .4, r: .4, n: 'trim' });
  const root = bone('root', null), hb = horseBody(c, root, { coat: 0xf0e4c4, dcoat: 0xe6d6ac, sock: 0xf8f0dc, tail: 0xefd9a0, chestMat: cream, eagle: true, eagleFeather: cream, eagleGold: gf, y: 1.0 }), { hips, hSpine, hChest } = hb;
  // chest ruff + back feathers
  for (let r = 0; r < 3; r++) for (let i = 0; i < 7; i++) add(hChest, G.cone(.06, .18 - r * .02, 4), [wh, cream, gf][(i + r) % 3], (i - 3) * .075, .12 - r * .12, .28 - r * .03, { r: [PI + .35, 0, (i - 3) * .12], s: [1, 1, .4] });
  for (let i = 0; i < 6; i++) add(hSpine, G.cone(.05, .14, 4), [cream, gf][i % 2], ((i % 3) - 1) * .15, .27, -.15 + (i < 3 ? .2 : -.2), { r: [PI + .5, 0, ((i % 3) - 1) * .2], s: [1, 1, .4] });
  // neck + eagle head
  const neck = bone('neck', hChest, 0, .26, .22), head = bone('head', neck, 0, .34, .1), jaw = bone('jaw', head, 0, -.03, .05); neck.rotation.x = .25; head.rotation.x = -.15;
  add(neck, G.sph(.17, 8, 6), cream, 0, .1, 0, { s: [.95, 1.7, 1.1] }); for (let i = 0; i < 6; i++) add(neck, G.cone(.05, .16, 4), [wh, cream][i % 2], ((i % 3) - 1) * .09, .2 - Math.floor(i / 3) * .12, .12, { r: [PI + .2, 0, 0], s: [1, 1, .4] });
  add(head, G.sph(.13, 9, 7), wh, 0, .03, 0, { s: [.95, 1.05, 1.15] }); add(head, G.cone(.07, .2, 5), yl, 0, -.015, .16, { r: [PI / 2, 0, 0], s: [1, 1, 1.15] }); add(head, G.cone(.045, .1, 4), yl, 0, -.065, .26, { r: [PI / 2 + 1.0, 0, 0] }); add(jaw, G.box(.07, .025, .16), yl, 0, -.02, .12);
  for (const k of [-1, 1]) { add(head, G.sph(.024, 6, 5), M(0xffb800, { e: 0xffa000, ei: .35, n: 'zeye' }), k * .085, .07, .09); add(head, G.sph(.011, 4, 3), M(0x100804), k * .097, .07, .105); add(head, G.box(.07, .02, .05), gf, k * .08, .1, .09, { r: [0, 0, k * -.3] }); }
  for (let i = 0; i < 7; i++) { const a = (i - 3) * .3; add(head, G.cone(.03, .16 + (i % 2) * .05, 4), i % 2 ? gf : cream, Math.sin(a) * .06, .15, -.06 + Math.cos(a) * -.02, { r: [-.6, 0, -a * .8], s: [1, 1, .4] }); }
  // tack: bridle, chest harness + medallion, blue fleur caparison, tassels
  add(head, G.tor(.115, .008, 4, 12), dleather, 0, .0, .04, { r: [0, PI / 2, 0], s: [1, 1.05, 1] }); add(head, G.tor(.095, .008, 4, 12), dleather, 0, .02, .14, { r: [0, PI / 2, 0] });
  add(hChest, G.tor(.3, .022, 5, 14), dleather, 0, -.02, .1, { r: [0, 0, 0], s: [1, 1.05, .8] }); add(hChest, G.cyl(.075, .075, .02, 10), tm, 0, -.02, .39, { r: [PI / 2, 0, 0] }); emblem(c, hChest, 'sun', .1, M(0x24429a), 0, -.02, .405);
  for (const k of [-1, 1]) for (const [bn, w] of [[hSpine, .6], [hips, .5]]) { add(bn, G.box(.03, .5, w), blue, k * .3, -.1, 0, { r: [0, 0, k * .1] }); add(bn, G.box(.034, .035, w), tm, k * .32, -.35, 0, { r: [0, 0, k * .1] }); emblem(c, bn, 'fleur', .22, tm, k * .325, -.08, 0, k * PI / 2); for (let i = 0; i < 3; i++) tassel(c, bn, 0xd2a43c, k * .33, -.36, (i - 1) * w * .35, .9); }
  add(hSpine, G.box(.5, .035, .6), blue, 0, .3, 0); add(hSpine, G.box(.52, .03, .03), tm, 0, .3, .3); add(hSpine, G.box(.52, .03, .03), tm, 0, .3, -.3); add(hSpine, G.box(.22, .05, .3), dleather, 0, .33, 0);
  // wings (hawk-style fans, raised) with bone chains wing_L/R + wingTip_L/R
  for (const k of [-1, 1]) { const S = k > 0 ? 'L' : 'R', w = bone('wing_' + S, hChest, k * .24, .3, -.1), wt = bone('wingTip_' + S, w, 0, -.55, 0); w.rotation.z = k * 2.3; w.rotation.x = .15;
    add(w, G.sph(.1, 7, 5), cream, k * .01, -.2, 0, { s: [.6, 3, .9] }); add(w, G.box(.07, .5, .06), cream, k * .02, -.25, 0);
    fan(c, w, k, { n: 7, l0: .3, l1: .5, a0: -.15, spread: -.75, mats: [cream, wh], w: .11, z: .008 }); fan(c, w, k, { n: 7, l0: .5, l1: .38, a0: .05, spread: .6, mats: [gf, gf2], w: .115, z: -.008 });
    fan(c, wt, k, { n: 8, l0: .45, l1: .62, a0: -.25, spread: 1.0, mats: [gf, wh, gf2], w: .1 }); fan(c, wt, k, { n: 5, l0: .3, l1: .2, a0: -.45, spread: -.35, mats: [cream, wh], w: .06, z: .01 }); }
  const upd = (t, mode, R, Bn) => horseUpd(t, mode, R, Bn, (ph, m) => { const j = m === 'walk' ? 1 : .35;
    for (const S of ['L', 'R']) { const k = S === 'L' ? 1 : -1; R('wing_' + S, 0, 0, k * (-.15 + Math.sin(ph * (m === 'walk' ? 2 : 1)) * .14 * j * (m === 'walk' ? 1.6 : 1))); R('wingTip_' + S, 0, 0, k * Math.sin(ph * (m === 'walk' ? 2 : 1) - 1) * .18 * j); }
    R('neck', Math.sin(ph * (m === 'walk' ? 2 : 1)) * .03 * j); R('head', m === 'walk' ? 0 : Math.sin(ph * .5) * .03, Math.sin(ph * .5) * (m === 'walk' ? .05 : .25)); R('jaw', Math.max(0, Math.sin(ph * 2)) * .05); });
  return bakeRig(c, root, 'Zephyr', upd, {}); } };
export const ORDER4 = ['cinder', 'neris', 'briar', 'zephyr', 'coral', 'mortimer', 'pip'];
