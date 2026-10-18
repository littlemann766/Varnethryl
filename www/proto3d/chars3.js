// ================= batch 3: Lorian (+hawk), Snowy, Queen Marella, Lunara, Kestrel, Mossgut, Captain Hearth, Elder Wren, Valen (centaur), Thrain =================
// Same kit as chars.js (named bones, rigid-parted nodes, flat palette). Non-humanoids reuse humanoid() and swap the head / legs.
import * as THREE from 'three';
import * as K from './chars_core.js';
const { makeCtx, humanoid, platePack, belt, strapX, hair, hood, furCollar, cape, tabard, skirt, emblem, finalize } = K;
const PI = Math.PI;
export const pal = c => ({
  steel: c.M(0xb4bac2, { m: .4, r: .38, n: 'steel' }), gold: c.M(0xd2a43c, { m: .4, r: .35, n: 'gold' }), leather: c.M(0x5a3720, { r: .85, n: 'leather' }),
  dleather: c.M(0x3c2616, { r: .85, n: 'dleather' }), brass: c.M(0xb07a34, { m: .4, r: .4, n: 'brass' }) });
export const hold = (c, b, n, g, px = 0, py = -.05, pz = 0, rx = 0, ry = 0, rz = 0) => { g.position.set(px, py, pz); g.rotation.set(rx, ry, rz); c.bones[n].add(g); return g; };
export const backEmblem = (c, cp, type, size, mat, f = .4) => emblem(c, cp.cb, type, size, mat, 0, -f * (cp.len ?? 1), cp.z(f) - .024, PI);
export const rnd = seed => () => (seed = (seed * 16807) % 2147483647) / 2147483647;
export const noHead = c => { const h = c.bones.head; [...h.children].forEach(m => { if (m.isMesh) h.remove(m); }); };
export const tassel = (c, par, col, x, y, z, s = 1) => { c.add(par, c.G.cyl(.008 * s, .008 * s, .03 * s, 5), c.M(0xd2a43c, { m: .4, r: .4 }), x, y, z); c.add(par, c.G.cone(.018 * s, .07 * s, 5), c.M(col, { r: .9 }), x, y - .05 * s, z, { r: [PI, 0, 0] }); };
export const moon = (c, par, mat, size, x, y, z, ry = 0) => { const g = new THREE.Group(); g.position.set(x, y, z); g.rotation.y = ry; par.add(g); c.add(g, new THREE.TorusGeometry(size * .4, size * .07, 4, 12, PI * 1.5), mat, 0, 0, 0, { r: [0, 0, PI * .75] });
  c.add(g, c.G.cyl(size * .06, size * .06, .012, 4), mat, size * .5, size * .25, 0, { r: [PI / 2, PI / 4, 0] }); return g; };
const mush = (c, par, x, y, z, s = 1, col = 0xd8582a) => { c.add(par, c.G.cyl(.012 * s, .018 * s, .05 * s, 5), c.M(0xe8dcc0, { r: .9 }), x, y + .025 * s, z); c.add(par, c.G.dome(.04 * s, 7, 3), c.M(col, { r: .8, n: 'mush' }), x, y + .05 * s, z, { s: [1, .9, 1] }); };
const mossBlob = (c, par, n, rx, ry, rz, cx, cy, cz, sz = .06, seed = 3) => { const r = rnd(seed), cols = [0x4f7a2a, 0x6a8f32, 0x3f6a26]; for (let i = 0; i < n; i++) c.add(par, c.G.sph(sz * (.7 + r() * .7), 6, 4), c.M(cols[i % 3], { r: 1, n: 'moss' + (i % 3) }), cx + (r() - .5) * 2 * rx, cy + (r() - .5) * 2 * ry, cz + (r() - .5) * 2 * rz, { s: [1.2, .55, 1.2] }); };
const hang = (c, par, n, w, y, z, len, col, seed = 5) => { const r = rnd(seed); for (let i = 0; i < n; i++) c.add(par, c.G.cone(.018, len * (.6 + r() * .6), 4), c.M(col, { r: 1, d: 1 }), (r() - .5) * 2 * w, y - r() * .04, z + (r() - .5) * .06, { r: [PI, 0, (r() - .5) * .3], s: [1, 1, .5] }); };
const ropeRing = (c, bone, y, r, col = 0x8a6a3a) => c.add(bone, c.G.tor(r, .012, 4, 10), c.M(col, { r: .95, n: 'rope' }), 0, y, 0, { r: [PI / 2, 0, 0] });
export const gemM = (c, col, ei = 1.3) => c.M(col, { e: col, ei, r: .15, n: 'gem' + col });

// generic baked rig (custom bone sets). update(t01, mode) mutates bone rotations from rest.
export function bakeRig(c, root, name, update, holdFlags = {}) {
  if (K.REG[c.spec.name]) K.REG[c.spec.name](c);
  const B = c.bones, names = Object.keys(B); for (const k of names) B[k].userData.rest = { r: B[k].rotation.clone(), p: B[k].position.clone() };
  const wrap = (t, mode) => { for (const n of names) { const b = B[n], r = b.userData.rest; b.rotation.copy(r.r); b.position.copy(r.p); }
    const R = (n, x = 0, y = 0, z = 0) => { const b = B[n]; if (!b) return; b.rotation.x += x; b.rotation.y += y; b.rotation.z += z; }; update(t, mode, R, B); };
  wrap(0, 'idle'); const grp = new THREE.Group(); grp.name = name; grp.add(root);
  const clip = (mode, dur, N) => { const times = [...Array(N)].map((_, i) => i * dur / N), rec = {}, hp = [];
    times.forEach(t => { wrap(t / dur, mode); for (const n of names) (rec[n] ??= []).push(...B[n].quaternion.toArray()); hp.push(...B.hips.position.toArray()); });
    const tracks = []; for (const n of names) { const q0 = new THREE.Quaternion().setFromEuler(B[n].userData.rest.r), a = rec[n]; let mv = false; for (let i = 0; i < N && !mv; i++) mv = Math.abs(a[i * 4] - q0.x) + Math.abs(a[i * 4 + 1] - q0.y) + Math.abs(a[i * 4 + 2] - q0.z) + Math.abs(a[i * 4 + 3] - q0.w) > 1e-4; if (mv) tracks.push(new THREE.QuaternionKeyframeTrack(n + '.quaternion', times, a)); }
    tracks.push(new THREE.VectorKeyframeTrack('hips.position', times, hp)); wrap(0, 'idle'); return new THREE.AnimationClip(mode, dur, tracks); };
  return { root: grp, bones: B, update: wrap, clips: () => [clip('idle', 3, 12), clip('walk', 1, 16)], hold: holdFlags };
}

// ---------- hawk (prop on Lorian's fist + standalone rigged companion) ----------
function hawkParts(c, mk, o = {}) { // mk(name,parent,x,y,z) -> node (Bone for the rigged one, Group for the static prop)
  const { add, G, M } = c, br = M(0x7a5a3a, { r: 1, n: 'hawkbrown' }), dk = M(0x4a3524, { r: 1, n: 'hawkdark' }), cr = M(0xe6d8bc, { r: 1, n: 'hawkcream' }), yl = M(0xe0a830, { r: .6, n: 'hawkyellow' }), bk = M(0x2a2a2e, { r: .5, n: 'hawkbeak' });
  const P = o.prefix ?? '';
  const body = mk(P + 'body', o.root, 0, 0, 0), head = mk(P + 'head', body, 0, .13, .035), tail = mk(P + 'tail', body, 0, -.12, -.07);
  add(body, G.sph(.085, 8, 6), br, 0, 0, 0, { s: [.85, 1.45, .95], r: [.15, 0, 0] }); add(body, G.sph(.07, 7, 5), cr, 0, -.01, .035, { s: [.8, 1.3, .6] });
  for (let i = 0; i < 6; i++) add(body, G.box(.012, .035, .01), dk, (i % 3 - 1) * .035, -.04 + (i > 2 ? .04 : 0), .075, { r: [.1, 0, 0] });
  add(head, G.sph(.052, 7, 6), br, 0, .02, 0, { s: [.95, 1, 1.05] }); add(head, G.cone(.02, .05, 5), bk, 0, .0, .062, { r: [PI / 2 + .3, 0, 0] }); add(head, G.box(.03, .012, .03), yl, 0, .018, .05);
  for (const k of [-1, 1]) { add(head, G.sph(.012, 5, 4), M(0xf2c040, { e: 0xf2c040, ei: .3 }), k * .032, .035, .036); add(head, G.sph(.005, 4, 3), M(0x111111), k * .034, .035, .045); add(head, G.box(.035, .008, .015), dk, k * .03, .05, .04, { r: [0, 0, k * -.25] }); }
  add(tail, G.box(.075, .17, .012), br, 0, -.08, -.01, { r: [.25, 0, 0] }); for (let i = 0; i < 3; i++) add(tail, G.box(.075, .012, .014), dk, 0, -.06 - i * .035, -.015 - i * .008, { r: [.25, 0, 0] });
  for (const k of [-1, 1]) { const S = k > 0 ? 'L' : 'R', w = mk(P + 'wing_' + S, body, k * .075, .05, -.01), wt = mk(P + 'wingTip_' + S, w, 0, -.13, 0);
    add(w, G.sph(.04, 6, 5), br, k * .008, -.05, 0, { s: [.5, 1.9, 1] }); add(w, G.box(.02, .14, .075), br, k * .02, -.07, 0); add(wt, G.box(.02, .14, .06), dk, k * .018, -.07, 0); add(wt, G.cone(.03, .08, 4), dk, k * .018, -.17, 0, { r: [PI, 0, 0], s: [.5, 1, 1] });
    for (let i = 0; i < 3; i++) add(w, G.box(.022, .012, .07), cr, k * .028, -.03 - i * .035, 0); }
  for (const k of [-1, 1]) { const lg = mk(P + 'leg_' + (k > 0 ? 'L' : 'R'), body, k * .03, -.1, .02); add(lg, G.cyl(.01, .01, .06, 5), yl, 0, -.03, 0); for (let i = -1; i <= 1; i++) add(lg, G.cone(.007, .04, 4), yl, i * .012, -.075, .018, { r: [PI / 2 + .6, 0, 0] }); }
  return { body, head, tail };
}
function hawkRig() {
  const c = makeCtx({ name: 'Hawk' }), root = c.bone('root', null), hips = c.bone('hips', root, 0, .4, 0);
  const mk = (n, p, x, y, z) => { const b = c.bone(n, p, x, y, z); return b; };
  hawkParts(c, (n, p, x, y, z) => n === 'body' ? hips : mk(n, p, x, y, z), { root: hips, prefix: '' });
  const upd = (t, mode, R, B) => { const ph = t * PI * 2;
    if (mode === 'walk') { for (const S of ['L', 'R']) { const k = S === 'L' ? 1 : -1; R('wing_' + S, 0, 0, k * (.7 + Math.sin(ph) * .55)); R('wingTip_' + S, 0, 0, k * (.3 + Math.sin(ph - .8) * .35)); } R('hips', -.35 + Math.sin(ph * 2) * .03); B.hips.position.y += Math.sin(ph) * .035; R('tail', .3 + Math.sin(ph) * .08); R('head', .35); for (const S of ['L', 'R']) R('leg_' + S, .5); }
    else { R('head', 0, Math.sin(ph) * .5 * Math.max(0, Math.sin(ph * .5)), 0); R('hips', Math.sin(ph) * .012); for (const S of ['L', 'R']) { const k = S === 'L' ? 1 : -1; R('wing_' + S, 0, 0, k * (.04 + Math.sin(ph) * .015)); } R('tail', Math.sin(ph) * .03); B.hips.position.y += Math.sin(ph) * .003; } };
  return bakeRig(c, root, 'Hawk', upd);
}

// ====================================== LORIAN ======================================
export const CHARS3 = {};
CHARS3.lorian = { name: 'Lorian Skysong', sheetKey: 'lorian', build() {
  const c = makeCtx({ name: 'Lorian_Skysong', bulk: 1.0, sw: 1.04, skin: 0xe9bd96, hair: 0xc9944a, under: 0xefe6d0, pants: 0x3a3330, sleeve: 0xefe6d0, glove: 0x3a2a20, boot: 0x4a2e1c });
  const h = humanoid(c), { gold, leather, dleather, brass } = pal(c), blue = 0x24429a, cream = 0xefe6d0;
  hair(c, 'curly', 0xc9944a); hair(c, 'swept', 0xc9944a);
  c.add(c.bones.chest, c.G.cyl(.2, .15, .26, 8), c.M(0x6a4126, { r: .85, n: 'vest' }), 0, .1, .006, { s: [1, 1, .72] }); belt(c, dleather, gold); strapX(c, leather, gold); strapX(c, dleather, gold);
  { const f1 = c.M(0xf0e8d2, { r: 1, d: 1, n: 'feather' }), f2 = c.M(0xd8c9a4, { r: 1, d: 1, n: 'feather2' }); for (const k of [-1, 1]) { const sh = c.bones['shoulder_' + (k > 0 ? 'L' : 'R')]; for (let row = 0; row < 3; row++) for (let i = 0; i < 5; i++) { const a = (i - 2) * .45; c.add(sh, c.G.cone(.035 - row * .004, .15 - row * .015, 4), (i + row) % 2 ? f1 : f2, k * (.06 + row * .025) + Math.sin(a) * .06, .06 - row * .045, Math.cos(a) * .11 - .0, { r: [PI + Math.cos(a) * .0, 0, k * (.9 + row * .15)], s: [1, 1, .35] }); } } }
  skirt(c, { col: cream, trim: 0xd2a43c, len: .62, top: .17, bot: .3, y: -.04, zs: .85, ragged: .06, segs: 14 });
  tabard(c, { w: .22, len: .6, col: blue, trim: gold, emblem: 'lion', point: .09, z: .18, y: -.02 });
  const cp = cape(c, { topW: .62, botW: 1.25, len: 1.08, col: blue, trim: gold.color.getHex(), lining: 0x1a3174, waves: 9, segs: 16, seed: 21, wrap: .14 }); cp.len = 1.08;
  backEmblem(c, cp, 'lion', .62, gold, .4); for (const k of [-1, 0, 1]) emblem(c, cp.cb, 'fleur', .13, gold, k * .28, -.92, cp.z(.9) - .026, PI);
  emblem(c, c.bones.chest, 'sun', .1, gold, 0, .22, .125); for (const k of [-1, 1]) tassel(c, c.bones.chest, 0xd2a43c, k * .05, .15, .13);
  for (const S of ['L', 'R']) { const fa = c.bones['foreArm_' + S]; c.add(fa, c.G.cyl(.056, .05, .21, 8), dleather, 0, -.16, 0); c.add(fa, c.G.cyl(.058, .058, .02, 8), gold, 0, -.06, 0);
    c.add(c.bones['shin_' + S], c.G.cone(.055, .07, 4), gold, 0, -.0, .06, { r: [PI / 2, PI / 4, 0] }); c.add(c.bones['shin_' + S], c.G.cyl(.07, .06, .1, 8), c.M(0x6a6a72, { m: .4, r: .5 }), 0, -.02, 0); }
  K.pouch(c, c.bones.hips, 0x5a3720, .2, -.06, .03, 1, gold); K.pouch(c, c.bones.hips, 0x5a3720, -.2, -.07, .02, .9, gold);
  c.add(c.bones.hips, c.G.cyl(.04, .04, .22, 8), c.M(0x6a4126, { r: .8 }), -.14, -.08, -.12, { r: [PI / 2 - .25, 0, .3] });
  // trumpet (L hand) with banner
  const tr = new THREE.Group(), br = c.M(0xe0b040, { m: .6, r: .3, n: 'trumpet' });
  c.add(tr, c.G.cyl(.012, .012, .45, 6), br, 0, 0, 0, { r: [PI / 2, 0, 0] }); c.add(tr, c.G.cone(.075, .22, 10), br, 0, 0, .33, { r: [PI / 2, 0, 0] }); c.add(tr, c.G.tor(.02, .006, 4, 8), br, 0, 0, -.2, { r: [0, 0, 0] });
  const bn = c.add(tr, c.G.box(.01, .26, .13), c.M(blue, { r: .9, d: 1 }), 0, -.15, .0); emblem(c, bn, 'lion', .09, gold, .006, .0, 0, PI / 2);
  hold(c, h.hips, 'hand_L', tr, 0, -.06, .1, .0, 0, 0);
  // hawk on raised right fist
  const hk = new THREE.Group(); hawkParts(c, (n, p, x, y, z) => { const g = new THREE.Group(); g.name = 'h_' + n; g.position.set(x, y, z); p.add(g); return g; }, { root: hk, prefix: 'h' });
  hk.scale.setScalar(1.25); hk.position.set(0, -.03, .12); hk.rotation.set(PI / 2, 0, 0); c.bones.hand_R.add(hk);
  c.add(c.bones.hand_R, c.G.cyl(.052, .056, .08, 8), c.M(0x2a1c14, { r: .85 }), 0, -.04, 0);
  return finalize(c, h.root, { L: 1, R: 1 }, B => { B.upperArm_R.rotation.set(-.7, 0, -.02); B.foreArm_R.rotation.set(-1.1, 0, 0); B.upperArm_L.rotation.set(-.25, 0, .22); B.foreArm_L.rotation.set(-.8, 0, 0); }); } };
CHARS3.hawk = { name: 'Hawk (Lorian companion)', sheetKey: 'lorian', build() { return hawkRig(); } };

// ====================================== SNOWY (yeti) ======================================
CHARS3.snowy = { name: 'Snowy', sheetKey: 'snowy', build() {
  const fur = 0xfbf7ec;
  const c = makeCtx({ name: 'Snowy', bulk: 1.65, sw: 1.22, skin: fur, hair: fur, under: fur, pants: fur, sleeve: fur, glove: 0xe8def4, boot: fur });
  const h = humanoid(c), { gold, leather, dleather } = pal(c), F = c.M(fur, { r: 1, n: 'fur' }), F2 = c.M(0xe2d6bc, { r: 1, n: 'fur2' }), blue = c.M(0x2c4a9a, { r: .9, d: 1, n: 'scarf' }), claw = c.M(0x2f4590, { r: .6, n: 'claw' });
  noHead(c); const hd = c.bones.head, { add, G } = c;
  for (const S of ['L', 'R']) { c.bones['thigh_' + S].scale.set(1.3, .74, 1.3); c.bones['upperArm_' + S].scale.set(1.25, .85, 1.25); } c.bones.hips.position.y = .72; hd.scale.setScalar(1.22);
  add(c.bones.chest, G.sph(.27, 9, 7), F, 0, .02, .0, { s: [1.15, 1.0, .95] }); add(c.bones.spine, G.sph(.27, 9, 7), F, 0, -.02, .04, { s: [1.1, 1.1, 1.05] });
  add(hd, G.sph(.135, 10, 8), F, 0, .1, 0, { s: [1.15, 1.0, 1.05] }); add(hd, G.sph(.07, 8, 6), c.M(0xf9f4e6, { r: 1, n: 'muzzle' }), 0, .06, .1, { s: [1.1, .85, 1] }); add(hd, G.sph(.025, 6, 5), c.M(0x2c4590, { r: .4, n: 'nose' }), 0, .085, .165, { s: [1.3, .9, 1] });
  for (const k of [-1, 1]) { add(hd, G.sph(.03, 7, 6), c.M(0x2a58c0, { r: .3, n: 'eyeblue' }), k * .06, .125, .125, { s: [1, 1.2, .6] }); add(hd, G.sph(.012, 5, 4), c.M(0x0a0a18), k * .06, .125, .142); add(hd, G.sph(.006, 4, 3), c.M(0xffffff), k * .054, .135, .148);
    add(hd, G.sph(.045, 7, 6), F, k * .12, .21, -.01, { s: [1, 1, .6] }); add(hd, G.sph(.026, 6, 5), c.M(0xd9a0a0, { r: 1 }), k * .12, .21, .015, { s: [1, 1, .4] }); add(hd, G.box(.05, .01, .01), F2, k * .06, .165, .13, { r: [0, 0, k * -.3] }); }
  for (let i = 0; i < 9; i++) { const a = i / 9 * PI * 2; add(hd, G.cone(.03, .09, 4), i % 2 ? F : F2, Math.sin(a) * .1, .22 + (i % 3) * .01, Math.cos(a) * .09, { r: [Math.cos(a) * .9, 0, -Math.sin(a) * .9], s: [1, 1, .6] }); }
  for (let i = 0; i < 7; i++) { const a = i / 7 * PI * 2; add(hd, G.cone(.03, .08, 4), F, Math.sin(a) * .13, .05, Math.cos(a) * .1, { r: [PI + Math.cos(a) * .9, 0, -Math.sin(a) * .9], s: [1, 1, .6] }); }
  // fur tufts on body + paw claws
  const r = rnd(7); for (let i = 0; i < 26; i++) { const a = r() * PI * 2, bone = i % 3 ? c.bones.chest : c.bones.hips; add(bone, G.cone(.03, .08, 4), i % 2 ? F : F2, Math.sin(a) * .26, (r() - .5) * .3, Math.cos(a) * .2, { r: [PI + Math.cos(a) * 1.2, 0, -Math.sin(a) * 1.2], s: [1, 1, .6] }); }
  add(c.bones.spine, G.sph(.19, 8, 6), F, 0, 0, .06, { s: [1.2, 1.1, 1.0] });
  for (const S of ['L', 'R']) { for (let i = -1; i <= 1; i++) add(c.bones['foot_' + S], G.cone(.012, .04, 4), claw, i * .03, -.0, .19, { r: [PI / 2, 0, 0] }); add(c.bones['shin_' + S], G.sph(.1, 7, 5), F, 0, -.08, 0, { s: [1, 1.1, 1] }); add(c.bones['foot_' + S], G.sph(.07, 7, 5), F, 0, .01, .08, { s: [1.1, .7, 1.5] });
    for (let i = -1; i <= 1; i++) add(c.bones['hand_' + S], G.sph(.014, 4, 3), claw, i * .02, -.08, .02); add(c.bones['foreArm_' + S], G.sph(.07, 7, 5), F, 0, -.18, 0, { s: [1, 1.5, 1] }); }
  // scarf, medallion, bell, tassels
  furCollar(c, blue, .22, .075); for (const k of [-1, 1]) { add(c.bones.chest, G.box(.1, .3, .02), blue, k * .1, .02, .17, { r: [0, 0, k * .12], n: 'scarfpanel' }); emblem(c, c.bones.chest, 'snow', .07, c.M(0xf0e4c0, { r: .6 }), k * .1, .05, .182); tassel(c, c.bones.chest, 0x2c4a9a, k * .11, -.12, .17, 1.1); }
  add(c.bones.chest, G.cyl(.05, .05, .015, 10), gold, 0, .2, .2, { r: [PI / 2, 0, 0] }); emblem(c, c.bones.chest, 'sun', .07, c.M(0xf2d27a, { m: .4 }), 0, .2, .21);
  add(c.bones.chest, G.cone(.04, .06, 8), gold, -.12, -.04, .2, { r: [PI, 0, 0] }); add(c.bones.chest, G.sph(.012, 4, 3), gold, -.12, -.09, .2);
  // backpack + bedroll
  const bp = c.bones.chest; add(bp, G.box(.4, .42, .2), leather, 0, .08, -.24); add(bp, G.box(.4, .16, .22), dleather, 0, -.08, -.24); add(bp, G.cyl(.075, .075, .38, 10), c.M(0x2c4a9a, { r: .9, n: 'rollblue' }), 0, .27, -.2, { r: [0, 0, PI / 2] });
  for (const k of [-1, 1]) { add(bp, G.cyl(.06, .06, .02, 10), F2, k * .2, .27, -.2, { r: [0, 0, PI / 2] }); add(bp, G.box(.04, .3, .02), dleather, k * .1, .12, -.14); add(bp, G.box(.045, .04, .025), gold, k * .1, .26, -.285); }
  emblem(c, bp, 'snow', .16, c.M(0xf2d27a, { m: .3 }), 0, .27, -.27, PI);
  K.pouch(c, c.bones.hips, 0x5a3720, -.3, -.04, .0, 1.2, gold);
  const rig = finalize(c, h.root, {}); rig.root.scale.setScalar(.8); return rig; } };


// ====================================== QUEEN MARELLA (mermaid) ======================================
CHARS3.marella = { name: 'Queen Marella', sheetKey: 'marella', build() {
  const c = makeCtx({ name: 'Queen_Marella', fem: true, nobust: true, bulk: .9, sw: .94, skin: 0xd9a888, hair: 0x1f6a66, under: 0xe8dcc0, pants: 0x2a7a6a, sleeve: 0xd7e6d6, glove: 0xd9a888, boot: 0x2a7a6a });
  const h = humanoid(c), { gold } = pal(c), { add, G, M, bones: B, bone } = c;
  // no legs: remove leg meshes (tail replaces them)
  for (const S of ['L', 'R']) for (const n of ['thigh_', 'shin_', 'foot_']) { const b = B[n + S]; [...b.children].forEach(m => { if (m.isMesh) b.remove(m); }); }
  const sc1 = M(0x2c8a74, { r: .5, m: .15, n: 'scale1' }), sc2 = M(0x1c5e58, { r: .5, m: .15, n: 'scale2' }), fin = M(0x3aa89a, { r: .6, d: 1, n: 'fin' }), belly = M(0xcfe0c8, { r: .7, n: 'bellyscale' });
  const tl = [[.3, .15, .11, 0], [.3, .115, .085, .1], [.28, .09, .06, .18], [.2, .06, .04, .26]]; let par = B.hips, y0 = -.02;
  tl.forEach(([len, r0, r1, rot], i) => { const t = bone('tail_' + (i + 1), par, 0, y0, 0); t.rotation.x = rot; const g = G.cyl(r0, r1, len, 9); g.translate(0, -len / 2, 0); add(t, g, i % 2 ? sc2 : sc1, 0, 0, 0, { s: [1, 1, .78] });
    add(t, G.cyl(r0 * 1.02, r0 * 1.02, .025, 9), sc2, 0, -.01, 0, { s: [1, 1, .8] }); add(t, G.box(r0 * 1.0, len * .85, .03), belly, 0, -len / 2, r0 * .62 - .01, { s: [1, 1, 1] }); par = t; y0 = -len; });
  const tipB = bone('tail_5', par, 0, -.2, 0); tipB.rotation.x = .3; { const fs = new THREE.Shape(); fs.moveTo(0, 0); fs.quadraticCurveTo(.3, -.05, .36, -.3); fs.quadraticCurveTo(.15, -.24, 0, -.34); fs.quadraticCurveTo(-.15, -.24, -.36, -.3); fs.quadraticCurveTo(-.3, -.05, 0, 0);
    const fg = new THREE.ExtrudeGeometry(fs, { depth: .014, bevelEnabled: false, curveSegments: 6 }); fg.translate(0, 0, -.007); add(tipB, fg, fin, 0, 0, 0); add(tipB, G.box(.012, .3, .02), sc2, 0, -.17, 0); add(tipB, G.box(.012, .25, .02), sc2, .12, -.16, 0, { r: [0, 0, .3] }); add(tipB, G.box(.012, .25, .02), sc2, -.12, -.16, 0, { r: [0, 0, -.3] }); }
  add(B.hips, G.sph(.15, 8, 6), sc1, 0, -.03, 0, { s: [1, 1, .85] });
  // bodice: shell cups, pearl strings, gold bands
  for (const k of [-1, 1]) { add(B.chest, G.dome(.09, 8, 4), M(0xf0e4d0, { r: .5, n: 'shell' }), k * .07, .13, .1, { r: [PI / 2 - .2, 0, 0], s: [1, 1, .8] }); add(B.chest, G.sph(.012, 5, 4), M(0xffffff, { r: .2, e: 0xaaaaaa, ei: .2 }), k * .07, .13, .165); }
  add(B.chest, G.cyl(.17, .12, .16, 8), M(0x2c8a74, { r: .5, n: 'bodice' }), 0, .02, .005, { s: [1, 1, .72] }); belt(c, gold, M(0xf0e4d0, { r: .3 }), .02);
  for (let i = 0; i < 8; i++) { const a = i / 8 * PI - PI * .5; add(B.chest, G.sph(.012, 5, 4), M(0xffffff, { r: .2 }), Math.sin(a) * .19, .04 - Math.cos(a * 1.5) * .07, .13 + Math.cos(a) * .02); }
  add(B.chest, G.tor(.12, .012, 4, 10), gold, 0, .23, .03, { r: [PI / 2, 0, 0], s: [1, 1, .8] });
  // hair: long teal waves + crown of coral
  hair(c, 'wavy', 0x1f6a66, { len: 1.05 }); hair(c, 'swept', 0x1f6a66); for (const k of [-1, 1]) { add(B.head, G.box(.07, .6, .1), M(0x1f6a66, { r: .85 }), k * .13, -.28, -.04); add(B.chest, G.box(.08, .5, .1), M(0x1f6a66, { r: .85 }), k * .2, .0, -.1); }
  add(B.head, G.tor(.12, .014, 4, 14), gold, 0, .2, 0, { r: [PI / 2 - .05, 0, 0] }); const coral = M(0xd2503c, { r: .7, n: 'coral' });
  for (let i = 0; i < 7; i++) { const a = (i / 7 - .5) * PI * 1.1; add(B.head, G.cone(.02, .1 + (i % 3) * .035, 4), coral, Math.sin(a) * .12, .245, Math.cos(a) * .12 * .9, { r: [Math.cos(a) * .3, 0, -Math.sin(a) * .3] }); add(B.head, G.sph(.014, 5, 4), M(0xffffff, { r: .2 }), Math.sin(a) * .12, .21, Math.cos(a) * .12); }
  // translucent gown trains + sleeves
  const gown = 0xcfe2d4, gt = 0xd2a43c;
  const cp = cape(c, { topW: .46, botW: 1.3, len: 1.28, col: gown, trim: gt, lining: 0x9ec8bc, waves: 11, segs: 20, seed: 33, wrap: .2, ragged: .1, flare: .2 }); cp.len = 1.28;
  const cp2 = cape(c, { topW: .5, botW: 1.0, len: 1.0, col: 0x7ab8aa, trim: gt, waves: 8, segs: 16, seed: 19, wrap: .22, back: .16 }); cp2.len = 1.0;
  for (const S of ['L', 'R']) { const fa = B['foreArm_' + S]; add(fa, G.cyl(.06, .15, .32, 8, true), M(gown, { r: .9, d: 1, n: 'bellsleeve' }), 0, -.16, 0); add(fa, G.cyl(.15, .15, .02, 8, true), M(gt, { m: .4, r: .5, d: 1 }), 0, -.32, 0);
    add(fa, G.cyl(.056, .052, .08, 8), gold, 0, -.02, 0); for (let i = 0; i < 3; i++) add(fa, G.cone(.012, .05, 4), gemM(c, 0x3ac0e0, .6), (i - 1) * .08, -.36, .0, { r: [PI, 0, 0] }); }
  // staff: coral crown + pearl
  const stf = new THREE.Group(), gwood = M(0x8a6a3a, { m: .5, r: .4, n: 'gstaff' }); add(stf, G.cyl(.02, .024, 1.95, 6), gwood, 0, .2, 0); for (let i = 0; i < 10; i++) add(stf, G.tor(.026, .008, 4, 8), gold, 0, -.6 + i * .2, 0, { r: [PI / 2, 0, 0] });
  add(stf, G.sph(.07, 8, 6), M(0xf4f0ec, { r: .15, e: 0xdde8ff, ei: .35, n: 'pearl' }), 0, 1.28, 0); for (let i = 0; i < 6; i++) { const a = i / 6 * PI * 2; add(stf, G.cone(.016, .22 + (i % 2) * .06, 4), coral, Math.sin(a) * .06, 1.18, Math.cos(a) * .06, { r: [Math.cos(a) * .6, 0, -Math.sin(a) * .6] }); add(stf, G.cone(.012, .1, 4), coral, Math.sin(a) * .13, 1.34, Math.cos(a) * .13, { r: [Math.cos(a) * .9, 0, -Math.sin(a) * .9] }); }
  for (let i = 0; i < 3; i++) add(stf, G.cone(.014, .05, 4), gemM(c, 0x3ac0e0, .6), (i - 1) * .04, .95, .0, { r: [PI, 0, 0] });
  hold(c, h.hips, 'hand_R', stf, 0, -.05, 0, .12);
  add(B.neck, G.tor(.07, .01, 4, 10), M(0xffffff, { r: .2 }), 0, -.02, .02, { r: [PI / 2, 0, 0] });
  return finalize(c, h.root, { R: 1 }, Bn => { Bn.thigh_L.rotation.set(0, 0, 0); }); } };

// ====================================== LUNARA ======================================
CHARS3.lunara = { name: 'Lunara', sheetKey: 'lunara', build() {
  const c = makeCtx({ name: 'Lunara', fem: true, nobust: true, bulk: .88, sw: .92, skin: 0xedcdbb, hair: 0xcdb6dd, under: 0x2a2530, pants: 0x2e2830, sleeve: 0x2a2530, glove: 0x241c24, boot: 0x3a2a22 });
  const h = humanoid(c), { gold, leather, dleather, brass } = pal(c), { add, G, M, bones: B } = c, purple = 0x7a2fa8, cloakC = 0x2c2438, bone = M(0xc8b090, { m: .3, r: .5, n: 'bonetrim' });
  add(B.chest, G.cyl(.17, .12, .26, 8), M(0x4a3426, { r: .8, n: 'harness' }), 0, .1, .006, { s: [1, 1, .72] }); belt(c, dleather, brass); strapX(c, leather, brass); for (const k of [-1, 1]) add(B.chest, G.box(.04, .3, .02), dleather, k * .1, .1, .12, { r: [0, 0, k * .15] });
  for (const S of ['L', 'R']) { const fa = B['foreArm_' + S], th = B['thigh_' + S], sn = B['shin_' + S]; add(fa, G.cyl(.054, .048, .22, 8), dleather, 0, -.15, 0); add(fa, G.cyl(.056, .056, .02, 8), brass, 0, -.06, 0);
    add(th, G.cyl(.08, .068, .3, 8), c.M(0x3a2a22, { r: .85, n: 'boot' }), 0, -.2, 0); add(sn, G.cyl(.068, .062, .12, 8), dleather, 0, -.04, 0); add(sn, G.cone(.06, .06, 4), brass, 0, -.02, .065, { r: [PI / 2, PI / 4, 0] }); add(sn, G.cyl(.064, .064, .02, 8), brass, 0, -.38, 0); }
  skirt(c, { col: 0x2a2430, trim: purple, len: .55, top: .16, bot: .3, y: -.03, zs: .85, ragged: .22, segs: 18 }); skirt(c, { col: purple, trim: 0x2a2430, len: .46, top: .16, bot: .27, y: -.05, zs: .8, ragged: .2, segs: 14 });
  hair(c, 'long', 0xcdb6dd, { len: .75 }); hood(c, M(cloakC, { r: .95, d: 1, n: 'hood' }), 1.0); add(B.head, G.dome(.07, 8, 3), M(0x1a1420, { r: 1 }), 0, .12, .05, { s: [1, .5, 1] }); moon(c, B.head, bone, .1, 0, .22, .1);
  const cp = cape(c, { topW: .62, botW: 1.3, len: 1.05, col: cloakC, trim: 0xc8b090, lining: purple, waves: 9, ragged: .26, segs: 22, seed: 41, wrap: .15 }); cp.len = 1.05; moon(c, cp.cb, bone, .3, 0, -.45, cp.z(.45) - .024, PI); for (let i = 0; i < 6; i++) { const rr = rnd(i + 5); emblem(c, cp.cb, 'sun', .05, bone, (rr() - .5) * .6, -.2 - rr() * .6, cp.z(.5) - .026, PI); }
  add(B.chest, G.dome(.12, 8, 4), M(0x4a3426, { r: .85 }), .2, .2, 0, { s: [1.1, .6, 1] }); add(B.chest, G.dome(.12, 8, 4), M(0x4a3426, { r: .85 }), -.2, .2, 0, { s: [1.1, .6, 1] }); moon(c, B.chest, brass, .08, 0, .22, .12);
  // quiver w/ purple fletching + bow on back
  const qv = K.quiver(c, M(0x5a3a22, { r: .8 }), brass, 0); for (let i = 0; i < 5; i++) { const x = (i - 2) * .018; add(qv, G.cyl(.004, .004, .22, 4), M(0x8a6a3a), x, .36, (i % 2) * .02); add(qv, G.cone(.02, .07, 3), M(purple, { d: 1 }), x, .46, (i % 2) * .02, { s: [1, 1, .3] }); }
  const bw = K.bow(c, { wood: M(0x7a5028, { r: .6, n: 'bowwood' }), gold: brass, r: .66 }); bw.position.set(.0, .12, -.2); bw.rotation.set(0, 0, .25); B.chest.add(bw);
  const dg = K.dagger(c, brass); dg.position.set(-.18, -.1, .08); dg.rotation.set(PI - .4, 0, .2); B.hips.add(dg); add(B.hips, G.sph(.02, 5, 4), gemM(c, 0xb040ff, .8), -.2, -.2, .1); K.pouch(c, B.hips, 0x4a3426, .2, -.06, .02, 1, brass);
  const fl = K.flame(c, 0xa040ff, 0xe0a0ff, .9); fl.position.set(0, -.2, .02); B.hand_L.add(fl);
  return finalize(c, h.root, {}, Bn => { Bn.upperArm_L.rotation.set(-.6, 0, .45); Bn.foreArm_L.rotation.set(-1.05, 0, 0); }); } };

// ====================================== KESTREL DUSKWING ======================================
CHARS3.kestrel = { name: 'Kestrel Duskwing', sheetKey: 'kestrel', build() {
  const c = makeCtx({ name: 'Kestrel_Duskwing', fem: true, nobust: true, bulk: .92, sw: .95, skin: 0xdba684, hair: 0x4a2e22, under: 0xe9dcc0, pants: 0x3a2c24, sleeve: 0xe9dcc0, glove: 0x3a2a20, boot: 0x4a3220 });
  const h = humanoid(c), { gold, leather, dleather, brass } = pal(c), { add, G, M, bones: B } = c, blue = 0x24429a;
  add(B.chest, G.cyl(.18, .13, .28, 8), M(0x6a4126, { r: .8, n: 'corset' }), 0, .1, .006, { s: [1, 1, .72] }); for (let i = 0; i < 4; i++) add(B.chest, G.box(.28, .018, .02), dleather, 0, -.02 + i * .07, .13, { s: [1, 1, 1] }); belt(c, dleather, brass); belt(c, leather, brass, -.06); strapX(c, leather, brass); strapX(c, dleather, brass);
  for (const S of ['L', 'R']) { const fa = B['foreArm_' + S], sn = B['shin_' + S], th = B['thigh_' + S]; add(fa, G.cyl(.054, .048, .22, 8), dleather, 0, -.15, 0); add(fa, G.cyl(.056, .056, .02, 8), brass, 0, -.05, 0); add(sn, G.sph(.08, 6, 5), c.M(0xaab0b8, { m: .5, r: .4, n: 'kneeguard' }), 0, .0, .055, { s: [1, 1, .6] }); add(sn, G.cyl(.068, .062, .22, 8), dleather, 0, -.28, 0); add(sn, G.cyl(.066, .066, .02, 8), brass, 0, -.2, 0); add(th, G.cyl(.075, .07, .12, 8), leather, 0, -.35, 0); }
  skirt(c, { col: 0x3a2c24, trim: brass.color.getHex(), len: .3, top: .15, bot: .24, y: -.05, zs: .85, ragged: .05, segs: 12 });
  hair(c, 'wavy', 0x4a2e22, { len: .7 }); hood(c, M(blue, { r: .95, d: 1, n: 'hood' }), .85); add(B.head, G.tor(.12, .01, 4, 12), brass, 0, .1, .0, { r: [PI / 2 - .5, 0, 0] });
  const cp = cape(c, { topW: .6, botW: 1.28, len: 1.1, col: blue, trim: 0xc89a4a, lining: 0x1a3074, waves: 10, ragged: .3, segs: 22, seed: 17, wrap: .16 }); cp.len = 1.1; backEmblem(c, cp, 'sun', .22, brass, .22);
  furCollar(c, M(blue, { r: 1, d: 1, n: 'scarf' }), .22, .06); emblem(c, B.chest, 'sun', .08, brass, 0, .22, .125);
  // scroll cases, rope coils, satchel, tools
  for (const [i, x] of [[0, .22], [1, .24]]) add(B.hips, G.cyl(.028, .028, .22, 7), M(i ? 0xb89868 : 0xe0d0a8, { r: .8 }), x - .02, -.04 - i * .02, -.1 + i * .06, { r: [PI / 2 - .2, 0, .15] });
  K.rope(c, B.hips, -.2, -.08, .1); K.rope(c, B.hips, -.22, -.14, .06); K.pouch(c, B.hips, 0x5a3720, .22, -.1, .06, 1.15, brass); add(B.hips, G.box(.18, .2, .08), M(0x6a4126, { r: .85 }), -.0, -.1, -.19);
  add(B.chest, G.cyl(.04, .04, .02, 8), brass, .12, -.05, .13, { r: [PI / 2, 0, 0] });
  const dg = K.dagger(c, brass); dg.scale.setScalar(1.1); hold(c, h.hips, 'hand_R', dg, 0, -.05, 0, PI - .2);
  const hk = new THREE.Group(), iron = M(0x6a6e76, { m: .5, r: .4, n: 'iron' }); add(hk, G.cyl(.012, .012, .2, 6), iron, 0, -.08, 0); add(hk, G.tor(.02, .007, 4, 8), brass, 0, .03, 0); for (let i = 0; i < 3; i++) { const a = i / 3 * PI * 2; add(hk, G.cone(.012, .1, 4), iron, Math.sin(a) * .06, -.2, Math.cos(a) * .06, { r: [Math.cos(a) * -.6, 0, Math.sin(a) * .6] }); }
  for (let i = 0; i < 5; i++) add(hk, G.tor(.016, .006, 4, 6), M(0xb89868), 0, .08 + i * .04, 0, { r: [PI / 2, 0, i * .3] }); hold(c, h.hips, 'hand_L', hk, 0, -.06, 0, 0);
  return finalize(c, h.root, { R: 1 }, Bn => { Bn.upperArm_R.rotation.set(-.15, 0, -.15); Bn.foreArm_R.rotation.set(-.5, 0, 0); }); } };

// ====================================== MOSSGUT (moss troll) ======================================
CHARS3.mossgut = { name: 'Mossgut', sheetKey: 'mossgut', build() {
  const skinC = 0x7d8c4a, c = makeCtx({ name: 'Mossgut', bulk: 1.8, sw: 1.38, skin: skinC, hair: 0x4f7a2a, under: skinC, pants: 0x6f7d40, sleeve: skinC, glove: skinC, boot: 0x6f7d40 });
  const h = humanoid(c), { gold, leather, dleather } = pal(c), { add, G, M, bones: B } = c, SK = M(skinC, { r: .9, n: 'trollskin' }), bark = M(0x6a4a2a, { r: 1, n: 'bark' }), bark2 = M(0x4a3420, { r: 1, n: 'bark2' }), wood = M(0xb08a58, { r: .9, n: 'woodtrim' });
  noHead(c); const hd = B.head;
  add(hd, G.sph(.125, 9, 7), SK, 0, .09, .0, { s: [1.2, .95, 1.0] }); add(hd, G.box(.2, .09, .16), SK, 0, -.01, .06); add(hd, G.box(.22, .045, .1), M(0x5f6c36, { r: .9 }), 0, .125, .09, { r: [.2, 0, 0] });
  add(hd, G.sph(.04, 7, 5), M(0xc8704a, { r: .8, n: 'trollnose' }), 0, .06, .15, { s: [1.2, 1, 1] });
  for (const k of [-1, 1]) { add(hd, G.cone(.018, .09, 5), M(0xf0e8d0, { r: .6 }), k * .065, .015, .125, { r: [-.1, 0, k * .1] }); add(hd, G.sph(.014, 5, 4), M(0xf0d040, { e: 0xf0d040, ei: .5 }), k * .05, .115, .12); add(hd, G.cone(.04, .14, 4), SK, k * .15, .12, -.01, { r: [0, 0, -k * 1.35], s: [1, 1, .5] }); add(hd, G.sph(.028, 5, 4), SK, k * .09, .02, .1, { s: [1, 1, .7] }); }
  mossBlob(c, hd, 7, .09, .02, .08, 0, .2, -.02, .05, 5); hang(c, hd, 8, .1, .0, -.08, .12, 0x5b7a2a, 3); mush(c, hd, .05, .2, .0, .9); mush(c, hd, -.06, .21, -.04, .7);
  // belly + torso mass, shoulders of bark & moss
  add(B.spine, G.sph(.25, 9, 7), SK, 0, -.02, .06, { s: [1.2, 1.05, 1.0] }); add(B.chest, G.sph(.25, 9, 7), SK, 0, .06, .02, { s: [1.3, 1.0, .95] });
  for (const k of [-1, 1]) { const sh = B['shoulder_' + (k > 0 ? 'L' : 'R')]; add(sh, G.dome(.14, 8, 4), bark, k * .06, .0, 0, { s: [1.1, .6, 1.1], r: [0, 0, -k * .25] }); for (let i = 0; i < 6; i++) add(sh, G.box(.05, .17, .03), i % 2 ? bark : bark2, k * (.0 + i * .035), -.08, .1 - i * .035, { r: [.2, 0, -k * .5] });
    mossBlob(c, sh, 6, .12, .02, .12, k * .06, .06, 0, .06, 11 + k); mush(c, sh, k * .08, .09, .0, 1.1); mush(c, sh, k * .0, .08, -.1, .8); hang(c, sh, 6, .13, -.05, .0, .15, 0x4f7a2a, 8 + k); }
  mossBlob(c, B.chest, 12, .27, .05, .15, 0, .22, -.12, .075, 21); for (let i = 0; i < 6; i++) mush(c, B.chest, Math.sin(i * 1.4) * .2, .26, -.14 - Math.cos(i * 1.4) * .06, .8 + (i % 3) * .2, i % 2 ? 0xe06a2e : 0xd8502a); hang(c, B.chest, 14, .24, .12, -.2, .2, 0x5b7a2a, 31);
  mossBlob(c, B.hips, 5, .2, .03, .12, 0, -.02, 0, .06, 7);
  K.furCollar(c, M(0x4f7a2a, { r: 1, n: 'mossring' }), .22, .06); add(B.chest, G.cyl(.06, .06, .02, 10), wood, 0, .15, .21, { r: [PI / 2, 0, 0] }); emblem(c, B.chest, 'spiral', .08, M(0x5a3a22, { r: .8 }), 0, .15, .222); for (let i = 0; i < 5; i++) add(B.chest, G.cyl(.03, .03, .015, 8), wood, (i - 2) * .06, .2 - Math.abs(i - 2) * .02, .19, { r: [PI / 2, 0, 0] });
  belt(c, M(0x6a4126, { r: .9 }), wood, .0, .17); add(B.spine, G.cyl(.05, .05, .02, 10), wood, 0, -.03, .22, { r: [PI / 2, 0, 0] });
  const lc = tabard(c, { w: .26, len: .6, col: 0x7a5230, trim: 0xb08a4a, emblem: 'ornate', point: .12, z: .24, y: -.02 }); hang(c, B.hips, 12, .2, -.04, .2, .25, 0x7a5230, 9);
  for (const S of ['L', 'R']) { for (let i = 0; i < 3; i++) { ropeRing(c, B['foreArm_' + S], -.06 - i * .06, .08); ropeRing(c, B['shin_' + S], -.1 - i * .07, .095); } mossBlob(c, B['foreArm_' + S], 2, .04, .05, .04, 0, -.1, 0, .05, 3 + S.length); mossBlob(c, B['shin_' + S], 3, .06, .08, .06, 0, -.2, 0, .055, 2); mush(c, B['shin_' + S], .09, -.2, .02, .8);
    add(B['foot_' + S], G.box(.16, .07, .3), SK, 0, -.01, .08); for (let i = -1; i <= 1; i++) add(B['foot_' + S], G.sph(.035, 5, 4), SK, i * .05, -.01, .24, { s: [1, .8, 1] }); add(B['thigh_' + S], G.sph(.15, 7, 5), SK, 0, -.05, 0); add(B['thigh_' + S], G.dome(.13, 7, 3), bark2, 0, -.17, .08, { s: [1, .7, 1] }); }
  // club
  const cb = new THREE.Group(); add(cb, G.cyl(.05, .075, 1.25, 7), bark2, 0, .35, 0); add(cb, G.cyl(.1, .09, .5, 7), bark, 0, .95, 0); for (const [x, y, z, s] of [[.1, .95, .02, 1], [-.08, 1.12, .05, .8], [.03, .82, -.1, .9]]) add(cb, G.oct(.09 * s), M(0x8a8a82, { r: .9, n: 'stone' }), x, y, z, { s: [1, .9, 1.1] });
  for (let i = 0; i < 4; i++) add(cb, G.tor(.1, .016, 4, 10), M(0x8a6a3a, { r: .95 }), 0, .78 + i * .1, 0, { r: [PI / 2, 0, 0] }); mossBlob(c, cb, 4, .08, .1, .08, 0, .9, 0, .05, 5); mush(c, cb, .06, 1.18, 0, .9); hold(c, h.hips, 'hand_R', cb, 0, -.07, 0, 1.3, 0, 0);
  const rig = finalize(c, h.root, { R: 1 }, Bn => { Bn.spine.rotation.set(.12, 0, 0); Bn.neck.rotation.set(-.12, 0, 0); Bn.upperArm_L.rotation.set(.1, 0, .3); Bn.upperArm_R.rotation.set(-.2, 0, -.3); Bn.foreArm_R.rotation.set(-.9, 0, 0); Bn.thigh_L.rotation.set(0, 0, -.1); Bn.thigh_R.rotation.set(0, 0, .1); });
  rig.root.scale.setScalar(1.12); return rig; } };

// ====================================== CAPTAIN HEARTH ======================================
CHARS3.hearth = { name: 'Captain Hearth', sheetKey: 'hearth', build() {
  const c = makeCtx({ name: 'Captain_Hearth', bulk: 1.18, sw: 1.12, skin: 0xd9a07a, hair: 0x6a4a2a, under: 0xe2d4b8, pants: 0x4a3a2c, sleeve: 0xe9dcc0, glove: 0x4a3020, boot: 0x5a3a20 });
  const h = humanoid(c), { gold, leather, dleather, brass } = pal(c), { add, G, M, bones: B } = c, red = 0xa8302a, green = 0x3e6a42, iron = M(0x4a4e56, { m: .5, r: .45, n: 'iron' });
  add(B.chest, G.cyl(.22, .17, .27, 8), M(0x6a4126, { r: .85, n: 'vest' }), 0, .1, .006, { s: [1, 1, .72] }); belt(c, dleather, gold); belt(c, leather, gold, -.07); strapX(c, dleather, gold); strapX(c, leather, brass);
  hair(c, 'messy', 0x6a4a2a); add(B.head, G.sph(.085, 7, 5), M(0x6a4a2a, { r: 1, n: 'beard' }), 0, -.02, .05, { s: [1.15, 1.1, .85] }); add(B.head, G.box(.12, .03, .03), M(0x6a4a2a), 0, .045, .105);
  furCollar(c, M(red, { r: .95, d: 1, n: 'scarf' }), .22, .06); add(B.chest, G.dome(.14, 8, 4), M(green, { r: .95, d: 1 }), .22, .2, 0, { s: [1.1, .6, 1.1] }); add(B.chest, G.dome(.14, 8, 4), M(green, { r: .95, d: 1 }), -.22, .2, 0, { s: [1.1, .6, 1.1] });
  emblem(c, B.chest, 'sun', .09, gold, -.09, .22, .13); for (let i = 0; i < 2; i++) tassel(c, B.chest, 0xd2a43c, -.11 + i * .03, .17, .135);
  tabard(c, { w: .24, len: .58, col: 0xe9dcc0, trim: M(0xd2603a, { m: .2, r: .6 }), emblem: 'sun', point: .08, z: .2, y: -.03 });
  skirt(c, { col: 0x4a3a2c, trim: 0x2a2018, len: .3, top: .17, bot: .27, y: -.05, zs: .9, ragged: .04, segs: 12 });
  const cp = cape(c, { topW: .62, botW: 1.3, len: .98, col: green, trim: 0xb8402e, lining: red, waves: 9, ragged: .1, segs: 18, seed: 27, wrap: .16 }); cp.len = .98;
  // backpack + bedroll + pot
  add(B.chest, G.box(.34, .3, .15), M(0x6a4126, { r: .85 }), 0, .02, -.3); add(B.chest, G.box(.36, .12, .17), M(0x5a3720, { r: .85 }), 0, -.15, -.3); add(B.chest, G.cyl(.08, .08, .42, 10), M(0xc8b890, { r: .9, n: 'bedroll' }), 0, .26, -.3, { r: [0, 0, PI / 2] }); for (const k of [-1, 1]) add(B.chest, G.box(.05, .26, .02), dleather, k * .1, .28, -.3, { s: [1, 1, 1] }); for (const x of [-.1, .1]) add(B.chest, G.box(.05, .04, .03), gold, x, .1, -.385);
  for (const x of [-.12, .12]) add(B.chest, G.box(.045, .3, .02), dleather, x, .08, .12, { r: [0, 0, 0] });
  add(B.hips, G.cyl(.075, .09, .1, 8), iron, -.26, -.05, .05); add(B.hips, G.tor(.08, .008, 4, 10), iron, -.26, .0, .05, { r: [PI / 2, 0, 0] }); for (let i = 0; i < 2; i++) add(B.hips, G.cyl(.032, .028, .06, 7), M(0xaeb4bc, { m: .6, r: .3, n: 'tin' }), .22 + i * .06, -.08, .08);
  for (let i = 0; i < 3; i++) add(B.hips, G.tor(.02, .006, 4, 8), gold, .02 + i * .035, -.1 - i * .01, .17, { r: [0, i * .6, 0] }); K.pouch(c, B.hips, 0x5a3720, .22, -.05, -.05, 1.1, gold);
  for (const S of ['L', 'R']) { const fa = B['foreArm_' + S], sn = B['shin_' + S]; add(fa, G.cyl(.062, .055, .2, 8), dleather, 0, -.15, 0); add(fa, G.cyl(.065, .065, .02, 8), gold, 0, -.06, 0); add(sn, G.cyl(.09, .08, .12, 8), leather, 0, -.1, 0); add(sn, G.cyl(.092, .092, .02, 8), gold, 0, -.14, 0); add(sn, G.cyl(.085, .075, .2, 8), c.M(0x5a3a20, { r: .85, n: 'boot' }), 0, -.3, 0); add(sn, G.cyl(.09, .09, .02, 8), gold, 0, -.36, 0); }
  const ln = new THREE.Group(), lg = K.lantern(c, gold); lg.scale.setScalar(2.3); ln.add(lg); for (const [x, z] of [[1, 1], [-1, 1], [1, -1], [-1, -1]]) add(ln, G.cyl(.006, .006, .21, 4), gold, x * .06, 0, z * .06); add(ln, G.tor(.04, .006, 4, 8), gold, 0, .22, 0); add(ln, G.cone(.055, .04, 6), gold, 0, .18, 0); add(ln, G.cyl(.065, .065, .014, 6), gold, 0, -.11, 0);
  add(ln, G.sph(.04, 6, 5), M(0xffd27a, { e: 0xffb84a, ei: 1.5, a: .8 }), 0, 0, 0); hold(c, h.hips, 'hand_L', ln, 0, -.2, 0, 0);
  return finalize(c, h.root, { L: 1 }, Bn => { Bn.upperArm_L.rotation.set(-.3, 0, .6); Bn.foreArm_L.rotation.set(-1.0, 0, .0); }); } };

// ====================================== ELDER WREN (owl wizard) ======================================
CHARS3.wren = { name: 'Elder Wren', sheetKey: 'wren', build() {
  const navy = 0x24336e, tan = 0xb0865a, c = makeCtx({ name: 'Elder_Wren', bulk: 1.12, sw: 1.04, skin: tan, hair: tan, under: 0xe9dcc0, pants: 0x3a2c24, sleeve: navy, glove: 0xa87a4a, boot: 0xb08858 });
  const h = humanoid(c), { gold, leather, dleather } = pal(c), { add, G, M, bones: B } = c, cream = M(0xe8d8b8, { r: 1, n: 'owlcream' }), ft = M(tan, { r: 1, n: 'owlfeather' }), ftd = M(0x8a6240, { r: 1, n: 'owlfeather2' });
  noHead(c); const hd = B.head;
  add(hd, G.sph(.14, 10, 8), ft, 0, .1, 0, { s: [1.18, 1.0, 1.0] }); for (const k of [-1, 1]) { add(hd, G.sph(.075, 8, 6), cream, k * .06, .105, .09, { s: [1, 1.05, .45] }); add(hd, G.sph(.036, 8, 6), M(0xe8a020, { r: .3, e: 0xe8a020, ei: .35, n: 'owleye' }), k * .06, .115, .125, { s: [1, 1, .5] }); add(hd, G.sph(.017, 6, 5), M(0x0a0806), k * .06, .115, .14); add(hd, G.box(.075, .014, .02), ftd, k * .06, .17, .115, { r: [0, 0, k * -.35] }); }
  add(hd, G.cone(.026, .07, 5), M(0xc8742a, { r: .5, n: 'beak' }), 0, .06, .145, { r: [PI / 2 + .45, 0, 0] }); add(hd, G.box(.03, .06, .02), cream, 0, .1, .13);
  for (let i = 0; i < 8; i++) { const a = (i / 8 - .5) * PI * 1.1; add(hd, G.cone(.02, .06, 4), i % 2 ? ft : ftd, Math.sin(a) * .15, .11, -.02 + Math.cos(a) * .02, { r: [0, 0, -Math.sin(a) * 1.2], s: [1, 1, .5] }); }
  K.furCollar(c, cream, .2, .065); for (let i = 0; i < 7; i++) { const a = i / 7 * PI * 2; add(B.neck, G.cone(.025, .07, 4), cream, Math.sin(a) * .09, -.01, Math.cos(a) * .09, { r: [PI + Math.cos(a) * .6, 0, -Math.sin(a) * .6], s: [1, 1, .5] }); }
  // wizard hat
  const hm = M(navy, { r: .9, n: 'hat' }); add(hd, G.cyl(.23, .23, .02, 14), hm, 0, .2, 0, { r: [-.08, 0, 0] }); add(hd, G.cone(.15, .3, 12), hm, 0, .35, -.01, { r: [-.08, 0, 0] }); add(hd, G.cone(.07, .2, 8), hm, 0, .53, -.06, { r: [-.5, 0, 0] }); add(hd, G.tor(.15, .014, 4, 14), gold, 0, .23, 0, { r: [PI / 2 - .08, 0, 0] });
  emblem(c, hd, 'sun', .1, gold, 0, .3, .14, 0); for (const k of [-1, 1]) { add(hd, G.cyl(.012, .012, .1, 4), gold, k * .22, .14, 0); add(hd, G.cyl(.03, .03, .01, 8), gold, k * .22, .08, 0, { r: [0, 0, PI / 2] }); add(hd, G.cone(.014, .05, 4), M(navy, { r: .9 }), k * .22, .03, 0, { r: [PI, 0, 0] }); }
  // robe
  skirt(c, { col: navy, trim: 0xd2a43c, len: .95, top: .2, bot: .44, y: -.03, zs: .9, ragged: .05, segs: 16 });
  const tb = tabard(c, { w: .26, len: .86, col: 0xe9dcc0, trim: gold, point: .1, z: .24, y: -.05, tilt: -.03 }); moon(c, tb, gold, .12, 0, -.3, .02); moon(c, tb, gold, .1, 0, -.62, .02); emblem(c, tb, 'sun', .07, gold, 0, -.46, .02);
  add(B.chest, G.cyl(.22, .17, .27, 8), M(navy, { r: .9 }), 0, .1, .006, { s: [1, 1, .72] }); belt(c, leather, gold); strapX(c, dleather, gold);
  const cp = cape(c, { topW: .6, botW: 1.25, len: .98, col: navy, trim: 0xd2a43c, lining: 0x1a2658, waves: 9, segs: 16, seed: 31, wrap: .15 }); cp.len = .98; backEmblem(c, cp, 'sun', .5, gold, .35); moon(c, cp.cb, gold, .22, 0, -.72 * .98, cp.z(.72) - .024, PI);
  for (const S of ['L', 'R']) { const fa = B['foreArm_' + S]; add(fa, G.cyl(.065, .16, .32, 8, true), M(navy, { r: .9, d: 1 }), 0, -.15, 0); add(fa, G.cyl(.16, .16, .03, 8, true), M(0xe9dcc0, { m: .3, r: .55, d: 1 }), 0, -.3, 0); for (let i = 0; i < 4; i++) add(B['hand_' + S], G.cone(.014, .08, 4), ft, (i - 1.5) * .03, -.1, .0, { r: [PI, 0, 0] });
    for (let i = -1; i <= 1; i++) add(B['foot_' + S], G.cone(.012, .09, 4), M(0x2a2018, { r: .5 }), i * .035, -.01, .2, { r: [PI / 2 + .3, 0, 0] }); }
  for (const x of [.18, .22]) add(B.hips, G.cyl(.03, .03, .22, 7), M(0xe0d0a8, { r: .8 }), x, -.05, .02, { r: [.2, 0, .1] }); K.pouch(c, B.hips, 0x5a3720, -.2, -.07, .05, 1.1, gold);
  const bk = K.book(c, navy, gold, .17, .23); bk.position.set(.14, .02, .2); bk.rotation.set(0, 0, .15); B.chest.add(bk); emblem(c, bk, 'sun', .1, gold, 0, 0, .03);
  const st = K.staff(c, 'none', { gold, wood: M(0x6a4528, { r: .7 }), len: 1.95, twist: true, wood2: 0x8a6030 }); add(st.top, G.tor(.1, .016, 4, 12, PI * 1.2), M(0x6a4528, { r: .7 }), 0, .1, 0, { r: [0, PI / 2, -.3] });
  const lg = K.lantern(c, gold); lg.scale.setScalar(2.6); lg.position.set(0, .04, .12); st.top.add(lg); add(st.top, G.sph(.05, 6, 5), M(0xffd27a, { e: 0xffb84a, ei: 1.5, a: .8 }), 0, .04, .12); hold(c, h.hips, 'hand_R', st.g, 0, -.05, 0, .1);
  const rig = finalize(c, h.root, { R: 1 }, Bn => { Bn.upperArm_L.rotation.set(-.5, 0, -.1); Bn.foreArm_L.rotation.set(-1.25, -.3, 0); }); rig.root.scale.setScalar(.84); return rig; } };

// ====================================== THRAIN ANVILBEARD (dwarf) ======================================
CHARS3.thrain = { name: 'Thrain Anvilbeard', sheetKey: 'thrain', build() {
  const c = makeCtx({ name: 'Thrain_Anvilbeard', bulk: 1.5, sw: 1.38, skin: 0xe0a888, hair: 0xe8e4dc, under: 0x7a4a24, pants: 0x4a3a2c, sleeve: 0x4a4e58, glove: 0x5a3a20, boot: 0x4a2e1c });
  const h = humanoid(c), { gold, leather, dleather, steel } = pal(c), { add, G, M, bones: B } = c, blue = 0x24429a, wh = M(0xece8de, { r: 1, n: 'beard' }), brown = M(0x7a4a24, { r: .85, n: 'apronbrown' });
  hair(c, 'long', 0xe8e4dc, { len: .5 }); hair(c, 'swept', 0xe8e4dc); add(B.head, G.sph(.06, 6, 5), M(0xdc9878), 0, .08, .1, { s: [1.2, 1, .7] }); add(B.head, G.box(.11, .025, .02), M(0x8a8a88, { r: 1 }), 0, .15, .105, { r: [0, 0, 0] });
  // beard
  add(B.head, G.sph(.1, 8, 6), wh, 0, -.04, .06, { s: [1.2, 1.35, .9] }); add(B.chest, G.cone(.11, .38, 8), wh, 0, .12, .12, { r: [PI, 0, 0], s: [1.2, 1, .6] }); add(B.head, G.box(.2, .04, .04), wh, 0, .05, .1);
  for (const k of [-1, 1]) for (let i = 0; i < 6; i++) { add(B.chest, G.sph(.04 - i * .002, 5, 4), wh, k * .07, .13 - i * .06, .15 + i * .0, { s: [1, 1.3, 1] }); if (i % 2 == 0) add(B.chest, G.tor(.035, .01, 4, 8), gold, k * .07, .13 - i * .06 + .02, .15, { r: [PI / 2, 0, 0] }); }
  for (let i = 0; i < 6; i++) { add(B.head, G.sph(.04 - i * .002, 5, 4), wh, 0, .0 - i * .075, -.14, { s: [1, 1.3, 1] }); if (i % 2 == 0) add(B.head, G.tor(.034, .01, 4, 8), gold, 0, -.02 - i * .075, -.14, { r: [PI / 2, 0, 0] }); }
  // armor
  add(B.chest, G.cyl(.25, .2, .3, 8), brown, 0, .1, .006, { s: [1, 1, .72] }); belt(c, dleather, gold, 0, .21); strapX(c, dleather, gold);
  for (const k of [-1, 1]) { const sh = B['shoulder_' + (k > 0 ? 'L' : 'R')]; add(sh, G.dome(.17, 8, 4), M(blue, { r: .85, n: 'bluep' }), k * .06, .02, 0, { s: [1.2, .8, 1.15], r: [0, 0, -k * .3] }); add(sh, G.tor(.15, .014, 4, 12), gold, k * .06, .02, 0, { r: [PI / 2, 0, -k * .3], s: [1.2, 1.1, 1] }); emblem(c, sh, 'ornate', .1, gold, k * .12, .06, .0, k * PI / 2 - .0); }
  for (const S of ['L', 'R']) { const fa = B['foreArm_' + S], sn = B['shin_' + S], ua = B['upperArm_' + S]; add(fa, G.cyl(.08, .07, .24, 8), brown, 0, -.14, 0); add(fa, G.cyl(.082, .082, .02, 8), gold, 0, -.04, 0); add(fa, G.cyl(.082, .082, .02, 8), gold, 0, -.24, 0); add(ua, G.cyl(.085, .08, .12, 8), M(0x3c4048, { m: .4, r: .6, n: 'mail' }), 0, -.1, 0);
    add(sn, G.cyl(.1, .09, .16, 8), brown, 0, -.1, 0); add(sn, G.cyl(.1, .1, .02, 8), gold, 0, -.18, 0); add(sn, G.cyl(.095, .085, .2, 8), c.M(0x4a2e1c, { r: .85, n: 'boot' }), 0, -.3, 0); add(sn, G.cyl(.098, .098, .02, 8), gold, 0, -.38, 0); add(B['foot_' + S], G.box(.14, .07, .1), M(0xaab0b8, { m: .6, r: .35, n: 'toecap' }), 0, .0, .15); }
  const ap = tabard(c, { w: .3, len: .74, col: 0x7a4a24, trim: gold, emblem: 'ornate', emblem2: 'gear', point: .1, z: .2, y: -.03 });
  skirt(c, { col: 0x4a3a2c, trim: 0x8a6a3a, len: .3, top: .2, bot: .34, y: -.05, zs: .9, ragged: .06, segs: 12 });
  const cp = cape(c, { topW: .66, botW: 1.32, len: 1.02, col: blue, trim: 0xd2a43c, lining: 0x1a3074, waves: 8, segs: 16, seed: 35, wrap: .16 }); cp.len = 1.02; backEmblem(c, cp, 'ornate', .7, gold, .55); emblem(c, B.chest, 'sun', .09, gold, 0, .26, .17);
  for (let i = 0; i < 4; i++) add(B.hips, G.box(.025, .14 + i % 2 * .04, .02), M(0x8a8a90, { m: .6, r: .4 }), -.14 + i * .035, -.14, .21, { r: [.1, 0, (i - 1.5) * .12] }); for (let i = 0; i < 3; i++) add(B.hips, G.tor(.022, .007, 4, 8), gold, .18 + i * .03, -.1 - i * .02, .15, { r: [0, i * .6, 0] }); K.pouch(c, B.hips, 0x5a3720, .24, -.06, .0, 1.1, gold);
  // warhammer (grip at top, head on the ground)
  const wh2 = new THREE.Group(), st = M(0x8a8c92, { m: .5, r: .55, n: 'hammerstone' }); add(wh2, G.cyl(.032, .034, .95, 8), M(0x6a4528, { r: .8, n: 'hammerhaft' }), 0, -.38, 0); for (let i = 0; i < 6; i++) add(wh2, G.tor(.036, .01, 4, 8), gold, 0, .0 - i * .15, 0, { r: [PI / 2, 0, 0] }); add(wh2, G.sph(.045, 6, 5), gold, 0, .1, 0);
  add(wh2, G.box(.4, .24, .24), st, 0, -.92, 0); add(wh2, G.box(.42, .06, .26), M(0x50545a, { m: .6, r: .5 }), 0, -.82, 0); add(wh2, G.box(.42, .06, .26), M(0x50545a, { m: .6, r: .5 }), 0, -1.02, 0); for (const k of [-1, 1]) { add(wh2, G.box(.02, .17, .17), gold, k * .212, -.92, 0); add(wh2, G.box(.02, .1, .1), M(0x2a2a30), k * .214, -.92, 0); }
  hold(c, h.hips, 'hand_R', wh2, 0, -.07, 0, 1.15, 0, 0);
  const rig = finalize(c, h.root, { R: 1 }, Bn => { Bn.upperArm_R.rotation.set(-.55, 0, -.12); Bn.foreArm_R.rotation.set(-.6, 0, 0); Bn.thigh_L.rotation.set(0, 0, -.06); Bn.thigh_R.rotation.set(0, 0, .06); }); rig.root.scale.setScalar(.8); return rig; } };

// ====================================== VALEN HOOFGUARD (centaur; human torso on a horse rig) ======================================
CHARS3.valen = { name: 'Valen Hoofguard', sheetKey: 'valen', build() {
  const c = makeCtx({ name: 'Valen_Hoofguard', bulk: 1.12, sw: 1.1, skin: 0xe2b490, hair: 0xd9a050, under: 0x2b2b30, pants: 0x2a2a30, sleeve: 0x7a7a82, glove: 0x3a2a20, boot: 0x3a2a20 });
  const h = humanoid(c), { steel, gold, leather, dleather } = pal(c), { add, G, M, bones: B, bone } = c, blue = 0x24429a, root = h.root;
  // 1) detach human legs, rename human pelvis 'waist' (horse owns 'hips', 'hSpine', 'hChest')
  for (const S of ['L', 'R']) { const th = B['thigh_' + S]; th.parent.remove(th); for (const n of ['thigh_', 'shin_', 'foot_']) delete B[n + S]; }
  const waist = B.hips; waist.name = 'waist'; B.waist = waist; delete B.hips;
  const hips = bone('hips', root, 0, .98, -.45), hSpine = bone('hSpine', hips, 0, .02, .45), hChest = bone('hChest', hSpine, 0, .05, .42); hChest.add(waist); waist.position.set(0, .2, .12);
  const coat = M(0x7a4a2c, { r: .95, n: 'coat' }), dcoat = M(0x4a2c1c, { r: .95, n: 'coatdark' }), hoof = M(0x2a2018, { r: .6, n: 'hoof' }), fur = M(0xe8d8b0, { r: 1, n: 'feather' }), blond = M(0xe0c080, { r: 1, d: 1, n: 'tailhair' });
  add(hips, G.sph(.31, 10, 8), coat, 0, 0, 0, { s: [.92, 1.0, 1.1] }); add(hSpine, G.sph(.3, 10, 8), coat, 0, 0, 0, { s: [.95, .95, 1.6] }); add(hChest, G.sph(.32, 10, 8), coat, 0, 0, 0, { s: [.95, 1.05, 1.1] }); add(hChest, G.sph(.2, 8, 6), coat, 0, .22, .08, { s: [1, 1, 1] });
  for (const [fb, par, zz] of [['F', hChest, .08], ['B', hips, -.04]]) for (const k of [-1, 1]) { const S = fb + (k > 0 ? 'L' : 'R');
    const th = bone('thigh_' + S, par, k * .15, -.18, zz), sn = bone('shin_' + S, th, 0, -.44, 0), pw = bone('paw_' + S, sn, 0, -.44, 0), f = fb === 'B';
    const l = (p, len, r0, r1, m) => { const g = G.cyl(r0, r1, len, 8); g.translate(0, -len / 2, 0); add(p, g, m); };
    l(th, .44, f ? .11 : .09, .06, coat); add(th, G.sph(f ? .12 : .1, 7, 5), coat, 0, 0, 0); l(sn, .44, .055, .045, dcoat); add(sn, G.sph(.06, 6, 5), dcoat, 0, 0, 0);
    add(sn, G.cyl(.08, .09, .14, 8), fur, 0, -.34, 0); for (let i = 0; i < 6; i++) { const a = i / 6 * PI * 2; add(sn, G.cone(.025, .09, 4), fur, Math.sin(a) * .07, -.36, Math.cos(a) * .07, { r: [PI + Math.cos(a) * .5, 0, -Math.sin(a) * .5], s: [1, 1, .6] }); }
    add(pw, G.cyl(.065, .075, .08, 8), hoof, 0, -.02, .0); if (f) { th.rotation.x = .25; sn.rotation.x = -.45; } }
  // tail
  { let par = hips, y = .06, z = -.3; for (let i = 1; i <= 3; i++) { const t = bone('tail_' + i, par, 0, y, z); t.rotation.x = i === 1 ? -.35 : .05; const g = G.cone(.1 - i * .015, .34, 7); g.translate(0, -.17, 0); g.rotateX(PI); g.translate(0, 0, 0); const gg = G.cyl(.075 - i * .014, .05 - i * .012, .32, 7); gg.translate(0, -.16, 0); add(t, gg, blond, 0, 0, 0, { s: [1, 1, .6] }); add(t, G.cone(.05, .12, 5), blond, 0, -.36, 0, { r: [PI, 0, 0], s: [1, 1, .6] }); par = t; y = -.32; z = 0; } }
  // barding: blue caparison panels, trim, tassels, chest plate
  const bl = M(blue, { r: .9, d: 1, n: 'blue' }), tm = M(0xd2a43c, { m: .4, r: .4, n: 'trim' });
  for (const [bn, w, zz] of [[hips, .6, -.0], [hChest, .6, .02], [hSpine, .5, .0]]) for (const k of [-1, 1]) { add(bn, G.box(.03, .5, w), bl, k * .3, -.12, zz, { r: [0, 0, k * .1] }); add(bn, G.box(.034, .035, w), tm, k * .32, -.37, zz, { r: [0, 0, k * .1] }); if (bn !== hSpine) emblem(c, bn, bn === hips ? 'fleur' : 'lion', .2, tm, k * .325, -.1, zz, k * PI / 2); for (let i = 0; i < 3; i++) tassel(c, bn, 0xd2a43c, k * .33, -.38, zz + (i - 1) * w * .35, .9); }
  add(hSpine, G.box(.5, .035, .6), bl, 0, .3, 0); add(hSpine, G.box(.52, .03, .035), tm, 0, .3, .3); add(hSpine, G.box(.52, .03, .035), tm, 0, .3, -.3);
  add(hChest, G.sph(.2, 8, 6), steel, 0, -.02, .28, { s: [.95, 1.0, .5] }); add(hChest, G.cyl(.06, .06, .02, 10), gold, 0, .0, .38, { r: [PI / 2, 0, 0] }); add(hChest, G.tor(.2, .018, 4, 12), gold, 0, -.02, .26, { s: [1, 1, .5] });
  for (const k of [-1, 1]) { add(hips, G.dome(.1, 7, 3), steel, k * .24, .16, -.2, { s: [1, .5, 1.2] }); }
  // human torso armor (built by hand: platePack expects leg bones)
  const cu = M(0xb4bac2, { m: .4, r: .38, n: 'steel' }); add(B.chest, G.cyl(.24, .18, .3, 8), cu, 0, .1, .006, { s: [1, 1, .72] }); add(B.chest, G.box(.2, .26, .02), bl, 0, .08, .15); emblem(c, B.chest, 'lion', .2, tm, 0, .1, .163); add(B.spine, G.cyl(.18, .16, .2, 8), cu, 0, .02, 0, { s: [1, 1, .72] }); belt(c, dleather, gold, 0, .15);
  add(B.neck, G.cyl(.08, .095, .09, 8), cu, 0, .0, 0); strapX(c, dleather, gold);
  for (const k of [-1, 1]) { const S = k > 0 ? 'L' : 'R', sh = B['shoulder_' + S], ua = B['upperArm_' + S], fa = B['foreArm_' + S], pr = .13;
    add(sh, G.dome(pr, 8, 4), cu, k * .05, .01, 0, { s: [1.2, .85, 1.1], r: [0, 0, -k * .3] }); add(sh, G.dome(pr * .9, 8, 3), cu, k * .08, -.05, 0, { s: [1.1, .8, 1.05], r: [0, 0, -k * .35] }); add(sh, G.dome(pr * .8, 8, 3), tm, k * .1, -.1, 0, { s: [1.05, .7, 1], r: [0, 0, -k * .4] });
    add(ua, G.cyl(.065, .058, .2, 8), cu, 0, -.13, 0); add(fa, G.cyl(.06, .05, .22, 8), cu, 0, -.13, 0); add(fa, G.cyl(.062, .062, .02, 8), tm, 0, -.02, 0); add(fa, G.sph(.062, 6, 5), cu, 0, 0, -.015, { s: [1, .7, 1] }); add(B['hand_' + S], G.box(.08, .1, .07), cu, 0, -.04, 0); }
  hair(c, 'wavy', 0xd9a050, { len: .85 }); hair(c, 'swept', 0xd9a050); for (let i = 0; i < 5; i++) add(B.head, G.sph(.04, 5, 4), M(0xd9a050), .0, -.05 - i * .07, -.15, { s: [1, 1.3, .9] });
  const cp = cape(c, { topW: .5, botW: 1.0, len: .85, col: blue, trim: 0xd2a43c, lining: 0x1a3074, waves: 7, segs: 14, seed: 12, wrap: .12 }); cp.len = .85; backEmblem(c, cp, 'lion', .5, tm, .45);
  // lance with pennant
  const ln = new THREE.Group(); add(ln, G.cyl(.022, .026, 2.5, 6), M(0x6b4528, { r: .7 }), 0, .2, 0); add(ln, G.cone(.05, .28, 4), M(0xc6cdd4, { m: .7, r: .35 }), 0, 1.58, 0); for (const y of [1.4, -.8]) add(ln, G.cyl(.03, .03, .05, 6), tm, 0, y, 0); add(ln, G.cone(.03, .1, 5), tm, 0, -1.07, 0, { r: [PI, 0, 0] });
  for (let i = 0; i < 6; i++) add(ln, G.box(.015, .07, .06), bl, 0, 1.28 - i * .07, -.04 - i * .04 * (i % 2 ? 1 : .6) * 0 - i * .035, { r: [(i % 2 ? .4 : -.4), 0, 0] }); emblem(c, ln, 'fleur', .06, tm, .0, 1.3, -.08, PI / 2);
  hold(c, waist, 'hand_R', ln, 0, -.06, 0, 1.1, 0, 0);
  const upd = (t, mode, R, Bn) => { const ph = t * PI * 2;
    if (mode === 'walk') { for (const [S, o] of [['FL', 0], ['BR', 0], ['FR', PI], ['BL', PI]]) { const p = ph + o; R('thigh_' + S, Math.sin(p) * .5); R('shin_' + S, Math.max(0, Math.cos(p)) * .75); R('paw_' + S, -Math.sin(p) * .15); }
      Bn.hips.position.y += Math.abs(Math.sin(ph)) * .02; R('hSpine', Math.sin(ph) * .015, Math.sin(ph) * .035); R('hChest', 0, -Math.sin(ph) * .03); R('waist', 0, Math.sin(ph) * .03); R('head', 0, Math.sin(ph) * .03); for (let i = 1; i <= 3; i++) R('tail_' + i, Math.sin(ph - i * .7) * .08, 0, Math.sin(ph - i * .7) * .12); R('cape', .1 + Math.sin(ph * 2 - 1) * .05, 0, Math.sin(ph) * .03); R('upperArm_L', Math.sin(ph) * .06); }
    else { R('hChest', Math.sin(ph) * .008); R('waist', 0, Math.sin(ph * .5) * .03); R('head', Math.sin(ph * .5) * .02, Math.sin(ph * .5) * .06); Bn.hips.position.y += Math.sin(ph) * .004; for (let i = 1; i <= 3; i++) R('tail_' + i, Math.sin(ph - i * .6) * .04, 0, Math.sin(ph - i * .6) * .06); R('cape', .02 + Math.sin(ph + 1) * .02); R('thigh_FR', Math.max(0, Math.sin(ph * .5 - 1.2)) * .12); } };
  B.upperArm_L.rotation.set(-.1, 0, .15); B.foreArm_L.rotation.set(-.5, 0, 0); B.upperArm_R.rotation.set(-.3, 0, -.12); B.foreArm_R.rotation.set(-.8, 0, 0);
  return bakeRig(c, root, 'Valen_Hoofguard', upd, { R: 1 }); } };
export const ORDER3 = ['lorian', 'hawk', 'snowy', 'marella', 'lunara', 'kestrel', 'mossgut', 'hearth', 'wren', 'valen', 'thrain'];
