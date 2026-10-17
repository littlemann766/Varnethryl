// The 12 VARNETHRYL hero prototypes (from the boss's character sheets). Each build() returns a rig {root,bones,update,clips}.
import * as THREE from 'three';
import * as K from './chars_core.js';
const { makeCtx, humanoid, platePack, belt, strapX, hair, hood, furCollar, cape, tabard, skirt, emblem, skull, finalize } = K;
const PI = Math.PI;
const pal = c => ({
  steel: c.M(0xb4bac2, { m: .4, r: .38, n: 'steel' }), gold: c.M(0xd2a43c, { m: .4, r: .35, n: 'gold' }), leather: c.M(0x5a3720, { r: .85, n: 'leather' }),
  dleather: c.M(0x3c2616, { r: .85, n: 'dleather' }), brass: c.M(0xb07a34, { m: .4, r: .4, n: 'brass' }) });
const hold = (c, b, n, g, px = 0, py = -.05, pz = 0, rx = 0, ry = 0, rz = 0) => { g.position.set(px, py, pz); g.rotation.set(rx, ry, rz); c.bones[n].add(g); return g; };
const bell = (c, S, col, trim, len = .3, r1 = .12) => { const { add, G, M, bones: B } = c; add(B['foreArm_' + S], G.cyl(.06, r1, len, 8, true), M(col, { r: .9, d: 1 }), 0, -.15, 0); add(B['foreArm_' + S], G.cyl(r1, r1, .03, 8, true), M(trim, { m: .35, r: .55, d: 1 }), 0, -.15 - len / 2, 0); };
const backEmblem = (c, cp, type, size, mat, f = .4) => emblem(c, cp.cb, type, size, mat, 0, -f * (cp.len ?? 1), cp.z(f) - .024, PI);
const chain = (c, par, mat, x0, y0, z0, n, dy = -.04, r = .012) => { for (let i = 0; i < n; i++) c.add(par, c.G.tor(r * 1.4, r * .5, 4, 6), mat, x0, y0 + dy * i, z0, { r: [0, i % 2 ? PI / 2 : 0, 0] }); };
export const CHARS = {};

CHARS.aldric = { name: 'Sir Aldric', sheetKey: 'aldric', build() {
  const c = makeCtx({ name: 'Sir_Aldric', bulk: 1.1, sw: 1.06, skin: 0xe6b890, hair: 0xd9b36a, under: 0x2b2b30, pants: 0x2a2a30, sleeve: 0x4a4a52, glove: 0x2a2a2e, boot: 0x6b6b72 });
  const h = humanoid(c), { steel, gold, leather } = pal(c), blue = c.M(0x1f3f95, { r: .95, n: 'blue' });
  platePack(c, { steel, trim: gold, bigPauld: true }); hair(c, 'swept', 0xd9b36a); belt(c, leather, gold); strapX(c, leather, gold);
  tabard(c, { w: .27, len: .52, col: 0x1f3f95, trim: gold, emblem: 'lion', emblem2: 'fleur', point: .07, z: .165 });
  const cp = cape(c, { topW: .52, botW: 1.05, len: .98, col: 0x1f3f95, trim: gold.color.getHex(), lining: 0x182f72, waves: 8 }); cp.len = .98;
  backEmblem(c, cp, 'lion', .5, gold, .4); for (const k of [-1, 0, 1]) emblem(c, cp.cb, 'fleur', .13, gold, k * .26, -.86, cp.z(.88) - .026, PI);
  const sw = K.sword(c, { gold, blade: 0xcfd6dd, len: .85 }); hold(c, h.hips, 'hand_R', sw, 0, -.05, 0, 2.3);
  const sh = K.kiteShield(c, { rim: gold, face: blue, emblem: 'lion' }); sh.scale.setScalar(1.1); hold(c, h.hips, 'foreArm_L', sh, .1, -.1, .07, .3, .3, 0);
  for (const k of [-1, 1]) K.pouch(c, c.bones.hips, 0x5a3720, k * .16, -.05, -.02, .8, gold);
  return finalize(c, h.root, { L: 1, R: 1 }); } };

CHARS.darius = { name: 'Darius Umbral', sheetKey: 'darius', build() {
  const c = makeCtx({ name: 'Darius_Umbral', bulk: 1.2, sw: 1.15, skin: 0xd9ab88, hair: 0x2a1c14, under: 0x1e1c24, pants: 0x1e1c22, sleeve: 0x2c2c34, glove: 0x202024, boot: 0x2c2c32 });
  const h = humanoid(c), { gold, leather, brass } = pal(c), steel = c.M(0x5a5d6b, { m: .4, r: .45, n: 'darksteel' }), bronze = c.M(0xb08d4a, { m: .4, r: .4, n: 'bronze' });
  platePack(c, { steel, trim: bronze, pauld: 'spike', bigPauld: true }); hair(c, 'messy', 0x2a1c14); belt(c, leather, bronze);
  tabard(c, { w: .2, len: .6, col: 0x4a2278, trim: bronze, emblem: 'ornate', point: .08, z: .17 });
  const cp = cape(c, { topW: .58, botW: 1.15, len: 1.0, col: 0x4a2278, trim: bronze.color.getHex(), lining: 0x321a52, ragged: .16, segs: 18, seed: 5, waves: 10 }); cp.len = 1.0;
  backEmblem(c, cp, 'ornate', .55, c.M(0xbfa878, { r: .6, m: .3 }), .42);
  skull(c, c.bones.hips, bronze, .045, 0, -.06, .2); chain(c, c.bones.hips, bronze, 0, -.09, .21, 5);
  for (const k of [-1, 1]) { skull(c, c.bones['shoulder_' + (k > 0 ? 'L' : 'R')], bronze, .03, k * .05, .12, .08); chain(c, c.bones.chest, bronze, k * .05, .25, .1, 4, -.045); }
  const sw = K.sword(c, { gold: bronze, blade: 0x1c1626, len: 1.0, guard: .3, glow: 0x7a22d8, gem: 0xb040ff, grip: 0x2a1a10 });
  for (let i = 0; i < 3; i++) c.add(sw, c.G.cone(.02, .14, 4), c.M(0x7a22d8, { e: 0x9a40ff, ei: 1.2 }), (i - 1) * .1, .07, 0, { r: [0, 0, (i - 1) * -.6] });
  hold(c, h.hips, 'hand_R', sw, 0, -.05, 0, 2.4);
  return finalize(c, h.root, { R: 1 }); } };

CHARS.selene = { name: 'Selene Frostveil', sheetKey: 'selene', build() {
  const c = makeCtx({ name: 'Selene_Frostveil', fem: true, nobust: true, bulk: .92, sw: .98, skin: 0xf0c8a8, hair: 0xe6cf9c, under: 0xe9e3d3, pants: 0x2a3f78, sleeve: 0x2b4fa8, glove: 0x23232a, boot: 0xc4c8d2 });
  const h = humanoid(c), { steel, gold, leather } = pal(c), cream = c.M(0xf2eee4, { r: 1, n: 'fur' });
  c.add(c.bones.chest, c.G.cyl(.17, .12, .22, 8), steel, 0, .1, .005, { s: [1, 1, .72] }); belt(c, leather, gold);
  c.add(c.bones.chest, c.G.box(.09, .09, .02), c.M(0x6ec8ff, { e: 0x3a9cff, ei: .7 }), 0, .2, .105, { r: [0, 0, PI / 4] });
  furCollar(c, cream, .21, .09);
  skirt(c, { col: 0x2b4fa8, trim: 0xf2eee4, len: .52, top: .17, bot: .3, y: -.04 }); skirt(c, { col: 0xf2eee4, trim: 0xd2a43c, len: .62, top: .15, bot: .26, y: -.06, zs: .8 });
  tabard(c, { w: .2, len: .45, col: 0xf2eee4, trim: gold, emblem: 'snow', point: .08, z: .2, tilt: -.02, y: -.06 });
  for (const S of ['L', 'R']) bell(c, S, 0x2b4fa8, 0xf2eee4, .34, .13);
  hair(c, 'wavy', 0xe6cf9c, { len: .75 }); c.add(c.bones.head, c.G.oct(.03), c.M(0x6ec8ff, { e: 0x3a9cff, ei: .9 }), 0, .26, .09, { s: [.7, 1.8, .7] });
  const cp = cape(c, { topW: .6, botW: 1.2, len: 1.05, col: 0x2b4fa8, trim: 0xf2eee4, lining: 0xf2eee4, waves: 7, wrap: .15 }); cp.len = 1.05;
  backEmblem(c, cp, 'snow', .6, c.M(0xdbe9ff, { r: .5 }), .55); for (const k of [-1, 1]) emblem(c, cp.cb, 'snow', .16, c.M(0xdbe9ff, { r: .5 }), k * .3, -.92, cp.z(.9) - .026, PI);
  const st = K.staff(c, 'crystal', { gold, wood: c.M(0x6b5a3a, { r: .6, m: .4 }), len: 1.85 }); hold(c, h.hips, 'hand_R', st.g, 0, -.05, 0, .3);
  const bk = K.book(c, 0x24409a, gold, .15, .2); bk.position.set(.22, -.12, .04); bk.rotation.set(0, PI / 2, .1); c.bones.hips.add(bk); emblem(c, bk, 'snow', .12, gold, 0, 0, .03);
  for (let i = 0; i < 4; i++) c.add(c.bones.hips, c.G.oct(.02), c.M(0x6ec8ff, { e: 0x3a9cff, ei: .8 }), -.1 + i * .06, -.07 - i % 2 * .04, .17, { s: [.7, 1.8, .7] });
  return finalize(c, h.root, { R: 1 }); } };

CHARS.seraphine = { name: 'Dame Seraphine', sheetKey: 'x0', build() {
  const c = makeCtx({ name: 'Dame_Seraphine', fem: true, nobust: true, bulk: 1.0, sw: 1.0, skin: 0xf0c8a4, hair: 0xe0a850, under: 0x2b2b30, pants: 0x2a2a30, sleeve: 0x4a4a52, glove: 0x2a2a2e, boot: 0x6b6b72 });
  const h = humanoid(c), { steel, gold, leather } = pal(c), blue = c.M(0x2a3f8a, { r: .9, n: 'blue' });
  platePack(c, { steel, trim: gold, tassets: false }); hair(c, 'wavy', 0xe0a850, { len: .8 }); belt(c, leather, gold);
  c.add(c.bones.head, c.G.tor(.115, .014, 4, 14), gold, 0, .18, 0, { r: [PI / 2 - .15, 0, 0] }); for (const k of [-1, 1]) c.add(c.bones.head, c.G.tor(.03, .012, 4, 8), c.M(0xe0a850), k * .09, .08, -.03, { s: [1, 1.6, 1] });
  tabard(c, { w: .28, len: .62, col: 0xf1ead8, trim: gold, emblem: 'sun', emblem2: 'fleur', point: .07, z: .17 });
  skirt(c, { col: 0x2a3f8a, trim: gold, len: .42, top: .16, bot: .27, y: -.06, zs: .85 });
  const cp = cape(c, { topW: .55, botW: 1.1, len: 1.0, col: 0xf1ead8, trim: gold.color.getHex(), lining: 0x2a3f8a, waves: 8 }); cp.len = 1.0;
  backEmblem(c, cp, 'sun', .55, gold, .42); for (const k of [-1, 1]) emblem(c, cp.cb, 'fleur', .13, gold, k * .28, -.88, cp.z(.9) - .026, PI);
  const mc = K.mace(c, { gold }); hold(c, h.hips, 'hand_R', mc, 0, -.05, 0, .3);
  const sh = K.kiteShield(c, { rim: gold, face: blue, emblem: 'sun' }); sh.scale.setScalar(1.05); hold(c, h.hips, 'foreArm_L', sh, .1, -.1, .07, .3, .3, 0);
  K.pouch(c, c.bones.hips, 0x5a3720, .16, -.05, -.02, .8, gold);
  return finalize(c, h.root, { L: 1, R: 1 }); } };

CHARS.talia = { name: 'Talia Stormcall', sheetKey: 'x1', build() {
  const c = makeCtx({ name: 'Talia_Stormcall', fem: true, nobust: true, bulk: .95, sw: 1.0, skin: 0xb98560, hair: 0x3a2418, under: 0x1f6f7a, pants: 0x3a2a20, sleeve: 0x1f6f7a, glove: 0x4a3020, boot: 0x4a3322 });
  const h = humanoid(c), { gold, leather, dleather } = pal(c), fur = c.M(0xf0e6d0, { r: 1, n: 'fur' }), teal = 0x1f6f7a, bronze = c.M(0xb08a4a, { m: .4, r: .45, n: 'bronze' });
  c.add(c.bones.chest, c.G.cyl(.17, .12, .24, 8), dleather, 0, .09, .01, { s: [1, 1, .72] }); belt(c, dleather, bronze); strapX(c, leather, bronze);
  furCollar(c, fur, .24, .1); furCollar(c, c.M(0x2c8a96), .26, .045);
  skirt(c, { col: 0xe9dfc8, trim: teal, len: .78, top: .17, bot: .38, y: -.04, ragged: .04 }); skirt(c, { col: teal, trim: 0xf0e6d0, len: .55, top: .16, bot: .32, y: -.03, zs: .85, ragged: .05, segs: 16 });
  tabard(c, { w: .22, len: .6, col: teal, trim: bronze, emblem: 'spiral', point: .08, z: .2, y: -.04 });
  for (const S of ['L', 'R']) bell(c, S, 0xf0e6d0, teal, .32, .12); hair(c, 'wavy', 0x3a2418, { len: .85 });
  const cp = cape(c, { topW: .62, botW: 1.25, len: 1.0, col: teal, trim: 0xf0e6d0, lining: 0xe9dfc8, waves: 9, ragged: .09, segs: 18, seed: 3 }); cp.len = 1.0;
  backEmblem(c, cp, 'spiral', .6, c.M(0xf0e6d0), .45);
  const feath = [0x2c5fa8, 0xf0ead8, 0x2c8a96];
  for (let i = 0; i < 9; i++) { const k = i % 2 ? 1 : -1, par = c.bones['shoulder_' + (k > 0 ? 'L' : 'R')]; K.feather(c, par, feath[i % 3], k * (.06 + (i % 3) * .035), -.08 - (i % 3) * .03, .03 + (i % 2) * .05, [PI - .1, 0, k * .2], .22 + (i % 3) * .05); }
  for (let i = 0; i < 6; i++) K.feather(c, c.bones.hips, feath[i % 3], (i - 2.5) * .06, -.1, .17, [PI, 0, (i - 2.5) * .12], .2);
  c.add(c.bones.chest, c.G.tor(.1, .012, 4, 12), c.M(0x2aa8c8, { r: .4 }), 0, .22, .07, { r: [PI / 2 - .4, 0, 0] }); emblem(c, c.bones.chest, 'spiral', .1, bronze, 0, .08, .13);
  skull(c, c.bones.hips, c.M(0xefe6d0), .03, .13, -.05, .15);
  const st = K.staff(c, 'storm', { gold: bronze, wood: c.M(0x6b4528, { r: .9 }), len: 1.85, twist: true }); hold(c, h.hips, 'hand_R', st.g, 0, -.05, 0, .3);
  return finalize(c, h.root, { R: 1 }); } };

CHARS.finn = { name: 'Finn Valecourt', sheetKey: 'x2', build() {
  const c = makeCtx({ name: 'Finn_Valecourt', bulk: .86, sw: .96, skin: 0xe8b890, hair: 0x6a3f24, under: 0x1f3a8a, pants: 0x4a3020, sleeve: 0xe8e0cc, glove: 0x3a2618, boot: 0x3a2618 });
  const h = humanoid(c), { steel, gold, leather } = pal(c), blue = c.M(0x1f3a8a, { r: .9, n: 'blue' });
  platePack(c, { steel, trim: gold, cuirass: blue, tassets: false, cuisse: false, noGaunt: true });
  c.add(c.bones.spine, c.G.cyl(.15, .15, .1, 8), c.M(0x8e1c2a, { r: .9 }), 0, -.02, 0, { s: [1, 1, .75] }); c.add(c.bones.spine, c.G.sph(.04, 5, 4), c.M(0x8e1c2a), .1, -.03, .12);
  for (const x of [.09, .12]) c.add(c.bones.spine, c.G.cyl(.008, .008, .18, 4), gold, x, -.13, .12);
  skirt(c, { col: 0x1f3a8a, trim: gold, len: .36, top: .15, bot: .26, y: -.05, zs: .85 });
  tabard(c, { w: .2, len: .3, col: 0x1f3a8a, trim: gold, emblem: 'fleur', point: .05, z: .17, y: -.03 });
  c.add(c.bones.chest, c.G.cone(.07, .16, 6), c.M(0xf5f1e6, { r: 1 }), 0, .2, .12, { r: [PI, 0, 0] }); for (let i = 0; i < 3; i++) c.add(c.bones.chest, c.G.sph(.035, 5, 4), c.M(0xf5f1e6), (i - 1) * .04, .13, .14);
  for (const S of ['L', 'R']) c.add(c.bones['hand_' + S], c.G.cyl(.05, .065, .05, 8, true), c.M(0xf5f1e6, { d: 1 }), 0, 0, 0);
  hair(c, 'swept', 0x6a3f24);
  const cp = cape(c, { topW: .55, botW: 1.2, len: 1.0, col: 0x8e1c2a, trim: gold.color.getHex(), lining: 0x1f3a8a, waves: 8, wrap: .14, flare: .18 }); cp.len = 1.0;
  c.add(cp.cb, c.G.box(.34, .55, .01), blue, 0, -.4, cp.z(.4) - .02); emblem(c, cp.cb, 'fleur', .4, gold, 0, -.42, cp.z(.42) - .03, PI);
  c.add(c.bones.chest, c.G.tor(.05, .01, 4, 10), gold, 0, .24, -.1); for (const k of [-1, 1]) c.add(c.bones.chest, c.G.tor(.07, .01, 4, 10), gold, k * .1, .26, -.08, { r: [.4, 0, 0] });
  const rp = K.rapier(c, gold, 1.0); hold(c, h.hips, 'hand_R', rp, 0, -.05, 0, 2.3);
  return finalize(c, h.root, { R: 1 }, B => { B.upperArm_R.rotation.set(-.2, 0, -.2); B.foreArm_R.rotation.set(-.6, 0, 0); }); } };

CHARS.brynn = { name: 'Brynn Cogwright', sheetKey: 'x3', build() {
  const c = makeCtx({ name: 'Brynn_Cogwright', fem: true, nobust: true, bulk: .96, sw: .98, skin: 0xf0c4a0, hair: 0xc9622b, under: 0xe8dcc0, pants: 0x3a3028, sleeve: 0xe8dcc0, glove: 0x4a3020, boot: 0x5a3a22 });
  const h = humanoid(c), { gold, leather, dleather, brass } = pal(c), blue = 0x2f4f9a;
  c.add(c.bones.chest, c.G.cyl(.18, .125, .24, 8), c.M(0x7a4a26, { r: .85 }), 0, .09, .012, { s: [1, 1, .72] }); belt(c, dleather, brass); strapX(c, leather, brass);
  c.add(c.bones.chest, c.G.tor(.1, .028, 5, 12), c.M(0x2f4f9a), 0, .25, 0, { r: [PI / 2 - .2, 0, 0] });
  skirt(c, { col: blue, trim: 0xd2a43c, len: .6, top: .17, bot: .34, y: -.04, ragged: .02 });
  tabard(c, { w: .24, len: .5, col: 0x7a4a26, trim: brass, emblem: 'gear', point: .06, z: .2, y: -.02 });
  const cp = cape(c, { topW: .4, botW: .75, len: .75, col: blue, trim: 0xd2a43c, waves: 6, wrap: .08, back: .14 }); cp.len = .75; backEmblem(c, cp, 'gear', .35, brass, .4);
  for (const S of ['L', 'R']) { c.add(c.bones['foreArm_' + S], c.G.cyl(.052, .046, .14, 8), dleather, 0, -.16, 0); c.add(c.bones['foreArm_' + S], c.G.cyl(.055, .055, .02, 8), brass, 0, -.1, 0); c.add(c.bones['shin_' + S], c.G.sph(.06, 6, 5), c.M(0x8a6a3a, { m: .4, r: .45 }), 0, .01, .05, { s: [1, 1, .6] }); c.add(c.bones['shin_' + S], c.G.cyl(.066, .066, .02, 8), brass, 0, -.36, 0); }
  hair(c, 'bun', 0xc9622b); K.goggles(c, brass, dleather);
  K.pouch(c, c.bones.hips, 0x7a4a26, .19, -.08, .04, 1.5, brass); rope(c, c.bones.hips, -.2, -.02, .02); function rope(c, p, x, y, z) { K.rope(c, p, x, y, z); }
  for (let i = 0; i < 3; i++) c.add(c.bones.hips, c.G.cyl(.008, .008, .12, 4), i % 2 ? brass : c.M(0x9aa2aa, { m: .4, r: .3 }), .17 + i * .02, .04, .06, { r: [0, 0, .2] });
  const tr = new THREE.Group(); c.add(tr, c.G.tor(.07, .012, 4, 12), c.M(0x6a6a70, { m: .4, r: .4 }), 0, 0, 0, { r: [PI / 2, 0, 0] }); for (let i = 0; i < 8; i++) { const a = i / 8 * PI * 2; c.add(tr, c.G.cone(.012, .04, 4), c.M(0x6a6a70, { m: .4 }), Math.sin(a) * .07, .02, Math.cos(a) * .07); } tr.position.set(-.05, -.1, -.19); c.bones.hips.add(tr);
  const cb = K.crossbow(c, { metal: c.M(0x555a60, { m: .4, r: .4 }), gold: brass, gear: true, wood: 0x5a3a22 }); hold(c, h.hips, 'hand_R', cb, 0, -.04, -.02, .3, -.15, 0); cb.scale.setScalar(.62);
  return finalize(c, h.root, { R: 1 }, B => { B.upperArm_R.rotation.set(-.35, 0, -.1); B.foreArm_R.rotation.set(-.8, 0, 0); }); } };

CHARS.mirelle = { name: 'Mirelle Thornroot', sheetKey: 'x6', build() {
  const c = makeCtx({ name: 'Mirelle_Thornroot', fem: true, nobust: true, bulk: .94, sw: .98, skin: 0xf0c8a8, hair: 0x9a5a30, under: 0xefe6d0, pants: 0x4a3626, sleeve: 0xefe6d0, glove: 0x4a3020, boot: 0x5a3a22 });
  const h = humanoid(c), { gold, leather, dleather } = pal(c), green = 0x2f5d38, leaf = 0x3b7a3a;
  c.add(c.bones.chest, c.G.cyl(.17, .12, .24, 8), c.M(0x6a4a2a, { r: .85 }), 0, .09, .01, { s: [1, 1, .72] }); belt(c, dleather, gold); strapX(c, leather, gold);
  skirt(c, { col: 0xefe6d0, trim: 0xd2a43c, len: .9, top: .16, bot: .38, y: -.06, ragged: .02, segs: 16 }); skirt(c, { col: green, trim: 0xd2a43c, len: .75, top: .17, bot: .4, y: -.02, zs: .85, ragged: .06, segs: 16 });
  tabard(c, { w: .2, len: .6, col: 0xefe6d0, trim: gold, emblem: 'sprig', point: .07, z: .21, y: -.04 });
  for (const S of ['L', 'R']) bell(c, S, 0xefe6d0, 0xd2a43c, .34, .14);
  hair(c, 'wavy', 0x9a5a30, { len: .85 });
  const cp = cape(c, { topW: .62, botW: 1.2, len: 1.0, col: green, trim: 0xd2a43c, lining: 0x244a2c, waves: 8, ragged: .05, segs: 18, seed: 9, wrap: .14 }); cp.len = 1.0; backEmblem(c, cp, 'sprig', .55, gold, .5);
  for (let r = 0; r < 3; r++) K.leafCluster(c, c.bones.chest, 12 - r, .2 + r * .035, leaf, .26 - r * .05, -.01);
  for (const k of [-1, 1]) for (let r = 0; r < 2; r++) K.leafCluster(c, c.bones['shoulder_' + (k > 0 ? 'L' : 'R')], 7, .09 + r * .03, leaf, .03 - r * .05, 0);
  const wood = c.M(0x6a4528, { r: .9 }); for (const k of [-1, 1]) { c.add(c.bones.head, c.G.cyl(.01, .016, .2, 5), wood, k * .06, .3, -.02, { r: [0, 0, -k * .5] }); c.add(c.bones.head, c.G.cyl(.008, .012, .1, 5), wood, k * .14, .38, -.02, { r: [0, 0, k * .1] }); c.add(c.bones.head, c.G.cyl(.007, .01, .08, 5), wood, k * .11, .34, -.02, { r: [0, 0, -k * 1.0] }); }
  K.leafCluster(c, c.bones.head, 8, .115, leaf, .2, 0); for (let i = 0; i < 5; i++) c.add(c.bones.head, c.G.sph(.017, 5, 4), c.M(0xf8f4e8), Math.sin(i * 1.3) * .11, .2 + (i % 2) * .02, Math.cos(i * 1.3) * .1 + .0);
  K.pouch(c, c.bones.hips, 0x6a4a2a, .2, -.06, .03, 1.1, gold); for (let i = 0; i < 3; i++) { const v = K.vial(c, gold, 0x7dff6a); v.position.set(-.15 + i * .045, -.05, .15); c.bones.hips.add(v); }
  const st = K.staff(c, 'leaf', { gold, wood, len: 1.9, twist: true, wood2: 0x5a8a3a }); hold(c, h.hips, 'hand_R', st.g, 0, -.05, 0, .3);
  const orb = c.M(0x74ff62, { e: 0x74ff62, ei: 1.6, n: 'magic' }); c.add(c.bones.hand_L, c.G.sph(.045, 8, 6), orb, 0, -.15, .06); c.add(c.bones.hand_L, c.G.sph(.075, 8, 6), c.M(0x74ff62, { e: 0x74ff62, ei: .5, a: .25 }), 0, -.15, .06);
  for (let i = 0; i < 3; i++) c.add(c.bones.hand_L, c.G.tor(.08 + i * .02, .008, 4, 14), orb, 0, -.15 + i * .03, .06, { r: [PI / 2 + i * .5, i, 0] });
  return finalize(c, h.root, { R: 1 }, B => { B.upperArm_L.rotation.set(-.3, 0, .35); B.foreArm_L.rotation.set(-.9, 0, 0); }); } };

CHARS.nyx = { name: 'Nyx Varrin', sheetKey: 'x7', build() {
  const c = makeCtx({ name: 'Nyx_Varrin', fem: true, nobust: true, bulk: .86, sw: .92, skin: 0xe8bc9c, hair: 0x14100e, under: 0x2a2522, pants: 0x24201e, sleeve: 0x2f2a28, glove: 0x1e1a18, boot: 0x3a2a20 });
  const h = humanoid(c), { gold, leather, dleather } = pal(c), blk = c.M(0x3a302a, { r: .75, n: 'blackleather' }), aged = c.M(0xa8863c, { m: .4, r: .5, n: 'agedgold' }), crim = 0xa01e2e;
  platePack(c, { steel: blk, trim: aged, cuisse: false, tassets: false, noGaunt: true }); belt(c, dleather, aged); strapX(c, leather, aged);
  c.add(c.bones.chest, c.G.tor(.1, .035, 5, 12), c.M(crim, { r: .95 }), 0, .26, 0, { r: [PI / 2 - .25, 0, 0] });
  tabard(c, { w: .3, len: .5, col: crim, trim: aged, point: .1, z: .17, y: -.02 }); skirt(c, { col: 0x2a2522, trim: 0x2a2522, len: .4, top: .16, bot: .28, y: -.05, zs: .85, ragged: .1, segs: 16 });
  const cp = cape(c, { topW: .5, botW: 1.15, len: 1.05, col: 0x2c2a2e, trim: crim, lining: crim, ragged: .22, segs: 20, seed: 21, waves: 11, wrap: .12 }); cp.len = 1.05;
  hood(c, c.M(0x2c2a2e, { r: .95, d: 1, n: 'hood' }), 1.0); hair(c, 'short', 0x14100e);
  c.add(c.bones.chest, c.G.cyl(.035, .035, .015, 8), aged, .1, .23, .13, { r: [PI / 2, 0, 0] }); emblem(c, c.bones.chest, 'lion', .05, aged, .1, .23, .14);
  K.pouch(c, c.bones.hips, 0x4a3020, .19, -.06, .02, 1.1, aged); c.add(c.bones.hips, c.G.tor(.022, .006, 4, 8), aged, -.17, -.05, .08, { r: [0, PI / 2, 0] });
  for (let i = 0; i < 3; i++) c.add(c.bones.hips, c.G.cone(.012, .13, 4), c.M(0xaeb6bd, { m: .4, r: .35 }), -.1 + i * .03, -.12, .165, { r: [PI, 0, 0], s: [1, 1, .4] });
  for (const S of ['L', 'R']) { const d = K.dagger(c, aged); hold(c, c.bones.hips, 'hand_' + S, d, 0, -.05, 0, 2.3); }
  return finalize(c, h.root, { L: 1, R: 1 }); } };

CHARS.vesper = { name: 'Vesper Crowe', sheetKey: 'x8', build() {
  const c = makeCtx({ name: 'Vesper_Crowe', fem: true, nobust: true, bulk: .96, sw: 1.0, skin: 0xe2b18c, hair: 0x4a2c1e, under: 0x24201e, pants: 0x2a2220, sleeve: 0x2c2420, glove: 0x2a1c14, boot: 0x3a2618 });
  const h = humanoid(c), { steel, gold, leather, dleather } = pal(c), crim = 0xa3182a, dsteel = c.M(0x6a5a4a, { m: .4, r: .45, n: 'oldsteel' });
  platePack(c, { steel: dsteel, trim: gold, bigPauld: true, cuisse: false, tassets: false, cuirass: c.M(0x3a2c22, { r: .7 }) }); belt(c, dleather, gold); strapX(c, dleather, gold);
  tabard(c, { w: .24, len: .66, col: 0xf1ead8, trim: gold, emblem: 'ornate', point: .08, z: .19, y: -.04 }); skirt(c, { col: 0x222024, trim: 0x222024, len: .55, top: .16, bot: .32, y: -.05, zs: .85, ragged: .08, segs: 16 });
  const cp = cape(c, { topW: .58, botW: 1.15, len: 1.05, col: crim, trim: gold.color.getHex(), lining: 0x7a1020, ragged: .13, segs: 18, seed: 31, waves: 9 }); cp.len = 1.05; backEmblem(c, cp, 'ornate', .5, gold, .42);
  c.add(c.bones.neck, c.G.cyl(.15, .2, .14, 8, true), c.M(crim, { r: .95, d: 1 }), 0, -.03, -.02, { s: [1, 1, 1.05] });
  hair(c, 'curly', 0x4a2c1e);
  const cb = K.crossbow(c, { metal: dsteel, gold, banner: crim, wood: 0x3a2618 }); hold(c, h.hips, 'hand_R', cb, 0, -.04, -.02, .3, -.1, 0); cb.scale.setScalar(.7);
  const sw = K.sword(c, { gold, len: .75, gem: 0xe0262e }); sw.position.set(.2, -.12, .02); sw.rotation.set(2.9, 0, .5); c.bones.hips.add(sw); void 0;
  const lan = K.lantern(c, gold); lan.position.set(-.2, -.12, .05); c.bones.hips.add(lan); chain(c, c.bones.hips, gold, -.2, -.07, .05, 2, -.025);
  for (let i = 0; i < 3; i++) { const v = K.vial(c, gold); v.position.set(-.1 + i * .05, -.02, .17); c.bones.hips.add(v); }
  const bk = K.book(c, 0x3a2418, gold, .13, .17); bk.position.set(.02, -.05, -.2); c.bones.hips.add(bk); emblem(c, bk, 'cross', .1, gold, 0, 0, .03);
  return finalize(c, h.root, { R: 1 }, B => { B.upperArm_R.rotation.set(-.35, 0, -.1); B.foreArm_R.rotation.set(-.8, 0, 0); }); } };

CHARS.thorne = { name: 'Brother Thorne', sheetKey: 'x9', build() {
  const c = makeCtx({ name: 'Brother_Thorne', bulk: 1.06, sw: 1.0, skin: 0xe0b894, hair: 0xc8c8cc, under: 0xefe8d8, pants: 0xefe8d8, sleeve: 0xefe8d8, glove: 0xe0b894, boot: 0x5a3a22 });
  const h = humanoid(c), { gold, leather, dleather } = pal(c), blue = 0x1d3a8a, cream = 0xefe8d8;
  belt(c, dleather, gold);
  skirt(c, { col: cream, trim: 0xd2a43c, len: .9, top: .17, bot: .4, y: -.04, segs: 16 });
  tabard(c, { w: .26, len: .78, col: blue, trim: gold, emblem: 'cross', emblem2: 'fleur', point: .07, z: .22, y: .02 });
  const bk = tabard(c, { w: .26, len: .78, col: blue, trim: gold, emblem: 'ornate', point: .07, z: -.22, y: .02 }); bk.rotation.set(.06, PI, 0);
  for (const S of ['L', 'R']) bell(c, S, cream, 0xd2a43c, .36, .15);
  const cp = cape(c, { topW: .62, botW: .95, len: .7, col: cream, trim: gold.color.getHex(), lining: 0xe0d8c4, waves: 8, back: .17, wrap: .12 }); cp.len = .7;
  c.add(c.bones.chest, c.G.tor(.2, .07, 6, 12), c.M(cream, { r: 1 }), 0, .24, -.04, { r: [PI / 2 - .3, 0, 0], s: [1, 1.05, 1] });
  for (const k of [-1, 1]) c.add(c.bones.chest, c.G.cyl(.03, .03, .015, 8), gold, k * .1, .24, .12, { r: [PI / 2, 0, 0] }); chain(c, c.bones.chest, gold, 0, .22, .13, 3, -.03);
  hair(c, 'short', 0xc8c8cc); c.add(c.bones.head, c.G.sph(.06, 7, 5), c.M(0xc8c8cc, { r: .95 }), 0, -.015, .06, { s: [1.1, .8, .7] }); c.add(c.bones.head, c.G.cone(.05, .09, 5), c.M(0xc8c8cc), 0, -.07, .08, { r: [PI + .2, 0, 0] });
  const ce = K.censer(c, gold); ce.position.set(-.16, -.0, .1); c.bones.hips.add(ce); K.pouch(c, c.bones.hips, 0x5a3720, .19, -.04, .03, 1.0, gold);
  const st = K.staff(c, 'star', { gold, wood: c.M(0x4a2f1a, { r: .8 }), len: 1.9 }); st.top.add(...[-1, 1].map(k => { const g = new THREE.Group(); c.add(g, c.G.box(.04, .3, .008), c.M(blue, { d: 1 }), 0, -.15, 0); c.add(g, c.G.box(.045, .02, .01), gold, 0, -.3, 0); g.position.set(k * .03, -.05, 0); g.rotation.z = k * .15; return g; }));
  hold(c, h.hips, 'hand_R', st.g, 0, -.05, 0, .3);
  const book = K.book(c, blue, gold, .17, .23); emblem(c, book, 'cross', .14, gold, 0, 0, .03); book.position.set(0, -.12, .06); book.rotation.set(-.3, 0, 0); c.bones.hand_L.add(book);
  return finalize(c, h.root, { R: 1, L: 1 }, B => { B.upperArm_L.rotation.set(-.5, 0, .15); B.foreArm_L.rotation.set(-1.2, 0, 0); }); } };

CHARS.orin = { name: 'Orin Ashlance', sheetKey: 'orin', build() {
  const c = makeCtx({ name: 'Orin_Ashlance', bulk: 1.12, sw: 1.06, skin: 0xe2b48c, hair: 0x6a4025, under: 0x4a4e56, pants: 0x4a4e56, sleeve: 0x7a808a, glove: 0x5a3720, boot: 0x5a5e66 });
  const h = humanoid(c), { steel, gold, leather, dleather } = pal(c), blue = 0x1f3f95, cream = 0xefe3c4, mail = c.M(0x6b7078, { m: .6, r: .55, n: 'chainmail' });
  platePack(c, { steel, trim: gold, bigPauld: true }); hair(c, 'messy', 0x6a4025); belt(c, leather, gold);
  skirt(c, { col: 0x6b7078, trim: 0x8a9098, len: .3, top: .15, bot: .24, y: -.06, zs: .8 });
  tabard(c, { w: .32, len: .62, col: blue, trim: gold, point: .06, z: .172 });
  const cr = tabard(c, { w: .17, len: .56, col: cream, trim: blue, emblem: 'lion', emblem2: 'fleur', point: .05, z: .186 });
  const cp = cape(c, { topW: .56, botW: 1.1, len: 1.05, col: blue, trim: gold.color.getHex(), lining: 0x182f72, waves: 8 }); cp.len = 1.05;
  backEmblem(c, cp, 'lion', .55, gold, .42); for (const k of [-1, 1]) emblem(c, cp.cb, 'fleur', .13, gold, k * .27, -.9, cp.z(.9) - .026, PI);
  // sword at belt (left hip), sheathed
  const sg = new THREE.Group(); c.add(sg, c.G.box(.045, .8, .02), dleather, 0, -.4, 0); c.add(sg, c.G.box(.05, .04, .026), gold, 0, -.02, 0); c.add(sg, c.G.box(.05, .05, .026), gold, 0, -.8, 0);
  c.add(sg, c.G.cyl(.016, .016, .13, 6), c.M(0x4a2b18), 0, .08, 0); c.add(sg, c.G.box(.2, .028, .03), gold, 0, .02, 0); c.add(sg, c.G.sph(.024, 6, 5), gold, 0, .16, 0);
  sg.position.set(-.21, -.04, .02); sg.rotation.set(-.12, 0, .12); c.bones.hips.add(sg);
  // spear: shaft, steel head, gold collar, lion banner, tassels
  const sp = new THREE.Group(), wood = c.M(0x6b4528, { r: .7, n: 'wood' });
  c.add(sp, c.G.cyl(.02, .024, 1.95, 6), wood, 0, .33, 0); c.add(sp, c.G.cone(.02, .08, 5), gold, 0, -.69, 0, { r: [PI, 0, 0] });
  const hd = new THREE.Shape(); hd.moveTo(0, 0); hd.lineTo(.05, .1); hd.lineTo(0, .3); hd.lineTo(-.05, .1); hd.closePath();
  const hg = new THREE.ExtrudeGeometry(hd, { depth: .014, bevelEnabled: false }); hg.translate(0, 0, -.007); c.add(sp, hg, c.M(0xd5dae0, { m: .8, r: .3, n: 'spearhead' }), 0, 1.33, 0);
  c.add(sp, c.G.cyl(.032, .032, .05, 6), gold, 0, 1.3, 0); c.add(sp, c.G.cyl(.026, .026, .04, 6), gold, 0, .9, 0);
  const bn = new THREE.Group(); bn.position.set(0, 1.24, 0); sp.add(bn);
  c.add(bn, c.G.cyl(.01, .01, .3, 4), gold, .14, 0, 0, { r: [0, 0, PI / 2] });
  const bs = new THREE.Shape(); bs.moveTo(0, 0); bs.lineTo(.28, 0); bs.lineTo(.28, -.62); bs.lineTo(.14, -.54); bs.lineTo(0, -.62); bs.closePath();
  const bg = new THREE.ExtrudeGeometry(bs, { depth: .01, bevelEnabled: false }); c.add(bn, bg, c.M(blue, { r: .9, d: 1, n: 'banner' }), 0, -.01, -.005);
  c.add(bn, c.G.box(.28, .02, .014), gold, .14, -.015, 0); c.add(bn, c.G.box(.22, .2, .012), c.M(cream, { r: .9, d: 1 }), .14, -.14, 0, {});
  emblem(c, bn, 'lion', .2, c.M(blue, { r: .6 }), .14, -.15, .01, 0); emblem(c, bn, 'lion', .2, c.M(blue, { r: .6 }), .14, -.15, -.01, PI);
  emblem(c, bn, 'fleur', .1, gold, .14, -.38, .008, 0); emblem(c, bn, 'fleur', .1, gold, .14, -.38, -.008, PI);
  for (const x of [.02, .14, .26]) { c.add(bn, c.G.cyl(.012, .012, .1, 5), gold, x, -.62 - (x == .14 ? -.02 : 0), 0, {}); c.add(bn, c.G.cone(.025, .12, 6), c.M(0xd2a43c, { m: .3, r: .6, d: 1 }), x, -.7, 0, { r: [PI, 0, 0] }); }
  hold(c, h.hips, 'hand_R', sp, 0, -.05, .0, .3, 0, .13);
  for (const k of [-1, 1]) K.pouch(c, c.bones.hips, 0x5a3720, k * .17, -.06, -.04, .7, gold);
  return finalize(c, h.root, { R: 1 }); } };
export const ORDER = ['aldric', 'darius', 'selene', 'seraphine', 'talia', 'finn', 'brynn', 'mirelle', 'nyx', 'vesper', 'thorne', 'orin'];
