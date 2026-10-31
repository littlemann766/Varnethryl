// Real party buffs + summons: Battle Hymn, Raise Thrall, Turret, Totem of Wind, Overclock.
import { CombatController } from '../www/proto3d/combat/controller.js';
import { KITS } from '../www/proto3d/combat/herokits.js';
let ok = 0, bad = 0; const T = (n, c) => { c ? ok++ : bad++; console.log(c ? 'PASS' : 'FAIL', n); };
let seed = 7; const rnd = () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
const mkh = (id) => { const c = new CombatController({ HS: 1.5, rng: rnd }); c.setHero({ id, saber: false }); c.setPlayer(0, 0, 0); c.res.unlimited = true; return c; };
const go = (k, s) => { for (let i = 0; i < s * 60; i++) k.update(1 / 60); };
const sk = (h, n) => KITS[h].skills.find(s => s.id === h + '.' + n);
T('skills are real kinds now (no shield/storm approximations)', sk('cedric', 1).kind === 'buff' && sk('brynn', 3).kind === 'buff' && sk('morwen', 1).kind === 'summon' && sk('brynn', 1).kind === 'summon' && sk('talia', 2).kind === 'summon');
// Battle Hymn
{ const a = mkh('cedric'), b = mkh('cedric'); const wa = a.addEnemy('raider', 0, 2.5), wb = b.addEnemy('raider', 0, 2.5); wa.state = wb.state = 'stagger';
  let ev = null; a.on('buff', e => ev = e); a.use('cedric.1'); go(a, 0.4); T('Battle Hymn: buff with party flag + name', ev && ev.id === 'hymn' && ev.party && a.buffs.length === 1);
  T('Battle Hymn: +20% damage', Math.abs(a.buffSum('dmg') - 0.2) < 1e-9); T('Battle Hymn: damage reduction', a.buffSum('reduce') > 0);
  go(a, 9); T('Battle Hymn expires', a.buffs.length === 0); }
// Overclock: cooldowns tick faster
{ const a = mkh('brynn'), b = mkh('brynn'); a.use('brynn.3'); go(a, 0.4); a.cd.start('x', 3); b.cd.start('x', 3); go(a, 1.5); go(b, 1.5); T('Overclock: cooldowns recover faster', a.cd.left('x') < b.cd.left('x') - 0.5); }
// Turret
{ const a = mkh('brynn'); const e = a.addEnemy('raider', 6, 6); e.state = 'stagger'; let hits = 0; a.on('summonAttack', () => hits++); a.use('brynn.1'); go(a, 0.4);
  T('Turret: one summon spawned', a.summons.length === 1 && a.summons[0].id === 'turret'); go(a, 3); T('Turret: shoots enemies in range', hits >= 2 && e.hp < e.max);
  a.use('brynn.1'); T('Turret: no stacking (cooldown / replace)', a.summons.filter(s => s.id === 'turret').length === 1); go(a, 13); T('Turret expires', a.summons.length === 0); }
// Raise Thrall
{ const a = mkh('morwen'); const e = a.addEnemy('wolf', 14, 0); e.state = 'stagger'; a.use('morwen.1'); go(a, 0.4); const s = a.summons[0]; const x0 = s.x;
  T('Thrall summoned with HP', s && s.id === 'thrall' && s.hpMax > 0); go(a, 4); T('Thrall chases and damages the nearest enemy', Math.abs(s.x - x0) > 3 && e.hp < e.max); }
// Totem of Wind
{ const a = mkh('talia'); const e = a.addEnemy('wolf', 4, 0); a.use('talia.2'); go(a, 0.5); T('Totem placed at the player', a.summons[0] && a.summons[0].id === 'totem');
  T('Totem slows enemies inside', e.slowT > 0); T('Totem protects + hastes the player inside', a.buffSum('reduce') >= 0.2 && a.buffSum('haste') > 0);
  a.setPlayer(200, 200, 0); T('leaving the totem removes its aura', a.buffSum('reduce') === 0); }
// reduce applies to incoming damage
{ const a = mkh('cedric'), b = mkh('cedric'); a.use('cedric.1'); go(a, 0.4); a.res.unlimited = b.res.unlimited = false; a.res.hp = a.res.max.hp; b.res.hp = b.res.max.hp; const ea = a.addEnemy('raider', 0, 1), eb = b.addEnemy('raider', 0, 1); let da = 0, db = 0; a.on('enemyAttack', v => da += v.dmg); b.on('enemyAttack', v => db += v.dmg); for (let i = 0; i < 20; i++) { seed = 123456789 + i * 7919; a.iframes = 0; a.enemyStrike(ea); a.res.hp = a.res.max.hp; seed = 123456789 + i * 7919; b.iframes = 0; b.enemyStrike(eb); b.res.hp = b.res.max.hp; } T('buff damage reduction lowers hits taken', da < db); }
// Owner untouched + respawn clears
{ const o = new CombatController({ HS: 1.5, rng: rnd }); o.setHero({ id: 'o:owner', saber: true }); o.ownerUnlocked = true; o.addBuff({ id: 'hymn', dur: 5, dmg: 0.5 }); const e = o.addEnemy('wolf', 0, 2); o.hitEnemy(e, 1, {}); T('party dmg buff never changes Owner damage rules', e.max - e.hp === 99999 || e.state === 'defeated'); }
{ const a = mkh('brynn'); a.use('brynn.1'); go(a, 0.4); a.respawn(); T('respawn clears summons and buffs', a.summons.length === 0 && a.buffs.length === 0); }
console.log(ok + ' pass, ' + bad + ' fail'); process.exit(bad ? 1 : 0);
