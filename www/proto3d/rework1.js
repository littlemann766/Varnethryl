import * as THREE from 'three';
import * as K from './chars_core.js';
import { reg, heavyArmor, flaps, furRing, gunmetal, longCoat } from './chars7.js';
const PI = Math.PI, S = Math.sin, C = Math.cos;
const gold = c => c.M(0xd2a43c, { m: .5, r: .32, n: 'gold' });
// Sir Aldric: gunmetal plate w/ gold edge, long blue tabard + cloak, brown belt
reg('Sir_Aldric', c => { const g = gold(c), st = gunmetal(c, 0x7a828e); heavyArmor(c, { steel: st, steel2: gunmetal(c, 0x5a626e), trim: g });
  longCoat(c, 0x1f3f95, .46, .24, { trim: 0xd2a43c, ragged: .03, y: -.1 }); });
reg('Darius_Umbral', c => { const g = c.M(0xb08d4a, { m: .5, r: .35, n: 'bronze' }), st = gunmetal(c, 0x34363f), st2 = gunmetal(c, 0x24262d); heavyArmor(c, { steel: st, steel2: st2, trim: g, spikes: true });
  longCoat(c, 0x3a1a62, .85, .34, { ragged: .22, y: -.1 }); flaps(c, c.bones.hips, c.M(0x4a2278, { r: .9, d: 1 }), 9, .18, -.1, .5, .09, { jag: .5, flare: .3, seed: 9 }); });
reg('Selene_Frostveil', c => { const fur = c.M(0xf4f0e8, { r: 1, d: 1, n: 'fur' }), sil = c.M(0xdfe6f0, { m: .5, r: .35, n: 'silver' }), g = gold(c);
  longCoat(c, 0xf2eee4, .98, .42, { trim: 0xd2a43c, ragged: .05, y: -.08, zs: .8 }); flaps(c, c.bones.hips, c.M(0x2b4fa8, { r: .9, d: 1 }), 14, .2, -.04, .85, .12, { jag: .15, flare: .1, seed: 6, zs: .8 });
  furRing(c, c.bones.hips, fur, 18, .39, -.98, .09, { seed: 3 }); furRing(c, c.bones.chest, fur, 16, .24, .25, .1, { seed: 4, down: true });
  for (const k of [-1, 1]) { const sh = c.bones['shoulder_' + (k > 0 ? 'L' : 'R')]; furRing(c, sh, fur, 8, .1, .06, .1, { seed: 9 + k }); c.add(sh, c.G.dome(.13, 8, 4), sil, k * .05, .04, 0, { s: [1.2, .7, 1.1] }); }
  for (let i = 0; i < 5; i++) c.add(c.bones.head, c.G.cone(.018, .1 + (i % 2) * .05, 4), c.M(0x9fdcff, { e: 0x5ac0ff, ei: .7, n: 'ice' }), (i - 2) * .05, .24, .07, { r: [-.2, 0, -(i - 2) * .2] }); });
reg('Dame_Seraphine', c => { const g = gold(c), st = gunmetal(c, 0x9aa2ae), st2 = gunmetal(c, 0x7a828e); heavyArmor(c, { steel: st, steel2: st2, trim: g });
  longCoat(c, 0xf2ece0, .75, .3, { trim: 0xd2a43c, ragged: .03, y: -.1 }); flaps(c, c.bones.hips, c.M(0x24408a, { r: .9, d: 1 }), 10, .19, -.12, .55, .1, { flare: .3, jag: .2, seed: 5 }); });
reg('Talia_Stormcall', c => { const fur = c.M(0xe8dcc8, { r: 1, d: 1, n: 'fur' }), fur2 = c.M(0x7a5a3c, { r: 1, d: 1, n: 'fur2' }), tl = c.M(0x1e8a8a, { r: .8, d: 1, n: 'teal' }), ft = c.M(0x2a6a9a, { r: .7, d: 1, n: 'featherB' });
  flaps(c, c.bones.hips, tl, 14, .2, -.05, .8, .11, { jag: .35, flare: .12, seed: 8, zs: .8 }); furRing(c, c.bones.hips, fur, 18, .36, -.82, .12, { seed: 7 }); furRing(c, c.bones.hips, fur2, 12, .22, -.1, .12, { seed: 2 });
  for (const k of [-1, 1]) { const sh = c.bones['shoulder_' + (k > 0 ? 'L' : 'R')]; furRing(c, sh, fur, 10, .11, .05, .14, { seed: 3 + k }); for (let i = 0; i < 4; i++) c.add(sh, c.G.cone(.018, .2, 4), i % 2 ? ft : tl, k * (.08 + i * .03), -.12 - i * .03, (i - 1.5) * .04, { r: [PI, 0, k * .12] }); }
  for (let i = 0; i < 7; i++) c.add(c.bones.head, c.G.box(.025, .5 - (i % 3) * .08, .03), c.M(0x2a1a12, { r: .9, n: 'braid' }), (i - 3) * .03, -.12, -.1 - Math.abs(i - 3) * .008, {}); });
reg('Finn_Valecourt', c => { const g = gold(c), st = gunmetal(c, 0x7a828e); heavyArmor(c, { steel: st, steel2: gunmetal(c, 0x5a626e), trim: g, skirt: false });
  longCoat(c, 0x8a1c24, .82, .36, { trim: 0xd2a43c, ragged: .04, y: -.08 }); longCoat(c, 0x1c3a7a, .55, .26, { y: -.06 });
  c.add(c.bones.chest, c.G.tor(.1, .035, 5, 10), c.M(0xf4f0e8, { r: .9, n: 'ruff' }), 0, .26, .03, { r: [PI / 2, 0, 0] }); });
