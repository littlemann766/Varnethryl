// Generates /workspace/varn/HERO-ABILITIES.md table from combat/herokits.js (single source of truth).
import { KITS } from '../www/proto3d/combat/herokits.js'; import fs from 'fs';
const NAMES = { aldric: ['Sir Aldric', 'Knight'], darius: ['Darius Umbral', 'Dark Knight'], selene: ['Selene Frostveil', 'Cryomancer'], elira: ['Lady Elira', 'Ranger'], orin: ['Orin Ashlance', 'Spearman'], seraphine: ['Dame Seraphine', 'Paladin'], talia: ['Talia Stormcall', 'Shaman'], finn: ['Finn Valecourt', 'Duelist'], brynn: ['Brynn Cogwright', 'Engineer'], mirelle: ['Mirelle Thornroot', 'Druid'], nyx: ['Nyx Varrin', 'Rogue'], vesper: ['Vesper Crowe', 'Witch Hunter'], thorne: ['Brother Thorne', 'Cleric'], rook: ['Rook Wildbane', 'Beastmaster'], asha: ['Asha Ironfist', 'Monk'], rowan: ['Rowan Firebrand', 'Mage'], kael: ['Kael Runebinder', 'Runemaster'], cedric: ['Cedric Vale', 'Bard'], morwen: ['Morwen Blackveil', 'Necromancer'], garruk: ['Garruk Stonefist', 'Berserker'] };
const cost = c => Object.entries(c || {}).map(([k, v]) => v + ' ' + k.toUpperCase()).join('+') || '-';
const eff = s => { const b = []; if (s.mult && s.kind !== 'heal' && s.kind !== 'shield') b.push('x' + s.mult); if (s.heal) b.push('heal ' + Math.round(s.heal * 100) + '%'); if (s.shield) b.push('shield ' + s.shield + 's'); if (s.dur) b.push('guard ' + s.dur + 's -' + Math.round((s.reduce || 0) * 100) + '%'); if (s.stagger) b.push('stagger'); if (s.radius) b.push('r' + s.radius); return b.join(' ') || '-'; };
const cell = s => `${s.name} (${s.kind}, ${eff(s)}, ${s.cd}s, ${cost(s.cost)})`;
const ucell = s => `**${s.name}** (${s.kind}, ${eff(s)}, ${s.fury} Fury, ${s.cd}s cd)`;
const pc = v => (v ? '+' + Math.round(v * 100) + '%' : '-');
const load = K => `${K.weapon.name} (${pc(K.weapon.dmgPct)} dmg; ${K.weapon.glb ? 'model: ' + K.weapon.model : 'model needed (' + K.weapon.model + ')'}) / ${K.armor.name} (HP ${pc(K.armor.hpPct)}, MP ${pc(K.armor.mpPct)}, SP ${pc(K.armor.spPct)}, DEF ${pc(K.armor.defPct)})`;
const rows = Object.entries(NAMES).map(([k, [n, c]], i) => { const K = KITS[k]; return `| ${i} | ${n} | ${c} | ${K.color} | ${K.basic} | ${K.skills.slice(0, 3).map(cell).join(' | ')} | ${ucell(K.skills[3])} | ${load(K)} |`; });
const md = `# HERO ABILITIES - all 20 heroes (for boss review)

Generated from \`www/proto3d/combat/herokits.js\` on branch **hud-heroes** by \`tools/gen_hero_table.mjs\` (the code is the single source of truth). Skill format: name (move type, damage multiplier / effect, cooldown, cost). Damage multiplier x = multiple of the normal hit (UNARMED 28-48 x mult, crit rule unchanged); all damage is computed only in combat/calc.js. Animation comes later: casts reuse the existing attack clips.

## Rules
- Pad: Basic (big, spammable) + Skills 1-3 + Ultimate (needs 100 Fury, built by hits: +8 basic, +5 skill). Same layout for every hero; names / icons / ring colour come from the kit.
- Move types: melee (cone), aoe (ring), ranged (target), line (corridor), dash (move + corridor hit), blink (teleport to target + hit), heal, shield (guard), storm (3 ticks), meteor (delayed area, damage not instant-kill).
- Owner kit and rules are untouched: owner skills, saber, Holy/Unholy ultimates are gated by the owner account and never trusted from the UI. Non-owner heroes only ever use their own kit.
- Bosses (Ashen Titan etc.) take normal damage from kit ultimates; bossesInstantKill stays false.
- Buff-style moves (Battle Hymn, Totem of Wind, Overclock, Howl...) are approximated with guard/heal/stagger until real party buffs and summons exist (not built yet).

## Table
| # | Hero | Class | Colour | Basic | Skill 1 | Skill 2 | Skill 3 | Ultimate |
|---|---|---|---|---|---|---|---|---|
${rows.join('\n')}

## Weapon + armor kits
Data-driven in \`herokits.js\` (\`weapon\`, \`armor\` per hero). Weapon = signature weapon; \`dmgPct\` boosts NORMAL damage only (never the Owner's rules). Armor = the hero's EXISTING outfit (no new models), with bonuses to max HP/MP/SP and DEF (fractions). Shown in Settings > Loadout and in this table. Owner kit/rules are untouched.
Weapon models: Beth's GLBs from /workspace/weapons are referenced where one fits; **they are not attached in-game yet** (attach offsets validated only on Garruk's and Nyx's rigs; each other hero needs its own grip offset). No character model changed or rescaled.

### Model needs for Beth (no weapon model yet)
${Object.entries(KITS).filter(([k, K]) => !K.weapon.glb).map(([k, K]) => '- ' + K.weapon.name + ' (' + k + '): ' + K.weapon.model).join('\n')}

## Open questions for the boss
1. Keep these ultimate names, or replace any?
2. Party members: auto-cast skills, or only the controlled hero?
3. Real buffs/summons (Raise Thrall, Turret, Wolf pet, mines) as a second phase?
4. Cost / cooldown pass after playtesting.
`;
fs.writeFileSync('/workspace/varn/HERO-ABILITIES.md', md); console.log('rows', rows.length);
