/* CombatController: owns all combat state and rules. No THREE, no DOM. Reads only player position/facing (setPlayer) - never the camera.
   Talks to the outside through events: on(type, fn). The HUD listens; the host (fight.js) turns events into visuals/movement. */
import { PLAYER, ABILITIES, ENEMIES, TUNING, OWNER_SKILLS, ULTIMATE2 } from './data.js';
import { kitFor, kitSkill } from './herokits.js';
import { DamageCalculator } from './calc.js';
import { CooldownManager, ResourceManager, TargetingSystem } from './systems.js';
import { EnemyAIController } from './ai.js';
export class CombatController {
  constructor(o = {}) {
    this.rng = o.rng || Math.random; this.HS = o.HS || 1.5; this.P = Object.assign({}, PLAYER, o.player || {});
    this.cd = new CooldownManager(); this.noCooldown = false; this.cd.off = () => this.noCooldown && this.perkHero(); this.res = new ResourceManager(this.P); this.tgt = new TargetingSystem(this.P); this.ai = new EnemyAIController();
    this.enemies = []; this.ls = {}; this.p = { x: 0, z: 0, yaw: 0, dead: false };
    this.hero = { id: '', name: 'Hero', level: 40, className: 'Adventurer', saber: false };
    this.act = null; this.blocking = false; this.blockT = 0; this.iframes = 0; this.shield = 0; this.potions = this.P.potion.charges; this.dead = 0;
    this.xp = 0; this.gold = 0; this.kills = 0; this.lastTarget = null; this.lastHitT = -99; this.god = false; this.nextId = 1; this.fury = 0; this.kit = null; this._mk = ''; this.ownerUnlocked = false; this.meteors = []; this.bamboo = false; this.buffs = []; this.summons = []; this.sid = 1; this.RM = 1; this.ultSel = (() => { try { const v = typeof localStorage !== 'undefined' && localStorage.getItem('varn.ultsel'); return v === 'unholy' ? 'unholy' : 'holy'; } catch (e) { return 'holy'; } })(); this.bystanders = null;
    this.env = { HS: this.HS, move: o.move || ((e, dx, dz) => { e.x += dx; e.z += dz; }) };
  }
  on(t, f) { (this.ls[t] || (this.ls[t] = [])).push(f); return this; }
  emit(t, a) { const l = this.ls[t]; if (l) for (let i = 0; i < l.length; i++) l[i](a); }
  setHero(h) { Object.assign(this.hero, h); this.hero.owner = /(^|:)owner/.test(this.hero.id || ''); this.kit = this.gearKit(kitFor(this.hero.id));  /* Owner gate: only the Owner has 999,999 max HP */ this.applyMax(true); this.emit('hero', this.hero); }
  /* max HP/MP/SP: Owner skin = ownerHp; non-Owner hero holding the Owner saber on the owner account = x TUNING.perks.holderMul (not invincible); everyone else normal. Current values keep their fraction; reverts when the saber goes away. */
  /* Armory bonuses (armory.js bonuses(): percent fractions) override the kit's weapon/armor numbers on a COPY of the shared kit; null/Owner => untouched */
  setGear(b) { this.gear = b && !b.owner ? b : null; this.kit = this.gearKit(kitFor(this.hero.id)); this.applyMax(true); }
  gearKit(k) { const g = this.gear; if (!k || !g || !k.weapon || !k.armor) return k; return Object.assign({}, k, { weapon: Object.assign({}, k.weapon, { dmgPct: g.dmgPct }), armor: Object.assign({}, k.armor, { hpPct: g.hpPct, mpPct: g.mpPct, spPct: g.spPct, defPct: g.defPct }) }); }
  applyMax(force) {
    const own = !!this.hero.owner, hold = !own && this.ownerOk(), m = hold ? TUNING.perks.holderMul : 1, ar = (!own && this.kit && this.kit.armor) || null, key = (own ? 'o' : '') + m + (ar ? ar.name + ar.hpPct + ar.mpPct + ar.spPct : ''); if (!force && key === this._mk) return; this._mk = key;
    const nx = { hp: own ? this.P.ownerHp : Math.round(this.P.hp * m * (1 + (ar ? ar.hpPct : 0))), mp: Math.round(this.P.mp * m * (1 + (ar ? ar.mpPct : 0))), sp: Math.round(this.P.sp * m * (1 + (ar ? ar.spPct : 0))) }, R = this.res;
    for (const k of ['hp', 'mp', 'sp']) { if (R.max[k] === nx[k]) continue; R[k] = own && k === 'hp' ? nx[k] : Math.min(nx[k], Math.max(0, R[k] * nx[k] / R.max[k])); R.max[k] = nx[k]; }
  }
  /* real-size play: charscale.js profile (reach = melee/AoE range multiplier); pure data in, no THREE */
  setScale(p) { this.RM = Math.max(0.5, Math.min(8, +(p && p.reach) || 1)); this.env.RM = this.RM; this.scale = p || null; }
  setPlayer(x, z, yaw) { this.p.x = x; this.p.z = z; this.p.yaw = yaw; }   // the only world inputs
  /* Owner gate: Owner skin AND the host-confirmed owner unlock (fight.js sets ownerUnlocked from the owner gate; the HUD can never set it). */
  ownerOk() { return !!(this.ownerUnlocked && (this.hero.owner || this.hero.saber)); }   // owner account AND (Owner skin OR active hero wields the Owner saber)
  perkHero() { return !!(this.hero.owner || (TUNING.perks.saberHolderResources && this.ownerOk())); }   // unlimited MP/SP + no-cooldowns recipient
  skillDef(i) { return typeof i === 'string' ? (OWNER_SKILLS[i] || kitSkill(this.kit, i)) : ABILITIES[i]; }
  slotUsable(i) { const a = this.skillDef(i); if (!a) return false; if (a.owner && !this.ownerOk()) return false; return a.owner || !a.saber || !!this.hero.saber; }
  furyOn() { return this.ownerOk() || !!this.kit; }
  furyReady() { return this.res.unlimited || this.fury >= TUNING.ult.fury; }
  /* Bamboo Stick (test weapon): owner account only; while held it replaces the saber, so owner skills use the non-saber 99,999 x skillMul rule. */
  bambooOn() { return !!(this.bamboo && this.ownerUnlocked); }
  weapon() { return this.bambooOn() ? 'bamboo' : (this.hero.saber ? 'saber' : 'unarmed'); }
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
    const a = this.skillDef(i); if (!a || this.busy()) return false;
    if (a.owner && !this.ownerOk()) { this.emit('denied', { slot: i, why: 'Owner only' }); return false; }
    if (!this.slotUsable(i)) { this.emit('denied', { slot: i, why: a.owner ? 'Draw the saber' : 'Owner only' }); return false; }
    if (!this.cd.ok(a.id)) return false;
    if (a.fury && !this.furyReady()) { this.emit('denied', { slot: i, why: 'Fury not full' }); return false; }
    if (!this.res.can(a.cost)) { this.emit('denied', { slot: i, why: a.cost.mp && this.res.mp < a.cost.mp ? 'Not enough mana' : 'Not enough stamina' }); return false; }
    const nrm = !(this.hero.owner || this.ownerOk()), tn = TUNING.normal; let ab = a;
    if (nrm) ab = Object.assign({}, a, { cd: a.cd * (a.id === 'basic' ? tn.basicCdMul : 1), windup: a.windup * (a.id === 'basic' ? 1 : tn.windupMul), T: a.T * (a.id === 'basic' ? 0.8 : tn.windupMul), cost: a.id === 'basic' ? { sp: tn.basicSp } : a.cost });
    if (!this.res.can(ab.cost)) { this.emit('denied', { slot: i, why: 'Not enough stamina' }); return false; }
    this.res.spend(ab.cost); this.cd.start(a.id, ab.cd); this.act = { a: ab, slot: i, t: 0, done: false };
    if (a.fury && !this.res.unlimited) this.fury = 0;
    if (a.kind === 'meteor') { const U = a.kit ? { delay: a.delay, radius: a.radius } : TUNING.ult, tg = a.kit ? (this.tgt.target || this.tgt.nearest(this.enemies, this.p.x, this.p.z, this.p.yaw, 14 * this.HS)) : null, mx = tg ? tg.x : this.p.x, mz = tg ? tg.z : this.p.z; this.meteors.push({ t: U.delay, x: mx, z: mz, r: U.radius, kit: !!a.kit, mult: a.mult, mode: a.mode || 'hostile', name: a.name }); this.emit('meteorCast', { x: mx, z: mz, radius: U.radius, delay: U.delay, mode: a.mode || 'hostile', name: a.name }); }
    const t = this.tgt.target || this.tgt.nearest(this.enemies, this.p.x, this.p.z, this.p.yaw, 8 * this.HS);
    this.emit('action', { slot: i, a: ab, T: ab.T, aim: t });
    return true;
  }
  /* Unholy Destruction impact. Eligible = hostile, living, non-boss monsters inside the radius (friendlies/protected/props are never in cc.enemies and are skipped if flagged).
     Each gets the normal death handler (defeat) exactly once. Bosses take the normal owner saber hit unless TUNING.ult.bossesInstantKill. The Owner/party are never touched. */
  meteorImpact(m) {
    const U = TUNING.ult, hit = [], all = m.mode === 'all';   // 'all' (Unholy): everything in range except the Owner. 'hostile' (Holy): hostile monsters + hostile characters only.
    const um = Math.max(1, Math.min(100, Math.floor(+U.dmgMul || 1)));
    if (m.kit) { for (const e of this.enemies.slice()) if (e.state !== 'defeated' && Math.hypot(e.x - m.x, e.z - m.z) <= m.r + e.def.r) { this.hitEnemy(e, m.mult, { stagger: 1 }); hit.push({ e, kill: e.state === 'defeated' }); } this.emit('meteorImpact', { x: m.x, z: m.z, radius: m.r, hits: hit, name: m.name, kit: true }); return; }
    for (const e of this.enemies.slice()) {
      if (e.state === 'defeated' || e.owner || e.prop) continue;
      if (!all && (e.friendly || e.protected || e.npc || e.party || e.ally || e.hostile === false)) continue;
      if (Math.hypot(e.x - m.x, e.z - m.z) > m.r) continue;
      if (e.def.boss && !U.bossesInstantKill) { this.hitEnemy(e, 1, { stagger: 0, ult: true }); hit.push({ e, kill: false }); continue; }
      const dmg = Math.max(1, Math.ceil(e.hp)) * um; e.hp = 0; this.emit('damage', { e, dmg, crit: false, toPlayer: false }); this.defeat(e); hit.push({ e, kill: true });
    }
    if (all && typeof this.bystanders === 'function') for (const b of this.bystanders() || []) {   // party members / NPCs / friendly characters held by the host (never the Owner)
      if (!b || b.owner || b.isOwner || Math.hypot(b.x - m.x, b.z - m.z) > m.r) continue;
      const dmg = Math.max(1, Math.ceil(b.hp || 1)) * um; this.emit('bystanderKill', { b, dmg }); hit.push({ e: b, kill: true, bystander: true });
    }
    this.emit('meteorImpact', { x: m.x, z: m.z, radius: m.r, hits: hit, mode: m.mode, name: m.name });
  }
  /* Owner second ultimate: same gating as use() (cooldown, mana, busy), Owner/saber only */
  useUltimate2() {
    const a = ULTIMATE2; if (this.busy()) return false;
    if (!this.hero.saber || !this.ownerOk()) { this.emit('denied', { slot: 6, why: 'Owner only' }); return false; }
    if (!this.cd.ok(a.id)) return false;
    if (!this.res.can(a.cost)) { this.emit('denied', { slot: 6, why: 'Not enough mana' }); return false; }
    this.res.spend(a.cost); this.cd.start(a.id, a.cd); this.act = { a, slot: 6, t: 0, done: false };
    const t = this.tgt.target || this.tgt.nearest(this.enemies, this.p.x, this.p.z, this.p.yaw, a.range * this.HS * this.RM);
    this.emit('action', { slot: 6, a, T: a.T, aim: t }); return true;
  }
  chainStrike(a) {
    /* Thunderstorm kills EVERYTHING in range (no target cap, bosses included): every living enemy takes the full hit via hitEnemy/DamageCalculator.
       The chain is only for visuals: greedy nearest-neighbour order from the player; the host draws the first ~12 as bolts and the rest as cheap impact flashes. */
    const HS = this.HS, R = a.range * HS * this.RM, all = this.enemies.filter(e => e.state !== 'defeated' && !e.owner && !e.prop && Math.hypot(e.x - this.p.x, e.z - this.p.z) <= R + (e.def.r || 0));   // every model except the Owner (enemies, bosses, enemy characters, flagged friendlies/NPCs in cc.enemies)
    const um = Math.max(1, Math.min(100, Math.floor(+TUNING.ult.dmgMul || 1))), bys = [];
    if (typeof this.bystanders === 'function') for (const b of this.bystanders() || []) {   // host-held models: party/companions/followers/NPCs/townsfolk (never the Owner)
      if (!b || b.owner || b.isOwner || Math.hypot(b.x - this.p.x, b.z - this.p.z) > R) continue;
      this.emit('bystanderKill', { b, dmg: Math.max(1, Math.ceil(b.hp || 1)) * um }); bys.push(b);
    }
    if (!all.length && !bys.length) return; const order = []; let cx = this.p.x, cz = this.p.z, left = all.slice();
    while (left.length) { let bi = 0, bd = 1e18; for (let i = 0; i < left.length; i++) { const d = (left[i].x - cx) ** 2 + (left[i].z - cz) ** 2; if (d < bd) { bd = d; bi = i; } } const e = left.splice(bi, 1)[0]; order.push(e); cx = e.x; cz = e.z; }
    const path = []; let f = 1;
    order.forEach((e, i) => { path.push({ x: e.x, z: e.z, y: 1.1 * HS * Math.max(1, (e.def.scale || 1) * 0.8), falloff: f, flash: i >= (a.visualBolts || 12) }); f = Math.max(0.45, f * a.falloff); });
    for (const e of order) this.hitEnemy(e, a.mult, a);
    for (const b of bys) path.push({ x: b.x, z: b.z, y: 1.1 * HS, falloff: 0.5, flash: true });
    this.emit('lightning', { from: { x: this.p.x, z: this.p.z }, path, count: order.length + bys.length });
  }
  dodge(dx, dz) {
    const D = this.P.dodge; if (this.dead > 0 || !this.cd.ok('dodge') || !this.res.spend({ sp: D.sp })) { if (this.dead <= 0 && this.cd.ok('dodge')) this.emit('denied', { why: 'Not enough stamina' }); return false; }
    this.cd.start('dodge', D.cd); this.iframes = D.iframes; this.act = null;
    let l = Math.hypot(dx || 0, dz || 0); if (l < 0.01) { dx = -Math.sin(this.p.yaw); dz = -Math.cos(this.p.yaw); l = 1; }   // no input: step back
    this.emit('dash', { dx: dx / l, dz: dz / l, dist: D.dist, T: 0.2 }); return true;
  }
  block(on) { if (on && (this.dead > 0 || (!this.res.unlimited && this.res.sp < this.P.block.minSp))) on = false; if (on === this.blocking) return; this.blocking = on; this.blockT = 0; this.emit('block', on); }
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
    /* Thunderstorm (ULTIMATE2.lethal): kills regular enemies; bosses (Ashen Titan...) only die to it if TUNING.ult.bossesInstantKill (default false) - otherwise a normal hit. */
    const wp = (!this.ownerOk() && this.kit && this.kit.weapon) ? 1 + this.kit.weapon.dmgPct : 1;   // signature weapon bonus (kit heroes only, never Owner rules)
    const lethal = !!(a && a.lethal && (!e.def.boss || TUNING.ult.bossesInstantKill));
    const r = lethal ? { dmg: Math.max(1, Math.ceil(e.hp)), crit: true } : DamageCalculator.playerHit(this.weapon(), mult, this.rng);
    /* Owner saber: regular hostile monsters take current HP x12 per hit (always lethal). Bosses keep flat 99,999 unless TUNING.perks.saberBossesX12. Owner gate enforced here, never from the UI. */
    /* Owner skills (Royal/Chains/Wrath) = 99,999 x skillMul with ANY weapon except the lightsaber; while the saber is held the saber rule (x current HP) applies. */
    const skm = a && a.id && TUNING.skillMul && TUNING.skillMul[a.id];
    if (lethal) { /* already lethal */ }
    else if (skm > 0 && this.weapon() !== 'saber' && this.ownerOk()) r.dmg = Math.round(99999 * skm);
    else if (TUNING.ownerWeaponBase > 0 && this.weapon() !== 'saber' && this.ownerOk()) r.dmg = Math.round(TUNING.ownerWeaponBase);
    else {
    const sm = Math.max(0, Math.min(50, Math.floor(+TUNING.perks.saberMul || 0)));   // 0 = flat 99,999 (old behavior); 1-50 = x target current HP
    if (sm > 0 && this.weapon() === 'saber' && this.ownerOk() && e.hp > 0 && (!e.def.boss || TUNING.perks.saberBossesX12)) r.dmg = Math.max(1, Math.round(e.hp)) * sm; }
    if (wp !== 1 && !lethal) r.dmg = Math.round(r.dmg * wp);
    { const bd = !this.ownerOk() && !lethal ? this.buffSum('dmg') : 0; if (bd > 0) r.dmg = Math.round(r.dmg * (1 + bd)); }   // party buffs never touch Owner rules
    e.hp = Math.max(0, e.hp - r.dmg); e.flash = 0.2; this.lastTarget = e; this.lastHitT = this.cd.t;
    const dx = e.x - this.p.x, dz = e.z - this.p.z, d = Math.hypot(dx, dz) || 1; e.kx = dx / d; e.kz = dz / d; e.knockT = (a && a.knock ? 0.35 : 0.12);
    this.emit('damage', { e, dmg: r.dmg, crit: r.crit, toPlayer: false });
    if (this.furyOn() && !(a && a.ult)) this.fury = Math.min(TUNING.ult.fury, this.fury + (a && a.id !== 'basic' ? TUNING.ult.furyPerSkill : TUNING.ult.furyPerBasic));
    if (e.hp <= 0) { this.defeat(e); return; }
    e.poiseDmg = (e.poiseDmg || 0) + r.dmg; const big = e.poiseDmg >= e.def.hp * TUNING.normal.staggerFrac && !(this.hero.owner || this.ownerOk());
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
    if (a.kind === 'meteor') return;
    if (a.heal) { const n = this.res.heal(Math.round(this.res.max.hp * a.heal)); this.emit('heal', { n, x: this.p.x, z: this.p.z }); if (a.kind === 'heal') return; }
    if (a.shield) { this.shield = a.shield; this.emit('shield', a); }
    if (a.kind === 'dash') { const fx = Math.sin(this.p.yaw), fz = Math.cos(this.p.yaw); this.emit('dash', { dx: fx, dz: fz, dist: a.dist, T: 0.25 }); for (const e of this.enemies.slice()) { const dx = e.x - this.p.x, dz = e.z - this.p.z, d = Math.hypot(dx, dz), al = dx * fx + dz * fz; if (al > -1 && al < a.dist + e.def.r && Math.abs(dx * fz - dz * fx) < 2.2 + e.def.r) this.hitEnemy(e, a.mult, a); } return; }
    if (a.kind === 'line') { const fx = Math.sin(this.p.yaw), fz = Math.cos(this.p.yaw); for (const e of this.enemies.slice()) { const dx = e.x - this.p.x, dz = e.z - this.p.z, al = dx * fx + dz * fz; if (al > 0 && al < a.range + e.def.r && Math.abs(dx * fz - dz * fx) < 1.4 + e.def.r) this.hitEnemy(e, a.mult, a); } return; }
    if (a.kind === 'blink') { const t = this.tgt.target || this.tgt.nearest(this.enemies, this.p.x, this.p.z, this.p.yaw, a.range); if (t) { const dx = t.x - this.p.x, dz = t.z - this.p.z, d = Math.hypot(dx, dz) || 1, bx = t.x + dx / d * (t.def.r + 1.2), bz = t.z + dz / d * (t.def.r + 1.2); this.emit('blink', { x: bx, z: bz, yaw: Math.atan2(-dx, -dz) + Math.PI }); this.p.x = bx; this.p.z = bz; this.hitEnemy(t, a.mult, a); } return; }   // lands later via this.meteors
    if (a.kind === 'shield') { this.shield = a.dur; this.emit('shield', a); return; }
    if (a.kind === 'buff') { this.addBuff(a.buff, a); return; }
    if (a.kind === 'summon') { this.addSummon(a.summon, a); return; }
    if (a.kind === 'ranged') { const t = this.tgt.target || this.tgt.nearest(this.enemies, this.p.x, this.p.z, this.p.yaw, a.range * HS * this.RM); if (t && Math.hypot(t.x - this.p.x, t.z - this.p.z) <= a.range * HS * this.RM + t.def.r) { this.emit('throw', { e: t }); this.hitEnemy(t, a.mult, a); } return; }
    if (a.kind === 'chain') { this.chainStrike(a); return; }
    if (a.kind === 'storm') { act.storm = 3; act.stormT = 0; this.stormHit(act); return; }
    for (const e of this.enemies.slice()) if (this.inCone(e, a.range * HS * this.RM, a.arc)) this.hitEnemy(e, a.mult, a);
  }
  stormHit(act) { const a = act.a; for (const e of this.enemies.slice()) if (this.inCone(e, a.range * this.HS * this.RM, -1)) this.hitEnemy(e, a.mult / 3, a); }
  /* ---- damage in ---- */
  enemyStrike(e) {
    const dx = this.p.x - e.x, dz = this.p.z - e.z, d = Math.hypot(dx, dz), pt = e.def.boss ? e.pat : null, reach = (pt ? pt.reach : e.def.reach) * this.HS + e.def.r;
    if (this.p.dead || this.dead > 0) { e.pat = null; return; }
    /* boss patterns: ring = within reach; cone = within reach and inside the facing arc; line = down the facing axis, inside the width. Facing is frozen during the telegraph, so it can be side-stepped. */
    let inside = d <= reach * 1.25;
    if (pt) { const fx = Math.sin(e.yaw), fz = Math.cos(e.yaw), al = dx * fx + dz * fz, pp = Math.abs(dx * fz - dz * fx);
      inside = pt.shape === 'cone' ? (d <= reach * 1.1 && (d < 1 || al / d >= pt.cos)) : pt.shape === 'line' ? (al >= -1 && al <= reach && pp <= pt.width * this.HS / 2 + 0.6) : d <= reach * 1.1; }
    if (pt) { e.pat = null; this.emit('bossAttack', { e, pat: pt, hit: inside }); }
    if (!inside) { this.emit('enemyAttack', { e, result: 'missed', dmg: 0 }); return; }
    if (this.iframes > 0 || this.god) { this.emit('enemyAttack', { e, result: 'dodged', dmg: 0 }); this.emit('dodged', e); return; }
    if (this.blocking && this.blockT <= this.P.block.parry) { this.ai.stagger(e, 0.9); e.poiseBreak = true; this.emit('enemyAttack', { e, result: 'parried', dmg: 0 }); return; }
    let h = DamageCalculator.enemyHit(e.def.atk, this.P.def * (1 + ((!this.hero.owner && this.kit && this.kit.armor) ? this.kit.armor.defPct : 0)), this.P.agi, this.rng), res = 'hit'; if (pt && pt.dmg) h = Math.round(h * pt.dmg);
    if (h === 0) res = 'dodged';
    if (this.blocking) { h = Math.round(h * (1 - this.P.block.reduce)); if (!this.res.unlimited) this.res.sp = Math.max(0, this.res.sp - Math.max(8, h * 0.02)); res = 'blocked'; if (this.res.sp <= 0) this.block(false); }
    if (this.shield > 0) h = Math.round(h * (1 - ABILITIES[4].reduce));
    { const br = Math.min(0.6, this.buffSum('reduce')); if (br > 0) h = Math.round(h * (1 - br)); }
    this.res.hp = Math.max(0, this.res.hp - h);
    this.emit('enemyAttack', { e, result: res, dmg: h }); if (h > 0) this.emit('damage', { e, dmg: h, crit: false, toPlayer: true });
    if (this.res.hp <= 0) { this.dead = this.P.respawn; this.act = null; this.block(false); this.emit('playerDown'); }
  }
  respawn() { for (const s of this.summons.slice()) this.removeSummon(s, 'respawn'); this.buffs.length = 0; this.res.full(); this.dead = 0; this.potions = this.P.potion.charges; this.cd.reset(); this.iframes = 0; this.shield = 0; this.act = null; this.meteors.length = 0; this.clearEnemies(); this.tgt.target = null; this.tgt.locked = false; this.emit('respawn'); }
  /* ---- frame ---- */
  /* ---- real party buffs + summons (kit skills). Buffs: dmg (+fraction, non-Owner normal damage), reduce (damage taken), cdRate (extra cooldown speed), summonRate (summon attack speed); party:true also emits for the host's followers (visual aura). Re-cast refreshes. ---- */
  addBuff(b, a) { const o = this.buffs.find(x => x.id === b.id); if (o) o.t = b.dur; else this.buffs.push(Object.assign({ t: b.dur }, b)); this.emit('buff', { id: b.id, dur: b.dur, party: !!b.party, name: a && a.name }); }
  buffSum(k) { let v = 0; for (const b of this.buffs) v += b[k] || 0; for (const s of this.summons) if (s.id === 'totem' && Math.hypot(s.x - this.p.x, s.z - this.p.z) <= s.radius * this.HS) v += k === 'reduce' ? s.reduce : k === 'haste' ? s.haste : 0; return v; }
  /* Summons are simple controller entities (no AI tree): thrall chases + melees the nearest enemy, turret shoots in range, totem is an aura (slow enemies, protect/haste the player inside). One of each id at a time (re-cast replaces). */
  addSummon(sm, a) {
    for (const o of this.summons.filter(x => x.id === sm.id)) this.removeSummon(o, 'replaced');
    const HS = this.HS, fx = Math.sin(this.p.yaw), fz = Math.cos(this.p.yaw), off = sm.id === 'totem' ? 0 : 2.2 * HS;
    const s = Object.assign({ uid: this.sid++, t: sm.dur, cd: 0.3, x: this.p.x + fx * off, z: this.p.z + fz * off, hpMax: Math.round(this.res.max.hp * (sm.hp || 0)) }, sm); s.hp = s.hpMax;
    this.summons.push(s); this.emit('summon', s); return s;
  }
  removeSummon(s, why) { const i = this.summons.indexOf(s); if (i >= 0) { this.summons.splice(i, 1); this.emit('summonEnd', { s, why }); } }
  summonHit(s, e) { const r = DamageCalculator.playerHit('unarmed', s.mult, this.rng); r.dmg = Math.max(1, Math.round(r.dmg * (1 + this.buffSum('dmg')))); e.hp = Math.max(0, e.hp - r.dmg); e.flash = 0.12; this.emit('damage', { e, dmg: r.dmg, crit: r.crit, toPlayer: false, summon: s.id }); if (e.state === 'idle') this.ai.set(e, 'chase'); if (e.hp <= 0) this.defeat(e); }
  tickSummons(dt) {
    const HS = this.HS, rate = 1 + this.buffSum('summonRate');
    for (const s of this.summons.slice()) {
      s.t -= dt; if (s.t <= 0 || (s.hpMax && s.hp <= 0)) { this.removeSummon(s, s.t <= 0 ? 'expired' : 'killed'); continue; }
      const live = this.enemies.filter(e => e.state !== 'defeated');
      if (s.id === 'totem') { for (const e of live) e.slowT = Math.hypot(e.x - s.x, e.z - s.z) <= s.radius * HS ? s.slow : 0; continue; }
      let best = null, bd = 1e9; const lim = (s.id === 'turret' ? s.range : s.aggro) * HS; for (const e of live) { const d = Math.hypot(e.x - s.x, e.z - s.z) - (e.def.r || 0); if (d < bd && d <= lim) { bd = d; best = e; } }
      if (s.id === 'thrall') {   // follow the player when idle
        const tx = best ? best.x : this.p.x, tz = best ? best.z : this.p.z, d = Math.hypot(tx - s.x, tz - s.z), stop = best ? (best.def.r || 0) + s.range * HS * 0.6 : 2.5 * HS;
        if (d > stop) { const k = Math.min(1, (s.speed * HS * dt) / d); s.x += (tx - s.x) * k; s.z += (tz - s.z) * k; } s.yaw = Math.atan2(tx - s.x, tz - s.z);
      }
      s.cd -= dt * rate; if (best && s.cd <= 0 && bd <= (s.id === 'turret' ? s.range : s.range) * HS + 0.01) { s.cd = s.every; this.emit('summonAttack', { s, e: best }); this.summonHit(s, best); }
    }
    for (const b of this.buffs.slice()) { b.t -= dt; if (b.t <= 0) { this.buffs.splice(this.buffs.indexOf(b), 1); this.emit('buffEnd', { id: b.id }); } }
  }
  update(dt) {
    this.applyMax(false); this.cd.tick(dt * (1 + this.buffSum('cdRate') + this.buffSum('haste'))); this.tickSummons(dt); this.res.tick(dt, this.blocking);
    if (this.res.unlimited && this.furyOn()) this.fury = TUNING.ult.fury;
    if (this.meteors.length) for (const m of this.meteors.slice()) { m.t -= dt; if (m.t <= 0) { this.meteors.splice(this.meteors.indexOf(m), 1); if (this.dead <= 0) this.meteorImpact(m); } }
    this.iframes = Math.max(0, this.iframes - dt); this.shield = Math.max(0, this.shield - dt);
    if (this.blocking) { this.blockT += dt; if (!this.res.unlimited) this.res.sp = Math.max(0, this.res.sp - this.P.block.drain * dt); if (this.res.sp <= 0) this.block(false); }
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
      if (e.def.boss && e.phase !== 2 && e.state !== 'defeated' && e.hp / e.max < TUNING.boss.enrageAt) { e.phase = 2; e.pat = null; this.emit('bossPhase', { e, phase: 2 }); }
      if (this.ai.update(e, this.p, dt, this.env) === 'attack') this.enemyStrike(e);
    }
    this.tgt.update(this.enemies, this.p.x, this.p.z);
    if (!this.tgt.locked && this.lastTarget && (this.lastTarget.state === 'defeated' || this.cd.t - this.lastHitT > 6)) this.lastTarget = null;
  }
  /* what the target panel shows */
  shownTarget() { return this.tgt.target || this.lastTarget; }
}
