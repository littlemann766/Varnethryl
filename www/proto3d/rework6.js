import * as THREE from 'three';
import * as K from './chars_core.js';
import { reg, flaps, furRing } from './chars7.js';
const PI = Math.PI, S = Math.sin, C = Math.cos;
reg('Snowy', c => { const B = c.bones, fur = c.M(0xf2eadc, { r: 1, d: 1, n: 'snowfur' }), fur2 = c.M(0xdcd2c0, { r: 1, d: 1, n: 'snowfur2' }), bl = c.M(0x24429a, { r: .9, d: 1, n: 'scarf' }), gd = c.M(0xd2a43c, { m: .5, r: .35, n: 'bell' });
  for (const k of [-1, 1]) { const Sd = k > 0 ? 'L' : 'R'; B['thigh_' + Sd].scale.set(1.15, .72, 1.15); B['upperArm_' + Sd].scale.set(1.15, .85, 1.15); B['foreArm_' + Sd].scale.set(1.2, .85, 1.2); }
  B.hips.position.y -= .2;
  furRing(c, B.hips, fur, 18, .22, -.05, .14, { seed: 3 }); furRing(c, B.chest, fur, 18, .26, .2, .16, { seed: 4, down: true }); furRing(c, B.head, fur, 16, .13, .12, .12, { seed: 5, down: false, w: .04 });
  for (const k of [-1, 1]) { const Sd = k > 0 ? 'L' : 'R'; furRing(c, B['foreArm_' + Sd], fur2, 9, .09, -.08, .1, { seed: 6 }); furRing(c, B['shin_' + Sd], fur2, 9, .1, -.05, .12, { seed: 7 }); furRing(c, B['upperArm_' + Sd], fur, 9, .1, -.1, .1, { seed: 8 }); c.add(B['shoulder_' + Sd], c.G.sph(.11, 7, 5), fur, k * .05, 0, 0, { s: [1.2, 1, 1.1] }); }
  c.add(B.chest, c.G.sph(.3, 8, 6), fur, 0, -.05, .06, { s: [1.1, 1.2, .9] });
  for (let i = 0; i < 4; i++) { c.add(B.chest, c.G.cyl(.012, .012, .1, 4), gd, -.12 + i * .08, .02 - (i % 2) * .05, .24, {}); c.add(B.chest, c.G.sph(.03, 6, 5), gd, -.12 + i * .08, -.04 - (i % 2) * .05, .24); c.add(B.chest, c.G.cone(.025, .08, 4), bl, -.12 + i * .08, -.12 - (i % 2) * .05, .24, { r: [PI, 0, 0] }); }
  c.add(B.chest, c.G.tor(.2, .05, 5, 10), bl, 0, .22, .02, { r: [PI / 2, 0, 0] }); });
reg('Pip', c => { const B = c.bones, fl = c.M(0xf2e6d0, { r: 1, d: 1, n: 'foxwhite' }), or = c.M(0xe8782a, { r: 1, d: 1, n: 'foxorange' }), dk = c.M(0x3a2a1e, { r: 1, n: 'foxdark' });
  for (const k of ['L', 'R']) if (B['ear_' + k]) B['ear_' + k].scale.setScalar(1.5); for (const n of ['tail_1', 'tail_2', 'tail_3', 'tail_4']) if (B[n]) B[n].scale.set(1.55, 1.55, 1.1);
  for (let i = 0; i < 12; i++) { const a = i / 12 * PI * 2; c.add(B.chest, c.G.cone(.045, .16, 4), i % 2 ? fl : or, S(a) * .17, -.05 + C(a) * .1, .1 + C(a) * .08, { r: [PI + .3 * C(a), 0, -.4 * S(a)] }); }
  for (const k of [-1, 1]) for (let i = 0; i < 4; i++) c.add(B.head, c.G.cone(.03, .11, 4), i % 2 ? fl : or, k * .09, -.03 - i * .012, .01 + i * .03, { r: [0, 0, -k * (1.3 + i * .15)] });
  for (const n of ['shin_FL', 'shin_FR', 'shin_BL', 'shin_BR']) if (B[n]) c.add(B[n], c.G.cyl(.05, .045, .22, 6), dk, 0, -.14, 0); });
reg('Cinder', c => { const B = c.bones, fl = c.M(0xff7a1a, { e: 0xff5a10, ei: .9, r: .6, d: 1, n: 'flameFeather' }), fl2 = c.M(0xffc040, { e: 0xffb020, ei: 1.1, r: .6, d: 1, n: 'flameFeather2' }), rd = c.M(0xc82a1a, { r: .7, d: 1, n: 'redFeather' });
  for (let i = 0; i < 7; i++) c.add(B.hips, c.G.cone(.04, .55 - Math.abs(i - 3) * .06, 4), [fl, fl2, rd][i % 3], (i - 3) * .05, .0, -.25, { r: [-PI / 2 - .35 + Math.abs(i - 3) * .05, 0, (i - 3) * .15], s: [1, 1, .4] });
  for (let i = 0; i < 6; i++) c.add(B.head, c.G.cone(.025, .16 + (i % 2) * .06, 4), i % 2 ? fl2 : fl, (i - 2.5) * .03, .1, -.03 - Math.abs(i - 2.5) * .01, { r: [-.5, 0, (i - 2.5) * .12], s: [1, 1, .4] });
  for (let i = 0; i < 6; i++) c.add(B.neck, c.G.cone(.035, .12, 4), i % 2 ? rd : fl, (i - 2.5) * .035, -.05, .06, { r: [PI + .2, 0, 0] }); });
reg('Zephyr', c => { const B = c.bones, wh = c.M(0xf2ead8, { r: 1, d: 1, n: 'feathW' }), cr = c.M(0xd8b878, { r: 1, d: 1, n: 'feathCream' }), gd = c.M(0xd2a43c, { m: .4, r: .4, n: 'gold' });
  for (let i = 0; i < 14; i++) { const a = i / 14 * PI * 2; c.add(B.neck, c.G.cone(.04, .2, 4), i % 2 ? wh : cr, S(a) * .13, -.05 + C(a) * .09, .0 + C(a) * .09, { r: [PI + .5 * C(a), 0, -.5 * S(a)] }); }
  for (const n of Object.keys(B)) if (/^(thigh|leg|shin)_/.test(n)) for (let i = 0; i < 4; i++) c.add(B[n], c.G.cone(.035, .14, 4), i % 2 ? wh : cr, (i % 2 - .5) * .08, -.08 - i * .05, -.05, { r: [PI - .3, 0, 0] }); });
reg('Hawk', c => { const B = c.bones; B.hips.scale.setScalar(1.3); const br = c.M(0x8a6a4a, { r: 1, d: 1, n: 'hawkbar' }), wh = c.M(0xf0e8d8, { r: 1, d: 1, n: 'hawkwhite' }); for (let i = 0; i < 6; i++) c.add(B.hips, c.G.cone(.03, .14, 4), i % 2 ? wh : br, (i - 2.5) * .03, .0, .06, { r: [PI + .1, 0, 0] }); });
