/* Hero kits (data-driven): per-hero basic style + 3 skills + ultimate, color and icon. No logic here; rules run in controller.js (damage only via calc.js).
   kinds: melee (cone), aoe (ring), ranged (target), line (corridor), dash (move + corridor hit), blink (teleport behind target + hit), heal, storm (3 ticks), meteor (delayed area), shield.
   Draft table for all 20 heroes: /workspace/varn/HERO-ABILITIES.md. All 20 playable heroes have a kit. */
const sk = (hero, n, o) => Object.assign({ id: hero + '.' + n, kit: true, stagger: 0, windup: 0.18, T: 0.5, arc: 0.3, cost: {}, mult: 1.5 }, o);
const ult = (hero, o) => sk(hero, 'u', Object.assign({ fury: 100, cd: 30, windup: 0.3, T: 0.9, cost: {} }, o));
export const KITS = {
  aldric: { color: '#d9b44a', basic: 'Shield Bash combo', skills: [
    sk('aldric', 1, { name: 'Shield Bash', icon: 'shield', cd: 4, cost: { sp: 15 }, kind: 'melee', range: 3.6, arc: 0.3, mult: 1.6, stagger: 1 }),
    sk('aldric', 2, { name: 'Guardian Slam', icon: 'ring', cd: 8, cost: { sp: 25 }, kind: 'aoe', range: 6, arc: -1, mult: 2.2, stagger: 1, knock: 4 }),
    sk('aldric', 3, { name: 'Bulwark Charge', icon: 'dash', cd: 12, cost: { sp: 30 }, kind: 'dash', range: 9, dist: 9, arc: 0.7, mult: 2.4, stagger: 1 }),
    ult('aldric', { name: 'Lionheart Bulwark', icon: 'lion', kind: 'aoe', range: 10, arc: -1, mult: 4.5, stagger: 1, knock: 6, shield: 4 })] },
  elira: { color: '#5fbf6a', basic: 'Quick-draw arrow', skills: [
    sk('elira', 1, { name: 'Aimed Shot', icon: 'arrow', cd: 4, cost: { sp: 12 }, kind: 'ranged', range: 20, arc: 0.6, mult: 1.8 }),
    sk('elira', 2, { name: 'Piercing Arrow', icon: 'line', cd: 8, cost: { mp: 20 }, kind: 'line', range: 22, arc: 0.93, mult: 2.6 }),
    sk('elira', 3, { name: 'Snare Trap', icon: 'trap', cd: 12, cost: { mp: 25 }, kind: 'aoe', range: 5, arc: -1, mult: 1.2, stagger: 2 }),
    ult('elira', { name: 'Eagle-Eye Barrage', icon: 'volley', kind: 'storm', range: 16, arc: 0.4, mult: 6 })] },
  rowan: { color: '#ff7a2a', basic: 'Firebolt', skills: [
    sk('rowan', 1, { name: 'Firebolt', icon: 'flame', cd: 4, cost: { mp: 15 }, kind: 'ranged', range: 18, arc: 0.6, mult: 2 }),
    sk('rowan', 2, { name: 'Flame Wave', icon: 'wave', cd: 8, cost: { mp: 25 }, kind: 'melee', range: 9, arc: 0.25, mult: 2.4, stagger: 1 }),
    sk('rowan', 3, { name: 'Ember Burst', icon: 'ring', cd: 12, cost: { mp: 30 }, kind: 'aoe', range: 6.5, arc: -1, mult: 2.6, stagger: 1 }),
    ult('rowan', { name: 'Meteor Burst', icon: 'meteor', kind: 'meteor', mult: 8, radius: 10, delay: 1.4 })] },
  thorne: { color: '#f3f0d0', basic: 'Staff light bolt', skills: [
    sk('thorne', 1, { name: 'Radiant Bolt', icon: 'sun', cd: 4, cost: { mp: 12 }, kind: 'ranged', range: 18, arc: 0.6, mult: 1.8 }),
    sk('thorne', 2, { name: 'Mend', icon: 'heal', cd: 8, cost: { mp: 25 }, kind: 'heal', heal: 0.3 }),
    sk('thorne', 3, { name: 'Holy Smite', icon: 'ring', cd: 12, cost: { mp: 30 }, kind: 'aoe', range: 5.5, arc: -1, mult: 2.4, stagger: 1 }),
    ult('thorne', { name: 'Divine Renewal', icon: 'heal2', kind: 'aoe', range: 8, arc: -1, mult: 3, heal: 0.6 })] },
  nyx: { color: '#7a4bd0', basic: 'Twin dagger flurry', skills: [
    sk('nyx', 1, { name: 'Dagger Flurry', icon: 'dagger', cd: 4, cost: { sp: 15 }, kind: 'storm', range: 3.8, arc: -1, mult: 2.4 }),
    sk('nyx', 2, { name: 'Shadow Step', icon: 'blink', cd: 8, cost: { sp: 20 }, kind: 'blink', range: 14, arc: 0.6, mult: 2 }),
    sk('nyx', 3, { name: 'Poison Cut', icon: 'poison', cd: 12, cost: { sp: 25 }, kind: 'melee', range: 3.8, arc: 0.3, mult: 2.6, stagger: 1 }),
    ult('nyx', { name: 'Shadow Flurry', icon: 'storm', kind: 'storm', range: 8, arc: -1, mult: 7 })] },
  /* ---- remaining 15 heroes (draft: /workspace/varn/HERO-ABILITIES.md) ---- */
  seraphine: { color: '#ffd86a', basic: "Mace swing", skills: [
    sk('seraphine', 1, { name: "Sun Smite", icon: 'sun', cd: 4, cost: { mp: 15 }, kind: 'line', range: 16, arc: 0.9, mult: 1.9 }),
    sk('seraphine', 2, { name: "Aegis Dash", icon: 'dash', cd: 8, cost: { sp: 25 }, kind: 'dash', range: 8, dist: 8, arc: 0.7, mult: 2.3, stagger: 1 }),
    sk('seraphine', 3, { name: "Consecrate", icon: 'ring', cd: 12, cost: { mp: 30 }, kind: 'aoe', range: 6, arc: -1, mult: 2.2, heal: 0.15 }),
    ult('seraphine', { name: "Radiant Aegis", icon: 'sun', kind: 'aoe', range: 10, arc: -1, mult: 4.5, stagger: 1, shield: 5, heal: 0.3 })] },
  garruk: { color: '#c0392b', basic: "Axe chop", skills: [
    sk('garruk', 1, { name: "Whirl Axe", icon: 'slash', cd: 4, cost: { sp: 15 }, kind: 'aoe', range: 4.5, arc: -1, mult: 2.0 }),
    sk('garruk', 2, { name: "Ground Pound", icon: 'ring', cd: 8, cost: { sp: 25 }, kind: 'aoe', range: 7, arc: -1, mult: 2.4, stagger: 1, knock: 5 }),
    sk('garruk', 3, { name: "War Cry", icon: 'lion', cd: 12, cost: { sp: 20 }, kind: 'shield', dur: 4, reduce: 0.4 }),
    ult('garruk', { name: "Bloodstorm", icon: 'storm', kind: 'storm', range: 8, arc: -1, mult: 7 })] },
  mirelle: { color: '#7bd36a', basic: "Thorn lash", skills: [
    sk('mirelle', 1, { name: "Entangle", icon: 'trap', cd: 4, cost: { mp: 15 }, kind: 'aoe', range: 5.5, arc: -1, mult: 1.4, stagger: 2 }),
    sk('mirelle', 2, { name: "Bloom", icon: 'heal', cd: 8, cost: { mp: 25 }, kind: 'heal', heal: 0.28 }),
    sk('mirelle', 3, { name: "Wolf Dash", icon: 'dash', cd: 12, cost: { sp: 25 }, kind: 'dash', range: 9, dist: 9, arc: 0.7, mult: 2.4 }),
    ult('mirelle', { name: "Grove Awakening", icon: 'ring', kind: 'aoe', range: 11, arc: -1, mult: 5, stagger: 2 })] },
  cedric: { color: '#e8a0d0', basic: "Lute strum", skills: [
    sk('cedric', 1, { name: "Battle Hymn", icon: 'bolt', cd: 4, cost: { mp: 15 }, kind: 'shield', dur: 4, reduce: 0.25, heal: 0.1 }),
    sk('cedric', 2, { name: "Dissonance", icon: 'wave', cd: 8, cost: { mp: 25 }, kind: 'melee', range: 8, arc: 0.3, mult: 2.2, stagger: 2 }),
    sk('cedric', 3, { name: "Encore", icon: 'heal2', cd: 12, cost: { mp: 30 }, kind: 'heal', heal: 0.2 }),
    ult('cedric', { name: "Grand Crescendo", icon: 'wave', kind: 'aoe', range: 10, arc: -1, mult: 4.5, stagger: 1, heal: 0.3 })] },
  morwen: { color: '#4de0a0', basic: "Scythe sweep", skills: [
    sk('morwen', 1, { name: "Raise Thrall", icon: 'throw', cd: 4, cost: { mp: 15 }, kind: 'ranged', range: 16, arc: 0.6, mult: 1.8 }),
    sk('morwen', 2, { name: "Soul Drain", icon: 'line', cd: 8, cost: { mp: 25 }, kind: 'line', range: 14, arc: 0.9, mult: 2.4, heal: 0.06 }),
    sk('morwen', 3, { name: "Bone Cage", icon: 'trap', cd: 12, cost: { mp: 30 }, kind: 'aoe', range: 5.5, arc: -1, mult: 2.0, stagger: 2 }),
    ult('morwen', { name: "Legion of the Dead", icon: 'storm', kind: 'line', range: 22, arc: 0.95, mult: 6.5 })] },
  kael: { color: '#40c4ff', basic: "Rune bolt", skills: [
    sk('kael', 1, { name: "Arc Rune", icon: 'bolt', cd: 4, cost: { mp: 15 }, kind: 'ranged', range: 18, arc: 0.6, mult: 2.0 }),
    sk('kael', 2, { name: "Ward Rune", icon: 'trap', cd: 8, cost: { mp: 25 }, kind: 'aoe', range: 5.5, arc: -1, mult: 2.4, stagger: 1 }),
    sk('kael', 3, { name: "Rune Swap", icon: 'blink', cd: 12, cost: { mp: 25 }, kind: 'blink', range: 14, arc: 0.6, mult: 2.0 }),
    ult('kael', { name: "Runic Cataclysm", icon: 'ring', kind: 'aoe', range: 11, arc: -1, mult: 5.5, stagger: 1 })] },
  vesper: { color: '#b38b59', basic: "Crossbow bolt", skills: [
    sk('vesper', 1, { name: "Hex Mark", icon: 'arrow', cd: 4, cost: { sp: 12 }, kind: 'ranged', range: 20, arc: 0.6, mult: 2.0 }),
    sk('vesper', 2, { name: "Purge Flare", icon: 'sun', cd: 8, cost: { mp: 25 }, kind: 'aoe', range: 6, arc: -1, mult: 1.8, stagger: 2 }),
    sk('vesper', 3, { name: "Hunter's Roll", icon: 'dash', cd: 12, cost: { sp: 25 }, kind: 'dash', range: 8, dist: 8, arc: 0.7, mult: 2.2 }),
    ult('vesper', { name: "Judgement Volley", icon: 'volley', kind: 'storm', range: 16, arc: 0.4, mult: 6 })] },
  talia: { color: '#59c3ff', basic: "Spark staff", skills: [
    sk('talia', 1, { name: "Chain Lightning", icon: 'bolt', cd: 4, cost: { mp: 15 }, kind: 'ranged', range: 18, arc: 0.6, mult: 2.2 }),
    sk('talia', 2, { name: "Totem of Wind", icon: 'wave', cd: 8, cost: { mp: 25 }, kind: 'shield', dur: 4, reduce: 0.25 }),
    sk('talia', 3, { name: "Static Field", icon: 'trap', cd: 12, cost: { mp: 30 }, kind: 'aoe', range: 6, arc: -1, mult: 1.6, stagger: 2 }),
    ult('talia', { name: "Tempest Call", icon: 'bolt', kind: 'storm', range: 14, arc: -1, mult: 6.5 })] },
  orin: { color: '#d0a070', basic: "Spear thrust", skills: [
    sk('orin', 1, { name: "Sweep", icon: 'slash', cd: 4, cost: { sp: 15 }, kind: 'melee', range: 5, arc: 0.8, mult: 1.8, stagger: 1 }),
    sk('orin', 2, { name: "Vault Strike", icon: 'dash', cd: 8, cost: { sp: 25 }, kind: 'dash', range: 9, dist: 9, arc: 0.7, mult: 2.4, stagger: 1 }),
    sk('orin', 3, { name: "Phalanx Stance", icon: 'shield', cd: 12, cost: { sp: 20 }, kind: 'shield', dur: 4, reduce: 0.6 }),
    ult('orin', { name: "Thousand Thrusts", icon: 'line', kind: 'storm', range: 9, arc: 0.5, mult: 7 })] },
  selene: { color: '#9fe8ff', basic: "Ice shard", skills: [
    sk('selene', 1, { name: "Frost Nova", icon: 'ring', cd: 4, cost: { mp: 15 }, kind: 'aoe', range: 5.5, arc: -1, mult: 1.8, stagger: 2 }),
    sk('selene', 2, { name: "Glacier Wall", icon: 'shield', cd: 8, cost: { mp: 25 }, kind: 'shield', dur: 3, reduce: 0.5 }),
    sk('selene', 3, { name: "Blink Frost", icon: 'blink', cd: 12, cost: { mp: 25 }, kind: 'blink', range: 14, arc: 0.6, mult: 2.2 }),
    ult('selene', { name: "Absolute Zero", icon: 'ring', kind: 'aoe', range: 12, arc: -1, mult: 5.5, stagger: 2 })] },
  darius: { color: '#6a3d9a', basic: "Greatsword cleave", skills: [
    sk('darius', 1, { name: "Shadow Cleave", icon: 'wave', cd: 4, cost: { sp: 15 }, kind: 'line', range: 12, arc: 0.9, mult: 1.9 }),
    sk('darius', 2, { name: "Vampiric Grasp", icon: 'poison', cd: 8, cost: { mp: 25 }, kind: 'melee', range: 7, arc: 0.3, mult: 2.2, stagger: 1, heal: 0.08 }),
    sk('darius', 3, { name: "Dark Armor", icon: 'shield', cd: 12, cost: { mp: 25 }, kind: 'shield', dur: 4, reduce: 0.5 }),
    ult('darius', { name: "Eclipse Reaver", icon: 'heavy', kind: 'aoe', range: 11, arc: -1, mult: 6, stagger: 2, knock: 6 })] },
  finn: { color: '#e84a5f', basic: "Rapier lunges", skills: [
    sk('finn', 1, { name: "Riposte", icon: 'shield', cd: 4, cost: { sp: 12 }, kind: 'shield', dur: 1.2, reduce: 0.9 }),
    sk('finn', 2, { name: "Fleche Dash", icon: 'dash', cd: 8, cost: { sp: 25 }, kind: 'dash', range: 11, dist: 11, arc: 0.6, mult: 2.6 }),
    sk('finn', 3, { name: "Feint", icon: 'slash', cd: 12, cost: { sp: 20 }, kind: 'melee', range: 4, arc: 0.4, mult: 2.0, stagger: 2 }),
    ult('finn', { name: "Thousand Cuts", icon: 'dagger', kind: 'storm', range: 9, arc: -1, mult: 7 })] },
  brynn: { color: '#ffb03a', basic: "Repeater crossbow", skills: [
    sk('brynn', 1, { name: "Turret", icon: 'trap', cd: 4, cost: { sp: 15 }, kind: 'storm', range: 14, arc: 0.5, mult: 2.2 }),
    sk('brynn', 2, { name: "Mine Field", icon: 'ring', cd: 8, cost: { sp: 25 }, kind: 'aoe', range: 6, arc: -1, mult: 2.4, stagger: 1 }),
    sk('brynn', 3, { name: "Overclock", icon: 'bolt', cd: 12, cost: { sp: 20 }, kind: 'shield', dur: 4, reduce: 0.2 }),
    ult('brynn', { name: "Siege Cannon", icon: 'meteor', kind: 'meteor', mult: 8, radius: 12, delay: 1.4 })] },
  asha: { color: '#ffcf5a', basic: "Palm combo", skills: [
    sk('asha', 1, { name: "Dragon Kick", icon: 'push', cd: 4, cost: { sp: 15 }, kind: 'melee', range: 4, arc: 0.4, mult: 2.0, stagger: 1, knock: 6 }),
    sk('asha', 2, { name: "Meditation Shield", icon: 'heal', cd: 8, cost: { mp: 25 }, kind: 'shield', dur: 3, reduce: 0.5, heal: 0.15 }),
    sk('asha', 3, { name: "Chi Burst", icon: 'ring', cd: 12, cost: { mp: 30 }, kind: 'aoe', range: 6, arc: -1, mult: 2.2, stagger: 2 }),
    ult('asha', { name: "Heaven's Fist", icon: 'heavy', kind: 'meteor', mult: 8, radius: 8, delay: 1.0 })] },
  rook: { color: '#8fae5a', basic: "Whip snare", skills: [
    sk('rook', 1, { name: "Wolf Pounce", icon: 'dash', cd: 4, cost: { sp: 15 }, kind: 'dash', range: 8, dist: 8, arc: 0.7, mult: 2.0 }),
    sk('rook', 2, { name: "Howl", icon: 'wave', cd: 8, cost: { sp: 25 }, kind: 'aoe', range: 7, arc: -1, mult: 1.6, stagger: 1 }),
    sk('rook', 3, { name: "Feral Mend", icon: 'heal', cd: 12, cost: { sp: 25 }, kind: 'heal', heal: 0.3 }),
    ult('rook', { name: "Pack Stampede", icon: 'storm', kind: 'line', range: 20, arc: 0.95, mult: 6.5 })] },
};

/* ---- Weapon + armor loadout per hero (data only; no model changes). weapon.glb = file in /workspace/weapons (Beth) when one fits, else null; dmgPct = bonus to NORMAL damage (non-Owner only). armor = the hero's EXISTING outfit, stat bonuses as fractions of max HP/MP/SP and DEF. ---- */
export const LOADOUT = {
  aldric: { weapon: { name: 'Steel Longsword', glb: null, model: 'procedural (aldric.js)', dmgPct: 0.05 }, armor: { name: 'Lionguard Plate', hpPct: 0.2, mpPct: 0, spPct: 0, defPct: 0.15 } },
  darius: { weapon: { name: 'Shadow Greatsword', glb: null, model: 'procedural (heroes2.js)', dmgPct: 0.08 }, armor: { name: 'Umbral Plate', hpPct: 0.15, mpPct: 0, spPct: 0, defPct: 0.12 } },
  selene: { weapon: { name: 'Crystal Staff', glb: null, model: 'procedural (heroes2.js)', dmgPct: 0.05 }, armor: { name: 'Frostveil Robes', hpPct: 0.05, mpPct: 0.2, spPct: 0, defPct: 0.04 } },
  elira: { weapon: { name: 'Longbow', glb: null, model: 'none yet', dmgPct: 0.06 }, armor: { name: 'Ranger Leathers', hpPct: 0.08, mpPct: 0.05, spPct: 0.1, defPct: 0.06 } },
  orin: { weapon: { name: 'Ashlance Spear', glb: null, model: 'none yet', dmgPct: 0.06 }, armor: { name: 'Ashplate Cuirass', hpPct: 0.15, mpPct: 0, spPct: 0.05, defPct: 0.12 } },
  seraphine: { weapon: { name: 'Holy Mace', glb: 'seraphine_holymace', model: 'weapons/seraphine_holymace.glb', dmgPct: 0.06 }, armor: { name: 'Sunforged Armor', hpPct: 0.18, mpPct: 0.05, spPct: 0, defPct: 0.14 } },
  talia: { weapon: { name: 'Storm Staff', glb: null, model: 'none yet', dmgPct: 0.05 }, armor: { name: 'Stormcaller Garb', hpPct: 0.05, mpPct: 0.18, spPct: 0, defPct: 0.04 } },
  finn: { weapon: { name: 'Duelist Rapier', glb: 'finn_rapier', model: 'weapons/finn_rapier.glb (+ finn_parry_dagger.glb off-hand)', dmgPct: 0.07 }, armor: { name: 'Crimson Doublet', hpPct: 0.06, mpPct: 0, spPct: 0.15, defPct: 0.05 } },
  brynn: { weapon: { name: 'Repeater Crossbow', glb: 'brynn_repeater_crossbow', model: 'weapons/brynn_repeater_crossbow.glb', dmgPct: 0.06 }, armor: { name: 'Cogwright Apron', hpPct: 0.1, mpPct: 0, spPct: 0.12, defPct: 0.08 } },
  mirelle: { weapon: { name: 'Thorn Sickle', glb: 'mirelle_sickle', model: 'weapons/mirelle_sickle.glb', dmgPct: 0.05 }, armor: { name: 'Rootweave Vestments', hpPct: 0.08, mpPct: 0.15, spPct: 0, defPct: 0.05 } },
  nyx: { weapon: { name: 'Twin Daggers', glb: 'nyx_dagger', model: 'weapons/nyx_dagger.glb (R+L)', dmgPct: 0.07 }, armor: { name: 'Shadowsilk Leathers', hpPct: 0.05, mpPct: 0, spPct: 0.18, defPct: 0.05 } },
  vesper: { weapon: { name: 'Silver Hand Crossbow', glb: 'hand_crossbow', model: 'weapons/hand_crossbow.glb', dmgPct: 0.06 }, armor: { name: 'Hunter Coat', hpPct: 0.1, mpPct: 0, spPct: 0.1, defPct: 0.08 } },
  thorne: { weapon: { name: 'Radiant Spellbook (off-hand)', glb: 'spellbook', model: 'weapons/spellbook.glb (off-hand)', dmgPct: 0.04 }, armor: { name: 'Vestments of Light', hpPct: 0.06, mpPct: 0.2, spPct: 0, defPct: 0.05 } },
  rook: { weapon: { name: 'Beastmaster Whip', glb: 'rook_whip', model: 'weapons/rook_whip.glb', dmgPct: 0.05 }, armor: { name: 'Wildbane Hides', hpPct: 0.12, mpPct: 0, spPct: 0.12, defPct: 0.08 } },
  asha: { weapon: { name: 'Hand Wraps + Knuckles', glb: 'asha_knuckles', model: 'weapons/asha_knuckles.glb', dmgPct: 0.07 }, armor: { name: 'Saffron Gi', hpPct: 0.1, mpPct: 0.05, spPct: 0.12, defPct: 0.06 } },
  rowan: { weapon: { name: 'Fire Staff', glb: null, model: 'none yet', dmgPct: 0.05 }, armor: { name: 'Emberweave Robes', hpPct: 0.04, mpPct: 0.2, spPct: 0, defPct: 0.03 } },
  kael: { weapon: { name: 'Rune Staff', glb: null, model: 'none yet', dmgPct: 0.05 }, armor: { name: 'Runebound Coat', hpPct: 0.06, mpPct: 0.18, spPct: 0, defPct: 0.05 } },
  cedric: { weapon: { name: 'Lute', glb: null, model: 'none yet', dmgPct: 0.04 }, armor: { name: 'Minstrel Finery', hpPct: 0.06, mpPct: 0.1, spPct: 0.08, defPct: 0.04 } },
  morwen: { weapon: { name: 'Bone Scythe', glb: 'morwen_scythe', model: 'weapons/morwen_scythe.glb', dmgPct: 0.06 }, armor: { name: 'Blackveil Shroud', hpPct: 0.06, mpPct: 0.16, spPct: 0, defPct: 0.06 } },
  garruk: { weapon: { name: 'Stonefist Greataxe', glb: 'garruk_greataxe', model: 'weapons/garruk_greataxe.glb', dmgPct: 0.08 }, armor: { name: 'Stonefist Harness', hpPct: 0.22, mpPct: 0, spPct: 0.05, defPct: 0.15 } },
};
for (const k of Object.keys(KITS)) Object.assign(KITS[k], LOADOUT[k] || {});
export const heroKey = id => String(id || '').replace(/^[a-z]:/, '').replace(/(_(smooth|new\d*|cl_arms|fight\d*|arms))+$/, '');
export const kitFor = id => KITS[heroKey(id)] || null;
export const kitSkill = (kit, id) => (kit && kit.skills.find(s => s.id === id)) || null;
