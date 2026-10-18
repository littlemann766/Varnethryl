// ================= batch 6 (boss): The Ashen Titan — basalt/magma construct, ~4.3 m tall (player reference 1.8 m) =================
// Same kit as chars5.js (named bones, rigid-parted nodes, flat palette, baked idle + walk). Buildings live in buildings.js.
import * as THREE from 'three';
import * as K from './chars_core.js';
import { rnd, bakeRig } from './chars3.js';
const { makeCtx } = K;
const PI = Math.PI, S = Math.sin;
export const CHARS6 = {};

CHARS6.ashentitan = { name: 'The Ashen Titan', sheetKey: 'ashentitan', build() {
  const c = makeCtx({ name: 'Ashen_Titan' }), { M, bone: bone_, add, G } = c, bn = {}, bone = (...a) => (bn[a[0]] = bone_(...a)), rigB = n => bn[n];
  const B1 = M(0x453a33, { r: 1, n: 'basalt1' }), B2 = M(0x574a40, { r: 1, n: 'basalt2' }), B3 = M(0x1d1917, { r: 1, n: 'basalt3' }), B4 = M(0x5e5248, { r: 1, n: 'basalt4' });
  const MG = M(0xe84a0c, { e: 0xff4a08, ei: 1.25, r: .5, n: 'magma' }), HOT = M(0xffa828, { e: 0xffa020, ei: 1.15, r: .5, n: 'magmaHot' }), BR = M(0x8a6a34, { m: .5, r: .45, n: 'ancientBronze' }), BR2 = M(0xb08a42, { m: .55, r: .4, n: 'ancientGold' }), ASH = M(0x6a6560, { r: 1, n: 'ash' }), ASH2 = M(0x8a857e, { r: 1, n: 'ash2' });
  const SKM = M(0x2c1c16, { e: 0x6a1804, ei: .22, r: 1, n: 'magmaCrust' }), dk = [B1, B2, B3, B4];
  // flush armour plate: thin slab laid tangent to the body (faces outward from the parent's axis)
  const rock = (par, x, y, z, s, sd, sc = [1, .85, 1], m) => { const r = rnd(sd * 11 + 5); s *= 1.25; const a = Math.atan2(x, z), len = Math.hypot(x, z) || 1, pull = .9; return add(par, G.box(s * 1.9, s * 1.35, s * .62), m ?? dk[(r() * 4) | 0], x * pull, y, z * pull, { r: [(r() - .5) * .25, a + (r() - .5) * .35, (r() - .5) * .3], s: [Math.min(1.4, sc[0]) * (.9 + r() * .3), (.8 + r() * .35), 1] }); };
  // glowing crack running down a curved surface (radius rad around parent's y axis)
  const crack = (par, ang, y, rad, len, sd, m = MG, w = .055) => { const r = rnd(sd * 13 + 1); let yy = y, aa = ang; for (let i = 0; i < 3; i++) { const l = len / 3, dz = (r() - .5) * .35; add(par, G.box(w, l, .04), i === 1 ? HOT : m, Math.sin(aa) * rad, yy, Math.cos(aa) * rad, { r: [0, aa, dz] }); yy -= l * .9; aa += (r() - .5) * .25; } };
  const limb = (p, len, r0, r1, m, sides = 7) => { const g = G.cyl(r0, r1, len, sides); g.translate(0, -len / 2, 0); add(p, g, m); };
  const seam = (par, x, y, z, w, h, d, rz = 0, m) => add(par, G.box(w * 1.6, h, d * 1.4), m ?? MG, x, y, z, { r: [0, 0, rz] });
  const root = bone('root', null), hips = bone('hips', root, 0, 2.1, 0), spine = bone('spine', hips, 0, .3, 0), chest = bone('chest', spine, 0, .5, 0), neck = bone('neck', chest, 0, .75, 0), head = bone('head', neck, 0, .2, 0);
  // ---- pelvis + abdomen + chest ----
  add(hips, G.sph(.62, 8, 6), SKM, 0, -.05, 0, { s: [1.25, .8, .9] }); rock(hips, 0, -.2, .35, .3, 1, [1.3, .8, .5]); rock(hips, 0, -.15, -.4, .32, 2, [1.4, .8, .5]);
  add(hips, G.box(1.5, .2, .85), BR, 0, .12, 0); add(hips, G.box(1.55, .06, .9), BR2, 0, .24, 0); for (const k of [-1, 1]) { add(hips, G.box(.55, .6, .08), BR, k * .5, -.45, .46); seam(hips, k * .5, -.45, .5, .05, .5, .02); }
  add(spine, G.sph(.55, 8, 6), SKM, 0, .1, 0, { s: [1.2, .95, .85] }); for (let i = 0; i < 5; i++) { const a = i * 1.3; rock(spine, Math.sin(a) * .55, .05 + (i % 3) * .12, Math.cos(a) * .4, .2, 20 + i); } seam(spine, -.15, .1, .45, .06, .5, .03, .2); seam(spine, .2, .0, .46, .05, .4, .03, -.3); seam(spine, 0, .15, -.45, .07, .5, .03, 0, HOT);
  add(chest, G.sph(.85, 9, 7), SKM, 0, .3, 0, { s: [1.3, 1.0, .95] }); add(chest, G.box(1.7, .9, 1.0), SKM, 0, .25, -.05);
  add(chest, G.box(1.8, .14, 1.12), BR, 0, -.12, -.05); add(chest, G.box(1.6, .14, 1.05), BR, 0, .55, -.05); add(chest, G.box(1.85, .05, 1.16), BR2, 0, -.04, -.05);
  for (let i = 0; i < 26; i++) { const a = i * 2.4, up = (i % 5) * .17; if (i < 20 && i % 2 === 0 && Math.abs(Math.sin(a) * .85) < .6) continue; rock(chest, Math.sin(a) * .85, .0 + up, (i % 2 ? -.62 : .6) * (i < 20 ? 1 : 0) + (i >= 20 ? -.62 : 0), .2 + (i % 3) * .05, 40 + i, [1, .9, .55]); }
  // magma core (front) with ring + cross runes
  add(chest, G.cyl(.34, .34, .08, 14), B3, 0, .3, .86, { r: [PI / 2, 0, 0] }); add(chest, G.cyl(.27, .27, .1, 14), MG, 0, .3, .87, { r: [PI / 2, 0, 0] }); add(chest, G.cyl(.12, .12, .12, 10), HOT, 0, .3, .88, { r: [PI / 2, 0, 0] });
  add(chest, G.tor(.38, .04, 4, 16), BR2, 0, .3, .86); add(chest, G.box(.04, .9, .05), HOT, 0, .3, .92); add(chest, G.box(.9, .04, .05), HOT, 0, .3, .92); for (let i = 0; i < 4; i++) { const a = i * PI / 2 + PI / 4; add(chest, G.box(.03, .18, .04), MG, Math.cos(a) * .52, .3 + Math.sin(a) * .52, .9, { r: [0, 0, a + PI / 2] }); }
  for (const [x, y, w, r] of [[-.55, .1, .5, .6], [.5, .0, .45, -.7], [-.4, .92, .4, -.4], [.6, .65, .35, .5]]) seam(chest, x, y, .85, w, .045, .03, r);
  // back: magma spine spikes + seams
  seam(chest, 0, .3, -.6, .08, 1.0, .03, 0, HOT); seam(chest, -.45, .25, -.58, .05, .7, .03, .3); seam(chest, .45, .35, -.58, .05, .7, .03, -.25);
  for (let i = 0; i < 7; i++) { const x = (i - 3) * .24; add(chest, G.cone(.12 - Math.abs(i - 3) * .008, .3 + (3 - Math.abs(i - 3)) * .08, 4), dk[i % 4], x, .6 + (3 - Math.abs(i - 3)) * .07, -.62, { r: [-.55, 0, x * .3] }); add(chest, G.cone(.04, .22, 4), MG, x, .62 + (3 - Math.abs(i - 3)) * .08, -.66, { r: [-.55, 0, x * .3] }); }
  for (let i = 0; i < 5; i++) { add(spine, G.cone(.09, .32, 4), dk[i % 4], (i - 2) * .22, .35, -.5, { r: [-.7, 0, (i - 2) * .15] }); }
  // ---- head / helm ----
  add(head, G.box(.62, .6, .6), SKM, 0, .22, 0); for (let i = 0; i < 5; i++) rock(head, (i - 2) * .14, .1 + (i % 2) * .3, -.3, .15, 240 + i); add(head, G.box(.7, .22, .66), B1, 0, .52, -.02, { r: [-.1, 0, 0] }); add(head, G.box(.55, .3, .35), B3, 0, .0, .28);
  add(head, G.box(.66, .1, .64), BR, 0, .1, .02); add(head, G.box(.1, .6, .64), BR, 0, .45, 0);
  add(head, G.box(.07, .5, .04), HOT, 0, .27, .31); add(head, G.box(.44, .06, .04), HOT, 0, .3, .31); for (const k of [-1, 1]) { add(head, G.box(.12, .08, .05), MG, k * .15, .22, .32); add(head, G.box(.06, .25, .05), MG, k * .27, .08, .3, { r: [0, 0, k * .2] }); }
  for (let i = 0; i < 9; i++) { const a = (i - 4) * .27; add(head, G.cone(.1, .3 + (4 - Math.abs(i - 4)) * .09, 4), dk[i % 4], Math.sin(a) * .3, .72, -.12 - Math.abs(a) * .1 + .05, { r: [-.2, 0, -a * .6] }); }
  for (let i = 0; i < 5; i++) add(head, G.cone(.04, .22, 4), MG, (i - 2) * .12, .78 + (2 - Math.abs(i - 2)) * .07, -.05, { r: [-.2, 0, -(i - 2) * .12] });
  for (const k of [-1, 1]) { rock(head, k * .38, .35, -.05, .2, 60 + k, [.7, 1, 1]); add(head, G.cone(.07, .3, 4), B3, k * .4, .5, -.1, { r: [0, 0, -k * .6] }); }
  add(neck, G.cyl(.3, .4, .4, 7), B1, 0, .02, 0); add(neck, G.tor(.36, .05, 4, 10), BR, 0, .1, 0, { r: [PI / 2, 0, 0] });
  // ---- arms (long, huge fists) ----
  for (const k of [-1, 1]) { const Sd = k > 0 ? 'L' : 'R';
    const sh = bone('shoulder_' + Sd, chest, k * 1.1, .5, 0), ua = bone('upperArm_' + Sd, sh, 0, 0, 0), fa = bone('foreArm_' + Sd, ua, 0, -1.0, 0), ha = bone('hand_' + Sd, fa, 0, -1.0, 0);
    ua.rotation.z = k * .12; fa.rotation.x = -.35;
    add(sh, G.sph(.52, 8, 6), SKM, 0, 0, 0, { s: [1.1, .9, 1] }); add(sh, G.box(.95, .2, .85), BR, k * .08, .38, 0, { r: [0, 0, k * -.25] }); add(sh, G.box(.9, .06, .8), BR2, k * .08, .5, 0, { r: [0, 0, k * -.25] });
    for (let i = 0; i < 5; i++) add(sh, G.cone(.12, .28 + (i % 2) * .12, 4), dk[i % 4], k * (.1 + i * .12), .5 + (i % 2) * .08 - i * .05, -.12 + (i % 3) * .1, { r: [0, 0, k * -(.2 + i * .1)] });
    seam(sh, k * .3, .1, .5, .05, .5, .03, k * .3); seam(sh, k * .35, .2, -.45, .05, .5, .03, k * -.3, HOT);
    limb(ua, 1.0, .36, .32, SKM, 8); for (let i = 0; i < 7; i++) rock(ua, Math.sin(i * 1.9) * .34, -.1 - (i % 4) * .22, Math.cos(i * 1.9) * .34, .17, 200 + i + k); rock(ua, k * .12, -.45, .25, .22, 80 + k); rock(ua, -k * .1, -.6, -.2, .2, 82 + k); seam(ua, 0, -.5, .33, .04, .55, .03, 0); add(ua, G.cyl(.36, .36, .14, 8), BR, 0, -.9, 0);
    add(fa, G.sph(.36, 7, 5), B1, 0, 0, 0); limb(fa, 1.0, .4, .5, SKM, 8); add(fa, G.box(.8, .3, .8), BR, 0, -.3, 0); add(fa, G.box(.84, .05, .84), BR2, 0, -.14, 0); add(fa, G.box(.78, .12, .78), BR, 0, -.7, 0);
    for (let i = 0; i < 6; i++) rock(fa, Math.sin(i * 1.1) * .45, -.15 - (i % 3) * .25, Math.cos(i * 1.1) * .45, .17, 90 + i + k * 7); seam(fa, 0, -.5, .5, .05, .5, .03, 0); seam(fa, k * .15, -.55, -.5, .05, .4, .03, .2, HOT);
    // fist
    add(ha, G.sph(.52, 8, 6), SKM, 0, -.35, 0, { s: [1.0, .95, 1.05] }); add(ha, G.box(.9, .5, .85), SKM, 0, -.4, .0); for (let i = 0; i < 7; i++) rock(ha, Math.sin(i * 1.9) * .45, -.25 - (i % 3) * .15, Math.cos(i * 1.9) * .45, .17, 210 + i); for (let i = 0; i < 4; i++) add(ha, G.box(.2, .22, .24), B3, (i - 1.5) * .22, -.62, .42, { r: [.2, 0, 0] }); add(ha, G.box(.22, .3, .22), B1, k * .5, -.35, .25, { r: [.5, 0, 0] });
    for (let i = 0; i < 4; i++) rock(ha, (i - 1.5) * .22, -.15, .35, .12, 100 + i, [1, .8, 1]); seam(ha, 0, -.2, .44, .3, .05, .03, 0, HOT); seam(ha, 0, -.38, .45, .04, .3, .03, 0); add(ha, G.tor(.4, .05, 4, 10), BR, 0, -.1, 0, { r: [PI / 2, 0, 0] });
    // rune plaque on back of fist
    add(ha, G.box(.3, .3, .05), B3, 0, -.4, -.45); add(ha, G.box(.04, .22, .06), MG, 0, -.4, -.47); add(ha, G.box(.18, .04, .06), MG, 0, -.35, -.47); }
  // ---- legs ----
  for (const k of [-1, 1]) { const Sd = k > 0 ? 'L' : 'R';
    const th = bone('thigh_' + Sd, hips, k * .55, -.25, 0), sn = bone('shin_' + Sd, th, 0, -.95, 0), ft = bone('foot_' + Sd, sn, 0, -.85, 0);
    add(th, G.sph(.46, 8, 6), SKM, 0, -.05, 0); limb(th, .95, .42, .36, SKM, 8); for (let i = 0; i < 7; i++) rock(th, Math.sin(i * 1.9) * .4, -.1 - (i % 4) * .2, Math.cos(i * 1.9) * .4, .17, 220 + i + k); add(th, G.box(.8, .22, .78), BR, 0, -.35, 0); add(th, G.box(.84, .05, .82), BR2, 0, -.22, 0); rock(th, k * .1, -.3, .36, .2, 120 + k); rock(th, -k * .1, -.55, -.3, .2, 122 + k); seam(th, k * .05, -.55, .4, .05, .45, .03, 0); seam(th, 0, -.6, -.4, .05, .4, .03, .15, HOT);
    add(sn, G.sph(.38, 7, 5), B1, 0, 0, .04); add(sn, G.cyl(.34, .34, .15, 8), BR, 0, -.2, 0, {}); limb(sn, .85, .36, .42, SKM, 8); add(sn, G.box(.75, .5, .7), SKM, 0, -.5, .0); for (let i = 0; i < 6; i++) rock(sn, Math.sin(i * 1.9) * .4, -.2 - (i % 3) * .2, Math.cos(i * 1.9) * .4, .17, 230 + i + k); add(sn, G.box(.8, .12, .75), BR, 0, -.62, 0); for (let i = 0; i < 4; i++) rock(sn, Math.sin(i * 1.7) * .4, -.3 - (i % 2) * .25, Math.cos(i * 1.7) * .4, .15, 130 + i + k);
    seam(sn, 0, -.4, .38, .05, .45, .03, 0); seam(sn, k * .1, -.5, -.36, .05, .35, .03, -.2, HOT);
    add(ft, G.box(.78, .3, 1.1), B3, 0, .08, .25); add(ft, G.box(.8, .08, 1.12), BR, 0, .26, .25); for (let i = -1; i <= 1; i++) { add(ft, G.box(.22, .2, .3), B1, i * .26, .05, .85); rock(ft, i * .26, .2, .75, .13, 140 + i); } seam(ft, 0, .15, .8, .3, .04, .03, 0, HOT); }
  // magma crack networks over limbs/torso
  for (const k of [-1, 1]) { const Sd = k > 0 ? 'L' : 'R'; 
    for (let i = 0; i < 6; i++) { crack(rigB('upperArm_' + Sd), i * 1.05 + 5, -.2 - (i % 3) * .2, .37, .45, 300 + i + k); crack(rigB('foreArm_' + Sd), i * 1.05 + 1, -.3 - (i % 2) * .25, .5, .5, 320 + i + k); crack(rigB('thigh_' + Sd), i * 1.05 + 2, -.2 - (i % 3) * .2, .42, .5, 340 + i + k); crack(rigB('shin_' + Sd), i * 1.05 + 3, -.3 - (i % 2) * .2, .4, .5, 360 + i + k); } }
  for (let i = 0; i < 10; i++) { crack(chest, i * .63, .1 + (i % 3) * .2, .9, .6, 380 + i); crack(spine, i * .63 + .3, .0, .6, .45, 400 + i); }
  for (let i = 0; i < 6; i++) crack(hips, i * 1.05, -.2, .6, .5, 420 + i);
  // ---- static ash / ember clouds and floating rocks (root) ----
  { const r = rnd(33); const SM = [ASH, ASH2, M(0x4a4540, { r: 1, n: 'ash3' }), M(0x9a948c, { r: 1, n: 'ash4' })];
    for (let i = 0; i < 12; i++) { const k = i < 6 ? -1 : 1; add(chest, G.sph(.16 + r() * .14 + (i % 3) * .04, 6, 5), SM[i % 4], k * (.9 + r() * .9), .8 + r() * 1.5, (r() - .5) * 1.2, { s: [1, .75, 1] }); }
    for (let i = 0; i < 10; i++) add(head, G.sph(.24 - i * .012 + r() * .06, 6, 5), SM[i % 4], (r() - .5) * (.4 + i * .08), .8 + i * .17, -.1 + (r() - .5) * .5, { s: [1, .8, 1] });
    for (let i = 0; i < 5; i++) add(chest, G.sph(.15 + r() * .1, 5, 4), HOT, (r() - .5) * 1.4, .9 + r() * 1.2, -.5 - r() * .3);
    for (let i = 0; i < 5; i++) add(hips, G.sph(.3 + r() * .15, 6, 4), SM[i % 4], (r() - .5) * 2.4, -1.6 + r() * .4, (r() - .5) * 1.4, { s: [1.3, .5, 1.3] });
    for (let i = 0; i < 12; i++) { const a = r() * PI * 2, rr = 1.1 + r() * .8; rock(root, Math.sin(a) * rr, .2 + r() * 3.6, Math.cos(a) * rr, .06 + r() * .08, 150 + i); }
    for (let i = 0; i < 8; i++) { const a = r() * PI * 2, rr = .9 + r() * .8; add(root, G.oct(.03 + r() * .03), r() > .5 ? MG : HOT, Math.sin(a) * rr, .5 + r() * 3.8, Math.cos(a) * rr); }
    // scorched cracked base
    add(root, G.cyl(1.7, 1.9, .06, 14), B3, 0, .03, 0); for (let i = 0; i < 9; i++) { const a = i / 9 * PI * 2; seam(root, Math.sin(a) * 1.1, .08, Math.cos(a) * 1.1, .06, .02, .9, 0, i % 2 ? MG : HOT).rotation.y = a; rock(root, Math.sin(a + .3) * 1.7, .1, Math.cos(a + .3) * 1.7, .16, 170 + i); } }
  const upd = (t, mode, R, Bn) => { const ph = t * PI * 2, w = mode === 'walk';
    Bn.hips.position.y += w ? -Math.abs(S(ph)) * .09 : S(ph) * .015; R('hips', 0, w ? S(ph) * .1 : 0, w ? S(ph) * .04 : 0); R('spine', w ? .06 : S(ph) * .015, w ? -S(ph) * .12 : S(ph * .5) * .02, 0); R('chest', S(ph - .5) * (w ? .03 : .02), 0, 0); R('neck', -.04, 0); R('head', S(ph * .5) * .02, w ? S(ph) * .06 : S(ph * .5) * .04);
    for (const [Sd, s] of [['L', 0], ['R', PI]]) { const k = Sd === 'L' ? 1 : -1, p = ph + s; R('thigh_' + Sd, w ? -S(p) * .45 : 0, 0, k * .05); R('shin_' + Sd, w ? Math.max(0, Math.cos(p)) * .5 : 0); R('foot_' + Sd, w ? S(p) * .12 : 0);
      R('upperArm_' + Sd, w ? S(p) * .3 : S(ph + s) * .03, 0, k * .04); R('foreArm_' + Sd, w ? -.15 - Math.max(0, S(p + PI)) * .25 : -.03 + S(ph + s) * .02); R('shoulder_' + Sd, 0, 0, k * S(ph) * .015); } };
  const rig = bakeRig(c, root, 'Ashen_Titan', upd); return rig; } };
export const ORDER6 = ['ashentitan'];
