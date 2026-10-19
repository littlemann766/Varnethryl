/* Cooldown / Resource managers and the TargetingSystem. Pure logic (no THREE, no DOM). */
export class CooldownManager {
  constructor() { this.t = 0; this.ready = new Map(); this.dur = new Map(); }
  tick(dt) { this.t += dt; }
  start(key, d) { this.ready.set(key, this.t + d); this.dur.set(key, d); }
  left(key) { const r = this.ready.get(key); return r === undefined ? 0 : Math.max(0, r - this.t); }
  frac(key) { const d = this.dur.get(key); return d ? this.left(key) / d : 0; }
  ok(key) { return this.left(key) <= 0; }
  reset() { this.ready.clear(); }
}
export class ResourceManager {
  constructor(P) { this.P = P; this.hp = P.hp; this.mp = P.mp; this.sp = P.sp; this.max = { hp: P.hp, mp: P.mp, sp: P.sp }; this.spLock = 0; }
  can(cost) { return (!cost.mp || this.mp >= cost.mp) && (!cost.sp || this.sp >= cost.sp); }
  spend(cost) { if (!this.can(cost)) return false; if (cost.mp) this.mp -= cost.mp; if (cost.sp) { this.sp -= cost.sp; this.spLock = this.P.spDelay; } return true; }
  tick(dt, blocking) { if (this.spLock > 0) this.spLock -= dt; else if (!blocking) this.sp = Math.min(this.max.sp, this.sp + this.P.spRegen * dt); this.mp = Math.min(this.max.mp, this.mp + this.P.mpRegen * dt); }
  heal(n) { const b = this.hp; this.hp = Math.min(this.max.hp, this.hp + n); return this.hp - b; }
  full() { this.hp = this.max.hp; this.mp = this.max.mp; this.sp = this.max.sp; }
}
export class TargetingSystem {
  constructor(P) { this.P = P; this.target = null; this.locked = false; }
  live(list) { return list.filter(e => e.state !== 'defeated'); }
  nearest(list, x, z, yaw, range) {
    let best = null, bs = 1e9; const fx = Math.sin(yaw), fz = Math.cos(yaw);
    for (const e of list) { if (e.state === 'defeated') continue; const dx = e.x - x, dz = e.z - z, d = Math.hypot(dx, dz); if (d > range) continue; const front = d > 0.01 ? (dx * fx + dz * fz) / d : 1; const s = d * (1.4 - 0.4 * front); if (s < bs) { bs = s; best = e; } }
    return best;
  }
  lock(list, x, z, yaw) { if (this.locked) { this.locked = false; return null; } const t = this.nearest(list, x, z, yaw, this.P.lockRange); this.target = t; this.locked = !!t; return t; }
  switchNext(list, x, z) {
    const c = this.live(list).filter(e => Math.hypot(e.x - x, e.z - z) <= this.P.lockRange).sort((a, b) => Math.atan2(a.x - x, a.z - z) - Math.atan2(b.x - x, b.z - z));
    if (!c.length) return null; const i = c.indexOf(this.target); this.target = c[(i + 1) % c.length]; this.locked = true; return this.target;
  }
  update(list, x, z) { const t = this.target; if (t && (t.state === 'defeated' || Math.hypot(t.x - x, t.z - z) > this.P.lockBreak)) { this.target = null; this.locked = false; } }
}
