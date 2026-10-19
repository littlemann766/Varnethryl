/* CompanionCombat: followers/companions fight alongside the hero (modular, no THREE, no DOM). The host (main.js/fight.js) feeds it the follower list each frame and
   moves/animates them; this file owns target choice, stand-off distance, attack cadence and damage. Companions are modest (several hits per enemy; only the Owner is overpowered),
   never touch hero state, and downed ones (r.down > 0) do nothing. Cost: a target scan per follower every ~0.4 s, O(enemies); everything else is O(followers). */
import { TUNING } from './data.js';
export const COMPANION = { dmg: [95, 150], cdMs: [1100, 1500], windup: 0.22, reach: 2.6, rangedReach: 10, engageR: 12, idleEngageR: 6, leash: 20, rangedRe: /seraphine|zephyr|lunara|marella|ember|pip|wren|elira|mage/i };
export class CompanionCombat {
  constructor(o) { this.cc = o.cc; this.HS = o.HS || 1.5; this.rng = o.rng || Math.random; this.onSwing = o.onSwing || null; this.on = true; this.t = 0; }
  /* host reads this each frame to steer the follower: {x,z,face} or null (null = follow the hero as usual) */
  goal(r) { const c = r.cmb; return c && c.tgt && c.tgt.state !== 'defeated' && !(r.down > 0) ? c.go : null; }
  update(dt, followers, hero) {
    this.t += dt; const cc = this.cc, HS = this.HS, C = COMPANION;
    for (let i = 0; i < followers.length; i++) {
      const r = followers[i], c = r.cmb || (r.cmb = { tgt: null, go: { x: 0, z: 0, face: 0 }, scan: this.rng() * 0.4, cd: 0.5 + this.rng() * 0.6, wind: -1, ranged: C.rangedRe.test(r.id || '') });
      if (r.down > 0 || !this.on || r.kind !== 'party' || r.level !== hero.level || hero.level !== 0 || cc.dead > 0 || hero.dead) { c.tgt = null; c.wind = -1; continue; }
      const a = r.a; c.cd -= dt; c.scan -= dt;
      if (c.tgt && (c.tgt.state === 'defeated' || Math.hypot(c.tgt.x - hero.x, c.tgt.z - hero.z) > C.leash * HS)) c.tgt = null;
      if (c.scan <= 0) {
        c.scan = 0.35 + this.rng() * 0.1; let best = null, bd = 1e18;
        for (const e of cc.enemies) { if (e.state === 'defeated') continue; const dh = Math.hypot(e.x - hero.x, e.z - hero.z);
          if (dh > (e.state === 'idle' ? C.idleEngageR : C.engageR) * HS) continue;   // idle monsters keep their stand-off unless right next to the party
          const d = Math.hypot(e.x - a.x, e.z - a.z); if (d < bd) { bd = d; best = e; } }
        if (best !== c.tgt) { c.tgt = best; c.wind = -1; }
      }
      const e = c.tgt; if (!e) { c.wind = -1; continue; }
      const dx = e.x - a.x, dz = e.z - a.z, d = Math.hypot(dx, dz) || 1e-6, reach = (c.ranged ? C.rangedReach : C.reach) * HS * 0.8 + e.def.r, nx = dx / d, nz = dz / d;
      c.go.face = Math.atan2(nx, nz);
      if (d > reach) { c.go.x = e.x - nx * reach * 0.9; c.go.z = e.z - nz * reach * 0.9; c.wind = -1; }   // close in (melee) / take position (ranged)
      else { c.go.x = a.x; c.go.z = a.z; if (c.wind < 0 && c.cd <= 0) { c.wind = C.windup; if (this.onSwing) this.onSwing(r, e, c.ranged); }
        if (c.wind >= 0) { c.wind -= dt; if (c.wind <= 0) { c.wind = -1; c.cd = (C.cdMs[0] + (C.cdMs[1] - C.cdMs[0]) * this.rng()) / 1000; cc.companionHit(e, C.dmg, a.x, a.z, this.rng); } } }
    }
  }
}
