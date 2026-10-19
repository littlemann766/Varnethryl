/* Fight test adapter (Phase 1 combat layer host). Owner-gated sandbox. Rules live in ./combat/controller.js (no THREE/DOM), the HUD in ./combat/hud.js
   (presentation only). This file only turns controller events into world effects: models, saber, animation, dash/jump, telegraph rings, spawning.
   Reads for combat: player x/z/yaw only. */
import { CombatController } from './combat/controller.js';
import { CombatHUD } from './combat/hud.js';
import { loadLucian } from './combat/calc.js';
import { SABER, ENEMIES, WAVE_TABLE, ABILITIES } from './combat/data.js';
export const SABER_DAMAGE = SABER.max;     // 99,999 flat per hit
export const SABER_GLB = null;             // URL (or fight.setSaberModel(url)) for Beth's saber: hilt at origin, blade along +Y, ~1 m
const MAX_ALIVE = 5, AUTO_MAX = 9, AUTO_AGGRO = 3;   // Wilds: up to 9 passive mobs, aggro only within 3 m
export function createFight(env) {
  const { THREE, scene, camera, state, HS } = env;
  let on = false, saber = null, saberUrl = SABER_GLB, wave = 1, sheathed = false, spawnT = 0, bossOn = false;
  const v3 = new THREE.Vector3(), sc = [0, 0];
  const project = (x, y, z, out) => { v3.set(x, y, z).project(camera); if (v3.z > 1 || Math.abs(v3.x) > 1.3 || Math.abs(v3.y) > 1.3) return false; out[0] = (v3.x * 0.5 + 0.5) * innerWidth; out[1] = (-v3.y * 0.5 + 0.5) * innerHeight; return true; };
  const cc = new CombatController({ HS, move: (e, dx, dz) => { const p = { x: e.x + dx, z: e.z + dz }; env.resolve(p); e.x = p.x; e.z = p.z; } });
  loadLucian();
  const isOwner = () => /(^|:)owner/.test(env.heroId());
  const A = { vx: 0, vz: 0, lx: 0, lz: 0, dash: null, jump: -1, spin: 0, swing: null, fx: null };   // player-side animation state
  const api = {
    use: i => { if (on) cc.use(i); }, dodge: () => { if (on) cc.dodge(A.vx, A.vz); }, block: b => { if (on) cc.block(b); }, jump: () => { if (on) cc.jump(); },
    lock: () => on && cc.lock(), switchTarget: () => on && cc.switchTarget(), potion: () => on && cc.potion(), swap: () => { if (on) swapWeapon(); }, exit: () => stop(), summon: () => spawnBoss(),
  };
  const hud = new CombatHUD(cc, api, project);
  const onKey = e => {
    if (!on || e.repeat || /input|textarea/i.test((e.target && e.target.tagName) || '')) return;
    const k = e.key;
    if (k >= '1' && k <= '6') api.use(+k - 1); else if (k === 'f' || k === 'F') api.use(0); else if (k === ' ') { e.preventDefault(); api.dodge(); }
    else if (k === 'q' || k === 'Q') api.lock(); else if (k === 'Tab') { e.preventDefault(); api.switchTarget(); } else if (k === 'r' || k === 'R') api.potion(); else if (k === 'e' || k === 'E') api.swap(); else if (k === 'j' || k === 'J') api.jump();
  };
  const onMd = e => { if (on && e.button === 2) cc.block(true); }, onMu = e => { if (on && e.button === 2) cc.block(false); }, onCtx = e => { if (on) e.preventDefault(); };

  /* ---- lightsaber: Owner only. Beth's saber_owner.glb (root 'saber'): drawn = under weapon_R (+ *_saber clips), sheathed = under weapon_back, blade/glow hidden ---- */
  const SABER_URL = 'proto3d/models-new/saber_owner.glb';
  let saberG = null, igniteT = -1, slashA = null, saberLoading = false;
  const bone = (h, n) => { let b = null; h.traverse(o => { if (!b && o.name === n) b = o; }); return b; };
  function sabParts() { const r = {}; if (saber) saber.traverse(o => { if (o.name === 'saber_blade') r.blade = o; else if (o.name === 'saber_glow') r.glow = o; else if (o.name === 'saber_tip') r.tip = o; }); return r; }
  function setBlade(v, k) { const p = sabParts(); for (const o of [p.blade, p.glow]) if (o) { o.visible = v; o.scale.y = k === undefined ? 1 : k; } }
  function clipSet(drawn) {   // swap the loco clips between plain and *_saber (they share leg timing, so no crossfade)
    const u = env.hero().userData; if (!u || !u.act) return; u.plain = u.plain || { idle: u.act.idle, walk: u.act.walk, run: u.act.run };
    u.sab = u.sab || {}; const names = { idle: 'idle_saber', walk: 'walk_saber', run: 'run_saber' };
    for (const k in names) {
      if (!u.sab[k] && u.all[names[k]]) u.sab[k] = u.all[names[k]];
      const want = drawn && u.sab[k] ? u.sab[k] : u.plain[k], old = u.act[k]; if (!want || want === old) continue;
      if (old) old.setEffectiveWeight(0); want.play(); want.setEffectiveWeight(0); if (old) want.time = old.time; u.act[k] = want;
    }
    if (!slashA && u.all.saber_slash) { slashA = u.all.saber_slash; slashA.setLoop(THREE.LoopOnce, 1); slashA.clampWhenFinished = true; }
  }
  function attach(drawn) {
    const h = env.hero(), hb = bone(h, drawn ? 'weapon_R' : 'weapon_back'); if (!saber || !hb) return false;
    hb.add(saber); saber.position.set(0, 0, 0); saber.quaternion.identity(); saber.scale.set(1, 1, 1); setBlade(drawn, drawn ? 0.001 : 0); if (drawn) igniteT = 0; return true;
  }
  async function equip() {
    if (!isOwner() || sheathed) return false; if (saber && saber.parent && saber.parent.name === 'weapon_R') return true;
    if (!saber) { if (saberLoading) return false; saberLoading = true; try { saberG = await env.loadGLTF(SABER_URL + '?v=1.1.8'); saber = saberG.scene; saber.traverse(o => { o.frustumCulled = false; }); } catch (e) { saberLoading = false; return false; } saberLoading = false; }
    if (!isOwner() || sheathed) return false; clipSet(true); return attach(true);
  }
  function unequip() { if (saber && saber.parent) saber.parent.remove(saber); saber = null; igniteT = -1; slashA = null; const u = env.hero().userData; if (u && u.plain) clipSet(false); }
  function swapWeapon() {
    if (!isOwner()) { hud.say('Only the Owner can wield the lightsaber', 1400); return; }
    sheathed = !sheathed; syncHero();
    if (sheathed) { clipSet(false); if (saber) attach(false); } else { clipSet(true); if (saber) attach(true); else equip(); }
    hud.say(sheathed ? 'Saber sheathed (unarmed)' : 'Lightsaber drawn', 900);
  }
  function syncHero() { const id = env.heroId(), own = isOwner(), want = own && !sheathed; if (cc.hero.id !== id || cc.hero.saber !== want) cc.setHero({ id, saber: want, name: own ? 'Owner' : (id.split(':').pop().replace(/_.*/, '') || 'Hero').replace(/^./, c => c.toUpperCase()), className: own ? 'Saber Knight' : 'Adventurer' }); }

  /* ---- action clips (any model): attack, attack2, hit, death. Aliases are matched case-insensitively; missing clip => procedural lunge/flinch/fall ---- */
  const ALIAS = { attack: ['attack', 'attack1', 'slash', 'swing', 'strike', 'melee'], attack2: ['attack2', 'heavy', 'slash2', 'strike2', 'attack_heavy'], hit: ['hit', 'hurt', 'hit_react', 'damage', 'flinch', 'hitreact'], death: ['death', 'die', 'dead', 'defeat', 'defeated', 'fall'] };
  function clipFor(u, kind) {
    if (!u || !u.all) return null; u.cmap = u.cmap || {}; if (kind in u.cmap) return u.cmap[kind]; let r = null; const keys = Object.keys(u.all);
    for (const n of ALIAS[kind]) { const k = keys.find(x => x.toLowerCase() === n); if (k) { r = u.all[k]; break; } }
    if (!r && kind === 'attack2') r = clipFor(u, 'attack');
    return (u.cmap[kind] = r);
  }
  /* Owner-only smooth attack playback: crossfade in/out (~0.12/0.15 s, smoothstep), chained swings overlap (previous clip fades out while the next fades in, no dip to idle),
     and the clip's own weight fades so it never snaps back to the loco pose. Damage timing is untouched (this only drives the animation mixer). */
  const sstep = x => { x = Math.max(0, Math.min(1, x)); return x * x * (3 - 2 * x); };
  const FADE_IN = 0.12, FADE_OUT = 0.15;
  function altAct(u, a) { u.alt = u.alt || new Map(); let b = u.alt.get(a); if (!b) { const c = a.getClip().clone(); c.name = a.getClip().name + '_b'; b = u.mixer.clipAction(c); u.alt.set(a, b); u.alt.set(b, a); } return b; }
  function playAct(root, a, kind, dur, hold) {
    const u = root.userData; if (!a || !u || !u.mixer) return false;
    const smooth = root === env.hero() && isOwner() && !hold && (kind === 'atk' || kind === 'attack' || kind === 'attack2');
    if (smooth && u.os && !u.os.hold && (u.os.kind === 'atk' || u.os.kind === 'attack' || u.os.kind === 'attack2')) {   // chained swing: overlap with the one still playing
      const prev = u.os; if (u.prev) u.prev.a.stop(); if (a === prev.a) a = altAct(u, a);
      u.prev = { a: prev.a, w0: prev.a.getEffectiveWeight(), t: 0 };
      a.reset(); a.setLoop(THREE.LoopOnce, 1); a.clampWhenFinished = false; const d = a.getClip().duration; a.timeScale = dur ? Math.min(3, d / dur) : 1; a.setEffectiveWeight(0.001); a.play();
      u.os = { a, t: 0, dur: d / a.timeScale, hold: false, kind, smooth: true, chain: true }; return true;
    }
    if (u.os && u.os.a !== a) u.os.a.stop(); if (u.prev) { u.prev.a.stop(); u.prev = null; }
    a.reset(); a.setLoop(THREE.LoopOnce, 1); a.clampWhenFinished = !!hold; const d = a.getClip().duration; a.timeScale = dur ? Math.min(3, d / dur) : 1; a.setEffectiveWeight(smooth ? 0.001 : 1); a.play();
    u.os = { a, t: 0, dur: d / a.timeScale, hold: !!hold, kind, smooth }; return true;
  }
  const oneShot = (root, kind, dur, hold) => { const u = root.userData; return !!u && playAct(root, clipFor(u, kind), kind, dur, hold); };
  function tickOS(root, dt) {
    const u = root.userData, o = u && u.os; if (!u) return; if (!o) { if (u.prev) { u.prev.a.stop(); u.prev = null; } u.ovr = 0; return; }
    o.t += dt;
    if (o.smooth) {
      const k = sstep(o.t / FADE_IN), out = sstep((o.dur - o.t) / FADE_OUT), w = Math.min(k, out);
      o.a.setEffectiveWeight(Math.max(0.001, w));
      if (u.prev) { u.prev.t += dt; const pk = sstep(1 - u.prev.t / FADE_IN); u.prev.a.setEffectiveWeight(Math.max(0.001, pk * u.prev.w0)); if (u.prev.t >= FADE_IN) { u.prev.a.stop(); u.prev = null; } }
      u.ovr = o.chain || u.prev ? Math.max(w, u.prev ? 1 - 0 : w) : w;   // while overlapping, the loco layer stays fully behind the two attack clips
      if (o.chain && !u.prev) u.ovr = w;
      if (o.t >= o.dur) { o.a.stop(); if (u.prev) { u.prev.a.stop(); u.prev = null; } u.os = null; u.ovr = 0; }
      return;
    }
    u.ovr = Math.max(0, Math.min(1, o.t / 0.08, o.hold ? 1 : (o.dur - o.t) / 0.15));
    if (o.t >= o.dur && !o.hold) { o.a.stop(); u.os = null; u.ovr = 0; }
  }
  const clearOS = root => { const u = root.userData; if (u && u.os) { u.os.a.stop(); u.os = null; } if (u && u.prev) { u.prev.a.stop(); u.prev = null; } if (u) u.ovr = 0; };
  /* ---- fx ---- */
  const ring = new THREE.Mesh(new THREE.RingGeometry(0.9, 1, 40), new THREE.MeshBasicMaterial({ color: 0x66e6ff, transparent: true, opacity: 0.7, side: THREE.DoubleSide, depthWrite: false, blending: THREE.AdditiveBlending }));
  ring.rotation.x = -Math.PI / 2; ring.visible = false; scene.add(ring);
  const orb = new THREE.Mesh(new THREE.SphereGeometry(0.25, 10, 8), new THREE.MeshBasicMaterial({ color: 0x9ff })); orb.visible = false; scene.add(orb);
  const aura = new THREE.Mesh(new THREE.SphereGeometry(1, 16, 12), new THREE.MeshBasicMaterial({ color: 0x66ccff, transparent: true, opacity: 0.22, depthWrite: false, blending: THREE.AdditiveBlending })); aura.visible = false; scene.add(aura);
  let fxT = -1, fxMax = 1, orbT = -1, orbFrom = null, orbTo = null;

  /* ---- controller events -> world ---- */
  cc.on('action', ev => {
    A.swing = { t: 0, T: ev.T, big: ev.a.id === 'heavy' ? 1.5 : 1, kind: ev.a.kind };
    { const h = env.hero(), u = h.userData, drawn = slashA && saber && saber.parent && saber.parent.name === 'weapon_R';
      let ok = false; if (ev.a.kind !== 'shield') ok = drawn ? playAct(h, slashA, 'atk', Math.max(0.5, ev.T), false) : oneShot(h, ev.a.id === 'heavy' ? 'attack2' : 'attack', Math.max(0.5, ev.T), false);
      A.clipAtk = ok; }
    if (ev.aim && (ev.a.kind !== 'storm' && ev.a.kind !== 'aoe')) state.yaw = Math.atan2(ev.aim.x - state.heroX, ev.aim.z - state.heroZ);
    if (ev.a.kind === 'aoe' || ev.a.kind === 'storm') { fxT = 0; fxMax = ev.a.range * HS; ring.material.color.setHex(ev.a.kind === 'storm' ? 0xffd34a : 0x66e6ff); }
    if (ev.a.kind === 'storm') A.spin = 0.0001;
  }).on('dash', d => { A.dash = { dx: d.dx, dz: d.dz, left: d.dist, spd: d.dist / d.T }; })
    .on('jump', j => { A.jump = 0; }).on('throw', t => { orbT = 0; orbFrom = { x: state.heroX, z: state.heroZ }; orbTo = t.e; })
    .on('block', () => {}).on('swap', () => {})
    .on('playerDown', () => { if (!oneShot(env.hero(), 'death', 0, true)) env.hero().rotation.x = -1.3; })
    .on('respawn', () => { clearOS(env.hero()); { const rp = env.respawnPos ? env.respawnPos() : { x: 0, z: 60 }; state.heroX = rp.x; state.heroZ = rp.z; } state.target = null; env.hero().rotation.x = 0; });
  cc.on('damage', d => { if (d.toPlayer) { const h = env.hero(), u = h.userData; if (!(u.os && u.os.kind !== 'hit')) oneShot(h, 'hit', 0.45, false); } else if (d.e.view) { d.e.flinch = 0.18; if (d.e.state !== 'telegraph' && d.e.state !== 'stagger') oneShot(d.e.view, 'hit', 0.4, false); } });
  cc.on('defeat', e => { if (e.def.boss) { bossOn = false; hud.say('ASHEN TITAN DEFEATED', 2600); } if (cc.kills % 6 === 0) { wave++; } });
  cc.on('enemyAttack', a => { if (a.result === 'dodged' && a.dmg === 0 && !cc.god) hud.floatAt(cc.p.x, 2.8 * HS, cc.p.z, 'DODGE', 'heal'); else if (a.result === 'parried') hud.floatAt(cc.p.x, 2.8 * HS, cc.p.z, 'PARRY', 'crit'); else if (a.result === 'blocked') hud.floatAt(cc.p.x, 2.8 * HS, cc.p.z, 'BLOCK', ''); });

  /* ---- enemies ---- */
  async function spawn(key, atPlayerDist, extra) {
    const def = ENEMIES[key], w = await env.makeModel(def.model); if (!w || !on) return null;
    let x = state.heroX + 12, z = state.heroZ;
    for (let k = 0; k < 20; k++) { const a = Math.random() * 6.283, r = (atPlayerDist || (14 + Math.random() * 14)) * HS / 1.5, px = state.heroX + Math.cos(a) * r, pz = state.heroZ + Math.sin(a) * r; if (env.free(px, pz)) { x = px; z = pz; break; } }
    w.position.set(x, 0, z); let top;
    if (def.boss || def.scale > 1) { top = (w.userData.heightW || 1.8 * HS * def.scale) + 0.5; }   // the GLB is already 6x the hero (11.4 m vs 1.9 m): no extra scaling in game
    else { w.updateMatrixWorld(true); top = Math.max(1.5, new THREE.Box3().setFromObject(w).max.y) + 0.3; }
    scene.add(w);
    const ems = []; w.traverse(o => { if (o.isMesh && o.material && o.material.emissive) { ems.push(o); o.userData.em = o.material.emissive.getHex(); } });
    const tele = new THREE.Mesh(ring.geometry, new THREE.MeshBasicMaterial({ color: 0xff2a2a, transparent: true, opacity: 0.45, side: THREE.DoubleSide, depthWrite: false })); tele.rotation.x = -Math.PI / 2; tele.visible = false; scene.add(tele);
    const e = cc.addEnemy(key, x, z, Object.assign({ view: w, top, ems, tele, flashOn: false, px: x, pz: z }, extra));
    if (def.boss) { bossOn = true; hud.say('ASHEN TITAN APPEARS', 2200); cc.tgt.target = e; cc.tgt.locked = false; cc.lastTarget = e; }
    return e;
  }
  const spawnBoss = () => { if (on && !bossOn) spawn('titan', 26); };
  cc.on('remove', e => { if (e.view) { scene.remove(e.view); scene.remove(e.tele); e.tele.material.dispose(); } });
  const yawLerp = (cur, to, k) => cur + (((to - cur + Math.PI * 3) % (Math.PI * 2)) - Math.PI) * k;

  /* ---- per frame ---- */
  function update(dt) {
    if (!on) return;
    dt = Math.min(dt, 0.1); syncHero();
    { const dx = state.heroX - A.lx, dz = state.heroZ - A.lz; A.lx = state.heroX; A.lz = state.heroZ; const l = Math.hypot(dx, dz); if (l > 0.005 && !A.dash) { A.vx = dx / l; A.vz = dz / l; } else if (l <= 0.005) { A.vx = 0; A.vz = 0; } }
    cc.setPlayer(state.heroX, state.heroZ, state.yaw);
    const h = env.hero();
    // lock-on: face the target
    if (cc.tgt.locked && cc.tgt.target && cc.dead <= 0) state.yaw = yawLerp(state.yaw, Math.atan2(cc.tgt.target.x - state.heroX, cc.tgt.target.z - state.heroZ), Math.min(1, dt * 9));
    cc.update(dt);
    // spawner (bad guys): small waves of regular enemies
    spawnT -= dt; const reg = cc.enemies.filter(e => !e.def.boss && e.state !== 'defeated').length;
    if (auto) {   // the Wilds: scattered, passive mobs (they stand off until you come within 3 m or hit them first); far ones are recycled
      if (spawnT <= 0 && reg < AUTO_MAX && cc.dead <= 0) { spawnT = 1.6; const r = Math.random(), key = r < 0.36 ? 'wolf' : r < 0.66 ? 'raider' : r < 0.86 ? 'wraith' : r < 0.95 ? 'skeleton' : 'frosttroll'; spawn(key, 12 + Math.random() * 38, { aggroR: AUTO_AGGRO }); }
      for (const e of cc.enemies) if (e.state === 'idle' && Math.hypot(e.x - state.heroX, e.z - state.heroZ) > 95) cc.removeEnemy(e);
    } else if (spawnT <= 0 && reg < Math.min(MAX_ALIVE, 2 + wave) && cc.dead <= 0) { spawnT = 3.5; spawn(WAVE_TABLE[Math.min(WAVE_TABLE.length - 1, Math.floor(Math.random() * Math.min(WAVE_TABLE.length, 1 + wave)))]); }
    // dash / jump
    if (A.dash) { const d = A.dash, s = Math.min(d.left, d.spd * dt), p = { x: state.heroX + d.dx * s, z: state.heroZ + d.dz * s }; env.resolve(p); state.heroX = p.x; state.heroZ = p.z; d.left -= s; if (d.left <= 0.01) A.dash = null; }
    if (A.jump >= 0) { A.jump += dt; const u = A.jump / cc.P.jump.dur; if (u >= 1) A.jump = -1; else h.position.y += cc.P.jump.height * HS * 4 * u * (1 - u); }
    // one-shot clips (saber_slash / attack / hit / death) blend over the loco clips; without a clip the arm overlay / procedural pose is used
    { const u = h.userData; tickOS(h, dt); const clip = u.os && (u.os.kind === 'atk' || u.os.kind === 'attack' || u.os.kind === 'attack2');
      if (A.swing && !clip) { const S = A.swing; S.t += dt; const p = Math.min(1, S.t / S.T), arc = Math.sin(p * Math.PI) * S.big, ua = bone(h, 'upperArm_R'), fa = bone(h, 'foreArm_R'), q = new THREE.Quaternion(), eu = new THREE.Euler();
        if (ua) { q.setFromEuler(eu.set(-2.4 * arc, 0, -0.3 * Math.sin(p * Math.PI * 2))); ua.quaternion.multiply(q); } if (fa) { q.setFromEuler(eu.set(-0.5 * arc, 0, 0)); fa.quaternion.multiply(q); } if (p >= 1) A.swing = null; }
      else if (A.swing) { A.swing.t += dt; if (A.swing.t >= A.swing.T) A.swing = null; }
      if (A.swing && A.swing.kind === 'storm') h.rotation.y += Math.min(1, A.swing.t / A.swing.T) * Math.PI * 4;
      if (igniteT >= 0) { igniteT += dt; const k = Math.min(1, igniteT / 0.25); setBlade(true, Math.max(0.001, k)); if (k >= 1) igniteT = -1; } }
    if (fxT >= 0) { fxT += dt; const u = fxT / 0.45; if (u >= 1) { fxT = -1; ring.visible = false; } else { ring.visible = true; ring.position.set(state.heroX, 0.15, state.heroZ); ring.scale.setScalar(Math.max(0.1, fxMax * u)); ring.material.opacity = 0.7 * (1 - u); } }
    if (orbT >= 0) { orbT += dt; const u = orbT / 0.25; if (u >= 1 || !orbTo) { orbT = -1; orb.visible = false; } else { orb.visible = true; orb.position.set(orbFrom.x + (orbTo.x - orbFrom.x) * u, 1.6 * HS * 0.6, orbFrom.z + (orbTo.z - orbFrom.z) * u); } }
    const au = cc.blocking || cc.shield > 0; aura.visible = au; if (au) { aura.position.set(state.heroX, 0.9 * HS, state.heroZ); aura.scale.setScalar(1.1 * HS); aura.material.color.setHex(cc.shield > 0 ? 0xffd34a : 0x66ccff); }
    // enemy visuals
    for (const e of cc.enemies.slice()) {
      const r = e.view; if (!r) continue; const u = r.userData, bs = e.def.boss ? 2.2 : 1;
      if (e.state === 'defeated') { if (!e.dying) { e.dying = true; e.deathClip = oneShot(r, 'death', 0, true); } const uu = r.userData; if (e.deathClip) { tickOS(r, dt); if (uu.glb && uu.act) { uu.mixer.update(dt); if (uu.sb) uu.sb.update(dt); } } else r.rotation.x = -Math.min(1.4, e.deadT * 4); r.position.y = -Math.max(0, e.deadT - 1.2) * 1.2 * bs; e.tele.visible = false; if (e.deadT > (e.deathClip ? 4 : 2.4)) cc.removeEnemy(e); continue; }
      const mv = Math.hypot(e.x - e.px, e.z - e.pz) / Math.max(dt, 1e-4); e.px = e.x; e.pz = e.z; r.position.x = e.x; r.position.z = e.z;
      r.rotation.y = yawLerp(r.rotation.y, e.yaw, Math.min(1, dt * 10));
      if (e.state !== e.ls) { if (e.state === 'telegraph') { e.alt = !e.alt; oneShot(r, e.def.boss && e.alt ? 'attack2' : 'attack', e.def.tele + 0.3, false); } else if (e.state === 'stagger') oneShot(r, 'hit', 0.5, false); e.ls = e.state; }
      if (e.flinch > 0) e.flinch -= dt; tickOS(r, dt);
      let lean = 0; if (e.state === 'telegraph') lean = -0.35 * Math.min(1, e.tStateT / e.def.tele); else if (e.state === 'attack') lean = 0.45; else if (e.state === 'stagger') lean = -0.5; else if (e.flinch > 0) lean = -0.25 * (e.flinch / 0.18);
      r.rotation.x += (lean - r.rotation.x) * Math.min(1, dt * 14);
      if (e.state === 'telegraph') { const reach = (e.def.reach * HS + e.def.r) * 1.1, f = Math.min(1, e.tStateT / e.def.tele); e.tele.visible = true; e.tele.position.set(e.x, 0.12, e.z); e.tele.scale.setScalar(reach); e.tele.material.opacity = 0.2 + 0.45 * f; } else e.tele.visible = false;
      if (u.glb && u.act) { env.loco(u, e.state === 'chase' ? mv : 0); u.mixer.update(dt); if (u.sb) u.sb.update(dt); }
      const f = e.flash > 0 || e.state === 'telegraph'; if (f !== e.flashOn) { e.flashOn = f; const hx = e.flash > 0 ? 0xff2020 : 0xaa5500; for (const o of e.ems) o.material.emissive.setHex(f ? hx : o.userData.em); }
    }
    hud.update(dt, cc.enemies);
    if (!saber && isOwner() && !sheathed && cc.dead <= 0) equip(); if (saber && (!isOwner() || sheathed)) unequip();
  }
  let auto = false;
  function start(isAuto) {
    if (on) return; auto = isAuto === true; on = true; wave = 1; sheathed = false; bossOn = false; cc.kills = 0; cc.xp = 0; cc.gold = 0; cc.res.full(); cc.cd.reset(); cc.dead = 0; cc.potions = cc.P.potion.charges; hud.show(true);
    addEventListener('keydown', onKey); addEventListener('mousedown', onMd); addEventListener('mouseup', onMu); addEventListener('contextmenu', onCtx);
    if (auto) { syncHero(); equip(); hud.say('THE WILDS - monsters about', 1800); return; }
    env.selectOwner().then(() => { syncHero(); equip(); hud.say('FIGHT TEST', 1800); });
  }
  function stop() {
    if (!on) return; on = false; hud.show(false); cc.block(false); cc.clearEnemies(); clearOS(env.hero()); unequip(); ring.visible = orb.visible = aura.visible = false; A.dash = null; A.swing = null; A.jump = -1;
    removeEventListener('keydown', onKey); removeEventListener('mousedown', onMd); removeEventListener('mouseup', onMu); removeEventListener('contextmenu', onCtx); env.hero().rotation.x = 0;
  }
  return { start, stop, startAuto: () => start(true), get auto() { return auto; }, toggle() { on ? stop() : start(); }, update, attack: () => api.use(0), use: api.use, dodge: api.dodge, lock: api.lock, potion: api.potion, spawnBoss, spawn, cc, hud, setSaberModel(u) { saberUrl = u; if (saber) loadModel(u); },
    get on() { return on; }, get hp() { return cc.res.hp; }, get kills() { return cc.kills; }, get monsters() { return cc.enemies; }, get hasSaber() { return !!saber; }, hurt(n) { cc.res.hp = Math.max(0, cc.res.hp - n); if (cc.res.hp <= 0 && cc.dead <= 0) { cc.dead = cc.P.respawn; cc.emit('playerDown'); } } };
}
