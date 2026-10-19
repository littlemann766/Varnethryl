/* EnemyAIController: idle -> chase -> telegraph -> attack -> recover, with stagger and defeated. Pure state machine; the controller applies results. */
export class EnemyAIController {
  /* returns 'attack' on the frame the telegraphed strike lands (controller resolves hit), else null. env.move(e,dx,dz) lets the host do collision. */
  update(e, p, dt, env) {
    if (e.state === 'defeated') return null;
    e.tStateT += dt; e.atkCd = Math.max(0, e.atkCd - dt); e.flash = Math.max(0, e.flash - dt);
    const dx = p.x - e.x, dz = p.z - e.z, d = Math.hypot(dx, dz) || 1e-6, nx = dx / d, nz = dz / d, reach = e.def.reach * env.HS + e.def.r;
    if (e.state !== 'telegraph' && e.state !== 'attack') e.yaw = Math.atan2(nx, nz);
    if (e.knockT > 0) { e.knockT = Math.max(0, e.knockT - dt); env.move(e, e.kx * 9 * e.knockT * dt * 4, e.kz * 9 * e.knockT * dt * 4); }
    switch (e.state) {
      case 'idle': if (!p.dead && d < (e.aggroR !== undefined ? e.aggroR : e.def.aggro * env.HS / 1.5 * 1.4)) this.set(e, 'chase'); break;
      case 'chase':
        if (p.dead) { this.set(e, 'idle'); break; }
        if (d > reach * 0.8) env.move(e, nx * e.def.speed * env.HS / 1.5 * dt, nz * e.def.speed * env.HS / 1.5 * dt);
        if (d <= reach && e.atkCd <= 0) { this.set(e, 'telegraph'); }
        break;
      case 'telegraph': if (e.tStateT >= e.def.tele) { this.set(e, 'attack'); return 'attack'; } break;
      case 'attack': if (e.tStateT >= 0.18) { e.atkCd = e.def.atkMs / 1000; this.set(e, 'recover'); } break;
      case 'recover': if (e.tStateT >= 0.45) this.set(e, 'chase'); break;
      case 'stagger': if (e.tStateT >= e.staggerFor) this.set(e, 'chase'); break;
    }
    return null;
  }
  set(e, s) { e.state = s; e.tStateT = 0; }
  stagger(e, secs) { if (e.state === 'defeated') return false; if (e.def.poise && Math.random() < e.def.poise) return false; e.staggerFor = secs || e.def.stagger; this.set(e, 'stagger'); return true; }
}
