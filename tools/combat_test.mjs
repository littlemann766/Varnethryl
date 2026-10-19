import { CombatController } from '../www/proto3d/combat/controller.js';
import { loadLucian, usingLucian } from '../www/proto3d/combat/calc.js';
import { ABILITIES, TUNING } from '../www/proto3d/combat/data.js';
let ok = 0, bad = 0; const T = (n, c) => { if (c) { ok++; console.log('PASS', n); } else { bad++; console.log('FAIL', n); } };
const lu = await loadLucian(); console.log('lucian combat.js loaded:', lu);
let seed = 12345; const rnd = () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
const mk = (saber = true) => { const c = new CombatController({ HS: 1.5, rng: rnd }); c.setHero({ id: 'o:owner', saber, name: 'Owner', className: 'Saber Knight' }); c.setPlayer(0, 0, 0); return c; };
const run = (c, s) => { for (let i = 0; i < s * 60; i++) c.update(1 / 60); };
let c = mk(); let w = c.addEnemy('wolf', 0, 3);
c.use(0); run(c, 0.5); T('saber hit flat 99999', w.state === 'defeated' && c.xp === w.def.xp);
let dmgs = []; c = mk(); c.on('damage', d => !d.toPlayer && dmgs.push(d)); let t = c.addEnemy('titan', 0, 8); c.setPlayer(0, 0, 0);
for (let i = 0; i < 40; i++) { c.cd.reset(); c.use(0); run(c, 0.45); if (t.state === 'defeated') break; }
T('every saber hit exactly 99999', dmgs.filter(d => true).every(d => d.dmg === 99999));
T('titan has 5,000,000 hp / 2100 atk / 2300ms', t.max === 5000000 && t.def.atk === 2100 && t.def.atkMs === 2300 && t.def.scale === 6);
c.clearEnemies(); c = mk(); let rew = 0; c.on('reward', () => rew++); w = c.addEnemy('wolf', 0, 3); c.hitEnemy(w, 1); c.hitEnemy(w, 1); c.defeat(w); T('rewards once per defeat', rew === 1 && c.kills === 1);
c = mk(); c.use(0); T('cooldown blocks reuse', !c.use(0) || false); run(c, 0.2); T('busy during action', c.busy());
c = mk(false); T('non-owner cannot use saber slots', !c.use(2) && c.use(0));
c = mk(); c.res.mp = 0; T('no mana -> denied', !c.use(2));
c = mk(); w = c.addEnemy('skeleton', 0, 3.5); const seen = new Set(); let hits = 0; c.on('enemyAttack', a => hits += a.dmg > 0 ? 1 : 0); for (let i = 0; i < 60 * 5; i++) { c.update(1 / 60); seen.add(w.state); }
T('state machine chase/telegraph/attack/recover', ['chase', 'telegraph', 'attack', 'recover'].every(s => seen.has(s)));
T('player damaged by enemy', c.res.hp < c.res.max.hp && hits >= 1);
c = mk(); w = c.addEnemy('titan', 0, 6); let res = []; c.on('enemyAttack', a => res.push(a.result)); const okd = c.dodge(1, 0); T('dodge consumes stamina + gives i-frames', okd && c.res.sp === c.res.max.sp - 20 && c.iframes > 0);
c = mk(); w = c.addEnemy('titan', 0, 6); c.iframes = 99; res = []; c.on('enemyAttack', a => res.push(a.result)); run(c, 6); T('i-frames negate strikes', res.length > 0 && res.every(r => r === 'dodged' || r === 'missed') && c.res.hp === c.res.max.hp);
c = mk(); w = c.addEnemy('titan', 0, 6); res = []; c.on('enemyAttack', a => res.push(a.result)); c.block(true); run(c, 4); T('block reduces / parries', res.some(r => r === 'parried' || r === 'blocked'));
c = mk(); c.res.hp = 1000; T('potion heals', c.potion() && c.res.hp > 1000 && c.potions === 2 && !c.potion());
c = mk(); c.setHero({ id: 'n:darius', saber: false }); w = c.addEnemy('titan', 0, 4); w.def = Object.assign({}, w.def, { atk: 99999 }); let down = 0, resp = 0; c.on('playerDown', () => down++); c.on('respawn', () => resp++); run(c, 20); T('death then respawn', down >= 1 && resp >= 1 && c.res.hp === c.res.max.hp);
c = mk(); const a = c.addEnemy('wolf', 5, 0), b = c.addEnemy('wolf', -5, 0); c.lock(); const f = c.tgt.target; c.switchTarget(); T('lock + switch target', f && c.tgt.target && c.tgt.target !== f && c.tgt.locked);
c = mk(); w = c.addEnemy('titan', 0, 4); c.cd.reset(); c.use(5); run(c, 1.3); T('Blade Storm hits 3x99999 on the 5M titan', w.max - w.hp === 3 * 99999);
c = mk(); w = c.addEnemy('titan', 0, 4); let dd = []; c.on('enemyAttack', a => a.dmg > 0 && dd.push(a.dmg)); run(c, 8); T('owner has 999999 max hp, takes normal damage', c.res.max.hp === 999999 && dd.length >= 1 && dd[0] > 1000 && c.res.hp < 999999);
c = mk(); c.setHero({ id: 'n:darius', saber: false }); w = c.addEnemy('titan', 0, 4); dd = []; c.on('enemyAttack', a => a.dmg > 0 && dd.push(a.dmg)); run(c, 4); T('non-owner takes full damage', dd.length >= 1 && dd[0] > 1000);
for (const [k, lo, hi] of [['wolf', 8, 15], ['raider', 11, 22]]) { c = mk(false); c.setHero({ id: 'n:darius', saber: false }); c.setPlayer(0, 0, 0); w = c.addEnemy(k, 0, 3); w.def = Object.assign({}, w.def, { atk: 0 }); let tt = 0, st = 0; c.on('enemyAttack', () => {}); const seenS = new Set(); while (w.state !== 'defeated' && tt < 120) { c.use(0); c.update(1 / 60); tt += 1 / 60; seenS.add(w.state); w.x = 0; w.z = 3; } T('normal char kills ' + k + ' in ' + lo + '-' + hi + 's (' + tt.toFixed(1) + 's)', tt >= lo && tt <= hi); if (k === 'wolf') T('normal hits stagger the enemy', seenS.has('stagger')); }
c = mk(false); c.setHero({ id: 'n:darius', saber: false }); c.setPlayer(0, 0, 0); w = c.addEnemy('skeleton', 0, 3); w.def = Object.assign({}, w.def, { atk: 0 }); let t3 = 0; while (w.state !== 'defeated' && t3 < 300) { c.use(0); c.update(1 / 60); t3 += 1 / 60; w.x = 0; w.z = 3; } T('normal char: elite takes longer (' + t3.toFixed(0) + 's)', t3 > 30);
// unlimited MP/SP (owner flag set by fight.js from the gated cheat flag)
c = mk(); c.res.unlimited = true; c.res.mp = 0; c.res.sp = 0;
T('unlimited: abilities usable at 0 MP/SP', c.use(2)); run(c, 1); T('unlimited: mp/sp stay full, nothing deducted', c.res.mp === c.res.max.mp && c.res.sp === c.res.max.sp);
c = mk(); c.res.unlimited = true; c.res.sp = 0; c.cd.reset(); T('unlimited: dodge ok at 0 SP, SP stays full', c.dodge(1, 0) && c.res.sp === c.res.max.sp);
c = mk(); c.res.unlimited = true; c.res.sp = 0; c.block(true); T('unlimited: block starts at 0 SP', c.blocking); run(c, 3); T('unlimited: block never drains', c.blocking && c.res.sp === c.res.max.sp);
c = mk(); c.res.unlimited = false; c.res.sp = 0; c.block(true); T('non-owner/off: block still needs SP', !c.blocking); c = mk(); c.dodge(1, 0); T('non-owner/off: costs still deducted', c.res.sp < c.res.max.sp);
{ const { createFlags } = await import('../www/proto3d/cheatflags.js'); const { createCheats } = await import('../www/proto3d/cheats.js'); const st = new Map(); const storage = { getItem: k => st.has(k) ? st.get(k) : null, setItem: (k, v) => st.set(k, String(v)) };
  const fl = createFlags(); T('non-owner flags: unlimited off by default (no cheats object)', fl.unlimited === false);
  const ch = createCheats({ flags: fl, storage, hooks: { unlimMode: on => storage.setItem('vn_owner_unlim_v1', on ? '1' : '0'), unlimPref: () => storage.getItem('vn_owner_unlim_v1') !== '0' } });
  ch.setUnlimited(true); T('owner toggle sets flag', fl.unlimited === true); ch.setUnlimited(false); T('toggle off persists', fl.unlimited === false && storage.getItem('vn_owner_unlim_v1') === '0'); ch.reset(); T('reset respects saved off pref', fl.unlimited === false); }
// No cooldowns: Owner skin only (gate = cheat flag AND hero.owner)
{ const nc = (id, flag) => { const k = mk(); k.setHero({ id, saber: id.includes('owner') }); k.noCooldown = flag; return k; };
  let k = nc('o:owner', true); k.res.unlimited = true;
  T('nocd owner: basic spam (no cooldown)', k.use(0) && (k.act = null, k.cd.left('basic') === 0 && k.use(0)));
  k = nc('o:owner', true); k.res.unlimited = true; T('nocd owner: ability reusable at once', k.use(2) && (k.act = null, k.use(2)));
  k = nc('o:owner', true); T('nocd owner: dodge twice', k.dodge(1, 0) && k.dodge(1, 0));
  k = nc('o:owner', true); k.res.hp = 1; T('nocd owner: potion twice', k.potion() && (k.res.hp = 1, k.potion()));
  k = nc('o:owner', true); k.jump(); T('nocd owner: jump no cooldown', k.cd.left('jump') === 0);
  k = nc('n:darius', true); k.use(0); T('other hero as owner: basic cooldown applies', k.cd.left('basic') > 0);
  k = nc('n:darius', true); k.dodge(1, 0); T('other hero as owner: dodge cooldown applies', k.cd.left('dodge') > 0 && !k.dodge(1, 0));
  k = nc('o:owner', false); k.dodge(1, 0); T('non-owner/off (owner skin, flag off): dodge cooldown applies', k.cd.left('dodge') > 0 && !k.dodge(1, 0));
  k = nc('o:owner', false); k.use(2); T('non-owner/off: ability cooldown applies', k.cd.left(ABILITIES[2].id) > 0);
  const { createFlags } = await import('../www/proto3d/cheatflags.js'); const { createCheats } = await import('../www/proto3d/cheats.js'); const st = new Map(); const storage = { getItem: q => st.has(q) ? st.get(q) : null, setItem: (q, v) => st.set(q, String(v)) };
  const fl = createFlags(); T('non-owner flags: noCooldown off (no cheats object)', fl.noCooldown === false);
  const ch = createCheats({ flags: fl, storage, hooks: { nocdMode: on => storage.setItem('vn_owner_nocd_v1', on ? '1' : '0'), nocdPref: () => storage.getItem('vn_owner_nocd_v1') !== '0' } });
  ch.setNoCooldown(true); T('nocd toggle sets flag', fl.noCooldown === true); ch.setNoCooldown(false); T('nocd off persists', fl.noCooldown === false && storage.getItem('vn_owner_nocd_v1') === '0'); ch.reset(); T('reset respects saved off pref', fl.noCooldown === false); st.clear(); ch.reset(); T('default ON when no pref', fl.noCooldown === true); }
// ---- Owner HUD skills + Unholy Destruction (1.1.9.4) ----
{ const { TUNING } = await import('../www/proto3d/combat/data.js');
  const ow = (unlocked = true, id = 'o:owner') => { const k = mk(); k.setHero({ id, saber: id.includes('owner') }); k.ownerUnlocked = unlocked; k.res.unlimited = false; k.fury = 100; return k; };
  const go = (k, s) => { for (let i = 0; i < s * 60; i++) k.update(1 / 60); };
  let k = ow(); let w1 = k.addEnemy('wolf', 0, 10), w2 = k.addEnemy('raider', 20, 0), far = k.addEnemy('wolf', 0, 40), bo = k.addEnemy('titan', 0, 15);
  let deaths = 0, rew = 0; k.on('defeat', () => deaths++); k.on('reward', () => rew++); k.use('unholy'); go(k, 0.3);
  T('ult: nothing dies before the meteor lands', w1.state !== 'defeated'); go(k, 1.5);
  T('ult: eligible monsters within 25 m defeated', w1.state === 'defeated' && w2.state === 'defeated');
  T('ult: monster beyond 25 m survives', far.state !== 'defeated');
  T('ult: boss NOT instantly killed, takes normal saber hit (99,999)', bo.state !== 'defeated' && bo.max - bo.hp === 99999);
  T('ult: death handler exactly once per monster', deaths === 2 && rew === 2 && k.kills === 2);
  T('ult: Fury spent, 35 s cooldown', k.fury === 0 && k.cd.left('unholy') > 32 && k.cd.left('unholy') <= 35);
  k = ow(); k.res.hp = k.res.max.hp - 5; const hp0 = k.res.hp; k.addEnemy('wolf', 0, 5).def = Object.assign({}, ENEMIES_atk0()); k.use('unholy'); go(k, 0.1);
  function ENEMIES_atk0() { return { name: 'w', level: 1, cls: 'x', hp: 100, atk: 0, def: 0, speed: 0, atkMs: 9e9, tele: 9, reach: 0, aggro: 0, scale: 1, xp: 1, gold: 1, boss: false, stagger: 0, poise: 0, r: 1 }; }
  go(k, 2); T('ult: Owner hp untouched by meteor', k.res.hp === hp0 && k.p.dead === false);
  k = ow(); k.fury = 50; T('ult: needs full Fury', !k.use('unholy')); k.fury = 100; T('ult: castable at full Fury', k.use('unholy'));
  k = ow(false); T('ult: denied without owner gate (programmatic request)', !k.use('unholy') && k.meteors.length === 0);
  k = ow(true, 'n:darius'); k.setHero({ id: 'n:darius', saber: false }); T('ult: denied for other hero', !k.use('unholy') && !k.use('royal') && !k.use('chains') && !k.use('wrath') && !k.slotUsable('unholy'));
  k = ow(); k.hero.id = 'o:owner'; k.setHero({ id: 'n:darius', saber: false }); k.ownerUnlocked = true; T('ult: owner flag gone after swap to other hero (no saber)', !k.ownerOk());
  k = ow(); k.cd.ready.set('unholy', 99); T('ult: blocked during cooldown', !k.use('unholy'));
  k = ow(); k.noCooldown = true; k.fury = 100; k.use('unholy'); k.act = null; go(k, 2); k.fury = 100; T('ult: no-cooldown toggle respected (recast immediately), Fury still required', k.use('unholy') && (k.act = null, !k.use('unholy')));
  k = ow(); k.res.unlimited = true; k.fury = 0; k.res.mp = 0; T('ult/skills: unlimited MP/SP => Fury treated full + skills cast at 0 MP', k.use('unholy') && (k.act = null, k.use('royal')) );
  k = ow(); const e1 = k.addEnemy('wolf', 0, 5); e1.friendly = true; const e2 = k.addEnemy('wolf', 0, 6); e2.protected = true; const e3 = k.addEnemy('wolf', 0, 7); k.use('holy'); go(k, 2); T('ult: friendly/protected entities untouched', e1.state !== 'defeated' && e2.state !== 'defeated' && e3.state === 'defeated');
  const keep = TUNING.ult.bossesInstantKill; TUNING.ult.bossesInstantKill = true; k = ow(); const b2 = k.addEnemy('titan', 0, 15); let bd = 0; k.on('defeat', () => bd++); k.use('unholy'); go(k, 2); T('ult: bossesInstantKill flag true => boss defeated once', b2.state === 'defeated' && bd === 1); TUNING.ult.bossesInstantKill = keep;
  k = ow(); const s1 = k.addEnemy('wolf', 0, 5); k.use('royal'); go(k, 0.5); T('royal slash: cone hit, 99,999 saber rule', s1.state === 'defeated');
  k = ow(); const s2 = k.addEnemy('titan', 0, 10); k.use('chains'); go(k, 0.5); T('chains (saber held): flat 99,999 on boss', s2.max - s2.hp === 99999);
  k = ow(); const s3 = k.addEnemy('titan', 0, 6), s4 = k.addEnemy('wolf', 0, -4); k.use('wrath'); go(k, 0.5); T('wrath: area burst hits all around, 99,999 x1200% on boss', s4.state === 'defeated' && s3.max - s3.hp === 99999);
  k = ow(); k.fury = 0; const w9 = k.addEnemy('wolf', 0, 3); k.use(0); go(k, 0.5); T('fury builds from owner hits', k.fury === TUNING.ult.furyPerBasic);
  k = ow(); k.use('unholy'); go(k, 0.5); k.res.hp = 0; k.enemyStrike({ def: { reach: 99, r: 1, atk: 9e9 }, x: 0, z: 0 }); go(k, 0.2); T('meteor cancelled if owner dies before landing', k.meteors.length === 0 || k.dead > 0);
}
// ---- saber-holder rule: owner ACCOUNT + (Owner skin OR hero wielding the Owner saber); perks (unlimited/no-cd) stay Owner-skin only ----
{ const { TUNING } = await import('../www/proto3d/combat/data.js'); const go = (k, s) => { for (let i = 0; i < s * 60; i++) k.update(1 / 60); };
  const hero = (id, saber, unlocked) => { const k = mk(); k.setHero({ id, saber }); k.ownerUnlocked = unlocked; k.fury = 100; return k; };
  let k = hero('n:darius', true, true); k.addEnemy('wolf', 0, 5); T('holder: other hero WITH saber (owner account) gets owner ability set', k.ownerOk() && k.slotUsable('royal') && k.slotUsable('chains') && k.slotUsable('wrath') && k.slotUsable('unholy'));
  const m1 = k.addEnemy('raider', 0, 8), m2 = k.addEnemy('wolf', 0, 12); k.use('unholy'); go(k, 2); T('holder: Unholy Destruction works for saber holder', m1.state === 'defeated' && m2.state === 'defeated');
  k = hero('n:darius', true, true); const tt = k.addEnemy('titan', 0, 8); k.use('royal'); go(k, 0.5); T('holder: saber rule, flat 99,999 on boss', tt.max - tt.hp === 99999);
  k = hero('n:darius', false, true); T('holder: other hero WITHOUT saber has no owner abilities', !k.ownerOk() && !k.use('royal') && !k.use('unholy') && !k.slotUsable('wrath'));
  k = hero('n:darius', true, false); T('holder: non-owner account never (even if hero.saber were set)', !k.ownerOk() && !k.use('royal') && !k.use('unholy') && k.meteors.length === 0);
  k = hero('o:owner', true, false); T('holder: Owner skin on non-unlocked account gets no owner skills', !k.use('royal') && !k.use('unholy'));
  k = hero('n:darius', true, true); k.noCooldown = true; k.use('royal'); T('perks: holder gets NO cooldown skip by default (Owner skin only)', k.cd.left('royal') > 0 && !k.perkHero());
  k = hero('o:owner', true, true); k.noCooldown = true; k.use('royal'); T('perks: Owner skin keeps no-cooldowns', k.cd.left('royal') === 0 && k.perkHero());
  TUNING.perks.saberHolderResources = true; k = hero('n:darius', true, true); k.noCooldown = true; T('perks: single flag extends perks to saber holder', k.perkHero() && (k.use('royal'), k.cd.left('royal') === 0)); k = hero('n:darius', true, false); k.noCooldown = true; T('perks flag never helps non-owner account', !k.perkHero()); TUNING.perks.saberHolderResources = false;
}
// ---- saber-holder boost (x holderMul max HP/MP/SP), not invincible ----
{ const { TUNING, PLAYER } = await import('../www/proto3d/combat/data.js'); const M = TUNING.perks.holderMul;
  const hero = (id, saber, unlocked) => { const k = mk(); k.ownerUnlocked = unlocked; k.setHero({ id, saber }); k.applyMax(); return k; };
  let k = hero('n:darius', true, true); T('boost: holder max HP/MP/SP x' + M, k.res.max.hp === PLAYER.hp * M && k.res.max.mp === PLAYER.mp * M && k.res.max.sp === PLAYER.sp * M && k.res.hp === k.res.max.hp);
  k.setHero({ id: 'n:darius', saber: false }); k.applyMax(); T('boost off: reverts when saber swapped away', k.res.max.hp === PLAYER.hp && k.res.max.mp === PLAYER.mp && k.res.max.sp === PLAYER.sp && k.res.hp === PLAYER.hp);
  k.setHero({ id: 'n:darius', saber: true }); k.applyMax(); T('boost on again when saber back', k.res.max.hp === PLAYER.hp * M);
  k = hero('n:darius', true, false); T('boost: non-owner account never boosted', k.res.max.hp === PLAYER.hp && k.res.max.mp === PLAYER.mp && k.res.max.sp === PLAYER.sp);
  k = hero('n:darius', false, true); T('boost: other hero without saber not boosted', k.res.max.hp === PLAYER.hp);
  k = mk(); k.ownerUnlocked = true; k.setHero({ id: 'n:darius', saber: true }); k.applyMax(); k.ownerUnlocked = false; k.update(1 / 60); T('boost: reverts live if owner gate drops', k.res.max.hp === PLAYER.hp);
  k = hero('o:owner', true, true); T('boost: Owner skin keeps 999,999 (no multiplier)', k.res.max.hp === PLAYER.ownerHp && k.res.max.mp === PLAYER.mp);
  k = hero('n:darius', true, true); k.res.hp = 10; k.god = false; k.addEnemy('titan', 0, 4); let took = 0; k.on('enemyAttack', a => { if (a.dmg > 0) took++; }); for (let i = 0; i < 60 * 6; i++) k.update(1 / 60); T('holder: NOT invincible (takes hits, goes down)', took >= 1 || k.dead > 0);
  k = hero('n:darius', true, true); k.noCooldown = true; k.use('royal'); T('holder: costs + cooldowns normal (no unlimited/no-cd)', k.res.mp === k.res.max.mp - 12 && k.cd.left('royal') > 0 && !k.perkHero());
}
// ---- saber x12 current-HP rule ----
{ const go = (k, sec) => { for (let i = 0; i < sec * 60; i++) k.update(1 / 60); };
  const o = (id = 'o:owner', saber = true, unlocked = true) => { const k = mk(); k.setHero({ id, saber }); k.ownerUnlocked = unlocked; k.res.unlimited = true; return k; };
  let k = o(); const evs = []; k.on('damage', d => !d.toPlayer && evs.push(d)); let m = k.addEnemy('wolf', 0, 3); m.hp = 77; k.use(0); go(k, 0.5);
  T('x12: regular monster takes current HP x12 and dies', evs[0] && evs[0].dmg === 77 * 12 && m.state === 'defeated');
  k = o(); const ev2 = []; k.on('damage', d => !d.toPlayer && ev2.push(d)); let r = k.addEnemy('raider', 0, 3); const full = r.hp; k.use(0); go(k, 0.5); T('x12: full-health monster shows hp*12', ev2[0].dmg === full * 12 && r.state === 'defeated');
  k = o(); let tt = k.addEnemy('titan', 0, 8); const e3 = []; k.on('damage', d => !d.toPlayer && e3.push(d)); k.use(0); go(k, 0.6); T('x12: boss (Ashen Titan) stays flat 99,999 by default', tt.max - tt.hp === 99999 && e3.every(d => d.dmg === 99999) && TUNING.perks.saberBossesX12 === false);
  TUNING.perks.saberBossesX12 = true; k = o(); tt = k.addEnemy('titan', 0, 8); const e4 = []; k.on('damage', d => !d.toPlayer && e4.push(d)); k.use(0); go(k, 0.6); T('x12: flag flips bosses to current HP x12', e4[0] && e4[0].dmg === 5000000 * 12 && tt.state === 'defeated'); TUNING.perks.saberBossesX12 = false;
  k = o('n:darius', true, true); m = k.addEnemy('wolf', 0, 3); m.hp = 50; const e5 = []; k.on('damage', d => !d.toPlayer && e5.push(d)); k.use('royal'); go(k, 0.6); T('any hero holding the saber: skills use the saber rule (x12 current HP)', e5.some(d => d.dmg === 600) && m.state === 'defeated');
  k = o('n:darius', true, false); m = k.addEnemy('wolf', 0, 3); m.hp = 50; const e6 = []; k.on('damage', d => !d.toPlayer && e6.push(d)); k.use(0); go(k, 0.6); T('x12: non-owner account never gets x12', !e6.some(d => d.dmg === 600));
  k = o('n:darius', false, true); m = k.addEnemy('wolf', 0, 3); m.hp = 1000; const e7 = []; k.on('damage', d => !d.toPlayer && e7.push(d)); k.use(0); go(k, 0.6); T('x12: other weapons unchanged (unarmed 28-48)', e7.length > 0 && e7.every(d => d.dmg < 200));
  k = o(); const hp0 = k.res.hp; k.use(0); go(k, 0.5); T('x12: never touches the owner', k.res.hp === hp0);
}
{ const go = (k, sec) => { for (let i = 0; i < sec * 60; i++) k.update(1 / 60); };
  const o = () => { const k = mk(); k.ownerUnlocked = true; k.res.unlimited = true; return k; };
  const hit = (mul, boss) => { TUNING.perks.saberMul = mul; const k = o(); const m = k.addEnemy(boss ? 'titan' : 'wolf', 0, 4); m.hp = boss ? 1000000 : 40; const ev = []; k.on('damage', d => !d.toPlayer && ev.push(d)); k.use(0); go(k, 0.6); return ev[0] && ev[0].dmg; };
  T('mult: x1 = current HP, x5, x50', hit(1) === 40 && hit(5) === 200 && hit(50) === 2000);
  T('mult: 0 = flat 99,999 (old behavior)', hit(0) === 99999 && hit(0, true) === 99999);
  T('mult: out-of-range clamps (99 -> 50, -3 -> flat)', hit(99) === 2000 && hit(-3) === 99999);
  TUNING.perks.saberBossesX12 = true; T('mult: boss toggle applies chosen multiplier to bosses', hit(3, true) === 3000000); TUNING.perks.saberBossesX12 = false;
  T('mult: boss unaffected when toggle off', hit(3, true) === 99999); TUNING.perks.saberMul = 12; }
{ const go = (k, sec) => { for (let i = 0; i < sec * 60; i++) k.update(1 / 60); };
  const o = () => { const k = mk(); k.ownerUnlocked = true; k.res.unlimited = true; k.fury = 100; return k; };
  let k = o(); const a = k.addEnemy('wolf', 0, 8), b = k.addEnemy('raider', 5, 10), far = k.addEnemy('wolf', 0, 60); a.hp = 30; const ev = []; k.on('damage', d => !d.toPlayer && ev.push(d)); k.use('unholy'); go(k, 2.5);
  T('ult x50: shows current HP x50 on each target and kills', ev.find(d => d.e === a).dmg === 30 * 50 && ev.find(d => d.e === b).dmg === b.max * 50 && a.state === 'defeated' && b.state === 'defeated' && far.state !== 'defeated');
  const hp0 = k.res.hp; T('ult: owner untouched', k.res.hp === hp0);
  k = o(); const ch = k.addEnemy('wolf', 0, 8), npc = k.addEnemy('wolf', 2, 8), pty = k.addEnemy('wolf', 3, 8), fr = k.addEnemy('wolf', 4, 8); ch.isCharacter = true; npc.npc = true; pty.party = true; fr.friendly = true; k.use('holy'); go(k, 2.5);
  T('ult: hostile characters die; npc/party/friendly skipped by default (unholy variant tested below)', ch.state === 'defeated' && npc.state !== 'defeated' && pty.state !== 'defeated' && fr.state !== 'defeated');
  TUNING.ult.dmgMul = 7; k = o(); const m7 = k.addEnemy('wolf', 0, 8); m7.hp = 20; const e7 = []; k.on('damage', d => !d.toPlayer && e7.push(d)); k.use('unholy'); go(k, 2.5); T('ult: multiplier adjustable', e7[0].dmg === 140); TUNING.ult.dmgMul = 50;
  k = o(); const bo = k.addEnemy('titan', 0, 10); k.use('unholy'); go(k, 2.5); T('ult: boss still follows bossesInstantKill=false', bo.state !== 'defeated' && bo.max - bo.hp === 99999 * 1 || bo.max - bo.hp >= 99999 && bo.state !== 'defeated');
  k = o(); k.setHero({ id: 'n:darius', saber: false }); k.ownerUnlocked = false; k.fury = 100; T('ult: non-owner cannot cast', !k.use('unholy')); }
{ const go = (k, sec) => { for (let i = 0; i < sec * 60; i++) k.update(1 / 60); };
  const o = () => { const k = mk(); k.ownerUnlocked = true; k.res.unlimited = true; k.fury = 100; return k; };
  const setup = k => { const r = {}; r.mon = k.addEnemy('wolf', 0, 8); r.chr = k.addEnemy('raider', 2, 8); r.npc = k.addEnemy('wolf', 3, 8); r.pty = k.addEnemy('wolf', 4, 8); r.fr = k.addEnemy('wolf', -3, 8); r.own = k.addEnemy('wolf', -4, 8); r.far = k.addEnemy('wolf', 0, 70); r.chr.isCharacter = true; r.npc.npc = true; r.pty.party = true; r.fr.friendly = true; r.own.owner = true; return r; };
  let k = o(); T('two ultimates exist; slot-4 default is Holy; swap picks Unholy', k.slotUsable('holy') && k.slotUsable('unholy') && k.ultSel === 'holy');
  k = o(); let r = setup(k); k.use('holy'); go(k, 2.5);
  T('HOLY: kills hostile monsters + hostile characters', r.mon.state === 'defeated' && r.chr.state === 'defeated');
  T('HOLY: never npc/party/friendly/owner, nothing out of range', r.npc.state !== 'defeated' && r.pty.state !== 'defeated' && r.fr.state !== 'defeated' && r.own.state !== 'defeated' && r.far.state !== 'defeated');
  k = o(); r = setup(k); const by = [{ x: 1, z: 5, hp: 100, id: 'party1' }, { x: 2, z: 5, hp: 40, isOwner: true }, { x: 0, z: 90, hp: 9 }]; k.bystanders = () => by; const bk = []; k.on('bystanderKill', e => bk.push(e)); const ev = []; k.on('damage', d => !d.toPlayer && ev.push(d)); k.use('unholy'); go(k, 2.5);
  T('UNHOLY: kills everything in range incl. npc/party/friendly entities', ['mon', 'chr', 'npc', 'pty', 'fr'].every(n => r[n].state === 'defeated'));
  T('UNHOLY: never the owner (flagged enemy or bystander) and not out of range', r.own.state !== 'defeated' && r.far.state !== 'defeated' && bk.length === 1 && bk[0].b.id === 'party1' && bk[0].dmg === 100 * 50);
  T('UNHOLY: x50 current HP shown', ev.find(d => d.e === r.mon).dmg === r.mon.max * 50);
  k = o(); k.setHero({ id: 'n:darius', saber: true }); k.ownerUnlocked = true; T('both ultimates work for saber holders (owner account)', k.ownerOk() && k.use('unholy'));
  k = o(); k.ownerUnlocked = false; k.fury = 100; T('both ultimates denied without owner gate', !k.use('holy') && !k.use('unholy'));
  k = o(); const bb = k.addEnemy('titan', 0, 10); k.use('holy'); go(k, 2.5); T('HOLY: boss follows bossesInstantKill=false', bb.state !== 'defeated');
}
{ const go = (k, sec) => { for (let i = 0; i < sec * 60; i++) k.update(1 / 60); };
  const o = (sab = false) => { const k = mk(sab); k.ownerUnlocked = true; k.res.unlimited = true; return k; };
  const dm = (id, sab = false) => { const k = o(sab); const t = k.addEnemy('titan', 0, 6); const ev = []; k.on('damage', d => !d.toPlayer && ev.push(d)); k.use(id); go(k, 0.6); return ev[0] && ev[0].dmg; };
  T('skills: Royal 300% / Chains 600% / Wrath 1200% of 99,999', dm('royal') === 299997 && dm('chains') === 599994 && dm('wrath') === 1199988);
  const sv = { ...TUNING.skillMul }; TUNING.skillMul.royal = 10; T('skills: multipliers live in one config block', dm('royal') === 999990); Object.assign(TUNING.skillMul, sv);
  let k = o(true); const w = k.addEnemy('wolf', 0, 3); w.hp = 30; const ev = []; k.on('damage', d => !d.toPlayer && ev.push(d)); k.use(0); go(k, 0.5); T('basic saber hit stays x12 current HP', ev[0].dmg === 360);
  k = o(); k.setHero({ id: 'n:darius', saber: false }); k.ownerUnlocked = false; const t2 = k.addEnemy('wolf', 0, 3); { const k2 = o(true); const w2 = k2.addEnemy('wolf', 0, 4); w2.hp = 25; const e2 = []; k2.on('damage', d => !d.toPlayer && e2.push(d)); k2.use('royal'); go(k2, 0.6); T('skills WITH saber held: saber rule (x12 current HP), not the skill multiplier', e2[0] && e2[0].dmg === 300); const t3 = o(true); const tt3 = t3.addEnemy('titan', 0, 6); const e3 = []; t3.on('damage', d => !d.toPlayer && e3.push(d)); t3.use('wrath'); go(t3, 0.6); T('saber held + boss: flat 99,999 (no x1200)', e3[0].dmg === 99999); }
  T('skills: no owner skill without gate', !k.use('royal') && !k.use('chains') && !k.use('wrath'));
}
console.log(ok + ' pass, ' + bad + ' fail'); process.exit(bad ? 1 : 0);
