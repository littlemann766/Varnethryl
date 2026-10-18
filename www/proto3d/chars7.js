// ================= REWORK KIT (boss: match the cards) — per-character hooks run inside finalize() via K.REG =================
// Adds layered plate, flared tassets, knee cops, cuffs, sabatons, fur trim, ragged coat panels, feather fringes etc. on top of the base humanoid.
import * as THREE from 'three';
import * as K from './chars_core.js';
const PI = Math.PI, S = Math.sin, C = Math.cos;
export const R7 = {};
const rnd = s => () => (s = (s * 16807) % 2147483647) / 2147483647;
// ring of overlapping plates / flaps hanging around a bone: n flaps, radius rad, y of top, length len, width w
export function flaps(c, par, mat, n, rad, y, len, w, o = {}) { const { add, G } = c, r = rnd(o.seed ?? 7);
  for (let i = 0; i < n; i++) { const a = i / n * PI * 2 + (o.a0 ?? 0), L = len * (1 - (o.jag ?? 0) * r()), zs = o.zs ?? .78;
    add(par, G.box(w, L, o.t ?? .018), mat, S(a) * rad, y - L / 2, C(a) * rad * zs, { r: [-C(a) * (o.flare ?? .2), a, S(a) * (o.flare ?? .2)] }); } }
export function gunmetal(c, col = 0x6a7280) { return c.M(col, { m: .3, r: .45, n: 'gunmetal', t: 'steel', e: col, ei: .32 }); }
// the standard "heavy armour" upgrade
export function heavyArmor(c, o) { const { add, G, M, bones: B } = c, b = c.spec.bulk ?? 1, st = o.steel, tr = o.trim, st2 = o.steel2 ?? st, fem = !!c.spec.fem;
  // layered skirt of plates (two rows) + belt plates
  if (o.skirt !== false) { flaps(c, B.hips, st, 12, .15 * b, -.04, .24, .1 * b, { flare: .25, seed: 3, t: .02 }); flaps(c, B.hips, st2, 12, .17 * b, -.2, .2, .1 * b, { flare: .35, a0: .26, seed: 4, jag: .1, t: .02 }); add(B.hips, G.cyl(.165 * b, .17 * b, .028, 12), tr, 0, -.035, 0, { s: [1, 1, .78] }); }
  // chest layering: centre ridge, pec plates, gorget, rivet row
  add(B.chest, G.box(.03, .3, .03), tr, 0, .1, .16 * Math.sqrt(b)); for (const k of [-1, 1]) { add(B.chest, G.box(.13 * b, .13, .045), st2, k * .075, .14, .14 * Math.sqrt(b), { r: [-.15, k * .2, 0] }); add(B.chest, G.box(.14, .05, .04), st, k * .07, .035, .15 * Math.sqrt(b), { r: [.2, 0, 0] }); }
  add(B.chest, G.tor(.13, .028, 5, 10), tr, 0, .245, .0, { r: [PI / 2, 0, 0], s: [1, 1.05, 1] }); add(B.neck, G.cyl(.09, .11, .07, 8), st2, 0, .0, 0);
  for (let i = 0; i < 7; i++) add(B.chest, G.sph(.012, 4, 3), tr, (i - 3) * .045, -.07, .15 * Math.sqrt(b));
  for (const k of [-1, 1]) { const Sd = k > 0 ? 'L' : 'R', sh = B['shoulder_' + Sd], fa = B['foreArm_' + Sd], hd = B['hand_' + Sd], sn = B['shin_' + Sd], th = B['thigh_' + Sd], ft = B['foot_' + Sd];
    // pauldron: extra stacked rim + gold edge + (optional) spikes
    add(sh, G.dome(.125 * b, 8, 4), st, k * .06, .035, 0, { s: [1.2, .8, 1.15], r: [0, 0, -k * .3] }); add(sh, G.tor(.12 * b, .012, 4, 10), tr, k * .08, -.015, 0, { r: [PI / 2, 0, -k * .3], s: [1.15, 1.1, 1] });
    if (o.spikes) for (let i = 0; i < 3; i++) add(sh, G.cone(.02, .1 + i * .03, 4), st2, k * (.07 + i * .02), .1, (i - 1) * .05, { r: [(i - 1) * .3, 0, -k * (.6 + i * .2)] });
    // vambrace flare + gauntlet cuff + longer glove
    add(fa, G.cyl(.052 * b, .07 * b, .06, 8), tr, 0, -.255, 0); add(hd, G.box(.075, .045, .065), st, 0, -.075, 0); for (let i = 0; i < 3; i++) add(hd, G.box(.016, .04, .016), st2, (i - 1) * .022, -.105, .015);
    // knee cop with spike, greave ridge, sabaton toe
    add(sn, G.sph(.07 * b, 6, 5), st2, 0, .005, .06, { s: [1.05, .9, .8] }); add(sn, G.cone(.02, .06, 4), tr, 0, .01, .115, { r: [PI / 2, 0, 0] }); add(sn, G.box(.02, .3, .02), tr, 0, -.24, .06 * b); add(sn, G.cyl(.062 * b, .075 * b, .045, 8), st2, 0, -.39, 0);
    add(ft, G.cone(.05, .09, 4), st, 0, -.005, .2, { r: [PI / 2, PI / 4, 0], s: [1, 1, .55] }); add(th, G.box(.04, .2, .02), tr, 0, -.18, .085 * b); }
}
export function furRing(c, par, mat, n, rad, y, len, o = {}) { const { add, G } = c, r = rnd(o.seed ?? 5);
  for (let i = 0; i < n; i++) { const a = i / n * PI * 2, L = len * (.75 + r() * .5); add(par, G.cone(o.w ?? .035, L, 4), mat, S(a) * rad, y - L / 2 * (o.down === false ? -1 : 1), C(a) * rad * (o.zs ?? .85), { r: [(o.down === false ? 0 : PI) + C(a) * .3, 0, -S(a) * .3], s: [1, 1, .6] }); } }
// ragged long coat / robe: tapered cylinder with torn hem (like skirt()) but split front option
export function longCoat(c, col, len, bot, o = {}) { return K.skirt(c, { col, trim: o.trim, len, top: o.top ?? .17, bot, y: o.y ?? -.04, zs: o.zs ?? .85, ragged: o.ragged ?? .1, segs: o.segs ?? 14 }); }
const reg = (name, fn) => { K.REG[name] = fn; };
export { reg };
