/* Fight test adapter (Phase 1 combat layer host). Owner-gated sandbox. Rules live in ./combat/controller.js (no THREE/DOM), the HUD in ./combat/hud.js
   (presentation only). This file only turns controller events into world effects: models, saber, animation, dash/jump, telegraph rings, spawning.
   Reads for combat: player x/z/yaw only. */
import { CombatController } from './combat/controller.js';
import { CombatHUD } from './combat/hud.js';
import { loadLucian } from './combat/calc.js';
import { worldProfile } from './charscale.js';
import { LightningFX } from './combat/lightning.js';
import { Armory } from './combat/armory.js';
import { gripFor } from './combat/grips.js';
import { heroKey } from './combat/herokits.js';
import { createExperience } from './combat/experience.js';
import { CompanionCombat } from './combat/companions.js';
import { SABER, ENEMIES, WAVE_TABLE, ABILITIES, OWNER_CLUSTER, TUNING } from './combat/data.js';
import { Respawner } from './combat/respawn.js';
import { TITAN_CENTER, FROST_REALM, FROST_SUMMIT, CITY_HALF, BALTHRIX_ROUTE, balthrixPosition, onLava, isCitySafe } from './bossregions.js';
import { FROST_BROTHERS } from './frostreach.js';
import { terrainBodyPitch } from './terrain-follow.js';
import { bossHome, telegraphKey } from './combat/boss-arena.js';
import { HOB_CAMPS } from './hobcamps.js';
export const SABER_DAMAGE = SABER.max;     // 99,999 flat per hit
export const SABER_GLB = null;             // URL (or fight.setSaberModel(url)) for Beth's saber: hilt at origin, blade along +Y, ~1 m
const MAX_ALIVE = 5, AUTO_MAX = (typeof matchMedia==='function' && matchMedia('(pointer:coarse)').matches) ? 12 : 15, AUTO_AGGRO = 3; // Lively world with mobile cap; wild mobs remain passive
export function createFight(env) {
  const { THREE, scene, camera, state, HS } = env;
  let on = false, saber = null, saberUrl = SABER_GLB, wave = 1, sheathed = false, spawnT = 0, bossOn = false;
  const terrainY=(x,z)=>env.groundY?env.groundY(x,z):0;
  const bossDue=new Map();const bossPending=new Set();let regionClock=0,roamClock=0,frostSpawnT=0,spawnEpoch=0;
  const v3 = new THREE.Vector3(), sc = [0, 0];
  const project = (x, y, z, out) => { v3.set(x, y, z).project(camera); if (v3.z > 1 || Math.abs(v3.x) > 1.3 || Math.abs(v3.y) > 1.3) return false; out[0] = (v3.x * 0.5 + 0.5) * innerWidth; out[1] = (-v3.y * 0.5 + 0.5) * innerHeight; return true; };
  const armory = new Armory({ ownerOk: () => !!(window.__p3d && window.__p3d.owner && window.__p3d.cheats), wallet: null });   // engine-side validation of every Armory UI request
  const cc = new CombatController({ HS, move: (e, dx, dz) => { const p = { x: e.x + dx, z: e.z + dz }; (env.resolveMob || env.resolve)(p); e.x = p.x; e.z = p.z; } });
  loadLucian();
  /* owner gate: Owner skin + the passphrase/owner unlock (window.__p3d.owner + cheats object, set only by the gated owner boot). Never read from UI or demo events. */
  const ownerGate = () => !!(window.__p3d && window.__p3d.owner && window.__p3d.cheats);
  /* Saber holder rule: the owner ACCOUNT may put the Owner saber on whichever hero is active; no other account can ever hold it. */
  const canWield = () => ownerGate();
  const isOwner = () => /(^|:)owner/.test(env.heroId());
  const A = { vx: 0, vz: 0, lx: 0, lz: 0, dash: null, jump: -1, spin: 0, swing: null, fx: null };   // player-side animation state
  const api = {
    use: i => { if (on) cc.use(i); }, dodge: () => { if (on) cc.dodge(A.vx, A.vz); }, block: b => { if (on) cc.block(b); }, jump: () => { if (on) cc.jump(); },
    lock: () => on && cc.lock(), switchTarget: () => on && cc.switchTarget(), potion: () => on && cc.potion(), swap: () => { if (on) swapWeapon(); }, exit: () => stop(), summon: () => spawnBoss(),
  };
  const hud = new CombatHUD(cc, api, project);
  // Combat XP previously reset every fight. The new per-hero progression is
  // persistent and rewards only the controller's one-time defeat event.
  const progress = createExperience((()=>{try{return localStorage;}catch(_){return null;}})());
  cc.on('reward', reward=>{
    const currentId=cc.hero.id;
    if(!currentId)return;
    const earned=progress.award(currentId,reward.xp);
    cc.hero.level=earned.level;
    cc.experience=earned;
    cc.emit('experience',earned);
    if(earned.levels){cc.emit('hero',cc.hero);hud.say(earned.levels===1?'LEVEL UP!  LV '+earned.level:'LEVEL UP!  +'+earned.levels+' LEVELS',2300);}
  });
  const onKey = e => {
    if (!on || e.repeat || /input|textarea/i.test((e.target && e.target.tagName) || '')) return;
    const k = e.key;
    if (k >= '1' && k <= '4') api.use(hud.slotAbility(+k)); else if (k >= '5' && k <= '8' && k !== '7') api.use(+k - 3); else if (k === '7' || k === 't' || k === 'T') api.use('unholy'); else if (k === 'x' || k === 'X') api.use(1); else if (k === 'f' || k === 'F') api.use(0); else if (k === ' ') { e.preventDefault(); api.dodge(); }
    else if (k === 'q' || k === 'Q') api.lock(); else if (k === 'Tab') { e.preventDefault(); api.switchTarget(); } else if (k === 'r' || k === 'R') api.potion(); else if (k === 'e' || k === 'E') api.swap(); else if (k === 'j' || k === 'J') api.jump();
  };
  const onMd = e => { if (on && e.button === 2) cc.block(true); }, onMu = e => { if (on && e.button === 2) cc.block(false); }, onCtx = e => { if (on) e.preventDefault(); };
  // Touch dodge without an extra HUD button: double tap the movement joystick.
  // The player keeps normal tap/drag movement and existing PC key bindings.
  let lastJoystickTap = 0, lastJoystickPointer = null;
  document.getElementById('stick')?.addEventListener('pointerdown',e=>{
    if(!on||window.__vnHudEditor?.isEditing?.()||document.body.classList.contains('vn-settings-open'))return;
    if(e.pointerType==='mouse')return;
    const now=performance.now();
    if(now-lastJoystickTap<300&&lastJoystickPointer!==e.pointerId){
      api.dodge();lastJoystickTap=0;
    }else lastJoystickTap=now;
    lastJoystickPointer=e.pointerId;
  });


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
    const h = env.hero(), hb = bone(h, drawn ? 'weapon_R' : 'weapon_back') || (drawn ? bone(h,'RightHand') || bone(h,'hand_R') : bone(h,'Spine')); if (!saber || !hb) return false;
    hb.add(saber); saber.position.set(0, 0, 0); saber.quaternion.identity(); saber.scale.set(1, 1, 1); setBlade(drawn, drawn ? 0.001 : 0); if (drawn) igniteT = 0; return true;
  }
  /* Bamboo Stick: procedural low-poly staff (green segments + darker nodes), auto-scaled to the hero (HS) and parented to the right-hand bone. */
  let BAM = null;
  function bambooBuild() { const g = new THREE.Group(), seg = new THREE.MeshStandardMaterial({ color: 0x5fae3a, roughness: 0.8, flatShading: true }), nod = new THREE.MeshStandardMaterial({ color: 0x2f6b1c, roughness: 0.9, flatShading: true }); const L = 2.4 * (env.HS ? env.HS / 1.5 : 1), n = 5, sl = L / n;
    for (let i = 0; i < n; i++) { const m = new THREE.Mesh(new THREE.CylinderGeometry(0.055, 0.06, sl * 0.92, 6), seg); m.position.y = (i + 0.5) * sl - L * 0.25; g.add(m); const k = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.075, sl * 0.1, 6), nod); k.position.y = (i + 1) * sl - L * 0.25; g.add(k); }
    g.name = 'bamboo_stick'; g.traverse(o => { o.frustumCulled = false; }); return g; }
  function bambooSync() { const want = cc.bambooOn() && cc.dead <= 0; if (want) { if (!BAM) BAM = bambooBuild(); const hb = bone(env.hero(), 'weapon_R') || bone(env.hero(), 'RightHand') || bone(env.hero(), 'weapon_back'); if (hb && BAM.parent !== hb) { hb.add(BAM); BAM.position.set(0, 0, 0); BAM.quaternion.identity(); } } else if (BAM && BAM.parent) BAM.parent.remove(BAM); }
  function bambooDispose() { if (BAM) { if (BAM.parent) BAM.parent.remove(BAM); BAM.traverse(o => { if (o.geometry) o.geometry.dispose(); if (o.material) o.material.dispose(); }); BAM = null; } }
  /* Hero-kit weapons in hand (non-Owner heroes): the armory's equipped weapon item (signature by default, Beth's optional weapons when chosen) is loaded once
     and parented to hand_R with the per-hero grip offset (combat/grips.js; refined2 sockets only when enabled). Owner keeps the saber/bamboo path. */
  const WCACHE = new Map(); let HW = null, hwKey = '', hwLoading = '';
  function heroWeaponClear() { if (HW) { if (HW.parent) HW.parent.remove(HW); HW = null; } hwKey = ''; }
  function heroWeaponSync() {
    const h = env.hero(), it = !cc.hero.owner && cc.dead <= 0 && armory.item(armory.s.equipment.weapon), url = it && it.glb ? it.glb : '', key = url && (h.uuid + '|' + url);
    if (!key) { if (HW) heroWeaponClear(); return; } if (key === hwKey || hwLoading === key) return;
    heroWeaponClear(); const hb = bone(h, 'hand_R') || bone(h,'RightHand'); if (!hb) return; hwLoading = key;
    const done = (g) => { hwLoading = ''; if (!g || env.hero() !== h || cc.hero.owner) return; const o = g.clone(true), G = gripFor(armory.key); o.position.fromArray(G.pos); o.quaternion.fromArray(G.quat); h.updateMatrixWorld(true); const ws = new THREE.Vector3(); hb.getWorldScale(ws); o.scale.setScalar((0.947 * HS) / (ws.x || 1));   /* weapon GLBs are metres: world size = metres * 0.947*HS whatever the rig's own scale */ o.name = 'hero_weapon'; o.userData.grip = G; o.traverse(m => { m.frustumCulled = false; if (m.isMesh) m.castShadow = true; }); hb.add(o); HW = o; hwKey = key; };
    if (WCACHE.has(url)) return done(WCACHE.get(url));
    env.loadGLTF(url).then(g => { WCACHE.set(url, g.scene); done(g.scene); }).catch(() => { hwLoading = ''; hwKey = key; });
  }
  async function equip() {
    if (!canWield() || sheathed) return false; if (saber && saber.parent && saber.parent.name === 'weapon_R') return true;
    if (!saber) { if (saberLoading) return false; saberLoading = true; try { saberG = await env.loadGLTF(SABER_URL + '?v=1.1.8'); saber = saberG.scene; saber.traverse(o => { o.frustumCulled = false; }); } catch (e) { saberLoading = false; return false; } saberLoading = false; }
    if (!canWield() || sheathed) return false; clipSet(true); return attach(true);
  }
  function unequip() { if (saber && saber.parent) saber.parent.remove(saber); saber = null; igniteT = -1; slashA = null; const u = env.hero().userData; if (u && u.plain) clipSet(false); }
  function swapWeapon() {
    if (!canWield()) { hud.say('Only the Owner can wield the lightsaber', 1400); return; }
    sheathed = !sheathed; syncHero();
    if (sheathed) { clipSet(false); if (saber) attach(false); } else { clipSet(true); if (saber) attach(true); else equip(); }
    hud.say(sheathed ? 'Saber sheathed (unarmed)' : 'Lightsaber drawn', 900);
  }
  function syncHero() { const id = env.heroId(), own = isOwner(), want = canWield() && !sheathed; const changed=cc.hero.id!==id; if(changed || cc.hero.saber!==want){ const saved=progress.get(id); cc.setHero({ id, saber: want, level:saved.level, name: own ? 'Owner' : (id.split(':').pop().replace(/_.*/, '') || 'Hero').replace(/^./, c => c.toUpperCase()), className: own ? 'Saber Knight' : 'Adventurer' }); cc.experience=saved;cc.emit('experience',saved); } cc.setScale(worldProfile(id, HS)); if (armory.key !== (cc.hero.owner ? 'owner' : heroKey(id))) { armory.setHero(id, cc.hero.owner); cc.setGear(armory.bonuses()); } }
  armory.wallet = { get: () => cc.gold, spend: (n) => { if (cc.gold < n) return false; cc.gold -= n; return true; } }; armory.on(() => cc.setGear(armory.bonuses()));

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
  const FADE_IN = 0.12, FADE_OUT = 0.15;   // Owner values; other heroes scale with the clip length (fades(d))
  const fades = (d, own) => own ? [FADE_IN, FADE_OUT] : [Math.max(0.06, Math.min(0.14, d * 0.22)), Math.max(0.08, Math.min(0.18, d * 0.3))];
  function altAct(u, a) { u.alt = u.alt || new Map(); let b = u.alt.get(a); if (!b) { const c = a.getClip().clone(); c.name = a.getClip().name + '_b'; b = u.mixer.clipAction(c); u.alt.set(a, b); u.alt.set(b, a); } return b; }
  function playAct(root, a, kind, dur, hold) {
    const u = root.userData; if (!a || !u || !u.mixer) return false;
    const smooth = (root === env.hero() || u.cmp) && !hold && (kind === 'atk' || kind === 'attack' || kind === 'attack2');
    if (smooth && u.os && !u.os.hold && (u.os.kind === 'atk' || u.os.kind === 'attack' || u.os.kind === 'attack2')) {   // chained swing: overlap with the one still playing
      const prev = u.os; if (u.prev) u.prev.a.stop(); if (a === prev.a) a = altAct(u, a);
      u.prev = { a: prev.a, w0: prev.a.getEffectiveWeight(), t: 0 };
      a.reset(); a.setLoop(THREE.LoopOnce, 1); a.clampWhenFinished = false; const d = a.getClip().duration; a.timeScale = dur ? Math.min(3, d / dur) : 1; a.setEffectiveWeight(0.001); a.play();
      { const dd = d / a.timeScale, f = fades(dd, root === env.hero() && isOwner()); u.os = { a, t: 0, dur: dd, hold: false, kind, smooth: true, chain: true, fi: f[0], fo: f[1] }; } return true;
    }
    if (u.os && u.os.a !== a) u.os.a.stop(); if (u.prev) { u.prev.a.stop(); u.prev = null; }
    a.reset(); a.setLoop(THREE.LoopOnce, 1); a.clampWhenFinished = !!hold; const d = a.getClip().duration; a.timeScale = dur ? Math.min(3, d / dur) : 1; a.setEffectiveWeight(smooth ? 0.001 : 1); a.play();
    { const dd = d / a.timeScale, f = fades(dd, root === env.hero() && isOwner()); u.os = { a, t: 0, dur: dd, hold: !!hold, kind, smooth, fi: f[0], fo: f[1] }; } return true;
  }
  const oneShot = (root, kind, dur, hold) => { const u = root.userData; return !!u && playAct(root, clipFor(u, kind), kind, dur, hold); };
  function tickOS(root, dt) {
    const u = root.userData, o = u && u.os; if (!u) return; if (!o) { if (u.prev) { u.prev.a.stop(); u.prev = null; } u.ovr = 0; return; }
    o.t += dt;
    if (o.smooth) {
      const k = sstep(o.t / o.fi), out = sstep((o.dur - o.t) / o.fo), w = Math.min(k, out);
      o.a.setEffectiveWeight(Math.max(0.001, w));
      if (u.prev) { u.prev.t += dt; const pk = sstep(1 - u.prev.t / o.fi); u.prev.a.setEffectiveWeight(Math.max(0.001, pk * u.prev.w0)); if (u.prev.t >= o.fi) { u.prev.a.stop(); u.prev = null; } }
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
  /* ---- Unholy Destruction visuals: one lazily built set (rock, shadow disc, zone ring, 48-point burst), reused per cast, disposed on stop() ---- */
  let MET = null, shakeT = 0, shakeA = 0;
  function metBuild() {
    if (MET) return MET;
    const rock = new THREE.Mesh(new THREE.IcosahedronGeometry(1, 1), new THREE.MeshStandardMaterial({ color: 0x3a2a24, emissive: 0xff4a12, emissiveIntensity: 0.9, flatShading: true, roughness: 1 }));
    const shadow = new THREE.Mesh(new THREE.CircleGeometry(1, 28), new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0, depthWrite: false })); shadow.rotation.x = -Math.PI / 2;
    const zone = new THREE.Mesh(new THREE.RingGeometry(0.97, 1, 48), new THREE.MeshBasicMaterial({ color: 0xff3a1a, transparent: true, opacity: 0, side: THREE.DoubleSide, depthWrite: false })); zone.rotation.x = -Math.PI / 2;
    const N = 48, pos = new Float32Array(N * 3), vel = new Float32Array(N * 3), pg = new THREE.BufferGeometry(); pg.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    const burst = new THREE.Points(pg, new THREE.PointsMaterial({ color: 0xffa23a, size: 0.7, transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending })); burst.frustumCulled = false;
    for (const o of [rock, shadow, zone, burst]) { o.visible = false; scene.add(o); }
    return (MET = { rock, shadow, zone, burst, pos, vel, N, st: 'off', t: 0, x: 0, z: 0, r: 25, delay: 1.5 });
  }
  /* Unholy lightning storm: 14 pooled zig-zag line bolts (additive purple), struck at random spots in the zone. */
  let LT = null;
  function ltBuild() { if (LT) return LT; const bolts = []; for (let i = 0; i < 14; i++) { const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(10 * 3), 3)); const l = new THREE.Line(g, new THREE.LineBasicMaterial({ color: 0xb04bff, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false })); l.frustumCulled = false; l.visible = false; scene.add(l); bolts.push({ l, t: 9 }); } return (LT = { bolts, next: 0, acc: 0 }); }
  function ltStrikeOld(x, z) { const L = ltBuild(), b = L.bolts[L.next++ % L.bolts.length], a = b.l.geometry.attributes.position.array, top = 85; for (let i = 0; i < 10; i++) { const u = i / 9, j = (i === 0 || i === 9) ? 0 : 4 * (1 - u * 0.5); a[i * 3] = x + (Math.random() - 0.5) * j + (1 - u) * 6; a[i * 3 + 1] = top * (1 - u); a[i * 3 + 2] = z + (Math.random() - 0.5) * j; } b.l.geometry.attributes.position.needsUpdate = true; b.t = 0; b.l.visible = true; b.l.material.color.setHex(Math.random() < 0.35 ? 0xe9d6ff : 0xa23cff); }
  function ltStrike(x, z) { getFx().strike({ path: [{ x, z, y: terrainY(x,z) + 1.1 * HS, falloff: 1 }] }); }   // Lucky's LightningFX bolts (pooled)
  let ltAcc = 0;
  function ltUpdate(dt, active, m) { if (!(active && m)) return; ltAcc += dt; const gap = m.st === 'burst' ? 0.14 : 0.2; while (ltAcc > gap) { ltAcc -= gap; const a = Math.random() * 6.283, d = Math.sqrt(Math.random()) * m.r; ltStrike(m.x + Math.cos(a) * d, m.z + Math.sin(a) * d); } }
  function ltDispose() { if (!LT) return; for (const b of LT.bolts) { scene.remove(b.l); b.l.geometry.dispose(); b.l.material.dispose(); } LT = null; }
  const metHide = () => { if (MET) { MET.st = 'off'; for (const o of [MET.rock, MET.shadow, MET.zone, MET.burst]) o.visible = false; } };
  function metDispose() { ltDispose(); bambooDispose(); if (!MET) return; for (const o of [MET.rock, MET.shadow, MET.zone, MET.burst]) { scene.remove(o); o.geometry.dispose(); o.material.dispose(); } MET = null; }
  const ROCK_R = 11, FALL_H = 75;
  function metStart(ev) { const m = metBuild(); m.st = 'fall'; m.t = 0; m.x = ev.x; m.z = ev.z; m.r = ev.radius; m.delay = ev.delay; m.mode = ev.mode; const uh = ev.mode === 'all'; m.zone.material.color.setHex(uh ? 0x8a2be2 : 0xffe9a0); m.burst.material.color.setHex(uh ? 0xb04bff : 0xfff0b0); m.rock.material.emissive.setHex(uh ? 0x000000 : 0xffd27a); m.rock.visible = !uh; m.shadow.visible = m.zone.visible = true; m.rock.scale.setScalar(ROCK_R); shakeA = 0.25; shakeT = 0.25; }
  function metImpact() { const m = MET; if (!m) return; m.st = 'burst'; m.t = 0; m.rock.visible = false; m.shadow.visible = false; m.burst.visible = true; m.burst.position.set(m.x, terrainY(m.x,m.z)+1, m.z);
    for (let i = 0; i < m.N; i++) { const a = Math.random() * 6.283, sp = 20 + Math.random() * 40, up = 15 + Math.random() * 30; m.vel.set([Math.cos(a) * sp, up, Math.sin(a) * sp], i * 3); m.pos.set([0, 0, 0], i * 3); } m.burst.geometry.attributes.position.needsUpdate = true; shakeA = 1.6; shakeT = 0.7; }
  function metUpdate(dt) {
    const m = MET; if (!m || m.st === 'off') { ltUpdate(dt, false); return; } m.t += dt; ltUpdate(dt, m.mode === 'all', m);
    if (m.st === 'fall') {
      const u = Math.min(1, m.t / m.delay), e = u * u;
      m.rock.position.set(m.x, terrainY(m.x,m.z)+ROCK_R * 0.6 + (1 - e) * FALL_H, m.z); m.rock.rotation.x += dt * 1.2; m.rock.rotation.z += dt * 0.7; m.rock.material.emissiveIntensity = 0.6 + u;
      m.shadow.position.set(m.x, terrainY(m.x,m.z)+0.1, m.z); m.shadow.scale.setScalar(Math.max(0.5, ROCK_R * 1.15 * e)); m.shadow.material.opacity = 0.65 * u;
      m.zone.position.set(m.x, terrainY(m.x,m.z)+0.12, m.z); m.zone.scale.setScalar(m.r); m.zone.material.opacity = 0.25 + 0.35 * Math.abs(Math.sin(m.t * 9));
    } else if (m.st === 'burst') {
      const u = m.t / 0.9; if (u >= 1) { metHide(); return; }
      const p = m.pos, v = m.vel; for (let i = 0; i < m.N; i++) { const k = i * 3; v[k + 1] -= 60 * dt; p[k] += v[k] * dt; p[k + 1] = Math.max(0, p[k + 1] + v[k + 1] * dt); p[k + 2] += v[k + 2] * dt; }
      m.burst.geometry.attributes.position.needsUpdate = true; m.burst.material.opacity = 1 - u;
      m.zone.visible = true; m.zone.scale.setScalar(Math.max(0.1, m.r * Math.min(1, u * 2.2))); m.zone.material.opacity = 0.8 * (1 - u); m.zone.material.color.setHex(m.mode === 'all' ? 0xb04bff : 0xffe9a0);
    }
  }
  function shake(cam) { if (shakeT <= 0) return; const k = shakeA * Math.min(1, shakeT / 0.3); cam.position.x += (Math.random() - 0.5) * k; cam.position.y += (Math.random() - 0.5) * k; cam.position.z += (Math.random() - 0.5) * k; }
  let fxT = -1, fxMax = 1, orbT = -1, orbFrom = null, orbTo = null;

  /* ---- controller events -> world ---- */
  cc.on('meteorCast', metStart).on('meteorImpact', ev => { metImpact();  hud.say(ev.name ? ev.name.toUpperCase() : 'DESTRUCTION', 1400); }).on('blink', b => { state.heroX = b.x; state.heroZ = b.z; state.yaw = b.yaw; });
  /* companions/followers fight too (combat/companions.js): attack clip with the same smoothing, damage via the controller */
  const companions = new CompanionCombat({ cc, HS, onSwing: (r, e, ranged) => { const w = r.root; if (!w || !w.userData) return; w.userData.cmp = true; oneShot(w, 'attack', 0.55, false); } });
  const folCache = { n: -1, list: [] }, heroInfo = { x: 0, z: 0, level: 0, dead: false };
  function updateCompanions(dt) {
    const L = env.followers ? env.followers() : []; heroInfo.x = state.heroX; heroInfo.z = state.heroZ; heroInfo.level = state.level; heroInfo.dead = cc.dead > 0;
    if (on) companions.update(dt, L, heroInfo); for (let i = 0; i < L.length; i++) { const w = L[i].root; if (w && w.userData && w.userData.os) tickOS(w, dt); }
  }
  let lfx = null; const getFx = () => lfx || (lfx = new LightningFX({ THREE, scene, HS, groundY: terrainY, canvas: document.querySelector('canvas') }));
  cc.on('lightning', ev => { getFx().strike(ev); });
  /* summons + buffs visuals (cheap shared geometry, 1-2 meshes each, removed on end) */
  const SUMG = { thrall: new THREE.CapsuleGeometry(0.45, 1.3, 3, 8), turret: new THREE.CylinderGeometry(0.35, 0.6, 1.1, 8), totem: new THREE.CylinderGeometry(0.22, 0.3, 2.6, 6), ring: new THREE.RingGeometry(0.92, 1, 40) };
  const SUMM = { thrall: new THREE.MeshLambertMaterial({ color: 0x3b2f4d, emissive: 0x2a0f3a }), turret: new THREE.MeshLambertMaterial({ color: 0x8a6d3b }), totem: new THREE.MeshLambertMaterial({ color: 0x6fae9a, emissive: 0x0d3a2a }) };
  const sumMesh = new Map(), buffRing = new THREE.Mesh(SUMG.ring, new THREE.MeshBasicMaterial({ color: 0xffd36a, transparent: true, opacity: 0.55, depthWrite: false, side: THREE.DoubleSide })); buffRing.rotation.x = -Math.PI / 2; buffRing.visible = false; scene.add(buffRing);
  cc.on('summon', s => { const g = new THREE.Group(), m = new THREE.Mesh(SUMG[s.id], SUMM[s.id]); m.position.y = s.id === 'totem' ? 1.3 * HS / 1.5 : 0.9 * HS / 1.5; m.scale.setScalar(HS / 1.5); g.add(m); if (s.id === 'totem') { const r = new THREE.Mesh(SUMG.ring, new THREE.MeshBasicMaterial({ color: 0x9be8d0, transparent: true, opacity: 0.4, depthWrite: false, side: THREE.DoubleSide })); r.rotation.x = -Math.PI / 2; r.position.y = 0.06; r.scale.setScalar(s.radius * HS); g.add(r); } g.position.set(s.x, terrainY(s.x,s.z), s.z); scene.add(g); sumMesh.set(s.uid, g); hud.say(s.id.toUpperCase(), 900); })
    .on('summonEnd', ({ s }) => { const g = sumMesh.get(s.uid); if (g) { scene.remove(g); g.traverse(o => { if (o.material && o.material !== SUMM[s.id]) o.material.dispose(); }); sumMesh.delete(s.uid); } })
    .on('summonAttack', ({ s, e }) => { if (s.id === 'turret' && getFx) getFx().strike({ from: { x: s.x, z: s.z }, path: [{ x: e.x, z: e.z, y: terrainY(e.x,e.z) + 1.1 * HS, falloff: 0.6, flash: true }], count: 1 }); })
    .on('buff', b => { if (b.name) hud.say(b.name.toUpperCase(), 1100); });
  function sumSync() { for (const s of cc.summons) { const g = sumMesh.get(s.uid); if (g) { g.position.set(s.x, terrainY(s.x,s.z), s.z); if (s.yaw !== undefined) g.rotation.y = s.yaw; } } const on2 = cc.buffs.length > 0; buffRing.visible = on2; if (on2) { buffRing.position.set(state.heroX, terrainY(state.heroX,state.heroZ)+0.07, state.heroZ); buffRing.scale.setScalar(1.6 * HS * Math.max(1, cc.RM)); } }
  if (env.bystanders) cc.bystanders = env.bystanders;   // Owner-gated server-trust: controller only fires these from owner ultimates
  cc.on('bystanderKill', ev => { if (env.killCrowd) env.killCrowd(ev.b); });
  cc.on('action', ev => {
    A.swing = { t: 0, T: ev.T, big: ev.a.id === 'heavy' ? 1.5 : 1, kind: ev.a.kind };
    { const h = env.hero(), u = h.userData, drawn = slashA && saber && saber.parent && saber.parent.name === 'weapon_R';
      let ok = false; if (ev.a.kind !== 'shield') ok = drawn ? playAct(h, slashA, 'atk', Math.max(0.5, ev.T), false) : oneShot(h, ev.a.id === 'heavy' ? 'attack2' : 'attack', Math.max(0.5, ev.T), false);
      A.clipAtk = ok; }
    if (ev.aim && (ev.a.kind !== 'storm' && ev.a.kind !== 'aoe')) state.yaw = Math.atan2(ev.aim.x - state.heroX, ev.aim.z - state.heroZ);
    if (ev.a.kind === 'aoe' || ev.a.kind === 'storm' || ev.a.kind === 'line') { fxT = 0; fxMax = ev.a.range * HS * cc.RM; ring.material.color.setHex(ev.a.kit && cc.kit ? parseInt(cc.kit.color.slice(1), 16) : ev.a.kind === 'storm' ? 0xffd34a : ev.a.owner ? 0xb36bff : 0x66e6ff); }
    if (ev.a.kind === 'storm') A.spin = 0.0001;
  }).on('dash', d => { A.dash = { dx: d.dx, dz: d.dz, left: d.dist, spd: d.dist / d.T }; })
    .on('jump', j => { A.jump = 0; }).on('throw', t => { orbT = 0; orbFrom = { x: state.heroX, z: state.heroZ }; orbTo = t.e; })
    .on('block', () => {}).on('swap', () => {})
    .on('playerDown', () => { if (!oneShot(env.hero(), 'death', 0, true)) env.hero().rotation.x = -1.3; })
    .on('respawn', () => { clearOS(env.hero()); { const rp = env.respawnPos ? env.respawnPos() : { x: 0, z: 60 }; state.heroX = rp.x; state.heroZ = rp.z; } state.target = null; env.hero().rotation.x = 0; });
  cc.on('damage', d => { if (d.toPlayer) { const h = env.hero(), u = h.userData; if (!(u.os && u.os.kind !== 'hit')) oneShot(h, 'hit', 0.45, false); } else if (d.e.view) { d.e.flinch = 0.18; if (d.e.state !== 'telegraph' && d.e.state !== 'stagger') oneShot(d.e.view, 'hit', 0.4, false); } });
  cc.on('chilled', () => hud.floatAt(cc.p.x, 2.8 * HS, cc.p.z, 'CHILLED', ''));
  cc.on('defeat',e=>{
    if(e.def.boss){
      bossDue.set(e.key,regionClock+100);
      bossOn=cc.enemies.some(v=>v!==e&&v.def.boss&&v.state!=='defeated');
      hud.say(e.def.name.toUpperCase()+' DEFEATED',2600);
      if(e.key==='hydra')env.onHydraDefeat?.();
      if(e.key==='frosttroll_a'||e.key==='frosttroll_b'){
        const sibling=cc.enemies.find(v=>v.key===(e.key==='frosttroll_a'?'frosttroll_b':'frosttroll_a')&&v.state!=='defeated');
        if(sibling){sibling.phase=2;sibling.pat=null;sibling.atkCd=0;hud.say("THE SURVIVING BROTHER ENRAGES",2400);}
      }
    }
    if(cc.kills%6===0)wave++;
  });
  cc.on('enemyAttack', a => { if (a.result === 'dodged' && a.dmg === 0 && !cc.god) hud.floatAt(cc.p.x, 2.8 * HS, cc.p.z, 'DODGE', 'heal'); else if (a.result === 'parried') hud.floatAt(cc.p.x, 2.8 * HS, cc.p.z, 'PARRY', 'crit'); else if (a.result === 'blocked') hud.floatAt(cc.p.x, 2.8 * HS, cc.p.z, 'BLOCK', ''); });

  /* ---- enemies ---- */
  async function spawn(key, atPlayerDist, extra) {
    const generation=spawnEpoch,spawnZone=env.zone?.();
    const def = ENEMIES[key], w = await env.makeModel(def.model);
    // A GLB may finish loading after a portal transition, death, or fight stop.
    // Never allow it to spawn into a different zone's new combat session.
    if (!w || !on || generation!==spawnEpoch || spawnZone!==env.zone?.()) return null;
    let x = state.heroX + 12, z = state.heroZ;
    if (extra && extra.at) { x = extra.at[0]; z = extra.at[1]; } else for (let k = 0; k < 20; k++) { const a = Math.random() * 6.283, r = (atPlayerDist || (14 + Math.random() * 14)) * HS / 1.5 * Math.max(1, cc.RM * 0.7), px = state.heroX + Math.cos(a) * r, pz = state.heroZ + Math.sin(a) * r; if (env.free(px, pz)) { x = px; z = pz; break; } }
    w.position.set(x, terrainY(x,z), z); let top;
    if (def.boss || def.scale > 1) { top = (w.userData.heightW || 1.8 * HS * def.scale) + 0.5; }   // the GLB is already 6x the hero (11.4 m vs 1.9 m): no extra scaling in game
    else { w.updateMatrixWorld(true); top = Math.max(1.5, new THREE.Box3().setFromObject(w).max.y) + 0.3; }
    // Both Frost Brothers use the humanoid Frost Troll rig; B has an ice-blue
    // material variant rather than falling back to a serpent asset.
    if(def.trollTint)w.traverse(o=>{
      if(!o.isMesh || !o.material)return;
      const src=Array.isArray(o.material)?o.material:[o.material];
      const tinted=src.map(mat=>{const copy=mat.clone();if(copy.color)copy.color.multiply(new THREE.Color(0xa2cfff));return copy;});
      o.material=Array.isArray(o.material)?tinted:tinted[0];
    });
    scene.add(w);
    const ems = []; w.traverse(o => { if (o.isMesh && o.material && o.material.emissive) { ems.push(o); o.userData.em = o.material.emissive.getHex(); } });
    const tele = new THREE.Mesh(ring.geometry, new THREE.MeshBasicMaterial({ color: 0xff2a2a, transparent: true, opacity: 0.45, side: THREE.DoubleSide, depthWrite: false })); tele.rotation.x = -Math.PI / 2; tele.visible = false; scene.add(tele);
    const e = cc.addEnemy(key, x, z, Object.assign({ view: w, top:top+terrainY(x,z), heightAbove:top, ems, tele, flashOn: false, px: x, pz: z }, bossHome(key,x,z)||{}, extra));
    if(def.boss){bossOn=true;
      if(key==='hydra')env.onHydraSpawn?.();
      if(Math.hypot(x-state.heroX,z-state.heroZ)<65){
        hud.say(def.name.toUpperCase()+' APPEARS',1250);
        cc.tgt.target=e;cc.tgt.locked=false;cc.lastTarget=e;
      }
    }
    return e;
  }
  const spawnBoss = () => { if (on && !bossOn) spawn('titan', 26); };
  /* boss telegraph shapes: ONE pooled mesh per boss (plane for line, sector for cone), created lazily. */
  let GL_LINE = null; const GL_CONES=new Map();
  function bossTele(e,shape,pt) {
    // Cone half-angles differ by skill: caching only by 'cone' made later
    // warnings display an older hitbox. Cache geometry by exact attack angle.
    const key=telegraphKey(shape,pt);
    if(!e.tele2 || e.tele2s!==key){
      if(e.tele2){scene.remove(e.tele2);e.tele2.material.dispose();}
      let g;
      if(shape==='line')g=GL_LINE||(GL_LINE=new THREE.PlaneGeometry(1,1));
      else{
        g=GL_CONES.get(key);
        if(!g){
          const half=Math.acos(Math.max(-1,Math.min(1,pt.cos)));
          g=new THREE.CircleGeometry(1,32,Math.PI/2-half,2*half);
          GL_CONES.set(key,g);
        }
      }
      e.tele2=new THREE.Mesh(g,new THREE.MeshBasicMaterial({color:0xff2a2a,transparent:true,opacity:.4,side:THREE.DoubleSide,depthWrite:false}));
      e.tele2s=key;scene.add(e.tele2);
    }
    e.tele2.material.color.setHex(e.phase===2?0xff7a1a:0xff2a2a);
    return e.tele2;
  }
  cc.on('remove', e => { if (e.view) { scene.remove(e.view); scene.remove(e.tele); e.tele.material.dispose(); if (e.tele2) { scene.remove(e.tele2); e.tele2.material.dispose(); } } });
  cc.on('bossPhase', ev => { hud.say((ev.e?.def?.name || 'THE BOSS').toUpperCase()+' ENRAGES', 1800); shakeA = 1.2; shakeT = 0.6; });
  cc.on('bossRetreat', ev=>hud.say((ev.e?.def?.name || 'Boss')+' retreats',1300));
  const yawLerp = (cur, to, k) => cur + (((to - cur + Math.PI * 3) % (Math.PI * 2)) - Math.PI) * k;

  /* ---- per frame ---- */
  // Region boss spawning happens near the player. Do not keep enormous GLBs active across the entire map.
  async function spawnRegion(key,x,z,extra={}){
    if(bossPending.has(key)||cc.enemies.some(e=>e.key===key&&e.state!=='defeated')||(bossDue.get(key)||0)>regionClock)return null;
    bossPending.add(key);
    try{return await spawn(key,0,Object.assign({at:[x,z],aggroR:34},extra));}
    finally{bossPending.delete(key);}
  }
  // Locate the player's nearest point along Balthrix's continuous world circuit.
  // Spawn close enough to be encountered rather than waiting for a distant global timer.
  function nearestRoamTime(x,z){
    const p=BALTHRIX_ROUTE;let best=Infinity,elapsed=0,closest=0;
    for(let i=0;i<p.length;i++){
      const a=p[i],b=p[(i+1)%p.length],dx=b[0]-a[0],dz=b[1]-a[1],len=Math.hypot(dx,dz);
      const u=Math.max(0,Math.min(1,((x-a[0])*dx+(z-a[1])*dz)/(len*len||1)));
      const d=Math.hypot(x-a[0]-dx*u,z-a[1]-dz*u);
      if(d<best){best=d;closest=(elapsed+len*u)/14;}elapsed+=len;
    }
    return{distance:best,time:closest};
  }
  let roamBusy=false;
  function startRegionBosses(zone){
    if(zone==='frost')for(const brother of FROST_BROTHERS)spawnRegion(brother.key,brother.x,brother.z,{aggroR:80});
    if(zone==='hydra'&&env.hydraBossAt){const at=env.hydraBossAt();if(at)spawnRegion('hydra',at.x,at.z,{aggroR:115});}
  }
  function regionUpdate(dt){
    const zone=env.zone?env.zone():'town';regionClock+=dt;
    if(zone==='hydra'){
      // Five attack patterns belong to one stationary boss. Restart only when
      // its defeat cooldown expires, not for every frame of the fight.
      if(cc.dead<=0&&regionClock>=frostSpawnT&&env.hydraBossAt){
        frostSpawnT=regionClock+2.5;
        const at=env.hydraBossAt();
        if(at)spawnRegion('hydra',at.x,at.z,{aggroR:115});
      }
      return;
    }
    if(zone==='frost'){
      // Dying clears all enemies. Repopulate the brothers once the player
      // respawns, without needing to exit and re-enter the cave portal.
      if(cc.dead<=0&&regionClock>=frostSpawnT){
        frostSpawnT=regionClock+2.5;
        for(const brother of FROST_BROTHERS)spawnRegion(brother.key,brother.x,brother.z,{aggroR:80});
      }
      return;
    }
    if(zone!=='town')return;
    // Protected village: no spawns or lava damage inside city walls.
    const outside=!isCitySafe(state.heroX,state.heroZ,8);
    if(outside){
      if(Math.hypot(state.heroX-TITAN_CENTER.x,state.heroZ-TITAN_CENTER.z)<125)
        spawnRegion('titan40',TITAN_CENTER.x,TITAN_CENTER.z,{aggroR:75});
      if(onLava(state.heroX,state.heroZ)){
        lavaT+=dt;if(lavaT>.8&&cc.dead<=0){lavaT=0;const amt=Math.max(18,Math.floor(cc.res.max.hp*.013));
          if(!cc.god){cc.res.hp=Math.max(0,cc.res.hp-amt);hud.floatAt(state.heroX,terrainY(state.heroX,state.heroZ)+2,state.heroZ,'LAVA -'+amt,'pl');
            if(cc.res.hp<=0){cc.dead=cc.P.respawn;cc.emit('playerDown');}
          }
        }
      }else lavaT=0;
      // Only discovery uses a slow timer. Once the serpent is visible its
      // location is integrated EVERY frame; moving it every .22 seconds caused
      // visible snapping and made its skeleton look like a sliding player.
      roamClock+=dt;
      if(roamClock>.22){
        roamClock=0;
        const route=nearestRoamTime(state.heroX,state.heroZ);
        const hasRoamer=cc.enemies.some(e=>e.key==='vaelthryx'&&e.state!=='defeated');
        if(!hasRoamer&&route.distance<112&&!roamBusy){
          roamBusy=true;
          const phase=route.time+2-regionClock,where=balthrixPosition(regionClock+phase);
          Promise.resolve(spawnRegion('vaelthryx',where.x,where.z,{aggroR:48,roaming:true,routePhase:phase}))
            .finally(()=>{roamBusy=false;});
        }
      }
      const roamer=cc.enemies.find(e=>e.key==='vaelthryx'&&e.state!=='defeated'&&e.roaming);
      if(roamer){
        const dHero=Math.hypot(roamer.x-state.heroX,roamer.z-state.heroZ);
        if(dHero>52&&roamer.state==='idle'){
          const p=balthrixPosition(regionClock+(roamer.routePhase||0));
          const dx=p.x-roamer.x,dz=p.z-roamer.z,dist=Math.hypot(dx,dz);
          if(dist>.01){
            // Physical pursuit of the curve, not instant correction of the
            // mesh transform. Combat interrupts his patrol without teleporting.
            const move=Math.min(dist,14*Math.max(0,dt));
            roamer.x+=dx/dist*move;roamer.z+=dz/dist*move;
            const heading=Math.atan2(dx,dz);
            roamer.yaw=yawLerp(Number.isFinite(roamer.yaw)?roamer.yaw:heading,heading,Math.min(1,Math.max(0,dt)*3.5));
          }
        }
      }
    }
    for(const e of cc.enemies.slice())if(e.def.boss&&Math.hypot(e.x-state.heroX,e.z-state.heroZ)>210){
      cc.removeEnemy(e);bossDue.set(e.key,regionClock+4);
    }
  }
  /* Fixed encampments: groups of hobgoblins defend their tents, with a global cap and
     per-camp reinforcement delay. They recycle when out of range; no surprise spawns in town. */
  // Low, breathy camp grunts. Audio starts only after the browser has
  // unlocked sound via player interaction; never creates a node per frame.
  let gruntClock=0, gruntAudio=null;
  function hobGrunt(distance){
    const AudioContextType=window.AudioContext||window.webkitAudioContext;
    if(!AudioContextType||document.hidden)return;
    try{
      if(!gruntAudio)return; // Do not instantiate an AudioContext outside a gesture on mobile.
      if(gruntAudio.state!=='running')return; // respect mobile autoplay restrictions
      const now=gruntAudio.currentTime;
      const osc=gruntAudio.createOscillator(), gain=gruntAudio.createGain();
      const filter=gruntAudio.createBiquadFilter();
      osc.type='sawtooth';filter.type='lowpass';filter.frequency.value=340;
      const volume=Math.min(.07,.075*Math.max(0,1-distance/43));
      osc.frequency.setValueAtTime(105+Math.random()*22,now);
      osc.frequency.exponentialRampToValueAtTime(62+Math.random()*12,now+.24);
      gain.gain.setValueAtTime(.0001,now);
      gain.gain.exponentialRampToValueAtTime(Math.max(.0002,volume),now+.045);
      gain.gain.exponentialRampToValueAtTime(.0001,now+.32);
      osc.connect(filter);filter.connect(gain);gain.connect(gruntAudio.destination);
      osc.start(now);osc.stop(now+.34);
      osc.onended=()=>{osc.disconnect();filter.disconnect();gain.disconnect();};
    }catch(e){/* audio is optional; gameplay must continue */ }
  }
  // The title-menu Enter button is a genuine user gesture on Android.
  document.getElementById('vnEnter')?.addEventListener('click',()=>{
    const AudioContextType=window.AudioContext||window.webkitAudioContext;
    if(!AudioContextType)return;
    try{gruntAudio ||= new AudioContextType();gruntAudio.resume().catch(()=>{});}catch(e){}
  });
  let campTimer=0;
  const campPending=new Set(),campNext=new Map();
  function updateHobCamps(dt){
    if(!auto||(env.zone&&env.zone()!=='town')||isCitySafe(state.heroX,state.heroZ,8)||cc.dead>0)return;
    gruntClock-=dt;
    if(gruntClock<=0){
      let nearest=Infinity;
      for(const e of cc.enemies)if(e.campId&&e.state!=='defeated')
        nearest=Math.min(nearest,Math.hypot(e.x-state.heroX,e.z-state.heroZ));
      if(nearest<43){hobGrunt(nearest);gruntClock=2.4+Math.random()*2.8;}
      else gruntClock=1.5;
    }
    campTimer-=dt;if(campTimer>0)return;campTimer=1.6;
    const regular=cc.enemies.filter(e=>!e.def.boss&&e.state!=='defeated').length;
    if(regular>=AUTO_MAX+4)return;
    for(const site of HOB_CAMPS){
      const distance=Math.hypot(state.heroX-site.x,state.heroZ-site.z);
      if(distance>135)continue;
      if(distance<16||regionClock<(campNext.get(site.id)||0)||campPending.has(site.id))continue;
      const campAlive=cc.enemies.filter(e=>e.campId===site.id&&e.state!=='defeated');
      if(campAlive.length>=site.guards)continue;
      const n=campAlive.length,angle=(n*2.4+site.id.length*.3)%(Math.PI*2);
      let x=site.x+Math.cos(angle)*(7.5+n*.6),z=site.z+Math.sin(angle)*(7.5+n*.6);
      if(!env.free(x,z)) { x=site.x+Math.cos(angle+1.1)*10;z=site.z+Math.sin(angle+1.1)*10; }
      if(!env.free(x,z)||Math.hypot(x-state.heroX,z-state.heroZ)<12)continue;
      const key=(n===site.guards-1)?'hob_enforcer':'raider';
      campPending.add(site.id);campNext.set(site.id,regionClock+2.5);
      // Spawn model asynchronously, without saturating WebGL model loads.
      Promise.resolve(spawn(key,0,{at:[x,z],aggroR:19,biome:'forest',campId:site.id}))
        .then(e=>{if(!e)campNext.set(site.id,regionClock+5);},()=>{campNext.set(site.id,regionClock+5);})
        .finally(()=>campPending.delete(site.id));
      break; // one guard per tick across camps
    }
  }
  let lavaT=0;
  function update(dt) {
    if (!on) return;
    dt = Math.min(dt, 0.1); syncHero(); cc.god = !!(env.cheat && env.cheat.god) && cc.perkHero(); cc.res.unlimited = !!(env.cheat && env.cheat.unlimited) && cc.perkHero(); cc.noCooldown = !!(env.cheat && env.cheat.noCooldown); cc.ownerUnlocked = ownerGate();
    { const dx = state.heroX - A.lx, dz = state.heroZ - A.lz; A.lx = state.heroX; A.lz = state.heroZ; const l = Math.hypot(dx, dz); if (l > 0.005 && !A.dash) { A.vx = dx / l; A.vz = dz / l; } else if (l <= 0.005) { A.vx = 0; A.vz = 0; } }
    cc.setPlayer(state.heroX, state.heroZ, state.yaw);
    const h = env.hero();
    // lock-on: face the target
    if (cc.tgt.locked && cc.tgt.target && cc.dead <= 0) state.yaw = yawLerp(state.yaw, Math.atan2(cc.tgt.target.x - state.heroX, cc.tgt.target.z - state.heroZ), Math.min(1, dt * 9));
    cc.update(dt); if (lfx) lfx.update(dt); updateCompanions(dt); regionUpdate(dt); updateHobCamps(dt);
    // spawner (bad guys): small waves of regular enemies
    spawnT -= dt; const reg = cc.enemies.filter(e => !e.def.boss && e.state !== 'defeated').length;
    if (auto && (env.zone?.()==='wilds'||env.zone?.()==='town')) {   // Wilds + wilderness beyond the walls: scattered, passive mobs (they stand off until you come within 3 m or hit them first); far ones are recycled
      RH.hero.x = state.heroX; RH.hero.z = state.heroZ; if (cc.dead <= 0 && (env.zone?.()==='wilds'||!isCitySafe(state.heroX,state.heroZ,8))) RS.update(dt, RH);   // respawn: 20-40 s after a kill, out of sight, per-biome cap, Wilds only
      for (const e of cc.enemies) if (e.state === 'idle' && Math.hypot(e.x - state.heroX, e.z - state.heroZ) > (e.campId?130:95)) { cc.removeEnemy(e); if(!e.campId)RS.freeSlot(false); }
    } else if (!auto && spawnT <= 0 && reg < Math.min(MAX_ALIVE, 2 + wave) && cc.dead <= 0) { spawnT = 3.5; spawn(WAVE_TABLE[Math.min(WAVE_TABLE.length - 1, Math.floor(Math.random() * Math.min(WAVE_TABLE.length, 1 + wave)))]); }
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
    if (fxT >= 0) { fxT += dt; const u = fxT / 0.45; if (u >= 1) { fxT = -1; ring.visible = false; } else { ring.visible = true; ring.position.set(state.heroX, terrainY(state.heroX,state.heroZ)+0.15, state.heroZ); ring.scale.setScalar(Math.max(0.1, fxMax * u)); ring.material.opacity = 0.7 * (1 - u); } }
    if (orbT >= 0) { orbT += dt; const u = orbT / 0.25; if (u >= 1 || !orbTo) { orbT = -1; orb.visible = false; } else { orb.visible = true; orb.position.set(orbFrom.x + (orbTo.x - orbFrom.x) * u, terrainY(orbFrom.x + (orbTo.x - orbFrom.x) * u,orbFrom.z + (orbTo.z - orbFrom.z) * u)+1.6 * HS * 0.6, orbFrom.z + (orbTo.z - orbFrom.z) * u); } }
    const au = cc.blocking || cc.shield > 0; aura.visible = au; if (au) { aura.position.set(state.heroX, terrainY(state.heroX,state.heroZ)+0.9 * HS, state.heroZ); aura.scale.setScalar(1.1 * HS); aura.material.color.setHex(cc.shield > 0 ? 0xffd34a : 0x66ccff); }
    // enemy visuals
    for (const e of cc.enemies.slice()) {
      const r = e.view; if (!r) continue; const u = r.userData, bs = e.def.boss ? 2.2 : 1;
      if (e.state === 'defeated') { if (!e.dying) { e.dying = true; e.deathClip = oneShot(r, 'death', 0, true); } const uu = r.userData; if (e.deathClip) { tickOS(r, dt); if (uu.glb && uu.act) { uu.mixer.update(dt); if (uu.sb) uu.sb.update(dt); } } else r.rotation.x = -Math.min(1.4, e.deadT * 4); r.position.y = -Math.max(0, e.deadT - 1.2) * 1.2 * bs; e.tele.visible = false; if (e.deadT > (e.deathClip ? 4 : 2.4)) cc.removeEnemy(e); continue; }
      const mv = Math.hypot(e.x - e.px, e.z - e.pz) / Math.max(dt, 1e-4); e.px = e.x; e.pz = e.z; r.position.x = e.x; r.position.z = e.z;
      // Bosses use the shared terrain height. Smooth the roamer's vertical movement
      // so steep ridges do not produce a visible up/down snap every simulation tick.
      const ground=terrainY(e.x,e.z);
      if(e.key==='vaelthryx'&&e.roaming){
        const previous=Number.isFinite(r.position.y)?r.position.y:ground;
        const rise=ground-previous;
        const maxStep=Math.max(.25,dt*13);
        r.position.y=previous+Math.max(-maxStep,Math.min(maxStep,rise));
      }else r.position.y=ground;
      e.top=r.position.y+(e.heightAbove||2.5);
      // Imported bosses can start without a finite yaw. Keep the rendered
      // heading valid so the serpent never disappears into NaN transforms.
      const heading=Number.isFinite(e.yaw)?e.yaw:0;
      r.rotation.y = yawLerp(Number.isFinite(r.rotation.y)?r.rotation.y:heading, heading, Math.min(1,Math.max(0,dt)*(e.key==='vaelthryx'?3.5:10)));
      if (e.state !== e.ls) { if(e.key==='hydra'&&e.state==='telegraph'&&e.pat)hud.say(e.pat.name.toUpperCase(),950); if (e.state === 'telegraph') { e.alt = !e.alt; oneShot(r, e.def.boss && e.alt ? 'attack2' : 'attack', e.def.tele + 0.3, false); } else if (e.state === 'stagger') oneShot(r, 'hit', 0.5, false); e.ls = e.state; }
      if (e.flinch > 0) e.flinch -= dt; tickOS(r, dt);
      let lean = 0; if (e.state === 'telegraph') lean = -0.35 * Math.min(1, e.tStateT / e.def.tele); else if (e.state === 'attack') lean = 0.45; else if (e.state === 'stagger') lean = -0.5; else if (e.flinch > 0) lean = -0.25 * (e.flinch / 0.18);
      // Balthrix's ROOT gently matches hill inclination, while authored
      // spine/tail joints handle the actual serpent gait. Never lean the
      // body through the ground or override strike/stagger attack poses.
      if(e.key==='vaelthryx'&&e.roaming&&(e.state==='idle'||e.state==='chase')){
        const along=7,fx=Math.sin(heading)*along,fz=Math.cos(heading)*along;
        const behind=terrainY(e.x-fx,e.z-fz),ahead=terrainY(e.x+fx,e.z+fz);
        lean+=terrainBodyPitch(behind,ahead,2*along,.16);
      }
      // Giant Troll B's bulky neck should not fold inside its chest during telegraphs or strikes.
      if (e.key === 'frosttroll_b') lean = Math.max(-0.12, Math.min(0.16, lean));
      if (e.key === 'vaelthryx') lean = Math.max(-.10, Math.min(.10, lean));
      r.rotation.x += (lean - r.rotation.x) * Math.min(1, dt * 14);
      if (e.state === 'telegraph') { const pt = (e.def.boss || e.def.patterns) ? e.pat : null, f = Math.min(1, e.tStateT / (e.curTele || e.def.tele)), reach = ((pt ? pt.reach : e.def.reach) * HS + e.def.r) * 1.1;
        const shape = pt ? pt.shape : 'ring'; e.tele.visible = shape === 'ring'; if (shape === 'ring') { e.tele.position.set(e.x, terrainY(e.x,e.z)+0.12, e.z); e.tele.scale.setScalar(reach); e.tele.material.opacity = 0.2 + 0.45 * f; e.tele.material.color.setHex(e.phase === 2 ? 0xff7a1a : 0xff2a2a); }
        if (shape !== 'ring') { const t2 = bossTele(e, shape, pt); t2.visible = true; const L = pt.reach * HS + e.def.r; t2.position.set(e.x, terrainY(e.x,e.z)+0.13, e.z); t2.rotation.set(-Math.PI / 2, 0, e.yaw + Math.PI); t2.material.opacity = 0.18 + 0.45 * f; if (shape === 'line') { t2.scale.set(pt.width * HS, L * (0.35 + 0.65 * f), 1); t2.position.set(e.x + Math.sin(e.yaw) * t2.scale.y / 2, terrainY(e.x + Math.sin(e.yaw) * t2.scale.y / 2,e.z + Math.cos(e.yaw) * t2.scale.y / 2)+0.13, e.z + Math.cos(e.yaw) * t2.scale.y / 2); } else t2.scale.setScalar(L * (0.35 + 0.65 * f)); } else if (e.tele2) e.tele2.visible = false;
      } else { e.tele.visible = false; if (e.tele2) e.tele2.visible = false; }
      if (u.glb && u.act) { env.loco(u, e.state === 'chase' || e.state === 'return' || e.roaming && mv > .5 ? mv : 0, dt); u.mixer.update(dt); if (u.sb) u.sb.update(dt); }
      const f = e.flash > 0 || e.state === 'telegraph'; if (f !== e.flashOn) { e.flashOn = f; const hx = e.flash > 0 ? 0xff2020 : 0xaa5500; for (const o of e.ems) o.material.emissive.setHex(f ? hx : o.userData.em); }
    }
    if (shakeT > 0) shakeT = Math.max(0, shakeT - dt); metUpdate(dt);
    hud.update(dt, cc.enemies);
    bambooSync(); heroWeaponSync(); sumSync(); if (!saber && canWield() && !sheathed && cc.dead <= 0 && !cc.bambooOn()) equip(); if (saber && (!canWield() || sheathed)) unequip(); if (saber) saber.visible = !cc.bambooOn();
  }
  /* owner cheat hooks (cheats.js -> main.js) */
  const cheatHeal = () => { cc.res.full(); cc.potions = cc.P.potion.charges; if (cc.dead > 0) { cc.dead = 0; cc.act = null; env.hero().rotation.x = 0; } hud.say('Party healed', 1200); return true; };
  const cheatKill = () => { let n = 0; for (const e of cc.enemies.slice()) if (e.state !== 'defeated') { e.hp = 0; cc.defeat(e); n++; } if (n) hud.say(n + ' slain', 1200); return n > 0; };
  const cheatSpawn = (key) => {
    if (!ENEMIES[key]) return false;
    if (ENEMIES[key].boss) { if (bossOn) return false; spawn(key, key === 'vaelthryx' ? 60 : 26); return true; }
    for (const e of cc.enemies.slice()) if (e.state === 'defeated' && !e.def.boss) cc.removeEnemy(e);
    spawn(key, 10); return true;
  };
  let auto = false;
  const RS = new Respawner({ max: AUTO_MAX, maxDist: 60 * (env.wildsScale || 280 / 170) /* enlarged Wilds: biomes are WS x farther apart */ }), RH = { hero: { x: 0, z: 0 }, zone: () => env.zone ? env.zone() : 'wilds', inWilds: (x, z) => env.inWilds ? env.inWilds(x, z) : true,
    biome: (x, z) => env.biome ? env.biome(x, z) : 'meadow', free: (x, z) => env.free(x, z), visible: (x, z) => project(x, 1.2, z, sc),
    alive: b => { let n = 0; for (const e of cc.enemies) if (e.biome === b && e.state !== 'defeated') n++; return n; }, spawn: (key, x, z, b) => spawn(key, 0, { aggroR: AUTO_AGGRO, at: [x, z], biome: b }) };
  cc.on('defeat', e => { if(auto&&e.campId)campNext.set(e.campId,regionClock+20+Math.random()*10); else if (auto && !e.def.boss) RS.freeSlot(true); });
  function start(isAuto) {
    if (on) { if (isAuto === true) auto = true; return; } auto = isAuto === true; on = true; wave = 1; sheathed = false; bossOn = false; cc.kills = 0; cc.xp = 0; cc.gold = 0; cc.res.full(); cc.cd.reset(); cc.dead = 0; cc.potions = cc.P.potion.charges; hud.show(true);
    addEventListener('keydown', onKey); addEventListener('mousedown', onMd); addEventListener('mouseup', onMu); addEventListener('contextmenu', onCtx);
    if (auto) { syncHero(); equip(); const zone=env.zone?.(); hud.say(zone==='hydra'?'HYDRA MIRE — FIVE HEADS AWAIT':zone==='frost'?'FROST CAVE — THE BROTHERS AWAIT':zone==='town'?'OUTSKIRTS — DANGER AHEAD':'THE WILDS — MONSTERS ABOUT',1800); return; }
    // Normal combat is available to every playable hero. Do not silently
    // replace the chosen character with the Owner when fight mode is toggled.
    syncHero(); equip(); hud.say('COMBAT READY', 1800);
  }
  function stop() { heroWeaponClear(); for (const s of cc.summons.slice()) cc.removeSummon(s, 'stop'); cc.buffs.length = 0; sumSync();
    if (!on) return; on = false; spawnEpoch++; metHide(); metDispose(); cc.meteors.length = 0; hud.show(false); cc.block(false); cc.clearEnemies(); clearOS(env.hero()); unequip(); ring.visible = orb.visible = aura.visible = false; A.dash = null; A.swing = null; A.jump = -1;
    removeEventListener('keydown', onKey); removeEventListener('mousedown', onMd); removeEventListener('mouseup', onMu); removeEventListener('contextmenu', onCtx); env.hero().rotation.x = 0;
  }
  const moveMul = () => (on && cc.chill > 0 && !cc.hero.owner) ? Math.max(0.3, 1 - (cc.chillAmt || 0)) : 1; if (typeof window !== 'undefined') window.__fightMove = moveMul;
  return { moveMul, armory, startRegionBosses, get heroWeapon() { return HW; }, setBamboo(v) { if (!ownerGate()) { cc.bamboo = false; return false; } cc.bamboo = !!v; bambooSync(); return cc.bamboo; }, bambooOn: () => cc.bambooOn(), useUltimate2: () => cc.useUltimate2(), get lightning() { return lfx; }, companions, cheatHeal, cheatKill, cheatSpawn, shake, start, stop, startAuto: () => start(true), get auto() { return auto; }, toggle() { on ? stop() : start(); }, update, attack: () => api.use(0), use: api.use, dodge: api.dodge, lock: api.lock, potion: api.potion, spawnBoss, spawn, cc, hud, setSaberModel(u) { saberUrl = u; if (saber) loadModel(u); },
    get on() { return on; }, get hp() { return cc.res.hp; }, get kills() { return cc.kills; }, get monsters() { return cc.enemies; }, get respawner() { return RS; }, get hasSaber() { return !!saber; }, hurt(n) { cc.res.hp = Math.max(0, cc.res.hp - n); if (cc.res.hp <= 0 && cc.dead <= 0) { cc.dead = cc.P.respawn; cc.emit('playerDown'); } } };
}
