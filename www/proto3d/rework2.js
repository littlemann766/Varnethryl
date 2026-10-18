import * as THREE from 'three';
import * as K from './chars_core.js';
import { reg, heavyArmor, flaps, furRing, gunmetal, longCoat } from './chars7.js';
const PI = Math.PI, S = Math.sin, C = Math.cos;
const gold = c => c.M(0xd2a43c, { m: .5, r: .32, n: 'gold' });
const strap = (c, par, mat, buckle, x, y, z, w, h, rz = 0, rx = 0) => { c.add(par, c.G.box(w, h, .02), mat, x, y, z, { r: [rx, 0, rz] }); c.add(par, c.G.box(.03, .03, .025), buckle, x, y, z + .008, { r: [0, 0, rz] }); };
reg('Brynn_Cogwright', c => { const br = c.M(0xb08a3e, { m: .5, r: .4, n: 'brass' }), lt = c.M(0x6a4426, { r: .85, n: 'leather' }), dl = c.M(0x3c2616, { r: .85, n: 'dl' });
  for (const k of [-1, 1]) { const Sd = k > 0 ? 'L' : 'R', sn = c.bones['shin_' + Sd], th = c.bones['thigh_' + Sd]; c.add(sn, c.G.cyl(.075, .085, .34, 8), lt, 0, -.26, 0); for (let i = 0; i < 3; i++) strap(c, sn, dl, br, 0, -.14 - i * .09, .075, .1, .025);
    c.add(th, c.G.cyl(.09, .08, .24, 8), c.M(0x3a3028, { r: .9, n: 'pants' }), 0, -.16, 0); c.add(th, c.G.box(.08, .1, .02), lt, 0, -.16, .09); }
  for (const k of [-1, 1]) { const sh = c.bones['shoulder_' + (k > 0 ? 'L' : 'R')]; c.add(sh, c.G.dome(.08, 7, 3), lt, k * .05, .03, 0, { s: [1.2, .7, 1.1] }); c.add(sh, c.G.cyl(.02, .02, .03, 6), br, k * .06, .06, 0, {}); }
  strap(c, c.bones.chest, dl, br, 0, .1, .15, .05, .4, .6); strap(c, c.bones.chest, dl, br, 0, .1, .15, .05, .4, -.6);
  for (let i = 0; i < 3; i++) c.add(c.bones.hips, c.G.box(.04, .06, .03), lt, -.1 + i * .075, -.06, .17); });
reg('Mirelle_Thornroot', c => { const leaf = c.M(0x3b7a3a, { r: .9, d: 1, n: 'leaf' }), leaf2 = c.M(0x5a9a40, { r: .9, d: 1, n: 'leaf2' });
  K.leafCluster(c, c.bones.hips, 26, .4, leaf, -.66, 0); K.leafCluster(c, c.bones.hips, 22, .36, leaf2, -.45, 0); K.leafCluster(c, c.bones.hips, 16, .3, leaf, -.22, 0);
  for (const k of [-1, 1]) { const fa = c.bones['foreArm_' + (k > 0 ? 'L' : 'R')]; K.leafCluster(c, fa, 7, .09, leaf2, -.2, 0); K.leafCluster(c, fa, 5, .08, leaf, -.05, 0); }
  for (let i = 0; i < 8; i++) c.add(c.bones.hips, c.G.sph(.02, 5, 4), c.M(0xf8f4e8, { n: 'blossom' }), S(i * 1.5) * .37, -.6 + (i % 3) * .1, C(i * 1.5) * .32); });
reg('Nyx_Varrin', c => { const lt = c.M(0x2e2420, { r: .8, n: 'leather' }), br = c.M(0xa8863c, { m: .5, r: .45, n: 'agedgold' }), red = c.M(0x8a1424, { r: .9, d: 1, n: 'plaidRed' }), blk = c.M(0x1c1818, { r: .9, d: 1, n: 'plaidBlk' });
  flaps(c, c.bones.hips, red, 14, .18, -.05, .75, .12, { jag: .55, flare: .22, seed: 4, zs: .8 }); flaps(c, c.bones.hips, blk, 12, .2, -.1, .6, .1, { jag: .6, flare: .3, a0: .25, seed: 5, zs: .8 });
  for (let i = 0; i < 4; i++) strap(c, c.bones.chest, lt, br, 0, .0 + i * .06, .14, .3, .028);
  strap(c, c.bones.chest, lt, br, .03, .1, .15, .05, .44, .6);
  for (const k of [-1, 1]) { const Sd = k > 0 ? 'L' : 'R', sn = c.bones['shin_' + Sd], th = c.bones['thigh_' + Sd], fa = c.bones['foreArm_' + Sd];
    c.add(sn, c.G.cyl(.07, .08, .34, 8), lt, 0, -.26, 0); for (let i = 0; i < 3; i++) strap(c, sn, lt, br, 0, -.14 - i * .09, .075, .1, .022); c.add(sn, c.G.sph(.065, 6, 5), br, 0, .0, .06, { s: [1, .8, .6] });
    c.add(th, c.G.cyl(.085, .07, .28, 8), lt, 0, -.18, 0); c.add(fa, c.G.cyl(.056, .06, .17, 8), lt, 0, -.19, 0); for (let i = 0; i < 2; i++) strap(c, fa, br, br, 0, -.14 - i * .06, .056, .1, .015); } });
reg('Vesper_Crowe', c => { const lt = c.M(0x3a2618, { r: .85, n: 'leather' }), g = gold(c), red = c.M(0x8a1020, { r: .9, d: 1, n: 'redcoat' });
  flaps(c, c.bones.hips, red, 14, .18, -.05, .85, .12, { jag: .45, flare: .18, seed: 6, zs: .8 }); for (let i = 0; i < 3; i++) strap(c, c.bones.chest, lt, g, 0, .0 + i * .07, .14, .3, .03);
  for (const k of [-1, 1]) { const Sd = k > 0 ? 'L' : 'R', sn = c.bones['shin_' + Sd], th = c.bones['thigh_' + Sd]; c.add(sn, c.G.cyl(.07, .082, .36, 8), lt, 0, -.25, 0); for (let i = 0; i < 4; i++) strap(c, sn, lt, g, 0, -.1 - i * .08, .076, .1, .02); c.add(sn, c.G.sph(.065, 6, 5), g, 0, 0, .06, { s: [1, .8, .6] }); c.add(th, c.G.cyl(.085, .07, .28, 8), c.M(0x2a2220, { r: .9, n: 'pants' }), 0, -.18, 0); } });
reg('Brother_Thorne', c => { const g = gold(c), bl = c.M(0x1d3a8a, { r: .85, d: 1, n: 'blue' }), fur = c.M(0xf4f0e8, { r: 1, d: 1, n: 'fur' });
  for (const k of [-1, 1]) { c.add(c.bones.hips, c.G.box(.05, .88, .01), g, k * .2, -.5, .17 * .9, { r: [0, k * -.2, 0] }); c.add(c.bones.hips, c.G.box(.1, .6, .012), bl, k * .3, -.5, .12, { r: [0, k * -.5, 0] }); }
  for (let i = 0; i < 3; i++) c.add(c.bones.hips, c.G.box(.5 + i * .09, .025, .012), g, 0, -.3 - i * .2, .33 - i * .01, { s: [1, 1, 1] });
  for (const k of [-1, 1]) { const sh = c.bones['shoulder_' + (k > 0 ? 'L' : 'R')]; furRing(c, sh, fur, 10, .11, .05, .12, { seed: 5 + k }); c.add(sh, c.G.box(.06, .3, .02), bl, k * .06, -.12, .08); c.add(sh, c.G.box(.065, .02, .025), g, k * .06, -.27, .08); }
  furRing(c, c.bones.chest, fur, 18, .25, .26, .1, { seed: 3 }); for (let i = 0; i < 4; i++) c.add(c.bones.chest, c.G.box(.14, .14, .01), bl, 0, .1 - i * .05, .17 + 0.001, { s: [1, .3, 1] }); });
reg('Orin_Ashlance', c => { const g = gold(c), st = gunmetal(c, 0x5e6672), st2 = gunmetal(c, 0x46505c), lt = c.M(0x6a4426, { r: .85, n: 'leather' }); heavyArmor(c, { steel: st, steel2: st2, trim: g, skirt: false });
  flaps(c, c.bones.hips, c.M(0x7a808a, { m: .5, r: .55, n: 'chainmail' }), 12, .16, -.04, .3, .09, { flare: .25, seed: 5 }); for (let i = 0; i < 3; i++) strap(c, c.bones.chest, lt, g, 0, .0 + i * .07, .15, .3, .028);
  longCoat(c, 0xefe3c4, .62, .22, { trim: 0x1f3f95, ragged: .03, y: -.08, top: .14, zs: .55 }); });
