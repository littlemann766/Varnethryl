/* Unit test for www/proto3d/bump.js. Run: node tools/bump_test.mjs */
import { createBump, makeActor, STYLES, COOLDOWN, CONTACT_R, findNodes, restoreNodes, applyPose } from '../www/proto3d/bump.js';
let bad = 0;
const ok = (n, c, d) => { console.log((c ? 'PASS ' : 'FAIL ') + n + (d ? ' ' + d : '')); if (!c) bad++; };
const IDS = ['aldric','elira','thorne','nyx','rowan','seraphine','garruk','mirelle','cedric','morwen','kael','vesper','talia','orin','selene','darius','finn','brynn','asha','rook'];
ok('20 hero styles', IDS.every(i => STYLES[i]), IDS.filter(i => !STYLES[i]).join());
const mk = (id, x, z, opts) => { const a = makeActor(id, opts); a.x = x; a.z = z; return a; };
function runInto(runnerId, bumpedId, dist) {
  const sys = createBump(), r = mk(runnerId, 0, 0, { fixed: true }), b = mk(bumpedId, 0, dist || 0.8);
  sys.add(r); sys.add(b); r.vz = 5; sys.update(1 / 60); r.vz = 0;
  return { sys, r, b };
}
{ /* bump happens: bumped shoved sideways + stumbles, runner staggers and slows */
  const { sys, r, b } = runInto('aldric', 'rowan');
  ok('bump event fired', sys.events === 1);
  ok('bumped stumbling', b.bT > 0 && b.bumped === 1);
  ok('runner staggers + slows', r.rT > 0 && r.bumps === 1 && r.slowT > 0);
  let moved = 0; for (let i = 0; i < 40; i++) { sys.update(1 / 60); moved += Math.hypot(b.dx, b.dz); b.x += b.dx; b.z += b.dz; }
  ok('bumped gets shoved a small distance', moved > 0.1 && moved < 1.3, 'moved ' + moved.toFixed(2));
  ok('runner slowdown within limits', r.slowMul >= 0.2 && r.slowMul <= 1);
}
{ /* cooldown 1.5 s per pair */
  const { sys, r, b } = runInto('nyx', 'finn');
  let ev = sys.events; for (let i = 0; i < 60; i++) { r.vz = 5; b.x = 0; b.z = 0.8; r.x = 0; r.z = 0; sys.update(1 / 60); }
  ok('no re-bump inside cooldown', sys.events === ev, 'events ' + sys.events);
  for (let i = 0; i < 60; i++) { r.vz = 5; b.x = 0; b.z = 0.8; r.x = 0; r.z = 0; sys.update(1 / 60); }
  ok('re-bump after cooldown', sys.events === ev + 1, 'events ' + sys.events + ' cd ' + COOLDOWN);
}
{ /* STR scaling */
  const a1 = runInto('garruk', 'finn'), a2 = runInto('rowan', 'finn');
  const sh = x => Math.hypot(x.b.svx, x.b.svz);
  ok('stronger runner shoves harder', sh(a1) > sh(a2) * 1.8, sh(a1).toFixed(2) + ' vs ' + sh(a2).toFixed(2));
  ok('stronger runner tilts bumped more', a1.b.bTilt > a2.b.bTilt);
  const h1 = runInto('aldric', 'garruk'), h2 = runInto('aldric', 'rowan');
  ok('heavier bumped hero resists', sh(h1) < sh(h2));
}
{ /* slow only on the runner; below run speed nothing happens */
  const sys = createBump(), a = mk('aldric', 0, 0, { fixed: true }), b = mk('elira', 0, 0.7); sys.add(a); sys.add(b); a.vz = 0.5; sys.update(1 / 60);
  ok('walking contact does not bump', sys.events === 0);
}
{ /* no stacking: soft actors dropped on the same spot spread out; the fixed player is never moved */
  const sys = createBump(), p = mk('aldric', 0, 0, { fixed: true }), f = [mk('elira', 0.1, 0.1), mk('orin', -0.1, 0), mk('finn', 0, 0), mk('thorne', 0.05, 0.02)];
  sys.add(p); f.forEach(x => sys.add(x));
  for (let i = 0; i < 400; i++) { sys.update(1 / 60); for (const x of f) { x.x += x.dx; x.z += x.dz; } }
  let minD = 9; const all = [p, ...f]; for (let i = 0; i < all.length; i++) for (let j = i + 1; j < all.length; j++) minD = Math.min(minD, Math.hypot(all[i].x - all[j].x, all[i].z - all[j].z));
  ok('no overlap after settling', minD > CONTACT_R * 2 * 0.95, 'min dist ' + minD.toFixed(2));
  ok('fixed player never displaced', p.x === 0 && p.z === 0 && p.dx === 0 && p.dz === 0);
  ok('settled party does not bump', sys.events === 0);
}
{ /* NaN / bad input safety */
  const sys = createBump(), a = mk('aldric', NaN, 0, { fixed: true }), b = mk('rowan', 0, Infinity); sys.add(a); sys.add(b);
  a.vx = NaN; b.vz = undefined; sys.update(NaN); sys.update(-5); sys.update(1e9);
  ok('NaN inputs give finite outputs', [a, b].every(x => ['dx','dz','slowMul','ptx','ptz','pyaw','phop','pfl','pfr','phead'].every(k => isFinite(x[k]))));
  const c = mk('x-unknown-hero', 0, 0, { str: NaN }), d = mk('rowan', 0.5, 0); const s2 = createBump(); s2.add(c); s2.add(d); c.vx = 6; s2.update(1 / 60);
  ok('unknown hero uses default style, finite str', isFinite(c.str) && s2.events === 1);
  ok('actor cap', (() => { const s = createBump(); let n = 0; for (let i = 0; i < 40; i++) if (s.add(mk('aldric', i * 5, 0))) n++; return n === 12; })());
}
{ /* all 20 heroes: pose stays finite and bounded, returns to rest */
  let worst = 0, fin = true;
  for (const id of IDS) for (const other of ['garruk', 'rowan']) {
    const { sys, r, b } = runInto(id, other), { sys: s2, r: r2, b: b2 } = runInto(other, id);
    for (let i = 0; i < 120; i++) {
      sys.update(1 / 60); s2.update(1 / 60);
      for (const x of [r, b, r2, b2]) for (const k of ['ptx', 'ptz', 'pyaw', 'phop', 'pfl', 'pfr', 'phead']) { if (!isFinite(x[k])) fin = false; if (k !== 'pyaw') worst = Math.max(worst, Math.abs(x[k])); }
    }
    if (Math.hypot(b.ptx, b.ptz, b.phop, b.pfl, b.phead) > 1e-6 || r.slowMul !== 1) fin = false;
  }
  ok('20 heroes: finite, bounded (<~1.3 rad / m), settle to rest', fin && worst < 1.3, 'peak ' + worst.toFixed(2));
}
{ /* applyPose with fake rigid nodes: no accumulation, restores base quaternion */
  const node = n => ({ name: n, isMesh: false, quaternion: { x: 0.1, y: 0.2, z: 0.3, w: Math.sqrt(1 - 0.14) }, children: [] });
  const root = { rotation: { x: 0, y: 0, z: 0, order: 'XYZ' }, position: { y: 0 }, traverse(f) { f(this); this.kids.forEach(f); }, kids: [node('upperArm_L'), node('upperArm_R'), node('head'), node('hand_L')] };
  const nd = findNodes(root), a = makeActor('rowan'); a.pfl = 0.5; a.pfr = -0.4; a.phead = 0.3; a.ptx = 0.2; a.phop = 0.1;
  ok('finds 3 rigid nodes', nd.list.length === 3);
  const q0 = { ...root.kids[0].quaternion };
  for (let i = 0; i < 50; i++) { restoreNodes(nd); applyPose(a, root, nd, 1.0); }
  const q = root.kids[0].quaternion, len = Math.hypot(q.x, q.y, q.z, q.w);
  ok('offset applied, quaternion unit length', Math.abs(len - 1) < 1e-6 && Math.abs(q.x - q0.x) > 0.01);
  ok('root order YXZ and pose set', root.rotation.order === 'YXZ' && root.rotation.x === 0.2 && root.position.y === 0.1 && root.rotation.y === 1.0);
  a.pfl = a.pfr = a.phead = 0; restoreNodes(nd); applyPose(a, root, nd, 0);
  ok('restores exactly (no drift after 50 frames)', Math.abs(root.kids[0].quaternion.x - q0.x) < 1e-12 && Math.abs(root.kids[0].quaternion.w - q0.w) < 1e-12);
}
{ /* allocation-free update: heap should not grow */
  const sys = createBump(), r = mk('aldric', 0, 0, { fixed: true }), b = mk('rowan', 0, 0.8); sys.add(r); sys.add(b);
  for (let i = 0; i < 2000; i++) { r.vz = 5; sys.update(1 / 60); } if (global.gc) global.gc();
  const h0 = process.memoryUsage().heapUsed; for (let i = 0; i < 200000; i++) { r.vz = 5; r.x = 0; r.z = 0; b.x = 0; b.z = 0.8; sys.update(1 / 60); } if (global.gc) global.gc();
  const dh = process.memoryUsage().heapUsed - h0; ok('update() allocation-free over 200k frames', dh < 2e6, (dh / 1e6).toFixed(2) + ' MB');
}
console.log(bad ? bad + ' FAILED' : 'ALL PASS'); process.exit(bad ? 1 : 0);
