// Varnethryl 3D buildings: 26 low-poly walk-in buildings built from the boss's sheets (guild blue / royal gold, lion crest, blue slate,
// timber + stone). Everything is generated in code (see bldkit.js / bldtex.js). Each builder returns a Builder with .update(hx,hz,dt).
import * as THREE from 'three';
import { Builder, M, GLOW, boxG, cylG, uvScale, TILE, mergeGroup } from './bldkit.js';
import { tex, goldDoorTexture } from './bldtex.js';

// ---------- shared decor ----------
function wins(B, o) { // facade windows: front [[x,y]], side [[z,y]] (both sides), back [[x,y]]
  const { w, d } = B, ww = o.w || .9, hh = o.h || 1.2, key = o.key || 'glass';
  for (const [x, y] of o.front || []) B.win(x, y, d / 2 + .04, 0, ww, hh, key);
  for (const [z, y] of o.side || []) for (const s of [-1, 1]) B.win(s * (w / 2 + .04), y, z, s * Math.PI / 2, ww, hh, key);
  for (const [x, y] of o.back || []) B.win(x, y, -d / 2 - .04, Math.PI, ww, hh, key);
}
const frontWinXs = (B, n = 1) => { const fw = (B.w - B.DW) / 2, out = []; for (const s of [-1, 1]) for (let i = 0; i < n; i++) out.push(s * (B.DW / 2 + fw * (i + .5) / n)); return out; };
function std(spec, ctx, o) { // rect shell + gable roof + chimney + windows + banners + sign
  const B = new Builder(ctx, spec); B.name = o.name; B.rectShell(o);
  const rh = o.roof === false ? 0 : B.roofGable({ rh: o.rh || 3, key: o.roofKey || 'slate', ridge: o.ridge || 'x', over: o.over, endKey: o.endKey || (o.upper === 'stone' || o.upper === 'stoneL' ? o.upper : 'timber') });
  B.rh = rh; const hs = o.hs === undefined ? B.h * .42 : o.hs, up = hs + (B.h - hs) / 2;
  const gy = Math.min(1.9, hs * .7 + .6);
  if (o.windows !== false) wins(B, { front: [...frontWinXs(B, o.wn || 1).map(x => [x, gy]), ...(B.h - hs > 1.8 ? frontWinXs(B, o.wn || 1).map(x => [x, up]) : []), ...(B.h - hs > 1.8 ? [[0, up]] : [])], side: o.sideWins || [[-B.d / 4, gy], [B.d / 4, gy]], back: [[-B.w / 4, gy], [B.w / 4, gy]], w: o.ww, h: o.wh });
  for (const bn of o.banners || []) B.banner(bn[0], bn[1] || up, B.d / 2 + .06, 0, bn[2] || .9, bn[3] || 2.1);
  if (o.sign) { const s = o.sign; B.sign(s[0], s[1], s[2] || B.w / 2 + .1, s[3] || B.h * .62, B.d / 2 + .5, 0); }
  for (const c of o.chimneys || []) B.chimney(c[0], B.h + 1, c[1], c[2] || 2.6, o.chimKey || 'stoneD');
  for (const x of o.dormers || []) B.dormer(x, B.h + (o.dormY || 1.4), o.dormZ === undefined ? B.d * .1 : o.dormZ);
  if (o.cross) B.crossGable(o.cross.x || 0, o.cross.w || B.w * .42, o.cross.rh || rh * .8, o.cross.depth || B.d * .5, o.roofKey || 'slate', o.endKey || 'timber', B.h);
  if (!o.noApron) { B.apron(B.w, B.d); B.bush(-B.w / 2 - .2, B.d / 2 + .5, .6); B.bush(B.w / 2 + .3, B.d / 2 + .6, .7); B.bush(-B.w / 2 - .4, -B.d / 4, .8); B.bush(B.w / 2 + .5, -B.d / 5, .6, '#4b8a3e'); }
  if (o.flowers !== false && B.h - hs > 1.8) for (const x of frontWinXs(B, o.wn || 1)) B.flowers(x, gy - .65, B.d / 2 + .2, 1.0);
  if (o.post) { B.lanternPost(B.w / 2 + 1.0, B.d / 2 + 1.2); B.lanternPost(-B.w / 2 - 1.0, B.d / 2 + 1.2); }
  if (o.extra) o.extra(B);
  if (o.interior) o.interior(B);
  B.radius = Math.hypot(B.w, B.d) / 2; return B.finish();
}

// themed full upper storey with a real flight on one side (free column), furniture on the back strip and opposite wall
function upperStd(B, o) {
  const iw = B.iw, id_ = B.id_, len = Math.min(o.len || 3.4, id_ * 2 - 1.3), sd = o.side === 'L' ? -1 : 1, th = o.theme || 'bed', y = o.y || 3.0;
  B.fullUpper({ y, stair: { cx: sd * (iw - .9), cz: id_ - .45 - len / 2, dir: '-z', len, w: 1.5 }, rooms(U) {
    const x0 = -sd * (iw - 1.1), span = iw * 2 - 2.2;
    if (th === 'bed') { U.bed(x0, -id_ + 1.3); U.bed(x0 + sd * 1.5, -id_ + 1.3); U.chest(0, -id_ + .6, .8); U.tableR(-sd * 1.0, .2, 1.4, .9); U.rugAt(-sd * 1.0, .2, 2.2, 1.8); U.lamp(0, 2.2, 0); }
    if (th === 'lab') { U.shelf(0, -id_ + .3, Math.min(span, 4.4), 0); U.tableR(-sd * 1.2, -.3, 2.2, 1.0); U.crystal(-sd * 1.2 + 1.0, -.3, 1.2, 'a07aff', .25); U.cyl(.5, .4, .6, 'iron', -sd * (iw - 1.2), .3, -id_ + 1.2, U.G.int, 10); U.ccol(-sd * (iw - 1.2), -id_ + 1.2, .6); U.lamp(0, 2.2, 0); U.barrel(-sd * (iw - .5), id_ - .6); }
    if (th === 'store') { for (let i = 0; i < 3; i++) U.crate(x0 + i * (-sd) * .0 - sd * 0 + (i - 1) * 1.1, -id_ + .7, .8); U.barrel(-sd * (iw - .5), 0); U.barrel(-sd * (iw - .5), 1.0); U.sack(-sd * (iw - 1.2), id_ - 1.0); U.sack(-sd * (iw - 1.2), id_ - 1.8); U.hay(0, 0.4, 1.6, 1.2, .8); U.lamp(0, 2.2, 0); }
    if (th === 'hall') { U.tableR(-sd * .8, -.2, 2.6, 1.1); U.shelf(0, -id_ + .3, Math.min(span, 4), 0); U.chest(-sd * (iw - 1.0), -id_ + .9, .9); U.rugAt(-sd * .8, -.2, 3.2, 2.2); U.lamp(0, 2.2, 0); U.lamp(-sd * 2.2, 2.2, 0); }
  } });
}
const hearthRight = B => B.hearth(B.iw - .5, 0, -Math.PI / 2), hearthLeft = B => B.hearth(-B.iw + .5, 0, Math.PI / 2);
function flagBanners(B, xs, y = null, z = null) { for (const x of xs) B.banner(x, y || B.h * .62, z === null ? -B.id_ + .3 : z, 0, 1, 2.2); }

// ---------- 1. Inn ----------
const inn = (spec, ctx) => std(spec, ctx, { name: 'Inn of Varnethryl', w: 11, d: 8, h: 6.6, hs: 3, upper: 'timber', rh: 3.4, ridge: 'z', over: .7, post: true, wn: 1, ww: .95,
  chimneys: [[-3.2, -1.5]], dormers: [-2.2, 2.2], dormZ: 1.2, banners: [[-4.2, 4.3, .8, 1.8]], sign: ['The Gilded Hearth', '🛏', 5.9, 3.7],
  interior(B) { const iw = B.iw, id_ = B.id_;
    B.counter(2.2, -id_ + 1.1, 4, .8); B.shelf(2.2, -id_ + .35, 3.4); for (let i = 0; i < 3; i++) B.cyl(.1, .1, .2, 'iron', 1.0 + i * .8, 1.2, -id_ + 1.1, B.G.int, 8);
    B.table(-1.8, .4); B.table(-.2, 2.2); B.table(-3.4, 2.4); B.barrel(iw - .5, -.2); B.barrel(iw - .5, .8); B.barrel(iw - .5, 1.8); hearthLeft(B);
    B.rugAt(-1.5, 1.2, 4, 3.2); B.lamp(-1.8, 3.6, .4); B.lamp(1.5, 3.6, 1.5); B.banner(-.6, 2.3, -id_ + .3, 0, .9, 1.8);
    // upper floor (sheet: stairs, hallway, bedrooms A/B, private sitting room)
    B.fullUpper({ y: 3.0, stair: { cx: iw - 1.1, cz: id_ - 2.0, dir: '-z', len: 3.6, w: 1.7 }, rooms(U) { const Z = -1.6;
      U.partition(0, Z, iw * 2, 'x', [[-3.4, 1.2], [0, 1.2], [3.4, 1.2]]); U.partition(-1.7, (Z - id_) / 2, id_ + Z, 'z', null); U.partition(1.7, (Z - id_) / 2, id_ + Z, 'z', null);
      U.bed(-iw + 1.6, -id_ + 1.0, 1); U.box(.5, .6, .5, -iw + .5, -id_ + .5); U.chest(-1.0 - 1.0, -id_ + .6, .8); U.rugAt(-3.4, -2.2, 2.2, 2.2); U.lamp(-3.4, 2.4, -2.2);
      U.bed(-.1, -id_ + 1.0, 1); U.box(.5, .6, .5, .8, -id_ + .5); U.chest(-1.2, -id_ + .6, .7); U.rugAt(0, -2.2, 2, 2); U.lamp(0, 2.4, -2.2);
      U.tableR(3.4, -2.5, 1.6, 1.0); U.pew(3.4, -1.9, 1.6); U.shelf(iw - .3, -2.4, 2.0, -1, false); U.rugAt(3.4, -2.4, 2.4, 2.0); U.lamp(3.4, 2.4, -2.4);
      U.table(-3.4, 1.8, .55); U.banner(-iw + .3, 1.5, 1.0, Math.PI / 2, .9, 1.8); U.lamp(-2.2, 2.5, .4);
    } });
  } });

// ---------- 2. Blacksmith ----------
const smithy = (spec, ctx) => std(spec, ctx, { name: 'Blacksmith of Varnethryl', w: 9, d: 8, h: 5.2, hs: 3.6, upper: 'stone', lower: 'stone', rh: 3.2, ridge: 'z', endKey: 'timber', over: .6, flowers: false, extra(B) { B.anvil(-B.w / 2 - 1.0, B.d / 2 + 1.2); B.cyl(.5, .55, .5, 'wood', -B.w / 2 - 1.0, .25, B.d / 2 + 1.2, B.G.ext, 8); B.rack(B.w / 2 + 1.3, B.d / 2 - 1.5, 4, 1); B.barrel; for (let i = 0; i < 3; i++) B.bx(.9, .22, .25, 'wood', B.w / 2 + 1.0, .12 + i * .22, B.d / 2 + 1.6 + (i % 2) * .05, B.G.ext); B.lanternPost(-1.9, B.d / 2 + 1.0); B.add(new THREE.PlaneGeometry(1.8, 2.2), GLOW('ff8a2a', 1.4), 0, 1.3, B.d / 2 - .55, B.G.ext, { shadow: false }); }, chimneys: [[3.2, -2.5, 4.2]], banners: [[3.8, 2.8, .7, 1.6]],
  interior(B) { const iw = B.iw, id_ = B.id_;
    B.box(1.8, 1.0, 1.4, iw - 1.2, -id_ + .9, 'stoneD'); B.add(boxG(1.2, .14, .9, 1), GLOW('ff7a1a', 1.5), iw - 1.2, 1.02, -id_ + .9, B.G.int, { shadow: false }); B.bx(.7, 2.2, .6, 'stoneD', iw - 1.2, 2.1, -id_ + .55, B.G.int);
    B.anvil(-.3, .2); B.rack(-iw + 1.7, -id_ + .35, 6); B.box(2.4, .9, .8, -1.5, -id_ + .6, 'darkWood'); B.barrel(-iw + .5, 1.4); B.barrel(-iw + 1.1, 1.9); B.bx(.5, .7, .5, 'iron', 1.5, .35, 1.0, B.G.int); B.ccol(1.5, 1.0, .5); B.banner(0, 2.4, -id_ + .3, 0, .9, 1.8); B.lamp(-1, 3.6, 1); B.lamp(2.2, 3.6, -1);
    for (let i = 0; i < 2; i++) B.bx(.45, 1.7, .08, 'iron', -iw + .25 + i * .6, 1.8, id_ - .1, B.G.int, { shadow: false }); B.rugAt(-.5, 1.5, 3, 2.2, 'rug'); upperStd(B, { theme: 'store', y: 3.4 });
  } });

// ---------- 3. Apothecary ----------
const apothecary = (spec, ctx) => std(spec, ctx, { name: 'Apothecary of Varnethryl', w: 8, d: 7, h: 6.0, hs: 2.6, upper: 'timber', rh: 3.2, ridge: 'z', over: .7, chimneys: [[-2.4, -1.5], [2.4, -1.5]], dormers: [0], dormY: 1.2, dormZ: 1.5, sign: ['Apothecary', '⚗', 4.3, 3.3],
  interior(B) { const iw = B.iw, id_ = B.id_;
    B.shelf(0, -id_ + .3, 5, 0); B.shelf(-iw + .3, -.5, 3.2, 1); B.shelf(iw - .3, -1.9, 2.0, -1); B.tableR(0, .6, 2.2, 1.1); for (let i = 0; i < 4; i++) B.cyl(.09, .09, .22, ['#4a9a6a', '#b5452f', '#6a4aa8', '#d8aa3a'][i], -.7 + i * .45, 1.06, .6, B.G.int, 6, { shadow: false });
    B.counter(-iw + 1.4, id_ - 1.0, 2, .7); B.barrel(-iw + .5, 1.8);
    for (let i = 0; i < 6; i++) B.add(new THREE.ConeGeometry(.18, .7, 5), M('#5a8a3a'), -2.4 + i * .95, 3.7, -.5 + (i % 2) * 1.5, B.G.int, { shadow: false });
    B.lamp(-1.5, 3.5, 1); B.lamp(1.5, 3.5, 1); B.rugAt(0, 1.8, 3, 2, 'rug'); upperStd(B, { theme: 'lab', y: 3.0 });
  } });

// ---------- 4. Temple ----------
function temple(spec, ctx) {
  const B = new Builder(ctx, spec); B.name = 'Temple of Varnethryl'; B.rectShell({ w: 14, d: 22, h: 9, hs: 0, upper: 'stoneL', lower: 'stoneL', DW: 3.2, DH: 4.2, floor: 'marbleInlay', posts: false });
  const { w, d, h } = B; B.roofGable({ rh: 4.4, key: 'slate', ridge: 'z', over: .5, endKey: 'stoneL' });
  for (const sx of [-1, 1]) { // twin front towers with blue spires
    B.bx(3, h + 3, 3, 'stoneL', sx * (w / 2 - .2), (h + 3) / 2, d / 2 - .2, B.G.ext); B.col(sx * (w / 2 - .2), d / 2 - .2, 3, 3);
    B.cone(2.4, 8.4, 'slate', sx * (w / 2 - .2), h + 3, d / 2 - .2, B.G.ext, 4); B.bx(.12, 1.4, .12, 'gold', sx * (w / 2 - .2), h + 11.5, d / 2 - .2, B.G.ext);
    B.win(sx * (w / 2 - .2), h - .5, d / 2 + 1.35, 0, .8, 2.4, 'stained'); B.banner(sx * (w / 2 - .2), 4.2, d / 2 + 1.35, 0, 1.0, 2.8);
    B.bx(.8, 6.2, .8, 'stoneL', sx * (w / 2 + .3), 3.1, -d / 4, B.G.ext); B.bx(.8, 6.2, .8, 'stoneL', sx * (w / 2 + .3), 3.1, d / 4 - 2, B.G.ext);
  }
  B.win(0, 6.7, d / 2 + .06, 0, 3.2, 3.8, 'stained'); B.bx(3.6, .3, .3, 'gold', 0, 4.7, d / 2 + .1, B.G.ext);    // rose window frame
  for (const z of [-5, 0, 5]) for (const s of [-1, 1]) B.win(s * (w / 2 + .06), 5.2, z, s * Math.PI / 2, 1.1, 3.2, 'stained');
  for (let i = 0; i < 5; i++) B.bx(w * .5 + i * .8, .3, 1, 'stoneL', 0, .15 + i * 0 - 0.0, d / 2 + 2.2 - i * 0 + i * .5, B.G.ext); // steps
  for (const s of [-1, 1]) { B.bx(.7, 1.8, .7, 'stoneL', s * 2.6, 1.2, d / 2 + 2.6, B.G.ext); B.bx(.5, .7, .5, 'gold', s * 2.6, 2.4, d / 2 + 2.6, B.G.ext); }
  B.bx(.5, 3.6, .1, 'carpet', 0, 2.4, d / 2 + .08, B.G.ext);
  { // cathedral flourishes (see Temple reference): steep central gable with glowing arched window, ridge pinnacles, lions + statues on pedestals, tall banners
    const zf = d / 2; const gs = new THREE.Shape(); gs.moveTo(-4.2, 0); gs.lineTo(0, 7.2); gs.lineTo(4.2, 0); gs.lineTo(-4.2, 0); const gg = new THREE.ExtrudeGeometry(gs, { depth: .9, bevelEnabled: false });
    B.add(gg, B.cm('stoneL'), 0, h - .2, zf - .2, B.G.ext); B.add(archRingGeo(0, 1.9, 1.5, 4.2, .5), M('gold'), 0, h + .1, zf + .7, B.G.ext); B.add(archFillGeo(0, 1.5, 4.2, 0), GLOW('2a62d8', .8), 0, h + .1, zf + .72, B.G.ext, { shadow: false });
    B.cone(.55, 3.2, 'slate', 0, h + 7.1, zf + .2, B.G.ext, 4); B.bx(.1, 1.2, .1, 'gold', 0, h + 10.9, zf + .2, B.G.ext);
    for (let i = 0; i < 5; i++) { const z = -d / 2 + 2.5 + i * (d - 5) / 4; for (const s of [-1, 1]) B.cone(.42, 2.6, 'slate', s * (w / 2 - .4), h + 3.1, z, B.G.ext, 4); }
    for (const s of [-1, 1]) { const x = s * 3.4, z = zf + 3.2; B.bx(1.4, 1.3, 1.4, 'stoneL', x, .65, z, B.G.ext); B.bx(.9, .6, 1.5, 'stoneL', x, 1.6, z, B.G.ext); B.add(new THREE.SphereGeometry(.42, 8, 6), B.cm('stoneL'), x, 2.0, z + .7, B.G.ext); B.bx(.35, .12, .6, 'stoneL', x, 1.35, z + .5, B.G.ext);
      const sx = s * (w / 2 + 3.2), sz = zf + 2.6; B.bx(1.4, 1.6, 1.4, 'stoneL', sx, .8, sz, B.G.ext); B.bx(.7, 2.6, .5, 'stoneL', sx, 2.9, sz, B.G.ext); B.add(new THREE.SphereGeometry(.34, 8, 6), B.cm('stoneL'), sx, 4.4, sz, B.G.ext);
      B.banner(s * 5.0, 4.8, zf + .08, 0, 1.2, 3.8); B.banner(s * 2.9, 4.8, zf + .08, 0, 1.0, 3.2); B.ccol(x, z, .9); B.ccol(sx, sz, .9); }
    for (let i = 0; i < 5; i++) B.bx(w * .7 + i * 1.2, .1, 1.1, 'stoneL', 0, .35, zf + 4.6 + i * .6, B.G.ext, { shadow: false });
  }
  for (const z of [-8, -3.5, 1, 5.5]) for (const s of [-1, 1]) { const x = s * (w / 2 + .5); B.bx(.9, h + 1.4, .9, 'stoneL', x, (h + 1.4) / 2, z, B.G.ext); B.cone(.62, 2.6, 'slate', x, h + 1.4, z, B.G.ext, 4); B.bx(.7, .22, 1.6, 'stoneL', s * (w / 2 + .1), h - 1.2, z + 2.2, B.G.ext).rotation.z = s * .5; }
  for (const s of [-1, 1]) for (const [dx, dz] of [[-.9, -.9], [.9, -.9], [-.9, .9], [.9, .9]]) B.cone(.34, 1.5, 'slate', s * (w / 2 - .2) + dx, h + 3, d / 2 - .2 + dz, B.G.ext, 4);
  B.statue(-4.2, d / 2 + 2.6, 1); B.statue(4.2, d / 2 + 2.6, 1); B.gable(6.2, 2.4, 3.4, 0, h + .2, d / 2 - 1.2, 'slate', B.G.roof, false, 0, 'stoneL'); B.banner(0, h + 1.4, d / 2 + .06, 0, 1.2, 1.8, B.G.roof);
  const iw = B.iw, id_ = B.id_;
  B.rugAt(0, 0, 3, d - 4, 'carpet'); B.add(boxG(3, .02, d - 4, 3), M('carpet'), 0, .09, 0, B.G.int, { shadow: false });
  for (let i = 0; i < 5; i++) for (const s of [-1, 1]) B.pew(s * 3, -2.5 + i * 1.7 + 2.5, 2.8);
  for (const z of [-6, -1.5, 3, 7.5]) for (const s of [-1, 1]) B.pillar(s * 4.8, z, .45, h - .6, 'stoneL');
  B.bx(5, .5, 2.4, 'stoneL', 0, .25, -id_ + 1.4, B.G.int); B.bx(3.2, 1.1, 1, 'gold', 0, 1.0, -id_ + 1.3, B.G.int); B.col(0, -id_ + 1.4, 5, 2.4); B.banner(0, 4.2, -id_ + .3, 0, 2.2, 4.4); B.win(-2.8, 5, -id_ + .1, 0, 1.2, 3, 'stained'); B.win(2.8, 5, -id_ + .1, 0, 1.2, 3, 'stained');
  B.crystal(-5.6, -id_ + 1.6, 1.5, '6aa8ff', .35); B.crystal(5.6, -id_ + 1.6, 1.5, '6aa8ff', .35);
  B.cyl(1.1, 1.3, .5, 'stoneL', 0, .25, 4.5, B.G.int, 16); B.add(new THREE.CylinderGeometry(.9, .9, .06, 16), M('water'), 0, .55, 4.5, B.G.int, { shadow: false }); B.cyl(.12, .12, 1.2, 'stoneL', 0, 1.1, 4.5, B.G.int, 8); B.ccol(0, 4.5, 1.35);
  // real upper galleries: side balconies over the aisles + choir loft across the back, reached by a flight on each side of the entrance
  { const GY = 4.4, gx = 4.0; const S = s => ({ cx: s * (iw - .9), cz: 8.4 - 2.3, ang: Math.PI, len: 4.6, w: 1.5, l0: 0, y0: 0, l1: 1, y1: GY });
    B.stairs(S(-1)); B.stairs(S(1));
    B.upperFloor(1, GY, [[-iw, -gx, -id_, 3.9], [gx, iw, -id_, 3.9], [-iw, iw, -id_, -id_ + 2.4]], { key: 'floorPlank' });
    B.onFloor(1, GY, U => { for (const s of [-1, 1]) { U.pew(s * 5.4, -4, 1.8); U.pew(s * 5.4, -1.5, 1.8); U.lamp(s * 4.6, 2.6, 2.0); } U.banner(0, 1.8, -id_ + .4, 0, 2.0, 2.4); U.chest(0, -id_ + 1.0, .9); }); }
  B.radius = 15; return B.finish();
}

// ---------- 5. Training Hall ----------
const training = (spec, ctx) => std(spec, ctx, { name: 'Training Hall of Varnethryl', w: 16, d: 11, h: 6.2, hs: 2.6, upper: 'timber', rh: 3.6, ridge: 'x', over: .8, DW: 3.4, DH: 3.4, floor: 'floorStone', wn: 2, banners: [[-3.2, 4, .9, 2], [3.2, 4, .9, 2]],
  interior(B) { const iw = B.iw, id_ = B.id_;
    B.rugAt(0, 0, 6, 6, 'carpet'); B.add(new THREE.CylinderGeometry(1.4, 1.4, .02, 20), M('gold'), 0, .1, 0, B.G.int, { shadow: false });
    for (const s of [-1, 1]) { B.rack(s * 4, -id_ + .4, 6); B.rack(s * (iw - .4), 1, 5, 1); }
    for (let i = 0; i < 3; i++) { const x = -4.5 + i * 4.5; B.bx(.2, 1.5, .2, 'wood', x, .75, 3.0, B.G.int); B.bx(.7, .9, .35, 'hay', x, 1.3, 3.0, B.G.int); B.ccol(x, 3.0, .45); }
    B.bx(5, .5, 2.4, 'floorPlank', 0, .25, -id_ + 1.3, B.G.int); B.col(0, -id_ + 1.3, 5, 2.4); B.tableR(0, -id_ + 1.3, 2.4, 1, 'darkWood');
    for (let i = 0; i < 4; i++) B.banner(-5 + i * 3.3, 3.8, -id_ + .3, 0, 1, 2.2); B.gallery({ stairX: iw - 1.2, depth: 1.8 }); B.barrel(-iw + .5, id_ - .5); B.crate(-iw + 1.3, id_ - .5, .8);
    for (const x of [-4, 4]) B.lamp(x, 4.2, 0);
  } });

// ---------- 6. Stables ----------
const stables = (spec, ctx) => std(spec, ctx, { name: 'Stables of Varnethryl', w: 18, d: 9, h: 4.6, hs: 1.4, upper: 'timber', lower: 'stone', rh: 3.6, ridge: 'x', over: .9, DW: 3.2, DH: 3.4, floor: 'floorStone', wn: 2, banners: [[-4, 3, .8, 1.8], [4, 3, .8, 1.8]], dormers: [-4, 4], dormY: 1.6, dormZ: 0, windows: false,
  interior(B) { const iw = B.iw, id_ = B.id_;
    for (const s of [-1, 1]) for (let i = 0; i < 4; i++) { const x = -iw + 2.4 + i * 3.6; B.bx(.1, 1.6, 2.6, 'darkWood', x + 1.8, .8, -id_ + 1.5 + (s > 0 ? 0 : 0), B.G.int); B.col(x + 1.8, -id_ + 1.5, .15, 2.6); }
    for (let i = 0; i < 4; i++) { const x = -iw + 1.3 + i * 3.6; B.hay(x, -id_ + 1.0, 1.4, 1.2, .5); const hz = B.add(new THREE.SphereGeometry(.4, 8, 6), M('#6a4a2a'), x + .5, 1.1, -id_ + 1.6, B.G.int); hz.scale.set(1.5, 1, .8); B.bx(.12, 1.1, .12, 'darkWood', x + .5, .45, -id_ + 1.6, B.G.int, { shadow: false }); }
    B.tableR(iw - 2.0, id_ - 1.4, 2.2, 1, 'darkWood');  B.barrel(iw - .5, id_ - .4); B.barrel(iw - .5, id_ - 3.6);
    B.rack(0, id_ - .3, 5); for (let i = 0; i < 5; i++) B.banner(-6 + i * 3, 2.9, id_ - .1, Math.PI, .6, 1.2);
    upperStd(B, { theme: 'store', y: 3.0, side: 'L', len: 3.4 });
    for (const x of [-5, 0, 5]) B.lamp(x, 3.6, 0);
  } });

// ---------- 7. Treasury ----------
function treasury(spec, ctx) {
  const B = new Builder(ctx, spec); B.name = 'Treasury of Varnethryl'; B.rectShell({ w: 12, d: 10, h: 7, hs: 7, upper: 'stone', lower: 'stone', DW: 2.8, DH: 3.4, floor: 'floorStone', posts: false });
  const { w, d, h } = B;
  for (let i = 0; i < 14; i++) { const x = -w / 2 + .5 + i * (w - 1) / 13; B.bx(.7, .7, .7, 'stone', x, h + .35, d / 2 - .35, B.G.ext); B.bx(.7, .7, .7, 'stone', x, h + .35, -d / 2 + .35, B.G.ext); }
  for (const s of [-1, 1]) { B.tower(s * (w / 2 + .6), d / 2 - .6, 1.9, h + 2.5, { windows: 3, coneH: 5.4, collide: true }); B.banner(s * 2.4, 4.8, d / 2 + .08, 0, 1.2, 3); }
  B.add(new THREE.TorusGeometry(1.2, .1, 6, 14, Math.PI), M('gold'), 0, 3.4, d / 2 + .05, B.G.ext); B.bx(2.6, .15, .2, 'gold', 0, 3.45, d / 2 + .1, B.G.ext);
  const gr = B.add(new THREE.PlaneGeometry(2.4, 2.4), M('iron', { side: THREE.DoubleSide }), 0, 3.2 + 1.7, d / 2 - .45, B.G.frame, { shadow: false });  // raised portcullis
  const iw = B.iw, id_ = B.id_; B.add(new THREE.CylinderGeometry(2.2, 2.2, .04, 24), M('sigil'), 0, .09, -.6, B.G.int, { shadow: false });
  for (let i = 0; i < 5; i++) for (let j = 0; j < 3 - (i > 2 ? 1 : 0); j++) { B.bx(.8, .3, .4, 'gold', -.8 + j * .8 + (i % 2) * .4, .15 + i * .3 * 0 + .15 + 0, -.6 - i * .0, B.G.int); }
  B.add(new THREE.ConeGeometry(1.6, 1.1, 4), M('gold'), 0, .65, -.6, B.G.int).rotation.y = .78; B.ccol(0, -.6, 1.5);
  for (const s of [-1, 1]) { B.shelf(s * (iw - .3), -2, 4.5, -s, false); if (s < 0) B.chest(s * (iw - 1.3), id_ - 1.2); }
  B.tableR(-2.5, -id_ + 1.2, 2.4, 1.2, 'darkWood'); B.bx(3.4, 2.3, .3, 'parchment', 0, 3.2, -id_ + .2, B.G.int, { shadow: false });
  B.cyl(.9, .9, .3, 'iron', 3.5, 1.2, -id_ + 1.2, B.G.int, 14).rotation.x = Math.PI / 2; B.banner(-iw + .4, 3.6, -id_ + .3, 0, 1, 2.4); B.banner(iw - .4, 3.6, -id_ + .3, 0, 1, 2.4);
  B.lamp(-3, 4.4, 0); B.lamp(3, 4.4, 0); upperStd(B, { theme: 'hall', y: 3.6 }); B.radius = 9; return B.finish();
}

// ---------- 8. Town Hall ----------
function townhall(spec, ctx) {
  const B = new Builder(ctx, spec); B.name = 'Town Hall of Varnethryl'; B.rectShell({ w: 14, d: 10, h: 7.6, hs: 0, upper: 'stoneL', lower: 'stoneL', DW: 2.8, DH: 3.6, floor: 'floorTile', posts: false });
  const { w, d, h } = B; B.roofGable({ rh: 3.8, key: 'slate', ridge: 'x', over: .6, endKey: 'stoneL' });
  for (const s of [-1, 1]) { const x = s * (w / 2 - .4); B.tower(x, d / 2 - .4, 1.5, h + 1.4, { key: 'stoneL', coneH: 5.6, windows: 3, wa: 1.2 }); B.banner(s * 3.6, 4.6, d / 2 + .08, 0, 1, 2.6); }
  B.gable(6, 2.6, 3.4, 0, h - .6, d / 2 - 1.3, 'slate', B.G.roof, false, 0, 'stoneL'); B.add(new THREE.CircleGeometry(.95, 14), M('gold', { side: THREE.DoubleSide }), 0, h + .9, d / 2 + .04, B.G.roof, { shadow: false }); B.banner(0, h + .9, d / 2 + .06, 0, 1.1, 1.3, B.G.roof);
  for (const s of [-1, 1]) { B.dormer(s * 4.2, h + 2.0, 1); B.dormer(s * 4.2, h + 2.0, -2.2); B.bx(.5, 1.0, 4.4, 'stoneL', s * 1.8, .5, d / 2 + 1.5, B.G.ext); B.cone(.2, .9, 'gold', s * 3.9, 1.0, d / 2 + 2.9, B.G.ext, 5); }
  B.statue(-4.6, d / 2 + 2.2, .9); B.statue(4.6, d / 2 + 2.2, .9); B.apron(w * .6, d * .5, 4);
  B.win(0, h - 1.4, d / 2 + .05, 0, 1.4, 1.8, 'stained'); B.add(new THREE.CircleGeometry(.9, 16), M('#1f3f86'), 0, h - .1 - 2.4 + 1.6, d / 2 + .06, B.G.ext, { shadow: false });
  wins(B, { front: [[-2.8, 1.9], [2.8, 1.9], [-2.8, 5.2], [2.8, 5.2]], side: [[-2.5, 2.0], [2.5, 2.0], [-2.5, 5.2], [2.5, 5.2]], back: [[-3, 2], [3, 2], [-3, 5.2], [3, 5.2]], h: 1.6 });
  for (let i = 0; i < 4; i++) B.bx(DWf(B) + 1 - i * .0 + 1.6 - 0, .22, .7, 'stoneL', 0, .11 + i * 0, d / 2 + .9 + i * .35 - .0, B.G.ext);
  const iw = B.iw, id_ = B.id_;
  B.add(boxG(3, .02, d - 3, 2), M('carpet'), 0, .09, 0, B.G.int, { shadow: false });
  B.bx(1.3, .3, 1.2, 'stoneL', 0, .15, -id_ + .9, B.G.int); B.tableR(0, -id_ + 1.3, 4.5, 1.1, 'darkWood'); B.bx(1.0, 1.4, .1, 'darkWood', 0, 1.1, -id_ + 1.0, B.G.int);
  B.bx(2.6, 1.6, .12, 'parchment', -iw + 1.7, 2.1, -id_ + .25, B.G.int, { shadow: false }); B.box(3, .8, .8, -iw + 1.7, -id_ + 1.2, 'darkWood'); // quest board + clerk desk
  B.shelf(iw - 1.4, -id_ + .3, 3, 0); B.tableR(iw - 1.8, 1, 2.4, 1.2); B.table(-3.5, 1.5, .9);
  for (const s of [-1, 1]) for (const z of [-2, 1.2]) B.pillar(s * 2.4, z, .35, h - 1.4, 'stoneL');
  for (let i = 0; i < 3; i++) B.banner(-iw + .3, 3.4, -2 + i * 2.6, Math.PI / 2, 1, 2.4); B.lamp(-3, 4.8, 0); B.lamp(3, 4.8, 0);
  B.gallery({ stairX: iw - 1.0, depth: 1.6 }); B.radius = 10; return B.finish();
}
const DWf = B => B.DW;

// ---------- 9. Guild Hall ----------
const guildhall = (spec, ctx) => std(spec, ctx, { name: 'Guild Hall of Varnethryl', w: 15, d: 11, h: 7.2, hs: 3.0, upper: 'timber', rh: 4.4, ridge: 'z', over: .9, DW: 3, DH: 3.2, floor: 'floorPlank', wn: 2, chimneys: [[5.8, -2], [-5.8, -2]], dormers: [-3.2, 3.2], dormY: 1.4, dormZ: 1.2,
  banners: [[-3.4, 4.2, 1, 2.6], [3.4, 4.2, 1, 2.6]], sign: ['Guild Hall', '🦁', 7.1, 4.4],
  interior(B) { const iw = B.iw, id_ = B.id_;
    B.add(boxG(2.4, .02, B.d - 2, 2), M('carpet'), 0, .09, .4, B.G.int, { shadow: false });
    B.add(new THREE.BoxGeometry(2, .02, 2), M('gold'), 0, .1, -2, B.G.int, { shadow: false });
    B.tableR(-iw + 3.2, -.6, 3, 1.3); B.tableR(iw - 3.2, -.6, 3, 1.3); B.tableR(-iw + 3.2, 2.2, 2.4, 1.1);
    B.bx(3.2, 2.2, .14, 'parchment', -3.8, 2.0, -id_ + .3, B.G.int, { shadow: false }); B.bx(3.2, 2.2, .14, 'parchment', 3.8, 2.0, -id_ + .3, B.G.int, { shadow: false }); B.box(4, .8, .8, -3.8, -id_ + 1.1); B.box(4, .8, .8, 3.8, -id_ + 1.1);
    B.hearth(0, -id_ + .45, 0, 2.4); B.banner(-1.8, 3.0, -id_ + .3, 0, 1, 2.2); B.banner(1.8, 3.0, -id_ + .3, 0, 1, 2.2);
    B.barrel(iw - .5, id_ - .5); B.barrel(iw - 1.2, id_ - .5); for (const x of [-3.5, 3.5]) { B.cyl(.05, .05, 1.2, 'iron', x, 5.2, 0, B.G.int, 5, { shadow: false }); B.lamp(x, 4.6, 0); }
    B.shelf(-iw + .3, id_ - 3.5, 3, 1); B.gallery({ stairX: iw - 1.2, depth: 1.9 });
  } });

// ---------- 10. Grand Library ----------
function library(spec, ctx) {
  return std(spec, ctx, { name: 'Grand Library of Varnethryl', w: 14, d: 14, h: 8.4, hs: 0, upper: 'stoneL', lower: 'stoneL', rh: 4.6, ridge: 'z', over: .6, endKey: 'stoneL', DW: 3.0, DH: 3.6, floor: 'floorTile', posts: false, wn: 2, windows: false,
    extra(B) { const { w, d, h } = B;
      for (const sx of [-1, 1]) { B.tower(sx * (w / 2 - .2), d / 2 - .2, 1.3, h + 1, { key: 'stoneL', coneH: 5.4, windows: 3 }); B.banner(sx * 3.4, 4.4, d / 2 + .08, 0, 1.1, 3); B.bx(.6, 2.2, .6, 'stoneL', sx * 2.4, 1.1, d / 2 + 1.5, B.G.ext); }
      B.win(0, h - 1.8, d / 2 + .05, 0, 3, 4, 'stained'); for (const z of [-4, 0, 4]) for (const s of [-1, 1]) { B.win(s * (w / 2 + .05), 4.4, z, s * Math.PI / 2, 1.2, 3.4, 'stained'); B.bx(.5, h, .5, 'stoneL', s * (w / 2 + .1), h / 2, z + 2, B.G.ext); }
      for (let i = 0; i < 4; i++) B.bx(B.DW + 1.6, .22, .7, 'stoneL', 0, .11, d / 2 + .8 + i * .35, B.G.ext); B.sign('Grand Library', '📖', 4.6, 3.8, d / 2 + .5, 0); },
    interior(B) { const iw = B.iw, id_ = B.id_, h = B.h;
      for (const z of [-4, 0]) for (const s of [-1, 1]) { B.shelf(s * (iw - 3.2), z - 1, 5, 1.5707); B.shelf(s * (iw - 1.4), z - 1, 5, 1.5707); }
      B.shelf(0, -id_ + .3, 6, 0); B.tableR(0, 1.8, 3.2, 1.2); B.tableR(-3.6, 3.4, 2.4, 1.1); B.tableR(3.6, 3.4, 2.4, 1.1); B.counter(0, id_ - 1.4, 3, .8);
      B.hearth(0, -id_ + 1.3, 0, 2.0); B.add(new THREE.CylinderGeometry(.5, .5, .02, 12), M('gold'), 0, .1, 0, B.G.int); B.cyl(.5, .6, 1.0, 'darkWood', -iw + 1.0, .5, id_ - 1.2, B.G.int, 8); B.ccol(-iw + 1.0, id_ - 1.2, .6);
      for (const s of [-1, 1]) for (const z of [-3, 2]) B.cyl(.3, .3, 1.2, 'stoneL', s * 2.4, .6, z, B.G.int, 8);
      for (let i = 0; i < 3; i++) { B.add(new THREE.TorusGeometry(.9 + i * .1, .05, 5, 14), M('iron'), 0, 5.2, .5, B.G.int, { shadow: false }).rotation.x = Math.PI / 2; } B.lamp(0, 5.4, .5); B.lamp(-3, 5, 2); B.lamp(3, 5, 2);
      for (const s of [-1, 1]) { B.banner(s * 2.2, 4.6, -id_ + .3, 0, 1.2, 3); B.win(s * 5, 5, -id_ + .1, 0, 1.2, 3, 'stained'); } B.gallery({ stairX: 0, depth: 2 });
      B.bx(iw * 2, .16, 1.6, 'floorPlank', 0, 3.1, id_ - .9, B.G.int);
    } }); }

// ---------- 11. Market Provisioner ----------
const market = (spec, ctx) => std(spec, ctx, { name: 'Market Provisioner of Varnethryl', w: 12, d: 9, h: 6.6, hs: 2.8, upper: 'timber', rh: 3.8, ridge: 'z', over: .8, DW: 2.8, chimneys: [[4.6, -2.5, 4.4]], dormers: [-2.5, 2.5], dormY: 1.3, dormZ: 1.0, wn: 2,
  banners: [[0, 4.8, .9, 2]], sign: ['Provisioner', '⚗', 6.0, 3.6],
  extra(B) { const { w, d } = B; for (const s of [-1, 1]) { const x = s * (B.DW / 2 + (w - B.DW) / 4); const a = B.add(boxG((w - B.DW) / 2 - .4, .08, 1.6, 1.6), M('awning'), x, 2.9, d / 2 + .8, B.G.ext); a.rotation.x = .35; B.bx(.8, .8, .8, 'wood', x - 1, .4, d / 2 + 1, B.G.ext); B.bx(.7, .7, .7, 'hay', x + .9, .35, d / 2 + 1, B.G.ext); } },
  interior(B) { const iw = B.iw, id_ = B.id_;
    B.rugAt(0, 0, 2.6, 6, 'carpet'); B.add(boxG(2.6, .02, 6, 2), M('carpet'), 0, .09, .4, B.G.int, { shadow: false }); B.counter(0, -id_ + 1.5, 4, .9); B.shelf(0, -id_ + .35, 5.4); B.shelf(-iw + .3, 0, 4, 1); B.shelf(iw - .3, 0, 4, -1);
    B.tableR(-3, 2, 2, 1.1); B.tableR(3, 2, 2, 1.1); B.barrel(-iw + 1.2, id_ - .6); B.barrel(-iw + 1.9, id_ - .6); B.sack(iw - .7, id_ - .7); B.sack(iw - 1.4, id_ - .8); B.crate(iw - 1.0, id_ - 1.5, .8);
    B.cyl(.12, .12, .3, 'iron', .5, 1.2, -id_ + 1.5, B.G.int, 8); B.banner(-2.2, 3.6, -id_ + .3, 0, 1, 2); B.banner(2.2, 3.6, -id_ + .3, 0, 1, 2); B.lamp(-2, 4.2, .5); B.lamp(2, 4.2, .5); B.gallery({ stairX: iw - 1.2, depth: 1.8 });
  } });

// ---------- 12. Bakery ----------
const bakery = (spec, ctx) => std(spec, ctx, { name: 'Bakery of Varnethryl', w: 8, d: 7, h: 5.4, hs: 2.6, upper: 'timber', rh: 3, ridge: 'z', over: .7, chimneys: [[2.4, -1.8, 3.4]], dormers: [-1.6], dormY: 1.1, dormZ: 1.3, sign: ['Bakery', '🍞', 4.4, 3.3],
  extra(B) { const a = B.add(boxG(2.4, .08, 1.4, 1.6), M('#1f3f86'), B.w / 2 - 1.6, 2.9, B.d / 2 + .7, B.G.ext); a.rotation.x = .35; B.bx(1.6, .7, .8, 'wood', -B.w / 2 + 1.5, .35, B.d / 2 + .8, B.G.ext); for (let i = 0; i < 4; i++) B.add(new THREE.SphereGeometry(.2, 6, 5), M('#c88a3a'), -B.w / 2 + .9 + i * .35, .85, B.d / 2 + .8, B.G.ext); },
  interior(B) { const iw = B.iw, id_ = B.id_;
    B.add(boxG(B.w - 1, .02, B.d - 1, 2), M('floorTile'), 0, .09, 0, B.G.int, { shadow: false }); B.counter(-iw + 1.3, 1.0, 2.4, .8, 1); B.shelf(-iw + .3, -1.8, 2.6, 1, false); for (let i = 0; i < 6; i++) B.add(new THREE.SphereGeometry(.2, 6, 5), M('#c88a3a'), -iw + .45, 1.0 + (i % 3) * .55, -1.0 - i * .35 - 0.2, B.G.int, { shadow: false });
    B.box(1.9, 1.1, 1.5, iw - 1.0, -id_ + .9, 'stone'); B.add(boxG(1.0, .8, .4, 1), GLOW('ff7a1a', 1.4), iw - 1.0, .8, -id_ + 1.6, B.G.int, { shadow: false }); B.bx(.6, 2.2, .6, 'stoneD', iw - 1.0, 2.1, -id_ + .7, B.G.int);
    B.tableR(0, -.4, 2.4, 1.3, 'wood'); B.table(.7, 2.0, .6); B.barrel(-iw + .5, id_ - .5); B.sack(-iw + 1.3, id_ - .6); B.sack(-iw + 1.9, id_ - .7); for (let i = 0; i < 5; i++) B.cyl(.14, .14, .3, 'iron', -1.2 + i * .6, 3.2, -id_ + .3, B.G.int, 8, { shadow: false });
    B.lamp(-1.5, 3.8, 0); B.lamp(1.5, 3.8, 0); upperStd(B, { theme: 'bed', y: 2.9 });
  } });

// ---------- 13. Thieves' Den ----------
const thieves = (spec, ctx) => std(spec, ctx, { name: "Thieves' Den of Varnethryl", w: 8, d: 7, h: 6.2, hs: 2.4, upper: 'darkWood', lower: 'stoneD', postKey: 'darkWood', rh: 3.2, ridge: 'z', over: .8, endKey: 'darkWood', roofKey: 'slateG', chimneys: [[-2.4, -1.6]], banners: [[-2.6, 4.2, .7, 1.8], [2.6, 4.2, .7, 1.8]], sign: ["Varnethryl", '', 4.4, 3.4], floor: 'floorStone',
  interior(B) { const iw = B.iw, id_ = B.id_;
    B.counter(0, 0.6, 3.2, .9); B.shelf(0, -id_ + .3, 4.6); B.shelf(-iw + .3, 1.6, 2.6, 1); B.shelf(iw - .3, -1.6, 2.0, -1); B.crate(-iw + .6, id_ - .6, .9); B.chest(-iw + 1.7, id_ - .6, .8);
    B.table(-1.9, -.2, .6); B.bx(.1, 2.3, 1.2, 'door', 2.3, 1.15, -id_ + .5, B.G.int); B.banner(-iw + .4, 3.4, -id_ + .3, 0, 1, 2); B.lamp(-1.5, 3.4, 1); B.lamp(1.5, 3.4, 1); B.lamp(-2.6, 1.4, -2.2);
    B.bx(.12, 3, 3, 'darkWood', 0.9, 1.5, -1.8, B.G.int); B.col(.9, -1.8, .2, 3);   // partition to the secret back room (door gap at the front)
    upperStd(B, { theme: 'hall', y: 2.9 });
  } });

// ---------- 14. Mage Academy (simplified: hall + six spires) ----------
function mage(spec, ctx) {
  const B = new Builder(ctx, spec); B.name = 'Mage Academy of Varnethryl'; B.rectShell({ w: 16, d: 14, h: 8, hs: 0, upper: 'stone', lower: 'stone', DW: 3, DH: 3.8, floor: 'floorStone', posts: false });
  const { w, d, h } = B; B.roofGable({ rh: 4.4, key: 'slate', ridge: 'x', over: .5, endKey: 'stone' });
  const tp = [[-1, 1, 1.9, 4], [1, 1, 1.9, 4], [-1, -1, 1.6, 2.5], [1, -1, 1.6, 2.5]];
  for (const [sx, sz, r, up] of tp) { B.tower(sx * (w / 2 - .3), sz * (d / 2 - .3), r, h + up, { coneH: 7 + up, windows: 3, wa: sx + sz }); }
  for (const [sx] of [[-1], [1]]) { B.cone(1.1, 5.5, 'slate', sx * 3.4, h + 2.6, -1, B.G.roof, 6); B.add(new THREE.OctahedronGeometry(.4), GLOW('6aa8ff', 1.8), sx * 3.4, h + 8.4, -1, B.G.roof, { shadow: false }); }
  B.cone(1.5, 8, 'slate', 0, h + 3.4, -2, B.G.roof, 6); B.add(new THREE.OctahedronGeometry(.5), GLOW('6aa8ff', 1.8), 0, h + 11.6, -2, B.G.roof, { shadow: false });
  for (const sx of [-1, 1]) { B.banner(sx * 3.4, 4.6, d / 2 + .08, 0, 1, 3); B.win(sx * 5.4, 4.2, d / 2 + .05, 0, 1.2, 3, 'stained'); } B.win(0, 6.4, d / 2 + .05, 0, 2, 2.4, 'stained');
  for (const z of [-3, 1.5]) for (const s of [-1, 1]) B.win(s * (w / 2 + .05), 4.4, z, s * Math.PI / 2, 1.2, 3, 'stained');
  for (let i = 0; i < 4; i++) B.bx(B.DW + 1.8, .22, .7, 'stone', 0, .11, d / 2 + .8 + i * .35, B.G.ext);
  const iw = B.iw, id_ = B.id_;
  B.add(new THREE.CylinderGeometry(3, 3, .03, 28), M('sigil'), 0, .09, .5, B.G.int, { shadow: false }); B.crystal(0, .5, 1.5, '4fa0ff', .55);
  for (const s of [-1, 1]) { B.shelf(s * (iw - .3), -1.5, 6, -s, false); B.shelf(s * (iw - .3), 2.8, 3, -s, false); B.crystal(s * 3.2, -id_ + 1.0, 1.4, 'a07aff', .35); B.tableR(s * 4.2, 2.5, 2.2, 1.2); }
  B.tableR(0, -id_ + 1.2, 3.2, 1.2, 'darkWood'); B.bx(4, 2.2, .1, '#1f3f86', 0, 4.4, -id_ + .2, B.G.int, { shadow: false }); B.banner(-iw + .4, 3.8, -3, Math.PI / 2, 1, 2.4); B.banner(iw - .4, 3.8, -3, -Math.PI / 2, 1, 2.4);
  // gothic spire cluster, glowing lancet windows and a rocky terrace base (matches the sheet's blue spired silhouette)
  const spire = (x, z, y0, r, hh, k = 'slate') => { B.cyl(r, r * 1.15, 3, 'stone', x, y0 + 1.5, z, B.G.roof, 8); B.cone(r * 1.25, hh, k, x, y0 + 3, z, B.G.roof, 8); B.cyl(.0, .12, .9, 'gold', x, y0 + 3 + hh + .35, z, B.G.roof, 5); B.add(new THREE.OctahedronGeometry(.22), GLOW('6aa8ff', 1.8), x, y0 + 3 + hh + 1.0, z, B.G.roof, { shadow: false }); };
  for (const [x, z, r, hh] of [[-5.5, -1, .8, 6.5], [5.5, -1, .8, 6.5], [-3, 3, .7, 5], [3, 3, .7, 5], [-6.8, 4.8, .6, 4.2], [6.8, 4.8, .6, 4.2], [-6.8, -4.8, .6, 4.2], [6.8, -4.8, .6, 4.2], [0, 5, .9, 7.5]]) spire(x, z, h + 2.2, r, hh);
  for (let i = -3; i <= 3; i++) { if (i === 0) continue; B.add(new THREE.PlaneGeometry(.55, 2.8), GLOW('4f9aff', 1.1), i * 1.9, 5.2, d / 2 + .09, B.G.ext, { shadow: false }); B.add(new THREE.ConeGeometry(.3, .6, 3), GLOW('4f9aff', 1.1), i * 1.9, 6.9, d / 2 + .09, B.G.ext, { shadow: false }).rotation.z = 0; }
  for (const s of [-1, 1]) for (const z of [-4.5, -1.5, 1.5, 4.5]) { B.add(new THREE.PlaneGeometry(.55, 2.8), GLOW('4f9aff', 1.1), s * (w / 2 + .1), 5.2, z, B.G.ext, { shadow: false }).rotation.y = s * Math.PI / 2; B.bx(.5, h, .5, 'stone', s * (w / 2 + .15), h / 2, z + 1.5, B.G.ext); }
  B.rocks([[-w / 2 - 3, d / 2 + 1, 2.4, .8], [w / 2 + 3.2, d / 2, 2.6, .9], [-w / 2 - 4, -2, 3.2, .9], [w / 2 + 4.2, -3, 3.0, .9], [-6, -d / 2 - 3, 3.0], [6, -d / 2 - 3.2, 3.2], [0, -d / 2 - 4, 3.6, 1], [-w / 2 - 2.5, -d / 2 - 2, 2.6], [w / 2 + 2.8, -d / 2 - 2, 2.8]]); B.apron(w * .6, d * .4, 4);
  for (const x of [-3, 3]) B.lamp(x, 5.4, 0); B.gallery({ stairX: iw - 1.2, depth: 1.8, y: 3.3 }); B.radius = 15; return B.finish();
}

// ---------- 15. Colosseum ----------
function colosseum(spec, ctx) {
  const B = new Builder(ctx, spec); B.name = 'Colosseum of Varnethryl'; const R = 12.4, H = 7.6, PIT = 7.6;
  B.roundShell({ r: R, h: H, key: 'stone', N: 30, DW: 4.4, DH: 4.6, T: .9, floor: 'sand' });
  B.G.int.children.forEach(m => { if (m.material === M('sand')) { m.material = M('sand'); } });
  // seating bowl as a stepped lathe (gap at the gate tunnel)
  const pts = [new THREE.Vector2(PIT, 0), new THREE.Vector2(PIT, 1.3)]; for (let k = 0; k < 5; k++) { pts.push(new THREE.Vector2(PIT + .2 + k * .85, 1.3 + k * .95)); pts.push(new THREE.Vector2(PIT + 1.05 + k * .85, 1.3 + k * .95)); } pts.push(new THREE.Vector2(R - .9, 6.2)); pts.push(new THREE.Vector2(R - .9, 0));
  const gap = .33, lg = new THREE.LatheGeometry(pts, 40, gap, Math.PI * 2 - gap * 2); uvScale(lg, 6, 2);
  B.add(lg, B.cm('stone'), 0, 0, 0, B.G.walls); B.G.walls.children[B.G.walls.children.length - 1].material.side = THREE.DoubleSide;
  for (const s of [-1, 1]) { B.wallBox(.8, 5.4, R - PIT, 'stone', s * 2.6, 2.7, (R + PIT) / 2); B.col(s * 2.75, (R + PIT) / 2, .8, R - PIT); }
  // three tiers of dark round arches framed by pilasters + cornices (matches the arcaded facade of the reference)
  const archShape = (w, h) => { const s = new THREE.Shape(); const r = w / 2; s.moveTo(-r, 0); s.lineTo(-r, h - r); s.absarc(0, h - r, r, Math.PI, 0, true); s.lineTo(r, 0); s.lineTo(-r, 0); return new THREE.ShapeGeometry(s, 8); };
  const archG = archShape(1.15, 2.1), archG2 = archShape(.95, 1.7), NA = 26;
  const darkM = new THREE.MeshStandardMaterial({ color: 0x0c0c10, roughness: 1, side: THREE.DoubleSide });
  for (let i = 0; i < NA; i++) { const a = (i + .5) / NA * 6.283; if (Math.abs(Math.atan2(Math.sin(a), Math.cos(a))) < .5) continue; const sx = Math.sin(a), cz = Math.cos(a);
    for (const [y, g] of [[.5, archG], [3.1, archG], [5.5, archG2]]) { const m = B.add(g, darkM, sx * (R + .05), y, cz * (R + .05), B.G.ext, { shadow: false }); m.rotation.y = a; }
    const pa = i / NA * 6.283; const pm = B.bx(.55, H, .55, 'stoneD', Math.sin(pa) * (R + .18), H / 2, Math.cos(pa) * (R + .18), B.G.ext); pm.rotation.y = pa;
    if (i % 2) B.banner(sx * (R + .1), 4.3, cz * (R + .1), a, 1.25, 3.4); }
  for (const y of [2.9, 5.3, H - .1]) { const c = B.add(new THREE.CylinderGeometry(R + .35, R + .3, .28, 40, 1, true), B.cm('stoneD'), 0, y, 0, B.G.ext); c.material.side = THREE.DoubleSide; }
  for (let i = 0; i < 4; i++) { const a = 0; } 
  for (let i = 0; i < 30; i++) { const a = i / 30 * 6.283; B.bx(.9, .6, .6, 'stone', Math.sin(a) * (R - .45), H + .3, Math.cos(a) * (R - .45), B.G.ext).rotation.y = a; }
  for (const k of [-1, 1]) { const x = k * 3.2; B.bx(.9, 5.4, .9, 'stone', x * 1, 2.7, R - .3, B.G.ext); }
  B.bx(7, .8, .9, 'stone', 0, 5.4, R - .3, B.G.ext); B.banner(0, 3.2, R + .12, 0, 2, 3.4);
  // seating collision (rings of circles leave the tunnel open)
  for (let i = 0; i < 24; i++) { let a = i / 24 * 6.283; if (a > Math.PI) a -= 6.283; if (Math.abs(a) < .55) continue; B.ccol(Math.sin(a) * 10.0, Math.cos(a) * 10.0, 2.3); }
  B.radius = R + 3;
  const iw = B.iw; B.add(new THREE.RingGeometry(1.8, 2.0, 32), M('gold'), 0, .1, 0, B.G.int, { shadow: false }).rotation.x = -Math.PI / 2;
  for (let i = 0; i < 4; i++) { const a = i * Math.PI / 2 + .7, x = Math.sin(a) * 5.2, z = Math.cos(a) * 5.2; B.bx(.2, 1.5, .2, 'wood', x, .75, z, B.G.int); B.bx(.8, .9, .35, 'hay', x, 1.3, z, B.G.int); B.ccol(x, z, .45); }
  for (const s of [-1, 1]) B.rack(s * 5.8, 3.8, 5, 1);
  B.bx(3, .5, 1.6, 'stone', 0, 4.4, -PIT - 2.4, B.G.int); for (const s of [-1, 1]) B.banner(s * 2.2, 5.6, -PIT - 3, 0, 1, 2.2);   // royal box
  B.add(boxG(1.8, 2.2, .12, 1), M('iron', { side: THREE.DoubleSide }), 0, 3.9, PIT + 1.0, B.G.frame, { shadow: false });     // raised arena gate grille
  const lam = 6; for (let i = 0; i < lam; i++) { const a = i / lam * 6.283 + .3; B.lamp(Math.sin(a) * (PIT - .4), 1.6, Math.cos(a) * (PIT - .4)); }
  return B.finish();
}

// ---------- 16. Castle Keep (simplified: keep + 4 corner towers + throne room) ----------
function keep(spec, ctx) {
  const B = new Builder(ctx, spec); B.name = 'Castle Keep of Varnethryl'; B.rectShell({ w: 22, d: 16, h: 10, hs: 10, upper: 'stone', lower: 'stone', DW: 4.4, DH: 5.2, floor: 'floorStone', posts: false, T: .8 });
  const { w, d, h } = B; B.bx(w, .6, d, 'stoneD', 0, h + .3, 0, B.G.roof);
  for (let i = 0; i < 12; i++) { const x = -w / 2 + .6 + i * (w - 1.2) / 11; B.bx(.8, .8, .8, 'stone', x, h + 1, d / 2 - .4, B.G.roof); B.bx(.8, .8, .8, 'stone', x, h + 1, -d / 2 + .4, B.G.roof); }
  B.bx(10, 5, 8, 'stone', 0, h + 2.9, -1, B.G.roof); B.cone(6.4, 8, 'slate', 0, h + 5.4, -1, B.G.roof, 4).rotation.y = .78;
  for (const [sx, sz, r] of [[-1, 1, 3.3], [1, 1, 3.3], [-1, -1, 3.0], [1, -1, 3.0]]) B.tower(sx * (w / 2 - .2), sz * (d / 2 - .2), r, h + 4, { coneH: 8, windows: 3, wa: sx * 1.3 + sz });
  for (const s of [-1, 1]) B.banner(s * 4.6, 6, d / 2 + .08, 0, 1.5, 4.2);
  for (const [x, z, r, up] of [[-5, -3, 2.5, 8], [5, -4, 2.2, 10], [0, -6.2, 2.7, 6]]) B.tower(x, z, r, h + up, { coneH: 8 + up * .3, windows: 3, collide: false, wa: x });
  B.rocks([[-w / 2 - 2.6, d / 2 - 1, 2.0], [w / 2 + 2.8, d / 2 - 2, 2.3], [-w / 2 - 3.2, -2, 2.8, .9], [w / 2 + 3.4, -3, 2.6, .9], [-6, -d / 2 - 2.2, 2.4], [5, -d / 2 - 2.6, 2.8], [0, -d / 2 - 3.4, 3.0, 1], [-w / 2 - 1.6, d / 2 + 2.4, 1.3], [w / 2 + 1.8, d / 2 + 2.6, 1.5]]);
  B.guard(-2.6, d / 2 + 2.6); B.guard(2.6, d / 2 + 2.6); B.apron(w * .5, d * .4, 4);
  { // ornate gold double door (cropped from the reference), swung open, under a big pointed-arch surround with a tracery tympanum
    const gm = new THREE.MeshStandardMaterial({ map: goldDoorTexture(), metalness: .35, roughness: .5, side: THREE.DoubleSide, emissive: 0x5a3c0c }); const DHk = 5.2, zf = d / 2 + .06, hw = B.DW / 2;
    for (const s of [-1, 1]) { const dx = s * .72, dz = .69, th = -Math.atan2(dz, dx); const m = B.add(new THREE.PlaneGeometry(hw * .98, DHk * .98), gm, s * hw + dx * hw * .5, DHk * .49, zf + dz * hw * .5, B.G.ext, { shadow: false }); m.rotation.y = th; m.scale.x = 1; }
    const R1 = hw + .9, R0 = hw + .1, cy = DHk + .2; const ring = new THREE.Shape(); ring.moveTo(-R1, 0); ring.lineTo(-R1, cy); ring.absarc(0, cy, R1, Math.PI, 0, true); ring.lineTo(R1, 0); ring.lineTo(R0, 0); ring.lineTo(R0, cy); ring.absarc(0, cy, R0, 0, Math.PI, false); ring.lineTo(-R0, 0); ring.lineTo(-R1, 0);
    B.add(new THREE.ExtrudeGeometry(ring, { depth: .5, bevelEnabled: false, curveSegments: 14 }), B.cm('stoneD'), 0, 0, d / 2 - .05, B.G.ext);
    const tym = new THREE.Shape(); tym.moveTo(-R0, DHk); tym.lineTo(-R0, cy); tym.absarc(0, cy, R0, Math.PI, 0, true); tym.lineTo(R0, DHk); tym.lineTo(-R0, DHk); const tg = new THREE.ShapeGeometry(tym, 14); const uv = tg.attributes.uv, ps = tg.attributes.position; for (let i = 0; i < uv.count; i++) uv.setXY(i, (ps.getX(i) + R0) / (2 * R0), .45 + (ps.getY(i) - DHk) / (R0 + .2) * .55);
    B.add(tg, gm, 0, 0, d / 2 + .04, B.G.ext, { shadow: false }); B.add(new THREE.PlaneGeometry(1.4, .5), M('gold'), 0, 5.2 + R0 + .6, d / 2 + .5, B.G.ext, { shadow: false });
  }
  for (const x of [0]) 
  for (let i = 0; i < 4; i++) B.bx(B.DW + 2, .22, .8, 'stoneD', 0, .11, d / 2 + .8 + i * .4, B.G.ext);
  wins(B, { front: [[-6, 5], [6, 5], [-9, 5.5], [9, 5.5]], side: [[-4, 5], [0, 5], [4, 5]], back: [[-6, 5], [0, 5], [6, 5]], w: .6, h: 1.8 });
  const iw = B.iw, id_ = B.id_;
  B.add(boxG(3, .02, d - 2, 2), M('carpet'), 0, .09, 0, B.G.int, { shadow: false }); B.throne(0, -id_ + 1.3); B.banner(0, 5.2, -id_ + .4, 0, 2.4, 4.4); B.banner(-3.6, 5, -id_ + .4, 0, 1.2, 3); B.banner(3.6, 5, -id_ + .4, 0, 1.2, 3);
  for (const s of [-1, 1]) for (const z of [-4, 0, 4]) B.pillar(s * 4.2, z, .5, h - .6, 'stone');
  B.tableR(-iw + 2.6, 1.5, 1.6, 7, 'darkWood'); B.tableR(iw - 2.6, 1.5, 1.6, 7, 'darkWood'); for (const s of [-1, 1]) B.hearth(s * (iw - .5), -3.6, -s * Math.PI / 2, 2.2);
  for (let i = 0; i < 3; i++) for (const s of [-1, 1]) B.banner(s * (iw - .4), 5, -2 + i * 3.6, -s * Math.PI / 2, 1, 2.6);
  for (const z of [-2, 2.5]) for (const x of [-2.6, 2.6]) B.lamp(x, 6.2, z);
  B.fullUpper({ level: 1, y: 5.0, stair: { cx: iw - .9, cz: .95, dir: '-z', len: 4.5, w: 1.6 }, rooms(U) { const Z = -3.2;
    U.partition(0, Z, iw * 2, 'x', [[-5.5, 1.4], [0, 1.6], [5.5, 1.4]]); U.partition(-3.4, (Z - id_) / 2, id_ + Z, 'z', null, 2.7); U.partition(3.4, (Z - id_) / 2, id_ + Z, 'z', null, 2.7);
    U.bed(-iw + 1.6, -id_ + 1.2, 1); U.chest(-4.5, -id_ + .6, .9); U.rugAt(-6.8, -4.9, 3, 2.4); U.lamp(-6.8, 2.4, -4.9);
    U.tableR(0, -id_ + 1.6, 3.0, 1.2); U.pew(-1.0, -id_ + 2.4, 1.6); U.pew(1.0, -id_ + 2.4, 1.6); U.lamp(0, 2.4, -id_ + 1.6); U.hearth(0, -id_ + .5, 0, 2.4);
    U.bed(iw - 1.6, -id_ + 1.2, 1); U.chest(4.5, -id_ + .6, .9); U.rugAt(6.8, -4.9, 3, 2.4); U.lamp(6.8, 2.4, -4.9);
    U.tableR(-5.5, 1.5, 2.6, 1.2); U.banner(-iw + .4, 1.8, -2, Math.PI / 2, 1, 2.2); U.lamp(-5.5, 2.4, 1.5); U.lamp(0, 2.4, 1.0); } });
  B.fullUpper({ level: 2, y: 10.2, y0: 5.0, l0: 1, stair: { cx: -(iw - .9), cz: .7, dir: '-z', len: 5.0, w: 1.6 }, rails: true, rooms(U) { U.bx(1.2, .5, 1.2, 'stone', 6, .25, -3, U.G.int); U.ccol(6, -3, .8); U.lamp(0, 1.6, 0); U.banner(0, 1.2, -id_ + .6, 0, 1.4, 2.2); } });
  B.radius = 14; return B.finish();
}

// ---------- 17. Gatehouse (walkable tunnel gate) ----------
function gatehouse(spec, ctx) {
  const B = new Builder(ctx, spec); B.name = 'Gatehouse of Varnethryl'; const TW = 2.4, H = 8;
  B.w = 14; B.d = 6; B.h = H; B.radius = 9;
  for (const s of [-1, 1]) { B.tower(s * 5.6, 0, 2.9, H + 1.5, { coneH: 6.4, windows: 4, wa: 1 + s }); const x = s * ((TW + 5.6 - 2.6) / 2 + .0);
    B.bx(5.6 - 2.6 - TW + 0, H, 5, 'stone', s * ((TW + 5.6 - 2.5) / 2 + 0), H / 2, 0, B.G.ext); B.col(s * ((TW + 5.6 - 2.5) / 2), 0, 5.6 - 2.5 - TW, 5); }
  B.bx(TW * 2 + .02, H - 4.6, 5, 'stone', 0, 4.6 + (H - 4.6) / 2, 0, B.G.ext);
  for (let i = 0; i < 6; i++) { const x = -3 + i * 1.2; B.bx(.7, .7, .7, 'stone', x, H + .35, 2.2, B.G.ext); B.bx(.7, .7, .7, 'stone', x, H + .35, -2.2, B.G.ext); }
  B.bx(TW * 2, .8, .9, 'stoneD', 0, 4.6, 2.4, B.G.ext);
  B.add(new THREE.PlaneGeometry(TW * 2 - .3, 2.4), M('iron', { side: THREE.DoubleSide }), 0, 4.0, 2.0, B.G.ext, { shadow: false });                     // portcullis (raised)
  B.add(new THREE.PlaneGeometry(TW * 2 - .3, 2.4), M('iron', { side: THREE.DoubleSide }), 0, 4.0, -2.0, B.G.ext, { shadow: false });
  for (const s of [-1, 1]) { const dr = B.bx(.2, 3.8, 1.2, 'door', s * (TW + .15), 1.9, 2.2, B.G.ext); dr.rotation.y = 0; B.bx(.2, 3.8, 1.2, 'door', s * (TW + .15), 1.9, -2.2, B.G.ext); }
  B.banner(-3.6, 5.4, 2.56, 0, 1.4, 3.4); B.banner(3.6, 5.4, 2.56, 0, 1.4, 3.4); B.banner(-3.6, 5.4, -2.56, Math.PI, 1.4, 3.4); B.banner(3.6, 5.4, -2.56, Math.PI, 1.4, 3.4);
  B.add(new THREE.CircleGeometry(.6, 12), M('gold'), 0, 6.4, 2.54, B.G.ext, { shadow: false });
  // tunnel interior: stone floor, weapon racks and lanterns (walk-through gate)
  B.add(boxG(TW * 2, .06, 5, 3), M('floorStone'), 0, .03, 0, B.G.int, { shadow: false });
  B.rack(-TW + .4, -.8, 3, 1); B.rack(TW - .4, .8, 3, -1); B.lamp(-TW + .3, 3.2, 0); B.lamp(TW - .3, 3.2, 0);
  B.add(new THREE.TorusGeometry(TW, .25, 4, 12, Math.PI), M('stoneD'), 0, 3.6, 2.4, B.G.ext);
  for (const s of [-1, 1]) for (const z of [-2.65, 2.65]) for (const y of [2.6, 5.6]) B.bx(.16, 1.0, .14, '#0e0f12', s * 5.6 * .55 + s * 0, y, z, B.G.ext, { shadow: false });
  B.guard(-3.2, 4.6); B.guard(3.2, 4.6); B.guard(-3.2, -4.6); B.apron(14, 4, 5); B.bx(TW * 2 + 1, .08, 12, 'cobble', 0, .05, 0, B.G.ext, { shadow: false });
  B.rocks([[-9.5, 2.5, 1.6], [9.8, 2.2, 1.9], [-10.5, -2, 1.3], [10.4, -2.4, 1.5]]);
  B.insideTest = null; return B.finish();
}

// ---------- 18. Fountain Monument ----------
function fountain(spec, ctx) {
  const B = new Builder(ctx, spec); B.name = 'Fountain Monument of Varnethryl'; B.radius = 6; B.insideTest = null;
  B.cyl(6.3, 6.5, .3, 'pave', 0, .15, 0, B.G.ext, 8);                                             // octagonal plaza plinth
  B.cyl(4.2, 4.4, 1.0, 'stoneL', 0, .8, 0, B.G.ext, 24); B.add(new THREE.CylinderGeometry(3.8, 3.8, .1, 24), M('water'), 0, 1.3, 0, B.G.ext, { shadow: false }); B.ccol(0, 0, 4.4);
  B.cyl(1.3, 1.8, 2.0, 'stoneL', 0, 2.2, 0, B.G.ext, 12); B.cyl(2.4, 1.2, .5, 'stoneL', 0, 3.4, 0, B.G.ext, 16); B.add(new THREE.CylinderGeometry(2.1, 2.1, .08, 16), M('water'), 0, 3.66, 0, B.G.ext, { shadow: false });
  B.cyl(.8, 1.0, 1.2, 'stoneL', 0, 4.3, 0, B.G.ext, 10); B.cyl(1.5, .8, .35, 'stoneL', 0, 4.9, 0, B.G.ext, 12);
  for (let i = 0; i < 4; i++) { const a = i * 1.571 + .78; B.add(new THREE.CylinderGeometry(.08, .1, .5, 5), M('gold'), Math.sin(a) * 3.0, 3.8, Math.cos(a) * 3.0, B.G.ext); B.add(new THREE.CylinderGeometry(.05, .05, 2.2, 5), M('water', { transparent: true, opacity: .6 }), Math.sin(a) * 3.3, 2.6, Math.cos(a) * 3.3, B.G.ext, { shadow: false }); }
  // heraldic plaques on the basin
  for (let i = 0; i < 4; i++) { const a = i * 1.571; B.banner(Math.sin(a) * 4.45, 1.0, Math.cos(a) * 4.45, a, .9, .9); }
  const BL = M('#1f4a9a'), ST = M('stoneL'); // blue lion statue
  B.add(new THREE.BoxGeometry(1.5, .8, .8), ST, 0, 5.5, 0, B.G.ext); B.add(new THREE.BoxGeometry(.5, 1.0, .6), ST, .5, 5.4, .5 * 0, B.G.ext);
  B.add(new THREE.BoxGeometry(.28, .9, .28), ST, .55, 5.35, .25, B.G.ext); B.add(new THREE.BoxGeometry(.28, .9, .28), ST, .55, 5.35, -.25, B.G.ext); B.add(new THREE.BoxGeometry(.3, .6, .3), ST, -.55, 5.3, .22, B.G.ext); B.add(new THREE.BoxGeometry(.3, .6, .3), ST, -.55, 5.3, -.22, B.G.ext);
  B.add(new THREE.SphereGeometry(.55, 10, 8), BL, .75, 6.45, 0, B.G.ext); B.add(new THREE.SphereGeometry(.38, 8, 6), ST, .98, 6.35, 0, B.G.ext); B.add(new THREE.BoxGeometry(.4, .3, .25), BL, .35, 6.0, 0, B.G.ext);
  B.add(new THREE.BoxGeometry(.9, .7, .8), BL, .3, 5.95, 0, B.G.ext); B.add(new THREE.CylinderGeometry(.06, .1, 1.0, 5), ST, -.9, 5.6, 0, B.G.ext).rotation.z = .8;
  for (const [sx, sz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) { const x = sx * 5.6, z = sz * 5.6; B.cyl(.14, .18, 2.8, 'iron', x, 1.4, z, B.G.ext, 6); B.add(new THREE.SphereGeometry(.28, 6, 5), GLOW('ffc060', 1.5), x, 3.0, z, B.G.ext, { shadow: false }); B.cyl(.7, .8, .5, 'stoneL', x + sx * .9, .25, z, B.G.ext, 8); B.add(new THREE.SphereGeometry(.55, 6, 5), M('#3f7a3a'), x + sx * .9, .7, z, B.G.ext); }
  return B.finish();
}

// ---------- 19. Observatory ----------
function observatory(spec, ctx) {
  const B = new Builder(ctx, spec); B.name = 'Observatory of Varnethryl'; const R = 4.6, H = 11;
  B.roundShell({ r: R, h: H, key: 'stone', N: 16, DW: 2.4, DH: 3.2, floor: 'marbleInlay', T: .6 });
  for (const y of [3.4, 7.2, H - .3]) B.ring(R + .12, .3, 'gold', 0, y, 0, B.G.ext, 16);
  for (let i = 0; i < 8; i++) { const a = i / 8 * 6.283 + .4; if (Math.abs(Math.atan2(Math.sin(a), Math.cos(a))) < .5) continue; for (const y of [5.4, 9.2]) B.win(Math.sin(a) * (R + .02), y, Math.cos(a) * (R + .02), a, .8, 1.8, 'stained'); }
  const dm = new THREE.SphereGeometry(R + .2, 20, 10, 0, Math.PI * 2, 0, Math.PI / 2); uvScale(dm, 1, 1);
  B.add(dm, M('#16306e', { side: THREE.DoubleSide }), 0, H, 0, B.G.roof); for (let i = 0; i < 6; i++) { const t = B.add(new THREE.TorusGeometry(R + .22, .07, 5, 16, Math.PI), M('gold'), 0, H, 0, B.G.roof, { shadow: false }); t.rotation.y = i / 6 * Math.PI; }
  B.add(new THREE.CylinderGeometry(.14, .2, 1.8, 6), M('gold'), 3.3, H + 3.0, 0, B.G.roof).rotation.z = -.7; B.cyl(.0, .3, .8, 'gold', 0, H + R + .3, 0, B.G.roof, 6);
  B.banner(2.6, 6.5, R + .02 - .15, 0, .8, 2.2);
  { // craggy mountain-top base (reference), warm arched windows, rocky steps
    const rm = '#5d6068'; for (let i = 0; i < 11; i++) { const a = 1.0 + i * (Math.PI * 2 - 2.0) / 10 + .3, rr = R + 2.4 + (i % 3) * .6, s = 1.8 + (i % 4) * .6; const m = B.add(new THREE.DodecahedronGeometry(s, 0), M(rm), Math.sin(a) * rr, s * .55, Math.cos(a) * rr, B.G.ext); m.scale.y = 1.3 + (i % 2) * .5; m.rotation.y = a * 2; B.ccol(Math.sin(a) * rr, Math.cos(a) * rr, s * .8); }
    for (let i = 0; i < 6; i++) B.bx(3.2 + i * .1, .24, .7, 'stoneD', 0, .12 + i * .01, R + .6 + i * .4, B.G.ext);
    for (let i = 0; i < 10; i++) { const a = i / 10 * 6.283 + .15; if (Math.abs(Math.atan2(Math.sin(a), Math.cos(a))) < .5) continue; B.add(new THREE.PlaneGeometry(.55, 1.5), GLOW('ffb347', 1.3), Math.sin(a) * (R + .06), 5.4, Math.cos(a) * (R + .06), B.G.ext, { shadow: false }).rotation.y = a; B.add(new THREE.PlaneGeometry(.55, 1.5), GLOW('6aa8ff', 1.2), Math.sin(a + .31) * (R + .06), 9.2, Math.cos(a + .31) * (R + .06), B.G.ext, { shadow: false }).rotation.y = a + .31; } }
  B.add(new THREE.CylinderGeometry(1.7, 1.9, .06, 20), M('sigil'), 0, .1, -.2, B.G.int, { shadow: false });
  B.cyl(.7, .9, 1.0, 'darkWood', 0, .5, -.2, B.G.int, 10); B.ccol(0, -.2, 1.0); B.add(new THREE.SphereGeometry(.55, 12, 10), GLOW('5fa8ff', 1.4), 0, 1.7, -.2, B.G.int, { shadow: false });
  for (const a of [.8, 2.4, 3.9, 5.5]) B.add(new THREE.TorusGeometry(.8 + a * .02, .03, 4, 20), GLOW('9fd0ff', 1.2), 0, 1.7, -.2, B.G.int, { shadow: false }).rotation.set(a, a * 1.7, 0);
  B.cyl(.25, .35, 1.2, 'gold', 2.2, .6, -1.6, B.G.int, 8); B.add(new THREE.CylinderGeometry(.2, .24, 2.2, 8), M('#b8902c'), 2.6, 1.9, -1.9, B.G.int).rotation.z = -.9; B.ccol(2.2, -1.6, .5);
  const iw = B.iw; for (let i = 0; i < 5; i++) { const a = Math.PI + (i - 2) * .55; const x = Math.sin(a) * (iw - .4), z = Math.cos(a) * (iw - .4); const s = B.bx(1.9, 2.4, .5, 'books', x, 1.2, z, B.G.int); s.rotation.y = a; B.ccol(x, z, .9); }
  B.tableR(2.0, 1.4, 1.8, 1.0, 'darkWood'); for (const [x, z] of [[2.4, 1.6]]) B.chest(x, z, .8); B.banner(0, 5.2, -iw + .1, 0, 1, 2.4); B.lamp(1.5, 3.4, 0); B.lamp(-1.5, 3.4, 0);
  { const S1 = { cx: -1.8, cz: .6, dir: '-z', len: 4.4, w: 1.5 }, S2 = { cx: 1.8, cz: .6, dir: '+z', len: 4.4, w: 1.5 };
    B.fullUpper({ level: 1, y: 3.7, disc: B.iw - .05, stair: S1, rooms(U) { U.lamp(0, 2.8, 0); U.lamp(0, 2.8, -2.4); } });
    B.fullUpper({ level: 2, y: 7.4, y0: 3.7, l0: 1, disc: B.iw - .05, stair: S2, rooms(U) { U.lamp(0, 2.8, 0); U.lamp(0, 2.8, 2.4); } });
    B.fullUpper({ level: 3, y: 10.9, y0: 7.4, l0: 2, disc: B.iw - .05, stair: S1, rooms(U) { U.add(new THREE.CylinderGeometry(.12, .18, 2.2, 8), M('#b8902c'), 1.8, 1.2, -.4, U.G.int).rotation.z = -.9; U.crystal(2.2, 1.4, .8, '5fa8ff', .3); U.lamp(0, 2.4, 0); } }); }
  return B.finish();
}

// ---------- 20. Crypt (links to the Dusk Hollow / Veyra quest) ----------
function archRingGeo(x0, R1, R0, cy, depth) { const s = new THREE.Shape(); s.moveTo(x0 - R1, 0); s.lineTo(x0 - R1, cy); s.absarc(x0, cy, R1, Math.PI, 0, true); s.lineTo(x0 + R1, 0); s.lineTo(x0 + R0, 0); s.lineTo(x0 + R0, cy); s.absarc(x0, cy, R0, 0, Math.PI, false); s.lineTo(x0 - R0, 0); s.lineTo(x0 - R1, 0); return new THREE.ExtrudeGeometry(s, { depth, bevelEnabled: false, curveSegments: 12 }); }
function archFillGeo(x0, R, cy, y0 = 0) { const s = new THREE.Shape(); s.moveTo(x0 - R, y0); s.lineTo(x0 - R, cy); s.absarc(x0, cy, R, Math.PI, 0, true); s.lineTo(x0 + R, y0); s.lineTo(x0 - R, y0); return new THREE.ShapeGeometry(s, 12); }
function crypt(spec, ctx) {
  const B = new Builder(ctx, spec); B.name = 'Crypt of Varnethryl'; B.quest = 'veyra'; B.DH = 3.4; B.rectShell({ w: 10, d: 14, h: 5.4, hs: 5.4, upper: 'stoneD', lower: 'stoneD', DW: 2.4, DH: 3.4, floor: 'floorStone', posts: false });
  const { w, d, h } = B; B.roofGable({ rh: 2.4, key: 'slate', ridge: 'z', over: .5, endKey: 'stoneD' });
  for (const [x, z, s] of [[-w / 2 - 1.8, 0, 2.4], [w / 2 + 1.8, 0, 2.4], [-w / 2 - 1.2, -4.6, 2.0], [w / 2 + 1.2, -4.6, 2.0], [0, -d / 2 - 2.0, 3.2], [-3, -d / 2 - 1.2, 2.2], [3, -d / 2 - 1.2, 2.2]]) { const m = B.add(new THREE.DodecahedronGeometry(s, 0), M('rock'), x, s * .45, z, B.G.roof); m.scale.set(1.3, .9, 1.2); }
  for (const s of [-1, 1]) { B.bx(.9, h + .6, .9, 'stoneD', s * (B.DW / 2 + 1.3), (h + .6) / 2, d / 2 + .1, B.G.ext); B.cone(.65, 1.6, 'slate', s * (B.DW / 2 + 1.3), h + .6, d / 2 + .1, B.G.ext, 4); B.add(new THREE.SphereGeometry(.2, 6, 5), GLOW('4fa0ff', 2), s * (B.DW / 2 + .75), 2.6, d / 2 + .55, B.G.ext, { shadow: false }); }
  B.add(new THREE.CylinderGeometry(1.8, 1.8, .12, 3, 1, false, 0, 6.283), M('#142a5a', { side: THREE.DoubleSide }), 0, 4.2, d / 2 + .03, B.G.ext).scale.set(1, 1, .1);
  B.win(0, 4.3, d / 2 + .08, 0, 1.4, 2.2, 'stained'); B.bx(2.9, .25, .3, 'stoneD', 0, 3.55, d / 2 + .12, B.G.ext);
  for (let i = 0; i < 4; i++) B.bx(B.DW + 1.4 + i * .3, .22, .8, 'stone', 0, .11, d / 2 + 1 + i * .45, B.G.ext);
  { // gothic frontispiece: tall pointed-arch rings (door + two glowing blind arches), pinnacles, cliff rocks, blue lanterns (see Crypt reference)
    const zf = d / 2 + .02, rockM = '#4d5058';
    B.add(archRingGeo(0, 2.3, 1.45, B.DH + .3, .55), B.cm('stoneD'), 0, 0, zf, B.G.ext); B.add(archRingGeo(0, 1.45, 1.25, B.DH + .3, .35), B.cm('stone'), 0, 0, zf + .1, B.G.ext);
    B.add(archFillGeo(0, 1.4, B.DH + .3, B.DH), GLOW('2a6cff', .45), 0, 0, zf + .06, B.G.ext, { shadow: false });
    for (const s of [-1, 1]) { const x = s * 4.0; B.add(archRingGeo(x, 1.55, 1.15, 3.8, .45), B.cm('stoneD'), 0, 0, zf, B.G.ext); B.add(archFillGeo(x, 1.15, 3.8, .5), GLOW('1d4fcf', .5), 0, 0, zf + .04, B.G.ext, { shadow: false }); B.bx(.5, .4, .5, 'stoneD', s * 2.6, 6.0, d / 2 + .2, B.G.ext); B.cone(.45, 2.0, 'slate', s * 2.65, 6.6, d / 2 + .2, B.G.ext, 4);
      B.bx(.9, 1.0, .9, 'stoneD', s * 3.0, .5, d / 2 + 2.2, B.G.ext); B.add(new THREE.SphereGeometry(.28, 8, 6), GLOW('4fa0ff', 2.2), s * 3.0, 1.35, d / 2 + 2.2, B.G.ext, { shadow: false }); }
    for (const [x, z, r, sy] of [[-7, -2, 4.0, 1.5], [7, -2, 4.0, 1.5], [-4, -7, 4.6, 1.7], [4, -7, 4.6, 1.7], [0, -10, 5.2, 1.9], [-7.5, 4, 3.0, 1.3], [7.5, 4, 3.0, 1.3], [-9, -8, 3.2, 1.2], [9, -8, 3.2, 1.2], [0, 1, 3.4, 1.1]]) { const m = B.add(new THREE.DodecahedronGeometry(r, 0), M(rockM), x, r * .75 + (z > 1 ? 2.6 : 3.4), z, B.G.roof); m.scale.y = sy; m.rotation.y = x + z; }
  }
  const iw = B.iw, id_ = B.id_;
  B.add(new THREE.CylinderGeometry(3.0, 3.0, .04, 28), M('sigil'), 0, .09, -id_ + 3.6, B.G.int, { shadow: false });
  for (const z of [-3, 1, 4.5]) for (const s of [-1, 1]) B.pillar(s * 2.6, z, .38, h - .5, 'stoneD');
  for (const z of [-2.2, 2.6]) { B.bx(1.5, .7, 3, 'stone', 0, .35, z, B.G.int); B.bx(1.7, .22, 3.2, 'stoneL', 0, .8, z, B.G.int); B.col(0, z, 1.7, 3.2); }
  for (const s of [-1, 1]) for (let i = 0; i < 3; i++) { B.bx(.3, 1.4, 1.2, '#10141f', s * (iw - .1), 1.2, -3 + i * 3, B.G.int); B.lamp(s * (iw - .6), 3.0, -3 + i * 3); B.add(new THREE.SphereGeometry(.16, 6, 5), GLOW('4fa0ff', 2), s * (iw - .5), 2.4, -1.5 + i * 3, B.G.int, { shadow: false }); }
  B.add(new THREE.PlaneGeometry(2.2, 3), M('iron', { side: THREE.DoubleSide }), 0, 1.7, -id_ + .1, B.G.int, { shadow: false }); B.banner(-3.6, 3.4, -id_ + .2, 0, .9, 2.2); B.banner(3.6, 3.4, -id_ + .2, 0, .9, 2.2);
  B.crystal(0, -id_ + 3.6, 1.4, '4fa0ff', .4); B.radius = 10; return B.finish();
}

// ---------- 21. Windmill ----------
function windmill(spec, ctx) {
  const B = new Builder(ctx, spec); B.name = 'Windmill of Varnethryl'; const R = 3.4, H = 4.6;
  B.roundShell({ r: R, h: H, key: 'stone', N: 14, DW: 2.0, DH: 2.6, floor: 'floorStone', T: .55 });
  B.cyl(R - .2, R - .7, 4.6, 'stone', 0, H + 2.3, 0, B.G.roof, 12); B.cyl(R, R, .2, 'darkWood', 0, H + .1, 0, B.G.roof, 12);
  B.cone(R, 3.0, 'slate', 0, H + 4.6, 0, B.G.roof, 12, { shadow: true }); B.cyl(R - .55, R - .55, .16, 'darkWood', 0, H + 4.6, 0, B.G.roof, 12);
  { // four lattice sails on a hub (rotate slowly), as in the reference
    const sg = new THREE.Group(); sg.position.set(0, H + 3.4, R + .1); B.root.add(sg); const wm = M('darkWood'), cl = M('#d9cfae', { side: THREE.DoubleSide });
    const hub = new THREE.Mesh(new THREE.CylinderGeometry(.3, .3, .6, 8), wm); hub.rotation.x = Math.PI / 2; sg.add(hub);
    for (let k = 0; k < 4; k++) { const arm = new THREE.Group(); arm.rotation.z = k * Math.PI / 2 + .35; sg.add(arm); const sp = new THREE.Mesh(boxG(.14, 8, .12, 1), wm); sp.position.y = 4.2; arm.add(sp);
      const sl = new THREE.Mesh(new THREE.PlaneGeometry(1.4, 5.6), cl); sl.position.set(.85, 4.8, .02); arm.add(sl); for (let q = 0; q < 6; q++) { const cb = new THREE.Mesh(boxG(1.5, .07, .07, 1), wm); cb.position.set(.85, 2.2 + q * .9, .05); arm.add(cb); } const edge = new THREE.Mesh(boxG(.08, 5.6, .08, 1), wm); edge.position.set(1.55, 4.8, .04); arm.add(edge); }
    for (const m of sg.children) m.castShadow = true; let rt = 0; const prev = B.tick; B.tick = dt => { rt += dt * .25; sg.rotation.z = rt; if (prev) prev(dt); }; }
  for (let i = 0; i < 3; i++) { const a = i * 2.1 + .4; B.win(Math.sin(a) * (R - .3), H + 2.4, Math.cos(a) * (R - .3), a, .5, .8, 'glass', B.G.roof); }
  const hub = new THREE.Group(); hub.position.set(0, H + 4.0, R + .5); B.root.add(hub);
  const sailMat = M('#e6dcc0', { side: THREE.DoubleSide }), frame = M('darkWood');
  for (let i = 0; i < 4; i++) { const arm = new THREE.Group(); arm.rotation.z = i * Math.PI / 2; hub.add(arm);
    const spar = new THREE.Mesh(boxG(.2, 8.2, .18, 1), frame); spar.position.y = 4.3; arm.add(spar); const sail = new THREE.Mesh(new THREE.PlaneGeometry(1.4, 5.6), sailMat); sail.position.set(.8, 5.0, .02); arm.add(sail);
    for (let k = 0; k < 8; k++) { const rung = new THREE.Mesh(boxG(1.5, .06, .06, 1), frame); rung.position.set(.8, 2.4 + k * .75, .06); arm.add(rung); } }
  const hb = new THREE.Mesh(new THREE.SphereGeometry(.4, 8, 6), M('gold')); hub.add(hb); B.tick = dt => { hub.rotation.z += dt * .5; };
  B.add(new THREE.CylinderGeometry(.18, .22, 1, 6), M('iron'), 0, H + 4.0, R - .2, B.G.roof).rotation.x = Math.PI / 2;
  for (let i = 0; i < 4; i++) B.bx(B.DW + 1.2 - i * .0, .22, .7, 'stone', 0, .11 + i * .0, R + .9 + i * .35, B.G.ext);
  const iw = B.iw; B.cyl(.85, .95, .6, 'stone', 1.0, .3, -.3, B.G.int, 14); B.cyl(.7, .7, .25, 'stoneD', 1.0, .72, -.3, B.G.int, 14); B.cone(.4, 1.0, 'stoneD', 1.0, .8, -.3, B.G.int, 8).rotation.x = Math.PI; B.ccol(1.0, -.3, 1.0);
  for (const [x, z] of [[iw - .8, 1.4], [iw - .6, 0.4]]) B.sack(x, z); B.crate(iw - 1.0, -1.4, .8);
  B.add(new THREE.TorusGeometry(.7, .09, 5, 12), M('gold'), 1.0, 3.0, -iw + .4, B.G.int, { shadow: false }); B.add(new THREE.TorusGeometry(.5, .09, 5, 12), M('iron'), -1.0, 3.0, -iw + .4, B.G.int, { shadow: false });
  B.bx(.1, 3.2, .5, 'darkWood', 0, 3.0, -iw + .5, B.G.int); B.lamp(1.4, 2.2, 1.0); B.banner(-iw + .1, 2.0, 0, Math.PI / 2, .7, 1.6);
  B.fullUpper({ y: 2.9, disc: iw - .05, stair: { cx: -1.1, cz: 0, dir: '-z', len: 3.2, w: 1.4 }, rooms(U) { U.sack(1.2, 0); U.sack(1.2, .9); U.crate(.6, -1.4, .8); U.barrel(1.5, -1.0); U.lamp(.6, 2.0, 0.3); U.cyl(.35, .35, .5, 'wood', 1.2, .25, 1.6, U.G.int, 8); } });
  return B.finish();
}

// ---------- 22. Lighthouse of Tidewrack Coast ----------
function lighthouse(spec, ctx) {
  const B = new Builder(ctx, spec); B.name = 'Lighthouse of Tidewrack Coast'; const R = 3.4, H = 12;
  B.roundShell({ r: R, h: H, key: 'stone', N: 18, DW: 1.9, DH: 2.5, floor: 'floorStone', T: .55 });
  for (const y of [4.2, 8]) B.ring(R + .1, .5, 'stone', 0, y, 0, B.G.ext, 14); B.ring(R + .5, .5, 'stoneD', 0, H + .2, 0, B.G.ext, 14);
  for (let i = 0; i < 20; i++) { const a = i / 20 * 6.283; B.bx(.12, 1.0, .12, 'iron', Math.sin(a) * (R + .4), H + .9, Math.cos(a) * (R + .4), B.G.ext, { shadow: false }); }
  B.add(new THREE.CylinderGeometry(1.45, 1.55, 2.2, 12, 1, true), M('#ffe49a', { emissive: new THREE.Color(0xc89a30), side: THREE.DoubleSide, transparent: true, opacity: .85 }), 0, H + 1.5, 0, B.G.ext, { shadow: false });
  B.add(new THREE.SphereGeometry(.8, 10, 8), GLOW('fff0b0', 2.2), 0, H + 1.5, 0, B.G.ext, { shadow: false }); B.cone(1.9, 1.8, 'slate', 0, H + 2.6, 0, B.G.ext, 12); B.cyl(0, .22, .6, 'gold', 0, H + 4.7, 0, B.G.ext, 6);
  for (const y of [3, 6, 9]) { const a = y * .7; B.win(Math.sin(a) * (R + .02), y, Math.cos(a) * (R + .02), a, .5, 1.0, 'glass'); }
  B.banner(0, 4.8, R + .04, 0, .8, 1.8);
  for (let i = 0; i < 9; i++) { const a = i * .9 + 2.2; const s = 1.5 + (i % 3) * .8; const m = B.add(new THREE.DodecahedronGeometry(s, 0), M('rock'), Math.sin(a) * (R + 2.0 + (i % 2)), s * .35, Math.cos(a) * (R + 2.4 + (i % 2)) - (Math.abs(a - 0) < 1 ? 0 : 0), B.G.ext); m.scale.y = .8; }
  for (let i = 0; i < 6; i++) B.bx(2.0, .3, .5, 'stone', 0, .15 + i * 0, R + 1 + i * .45, B.G.ext);
  const iw = B.iw;   // ground: hearth + table + barrels; stair flight 1 climbs the west side (stacked switchback: west, east, west)
  B.box(.9, .9, .7, iw - .8, -iw + .9, 'stoneD'); B.add(boxG(.5, .12, .4, 1), GLOW('ff7a1a', 1.4), iw - .8, .95, -iw + .9, B.G.int, { shadow: false }); B.barrel(iw - .6, .4); B.barrel(iw - .6, 1.1); B.crate(.9, 1.5, .8); B.table(1.0, -.2, .5); B.lamp(0, 3.2, 0);
  const S1 = { cx: -1.0, cz: 0, dir: '-z', len: 3.2, w: 1.4 }, S2 = { cx: 1.0, cz: 0, dir: '+z', len: 3.2, w: 1.4 };
  B.fullUpper({ level: 1, y: 4.1, disc: iw - .05, stair: S1, rooms(U) { U.chest(0, 1.65, .6); U.lamp(0, 2.6, 1.0); U.lamp(0, 2.6, -1.0); } });
  B.fullUpper({ level: 2, y: 8.2, y0: 4.1, l0: 1, disc: iw - .05, stair: S2, rooms(U) { U.chest(0, -1.65, .6); U.lamp(0, 2.6, 1.0); U.lamp(0, 2.6, -1.0); } });
  B.fullUpper({ level: 3, y: 12, y0: 8.2, l0: 2, disc: iw - .05, stair: S1, rooms(U) { U.add(new THREE.SphereGeometry(.45, 10, 8), GLOW('fff0b0', 2.2), 1.0, 1.2, 0, U.G.int, { shadow: false }); U.cyl(.5, .6, .7, 'iron', 1.0, .35, 0, U.G.int, 10); U.ccol(1.0, 0, .75); U.rugAt(1.0, 0, 1.6, 1.6, 'rug'); } });
  return B.finish();
}

// ---------- 23. Port of Varnethryl (simplified: harbour pond, pier, boats, dock warehouse/tavern, harbour sign) ----------
function port(spec, ctx) {
  const parts = []; const mk = (s, f) => { const b = f({ ...s }, ctx); parts.push(b); return b; };
  const warehouse = mk({ id: 'port', cx: spec.cx + 3, cz: spec.cz - 6, rot: 0 }, (s, c) => std(s, c, { name: 'Port Tavern & Dockmaster', w: 11, d: 8, h: 6, hs: 2.6, upper: 'darkWood', lower: 'stone', postKey: 'darkWood', rh: 3.2, ridge: 'x', over: .8, endKey: 'darkWood', sign: ['Port Tavern', '⚓', 5.9, 3.6], banners: [[-4, 4.4, .8, 1.8], [4, 4.4, .8, 1.8]], chimneys: [[-3, -2]], floor: 'floorPlank', wn: 2,
    interior(B) { const iw = B.iw, id_ = B.id_;
      B.counter(1.5, -id_ + 1.1, 4, .8); B.shelf(1.5, -id_ + .35, 3.2); B.table(-2.0, .2); B.table(-.6, 2.0); B.table(-2.4, 2.6); B.barrel(iw - .5, 0); B.barrel(iw - .5, 1); B.crate(iw - 1.2, 2.2, .9); B.tableR(-iw + 1.6, -id_ + 1.3, 2.4, 1.2, 'darkWood'); B.bx(2.6, 1.7, .1, 'parchment', -iw + 1.7, 2.3, -id_ + .2, B.G.int, { shadow: false });
      B.banner(-.4, 3.0, -id_ + .3, 0, .9, 1.8); B.lamp(-2, 3.6, 1); B.lamp(2, 3.6, 1); B.rugAt(-1.4, 1.4, 3.2, 2.8); B.hay(iw - 1.2, -id_ + .8, 1.4, 1, .8); upperStd(B, { theme: 'bed', y: 3.0, side: 'L' });
    } }));
  const B = new Builder(ctx, { id: 'port_dock', cx: spec.cx, cz: spec.cz, rot: 0 }); B.insideTest = null; B.radius = 16; B.name = 'Port of Varnethryl';
  const PW = 20, PD = 9, Z0 = 0;           // water basin local: x -10..10, z 0..9 (z grows toward the sea)
  B.add(new THREE.PlaneGeometry(PW, PD), M('water', { transparent: true, opacity: .95 }), 0, .02, Z0 + PD / 2 + .0, B.G.ext, { shadow: false }).rotation.x = -Math.PI / 2;
  B.bx(PW + 1.6, .6, .8, 'stoneD', 0, .2, Z0 - .3, B.G.ext); B.bx(.8, .6, PD + .6, 'stoneD', -PW / 2 - .4, .2, Z0 + PD / 2, B.G.ext); B.bx(.8, .6, PD + .6, 'stoneD', PW / 2 + .4, .2, Z0 + PD / 2, B.G.ext);
  B.bx(PW + 1.6, .6, .8, 'stoneD', 0, .2, Z0 + PD + .4, B.G.ext);
  B.bx(2.6, .22, PD + .8, 'wood', 0, .45, Z0 + PD / 2 + .3, B.G.ext); for (let i = 0; i < 6; i++) { B.cyl(.2, .22, 1.5, 'darkWood', -1.3, .2, Z0 + .8 + i * 1.5, B.G.ext, 6); B.cyl(.2, .22, 1.5, 'darkWood', 1.3, .2, Z0 + .8 + i * 1.5, B.G.ext, 6); }
  for (const s of [-1, 1]) B.col(s * (PW / 4 + .7), Z0 + PD / 2, PW / 2 - 1.4, PD + 1);
  for (const s of [-1, 1]) B.col(s * 6.2, Z0 + PD + .6, 9, 1);
  const boatMats = [M('darkWood'), M('wood')]; const boats = [];
  for (const [bx_, bz, s] of [[-5.5, Z0 + 4, 1], [5.8, Z0 + 6.2, .8]]) {
    const g = new THREE.Group(); g.position.set(bx_, .2, bz); B.root.add(g);
    const hull = new THREE.Mesh(boxG(1.6 * s, .6, 4.2 * s, 1.4), boatMats[0]); hull.position.y = .2; g.add(hull); const bow = new THREE.Mesh(new THREE.ConeGeometry(.8 * s, 1.4 * s, 4), boatMats[0]); bow.rotation.x = Math.PI / 2; bow.rotation.z = Math.PI / 4; bow.position.set(0, .2, 2.7 * s); g.add(bow);
    const mast = new THREE.Mesh(boxG(.1, 3.6 * s, .1, 1), boatMats[1]); mast.position.y = 2; g.add(mast); const sail = new THREE.Mesh(new THREE.PlaneGeometry(1.7 * s, 2.6 * s), M('#1f3f86', { side: THREE.DoubleSide })); sail.position.set(0, 2.2, .05); g.add(sail);
    for (const m of g.children) { m.castShadow = true; } boats.push(g); B.ccolWorld = 1; }
  B.col(-5.5, Z0 + 4, 2, 4.4); B.col(5.8, Z0 + 6.2, 1.8, 3.6);
  let t = 0; B.tick = dt => { t += dt; boats.forEach((g, i) => { g.position.y = .2 + Math.sin(t * 1.4 + i * 2) * .05; g.rotation.z = Math.sin(t * 1.1 + i) * .04; }); };
  for (const [x, z] of [[-6.5, -1.2], [-8, -1.0], [7.5, -1.1], [8.4, -1.6]]) { B.col(x, z, .9, .9); B.bx(.9, .9, .9, 'wood', x, .45, z, B.G.ext); }
  B.barrel; B.bx(.25, 3.2, .25, 'darkWood', -4, 1.6, -1.0, B.G.ext); B.add(new THREE.PlaneGeometry(2.4, 1.1), new THREE.MeshLambertMaterial({ map: signTex() , side: THREE.DoubleSide }), -4, 3.0, -.85, B.G.ext, { shadow: false, keep: true });
  for (const [x, z] of [[-9, Z0 + 9.8], [9, Z0 + 9.8]]) { B.cyl(.35, .5, 2.4, 'stone', x, 1.2, z, B.G.ext, 8); B.add(new THREE.SphereGeometry(.28, 6, 5), GLOW('ffc060', 1.5), x, 2.6, z, B.G.ext, { shadow: false }); }
  for (const x of [-8, 8]) B.banner(x, 2.4, -1.1, 0, .8, 1.8);
  // ---- harbour town backdrop: open sea beyond the quay, long pier, galleon, terraced timber houses and a rocky cliff (see Port reference)
  const wm = M('water', { transparent: true, opacity: .95 }); B.add(new THREE.PlaneGeometry(44, 18), wm, 0, .02, Z0 + PD + 9.4, B.G.ext, { shadow: false }).rotation.x = -Math.PI / 2;
  B.bx(2.6, .22, 15, 'wood', 0, .45, Z0 + PD + 8, B.G.ext); for (let i = 0; i < 8; i++) for (const s of [-1, 1]) { B.cyl(.2, .22, 1.3, 'darkWood', s * 1.4, .1, Z0 + PD + 1 + i * 1.9, B.G.ext, 6); if (i % 3 === 2) B.add(new THREE.SphereGeometry(.2, 6, 5), GLOW('ffc060', 1.6), s * 1.4, 1.5, Z0 + PD + 1 + i * 1.9, B.G.ext, { shadow: false }); }
  for (const [px, pz, pl] of [[-4, Z0 + PD + 8, 7], [4.5, Z0 + PD + 13, 6]]) { B.bx(1.8, .2, pl, 'wood', px, .42, pz, B.G.ext); for (let i = 0; i < 4; i++) for (const s of [-1, 1]) B.cyl(.16, .18, 1.1, 'darkWood', px + s * .9, .1, pz - pl / 2 + .5 + i * (pl - 1) / 3, B.G.ext, 6); }
  { // galleon: dark hull, 3 masts, cream sails, gold stern lanterns
    const g = new THREE.Group(); g.position.set(7.5, .2, Z0 + PD + 10); g.rotation.y = .12; B.root.add(g); const wd = M('darkWood'), sailM = M('#d8cba4', { side: THREE.DoubleSide });
    const hull = new THREE.Mesh(boxG(3.2, 1.3, 9, 1.4), wd); hull.position.y = .5; g.add(hull); const bow = new THREE.Mesh(new THREE.ConeGeometry(1.6, 3, 4), wd); bow.rotation.x = Math.PI / 2; bow.rotation.y = Math.PI / 4; bow.scale.set(1, 1, .8); bow.position.set(0, .5, 5.8); g.add(bow);
    const cast = new THREE.Mesh(boxG(3.0, 1.2, 2.6, 1.4), wd); cast.position.set(0, 1.7, -3.2); g.add(cast);
    for (const [mz, mh, sw] of [[2.6, 7.5, 3.4], [0, 9, 4.2], [-2.8, 6.5, 3]]) { const m = new THREE.Mesh(boxG(.2, mh, .2, 1), wd); m.position.set(0, mh / 2 + .8, mz); g.add(m); for (const [sy, sh] of [[mh * .55, mh * .38], [mh * .88, mh * .26]]) { const s = new THREE.Mesh(new THREE.PlaneGeometry(sw * (sh / (mh * .38) > .8 ? 1 : .75), sh), sailM); s.position.set(0, sy + .8, mz + .15); g.add(s); const y = new THREE.Mesh(boxG(sw + .4, .12, .12, 1), wd); y.position.set(0, sy + sh / 2 + .8, mz); g.add(y); } }
    const fl = new THREE.Mesh(new THREE.PlaneGeometry(1, .6), M('#1f3f86', { side: THREE.DoubleSide })); fl.position.set(.5, 10.1, 0); g.add(fl);
    for (const sx of [-.8, .8]) { const l = new THREE.Mesh(new THREE.SphereGeometry(.18, 6, 5), GLOW('ffc060', 1.8)); l.position.set(sx, 2.5, -4.6); g.add(l); }
    for (const m of g.children) m.castShadow = true; boats.push(g); B.col(7.5, Z0 + PD + 10, 3.4, 9.5); }
  const TERR = [[-13, -8, 6, 5.5, 0, 3.2], [15.5, -7, 6, 5, 0, 3.4], [19, -23, 5.5, 5, 3.4, 3.2], [20, -15, 5.5, 5, 1.5, 3.2]];
  for (const [hx, hz, hw, hd, hy, hh] of TERR) { if (hy) { B.bx(hw + 1.4, hy, hd + 1.4, 'stoneD', hx, hy / 2, hz, B.G.ext); } B.bx(hw, hh, hd, 'darkWood', hx, hy + hh / 2, hz, B.G.ext); B.gable(hw, hd, 2.4 + (hw > 6 ? .4 : 0), hx, hy + hh, hz, 'slate', B.G.ext, true, .6, 'timber'); B.bx(1, 1, .3, 'stoneD', hx + 1.6, hy + hh + 2.3, hz, B.G.ext);
    for (let k = -1; k <= 1; k += 2) for (const wy of [1.2, 2.5]) if (hy + wy < hy + hh) B.add(new THREE.PlaneGeometry(.7, .9), GLOW('ffb347', 1.4), hx + k * hw * .27, hy + wy, hz + hd / 2 + .02, B.G.ext, { shadow: false });
    B.bx(hw * .9, .15, 1.0, 'wood', hx, hy + 2.3, hz + hd / 2 + .5, B.G.ext); B.col(hx, hz, hw + .5, hd + .5); }
  B.rocks([[-22, -3, 4.6, 1.1], [24, -2, 4.4, 1.2], [26, -10, 5, 1.3], [-14, -2, 3.0, 1.0], [-4, -26, 6, 1.8], [7, -26, 6, 1.7], [17, -25, 5.5, 1.5], [26, -20, 5, 1.4], [-20, 6, 3.6, .8], [22, 5, 3.4, .8], [-11, Z0 - 3, 1.8, .6], [11, Z0 - 3, 1.8, .6]], '#585b61');
  B.finish(); parts.push(B);
  return { id: 'port', parts, update(hx, hz, dt, lv) { let ins = false; for (const p of parts) if (p.update(hx, hz, dt, lv)) ins = true; return ins; }, name: 'Port of Varnethryl' };
}
import { signTexture } from './bldtex.js';
const signTex = () => signTexture('PORT OF VARNETHRYL', '⚓');

// ---------- 24/25. Farmhouse & Barn ----------
const farmhouse = (spec, ctx) => std(spec, ctx, { name: 'Farmhouse of Varnethryl', w: 10, d: 8, h: 5.4, hs: 2.6, upper: 'timber', lower: 'stone', rh: 3.2, ridge: 'x', over: .7, cross: { x: -2, w: 4, depth: 4 }, post: true, chimneys: [[-3.2, -1.6, 3.4]], dormers: [-2.6, 2.6], dormY: 1.2, dormZ: .8, wn: 1,
  interior(B) { const iw = B.iw, id_ = B.id_;
    B.hearth(0, -id_ + .45, 0, 2.2); B.tableR(-2.4, .8, 2.6, 1.2); B.table(.4, 1.9, .6); B.shelf(-iw + .3, -1.8, 2.6, 1, false); B.barrel(-iw + .5, id_ - .5); B.sack(-iw + 1.2, id_ - .6); B.chest(2.0, -id_ + .7, .9);
    B.rugAt(-1, 1, 3.4, 2.6); B.lamp(-2, 3.5, 0); B.lamp(2, 3.5, 1); B.banner(-3.6, 3.6, -id_ + .3, 0, .8, 1.6); B.fullUpper({ y: 2.9, stair: { cx: iw - .9, cz: id_ - .45 - 1.7, dir: '-z', len: 3.4, w: 1.5 }, rooms(U) { U.bed(iw - 1.2, -id_ + 1.3); U.bed(-iw + 1.1, -id_ + 1.3); U.bed(-iw + 2.5, -id_ + 1.3); U.chest(0, -id_ + .6, .9); U.tableR(-1.8, .4, 1.4, .9); U.shelf(-iw + .3, .8, 2.0, 1, false); U.rugAt(-1.8, .4, 2.4, 1.8); U.lamp(0, 2.2, 0); U.hay(1.5, 0.2, 1.3, 1, .6); } });
  } });
const barn = (spec, ctx) => std(spec, ctx, { name: 'Barn of Varnethryl', w: 10, d: 12, h: 4.8, hs: 1.2, upper: 'darkWood', lower: 'stone', postKey: 'darkWood', rh: 4.4, ridge: 'z', over: .8, endKey: 'darkWood', DW: 3.4, DH: 3.6, floor: 'floorStone', windows: false,
  extra(B) { B.bx(2.0, 1.8, .1, '#241608', 0, B.h + 1.8, B.d / 2 + .06, B.G.roof, { shadow: false }); for (let i = 0; i < 3; i++) B.bx(.9, .6, .6, 'hay', -.5 + i * .5, B.h + 1.1 + i * .0, B.d / 2 - .2, B.G.roof); B.banner(-3.6, 3, B.d / 2 + .06, 0, .8, 1.6); },
  interior(B) { const iw = B.iw, id_ = B.id_;
    for (let i = 0; i < 4; i++) for (let j = 0; j < 2; j++) B.hay(-iw + 1.3 + j * 1.6, -id_ + 1 + i * 1.3, 1.4, 1.1, .9 + (i % 2) * .5); B.hay(-iw + 1.3, -id_ + 1 + 4 * 1.3, 1.4, 1.1, 1.3);
    B.bx(1.6, .5, 2.6, 'darkWood', iw - 1.6, .7, 1.2, B.G.int); B.cyl(.5, .5, .1, 'darkWood', iw - 2.3, .7, 2.2, B.G.int, 8).rotation.z = Math.PI / 2; B.col(iw - 1.6, 1.2, 1.8, 2.8);
    B.rack(iw - .3, -id_ + 1.6, 4, 1); B.barrel(iw - .6, -id_ + .6); B.barrel(iw - .6, -id_ + 3.2); B.sack(iw - 1.4, -id_ + 4); B.crate(iw - 1.5, -id_ + .7, .8);
    upperStd(B, { theme: 'store', y: 3.0, side: 'L', len: 3.6 }); B.lamp(0, 3.7, 1); B.lamp(0, 3.7, -2);
  } });

// ---------- 26. Village Houses ----------
const houseSpecs = [
  { w: 7, d: 6, h: 5.6, hs: 2.6, ridge: 'z', roofKey: 'slate', up: 'timber' }, { w: 7.5, d: 6.4, h: 5.8, hs: 2.7, ridge: 'x', roofKey: 'slate', up: 'timber' },
  { w: 6.5, d: 6, h: 5.4, hs: 2.5, ridge: 'z', roofKey: 'slateG', up: 'timber' }, { w: 7, d: 7, h: 6, hs: 2.8, ridge: 'x', roofKey: 'slate', up: 'timber' } ];
const house = n => (spec, ctx) => { const p = houseSpecs[n % 4];
  return std(spec, ctx, { name: 'Village House', w: p.w, d: p.d, h: p.h, hs: p.hs, upper: p.up, lower: 'stone', rh: 3, ridge: p.ridge, over: .7, roofKey: p.roofKey, chimneys: [[p.w * .28, -p.d * .22, 3.2]], dormers: n % 2 ? [0] : [], dormY: 1.2, dormZ: p.d * .1, banners: n === 1 ? [[-p.w * .3, p.h * .6, .6, 1.4]] : [], cross: p.ridge === 'x' ? { x: 0, w: p.w * .42, depth: p.d * .55 } : null, post: n % 2 === 0,
    interior(B) { const iw = B.iw, id_ = B.id_;
      B.hearth(0, -id_ + .45, 0, 2.0); B.bed(-iw + 1.0, -id_ + 1.7); B.table(-.6, .5, .55); B.shelf(-iw + .3, id_ - 1.9, 1.8, 1, false); B.rugAt(-.6, .5, 2.2, 2.0); B.lamp(0, 3.0, .5); B.barrel(-iw + .5, id_ - .5);
      const len = Math.min(3.4, id_ * 2 - 1.3), Y = p.hs + .35;
      B.fullUpper({ y: Y, stair: { cx: iw - .85, cz: id_ - .45 - len / 2, dir: '-z', len, w: 1.5 }, rooms(U) { U.bed(-iw + 1.0, -id_ + 1.7); U.bed(-iw + 1.0 + 1.3, -id_ + 1.7); U.chest(0, -id_ + .6, .8); U.tableR(-.4, 0, 1.2, .9); U.shelf(-iw + .3, 0.2, 1.8, 1, false); U.rugAt(-.4, 0, 2, 1.8); U.lamp(0, 2.2, 0); } });
    } }); };

// ---------- town walls & watchtowers ----------
export function buildWalls(ctx, WORLD, GATE_W) {
  const tmpl = { id: 'walls', cx: 0, cz: 0, rot: 0 }; const B = new Builder(ctx, tmpl); B.name = 'Town Walls & Watchtowers'; B.insideTest = null; B.radius = 9999;
  const run = (x1, z1, x2, z2) => { const len = Math.hypot(x2 - x1, z2 - z1), horiz = Math.abs(z2 - z1) < .01, h = 4.2, t = 1.4, cx = (x1 + x2) / 2, cz = (z1 + z2) / 2;
    B.bx(horiz ? len : t, h, horiz ? t : len, 'stone', cx, h / 2, cz, B.G.ext); B.bx(horiz ? len : t * .5, .5, horiz ? t * .5 : len, 'stoneD', cx, h + .25, cz + (horiz ? (z1 < 0 ? .4 : -.4) : 0) + 0, B.G.ext) ; B.bx(horiz ? len : .4, .3, horiz ? .4 : len, 'stoneD', cx + (horiz ? 0 : (x1 < 0 ? .5 : -.5)), h + .15, cz + (horiz ? (z1 < 0 ? .5 : -.5) : 0), B.G.ext);
    const n = Math.floor(len / 1.8); for (let i = 0; i < n; i++) { const f = (i + .5) / n, px = x1 + (x2 - x1) * f, pz = z1 + (z2 - z1) * f; B.bx(horiz ? .9 : t, .8, horiz ? t : .9, 'stone', px, h + .4 + .3, pz, B.G.ext); }
    const nb = Math.floor(len / 9); for (let i = 1; i < nb; i++) { const f = i / nb, px = x1 + (x2 - x1) * f, pz = z1 + (z2 - z1) * f, sx = horiz ? 0 : (x1 < 0 ? 1 : -1), sz = horiz ? (z1 < 0 ? 1 : -1) : 0; B.bx(1.1, 4.8, 1.1, 'stoneD', px + sx * (t / 2 + .3), 2.4, pz + sz * (t / 2 + .3), B.G.ext); if (i % 2) B.banner(px + sx * (t / 2 + .02), 2.6, pz + sz * (t / 2 + .02), horiz ? (z1 < 0 ? 0 : Math.PI) : (x1 < 0 ? Math.PI / 2 : -Math.PI / 2), 1.1, 2.6); }
    B.col(cx, cz, horiz ? len : t, horiz ? t : len); };
  const g = GATE_W;
  run(-WORLD, -WORLD, WORLD, -WORLD); run(-WORLD, -WORLD, -WORLD, WORLD); run(WORLD, -WORLD, WORLD, WORLD); run(-WORLD, WORLD, -7.4, WORLD); run(7.4, WORLD, WORLD, WORLD);
  const towers = []; const tw = (x, z, enter) => { if (!enter) { B.tower(x, z, 2.4, 7.6, { coneH: 5.4, windows: 3, wa: x + z }); B.banner(x, 4.2, z + (z < 0 ? 2.5 : -2.5), z < 0 ? 0 : Math.PI, 1, 2.2); return; }
    const th = Math.atan2(-x, -z), t = new Builder(ctx, { id: 'wt' + towers.length, cx: x, cz: z, rot: th }); t.name = 'Watchtower'; t.roundShell({ r: 3.4, h: 8, key: 'stone', N: 16, T: .6, floor: 'floorStone' });
    t.ring(3.7, .5, 'stoneD', 0, 8.25, 0, t.G.ext, 16); for (let i = 0; i < 10; i++) { const a = i / 10 * 6.283; t.bx(.7, .7, .7, 'stone', Math.sin(a) * 3.55, 8.85, Math.cos(a) * 3.55, t.G.ext); }
    t.cone(4.2, 6.2, 'slate', 0, 8.5, 0, t.G.roof, 16); t.banner(0, 4.6, 3.4 + .05, 0, 1, 2.4);
    for (let i = 0; i < 3; i++) { const a = 2.2 + i * 1.3; t.win(Math.sin(a) * 3.45, 5, Math.cos(a) * 3.45, a, .4, .9, 'glass'); }
    const iw = t.iw; t.table(0, -.6, .7); t.rack(-iw + .5, -.5, 4, 1); t.bed(iw - 1.0, -1.0, 1); t.barrel(iw - 1, 1.6); t.crate(-iw + 1, 1.6, .8); t.lamp(0, 3.4, 0);
    { const S1 = { cx: -1.2, cz: 0, dir: '-z', len: 3.6, w: 1.4 }, S2 = { cx: 1.2, cz: 0, dir: '+z', len: 3.6, w: 1.4 };
      t.fullUpper({ level: 1, y: 4.0, disc: iw - .05, stair: S1, rooms(U) { U.lamp(0, 2.6, 0); } });
      t.fullUpper({ level: 2, y: 8.0, y0: 4.0, l0: 1, disc: iw - .05, stair: S2, rooms(U) { U.barrel(-1.6, -1.5); U.crate(-1.7, 1.5, .7); U.lamp(0, 1.6, 0); } }); }
    t.radius = 8; t.finish(); towers.push(t); };
  const E = WORLD - 4;
  tw(-E, -E, true); tw(E, -E, true); tw(-E, E, true); tw(E, E, true);
  for (const [x, z] of [[0, -WORLD], [-30, -WORLD], [30, -WORLD], [-WORLD, 0], [WORLD, 0], [-WORLD, 30], [WORLD, 30], [-WORLD, -30], [WORLD, -30], [-30, WORLD], [30, WORLD]]) tw(x, z, false);
  B.finish(); return { id: 'walls', parts: [B, ...towers], update(hx, hz, dt, lv) { let ins = null; for (const p of towers) if (p.update(hx, hz, dt, lv)) ins = p.id; return ins; } };
}

// ---------- registry + village layout ----------
export const BUILDING_DEFS = [
  { id: 'guildhall', f: guildhall, cx: 0, cz: -21, rot: 0, name: 'Guild Hall' },
  { id: 'library', f: library, cx: -24, cz: -27, rot: 0, name: 'Grand Library' },
  { id: 'townhall', f: townhall, cx: 23, cz: -26, rot: 0, name: 'Town Hall' },
  { id: 'mage', f: mage, cx: -44, cz: -31, rot: 0, name: 'Mage Academy' },
  { id: 'treasury', f: treasury, cx: 41, cz: -27, rot: 0, name: 'Treasury' },
  { id: 'keep', f: keep, cx: 0, cz: -48, rot: 0, name: 'Castle Keep' },
  { id: 'observatory', f: observatory, cx: -41, cz: -46, rot: 0, name: 'Observatory' },
  { id: 'crypt', f: crypt, cx: 43, cz: -45, rot: 0, name: 'Crypt' },
  { id: 'market', f: market, cx: -24, cz: -6, rot: Math.PI / 2, name: 'Market Provisioner' },
  { id: 'apothecary', f: apothecary, cx: -24, cz: 8, rot: Math.PI / 2, name: 'Apothecary' },
  { id: 'bakery', f: bakery, cx: -24, cz: 20, rot: Math.PI / 2, name: 'Bakery' },
  { id: 'inn', f: inn, cx: 24, cz: -8, rot: -Math.PI / 2, name: 'Inn' },
  { id: 'smithy', f: smithy, cx: 24, cz: 6, rot: -Math.PI / 2, name: 'Blacksmith' },
  { id: 'temple', f: temple, cx: 46, cz: -8, rot: -Math.PI / 2, name: 'Temple' },
  { id: 'training', f: training, cx: 45, cz: 10, rot: -Math.PI / 2, name: 'Training Hall' },
  { id: 'colosseum', f: colosseum, cx: 42, cz: 38, rot: 0, name: 'Colosseum' },
  { id: 'thieves', f: thieves, cx: -40, cz: 8, rot: 0, name: "Thieves' Den" },
  { id: 'farmhouse', f: farmhouse, cx: -42, cz: -9, rot: 0, name: 'Farmhouse' },
  { id: 'barn', f: barn, cx: -51, cz: 22, rot: Math.PI / 2, name: 'Barn' },
  { id: 'stables', f: stables, cx: -22, cz: 36, rot: 0, name: 'Stables' },
  { id: 'windmill', f: windmill, cx: 20, cz: 46, rot: 0, name: 'Windmill' },
  { id: 'house1', f: house(0), cx: -9, cz: 19, rot: Math.PI, name: 'Village House' },
  { id: 'house2', f: house(1), cx: 9, cz: 19, rot: Math.PI, name: 'Village House' },
  { id: 'house3', f: house(2), cx: -9, cz: 31, rot: Math.PI, name: 'Village House' },
  { id: 'house4', f: house(3), cx: 9, cz: 31, rot: Math.PI, name: 'Village House' },
  { id: 'lighthouse', f: lighthouse, cx: -33, cz: 51, rot: 0, name: 'Lighthouse' },
  { id: 'port', f: port, cx: -45, cz: 40, rot: 0, name: 'Port' },
  { id: 'gatehouse', f: gatehouse, cx: 0, cz: 59, rot: 0, name: 'Gatehouse' },
  { id: 'fountain', f: fountain, cx: 0, cz: 0, rot: 0, name: 'Fountain Monument' },
];
export function buildVillage(ctx, only) {
  const out = []; for (const d of BUILDING_DEFS) { if (only && !only.includes(d.id)) continue; const b = d.f({ id: d.id, cx: d.cx, cz: d.cz, rot: d.rot }, ctx); b.defName = d.name; b.def = d; out.push(b); } return out;
}
