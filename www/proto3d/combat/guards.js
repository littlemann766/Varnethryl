/* Town guards (gate, guild hall, town hall): stationary posts that strike any living monster within GUARD.range (15 m).
   Damage comes only from DamageCalculator.guardHit. Targets only the combat controller's enemy list, so the hero / companions / townsfolk
   can never be hit. No per-frame allocation: posts are scanned on a fixed tick with plain loops; one small event object per strike (~1 / 1.5 s). */
import { DamageCalculator, GUARD } from './calc.js';
export class TownGuards {
  constructor(posts, rng = Math.random) { this.posts = posts.map(p => ({ x: p.x, z: p.z, at: p.at, cd: 0.4 + rng() * GUARD.cd, target: null })); this.rng = rng; this.scan = 0; this.hits = 0; this.dmgDone = 0; this.onStrike = null; }
  nearest(enemies, x, z) {
    let best = null, bd = GUARD.range; for (let i = 0; i < enemies.length; i++) { const e = enemies[i]; if (e.state === 'defeated' || e.hp <= 0) continue; const d = Math.hypot(e.x - x, e.z - z) - ((e.def && e.def.r) || 0); if (d <= bd) { bd = d; best = e; } }
    return best;
  }
  /* cc: CombatController (enemies, emit, defeat). */
  update(dt, cc) {
    const P = this.posts, E = cc.enemies; this.scan -= dt;
    const doScan = this.scan <= 0; if (doScan) this.scan = 0.25;
    for (let i = 0; i < P.length; i++) {
      const g = P[i]; g.cd -= dt;
      if (doScan) g.target = E.length ? this.nearest(E, g.x, g.z) : null;
      const e = g.target; if (!e || g.cd > 0) continue;
      if (e.state === 'defeated' || Math.hypot(e.x - g.x, e.z - g.z) - ((e.def && e.def.r) || 0) > GUARD.range) { g.target = null; continue; }
      g.cd = GUARD.cd; const r = DamageCalculator.guardHit(this.rng);
      e.hp = Math.max(0, e.hp - r.dmg); e.flash = 0.2; this.hits++; this.dmgDone += r.dmg;
      if (this.onStrike) this.onStrike(g, e);
      cc.emit('damage', { e, dmg: r.dmg, crit: false, toPlayer: false, byGuard: true });
      if (e.hp <= 0) { e.byGuard = true; cc.defeat(e); g.target = null; }
      else if (e.state === 'idle' && cc.ai && cc.ai.set) cc.ai.set(e, 'chase');
    }
  }
}
