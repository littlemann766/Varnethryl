// Frost Troll (elite with patterns) + enemy Vaelthryx boss patterns.
import { CombatController } from '../www/proto3d/combat/controller.js';
import { ENEMIES, BOSS_PATTERNS, TUNING } from '../www/proto3d/combat/data.js';
let ok = 0, bad = 0; const T = (n, c) => { c ? ok++ : bad++; console.log(c ? 'PASS' : 'FAIL', n); };
let seed = 99; const rnd = () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
const mk = () => { const c = new CombatController({ HS: 1.5, rng: rnd }); c.setHero({ id: 'aldric', saber: false }); c.setPlayer(0, 0, 0); return c; };
const go = (k, s) => { for (let i = 0; i < s * 60; i++) k.update(1 / 60); };
T('vaelthryx enemy def is a boss with the 10x rig', ENEMIES.vaelthryx && ENEMIES.vaelthryx.boss && ENEMIES.vaelthryx.model === 'n:vaelthryx_new7' && ENEMIES.vaelthryx.scale === 10);
T('frost troll stays an elite (not a boss) but has patterns', !ENEMIES.frosttroll.boss && ENEMIES.frosttroll.patterns && BOSS_PATTERNS.frosttroll.length >= 3);
for (const key of ['frosttroll', 'vaelthryx', 'titan']) {
  const c = mk(); c.god = true; const e = c.addEnemy(key, 0, 3); const seen = new Set(); c.on('bossAttack', a => seen.add(a.pat.id));
  go(c, 40); const p1 = BOSS_PATTERNS[key].filter(p => !p.phase).map(p => p.id);
  T(key + ': rotates through all phase-1 patterns', p1.every(id => seen.has(id)));
  T(key + ': no phase-2 move before enrage', !BOSS_PATTERNS[key].filter(p => p.phase === 2).some(p => seen.has(p.id)));
  e.hp = e.max * 0.4; let ph = 0; c.on('bossPhase', () => ph++); go(c, 0.2); T(key + ': enrages under ' + TUNING.boss.enrageAt * 100 + '%', ph === 1 && e.phase === 2);
  seen.clear(); go(c, 50); T(key + ': phase-2 move appears after enrage', BOSS_PATTERNS[key].filter(p => p.phase === 2).every(p => seen.has(p.id)));
}
{ const c = mk(); const e = c.addEnemy('frosttroll', 0, 2); e.pat = BOSS_PATTERNS.frosttroll.find(p => p.id === 'stomp'); let ch = 0; c.on('chilled', () => ch++);
  for (let i = 0; i < 10 && !ch; i++) { seed = 123456789 + i * 7919; c.iframes = 0; e.pat = BOSS_PATTERNS.frosttroll[1]; c.enemyStrike(e); }
  T('frost stomp chills the player', ch >= 1 && c.chill > 0 && c.chillAmt === 0.4); go(c, 3); T('chill wears off', c.chill === 0); }
{ const c = mk(); c.god = true; const e = c.addEnemy('frosttroll', 0, 30); let atk = 0; c.on('bossAttack', a => { if (!a.hit) atk++; }); go(c, 2); T('patterns only fire in range', atk === 0); }
console.log(ok + ' pass, ' + bad + ' fail'); process.exit(bad ? 1 : 0);
