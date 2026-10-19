# HERO ABILITIES - all 20 heroes (for boss review)

Generated from `www/proto3d/combat/herokits.js` on branch **hud-heroes** by `tools/gen_hero_table.mjs` (the code is the single source of truth). Skill format: name (move type, damage multiplier / effect, cooldown, cost). Damage multiplier x = multiple of the normal hit (UNARMED 28-48 x mult, crit rule unchanged); all damage is computed only in combat/calc.js. Animation comes later: casts reuse the existing attack clips.

## Rules
- Pad: Basic (big, spammable) + Skills 1-3 + Ultimate (needs 100 Fury, built by hits: +8 basic, +5 skill). Same layout for every hero; names / icons / ring colour come from the kit.
- Move types: melee (cone), aoe (ring), ranged (target), line (corridor), dash (move + corridor hit), blink (teleport to target + hit), heal, shield (guard), storm (3 ticks), meteor (delayed area, damage not instant-kill).
- Owner kit and rules are untouched: owner skills, saber, Holy/Unholy ultimates are gated by the owner account and never trusted from the UI. Non-owner heroes only ever use their own kit.
- Bosses (Ashen Titan etc.) take normal damage from kit ultimates; bossesInstantKill stays false.
- Buff-style moves (Battle Hymn, Totem of Wind, Overclock, Howl...) are approximated with guard/heal/stagger until real party buffs and summons exist (not built yet).

## Table
| # | Hero | Class | Colour | Basic | Skill 1 | Skill 2 | Skill 3 | Ultimate |
|---|---|---|---|---|---|---|---|---|
| 0 | Sir Aldric | Knight | #d9b44a | Shield Bash combo | Shield Bash (melee, x1.6 stagger, 4s, 15 SP) | Guardian Slam (aoe, x2.2 stagger, 8s, 25 SP) | Bulwark Charge (dash, x2.4 stagger, 12s, 30 SP) | **Lionheart Bulwark** (aoe, x4.5 shield 4s stagger, 100 Fury, 30s cd) | Steel Longsword (+5% dmg; model needed (procedural (aldric.js))) / Lionguard Plate (HP +20%, MP -, SP -, DEF +15%) |
| 1 | Darius Umbral | Dark Knight | #6a3d9a | Greatsword cleave | Shadow Cleave (line, x1.9, 4s, 15 SP) | Vampiric Grasp (melee, x2.2 heal 8% stagger, 8s, 25 MP) | Dark Armor (shield, guard 4s -50%, 12s, 25 MP) | **Eclipse Reaver** (aoe, x6 stagger, 100 Fury, 30s cd) | Shadow Greatsword (+8% dmg; model needed (procedural (heroes2.js))) / Umbral Plate (HP +15%, MP -, SP -, DEF +12%) |
| 2 | Selene Frostveil | Cryomancer | #9fe8ff | Ice shard | Frost Nova (aoe, x1.8 stagger, 4s, 15 MP) | Glacier Wall (shield, guard 3s -50%, 8s, 25 MP) | Blink Frost (blink, x2.2, 12s, 25 MP) | **Absolute Zero** (aoe, x5.5 stagger, 100 Fury, 30s cd) | Crystal Staff (+5% dmg; model needed (procedural (heroes2.js))) / Frostveil Robes (HP +5%, MP +20%, SP -, DEF +4%) |
| 3 | Lady Elira | Ranger | #5fbf6a | Quick-draw arrow | Aimed Shot (ranged, x1.8, 4s, 12 SP) | Piercing Arrow (line, x2.6, 8s, 20 MP) | Snare Trap (aoe, x1.2 stagger, 12s, 25 MP) | **Eagle-Eye Barrage** (storm, x6, 100 Fury, 30s cd) | Longbow (+6% dmg; model needed (none yet)) / Ranger Leathers (HP +8%, MP +5%, SP +10%, DEF +6%) |
| 4 | Orin Ashlance | Spearman | #d0a070 | Spear thrust | Sweep (melee, x1.8 stagger, 4s, 15 SP) | Vault Strike (dash, x2.4 stagger, 8s, 25 SP) | Phalanx Stance (shield, guard 4s -60%, 12s, 20 SP) | **Thousand Thrusts** (storm, x7, 100 Fury, 30s cd) | Ashlance Spear (+6% dmg; model needed (none yet)) / Ashplate Cuirass (HP +15%, MP -, SP +5%, DEF +12%) |
| 5 | Dame Seraphine | Paladin | #ffd86a | Mace swing | Sun Smite (line, x1.9, 4s, 15 MP) | Aegis Dash (dash, x2.3 stagger, 8s, 25 SP) | Consecrate (aoe, x2.2 heal 15%, 12s, 30 MP) | **Radiant Aegis** (aoe, x4.5 heal 30% shield 5s stagger, 100 Fury, 30s cd) | Holy Mace (+6% dmg; model: weapons/seraphine_holymace.glb) / Sunforged Armor (HP +18%, MP +5%, SP -, DEF +14%) |
| 6 | Talia Stormcall | Shaman | #59c3ff | Spark staff | Chain Lightning (ranged, x2.2, 4s, 15 MP) | Totem of Wind (shield, guard 4s -25%, 8s, 25 MP) | Static Field (aoe, x1.6 stagger, 12s, 30 MP) | **Tempest Call** (storm, x6.5, 100 Fury, 30s cd) | Storm Staff (+5% dmg; model needed (none yet)) / Stormcaller Garb (HP +5%, MP +18%, SP -, DEF +4%) |
| 7 | Finn Valecourt | Duelist | #e84a5f | Rapier lunges | Riposte (shield, guard 1.2s -90%, 4s, 12 SP) | Fleche Dash (dash, x2.6, 8s, 25 SP) | Feint (melee, x2 stagger, 12s, 20 SP) | **Thousand Cuts** (storm, x7, 100 Fury, 30s cd) | Duelist Rapier (+7% dmg; model: weapons/finn_rapier.glb (+ finn_parry_dagger.glb off-hand)) / Crimson Doublet (HP +6%, MP -, SP +15%, DEF +5%) |
| 8 | Brynn Cogwright | Engineer | #ffb03a | Repeater crossbow | Turret (storm, x2.2, 4s, 15 SP) | Mine Field (aoe, x2.4 stagger, 8s, 25 SP) | Overclock (shield, guard 4s -20%, 12s, 20 SP) | **Siege Cannon** (meteor, x8 r12, 100 Fury, 30s cd) | Repeater Crossbow (+6% dmg; model: weapons/brynn_repeater_crossbow.glb) / Cogwright Apron (HP +10%, MP -, SP +12%, DEF +8%) |
| 9 | Mirelle Thornroot | Druid | #7bd36a | Thorn lash | Entangle (aoe, x1.4 stagger, 4s, 15 MP) | Bloom (heal, heal 28%, 8s, 25 MP) | Wolf Dash (dash, x2.4, 12s, 25 SP) | **Grove Awakening** (aoe, x5 stagger, 100 Fury, 30s cd) | Thorn Sickle (+5% dmg; model: weapons/mirelle_sickle.glb) / Rootweave Vestments (HP +8%, MP +15%, SP -, DEF +5%) |
| 10 | Nyx Varrin | Rogue | #7a4bd0 | Twin dagger flurry | Dagger Flurry (storm, x2.4, 4s, 15 SP) | Shadow Step (blink, x2, 8s, 20 SP) | Poison Cut (melee, x2.6 stagger, 12s, 25 SP) | **Shadow Flurry** (storm, x7, 100 Fury, 30s cd) | Twin Daggers (+7% dmg; model: weapons/nyx_dagger.glb (R+L)) / Shadowsilk Leathers (HP +5%, MP -, SP +18%, DEF +5%) |
| 11 | Vesper Crowe | Witch Hunter | #b38b59 | Crossbow bolt | Hex Mark (ranged, x2, 4s, 12 SP) | Purge Flare (aoe, x1.8 stagger, 8s, 25 MP) | Hunter's Roll (dash, x2.2, 12s, 25 SP) | **Judgement Volley** (storm, x6, 100 Fury, 30s cd) | Silver Hand Crossbow (+6% dmg; model: weapons/hand_crossbow.glb) / Hunter Coat (HP +10%, MP -, SP +10%, DEF +8%) |
| 12 | Brother Thorne | Cleric | #f3f0d0 | Staff light bolt | Radiant Bolt (ranged, x1.8, 4s, 12 MP) | Mend (heal, heal 30%, 8s, 25 MP) | Holy Smite (aoe, x2.4 stagger, 12s, 30 MP) | **Divine Renewal** (aoe, x3 heal 60%, 100 Fury, 30s cd) | Radiant Spellbook (off-hand) (+4% dmg; model: weapons/spellbook.glb (off-hand)) / Vestments of Light (HP +6%, MP +20%, SP -, DEF +5%) |
| 13 | Rook Wildbane | Beastmaster | #8fae5a | Whip snare | Wolf Pounce (dash, x2, 4s, 15 SP) | Howl (aoe, x1.6 stagger, 8s, 25 SP) | Feral Mend (heal, heal 30%, 12s, 25 SP) | **Pack Stampede** (line, x6.5, 100 Fury, 30s cd) | Beastmaster Whip (+5% dmg; model: weapons/rook_whip.glb) / Wildbane Hides (HP +12%, MP -, SP +12%, DEF +8%) |
| 14 | Asha Ironfist | Monk | #ffcf5a | Palm combo | Dragon Kick (melee, x2 stagger, 4s, 15 SP) | Meditation Shield (shield, heal 15% guard 3s -50%, 8s, 25 MP) | Chi Burst (aoe, x2.2 stagger, 12s, 30 MP) | **Heaven's Fist** (meteor, x8 r8, 100 Fury, 30s cd) | Hand Wraps + Knuckles (+7% dmg; model: weapons/asha_knuckles.glb) / Saffron Gi (HP +10%, MP +5%, SP +12%, DEF +6%) |
| 15 | Rowan Firebrand | Mage | #ff7a2a | Firebolt | Firebolt (ranged, x2, 4s, 15 MP) | Flame Wave (melee, x2.4 stagger, 8s, 25 MP) | Ember Burst (aoe, x2.6 stagger, 12s, 30 MP) | **Meteor Burst** (meteor, x8 r10, 100 Fury, 30s cd) | Fire Staff (+5% dmg; model needed (none yet)) / Emberweave Robes (HP +4%, MP +20%, SP -, DEF +3%) |
| 16 | Kael Runebinder | Runemaster | #40c4ff | Rune bolt | Arc Rune (ranged, x2, 4s, 15 MP) | Ward Rune (aoe, x2.4 stagger, 8s, 25 MP) | Rune Swap (blink, x2, 12s, 25 MP) | **Runic Cataclysm** (aoe, x5.5 stagger, 100 Fury, 30s cd) | Rune Staff (+5% dmg; model needed (none yet)) / Runebound Coat (HP +6%, MP +18%, SP -, DEF +5%) |
| 17 | Cedric Vale | Bard | #e8a0d0 | Lute strum | Battle Hymn (shield, heal 10% guard 4s -25%, 4s, 15 MP) | Dissonance (melee, x2.2 stagger, 8s, 25 MP) | Encore (heal, heal 20%, 12s, 30 MP) | **Grand Crescendo** (aoe, x4.5 heal 30% stagger, 100 Fury, 30s cd) | Lute (+4% dmg; model needed (none yet)) / Minstrel Finery (HP +6%, MP +10%, SP +8%, DEF +4%) |
| 18 | Morwen Blackveil | Necromancer | #4de0a0 | Scythe sweep | Raise Thrall (ranged, x1.8, 4s, 15 MP) | Soul Drain (line, x2.4 heal 6%, 8s, 25 MP) | Bone Cage (aoe, x2 stagger, 12s, 30 MP) | **Legion of the Dead** (line, x6.5, 100 Fury, 30s cd) | Bone Scythe (+6% dmg; model: weapons/morwen_scythe.glb) / Blackveil Shroud (HP +6%, MP +16%, SP -, DEF +6%) |
| 19 | Garruk Stonefist | Berserker | #c0392b | Axe chop | Whirl Axe (aoe, x2, 4s, 15 SP) | Ground Pound (aoe, x2.4 stagger, 8s, 25 SP) | War Cry (shield, guard 4s -40%, 12s, 20 SP) | **Bloodstorm** (storm, x7, 100 Fury, 30s cd) | Stonefist Greataxe (+8% dmg; model: weapons/garruk_greataxe.glb) / Stonefist Harness (HP +22%, MP -, SP +5%, DEF +15%) |

## Weapon + armor kits
Data-driven in `herokits.js` (`weapon`, `armor` per hero). Weapon = signature weapon; `dmgPct` boosts NORMAL damage only (never the Owner's rules). Armor = the hero's EXISTING outfit (no new models), with bonuses to max HP/MP/SP and DEF (fractions). Shown in Settings > Loadout and in this table. Owner kit/rules are untouched.
Weapon models: Beth's GLBs from /workspace/weapons are referenced where one fits; **they are not attached in-game yet** (attach offsets validated only on Garruk's and Nyx's rigs; each other hero needs its own grip offset). No character model changed or rescaled.

### Model needs for Beth (no weapon model yet)
- Steel Longsword (aldric): procedural (aldric.js)
- Longbow (elira): none yet
- Fire Staff (rowan): none yet
- Lute (cedric): none yet
- Rune Staff (kael): none yet
- Storm Staff (talia): none yet
- Ashlance Spear (orin): none yet
- Crystal Staff (selene): procedural (heroes2.js)
- Shadow Greatsword (darius): procedural (heroes2.js)

## Open questions for the boss
1. Keep these ultimate names, or replace any?
2. Party members: auto-cast skills, or only the controlled hero?
3. Real buffs/summons (Raise Thrall, Turret, Wolf pet, mines) as a second phase?
4. Cost / cooldown pass after playtesting.
