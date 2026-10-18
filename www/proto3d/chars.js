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
const backEmblem = (c, cp, type, size, mat, f = .4) => cp.decal(type, size, mat, f);
const chain = (c, par, mat, x0, y0, z0, n, dy = -.04, r = .012) => { for (let i = 0; i < n; i++) c.add(par, c.G.tor(r * 1.4, r * .5, 4, 6), mat, x0, y0 + dy * i, z0, { r: [0, i % 2 ? PI / 2 : 0, 0] }); };
export const CHARS = {};

CHARS.aldric = { name: 'Sir Aldric', sheetKey: 'aldric', build() {
  const c = makeCtx({ name: 'Sir_Aldric', eye: 0x4a78b8, bulk: 1.1, sw: 1.06, skin: 0xe6b890, hair: 0xd9b36a, under: 0x2b2b30, pants: 0x2a2a30, sleeve: 0x4a4a52, glove: 0x2a2a2e, boot: 0x6b6b72 });
  const h = humanoid(c), { steel, gold, leather } = pal(c), blue = c.M(0x1f3f95, { r: .95, n: 'blue' });
  platePack(c, { steel, trim: gold, bigPauld: true }); hair(c, 'swept', 0xd9b36a); belt(c, leather, gold); strapX(c, leather, gold);
  tabard(c, { w: .27, len: .52, col: 0x1f3f95, trim: gold, emblem: 'lion', emblem2: 'fleur', point: .07, z: .165 });
  const cp = cape(c, { topW: .52, botW: 1.05, len: .98, col: 0x1f3f95, trim: gold.color.getHex(), lining: 0x182f72, waves: 8 }); cp.len = .98;
  backEmblem(c, cp, 'lion', .5, gold, .4); for (const k of [-1, 0, 1]) cp.decal('fleur', .13, gold, .86 / cp.len, k * .26);
  const sw = K.sword(c, { gold, blade: 0xcfd6dd, len: .85 }); hold(c, h.hips, 'hand_R', sw, 0, -.05, 0, 2.3);
  const sh = K.kiteShield(c, { rim: gold, face: blue, emblem: 'lion' }); sh.scale.setScalar(1.1); hold(c, h.hips, 'foreArm_L', sh, .1, -.1, .07, .3, .3, 0);
  for (const k of [-1, 1]) K.pouch(c, c.bones.hips, 0x5a3720, k * .16, -.05, -.02, .8, gold);
  return finalize(c, h.root, { L: 1, R: 1 }); } };

CHARS.darius = { name: 'Darius Umbral', sheetKey: 'darius', build() {
  const c = makeCtx({ name: 'Darius_Umbral', eye: 0x5a3a2a, brow: 1.5, scar: true, bulk: 1.2, sw: 1.15, skin: 0xd9ab88, hair: 0x2a1c14, under: 0x1e1c24, pants: 0x1e1c22, sleeve: 0x2c2c34, glove: 0x202024, boot: 0x2c2c32 });
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
  const c = makeCtx({ name: 'Selene_Frostveil', eye: 0x7ab8e8, fem: true, nobust: true, bulk: .92, sw: .98, skin: 0xf0c8a8, hair: 0xe6cf9c, under: 0xe9e3d3, pants: 0x2a3f78, sleeve: 0x2b4fa8, glove: 0x23232a, boot: 0xc4c8d2 });
  const h = humanoid(c), { steel, gold, leather } = pal(c), cream = c.M(0xf2eee4, { r: 1, n: 'fur' });
  c.add(c.bones.chest, c.G.cyl(.17, .12, .22, 8), steel, 0, .1, .005, { s: [1, 1, .72] }); belt(c, leather, gold);
  c.add(c.bones.chest, c.G.box(.09, .09, .02), c.M(0x6ec8ff, { e: 0x3a9cff, ei: .7 }), 0, .2, .105, { r: [0, 0, PI / 4] });
  furCollar(c, cream, .21, .09);
  skirt(c, { col: 0x2b4fa8, trim: 0xf2eee4, len: .52, top: .17, bot: .3, y: -.04 }); skirt(c, { col: 0xf2eee4, trim: 0xd2a43c, len: .62, top: .15, bot: .26, y: -.06, zs: .8 });
  tabard(c, { w: .2, len: .45, col: 0xf2eee4, trim: gold, emblem: 'snow', point: .08, z: .2, tilt: -.02, y: -.06 });
  for (const S of ['L', 'R']) bell(c, S, 0x2b4fa8, 0xf2eee4, .34, .13);
  hair(c, 'wavy', 0xe6cf9c, { len: .75 }); c.add(c.bones.head, c.G.oct(.03), c.M(0x6ec8ff, { e: 0x3a9cff, ei: .9 }), 0, .26, .09, { s: [.7, 1.8, .7] });
  const cp = cape(c, { topW: .6, botW: 1.2, len: 1.05, col: 0x2b4fa8, trim: 0xf2eee4, lining: 0xf2eee4, waves: 7, wrap: .15 }); cp.len = 1.05;
  backEmblem(c, cp, 'snow', .6, c.M(0xdbe9ff, { r: .5 }), .55); for (const k of [-1, 1]) cp.decal('snow', .16, c.M(0xdbe9ff, { r: .5 }), .92 / cp.len, k * .3);
  const st = K.staff(c, 'crystal', { gold, wood: c.M(0x6b5a3a, { r: .6, m: .4 }), len: 1.85 }); hold(c, h.hips, 'hand_R', st.g, 0, -.05, 0, .3);
  const bk = K.book(c, 0x24409a, gold, .15, .2); bk.position.set(.22, -.12, .04); bk.rotation.set(0, PI / 2, .1); c.bones.hips.add(bk); emblem(c, bk, 'snow', .12, gold, 0, 0, .03);
  for (let i = 0; i < 4; i++) c.add(c.bones.hips, c.G.oct(.02), c.M(0x6ec8ff, { e: 0x3a9cff, ei: .8 }), -.1 + i * .06, -.07 - i % 2 * .04, .17, { s: [.7, 1.8, .7] });
  return finalize(c, h.root, { R: 1 }); } };

CHARS.seraphine = { name: 'Dame Seraphine', sheetKey: 'x0', build() {
  const c = makeCtx({ name: 'Dame_Seraphine', eye: 0x6a9ac8, fem: true, nobust: true, bulk: 1.0, sw: 1.0, skin: 0xf0c8a4, hair: 0xe0a850, under: 0x2b2b30, pants: 0x2a2a30, sleeve: 0x4a4a52, glove: 0x2a2a2e, boot: 0x6b6b72 });
  const h = humanoid(c), { steel, gold, leather } = pal(c), blue = c.M(0x2a3f8a, { r: .9, n: 'blue' });
  platePack(c, { steel, trim: gold, tassets: false }); hair(c, 'wavy', 0xe0a850, { len: .8 }); belt(c, leather, gold);
  c.add(c.bones.head, c.G.tor(.115, .014, 4, 14), gold, 0, .18, 0, { r: [PI / 2 - .15, 0, 0] }); for (const k of [-1, 1]) c.add(c.bones.head, c.G.tor(.03, .012, 4, 8), c.M(0xe0a850), k * .09, .08, -.03, { s: [1, 1.6, 1] });
  tabard(c, { w: .28, len: .62, col: 0xf1ead8, trim: gold, emblem: 'sun', emblem2: 'fleur', point: .07, z: .17 });
  skirt(c, { col: 0x2a3f8a, trim: gold, len: .42, top: .16, bot: .27, y: -.06, zs: .85 });
  const cp = cape(c, { topW: .55, botW: 1.1, len: 1.0, col: 0xf1ead8, trim: gold.color.getHex(), lining: 0x2a3f8a, waves: 8 }); cp.len = 1.0;
  backEmblem(c, cp, 'sun', .55, gold, .42); for (const k of [-1, 1]) cp.decal('fleur', .13, gold, .88 / cp.len, k * .28);
  const mc = K.mace(c, { gold }); hold(c, h.hips, 'hand_R', mc, 0, -.05, 0, .3);
  const sh = K.kiteShield(c, { rim: gold, face: blue, emblem: 'sun' }); sh.scale.setScalar(1.05); hold(c, h.hips, 'foreArm_L', sh, .1, -.1, .07, .3, .3, 0);
  K.pouch(c, c.bones.hips, 0x5a3720, .16, -.05, -.02, .8, gold);
  return finalize(c, h.root, { L: 1, R: 1 }); } };

CHARS.talia = { name: 'Talia Stormcall', sheetKey: 'x1', build() {
  const c = makeCtx({ name: 'Talia_Stormcall', eye: 0x5a3a22, fem: true, nobust: true, bulk: .95, sw: 1.0, skin: 0xb98560, hair: 0x3a2418, under: 0x1f6f7a, pants: 0x3a2a20, sleeve: 0x1f6f7a, glove: 0x4a3020, boot: 0x4a3322 });
  const h = humanoid(c), { gold, leather, dleather } = pal(c), fur = c.M(0xf0e6d0, { r: 1, n: 'fur' }), teal = 0x1f6f7a, bronze = c.M(0xb08a4a, { m: .4, r: .45, n: 'bronze' });
  c.add(c.bones.chest, c.G.cyl(.17, .12, .24, 8), dleather, 0, .09, .01, { s: [1, 1, .72] }); belt(c, dleather, bronze); strapX(c, leather, bronze);
  furCollar(c, fur, .24, .1); furCollar(c, c.M(0x2c8a96), .26, .045);
  skirt(c, { col: 0xe9dfc8, trim: teal, len: .78, top: .17, bot: .38, y: -.04, ragged: .04 }); skirt(c, { col: teal, trim: 0xf0e6d0, len: .55, top: .15, bot: .25, y: -.03, zs: .85, ragged: .05, segs: 16 });
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
  const c = makeCtx({ name: 'Finn_Valecourt', eye: 0x5a4028, brow: .5, bulk: .86, sw: .96, skin: 0xe8b890, hair: 0x6a3f24, under: 0x1f3a8a, pants: 0x4a3020, sleeve: 0xe8e0cc, glove: 0x3a2618, boot: 0x3a2618 });
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
  c.add(cp.cb, c.G.box(.34, .55, .01), blue, 0, -.4, cp.z(.4) - .02); cp.decal('fleur', .4, gold, .42 / cp.len, 0);
  c.add(c.bones.chest, c.G.tor(.05, .01, 4, 10), gold, 0, .24, -.1); for (const k of [-1, 1]) c.add(c.bones.chest, c.G.tor(.07, .01, 4, 10), gold, k * .1, .26, -.08, { r: [.4, 0, 0] });
  const rp = K.rapier(c, gold, 1.0); hold(c, h.hips, 'hand_R', rp, 0, -.05, 0, 2.3);
  return finalize(c, h.root, { R: 1 }, B => { B.upperArm_R.rotation.set(-.2, 0, -.2); B.foreArm_R.rotation.set(-.6, 0, 0); }); } };

CHARS.brynn = { name: 'Brynn Cogwright', sheetKey: 'x3', build() {
  const c = makeCtx({ name: 'Brynn_Cogwright', eye: 0x4a7a9a, fem: true, nobust: true, bulk: .96, sw: .98, skin: 0xf0c4a0, hair: 0xc9622b, under: 0xe8dcc0, pants: 0x3a3028, sleeve: 0xe8dcc0, glove: 0x4a3020, boot: 0x5a3a22 });
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
  const c = makeCtx({ name: 'Mirelle_Thornroot', fem: true, elf: true, eye: 0x4a9a58, nobust: true, bulk: .94, sw: .98, skin: 0xf0c8a8, hair: 0x9a5a30, under: 0xefe6d0, pants: 0x4a3626, sleeve: 0xefe6d0, glove: 0x4a3020, boot: 0x5a3a22 });
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
  const c = makeCtx({ name: 'Nyx_Varrin', eye: 0x3a2a22, brow: 1, fem: true, nobust: true, bulk: .86, sw: .92, skin: 0xe8bc9c, hair: 0x14100e, under: 0x2a2522, pants: 0x24201e, sleeve: 0x2f2a28, glove: 0x1e1a18, boot: 0x3a2a20 });
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
  const c = makeCtx({ name: 'Vesper_Crowe', eye: 0x5a3a2a, brow: .8, fem: true, nobust: true, bulk: .96, sw: 1.0, skin: 0xe2b18c, hair: 0x4a2c1e, under: 0x24201e, pants: 0x2a2220, sleeve: 0x2c2420, glove: 0x2a1c14, boot: 0x3a2618 });
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
  const bk = K.book(c, 0x3a2418, gold, .13, .17); bk.position.set(.02, -.05, -.145); c.bones.hips.add(bk); emblem(c, bk, 'cross', .1, gold, 0, 0, .03);
  return finalize(c, h.root, { R: 1 }, B => { B.upperArm_R.rotation.set(-.35, 0, -.1); B.foreArm_R.rotation.set(-.8, 0, 0); }); } };

CHARS.thorne = { name: 'Brother Thorne', sheetKey: 'x9', build() {
  const c = makeCtx({ name: 'Brother_Thorne', eye: 0x6a8ab0, beard: 0xc8c8cc, bulk: 1.06, sw: 1.0, skin: 0xe0b894, hair: 0xc8c8cc, under: 0xefe8d8, pants: 0xefe8d8, sleeve: 0xefe8d8, glove: 0xe0b894, boot: 0x5a3a22 });
  const h = humanoid(c), { gold, leather, dleather } = pal(c), blue = 0x1d3a8a, cream = 0xefe8d8;
  belt(c, dleather, gold);
  skirt(c, { col: cream, trim: 0xd2a43c, len: .9, top: .17, bot: .4, y: -.04, segs: 16 });
  tabard(c, { w: .26, len: .78, col: blue, trim: gold, emblem: 'cross', emblem2: 'fleur', point: .07, z: .22, y: .02 });
  const bk = tabard(c, { w: .26, len: .78, col: blue, trim: gold, emblem: 'ornate', point: .07, z: -.22, y: .02 }); bk.rotation.set(.06, PI, 0);
  for (const S of ['L', 'R']) bell(c, S, cream, 0xd2a43c, .36, .15);
  const cp = cape(c, { topW: .62, botW: .95, len: .7, col: cream, trim: gold.color.getHex(), lining: 0xe0d8c4, waves: 8, back: .17, wrap: .12 }); cp.len = .7;
  c.add(c.bones.chest, c.G.tor(.17, .05, 6, 12), c.M(cream, { r: 1 }), 0, .22, -.04, { r: [PI / 2 - .3, 0, 0], s: [1, 1.05, 1] });
  for (const k of [-1, 1]) c.add(c.bones.chest, c.G.cyl(.03, .03, .015, 8), gold, k * .1, .24, .12, { r: [PI / 2, 0, 0] }); chain(c, c.bones.chest, gold, 0, .22, .13, 3, -.03);
  hair(c, 'short', 0xc8c8cc); c.add(c.bones.head, c.G.sph(.06, 7, 5), c.M(0xc8c8cc, { r: .95 }), 0, -.015, .06, { s: [1.1, .8, .7] }); c.add(c.bones.head, c.G.cone(.05, .09, 5), c.M(0xc8c8cc), 0, -.07, .08, { r: [PI + .2, 0, 0] });
  const ce = K.censer(c, gold); ce.position.set(-.16, -.0, .1); c.bones.hips.add(ce); K.pouch(c, c.bones.hips, 0x5a3720, .19, -.04, .03, 1.0, gold);
  const st = K.staff(c, 'star', { gold, wood: c.M(0x4a2f1a, { r: .8 }), len: 1.9 }); st.top.add(...[-1, 1].map(k => { const g = new THREE.Group(); c.add(g, c.G.box(.04, .3, .008), c.M(blue, { d: 1 }), 0, -.15, 0); c.add(g, c.G.box(.045, .02, .01), gold, 0, -.3, 0); g.position.set(k * .03, -.05, 0); g.rotation.z = k * .15; return g; }));
  hold(c, h.hips, 'hand_R', st.g, 0, -.05, 0, .3);
  const book = K.book(c, blue, gold, .17, .23); emblem(c, book, 'cross', .14, gold, 0, 0, .03); book.position.set(0, -.12, .06); book.rotation.set(-.3, 0, 0); c.bones.hand_L.add(book);
  return finalize(c, h.root, { R: 1, L: 1 }, B => { B.upperArm_L.rotation.set(-.5, 0, .15); B.foreArm_L.rotation.set(-1.2, 0, 0); }); } };

CHARS.orin = { name: 'Orin Ashlance', sheetKey: 'orin2', build() {
  const c = makeCtx({ name: 'Orin_Ashlance', eye: 0x5a4028, brow: .4, bulk: 1.12, sw: 1.06, skin: 0xe2b48c, hair: 0x6a4025, under: 0x4a4e56, pants: 0x4a4e56, sleeve: 0x7a808a, glove: 0x5a3720, boot: 0x5a5e66 });
  const h = humanoid(c), { steel, gold, leather, dleather } = pal(c), blue = 0x1f3f95, cream = 0xefe3c4, mail = c.M(0x6b7078, { m: .6, r: .55, n: 'chainmail' });
  platePack(c, { steel, trim: gold, bigPauld: true }); hair(c, 'messy', 0x6a4025); belt(c, leather, gold);
  skirt(c, { col: 0x6b7078, trim: 0x8a9098, len: .3, top: .15, bot: .24, y: -.06, zs: .8 });
  tabard(c, { w: .32, len: .62, col: blue, trim: gold, point: .06, z: .172 });
  const cr = tabard(c, { w: .17, len: .56, col: cream, trim: blue, emblem: 'lion', emblem2: 'fleur', point: .05, z: .186 });
  const cp = cape(c, { topW: .56, botW: 1.1, len: 1.05, col: blue, trim: gold.color.getHex(), lining: 0x182f72, waves: 8 }); cp.len = 1.05;
  backEmblem(c, cp, 'lion', .55, gold, .42); for (const k of [-1, 1]) cp.decal('fleur', .13, gold, .9 / cp.len, k * .27);
  // sword at belt (left hip), sheathed
  const sg = new THREE.Group(); c.add(sg, c.G.box(.045, .8, .02), dleather, 0, -.4, 0); c.add(sg, c.G.box(.05, .04, .026), gold, 0, -.02, 0); c.add(sg, c.G.box(.05, .05, .026), gold, 0, -.8, 0);
  c.add(sg, c.G.cyl(.016, .016, .13, 6), c.M(0x4a2b18), 0, .08, 0); c.add(sg, c.G.box(.2, .028, .03), gold, 0, .02, 0); c.add(sg, c.G.sph(.024, 6, 5), gold, 0, .16, 0);
  sg.position.set(-.21, -.04, .02); sg.rotation.set(-.12, 0, .12); c.bones.hips.add(sg);
  // spear (corrected sheet): ringed shaft, leaf head, gold collar, long cream/blue lion banner with fleur border + tassels
  const sp = new THREE.Group(), wood = c.M(0x6b4528, { r: .7, n: 'wood' }), steelH = c.M(0xd5dae0, { m: .8, r: .3, n: 'spearhead' });
  c.add(sp, c.G.cyl(.02, .024, 1.9, 6), wood, 0, .1, 0); c.add(sp, c.G.cone(.022, .09, 5), gold, 0, -.89, 0, { r: [PI, 0, 0] });
  for (const y of [-.7, -.4, -.1, .2, .5, .8]) c.add(sp, c.G.cyl(.028, .028, .025, 6), gold, 0, y, 0);
  const hd = new THREE.Shape(); hd.moveTo(0, 0); hd.quadraticCurveTo(.07, .1, .0, .3); hd.quadraticCurveTo(-.07, .1, 0, 0);
  const hg = new THREE.ExtrudeGeometry(hd, { depth: .016, bevelEnabled: false, curveSegments: 6 }); hg.translate(0, 0, -.008); c.add(sp, hg, steelH, 0, 1.08, 0);
  c.add(sp, c.G.cyl(.036, .028, .06, 6), gold, 0, 1.05, 0); c.add(sp, c.G.sph(.032, 6, 5), gold, 0, 1.08, 0);
  const bn = new THREE.Group(); bn.position.set(0, .98, 0); bn.rotation.y = PI; sp.add(bn);
  c.add(bn, c.G.cyl(.01, .01, .3, 4), gold, .15, 0, 0, { r: [0, 0, PI / 2] }); c.add(bn, c.G.sph(.016, 5, 4), gold, .3, 0, 0);
  const bs = new THREE.Shape(); bs.moveTo(0, 0); bs.lineTo(.3, 0); bs.lineTo(.3, -.82); bs.lineTo(.15, -.72); bs.lineTo(0, -.82); bs.closePath();
  const bg = new THREE.ExtrudeGeometry(bs, { depth: .008, bevelEnabled: false }); bg.translate(0, -.012, -.004); c.add(bn, bg, c.M(blue, { r: .9, d: 1, n: 'banner' }));
  const cs = new THREE.Shape(); cs.moveTo(.035, 0); cs.lineTo(.265, 0); cs.lineTo(.265, -.74); cs.lineTo(.15, -.65); cs.lineTo(.035, -.74); cs.closePath();
  const cg = new THREE.ExtrudeGeometry(cs, { depth: .008, bevelEnabled: false }); cg.translate(0, -.012, 0); c.add(bn, cg, c.M(cream, { r: .9, d: 1, n: 'bannercream' }), 0, 0, .004); c.add(bn, cg, c.M(cream, { r: .9, d: 1, n: 'bannercream' }), 0, 0, -.012);
  c.add(bn, c.G.box(.3, .018, .014), gold, .15, -.012, 0);
  for (const [y, sz] of [[-.14, .1], [-.34, .09], [-.54, .08]]) { emblem(c, bn, 'fleur', sz, c.M(blue, { r: .6 }), .15, y, .012, 0); emblem(c, bn, 'fleur', sz, c.M(blue, { r: .6 }), .15, y, -.016, PI); }
  for (const x of [.02, .15, .28]) { c.add(bn, c.G.cyl(.012, .012, .08, 5), gold, x, x == .15 ? -.78 : -.84, 0); c.add(bn, c.G.cone(.026, .12, 6), c.M(x == .15 ? 0x1f3f95 : 0xd2a43c, { m: .3, r: .6, d: 1 }), x, x == .15 ? -.86 : -.92, 0, { r: [PI, 0, 0] }); }
  hold(c, h.hips, 'hand_R', sp, 0, -.05, .0, .12, 0, .06);
  for (const k of [-1, 1]) K.pouch(c, c.bones.hips, 0x5a3720, k * .17, -.06, -.04, .7, gold);
  return finalize(c, h.root, { R: 1 }); } };

CHARS.elira_a = { name: 'Lady Elira', sheetKey: 'x5', build() {
  const c = makeCtx({ name: 'Lady_Elira',  fem: true, nobust: true, elf: true, bulk: .92, sw: .96, skin: 0xf2cba8, hair: 0xe3b564, eye: 0x4a8a58, under: 0x2c6a3c, pants: 0x2e2a28, sleeve: 0xeee6d2, glove: 0x2a2018, boot: 0x5a3a22 });
  const h = humanoid(c), { gold, leather, dleather } = pal(c), green = 0x1f5a30, lea = c.M(0x6e4528, { r: .8, t: 'leather', n: 'leather' });
  c.add(c.bones.chest, c.G.cyl(.17, .12, .26, 8), lea, 0, .09, .012, { s: [1, 1, .72] }); belt(c, dleather, gold); strapX(c, leather, gold);
  c.add(c.bones.chest, c.G.tor(.1, .02, 5, 12), c.M(0xeee6d2, { r: 1, n: 'under' }), 0, .25, 0, { r: [PI / 2 - .2, 0, 0] });
  for (let i = 0; i < 3; i++) c.add(c.bones.chest, c.G.box(.2, .008, .01), dleather, 0, .0 + i * .07, .125 - i * .006, { r: [0, 0, 0] });
  skirt(c, { col: green, trim: 0xd2a43c, len: .4, top: .17, bot: .3, y: -.03, ragged: .05, zs: .85 });
  tabard(c, { w: .22, len: .5, col: green, trim: gold, emblem: 'sprig', point: .06, z: .19, y: -.03 });
  tabard(c, { w: .14, len: .34, col: 0xeee6d2, trim: gold, point: .04, z: .182, y: -.08, tilt: -.1 }).position.x = .13;
  for (const S of ['L', 'R']) { c.add(c.bones['foreArm_' + S], c.G.cyl(.055, .047, .16, 8), lea, 0, -.17, 0); c.add(c.bones['foreArm_' + S], c.G.tor(.054, .008, 4, 8), gold, 0, -.1, 0, { r: [PI / 2, 0, 0] });
    c.add(c.bones['shin_' + S], c.G.cyl(.072, .06, .36, 8), c.M(0x5a3a22, { r: .8, t: 'leather', n: 'boot' }), 0, -.26, 0); c.add(c.bones['shin_' + S], c.G.sph(.066, 7, 5), c.M(0x8a6a3a, { m: .4, r: .4, n: 'bronze' }), 0, .0, .035, { s: [1, .9, .8] }); c.add(c.bones['shin_' + S], c.G.tor(.068, .01, 4, 8), gold, 0, -.14, 0, { r: [PI / 2, 0, 0] }); }
  hair(c, 'wavy', 0xe3b564, { len: .78 });
  hood(c, c.M(green, { r: .95, d: 1, n: 'hood' }), 1.05);
  const cp = cape(c, { topW: .6, botW: 1.3, len: 1.08, col: green, trim: gold.color.getHex(), lining: 0x174a26, waves: 8, ragged: .05, segs: 18, seed: 17, wrap: .16, flare: .16 }); cp.len = 1.08;
  backEmblem(c, cp, 'sprig', .5, gold, .62); for (const k of [-1, 1]) cp.decal('sprig', .16, gold, .93, k * .3);
  c.add(c.bones.chest, c.G.cyl(.032, .032, .012, 10), gold, 0, .22, .12, { r: [PI / 2, 0, 0] }); emblem(c, c.bones.chest, 'sprig', .05, gold, 0, .22, .13);
  const q = K.quiver(c, { gold }); q.position.set(.1, .12, -.19); q.rotation.set(.1, 0, -.3); c.bones.chest.add(q);
  K.pouch(c, c.bones.hips, 0x6a4326, .2, -.05, .03, 1.0, gold); K.pouch(c, c.bones.hips, 0x6a4326, -.2, -.04, .04, .8, gold);
  const dg = K.dagger(c, gold); dg.position.set(-.19, -.1, .06); dg.rotation.set(PI - .2, 0, .15); dg.scale.setScalar(.8); c.bones.hips.add(dg);
  K.leafCluster(c, c.bones.hips, 5, .03, 0x4f9a3f, -.12, .1, .6);
  const bw = K.bow(c, { gold, len: .62 }); hold(c, h.hips, 'hand_L', bw, 0, -.07, .0, PI / 2, 0, 0);
  return finalize(c, h.root, { L: 1 }, B => { B.upperArm_L.rotation.set(-1.2, 0, .22); B.foreArm_L.rotation.set(-.2, 0, 0); B.upperArm_R.rotation.set(.05, 0, -.18); }); } };

// ================= batch 2: Elira, Rook (+wolf), Asha, Rowan, Kael, Cedric, Morwen, Garruk =================
const ear = (c, col) => { for (const k of [-1, 1]) c.add(c.bones.head, c.G.cone(.03, .11, 4), col, k * .105, .1, -.02, { r: [-.2, 0, -k * 1.45], s: [1, 1, .4] }); };
const gemMat = (c, col, ei = 1.3) => c.M(col, { e: col, ei, r: .15, n: 'gem' + col });
const streamer = (c, par, col, x, y, z, n = 3) => { for (let i = 0; i < n; i++) c.add(par, c.G.cone(.016, .16 + i * .03, 4), c.M(col, { d: 1 }), x + (i - 1) * .018, y - i * .01, z, { r: [PI, 0, (i - 1) * .2], s: [1, 1, .3] }); };

CHARS.elira = { name: 'Lady Elira', sheetKey: 'elira', build() {
  const c = makeCtx({ name: 'Lady_Elira', fem: true, nobust: true, elf: true, eye: 0x3f8a4a, bulk: .9, sw: .96, skin: 0xf2cdaa, hair: 0xe3b650, under: 0x2f6a3a, pants: 0x34343a, sleeve: 0x4a3322, glove: 0x2c2018, boot: 0x5a3820 });
  const h = humanoid(c), { gold, leather, dleather } = pal(c), green = 0x2a5a32, brownLeather = c.M(0x6a4428, { r: .8, n: 'brownarmor' }), bronze = c.M(0x8a6234, { m: .35, r: .5, n: 'bronzeplate' });
  platePack(c, { steel: bronze, trim: gold, cuirass: brownLeather, cuisse: false, tassets: false, noGaunt: true }); belt(c, dleather, gold); strapX(c, dleather, gold);
  c.add(c.bones.chest, c.G.cyl(.16, .12, .12, 8), c.M(0x2f6a3a, { r: .85, t: 'cloth' }), 0, .2, .005, { s: [1, 1, .74] });
  hair(c, 'wavy', 0xe3b650, { len: .85 }); hood(c, c.M(0x28542f, { r: .95, d: 1, n: 'hood' }), 1.1);
  tabard(c, { w: .24, len: .46, col: green, trim: gold, emblem: 'sprig', point: .09, z: .19, y: -.02 });
  skirt(c, { col: green, trim: 0xd2a43c, len: .42, top: .17, bot: .3, y: -.04, zs: .8, ragged: .05, segs: 16 });
  const cp = cape(c, { topW: .6, botW: 1.22, len: 1.05, col: green, trim: gold.color.getHex(), lining: 0x1f4426, waves: 9, ragged: .07, segs: 18, seed: 14, wrap: .14 }); cp.len = 1.05; backEmblem(c, cp, 'sprig', .6, gold, .5);
  for (const S of ['L', 'R']) { c.add(c.bones['foreArm_' + S], c.G.cyl(.056, .05, .2, 8), dleather, 0, -.15, 0); c.add(c.bones['foreArm_' + S], c.G.cyl(.058, .058, .02, 8), gold, 0, -.06, 0); c.add(c.bones['shin_' + S], c.G.sph(.07, 6, 5), bronze, 0, .01, .055, { s: [1, 1, .6] }); }
  K.quiver2(c, brownLeather, gold, 6); K.pouch(c, c.bones.hips, 0x5a3720, .2, -.06, .02, 1, gold);
  const dg = K.dagger(c, gold); dg.position.set(-.2, -.1, .04); dg.rotation.set(PI - .3, 0, -.2); dg.scale.setScalar(.8); c.bones.hips.add(dg);
  const bw = K.bow2(c, { wood: c.M(0x7a5028, { r: .6, n: 'bowwood' }), gold, r: .62 }); hold(c, h.hips, 'hand_L', bw, 0, -.04, .02, 0, -PI / 2, 0);
  return finalize(c, h.root, { L: 1 }, B => { B.upperArm_L.rotation.set(-.35, 0, .12); B.foreArm_L.rotation.set(-.5, 0, 0); }); } };

CHARS.rook = { name: 'Rook Wildbane', sheetKey: 'rook', build() {
  const c = makeCtx({ name: 'Rook_Wildbane', eye: 0x5a3a22, beard: 0x4a2c18, brow: .85, bulk: 1.12, sw: 1.1, skin: 0xc9966c, hair: 0x6a4126, under: 0x4a3322, pants: 0x4a3a2c, sleeve: 0x4a3322, glove: 0x3a281a, boot: 0x5a3a22 });
  const h = humanoid(c), { gold, leather, dleather } = pal(c), fur = c.M(0xd8cbaa, { r: 1, n: 'fur', t: 'fur' }), dfur = c.M(0x8a7a5e, { r: 1, n: 'furdark', t: 'fur' }), green = 0x2a5a32, bronze = c.M(0x8a6234, { m: .35, r: .5, n: 'bronzeplate' });
  platePack(c, { steel: bronze, trim: gold, cuirass: c.M(0x5a3a22, { r: .8, t: 'leather' }), cuisse: false, tassets: false, noGaunt: true }); belt(c, dleather, gold); strapX(c, leather, gold);
  c.add(c.bones.chest, c.G.box(.05, .42, .02), leather, .03, .1, .128, { r: [0, 0, -.6] });
  hair(c, 'messy', 0x6a4126); for (const k of [-1, 1]) c.add(c.bones.head, c.G.cyl(.02, .015, .26, 5), c.M(0x6a4126, { r: .9, t: 'cloth' }), k * .1, -.05, -.02);
  c.add(c.bones.head, c.G.box(.09, .06, .04), c.M(0x5a3820, { r: .9, t: 'cloth' }), 0, .02, .09, { s: [1, .8, .5] });
  K.furMantle(c, fur, dfur, .22, .07); for (const S of ['L', 'R']) { K.furCuff(c, c.bones['foreArm_' + S], fur, .06, -.1); K.furCuff(c, c.bones['shin_' + S], fur, .075, -.12, .045); c.add(c.bones['foreArm_' + S], c.G.cyl(.06, .054, .17, 8), c.M(0x5a3820, { r: .85, t: 'cloth' }), 0, -.17, 0); }
  tabard(c, { w: .26, len: .66, col: green, trim: gold, emblem: 'sprig', point: .09, z: .19, y: -.02 });
  skirt(c, { col: 0x2a5a32, trim: 0xd2a43c, len: .55, top: .17, bot: .34, y: -.04, zs: .85, ragged: .1, segs: 16 });
  const cp = cape(c, { topW: .6, botW: 1.2, len: 1.1, col: green, trim: gold.color.getHex(), lining: 0x1f4426, waves: 9, ragged: .12, segs: 18, seed: 8, wrap: .14 }); cp.len = 1.1; backEmblem(c, cp, 'sprig', .6, gold, .55);
  K.quiver2(c, c.M(0x5a3a22, { r: .8, t: 'leather' }), gold, 6); K.pouch(c, c.bones.hips, 0x5a3720, .2, -.06, .02, 1, gold);
  for (let i = 0; i < 4; i++) c.add(c.bones.hips, c.G.cone(.016, .07, 4), c.M(0xf0ead8), -.1 + i * .045, -.08, .165, { r: [PI, 0, 0] });
  const sp = new THREE.Group(), wood = c.M(0x6b4528, { r: .7, n: 'wood' }), steelH = c.M(0xc6cdd4, { m: .7, r: .35, n: 'spearhead' });
  c.add(sp, c.G.cyl(.02, .024, 1.9, 6), wood, 0, .1, 0); c.add(sp, c.G.cone(.022, .09, 5), gold, 0, -.89, 0, { r: [PI, 0, 0] });
  const hd = new THREE.Shape(); hd.moveTo(0, 0); hd.quadraticCurveTo(.075, .12, 0, .34); hd.quadraticCurveTo(-.075, .12, 0, 0); const hg = new THREE.ExtrudeGeometry(hd, { depth: .018, bevelEnabled: false, curveSegments: 6 }); hg.translate(0, 0, -.009); c.add(sp, hg, steelH, 0, 1.08, 0);
  c.add(sp, c.G.cyl(.032, .028, .06, 6), gold, 0, 1.05, 0); for (const y of [.2, .55]) c.add(sp, c.G.cyl(.028, .028, .025, 6), c.M(0x5a3820), 0, y, 0);
  streamer(c, sp, 0x3f8f3a, .02, .98, 0, 3); streamer(c, sp, 0xd8cbaa, .0, .94, .02, 2); for (let i = 0; i < 3; i++) c.add(sp, c.G.cone(.018, .1, 4), c.M(0x3f8f3a, { d: 1 }), .03, .6 - i * .1, 0, { r: [PI, 0, -.4], s: [1, 1, .3] });
  hold(c, h.hips, 'hand_R', sp, 0, -.05, 0, .1, 0, .05);
  return finalize(c, h.root, { R: 1 }); } };

CHARS.wolf = { name: 'Wolf', sheetKey: 'rook', build() { return K.wolfRig(); } };

CHARS.asha = { name: 'Asha Ironfist', sheetKey: 'asha', build() {
  const c = makeCtx({ name: 'Asha_Ironfist', eye: 0x3a2418, fem: true, nobust: true, bulk: .92, sw: .96, skin: 0xb98260, hair: 0x2c1a14, under: 0xb8222c, pants: 0xeee4d0, sleeve: 0xb98260, glove: 0xe9e1cf, boot: 0x5a3a22 });
  const h = humanoid(c), { gold, leather, dleather } = pal(c), red = 0xb8222c, cream = 0xeee4d0, bronze = c.M(0x8a6234, { m: .35, r: .5, n: 'bronzeplate' });
  belt(c, c.M(red, { r: .9, t: 'cloth' }), gold); c.add(c.bones.chest, c.G.cyl(.15, .12, .2, 8), c.M(red, { r: .85, t: 'cloth' }), 0, .12, .006, { s: [1, 1, .74] });
  tabard(c, { w: .3, len: .66, col: red, trim: gold, emblem: 'ornate', point: .1, z: .17, y: -.02 }); const bk = tabard(c, { w: .3, len: .62, col: red, trim: gold, point: .1, z: -.17, y: -.02 }); bk.rotation.set(.1, PI, 0);
  for (const k of [-1, 1]) { const g = tabard(c, { w: .15, len: .5, col: red, trim: gold, point: .07, z: 0, y: -.02 }); g.position.set(k * .17, -.02, .0); g.rotation.set(0, k * PI / 2, 0); }
  skirt(c, { col: cream, trim: 0xd2a43c, len: .46, top: .17, bot: .27, y: -.05, ragged: .06, segs: 14 });
  for (let i = 0; i < 9; i++) c.add(c.bones.spine, c.G.sph(.028, 5, 4), c.M(0x4a2c1a, { r: .7 }), Math.sin(i * .5 - 2.2) * .17, -.04 - Math.abs(Math.sin(i * .5 - 2.2)) * .06, Math.cos(i * .5 - 2.2) * .12 + .0);
  hair(c, 'wavy', 0x2c1a14, { len: .75 }); c.add(c.bones.head, c.G.sph(.06, 6, 5), c.M(0x2c1a14, { r: .9, t: 'cloth' }), 0, .27, -.03); c.add(c.bones.head, c.G.tor(.113, .014, 4, 14), c.M(red, { r: .9, t: 'cloth' }), 0, .15, 0, { r: [PI / 2 - .05, 0, 0] });
  for (const k of [-1, 1]) c.add(c.bones.head, c.G.cone(.018, .2, 4), c.M(red, { d: 1 }), k * .04, .16, -.14, { r: [PI - .2, 0, k * .3], s: [1, 1, .3] });
  for (const S of ['L', 'R']) { const fa = c.bones['foreArm_' + S], ua = c.bones['upperArm_' + S]; c.add(fa, c.G.cyl(.058, .05, .24, 8), c.M(0xeee4d0, { r: .95, n: 'wrap' }), 0, -.15, 0); c.add(fa, c.G.cyl(.06, .06, .035, 8), gold, 0, -.04, 0); c.add(ua, c.G.cyl(.058, .056, .05, 8), gold, 0, -.16, 0);
    c.add(c.bones['hand_' + S], c.G.sph(.062, 7, 5), c.M(0xeee4d0, { r: .95, t: 'cloth' }), 0, -.05, .0, { s: [1, 1.15, 1] }); c.add(c.bones['shin_' + S], c.G.cyl(.066, .056, .2, 8), bronze, 0, -.27, 0); c.add(c.bones['shin_' + S], c.G.cyl(.058, .058, .03, 8), c.M(0xeee4d0, { r: .95, t: 'cloth' }), 0, -.38, 0); c.add(c.bones['shin_' + S], c.G.sph(.07, 6, 5), bronze, 0, .01, .055, { s: [1, 1, .6] }); c.add(c.bones['thigh_' + S], c.G.cyl(.105, .09, .3, 8), c.M(cream, { r: .95, n: 'baggy' }), 0, -.18, 0); }
  for (const S of ['L', 'R']) K.kiRing(c, c.bones['hand_' + S], 0xffc84a, -.05);
  c.add(c.bones.chest, c.G.cyl(.04, .04, .015, 8), gold, 0, .1, .142, { r: [PI / 2, 0, 0] });
  const cp = cape(c, { topW: .3, botW: .55, len: .5, col: red, trim: gold.color.getHex(), waves: 7, ragged: .12, segs: 12, seed: 4, back: .13 }); cp.len = .5;
  return finalize(c, h.root, { L: 1, R: 1 }, B => { B.upperArm_L.rotation.set(-.5, 0, .45); B.foreArm_L.rotation.set(-1.2, 0, 0); B.upperArm_R.rotation.set(-.5, 0, -.45); B.foreArm_R.rotation.set(-1.2, 0, 0); B.thigh_L.rotation.set(0, 0, -.12); B.thigh_R.rotation.set(0, 0, .12); }); } };

CHARS.rowan = { name: 'Rowan Firebrand', sheetKey: 'rowan', build() {
  const c = makeCtx({ name: 'Rowan_Firebrand', eye: 0x5a3a22, bulk: 1.0, sw: 1.02, skin: 0xe4b58e, hair: 0x5a3822, under: 0x1f3470, pants: 0x28243a, sleeve: 0x1f3470, glove: 0x4a3020, boot: 0x4a3220 });
  const h = humanoid(c), { gold, leather, dleather } = pal(c), crim = 0xa8202c, bronze = c.M(0x8a6234, { m: .35, r: .5, n: 'bronzeplate' });
  platePack(c, { steel: bronze, trim: gold, cuirass: c.M(0x1f3470, { r: .85, t: 'cloth' }), cuisse: false, tassets: false }); belt(c, leather, gold); strapX(c, leather, gold); hair(c, 'swept', 0x5a3822);
  tabard(c, { w: .26, len: .78, col: 0x1f3470, trim: gold, emblem: 'ornate', point: .08, z: .18, y: -.02 });
  skirt(c, { col: crim, trim: 0xd2a43c, len: .6, top: .17, bot: .34, y: -.05, zs: .85, ragged: .05, segs: 16 });
  c.add(c.bones.neck, c.G.cyl(.14, .21, .14, 8, true), c.M(crim, { r: .95, d: 1, t: 'cloth' }), 0, -.0, -.02, { s: [1, 1, 1.05] });
  const cp = cape(c, { topW: .6, botW: 1.2, len: 1.05, col: crim, trim: gold.color.getHex(), lining: 0x7a1620, waves: 9, ragged: .08, segs: 18, seed: 12, wrap: .14 }); cp.len = 1.05; backEmblem(c, cp, 'sun', .6, gold, .5);
  c.add(cp.cb, c.G.dome(.14, 8, 4), c.M(crim, { r: .95, d: 1, t: 'cloth' }), 0, .03, -.1, { s: [1.2, .8, 1], r: [-.5, 0, 0] });
  const bk = K.book(c, 0x8a1c2a, gold, .15, .2); bk.position.set(-.2, -.08, .05); bk.rotation.set(0, PI / 2, .1); c.bones.hips.add(bk); emblem(c, bk, 'sun', .1, gold, 0, 0, .03);
  K.pouch(c, c.bones.hips, 0x5a3720, .2, -.06, .02, .9, gold);
  const st = K.staff(c, 'none', { gold, wood: c.M(0x6b4a2a, { r: .6, m: .3 }), len: 1.85, twist: true, wood2: 0x8a6030 });
  const hd = new THREE.Group(), cr = gemMat(c, 0xff2a2a, 1.2); c.add(hd, c.G.oct(.06), cr, 0, .18, 0, { s: [.8, 1.8, .8] }); c.add(hd, c.G.tor(.08, .012, 4, 10), gold, 0, .1, 0, { r: [PI / 2, 0, 0] });
  for (let i = 0; i < 4; i++) { const a = i / 4 * PI * 2; c.add(hd, c.G.cone(.016, .24, 4), gold, Math.sin(a) * .08, .16, Math.cos(a) * .08, { r: [Math.cos(a) * .4, 0, -Math.sin(a) * .4] }); }
  const fl = K.flame(c, 0xff6a14, 0xffd23a, 1); fl.position.y = .36; hd.add(fl); st.top.add(hd); hold(c, h.hips, 'hand_R', st.g, 0, -.05, 0, .25);
  const f2 = K.flame(c, 0xff6a14, 0xffd23a, 1.1); f2.position.set(0, -.12, .08); c.bones.hand_L.add(f2);
  return finalize(c, h.root, { R: 1, L: 1 }, B => { B.upperArm_L.rotation.set(-.6, 0, .4); B.foreArm_L.rotation.set(-1.0, 0, 0); }); } };

CHARS.kael = { name: 'Kael Runebinder', sheetKey: 'kael', build() {
  const c = makeCtx({ name: 'Kael_Runebinder', eye: 0x4a6ab0, bulk: .96, sw: 1.0, skin: 0xe4b99a, hair: 0x1c1822, under: 0x1f2f78, pants: 0x20284a, sleeve: 0x1f2f78, glove: 0x3a2c22, boot: 0x4a3626 });
  const h = humanoid(c), { gold, leather, dleather } = pal(c), navy = 0x1f2f78, silver = c.M(0xb9c2d4, { m: .5, r: .4, n: 'silver' }), cream = 0xe9e2cf;
  platePack(c, { steel: c.M(0x3a3e58, { m: .4, r: .5, n: 'darkmetal' }), trim: gold, cuirass: c.M(0x1f2f78, { r: .85, t: 'cloth' }), cuisse: false, greaves: true, tassets: false, noGaunt: true }); belt(c, dleather, gold); strapX(c, leather, gold); hair(c, 'messy', 0x1c1822);
  skirt(c, { col: navy, trim: 0xd2a43c, len: .95, top: .17, bot: .42, y: -.05, ragged: .04, segs: 16 });
  tabard(c, { w: .26, len: .85, col: cream, trim: gold, emblem: 'ornate', point: .09, z: .21, y: -.02 }); for (const k of [-1, 1]) { const g = tabard(c, { w: .1, len: .8, col: navy, trim: gold, point: .08, z: .205, y: -.02 }); g.position.x = k * .17; }
  for (const S of ['L', 'R']) bellK(c, S, navy);
  hood(c, c.M(navy, { r: .95, d: 1, n: 'hood' }), 1.35);
  const cp = cape(c, { topW: .62, botW: 1.25, len: 1.1, col: navy, trim: 0xe9e2cf, lining: 0x16205a, waves: 9, ragged: .08, segs: 18, seed: 6, wrap: .15 }); cp.len = 1.1; backEmblem(c, cp, 'ornate', .6, silver, .5);
  c.add(c.bones.chest, c.G.cyl(.04, .04, .015, 8), silver, 0, .24, .13, { r: [PI / 2, 0, 0] }); chain(c, c.bones.chest, silver, 0, .22, .13, 3, -.03);
  const bk = K.book(c, 0x3a2c22, silver, .14, .18); bk.position.set(-.2, -.08, .06); bk.rotation.set(0, PI / 2, .1); c.bones.hips.add(bk);
  K.pouch(c, c.bones.hips, 0x5a3720, .2, -.06, .02, .9, gold);
  const st = K.staff(c, 'none', { gold, wood: c.M(0x5a4228, { r: .6, m: .4 }), len: 1.9, twist: true, wood2: 0x7a5a30 }); const hd = new THREE.Group(), cr = gemMat(c, 0x4aa8ff, 1.3);
  c.add(hd, c.G.tor(.11, .014, 5, 14), gold, 0, .18, 0, { r: [0, PI / 2, 0] }); c.add(hd, c.G.tor(.1, .012, 5, 14), gold, 0, .16, 0, { r: [0, 0, .5] }); c.add(hd, c.G.oct(.05), cr, 0, .17, 0, { s: [.8, 1.6, .8] });
  for (let i = 0; i < 5; i++) c.add(hd, c.G.oct(.02), cr, Math.sin(i * 1.3) * .11, .06 + i * .05, Math.cos(i * 1.3) * .11, { s: [.7, 1.8, .7] }); st.top.add(hd); hold(c, h.hips, 'hand_R', st.g, 0, -.05, 0, .25);
  const glyphs = new THREE.Group(); glyphs.position.set(0, -.28, .08); c.bones.hand_L.add(glyphs);
  [[0, .06, .05, 0], [-.17, .12, 0, .5], [.17, .1, -.03, -.5], [-.1, .28, -.04, .2], [.12, .3, .0, -.3]].forEach(([x, y, z, r], i) => { const g = K.glyph(c, i % 2 ? 0x6ac4ff : 0x4a8cff, .075 + (i == 0) * .02); g.position.set(x, y, z); g.rotation.y = r; glyphs.add(g); });
  return finalize(c, h.root, { R: 1, L: 1 }, B => { B.upperArm_L.rotation.set(-.5, 0, .45); B.foreArm_L.rotation.set(-1.15, 0, 0); }); } };
function bellK(c, S, col) { const { add, G, M, bones: B } = c; add(B['foreArm_' + S], G.cyl(.06, .15, .3, 8, true), M(col, { r: .9, d: 1, t: 'cloth' }), 0, -.15, 0); add(B['foreArm_' + S], G.cyl(.15, .15, .03, 8, true), M(0xe9e2cf, { m: .3, r: .55, d: 1 }), 0, -.3, 0); }

CHARS.cedric = { name: 'Cedric Vale', sheetKey: 'cedric', build() {
  const c = makeCtx({ name: 'Cedric_Vale', eye: 0x5f8a3a, bulk: .94, sw: .98, skin: 0xe6b68e, hair: 0x7a4426, under: 0x1f3a78, pants: 0x34283a, sleeve: 0xf0e6cf, glove: 0x4a3020, boot: 0x5a3a20 });
  const h = humanoid(c), { gold, leather, dleather } = pal(c), navy = 0x1f3a78, crim = 0x8a1830, cream = 0xf0e6cf;
  c.add(c.bones.chest, c.G.cyl(.205, .15, .31, 8), c.M(navy, { r: .85, n: 'doublet' }), 0, .08, .004, { s: [1, 1, .7] }); belt(c, dleather, gold);
  c.add(c.bones.chest, c.G.tor(.1, .03, 5, 12), c.M(cream, { r: .95, t: 'cloth' }), 0, .26, .0, { r: [PI / 2 - .2, 0, 0] });
  skirt(c, { col: navy, trim: 0xd2a43c, len: .36, top: .16, bot: .3, y: -.05, zs: .85, ragged: .03, segs: 16 }); tabard(c, { w: .2, len: .42, col: navy, trim: gold, emblem: 'ornate', point: .06, z: .18, y: -.02 });
  for (const S of ['L', 'R']) { c.add(c.bones['upperArm_' + S], c.G.sph(.075, 7, 5), c.M(cream, { r: .95, t: 'cloth' }), 0, -.1, 0, { s: [1, 1.3, 1] }); c.add(c.bones['foreArm_' + S], c.G.cyl(.06, .06, .12, 8), c.M(cream, { r: .95, t: 'cloth' }), 0, -.08, 0); c.add(c.bones['foreArm_' + S], c.G.cyl(.06, .052, .15, 8), c.M(0x4a3020), 0, -.2, 0); c.add(c.bones['shin_' + S], c.G.cyl(.1, .07, .15, 8, true), c.M(0x5a3a20, { d: 1 }), 0, -.0, 0); c.add(c.bones['shin_' + S], c.G.cyl(.075, .06, .3, 8), c.M(0x5a3a20, { r: .8, t: 'leather' }), 0, -.28, 0); }
  hair(c, 'curly', 0x7a4426); K.hat(c, 0x1f3a78, 0xd2a43c); for (let i = 0; i < 3; i++) { K.feather(c, c.bones.head, i ? 0xf4efe0 : 0xf4efe0, .12 + i * .02, .27 + i * .02, -.02, [.3 - i * .2, .6 - i * .2, -1.1 + i * .1], .3 + i * .03); }
  const cp = cape(c, { topW: .55, botW: 1.1, len: 1.0, col: crim, trim: gold.color.getHex(), lining: 0x6a1226, waves: 9, ragged: .06, segs: 16, seed: 17, wrap: .14 }); cp.len = 1.0; backEmblem(c, cp, 'lion', .55, gold, .45);
  c.add(c.bones.shoulder_R, c.G.dome(.15, 8, 4), c.M(crim, { r: .95, d: 1, t: 'cloth' }), -.05, .03, 0, { s: [1.2, .9, 1.2], r: [0, 0, .3] });
  K.pouch(c, c.bones.hips, 0x5a3720, -.2, -.05, .03, .9, gold);
  const lu = K.lute(c, { wood: c.M(0xb07a3a, { r: .55, n: 'lutewood' }), gold }); lu.scale.setScalar(.95); lu.position.set(.03, -.07, .19); lu.rotation.set(.1, 0, 1.0); c.bones.chest.add(lu);
  return finalize(c, h.root, { R: 1, L: 1 }, B => { B.upperArm_R.rotation.set(-.55, 0, -.15); B.foreArm_R.rotation.set(-1.0, 0, 0); B.upperArm_L.rotation.set(-.75, 0, .2); B.foreArm_L.rotation.set(-1.0, 0, 0); }); } };

CHARS.morwen = { name: 'Morwen Blackveil', sheetKey: 'morwen', build() {
  const c = makeCtx({ name: 'Morwen_Blackveil', eye: 0x8a4ac8, fem: true, nobust: true, bulk: .92, sw: .96, skin: 0xe8d2c4, hair: 0x241636, under: 0x1c1620, pants: 0x1c1620, sleeve: 0x241c2c, glove: 0x1c1620, boot: 0x241a22 });
  const h = humanoid(c), { gold, leather, dleather } = pal(c), vio = 0x6a2aa8, blk = 0x1a1420, bone = c.M(0xe8e0cc, { r: .8, n: 'bone' }), silver = c.M(0x9a96a8, { m: .5, r: .45, n: 'silver' });
  platePack(c, { steel: c.M(0x3a3340, { m: .4, r: .5, n: 'darkplate' }), trim: silver, cuirass: c.M(0x241c2c, { r: .7 }), cuisse: false, tassets: false, noGaunt: true }); belt(c, c.M(0x2c2230, { r: .8, t: 'leather' }), silver);
  skirt(c, { col: blk, trim: 0x6a2aa8, len: .98, top: .17, bot: .42, y: -.05, ragged: .12, segs: 16 }); skirt(c, { col: 0x4a2078, trim: 0x8a5ac8, len: .8, top: .16, bot: .34, y: -.03, zs: .8, ragged: .1, segs: 16 });
  tabard(c, { w: .22, len: .7, col: 0x2c2036, trim: silver, emblem: 'cross', point: .1, z: .19, y: -.02, tilt: -.04 });
  hair(c, 'wavy', 0x241636, { len: .95 }); hood(c, c.M(blk, { r: .95, d: 1, n: 'hood' }), 1.2);
  const cp = cape(c, { topW: .6, botW: 1.3, len: 1.1, col: blk, trim: vio, lining: 0x4a2078, waves: 10, ragged: .24, segs: 20, seed: 23, wrap: .15 }); cp.len = 1.1; backEmblem(c, cp, 'ornate', .6, c.M(0xa88ad0, { r: .5 }), .5);
  c.add(c.bones.neck, c.G.cyl(.15, .2, .13, 8, true), c.M(blk, { r: .95, d: 1, t: 'cloth' }), 0, -.02, -.02, { s: [1, 1, 1.05] });
  K.skull(c, c.bones.hips, bone, .04, 0, -.05, .2); chain(c, c.bones.hips, silver, 0, -.09, .21, 5); for (const [x, y] of [[-.13, -.08], [.13, -.1]]) { K.skull(c, c.bones.hips, bone, .028, x, y, .17); }
  for (const k of [-1, 1]) { K.skull(c, c.bones['shoulder_' + (k > 0 ? 'L' : 'R')], bone, .035, k * .06, .11, .06); chain(c, c.bones.chest, silver, k * .06, .22, .1, 4, -.045); }
  c.add(c.bones.chest, c.G.oct(.03), gemMat(c, 0xb050ff, 1), 0, .17, .13, { s: [.7, 1.5, .7] });
  const bk = K.book(c, 0x2c1a3a, silver, .13, .17); bk.position.set(-.2, -.1, .04); bk.rotation.set(0, PI / 2, .1); c.bones.hips.add(bk);
  const st = K.staff(c, 'none', { gold: silver, wood: c.M(0x2a2030, { r: .6, m: .3 }), len: 1.9, twist: true, wood2: 0x4a3a58 }); const hd = new THREE.Group();
  c.add(hd, c.G.tor(.1, .014, 5, 12), silver, 0, .16, 0, { r: [0, PI / 2, 0] }); K.skull(c, hd, bone, .075, 0, .2, 0);
  for (const k of [-1, 1]) { c.add(hd, c.G.cone(.016, .14, 4), gemMat(c, 0xb050ff, 1.4), k * .09, .06, 0, { r: [PI, 0, 0] }); c.add(hd, c.G.oct(.025), gemMat(c, 0xb050ff, 1.4), k * .13, .27, 0, { s: [.7, 1.6, .7] }); }
  st.top.add(hd); hold(c, h.hips, 'hand_R', st.g, 0, -.05, 0, .25);
  const wisp = gemMat(c, 0xb060ff, 1.6); for (let i = 0; i < 4; i++) c.add(c.bones.hand_L, c.G.cone(.03 - i * .004, .18 + i * .04, 5), c.M(0xa04cff, { e: 0xa04cff, ei: 1.5, a: .8, d: 1 }), (i - 1.5) * .04, -.12 + i * .045, .06, { s: [1, 1, .6], r: [0, 0, (i - 1.5) * .35] });
  c.add(c.bones.hand_L, c.G.sph(.06, 7, 5), c.M(0xa04cff, { e: 0xa04cff, ei: .8, a: .3 }), 0, -.1, .06);
  return finalize(c, h.root, { R: 1, L: 1 }, B => { B.upperArm_L.rotation.set(-.55, 0, .45); B.foreArm_L.rotation.set(-1.0, 0, 0); }); } };

CHARS.garruk = { name: 'Garruk Stonefist', sheetKey: 'garruk', build() {
  const c = makeCtx({ name: 'Garruk_Stonefist', eye: 0x5a3820, beard: 0x3a2214, scar: true, brow: .95, bulk: 1.42, sw: 1.32, skin: 0xc08a60, hair: 0x4a2c1c, under: 0x4a3020, pants: 0x4a3828, sleeve: 0xc08a60, glove: 0x3a281a, boot: 0x4a3220 });
  const h = humanoid(c), { gold, leather, dleather } = pal(c), fur = c.M(0xd2c2a0, { r: 1, n: 'fur', t: 'fur' }), dfur = c.M(0x6a5236, { r: 1, n: 'furdark', t: 'fur' }), iron = c.M(0x5c5e66, { m: .5, r: .5, n: 'darkiron' }), crim = 0x8a1c22;
  platePack(c, { steel: iron, trim: gold, cuirass: c.M(0x4a3020, { r: .85, t: 'cloth' }), cuisse: false, tassets: false, bigPauld: true, pauld: 'spike' }); belt(c, dleather, gold); strapX(c, dleather, gold);
  c.add(c.bones.chest, c.G.box(.05, .42, .02), dleather, .04, .1, .132, { r: [0, 0, -.6] });
  for (const [x, y, rz] of [[-.12, .18, .6], [.1, .05, -.3]]) c.add(c.bones.chest, c.G.box(.02, .1, .01), c.M(0xa82020, { e: 0xa82020, ei: .2 }), x, y, .135, { r: [0, 0, rz] });
  hair(c, 'long', 0x4a2c1c, { len: .55 }); hair(c, 'messy', 0x4a2c1c);
  c.add(c.bones.head, c.G.box(.14, .1, .08), c.M(0x4a2c1c, { r: 1 }), 0, -.0, .06, { s: [1, 1, .7] }); c.add(c.bones.head, c.G.cone(.07, .12, 5), c.M(0x4a2c1c), 0, -.09, .07, { r: [PI + .2, 0, 0] });
  K.furMantle(c, fur, dfur, .25, .075); for (const S of ['L', 'R']) { K.furCuff(c, c.bones['foreArm_' + S], fur, .09, -.05, .05); K.furCuff(c, c.bones['shin_' + S], fur, .1, -.14, .055); K.furCuff(c, c.bones['shin_' + S], fur, .09, -.38, .045); }
  skirt(c, { col: crim, trim: 0x6a1418, len: .55, top: .2, bot: .34, y: -.04, zs: .85, ragged: .16, segs: 16 }); tabard(c, { w: .26, len: .5, col: crim, trim: gold, emblem: 'ornate', point: .1, z: .22, y: -.03 });
  const cp = cape(c, { topW: .72, botW: 1.3, len: 1.1, col: crim, trim: 0x4a1014, lining: 0x5a1014, waves: 9, ragged: .3, segs: 20, seed: 29, wrap: .12 }); cp.len = 1.1; backEmblem(c, cp, 'ornate', .6, c.M(0xd8c8a8, { r: .7 }), .5);
  K.pouch(c, c.bones.hips, 0x4a3020, .27, -.07, .02, 1.1, gold); for (let i = 0; i < 3; i++) c.add(c.bones.hips, c.G.cone(.018, .09, 4), c.M(0xf0ead8), -.12 + i * .05, -.1, .21, { r: [PI, 0, 0] });
  const ax = new THREE.Group(), wood = c.M(0x5a3a22, { r: .8, n: 'axehaft' }); c.add(ax, c.G.cyl(.03, .034, 1.0, 6), wood, 0, .2, 0); c.add(ax, c.G.cone(.034, .1, 5), iron, 0, -.34, 0, { r: [PI, 0, 0] });
  for (const y of [-.2, .0, .45, .6]) c.add(ax, c.G.cyl(.04, .04, .05, 6), gold, 0, y, 0);
  const hd = K.axeHead(c, { iron, gold, rune: 0xb02828 }); hd.position.set(0, .66, 0); hd.scale.setScalar(1.1); ax.add(hd);
  hold(c, h.hips, 'hand_R', ax, 0, -.05, 0, PI - .15, 0, 0);
  return finalize(c, h.root, { R: 1 }); } };

export const ORDER = ['aldric', 'darius', 'selene', 'seraphine', 'talia', 'finn', 'brynn', 'mirelle', 'nyx', 'vesper', 'thorne', 'orin', 'elira', 'rook', 'asha', 'rowan', 'kael', 'cedric', 'morwen', 'garruk', 'wolf'];
import { CHARS3, ORDER3 } from './chars3.js';
Object.assign(CHARS, CHARS3); ORDER.push(...ORDER3);
import { CHARS4, ORDER4 } from './chars4.js';
Object.assign(CHARS, CHARS4); ORDER.push(...ORDER4);
import { CHARS5, ORDER5 } from './chars5.js';
Object.assign(CHARS, CHARS5); ORDER.push(...ORDER5);
import { CHARS6, ORDER6 } from './chars6.js';
Object.assign(CHARS, CHARS6); ORDER.push(...ORDER6);

import './chars7.js';
import './rework1.js';
import './rework2.js';
import './rework3.js';
import './rework4.js';
import './rework5.js';
import './rework6.js';
import './rework7.js';
