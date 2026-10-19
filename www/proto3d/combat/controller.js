/* CombatController: owns all combat state and rules. No THREE, no DOM. Reads only player position/facing (setPlayer) - never the camera.
   Talks to the outside through events: on(type, fn). The HUD listens; the host (fight.js) turns events into visuals/movement. */
import { PLAYER, ABILITIES, ENEMIES, TUNING } from './data.js';
import { DamageCalculator } from './calc.js';
import { CooldownManager, ResourceManager, TargetingSystem } from './systems.js';
import { EnemyAIController } from './ai.js';
export class CombatController {
  constructor(o = {}) {
    this.rng = o.rng || Math.random; this.HS = o.HS || 1.5; this.P = Object.assign({}, PLAYER, o.player || {});
    this.cd = new CooldownManager(); this.res = new ResourceManager(this.P); this.tgt = new TargetingSystem(this.P); this.ai = new EnemyAIController();
    this.enemies = []; this.ls = {}; this.p = { x: 0, z: 0, yaw: 0, dead: false };
    this.hero = { id: '', name: 'Hero', level: 40, className: 'Adventurer', saber: false };
    this.act = null; this.blocking = false; this.blockT = 0; this.iframes = 0; this.shield = 0; this.potions = this.P.potion.charges; this.dead = 0;
    this.xp = 0; this.gold = 0; this.kills = 0; this.lastTarget = null; this.lastHitT = -99; this.god = false; this.nextId = 1;
    this.env = { HS: this.HS, move: o.move || ((e, dx, dz) => { e.x += dx; e.z += dz; }) };
  }
  on(t, f) { (this.ls[t] || (this.ls[t] = [])).push(f); return this; }
  emit(t, a) { const l = this.ls[t]; if (l) for (let i = 0; i < l.length; i++) l[i](a); }
  setHero(h) { Object.assign(this.hero, h); this.hero.owner = /(^|:)owner/.test(this.hero.id || '');  /* Owner gate: only the Owner has 999,999 max HP */ const mx = this.hero.owner ? this.P.ownerHp : this.P.hp; if (this.res.max.hp !== mx) { this.res.max.hp = mx; this.res.hp = mx; } this.emit('hero', this.hero); }
  setPlayer(x, z, yaw) { this.p.x = x; this.p.z = z; this.p.yaw = yaw; }   // the only world inputs
  slotUsable(i) { const a = ABILITIES[i]; return !a.saber || this.hero.saber; }
  weapon() { return this.hero.saber ? 'saber' : 'unarmed'; }
  addEnemy(key, x, z, extra) {
    const def = ENEMIES[key]; const e = Object.assign({ id: this.nextId++, key, def, x, z, yaw: 0, hp: def.hp, max: def.hp, state: 'idle', tStateT: 0, atkCd: 0.8 + this.rng(), flash: 0, knockT: 0, kx: 0, kz: 0, staggerFor: 0, rewarded: false, deadT: 0 }, extra);
    this.enemies.push(e); this.emit('spawn', e); return e;
  }
  removeEnemy(e) { const i = this.enemies.indexOf(e); if (i >= 0) this.enemies.splice(i, 1); if (this.tgt.target === e) { this.tgt.target = null; this.tgt.locked = false; } if (this.lastTarget === e) this.lastTarget = null; this.emit('remove', e); }
  clearEnemies() { for (const e of this.enemies.slice()) this.removeEnemy(e); }
  alive() { let n = 0; for (const e of this.enemies) if (e.state !== 'defeated') n++; return n; }
  /* ---- player inputs ---- */
  busy() { return this.dead > 0 || !!this.act; }
  use(i) {
    const a = ABILITIES[i]; if (!a || this.busy()) return false;
    if (!this.slotUsable(i)) { this.emit('denied', { slot: i, why: 'Owner only' }); return false; }
    if (!this.cd.ok(a.id)) return false;
    if (!this.res.can(a.cost)) { this.emit('denied', { slot: i, why: a.cost.mp && this.res.mp < a.cost.mp ? 'Not enough mana' : 'Not enough stamina' }); return false; }
    const nrm = !this.hero.owner, tn = TUNING.normal; let ab = a;
    if (nrm) ab = Object.assign({}, a, { cd: a.cd * (a.id === 'basic' ? tn.basicCdMul : 1), windup: a.windup * (a.id === 'basic' ? 1 : tn.windupMul), T: a.T * (a.id === 'basic' ? 0.8 : tn.windupMul), cost: a.id === 'basic' ? { sp: tn.basicSp } : a.cost });
    if (!this.res.can(ab.cost)) { this.emit('denied', { slot: i, why: 'Not enough stamina' }); return false; }
    this.res.spend(ab.cost); this.cd.start(a.id, ab.cd); this.act = { a: ab, slot: i, t: 0, done: false };
    const t = this.tgt.target || this.tgt.nearest(this.enemies, this.p.x, this.p.z, this.p.yaw, 8 * this.HS);
    this.emit('action', { slot: i, a: ab, T: ab.T, aim: t });
    return true;
  }
  dodge(dx, dz) {
    const D = this.P.dodge; if (this.dead > 0 || !this.cd.ok('dodge') || !this.res.spend({ sp: D.sp })) { if (this.dead <= 0 && this.cd.ok('dodge')) this.emit('denied', { why: 'Not enough stamina' }); return false; }
    this.cd.start('dodge', D.cd); this.iframes = D.iframes; this.act = null;
    let l = Math.hypot(dx || 0, dz || 0); if (l < 0.01) { dx = -Math.sin(this.p.yaw); dz = -Math.cos(this.p.yaw); l = 1; }   // no input: step back
    this.emit('dash', { dx: dx / l, dz: dz / l, dist: D.dist, T: 0.2 }); return true;
  }
  block(on) { if (on && (this.dead > 0 || this.res.sp < this.P.block.minSp)) on = false; if (on === this.blocking) return; this.blocking = on; this.blockT = 0; this.emit('block', on); }
  jump() { if (this.dead > 0 || !this.cd.ok('jump') || !this.res.spend({ sp: this.P.jump.sp })) return false; this.cd.start('jump', this.P.jump.dur + 0.1); this.emit('jump', this.P.jump); return true; }
  lock() { const t = this.tgt.lock(this.enemies, this.p.x, this.p.z, this.p.yaw); this.emit('lock', t); return t; }
  switchTarget() { const t = this.tgt.switchNext(this.enemies, this.p.x, this.p.z); this.emit('lock', t); return t; }
  potion() {
    if (this.dead > 0 || this.potions <= 0 || !this.cd.ok('potion') || this.res.hp >= this.res.max.hp) return false;
    this.potions--; this.cd.start('potion', this.P.potion.cd); const n = this.res.heal(Math.round(this.res.max.hp * this.P.potion.heal)); this.emit('heal', { n, x: this.p.x, z: this.p.z }); return true;
  }
  swap() { this.emit('swap', this.hero); }
  /* ---- damage out ---- */
  targetOf(e) { return e; }
  hitEnemy(e, mult, a) {
    if (e.state === 'defeated') return;
    const r = DamageCalculator.playerHit(this.weapon(), mult, this.rng); e.hp = Math.max(0, e.hp - r.dmg); e.flash = 0.2; this.lastTarget = e; this.lastHitT = this.cd.t;
    const dx = e.x - this.p.x, dz = e.z - this.p.z, d = Math.hypot(dx, dz) || 1; e.kx = dx / d; e.kz = dz / d; e.knockT = (a && a.knock ? 0.35 : 0.12);
    this.emit('damage', { e, dmg: r.dmg, crit: r.crit, toPlayer: false });
    if (e.hp <= 0) { this.defeat(e); return; }
    e.poiseDmg = (e.poiseDmg || 0) + r.dmg; const big = e.poiseDmg >= e.def.hp * TUNING.normal.staggerFrac && !this.hero.owner;
    if (big) { e.poiseDmg = 0; this.ai.stagger(e, e.def.stagger); }
    else if (a && a.stagger) this.ai.stagger(e, e.def.stagger);
    else if (e.state === 'idle') this.ai.set(e, 'chase');
  }
  defeat(e) {
    e.state = 'defeated'; e.tStateT = 0; if (this.tgt.target === e) { this.tgt.target = null; this.tgt.locked = false; }
    if (e.rewarded) return; e.rewarded = true; this.kills++; this.xp += e.def.xp; this.gold += e.def.gold;       // once per defeat
    this.emit('defeat', e); this.emit('reward', { xp: e.def.xp, gold: e.def.gold, totalXp: this.xp, totalGold: this.gold, e });
  }
  inCone(e, range, arc) {
    const dx = e.x - this.p.x, dz = e.z - this.p.z, d = Math.hypot(dx, dz); if (d > range + e.def.r) return false;
    return arc < -0.5 || d < 0.6 || (dx * Math.sin(this.p.yaw) + dz * Math.cos(this.p.yaw)) / d >= arc;
  }
  resolveAction(act) {
    const a = act.a, HS = this.HS;
    if (a.kind === 'shield') { this.shield = a.dur; this.emit('shield', a); return; }
    if (a.kind === 'ranged') { const t = this.tgt.target || this.tgt.nearest(this.enemies, this.p.x, this.p.z, this.p.yaw, a.range * HS); if (t && Math.hypot(t.x - this.p.x, t.z - this.p.z) <= a.range * HS + t.def.r) { this.emit('throw', { e: t }); this.hitEnemy(t, a.mult, a); } return; }
    if (a.kind === 'storm') { act.storm = 3; act.stormT = 0; this.stormHit(act); return; }
    for (const e of this.enemies.slice()) if (this.inCone(e, a.range * HS, a.arc)) this.hitEnemy(e, a.mult, a);
  }
  stormHit(act) { const a = act.a; for (const e of this.enemies.slice()) if (this.inCone(e, a.range * this.HS, -1)) this.hitEnemy(e, a.mult / 3, a); }
  /* ---- damage in ---- */
  enemyStrike(e) {
    const dx = this.p.x - e.x, dz = this.p.z - e.z, d = Math.hypot(dx, dz), reach = e.def.reach * this.HS + e.def.r;
    if (this.p.dead || this.dead > 0) return;
    if (d > reach * 1.25) { this.emit('enemyAttack', { e, result: 'missed', dmg: 0 }); return; }
    if (this.iframes > 0 || this.god) { this.emit('enemyAttack', { e, result: 'dodged', dmg: 0 }); this.emit('dodged', e); return; }
    if (this.blocking && this.blockT <= this.P.block.parry) { this.ai.stagger(e, 0.9); e.poiseBreak = true; this.emit('enemyAttack', { e, result: 'parried', dmg: 0 }); return; }
    let h = DamageCalculator.enemyHit(e.def.atk, this.P.def, this.P.agi, this.rng), res = 'hit';
    if (h === 0) res = 'dodged';
    if (this.blocking) { h = Math.round(h * (1 - this.P.block.reduce)); this.res.sp = Math.max(0, this.res.sp - Math.max(8, h * 0.02)); res = 'blocked'; if (this.res.sp <= 0) this.block(false); }
    if (this.shield > 0) h = Math.round(h * (1 - ABILITIES[4].reduce));
    this.res.hp = Math.max(0, this.res.hp - h);
    this.emit('enemyAttack', { e, result: res, dmg: h }); if (h > 0) this.emit('damage', { e, dmg: h, crit: false, toPlayer: true });
    if (this.res.hp <= 0) { this.dead = this.P.respawn; this.act = null; this.block(false); this.emit('playerDown'); }
  }
  respawn() { this.res.full(); this.dead = 0; this.potions = this.P.potion.charges; this.cd.reset(); this.iframes = 0; this.shield = 0; this.act = null; this.clearEnemies(); this.tgt.target = null; this.tgt.locked = false; this.emit('respawn'); }
  /* ---- frame ---- */
  update(dt) {
    this.cd.tick(dt); this.res.tick(dt, this.blocking);
    this.iframes = Math.max(0, this.iframes - dt); this.shield = Math.max(0, this.shield - dt);
    if (this.blocking) { this.blockT += dt; this.res.sp = Math.max(0, this.res.sp - this.P.block.drain * dt); if (this.res.sp <= 0) this.block(false); }
    if (this.dead > 0) { this.dead -= dt; if (this.dead <= 0) this.respawn(); }
    const act = this.act;
    if (act) {
      act.t += dt; if (!act.done && act.t >= act.a.windup) { act.done = true; this.resolveAction(act); }
      if (act.storm && act.t > act.a.windup + act.stormT + 0.22 && act.storm > 1) { act.stormT += 0.22; act.storm--; this.stormHit(act); }
      if (act.t >= act.a.T) this.act = null;
    }
    this.p.dead = this.dead > 0;
    for (const e of this.enemies) {
      if (e.state === 'defeated') { e.deadT += dt; continue; }
      if (this.ai.update(e, this.p, dt, this.env) === 'attack') this.enemyStrike(e);
    }
    this.tgt.update(this.enemies, this.p.x, this.p.z);
    if (!this.tgt.locked && this.lastTarget && (this.lastTarget.state === 'defeated' || this.cd.t - this.lastHitT > 6)) this.lastTarget = null;
  }
  /* what the target panel shows */
  shownTarget() { return this.tgt.target || this.lastTarget; }
}
