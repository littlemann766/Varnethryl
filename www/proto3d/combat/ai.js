/* EnemyAIController: idle -> chase -> telegraph -> attack -> recover, with stagger and defeated. Pure state machine; the controller applies results. */
import { BOSS_PATTERNS, TUNING } from './data.js';
/* Boss pattern pick: ordered rotation over the patterns available in the current phase (deterministic, learnable). Non-bosses return null (classic single attack). */
export function pickPattern(e) { const L = BOSS_PATTERNS[e.key]; if (!e.def.boss || !L) return null; const ph = e.phase || 1, A = L.filter(p => (p.phase || 1) <= ph); e.patI = (e.patI || 0) + 1; return A[(e.patI - 1) % A.length]; }
export class EnemyAIController {
  /* returns 'attack' on the frame the telegraphed strike lands (controller resolves hit), else null. env.move(e,dx,dz) lets the host do collision. */
  update(e, p, dt, env) {
    if (e.state === 'defeated') return null;
    e.tStateT += dt; e.atkCd = Math.max(0, e.atkCd - dt); e.flash = Math.max(0, e.flash - dt);
    const dx = p.x - e.x, dz = p.z - e.z, d = Math.hypot(dx, dz) || 1e-6, nx = dx / d, nz = dz / d, reach = e.def.reach * env.HS + e.def.r;
    if (e.state !== 'telegraph' && e.state !== 'attack') e.yaw = Math.atan2(nx, nz);
    if (e.knockT > 0) { e.knockT = Math.max(0, e.knockT - dt); env.move(e, e.kx * 9 * e.knockT * dt * 4, e.kz * 9 * e.knockT * dt * 4); }
    switch (e.state) {
      case 'idle': if (!p.dead && d < (e.aggroR !== undefined ? e.aggroR : e.def.aggro * env.HS / 1.5 * 1.4 * Math.max(1, 0.5 + 0.5 * (env.RM || 1)))) this.set(e, 'chase'); break;
      case 'chase':
        if (p.dead) { this.set(e, 'idle'); break; }
        const spd = e.phase === 2 ? TUNING.boss.enrageSpeed : 1, pt = e.def.boss ? (e.pat || (e.pat = pickPattern(e))) : null, eng = pt ? pt.reach * env.HS + e.def.r : reach;
        if (d > eng * 0.8) { const sl = 1 - (e.slowT || 0); env.move(e, nx * e.def.speed * spd * sl * env.HS / 1.5 * dt, nz * e.def.speed * spd * sl * env.HS / 1.5 * dt); }   // Totem of Wind slow
        if (d <= eng && e.atkCd <= 0) { e.curTele = pt ? pt.tele * (e.phase === 2 ? TUNING.boss.enrageTele : 1) : e.def.tele; this.set(e, 'telegraph'); }
        break;
      case 'telegraph': if (e.tStateT >= (e.curTele || e.def.tele)) { this.set(e, 'attack'); return 'attack'; } break;
      case 'attack': if (e.tStateT >= 0.18) { e.atkCd = e.def.atkMs / 1000 * (e.phase === 2 ? TUNING.boss.enrageCd : 1); this.set(e, 'recover'); e.lastPat = e.pat; } break;
      case 'recover': if (e.tStateT >= 0.45) this.set(e, 'chase'); break;
      case 'stagger': if (e.tStateT >= e.staggerFor) this.set(e, 'chase'); break;
    }
    return null;
  }
  set(e, s) { e.state = s; e.tStateT = 0; }
  stagger(e, secs) { if (e.state === 'defeated') return false; if (e.def.poise && Math.random() < e.def.poise) return false; e.staggerFor = secs || e.def.stagger; this.set(e, 'stagger'); return true; }
}
