/* Combat data (Phase 1). Enemy stats mirror www/data.js ENEMIES (hp / atk) and the 2D game's cadence (attack every 1750 ms, boss 2300 ms). No logic here. */
/* ---- ONE place for combat feel. Normal characters: ~8-15 s per normal enemy (wolf/raider), elites longer, bosses much longer. Owner is exempt. ---- */
export const TUNING = {
  normal: { dmg: [28, 48], basicCdMul: 0.6, windupMul: 1.5, basicSp: 3, hp: 700, staggerFrac: 0.2 },   // dmg per basic hit, cooldown/wind-up multipliers, stamina per swing, max HP, enemy staggers after this fraction of its HP in damage
  owner: { hp: 999999, saber: 99999 },
  /* Unholy Destruction (Owner ultimate). ONE config block: bossesInstantKill=false => bosses (Ashen Titan...) take the normal owner saber hit instead of dying. */
  perks: { saberBossesX12: false, saberMul: 12, saberHolderResources: false, holderMul: 3 },   // holderMul: max HP/MP/SP multiplier for a non-Owner hero holding the Owner saber (owner account only)   // false: unlimited MP/SP + no cooldowns only for the Owner skin; true: any hero holding the Owner saber gets them too
  skillMul: { royal: 3, chains: 6, wrath: 12 },   // OWNER SKILL DAMAGE = flat 99,999 x this (300% / 600% / 1200%); owner gate enforced in the controller
  ult: { dmgMul: 50, radius: 25, delay: 1.5, cooldown: 35, fury: 100, bossesInstantKill: false, furyPerBasic: 8, furyPerSkill: 5 },
};
export const UNARMED = { min: TUNING.normal.dmg[0], max: TUNING.normal.dmg[1] };                 // everybody else (no weapon in the fight test)
export const SABER = { min: 99999, max: 99999 };   // = TUNING.owner.saber                     // Owner lightsaber: 99,999 flat per hit (boss decision), NOT combinedStats; Owner gate only
export const PLAYER = {
  hp: TUNING.normal.hp, ownerHp: TUNING.owner.hp, mp: 100, sp: 100, def: 600, agi: 20, mpRegen: 3, spRegen: 24, spDelay: 0.9,
  crit: 0.06, critMult: 1.55,
  dodge: { sp: 20, iframes: 0.38, dist: 7, cd: 0.7 }, block: { drain: 8, reduce: 0.75, parry: 0.22, minSp: 5 },
  jump: { sp: 8, dur: 0.55, height: 1.6 }, potion: { heal: 0.4, cd: 20, charges: 3 }, respawn: 3.2, lockRange: 34, lockBreak: 46,
};
/* slot order matches the HUD: Basic, Heavy, Class, Secondary, Defensive, Ultimate. kind: melee | aoe | ranged | shield | storm */
export const ABILITIES = [
  { id: 'basic', name: 'Slash', icon: '\u2694', cd: 0.5, cost: {}, kind: 'melee', mult: 1, windup: 0.14, T: 0.38, range: 4.6, arc: 0.2, stagger: 0 },
  { id: 'heavy', name: 'Heavy', icon: '\u2692', cd: 3, cost: { sp: 25 }, kind: 'melee', mult: 1.8, windup: 0.32, T: 0.7, range: 5.0, arc: 0.1, stagger: 1 },
  { id: 'class', name: 'Force Push', icon: '\u2735', cd: 6, cost: { mp: 25 }, kind: 'aoe', mult: 0.5, windup: 0.18, T: 0.55, range: 7, arc: -1, stagger: 1, knock: 7, saber: true },
  { id: 'secondary', name: 'Saber Throw', icon: '\u27B9', cd: 5, cost: { mp: 20 }, kind: 'ranged', mult: 1.2, windup: 0.2, T: 0.5, range: 16, arc: 0.6, stagger: 0, saber: true },
  { id: 'defensive', name: 'Shield', icon: '\u26E8', cd: 12, cost: { mp: 30 }, kind: 'shield', mult: 0, windup: 0.05, T: 0.4, dur: 3, reduce: 0.8, saber: true },
  { id: 'ultimate', name: 'Blade Storm', icon: '\u2604', cd: 25, cost: { mp: 60 }, kind: 'storm', mult: 3, windup: 0.3, T: 1.0, range: 6.5, arc: -1, stagger: 1, saber: true },
];
const E = (name, level, cls, hp, atk, def, speed, o) => Object.assign({ name, level, cls, hp, atk, def, speed, atkMs: 1750, tele: 0.55, reach: 2.2, aggro: 24, scale: 1, xp: Math.round(hp / 25), gold: Math.round(hp / 90), boss: false, stagger: 0.55, poise: 0 }, o);
export const ENEMIES = {
  wolf:     E('Wild Wolf', 5, 'Beast', 1050, 42, 40, 6.4, { model: 'wolf', tele: 0.4, r: 0.9 }),
  raider:   E('Forest Raider', 12, 'Bandit', 1450, 56, 80, 4.6, { model: 'o:hobgoblin', r: 1.0 }),
  wraith:   E('Vine Wraith', 18, 'Spirit', 1700, 66, 90, 4.2, { model: 'o:mossgut', r: 1.1 }),
  skeleton: E('Ash Skeleton', 30, 'Undead', 5600, 270, 200, 3.6, { model: 'o:stonetroll', atkMs: 2300, tele: 0.8, r: 1.4 }),
  frosttroll: E('Frost Troll', 45, 'Elite', 60000, 900, 400, 4.2, { model: 'n:frosttroll_a', atkMs: 2300, tele: 0.9, reach: 4.2, r: 2.6, scale: 3, aggro: 40, stagger: 0.4, poise: 0.5, xp: 4000, gold: 900 }),
  titan:    E('Ashen Titan', 60, 'Boss', 5000000, 2100, 600, 7.3, { model: 'n:ashentitan_new', atkMs: 2300, tele: 1.1, reach: 8.4, r: 5, scale: 6, aggro: 60, boss: true, stagger: 0.3, poise: 0.85, xp: 20000, gold: 4000 }),
};
export const WAVE_TABLE = ['wolf', 'raider', 'wraith', 'skeleton'];

/* Owner-only skills (cluster buttons 1-3 + ultimate 4). Rules run in the controller: Owner skin AND owner gate required, never trusted from the UI. Damage is the normal owner saber rule (calc.js). */
export const OWNER_SKILLS = {
  royal:  { id: 'royal', name: 'Royal Slash', icon: 'slash', owner: true, saber: true, cd: 4, cost: { mp: 12 }, kind: 'melee', mult: 2.2, windup: 0.18, T: 0.5, range: 7, arc: 0.45, stagger: 0 },
  chains: { id: 'chains', name: 'Shadow Chains', icon: 'chains', owner: true, saber: true, cd: 8, cost: { mp: 20 }, kind: 'melee', mult: 1.2, windup: 0.22, T: 0.55, range: 12, arc: 0.3, stagger: 1 },
  wrath:  { id: 'wrath', name: "Sovereign's Wrath", icon: 'bolt', owner: true, saber: true, cd: 12, cost: { mp: 25 }, kind: 'aoe', mult: 1.5, windup: 0.2, T: 0.6, range: 9, arc: -1, stagger: 1, knock: 5 },
  unholy: { id: 'unholy', name: 'Unholy Destruction', icon: 'meteor', owner: true, saber: true, cd: TUNING.ult.cooldown, cost: {}, fury: TUNING.ult.fury, kind: 'meteor', mode: 'all', mult: 0, windup: 0.25, T: 0.7, stagger: 0 },   // kills EVERYTHING in range except the Owner
  holy: { id: 'holy', name: 'Holy Destruction', icon: 'meteor', owner: true, saber: true, cd: TUNING.ult.cooldown, cost: {}, fury: TUNING.ult.fury, kind: 'meteor', mode: 'hostile', mult: 0, windup: 0.25, T: 0.7, stagger: 0 },   // hostile monsters + hostile characters only
};
export const ULT_IDS = ['holy', 'unholy'];
export const OWNER_CLUSTER = ['royal', 'chains', 'wrath', 'unholy'];

/* Saber damage multiplier prefs (Settings, owner only to edit; the controller still requires the owner gate to apply them). */
export const SABER_PREF_KEY = 'varn.saberdmg.v1';
export function applySaberPrefs(o) { const P = TUNING.perks; if (o && typeof o === 'object') { if (Number.isFinite(+o.mul)) P.saberMul = Math.max(0, Math.min(50, Math.floor(+o.mul))); if (typeof o.bosses === 'boolean') P.saberBossesX12 = o.bosses; if (Number.isFinite(+o.ult)) TUNING.ult.dmgMul = Math.max(1, Math.min(100, Math.floor(+o.ult))); } return { mul: P.saberMul, bosses: P.saberBossesX12, ult: TUNING.ult.dmgMul }; }
export function saveSaberPrefs() { try { localStorage.setItem(SABER_PREF_KEY, JSON.stringify({ mul: TUNING.perks.saberMul, bosses: TUNING.perks.saberBossesX12, ult: TUNING.ult.dmgMul })); } catch (e) {} }
try { if (typeof localStorage !== 'undefined') { const j = localStorage.getItem(SABER_PREF_KEY); if (j) applySaberPrefs(JSON.parse(j)); } } catch (e) {}
