/* Combat data (Phase 1). Enemy stats mirror www/data.js ENEMIES (hp / atk) and the 2D game's cadence (attack every 1750 ms, boss 2300 ms). No logic here. */
/* ---- ONE place for combat feel. Normal characters: ~8-15 s per normal enemy (wolf/raider), elites longer, bosses much longer. Owner is exempt. ---- */
export const TUNING = {
  normal: { dmg: [28, 48], basicCdMul: 0.6, windupMul: 1.5, basicSp: 3, hp: 700, staggerFrac: 0.2 },   // dmg per basic hit, cooldown/wind-up multipliers, stamina per swing, max HP, enemy staggers after this fraction of its HP in damage
  owner: { hp: 999999, saber: 99999 },
  /* Unholy Destruction (Owner ultimate). ONE config block: bossesInstantKill=false => bosses (Ashen Titan...) take the normal owner saber hit instead of dying. */
  perks: { saberBossesX12: false, saberMul: 12, saberHolderResources: false, holderMul: 3 },   // holderMul: max HP/MP/SP multiplier for a non-Owner hero holding the Owner saber (owner account only)   // false: unlimited MP/SP + no cooldowns only for the Owner skin; true: any hero holding the Owner saber gets them too
  ownerWeaponBase: 99999,   // OWNER holding ANY weapon except the lightsaber: base damage per hit (0 = off, use the weapon's own damage)
  skillMul: { royal: 3, chains: 6, wrath: 12 },   // OWNER SKILL DAMAGE = flat 99,999 x this (300% / 600% / 1200%); owner gate enforced in the controller
  ult: { dmgMul: 50, radius: 25, delay: 1.5, cooldown: 35, fury: 100, bossesInstantKill: true, furyPerBasic: 8, furyPerSkill: 5 },
};
export const BAMBOO = { min: 4, max: 8 };   // Bamboo Stick (test weapon, owner account only): low base damage; owner skills use the 99,999 x skillMul rule with it
export const UNARMED = { min: TUNING.normal.dmg[0], max: TUNING.normal.dmg[1] };                 // everybody else (no weapon in the fight test)
/* ---- Boss attack patterns (data-driven). reach/len/width are in hero-scale units (x HS at runtime, like def.reach). shape: ring | cone | line.
   Patterns rotate in order (learnable); phase 2 (HP < TUNING.boss.enrageAt) adds the phase-2 moves, shortens telegraphs and speeds the boss up. Damage still goes through calc.js (atk x dmg). ---- */
export const BOSS_PATTERNS = {
  titan: [
    { id: 'stomp', name: 'Titan Stomp', shape: 'ring', reach: 6.5, tele: 1.1, dmg: 1.0 },
    { id: 'sweep', name: 'Cleaving Sweep', shape: 'cone', reach: 8.4, cos: 0.35, tele: 1.0, dmg: 1.1 },
    { id: 'slam', name: 'Ashen Slam', shape: 'line', reach: 14, width: 3.6, tele: 1.4, dmg: 1.4 },
    { id: 'quake', name: 'Rage Quake', shape: 'ring', reach: 12, tele: 1.0, dmg: 1.6, phase: 2 },
  ],
  titan40: [
    { id:'moltenStomp',name:'Molten Cataclysm',shape:'ring',reach:23,tele:2.1,dmg:1.35 },
    { id:'ashenWave',name:'Lava Shockwave',shape:'cone',reach:29,cos:.1,tele:1.9,dmg:1.5 },
    { id:'eruption',name:'Eruption Pillars',shape:'line',reach:39,width:11,tele:2.4,dmg:1.85 },
    { id:'inferno',name:'Inferno Collapse',shape:'ring',reach:34,tele:2.3,dmg:2.15,phase:2 }
  ],
  frosttroll_a:[
    { id:'winterhammer',name:'Winterhammer',shape:'cone',reach:6.4,cos:.28,tele:1.1,dmg:1.1,slow:.35 },
    { id:'glacierbreaker',name:'Glacier Breaker',shape:'line',reach:15,width:3.8,tele:1.5,dmg:1.5,slow:.5 },
    { id:'brotherswrath',name:"Brother's Wrath",shape:'ring',reach:10,tele:1.3,dmg:1.75,phase:2 }
  ],
  frosttroll_b:[
    { id:'frostcrash',name:'Frost Crash',shape:'ring',reach:7.2,tele:1.1,dmg:1.1,slow:.35 },
    { id:'avalanche',name:'Avalanche Lance',shape:'line',reach:18,width:4.6,tele:1.6,dmg:1.5,slow:.6 },
    { id:'brothersvengeance',name:"Brother's Vengeance",shape:'cone',reach:13,cos:.13,tele:1.2,dmg:1.8,phase:2 }
  ],
  /* Frost Troll (elite, patterns: true): short, readable club moves; phase 2 adds the glacier line. */
  frosttroll: [
    { id: 'club', name: 'Club Smash', shape: 'cone', reach: 4.6, cos: 0.4, tele: 0.9, dmg: 1.0 },
    { id: 'stomp', name: 'Frost Stomp', shape: 'ring', reach: 4.0, tele: 1.0, dmg: 0.9, slow: 0.4 },
    { id: 'roll', name: 'Avalanche Charge', shape: 'line', reach: 9, width: 2.6, tele: 1.2, dmg: 1.2 },
    { id: 'glacier', name: 'Glacier Spike', shape: 'line', reach: 13, width: 2.0, tele: 1.0, dmg: 1.5, phase: 2, slow: 0.5 },
  ],
  /* Vaelthryx (enemy boss, 10x hero): huge reaches, crystal moves; phase 2 adds the Sovereign Nova. */
  vaelthryx: [
    { id: 'claw', name: 'Crystal Claw', shape: 'cone', reach: 9.5, cos: 0.3, tele: 1.0, dmg: 1.0 },
    { id: 'tail', name: 'Tail Sweep', shape: 'ring', reach: 8.0, tele: 1.1, dmg: 1.1 },
    { id: 'breath', name: 'Prism Breath', shape: 'line', reach: 22, width: 4.2, tele: 1.5, dmg: 1.5 },
    { id: 'shards', name: 'Shard Rain', shape: 'ring', reach: 14, tele: 1.3, dmg: 1.2 },
    { id: 'nova', name: 'Sovereign Nova', shape: 'ring', reach: 20, tele: 1.4, dmg: 1.8, phase: 2 },
  ],
};
TUNING.boss = { enrageAt: 0.5, enrageTele: 0.75, enrageSpeed: 1.25, enrageCd: 0.8 };   // phase-2 tuning (bosses only)
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
/* Owner second ultimate (not a HUD slot yet - hud.js untouched; triggered by key 7 or T / fight.useUltimate2()). chain: strikes the nearest enemy from the sky, arcs to nearby ones with falloff. */
export const ULTIMATE2 = { id: 'ultimate2', name: 'Thunderstorm', icon: '\u26A1', cd: 30, cost: { mp: 70 }, kind: 'chain', lethal: true, mult: 4, windup: 0.35, T: 1.1, range: 220, visualBolts: 12, falloff: 0.9, stagger: 1, saber: true };
const E = (name, level, cls, hp, atk, def, speed, o) => Object.assign({ name, level, cls, hp, atk, def, speed, atkMs: 1750, tele: 0.55, reach: 2.2, aggro: 24, scale: 1, xp: Math.round(hp / 25), gold: Math.round(hp / 90), boss: false, stagger: 0.55, poise: 0 }, o);
export const ENEMIES = {
  wolf:     E('Wild Wolf', 5, 'Beast', 1050, 42, 40, 6.4, { model: 'wolf', tele: 0.4, r: 0.9 }),
  raider:   E('Hobgoblin Raider', 12, 'Bandit', 1450, 56, 80, 4.6, { model: 'o:hobgoblin', r: 1.0 }),
  hob_enforcer: E('Hobgoblin Enforcer', 19, 'Camp Guard', 3200, 100, 160, 4.2, { model:'o:hobgoblin', r:1.05, aggro:23, xp:190, gold:58 }),
  wraith:   E('Vine Wraith', 18, 'Spirit', 1700, 66, 90, 4.2, { model: 'o:mossgut', r: 1.1 }),
  skeleton: E('Ash Skeleton', 30, 'Undead', 5600, 270, 200, 3.6, { model: 'o:stonetroll', atkMs: 2300, tele: 0.8, r: 1.4 }),
  frosttroll: E('Frost Troll', 45, 'Elite', 60000, 900, 400, 4.2, { model: 'n:frosttroll_a', atkMs: 2300, tele: 0.9, reach: 4.2, r: 2.6, scale: 3, aggro: 40, patterns: true, stagger: 0.4, poise: 0.5, xp: 4000, gold: 900 }),
  frosttroll_a:E('Frost Troll A — Elder Brother',52,'Brother Boss',780000,1320,480,4.4,{model:'n:frosttroll_a',atkMs:2200,tele:1.0,reach:6.4,r:2.5,scale:3,aggro:65,boss:true,stagger:.45,poise:.65,xp:6200,gold:1500}),
  frosttroll_b:E('Frost Troll B — Younger Brother',52,'Brother Boss',780000,1450,430,4.9,{model:'n:frosttroll_b',atkMs:2250,tele:1.0,reach:7.2,r:2.5,scale:3,aggro:65,boss:true,stagger:.45,poise:.65,xp:6200,gold:1500}),
  titan40: E('Ashen Titan — 40×',80,'Volcanic Boss',11500000,3200,990,4.1,{model:'n:ashentitan_40',atkMs:3400,tele:2.2,reach:27,r:18,scale:40,aggro:105,boss:true,stagger:.25,poise:.95,xp:54000,gold:13000}),
  titan:    E('Ashen Titan', 60, 'Boss', 5000000, 2100, 600, 7.3, { model: 'n:ashentitan_new', atkMs: 2300, tele: 1.1, reach: 8.4, r: 5, scale: 6, aggro: 60, boss: true, stagger: 0.3, poise: 0.85, xp: 20000, gold: 4000 }),
  vaelthryx: E('Balthrix the Crystal Sovereign', 70, 'Boss', 8000000, 2600, 700, 7.0, { model: 'n:vaelthryx_straight_rig', atkMs: 2400, tele: 1.1, reach: 9.5, r: 5.2, scale: 10, aggro: 70, boss: true, stagger: 0.25, poise: 0.9, xp: 30000, gold: 6000 }),
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
export function applySaberPrefs(o) { const P = TUNING.perks; if (o && typeof o === 'object') { if (Number.isFinite(+o.mul)) P.saberMul = Math.max(0, Math.min(50, Math.floor(+o.mul))); if (typeof o.bosses === 'boolean') P.saberBossesX12 = o.bosses; if (typeof o.bossKill === 'boolean') TUNING.ult.bossesInstantKill = o.bossKill; if (Number.isFinite(+o.ult)) TUNING.ult.dmgMul = Math.max(1, Math.min(100, Math.floor(+o.ult))); } return { mul: P.saberMul, bosses: P.saberBossesX12, ult: TUNING.ult.dmgMul }; }
export function saveSaberPrefs() { try { localStorage.setItem(SABER_PREF_KEY, JSON.stringify({ mul: TUNING.perks.saberMul, bosses: TUNING.perks.saberBossesX12, ult: TUNING.ult.dmgMul, bossKill: TUNING.ult.bossesInstantKill })); } catch (e) {} }
try { if (typeof localStorage !== 'undefined') { const j = localStorage.getItem(SABER_PREF_KEY); if (j) applySaberPrefs(JSON.parse(j)); } } catch (e) {}
