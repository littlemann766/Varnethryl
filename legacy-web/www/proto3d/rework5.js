import * as THREE from 'three';
import * as K from './chars_core.js';
import { reg, heavyArmor, flaps, furRing, gunmetal, longCoat } from './chars7.js';
const PI = Math.PI, S = Math.sin, C = Math.cos;
const gold = c => c.M(0xd2a43c, { m: .5, r: .32, n: 'gold' });
const rnd = s => () => (s = (s * 16807) % 2147483647) / 2147483647;
const strap = (c, par, mat, buckle, x, y, z, w, h, rz = 0) => { c.add(par, c.G.box(w, h, .02), mat, x, y, z, { r: [0, 0, rz] }); c.add(par, c.G.box(.03, .03, .025), buckle, x, y, z + .008, { r: [0, 0, rz] }); };
const boots = (c, lt, br, h = .36, cuff) => { for (const k of [-1, 1]) { const sn = c.bones['shin_' + (k > 0 ? 'L' : 'R')]; c.add(sn, c.G.cyl(.07, .082, h, 8), lt, 0, -.25, 0); for (let i = 0; i < 3; i++) strap(c, sn, lt, br, 0, -.12 - i * .09, .076, .1, .022); c.add(sn, c.G.sph(.062, 6, 5), br, 0, 0, .06, { s: [1, .8, .6] }); if (cuff) c.add(sn, c.G.cyl(.085, .075, .06, 8), cuff, 0, -.07, 0); } };
const beltsX = (c, lt, g, n = 3) => { for (let i = 0; i < n; i++) strap(c, c.bones.chest, lt, g, 0, i * .06, .14, .3, .026); };
// scatter blobs over a bone's surface (moss, fur tufts)
const blobs = (c, par, mat, n, rx, rz, cy, sz, seed, spread = .2) => { const r = rnd(seed); for (let i = 0; i < n; i++) { const a = r() * PI * 2; c.add(par, c.G.sph(sz * (.6 + r() * .8), 6, 4), mat, S(a) * rx, cy + (r() - .5) * spread * 2, C(a) * rz, { s: [1, .6, 1] }); } };
reg('Kestrel_Duskwing', c => { const lt = c.M(0x4a3220, { r: .85, n: 'leather' }), br = c.M(0xb07a34, { m: .4, r: .4, n: 'brass' }), bl = c.M(0x24429a, { r: .9, d: 1, n: 'blue' }); boots(c, lt, br, .42, lt);
  flaps(c, c.bones.hips, c.M(0x3a2c24, { r: .9, d: 1, n: 'skirt' }), 10, .18, -.04, .4, .1, { jag: .5, flare: .25, seed: 3, zs: .8 }); flaps(c, c.bones.hips, bl, 8, .2, -.08, .5, .1, { jag: .7, flare: .25, a0: .3, seed: 6, zs: .8 }); beltsX(c, lt, br, 3); strap(c, c.bones.chest, lt, br, .03, .1, .15, .05, .44, .6); strap(c, c.bones.chest, lt, br, -.03, .1, .15, .05, .44, -.6);
  for (const k of [-1, 1]) { const th = c.bones['thigh_' + (k > 0 ? 'L' : 'R')]; c.add(th, c.G.cyl(.085, .07, .3, 8), lt, 0, -.2, 0); } });
reg('Mossgut', c => { const mo = c.M(0x4f7a2a, { r: 1, n: 'moss1' }), mo2 = c.M(0x6a8f32, { r: 1, n: 'moss2' }), mo3 = c.M(0x3f6a26, { r: 1, n: 'moss3' }), sk = c.M(0x8a9a58, { r: .9, n: 'belly' }), bark = c.M(0x6a4a2a, { r: 1, n: 'bark' });
  c.add(c.bones.spine, c.G.sph(.34, 9, 7), sk, 0, -.02, .1, { s: [1.15, 1, .95] }); c.add(c.bones.chest, c.G.sph(.3, 9, 7), sk, 0, -.1, .1, { s: [1.1, 1, .85] });
  blobs(c, c.bones.chest, mo, 22, .34, .3, .1, .06, 3, .25); blobs(c, c.bones.spine, mo2, 16, .36, .34, 0, .06, 5, .15); blobs(c, c.bones.hips, mo3, 12, .22, .2, 0, .06, 7, .1);
  for (const k of [-1, 1]) { const Sd = k > 0 ? 'L' : 'R'; for (const [bn, y, rr] of [['upperArm_', -.1, .1], ['foreArm_', -.15, .1], ['thigh_', -.2, .15], ['shin_', -.2, .12]]) blobs(c, c.bones[bn + Sd], [mo, mo2, mo3][bn.length % 3], 6, rr, rr, y, .05, 11 + k, .12);
    for (let i = 0; i < 5; i++) c.add(c.bones['shoulder_' + Sd], c.G.cone(.025, .16 + i * .02, 4), mo2, k * (.05 + i * .03), -.05, (i - 2) * .05, { r: [PI, 0, k * .1] }); }
  for (let i = 0; i < 14; i++) c.add(c.bones.hips, c.G.cone(.03, .22 + (i % 3) * .06, 4), i % 2 ? mo : mo3, S(i * .45) * .2, -.1, C(i * .45) * .2, { r: [PI, 0, 0] });
  for (let i = 0; i < 6; i++) c.add(c.bones.spine, c.G.box(.08, .06, .03), bark, (i - 2.5) * .08, -.05, .3, { r: [0, 0, (i % 2) * .3] }); });
reg('Captain_Hearth', c => { const lt = c.M(0x5a3820, { r: .85, n: 'leather' }), br = c.M(0xb07a34, { m: .4, r: .4, n: 'brass' }), cf = c.M(0x6a4126, { r: .9, d: 1, n: 'coat' }), rd = c.M(0xa8302a, { r: .9, d: 1, n: 'red' }); boots(c, lt, br, .42, lt);
  flaps(c, c.bones.hips, cf, 12, .22, -.04, .55, .12, { jag: .25, flare: .2, seed: 4, zs: .78 }); flaps(c, c.bones.hips, rd, 6, .23, -.04, .35, .1, { jag: .3, flare: .25, a0: .5, seed: 5, zs: .78 }); beltsX(c, lt, br, 3);
  for (let i = 0; i < 4; i++) c.add(c.bones.hips, c.G.tor(.022, .007, 4, 8), br, -.22 + i * .06, -.12, .2, { r: [0, i * .6, 0] }); for (const k of [-1, 1]) { const th = c.bones['thigh_' + (k > 0 ? 'L' : 'R')]; c.add(th, c.G.cyl(.095, .08, .3, 8), c.M(0x4a3a2c, { r: .9, n: 'pants' }), 0, -.2, 0); } });
reg('Elder_Wren', c => { const tan = c.M(0xc8a46a, { r: 1, n: 'owlTan' }), wh = c.M(0xf0e4c8, { r: 1, n: 'owlWhite' }), br = c.M(0x6a4a2a, { r: 1, n: 'owlBrown' }), ey = c.M(0xf0b020, { e: 0xf0b020, ei: .5, r: .4, n: 'owlEye' }), bk = c.M(0x3a2a1a, { r: .6, n: 'beak' }), bl = c.M(0x24429a, { r: .9, d: 1, n: 'blue' }); const hd = c.bones.head;
  c.add(hd, c.G.cyl(.14, .14, .03, 12), wh, 0, .11, .1, { r: [PI / 2, 0, 0], s: [1.2, 1, 1] }); for (const k of [-1, 1]) { c.add(hd, c.G.cyl(.065, .065, .03, 10), tan, k * .075, .12, .115, { r: [PI / 2, 0, 0] }); c.add(hd, c.G.cyl(.04, .04, .03, 10), ey, k * .075, .12, .128, { r: [PI / 2, 0, 0] }); c.add(hd, c.G.sph(.018, 5, 4), c.M(0x120c08), k * .075, .12, .146); c.add(hd, c.G.cone(.025, .12, 4), br, k * .1, .22, -.0, { r: [0, 0, -k * .35] }); }
  c.add(hd, c.G.cone(.035, .09, 4), bk, 0, .07, .17, { r: [PI / 2 + .3, 0, 0] });
  for (const k of [-1, 1]) { const Sd = k > 0 ? 'L' : 'R', fa = c.bones['foreArm_' + Sd], ua = c.bones['upperArm_' + Sd]; for (let i = 0; i < 6; i++) c.add(fa, c.G.box(.035, .22 - i * .018, .012), i % 2 ? tan : br, k * .07 + (i - 2.5) * .0, -.2 - i * .02, -.05 - i * .035, { r: [0, 0, k * .1] }); for (let i = 0; i < 5; i++) c.add(ua, c.G.cone(.03, .12, 4), i % 2 ? tan : wh, (i - 2) * .02, -.1 - i * .05, .07, { r: [PI, 0, 0] }); }
  flaps(c, c.bones.hips, bl, 12, .24, -.04, .8, .12, { jag: .15, flare: .15, seed: 5, zs: .8 }); for (let i = 0; i < 14; i++) c.add(c.bones.hips, c.G.cone(.035, .12, 4), i % 2 ? tan : wh, S(i * .45) * .3, -.86, C(i * .45) * .26, { r: [PI, 0, 0] });
  for (let i = 0; i < 4; i++) c.add(c.bones.chest, c.G.cone(.04, .12, 4), i % 2 ? tan : wh, (i - 1.5) * .06, .06 - (i % 2) * .05, .17, { r: [PI, 0, 0] }); });
reg('Thrain_Anvilbeard', c => { const lt = c.M(0x6a4126, { r: .85, n: 'leather' }), br = c.M(0xb08a3e, { m: .5, r: .4, n: 'brass' }), cf = c.M(0x7a4a24, { r: .9, d: 1, n: 'coat' }), nv = c.M(0x24429a, { r: .9, d: 1, n: 'blue' });
  flaps(c, c.bones.hips, cf, 12, .26, -.04, .5, .14, { jag: .1, flare: .2, seed: 5, zs: .8 }); flaps(c, c.bones.hips, nv, 8, .28, -.06, .38, .14, { jag: .2, flare: .25, a0: .4, seed: 7, zs: .8 }); beltsX(c, lt, br, 4);
  for (const k of [-1, 1]) { const Sd = k > 0 ? 'L' : 'R', fa = c.bones['foreArm_' + Sd]; c.add(fa, c.G.box(.12, .1, .12), lt, 0, -.27, 0); for (let i = 0; i < 4; i++) c.add(c.bones.chest, c.G.box(.045, .1, .02), br, k * (.05 + i * .035), .05, .19, {}); }
  for (let i = 0; i < 3; i++) c.add(c.bones.chest, c.G.box(.46 + i * .04, .02, .02), br, 0, .02 - i * .09, .2); });
reg('Valen_Hoofguard', c => { const bl = c.M(0x24429a, { r: .9, d: 1, n: 'blue' }), tm = gold(c), hair = c.M(0xe0c080, { r: 1, d: 1, n: 'tailhair' }), mane = c.M(0xb88a50, { r: 1, d: 1, n: 'mane' }), hips = c.bones.hips, hChest = c.bones.hChest, hSp = c.bones.hSpine;
  for (let i = 0; i < 9; i++) c.add(i < 3 ? hChest : hSp, c.G.cone(.04, .16, 4), mane, 0, .33, .2 - i * .075 + (i < 3 ? .05 : 0), { r: [PI / 2 + 1.1, 0, 0], s: [.7, 1, 1] });
  for (const k of [-1, 1]) for (const [bn, w] of [[hips, .6], [hChest, .6]]) for (let i = 0; i < 8; i++) c.add(bn, c.G.cone(.035, .16 + (i % 3) * .05, 3), bl, k * .31, -.4, (i - 3.5) * .075, { r: [PI, 0, 0], s: [.5, 1, 1] });
  for (let i = 0; i < 5; i++) c.add(hSp, c.G.box(.12, .02, .12), tm, 0, .31, (i - 2) * .12, {}); });
