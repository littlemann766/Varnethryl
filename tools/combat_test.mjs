import { CombatController } from '../www/proto3d/combat/controller.js';
import { loadLucian, usingLucian } from '../www/proto3d/combat/calc.js';
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
T('titan has 250000 hp / 2100 atk / 2300ms', t.max === 250000 && t.def.atk === 2100 && t.def.atkMs === 2300 && t.def.scale === 6);
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
c = mk(); w = c.addEnemy('titan', 0, 4); c.cd.reset(); c.use(5); run(c, 1.3); T('ultimate hits 3x99999 (kills titan)', w.state === 'defeated');
c = mk(); w = c.addEnemy('titan', 0, 4); let dd = []; c.on('enemyAttack', a => a.dmg > 0 && dd.push(a.dmg)); run(c, 8); T('owner has 999999 max hp, takes normal damage', c.res.max.hp === 999999 && dd.length >= 1 && dd[0] > 1000 && c.res.hp < 999999);
c = mk(); c.setHero({ id: 'n:darius', saber: false }); w = c.addEnemy('titan', 0, 4); dd = []; c.on('enemyAttack', a => a.dmg > 0 && dd.push(a.dmg)); run(c, 4); T('non-owner takes full damage', dd.length >= 1 && dd[0] > 1000);
for (const [k, lo, hi] of [['wolf', 8, 15], ['raider', 11, 22]]) { c = mk(false); c.setHero({ id: 'n:darius', saber: false }); c.setPlayer(0, 0, 0); w = c.addEnemy(k, 0, 3); w.def = Object.assign({}, w.def, { atk: 0 }); let tt = 0, st = 0; c.on('enemyAttack', () => {}); const seenS = new Set(); while (w.state !== 'defeated' && tt < 120) { c.use(0); c.update(1 / 60); tt += 1 / 60; seenS.add(w.state); w.x = 0; w.z = 3; } T('normal char kills ' + k + ' in ' + lo + '-' + hi + 's (' + tt.toFixed(1) + 's)', tt >= lo && tt <= hi); if (k === 'wolf') T('normal hits stagger the enemy', seenS.has('stagger')); }
c = mk(false); c.setHero({ id: 'n:darius', saber: false }); c.setPlayer(0, 0, 0); w = c.addEnemy('skeleton', 0, 3); w.def = Object.assign({}, w.def, { atk: 0 }); let t3 = 0; while (w.state !== 'defeated' && t3 < 300) { c.use(0); c.update(1 / 60); t3 += 1 / 60; w.x = 0; w.z = 3; } T('normal char: elite takes longer (' + t3.toFixed(0) + 's)', t3 > 30);
console.log(ok + ' pass, ' + bad + ' fail'); process.exit(bad ? 1 : 0);
