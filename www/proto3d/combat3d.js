/* 3D combat host (thin): turns CombatController events into world effects. Rules live in ./combat/* (shared with the fight-test work: no THREE, no DOM),
 * the HUD in ./combathud.js, enemy visuals in ./foes.js. Lazy-loaded by main.js only when combat is switched on.
 * Draw-call budget: <= 6 enemies x 1 mesh, telegraph planes only while winding up, 1 slash arc, 1 target ring, owner saber 3 meshes. */
import { CombatController } from './combat/controller.js';
import { createCombatHud } from './combathud.js';
import { createFoe } from './foes.js';
import { ENEMIES, SABER } from './combat/data.js';
import { loadLucian } from './combat/calc.js';

export const MAX_ENEMIES = 6, TARGET_ALIVE = 3, RESPAWN_S = 6, SPAWN_MIN = 14, SPAWN_MAX = 26, SOFT_RANGE = 8;
export const TITAN_DIST = 24, TITAN_RESPAWN_S = 45;
export const SPAWN_TABLE = ['wolf', 'wolf', 'raider', 'wraith'];
const yawLerp = (cur, to, k) => cur + (((to - cur + Math.PI * 3) % (Math.PI * 2)) - Math.PI) * k;

/* env: {THREE, scene, camera, state, HS, WORLD, resolve(p), free(x,z), hero(), flags, getCheats(), isOwner(), camRig, start:{x,z}} */
export function createCombat(env) {
  const { THREE, scene, camera, state, HS, flags } = env;
  let on = false, spawnT = 0, kills = 0, seq = 0, titanT = 1.5;
  const tmp = { x: 0, z: 0 }, v3 = new THREE.Vector3(), sc = [0, 0];
  const project = (x, y, z, out) => { v3.set(x, y, z).project(camera); if (v3.z > 1 || Math.abs(v3.x) > 1.3 || Math.abs(v3.y) > 1.3) return false; out[0] = (v3.x * 0.5 + 0.5) * innerWidth; out[1] = (-v3.y * 0.5 + 0.5) * innerHeight; return true; };
  const cc = new CombatController({ HS, move: (e, dx, dz) => { tmp.x = e.x + dx; tmp.z = e.z + dz; env.resolve(tmp); e.x = tmp.x; e.z = tmp.z; } });
  loadLucian();
  const api = {
    use: (i) => { if (on) cc.use(i); }, dodge: () => { if (on) cc.dodge(A.vx, A.vz); }, lock: () => { if (on) cc.lock(); }, next: () => { if (on) cc.switchTarget(); },
  };
  const hud = createCombatHud(cc, api, project);
  const A = { vx: 0, vz: 0, lx: 0, lz: 0, dash: null, swing: null, slash: -1 };
  const pool = []; const freeFoes = [];
  const getFoe = () => { let f = freeFoes.pop(); if (!f) { f = createFoe(scene, HS); pool.push(f); } return f; };

  /* ---- fx: slash arc, soft/lock target ring, owner saber ---- */
  const arcGeo = new THREE.RingGeometry(0.55, 1, 28, 1, -1.1, 2.2);
  const arc = new THREE.Mesh(arcGeo, new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.8, side: THREE.DoubleSide, depthWrite: false, blending: THREE.AdditiveBlending }));
  arc.rotation.x = -Math.PI / 2; arc.visible = false; scene.add(arc);
  const reticle = new THREE.Mesh(new THREE.RingGeometry(0.8, 1, 28), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.5, side: THREE.DoubleSide, depthWrite: false }));
  reticle.rotation.x = -Math.PI / 2; reticle.visible = false; scene.add(reticle);
  const saber = new THREE.Group();
  const SAB_LEN = 1.5 * HS * 0.8;
  const hilt = new THREE.Mesh(new THREE.CylinderGeometry(0.04 * HS, 0.045 * HS, 0.32 * HS, 8), new THREE.MeshLambertMaterial({ color: 0x2a2c33 })); hilt.position.y = 0.16 * HS;
  const blade = new THREE.Mesh(new THREE.CylinderGeometry(0.028 * HS, 0.028 * HS, SAB_LEN, 8), new THREE.MeshBasicMaterial({ color: 0xf4e8ff }));
  const glow = new THREE.Mesh(new THREE.CylinderGeometry(0.075 * HS, 0.075 * HS, SAB_LEN * 1.03, 10), new THREE.MeshBasicMaterial({ color: 0xa24dff, transparent: true, opacity: 0.55, depthWrite: false, blending: THREE.AdditiveBlending }));
  blade.geometry.translate(0, 0.32 * HS + SAB_LEN / 2, 0); glow.geometry.translate(0, 0.32 * HS + SAB_LEN / 2, 0);
  saber.add(hilt, blade, glow); saber.visible = false; scene.add(saber);
  let ignite = 0;
  const isOwner = () => !!env.isOwner();
  const saberOn = () => on && isOwner() && cc.dead <= 0 && !env.camRig.fp;   /* first person: the held model would fill the screen */

  const syncHero = () => { const own = isOwner(), want = own, id = own ? 'owner' : 'hero'; if (cc.hero.id !== id || cc.hero.saber !== want) cc.setHero({ id, saber: want, name: own ? 'Owner' : 'Hero' }); };

  /* ---- events ---- */
  cc.on('action', (ev) => {
    A.swing = { t: 0, T: Math.max(0.25, ev.T), big: ev.a.id === 'heavy' ? 1.4 : 1 }; A.slash = 0;
    if (ev.aim && ev.a.kind !== 'storm' && ev.a.kind !== 'aoe') state.yaw = Math.atan2(ev.aim.x - state.heroX, ev.aim.z - state.heroZ);
  }).on('dash', (d) => { A.dash = { dx: d.dx, dz: d.dz, left: d.dist, spd: d.dist / d.T }; })
    .on('damage', (d) => {
      if (!d.toPlayer) { hud.floatAt(d.e.x, d.e.top || 2.5, d.e.z, Math.round(d.dmg).toLocaleString('en-US'), d.crit || d.dmg >= 5000 ? 'big' : ''); return; }
      const ch = env.getCheats(), kept = ch && ch.mitigate ? ch.mitigate(d.dmg) : (flags.god ? 0 : d.dmg);
      if (kept < d.dmg) cc.res.hp = Math.min(cc.res.max.hp, cc.res.hp + (d.dmg - kept));
      if (kept > 0) { hud.floatAt(state.heroX, 2.6 * HS, state.heroZ, '-' + Math.round(kept), 'pl'); hud.hurtFlash(); }
    })
    .on('enemyAttack', (a) => { if (a.result === 'dodged' || (a.result === 'hit' && flags.god)) hud.floatAt(state.heroX, 2.8 * HS, state.heroZ, flags.god ? 'GOD' : 'DODGE', 'heal'); else if (a.result === 'missed') hud.floatAt(a.e.x, a.e.top || 2.5, a.e.z, 'MISS', 'heal'); })
    .on('defeat', (e) => { kills++; hud.say(e.def.name + ' defeated', 1100); })
    .on('playerDown', () => { hud.say('You fell...', 2500); env.hero().rotation.x = -1.3; })
    .on('respawn', () => { state.heroX = env.start.x; state.heroZ = env.start.z; state.target = null; env.hero().rotation.x = 0; spawnT = 1; })
    .on('remove', (e) => { if (e.foe) { e.foe.hide(); freeFoes.push(e.foe); e.foe = null; } });

  function spawn(key, dist) {
    if (cc.enemies.length >= MAX_ENEMIES + (key === 'titan' ? 1 : 0)) return null;
    let x = state.heroX + 12, z = state.heroZ, ok = false;
    for (let k = 0; k < 24 && !ok; k++) { const a = Math.random() * 6.283, r = (dist || (SPAWN_MIN + Math.random() * (SPAWN_MAX - SPAWN_MIN))) * HS / 1.5, px = state.heroX + Math.cos(a) * r, pz = state.heroZ + Math.sin(a) * r; if (Math.abs(px) < env.WORLD - 8 && Math.abs(pz) < env.WORLD - 8 && env.free(px, pz)) { x = px; z = pz; ok = true; } }
    if (!ok) return null;
    const f = getFoe(); f.setKind(key === 'wolf' ? 'wolf' : key === 'wraith' ? 'wraith' : key === 'titan' ? 'titan' : 'raider');
    f.mesh.visible = true; f.mesh.rotation.set(0, 0, 0); f.mesh.position.set(x, 0, z); f.mat.emissive.setHex(0);
    return cc.addEnemy(key, x, z, { foe: f, top: f.top, px: x, pz: z, flashOn: false });
  }

  /* ---- input ---- */
  const typing = (t) => !!t && /INPUT|TEXTAREA|SELECT/.test(t.tagName);
  const onKey = (e) => {
    if (!on || e.repeat || typing(e.target) || e.ctrlKey || e.metaKey || e.altKey) return; const k = e.key;
    if (k === 'f' || k === 'F' || k === 'j' || k === 'J') api.use(0); else if (k === 'g' || k === 'G') api.dodge(); else if (k === 't' || k === 'T') api.lock();
    else if (k === 'Tab') { e.preventDefault(); api.next(); } else if (k === 'h' || k === 'H') api.use(1); else if (k >= '1' && k <= '6') api.use(+k - 1);
  };

  function update(dt) {
    if (!on) return; dt = Math.min(dt, 0.1); syncHero(); cc.god = !!flags.god;
    { const dx = state.heroX - A.lx, dz = state.heroZ - A.lz; A.lx = state.heroX; A.lz = state.heroZ; const l = Math.hypot(dx, dz); if (l > 0.005 && !A.dash) { A.vx = dx / l; A.vz = dz / l; } else if (l <= 0.005) { A.vx = 0; A.vz = 0; } }
    const safe = state.level > 0 || !!state.inside;
    const fp = !!env.camRig.fp;
    cc.setPlayer(state.heroX, state.heroZ, state.yaw);
    const t = cc.tgt.target;
    if (cc.tgt.locked && t && cc.dead <= 0) {
      state.yaw = yawLerp(state.yaw, Math.atan2(t.x - state.heroX, t.z - state.heroZ), Math.min(1, dt * 9));
      if (!env.camRig.pinching) state.camYaw = yawLerp(state.camYaw, Math.atan2(state.heroX - t.x, state.heroZ - t.z), Math.min(1, dt * 2.5));
    }
    if (safe) { cc.cd.tick(dt); cc.res.tick(dt, false); for (const e of cc.enemies) { if (e.state === 'telegraph' || e.state === 'attack') cc.ai.set(e, 'idle'); } } else cc.update(dt);
    spawnT -= dt; let alive = 0, titan = null; for (const e of cc.enemies) if (e.key === 'titan') { if (e.state !== 'defeated') titan = e; } else if (e.state !== 'defeated') alive++;
    if (!safe && !titan && cc.dead <= 0) { titanT -= dt; if (titanT <= 0) { titanT = TITAN_RESPAWN_S; if (spawn('titan', TITAN_DIST)) hud.say('The Ashen Titan awakens!', 2200); else titanT = 3; } }
    if (!safe && spawnT <= 0 && alive < TARGET_ALIVE && cc.dead <= 0) { spawnT = RESPAWN_S; spawn(SPAWN_TABLE[seq++ % SPAWN_TABLE.length]); }
    if (fp && cc.tgt.locked && t && cc.dead <= 0) {   /* first person: tilt the view up/down toward the locked target (a 3x-tall titan sits well above eye level) */
      const eye = env.hero().position.y + HS * 1.55, d = Math.max(2, Math.hypot(t.x - state.heroX, t.z - state.heroZ)), want = Math.max(-0.5, Math.min(1.1, Math.atan2((t.top || 2.5) * 0.6 - eye, d)));
      env.camRig.pitch += (want - env.camRig.pitch) * Math.min(1, dt * 4);
    }
    if (A.dash) { const d = A.dash, s = Math.min(d.left, d.spd * dt); tmp.x = state.heroX + d.dx * s; tmp.z = state.heroZ + d.dz * s; env.resolve(tmp); state.heroX = tmp.x; state.heroZ = tmp.z; d.left -= s; if (d.left <= 0.01) A.dash = null; }
    const soft = cc.tgt.locked ? cc.tgt.target : cc.tgt.nearest(cc.enemies, state.heroX, state.heroZ, state.yaw, SOFT_RANGE * HS);
    if (soft && !cc.tgt.locked) cc.lastTarget = soft;
    if (soft) { reticle.visible = true; reticle.position.set(soft.x, 0.14, soft.z); reticle.scale.setScalar(Math.max(0.8, soft.def.r * 1.4)); reticle.material.color.setHex(cc.tgt.locked ? 0xffd54a : 0xffffff); reticle.material.opacity = cc.tgt.locked ? 0.95 : 0.4; } else reticle.visible = false;
    for (const e of cc.enemies) {
      const f = e.foe; if (!f) continue; const m = f.mesh;
      if (e.state === 'defeated') { m.rotation.x = -Math.min(1.4, e.deadT * 4); m.position.y = -Math.max(0, e.deadT - 1.2) * 1.2; f.tele.visible = false; if (e.deadT > 2.4) { cc.removeEnemy(e); } continue; }
      m.position.x = e.x; m.position.z = e.z; m.rotation.y = yawLerp(m.rotation.y, e.yaw, Math.min(1, dt * 10));
      const lean = e.state === 'telegraph' ? -0.3 * Math.min(1, e.tStateT / e.def.tele) : e.state === 'attack' ? 0.4 : e.state === 'stagger' ? -0.5 : 0; m.rotation.x += (lean - m.rotation.x) * Math.min(1, dt * 14);
      if (e.state === 'telegraph') { const reach = (e.def.reach * HS + e.def.r) * 1.1, p = Math.min(1, e.tStateT / e.def.tele); f.tele.visible = true; f.tele.position.set(e.x, 0.12, e.z); f.tele.scale.setScalar(reach); f.tele.material.opacity = 0.35 + 0.6 * p; } else if (f.tele.visible) f.tele.visible = false;
      const fl = e.flash > 0 || e.state === 'telegraph'; if (fl !== e.flashOn) { e.flashOn = fl; f.mat.emissive.setHex(e.flash > 0 ? 0xff2020 : fl ? 0x551100 : 0); }
    }
    /* slash arc + saber */
    if (A.slash >= 0) { A.slash += dt; const u = A.slash / 0.22; if (u >= 1) { A.slash = -1; arc.visible = false; } else { arc.visible = true; arc.position.set(state.heroX, 0.9 * HS, state.heroZ); arc.rotation.z = state.yaw + Math.PI / 2 + (u - 0.5) * 1.2; arc.scale.setScalar((cc.act && cc.act.a.range ? cc.act.a.range : 4.6) * HS * 0.45 * (0.8 + u * 0.3)); arc.material.opacity = 0.8 * (1 - u); } }
    const sv = saberOn(); saber.visible = sv;
    if (sv) {
      ignite = Math.min(1, ignite + dt * 4); blade.scale.y = glow.scale.y = Math.max(0.001, ignite);
      const sw = A.swing; let sweep = 0, tilt = 0.35; if (sw) { sw.t += dt; const p = Math.min(1, sw.t / sw.T); sweep = (p - 0.5) * 3.0 * sw.big; tilt = 1.3 + Math.sin(p * Math.PI) * 0.25; if (p >= 1) A.swing = null; }
      const y = state.yaw + sweep, sx = Math.cos(state.yaw), sz = -Math.sin(state.yaw);
      saber.position.set(state.heroX + sx * 0.42 * HS + Math.sin(state.yaw) * 0.25 * HS, env.hero().position.y + 0.85 * HS, state.heroZ + sz * 0.42 * HS + Math.cos(state.yaw) * 0.25 * HS);
      saber.rotation.set(0, y, 0); saber.rotateX(tilt);
    } else ignite = 0;
    hud.update(dt, cc.enemies, isOwner());
  }
  function start() {
    if (on) return; on = true; cc.res.full(); cc.cd.reset(); cc.dead = 0; spawnT = 0.5; titanT = 1.5; hud.show(true); syncHero(); cc.res.full(); addEventListener('keydown', onKey);
    hud.say(isOwner() ? 'FIGHT: F attack · G dodge · T lock-on · 1-6 abilities' : 'FIGHT: F attack · G dodge · T lock-on', 2600);
  }
  function stop() {
    if (!on) return; on = false; hud.show(false); cc.clearEnemies(); titanT = 1.5; arc.visible = reticle.visible = saber.visible = false; A.dash = null; A.swing = null; env.hero().rotation.x = 0; removeEventListener('keydown', onKey);
  }
  return { start, stop, update, spawn, cc, hud, api, get on() { return on; }, get kills() { return kills; }, get enemies() { return cc.enemies; }, get saberVisible() { return saber.visible; }, pool, SABER_DAMAGE: SABER.max };
}
