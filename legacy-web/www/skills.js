// Varnethryl skill table. Data-driven: four slots (minor, heavy, superHeavy, ultimate).
// RESOLUTION ORDER: HERO_SKILLS[hero] override  >  CLASS_SKILLS[className] (minor/heavy/superHeavy)  >  DEFAULT_SKILLS.
// CLASS_SKILLS: shared class pools (below). ULTIMATES: one placeholder ultimate per hero (EDIT THE TABLE, search 'ULTIMATES').
// Until the design team writes the real skills, every hero uses the generic defaults below.
// To plug in a hero's skills, add an entry to HERO_SKILLS keyed by HEROES index (or hero name):
//   HERO_SKILLS[0] = { minor:{name:'Shield Bash',cd:4000,mult:1.5,range:110,icon:'<svg…>'}, heavy:{…}, superHeavy:{…}, ultimate:{…} };
// Any field you omit falls back to the default for that slot.
// Fields: name, cd (ms), mult (damage/heal multiplier), range (px), splash (px radius, 0 = single target),
//         act (animation timing key: minor|heavy|super|ult), charge (ultimate only: charge needed, default 100), icon (SVG markup or image URL).
import {HEROES} from './data.js';
import {profileFor} from './classmotion.js';
const svg=(p)=>`<svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${p}</svg>`;
export const ICONS={
  basic:svg('<path d="M5 19 17 7M14 5l5 0 0 5M5 19l-1 1M8 16l-2 2"/>'),
  minor:svg('<path d="M12 3l3 6 6 1-4.5 4.2L18 21l-6-3.4L6 21l1.5-6.8L3 10l6-1z"/>'),
  heavy:svg('<path d="M4 20 14 10M12 4l8 8M9 7l8 8"/><path d="M15 3l6 6"/>'),
  superHeavy:svg('<path d="M12 2v6M12 16v6M2 12h6M16 12h6M5 5l4 4M15 15l4 4M19 5l-4 4M9 15l-4 4"/><circle cx="12" cy="12" r="2"/>'),
  ultimate:svg('<path d="M12 2l2.6 6.9 7.4.4-5.8 4.6 2 7.1L12 17l-6.2 4 2-7.1L2 9.3l7.4-.4z"/>')};
export const SLOTS=['minor','heavy','superHeavy','ultimate'];
export const DEFAULT_SKILLS={
  minor:     {name:'Quick Skill', cd:4000,  mult:1.5, range:200, splash:0,   act:'minor', icon:ICONS.minor},
  heavy:     {name:'Heavy Strike',cd:8000,  mult:2.4, range:150, splash:0,   act:'heavy', icon:ICONS.heavy},
  superHeavy:{name:'Super Heavy', cd:15000, mult:4.2, range:170, splash:110, act:'super', icon:ICONS.superHeavy},
  ultimate:  {name:'Ultimate',    cd:0,     mult:8,   range:260, splash:170, act:'ult',   icon:ICONS.ultimate, charge:100}};

// ---- icon library (id -> svg). Real painted icons can replace these later by id. ----
const IC={
 shield:'<path d="M12 3 5 6v5c0 5 3 8 7 10 4-2 7-5 7-10V6z"/>',bash:'<path d="M12 3 5 6v5c0 5 3 8 7 10 4-2 7-5 7-10V6z"/><path d="M12 8v6M9 11h6"/>',
 sword:'<path d="M5 19 17 7M14 5l5 0 0 5M5 19l-1 1M8 16l-2 2"/>',slash:'<path d="M4 18C9 18 16 12 20 5M7 20c6 0 11-6 14-12"/>',
 spear:'<path d="M4 20 18 6M15 3l6 0 0 6-3-3z"/>',rapier:'<path d="M4 20 19 5M16 4l4 0 0 4M6 16l3 3"/>',dagger:'<path d="M6 18 15 9M13 5l6 0 0 6M5 19l-2 2"/>',
 fist:'<path d="M7 11V7a2 2 0 0 1 4 0v3M11 10V6a2 2 0 0 1 4 0v5M15 11V8a2 2 0 0 1 4 0v6c0 4-3 7-7 7s-6-3-6-6v-3a2 2 0 0 1 2-1z"/>',
 bow:'<path d="M6 3c8 3 8 15 0 18M6 3v18M6 12h14M16 8l4 4-4 4"/>',arrows:'<path d="M3 6h14M3 12h16M3 18h14M15 4l3 2-3 2M17 10l3 2-3 2M15 16l3 2-3 2"/>',
 crossbow:'<path d="M3 8c6 0 12 0 18 0M12 8v13M6 8l6 5 6-5"/>',gear:'<circle cx="12" cy="12" r="3"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"/>',
 flame:'<path d="M12 3c1 4 5 5 5 10a5 5 0 0 1-10 0c0-2 1-3 2-4 0 2 1 3 2 3 0-3-1-6 1-9z"/>',meteor:'<circle cx="16" cy="16" r="4"/><path d="M13 13 3 3M12 17 5 10M17 12 10 5"/>',
 frost:'<path d="M12 2v20M3.3 7l17.4 10M3.3 17 20.7 7M9 4l3 2 3-2M9 20l3-2 3 2"/>',skull:'<path d="M5 12a7 7 0 0 1 14 0c0 2-1 3-2 4v3H7v-3c-1-1-2-2-2-4z"/><circle cx="9.5" cy="12" r="1.3"/><circle cx="14.5" cy="12" r="1.3"/>',
 rune:'<path d="M12 3 20 9v8l-8 4-8-4V9z"/><path d="M12 8v8M9 11l3-3 3 3"/>',leaf:'<path d="M5 19C5 9 11 4 20 4c0 9-5 15-15 15zM5 19 14 10"/>',
 bolt:'<path d="M13 2 5 14h6l-1 8 8-12h-6z"/>',cross:'<path d="M12 4v16M4 12h16"/><circle cx="12" cy="12" r="9"/>',sun:'<circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2"/>',
 note:'<path d="M9 18V5l10-2v13"/><circle cx="7" cy="18" r="2.5"/><circle cx="17" cy="16" r="2.5"/>',paw:'<circle cx="7" cy="9" r="1.8"/><circle cx="11" cy="6" r="1.8"/><circle cx="15" cy="6" r="1.8"/><circle cx="19" cy="9" r="1.8"/><path d="M12 11c-3 0-5 3-5 5.5S9 20 12 19s5 1 5-2.5-2-5.5-5-5.5z"/>',
 axe:'<path d="M5 20 15 8M12 4c4-2 8 1 8 5-3 0-6-1-8-5zM11 8c0 4 3 6 6 7"/>',hammer:'<path d="M4 20 13 11M11 5l8 0 0 6-4 0-4-4z"/>',
 dark:'<path d="M4 20 18 6M15 3l6 0 0 6"/><path d="M19 14a6 6 0 1 1-6-6 5 5 0 0 0 6 6z"/>',wing:'<path d="M3 17c4 0 8-3 9-11 1 8 5 11 9 11-3 1-6 0-9-3-3 3-6 4-9 3z"/>',
 eye:'<path d="M2 12c4-6 16-6 20 0-4 6-16 6-20 0z"/><circle cx="12" cy="12" r="3"/>',net:'<path d="M3 3l18 18M21 3 3 21M3 12h18M12 3v18"/>',
 wisp:'<path d="M12 3c5 3 6 8 2 11-2 2-6 1-6-2 0-2 3-3 5-1M9 20c3 1 7 0 9-3"/>',star:'<path d="M12 2l2.6 6.9 7.4.4-5.8 4.6 2 7.1L12 17l-6.2 4 2-7.1L2 9.3l7.4-.4z"/>',
 ward:'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><path d="M12 3v18M3 12h18"/>',heart:'<path d="M12 20S4 15 4 9a4 4 0 0 1 8-1 4 4 0 0 1 8 1c0 6-8 11-8 11z"/>'};
export const ICON_IDS=Object.keys(IC);
export const iconSvg=id=>svg(IC[id]||IC.star);
// ---- class skill pools. Fields: name, cd (ms), mult, range (px), splash (px, 0=single), effect (damage|heal|buff|control|dash|summon), anim (motion family), fx (VFX id in classmotion.js), icon (icon id) ----
const K=(name,cd,mult,range,splash,effect,anim,fx,icon)=>({name,cd,mult,range,splash,effect,anim,fx,icon});
export const CLASS_SKILLS={
 Knight:{minor:K('Shield Bash',4200,1.5,105,0,'control','bash','ring_bash','bash'),heavy:K('Guardian Slam',8500,2.5,120,70,'damage','overhead','ring_gold','shield'),superHeavy:K('Bulwark Charge',15000,4.2,200,120,'dash','bash','ring_quake','shield')},
 Paladin:{minor:K('Smiting Strike',4000,1.5,110,0,'damage','slash','arc_gold','sun'),heavy:K('Consecrated Hammer',8500,2.4,120,80,'damage','overhead','ring_gold','hammer'),superHeavy:K('Judgment Nova',15500,4.0,160,170,'damage','bash','burst_holy','sun')},
 Berserker:{minor:K('Rending Cleave',3800,1.6,110,0,'damage','slash','arc_blood','axe'),heavy:K('Skullsplitter',8000,2.8,115,0,'damage','overhead','arc_big_blood','axe'),superHeavy:K('Earthshaker Roar',14500,4.4,150,150,'damage','overhead','ring_blood','fist')},
 'Dark Knight':{minor:K('Umbral Cut',4200,1.5,115,0,'damage','slash','arc_umbral','dark'),heavy:K('Soul Cleave',8800,2.6,125,90,'damage','overhead','arc_big_umbral','dark'),superHeavy:K('Abyssal Quake',15500,4.3,160,150,'damage','overhead','ring_umbral','skull')},
 Spearman:{minor:K('Piercing Jab',3600,1.4,150,0,'damage','thrust','line_steel','spear'),heavy:K('Sweeping Haft',8000,2.3,140,100,'damage','slash','arc_steel','spear'),superHeavy:K('Impaling Lunge',14500,4.2,220,60,'dash','thrust','line_big','spear')},
 Duelist:{minor:K('Quick Lunge',3200,1.5,150,0,'damage','thrust','line_silver','rapier'),heavy:K('Riposte',7500,2.4,125,0,'damage','thrust','line_big','rapier'),superHeavy:K('Flèche',13500,4.0,230,0,'dash','thrust','line_big','rapier')},
 Rogue:{minor:K('Backstab',3200,1.6,105,0,'damage','flurry','flurry_shadow','dagger'),heavy:K('Shadow Fan',7500,2.3,150,90,'damage','flurry','flurry_shadow','dagger'),superHeavy:K('Death Blossom',13500,4.0,140,130,'damage','flurry','flurry_big_shadow','wisp')},
 Monk:{minor:K('Palm Strike',3200,1.5,100,0,'damage','flurry','flurry_gold','fist'),heavy:K('Dragon Kick',7500,2.4,120,0,'damage','thrust','flurry_big_gold','fist'),superHeavy:K('Thousand Palms',14000,4.1,130,120,'damage','flurry','flurry_big_gold','fist')},
 Ranger:{minor:K('Aimed Shot',3600,1.5,300,0,'damage','draw','arrow_green','bow'),heavy:K('Piercing Arrow',8000,2.6,340,60,'damage','draw','arrow_volley','arrows'),superHeavy:K('Rain of Arrows',15000,4.2,320,170,'damage','draw','arrow_volley','arrows')},
 'Witch Hunter':{minor:K('Silver Bolt',3800,1.5,290,0,'damage','draw','bolt_blood','crossbow'),heavy:K('Hexbreaker',8200,2.6,260,0,'control','draw','bolt_big_blood','eye'),superHeavy:K('Purging Volley',15000,4.2,300,130,'damage','draw','bolt_big_blood','crossbow')},
 Engineer:{minor:K('Rivet Shot',3600,1.4,290,0,'damage','draw','bolt_brass','crossbow'),heavy:K('Snare Trap',8500,2.2,240,90,'control','draw','bolt_net','net'),superHeavy:K('Clockwork Barrage',15500,4.3,300,150,'damage','draw','bolt_brass','gear')},
 Beastmaster:{minor:K('Hunting Thrust',3600,1.4,140,0,'damage','thrust','line_wild','spear'),heavy:K('Call the Pack',8500,2.4,200,90,'summon','thrust','line_big_wild','paw'),superHeavy:K('Alpha Rampage',15000,4.1,210,130,'summon','thrust','line_big_wild','paw')},
 Mage:{minor:K('Firebolt',3600,1.6,300,0,'damage','cast','orb_fire','flame'),heavy:K('Flame Burst',8200,2.5,280,110,'damage','cast','orb_fire_big','flame'),superHeavy:K('Meteor',15500,4.5,320,160,'damage','cast','orb_meteor','meteor')},
 Cryomancer:{minor:K('Frost Lance',3600,1.5,300,0,'control','cast','shard_frost','frost'),heavy:K('Glacial Burst',8500,2.4,280,120,'control','cast','shard_big','frost'),superHeavy:K('Blizzard',15500,4.0,320,190,'control','cast','shards_ring','frost')},
 Necromancer:{minor:K('Hex Bolt',3800,1.5,290,0,'damage','cast','wisp_shadow','skull'),heavy:K('Wither',8500,2.4,270,100,'control','cast','wisp_big','wisp'),superHeavy:K('Grave Surge',15500,4.2,300,170,'damage','cast','wisp_big','skull')},
 Runemaster:{minor:K('Arc Rune',3600,1.5,290,0,'damage','cast','glyph_rune','rune'),heavy:K('Rune Lattice',8300,2.4,270,110,'control','cast','glyph_big','rune'),superHeavy:K('Runic Detonation',15500,4.3,300,170,'damage','cast','glyph_big','rune')},
 Druid:{minor:K('Thorn Lash',3600,1.4,280,0,'damage','cast','orb_leaf','leaf'),heavy:K('Rejuvenate',8500,2.2,260,0,'heal','cast','rays_heal','heart'),superHeavy:K('Entangling Grove',15000,3.9,300,170,'control','cast','burst_leaf','leaf')},
 Shaman:{minor:K('Spark',3400,1.4,290,0,'damage','cast','bolt_storm','bolt'),heavy:K('Spirit Ward',8500,2.2,260,0,'buff','cast','glyph_ward','ward'),superHeavy:K('Chain Lightning',15000,4.1,310,170,'damage','cast','burst_storm','bolt')},
 Cleric:{minor:K('Mend',3800,1.5,260,0,'heal','cast','rays_heal','cross'),heavy:K('Radiant Smite',8300,2.4,280,80,'damage','cast','rays_holy','sun'),superHeavy:K('Sanctuary',15500,3.8,260,170,'heal','cast','rays_big','cross')},
 Bard:{minor:K('Rousing Chord',4000,1.3,260,0,'buff','strum','notes_bard','note'),heavy:K('Discordant Note',8200,2.3,280,100,'damage','strum','notes_big','note'),superHeavy:K('Crescendo',15000,3.8,280,170,'buff','strum','notes_big','note')}};
// ---- PLACEHOLDER ULTIMATES: one per hero, keyed by hero id. >>> THE TEAM REPLACES THESE <<< Edit name/effect/fx/mult freely; keep placeholder:true until replaced.
// effect: damage|heal|buff|control|summon.  fx: any id from VFX in classmotion.js.  icon: id from ICON_IDS.
const U=(name,effect,fx,icon,mult,range,splash,desc)=>({name,effect,fx,icon,mult,range,splash,desc,cd:0,act:'ult',charge:100,placeholder:true});
export const ULTIMATES={
 0:{hero:'Sir Aldric',...U('Lionheart Bulwark','buff','ring_gold','shield',7,230,160,'Placeholder: golden shockwave that staggers nearby foes and fortifies the party.')},
 1:{hero:'Lady Elira',...U('Eagle-Eye Barrage','damage','arrow_volley','arrows',8,330,200,'Placeholder: rapid volley of piercing arrows.')},
 2:{hero:'Brother Thorne',...U('Divine Renewal','heal','rays_big','cross',7,260,200,'Placeholder: mass heal and cleanse.')},
 3:{hero:'Nyx Varrin',...U('Shadow Flurry','damage','flurry_big_shadow','dagger',8.5,170,140,'Placeholder: teleporting dagger flurry.')},
 4:{hero:'Rowan Firebrand',...U('Meteor Burst','damage','orb_meteor','meteor',9,330,220,'Placeholder: giant meteor impact.')},
 5:{hero:'Dame Seraphine',...U('Radiant Aegis','buff','burst_holy','sun',6.5,240,180,'Placeholder: holy aegis shielding the party.')},
 6:{hero:'Garruk Stonefist',...U('Bloodstorm','damage','ring_blood','axe',9,180,190,'Placeholder: whirling axe storm.')},
 7:{hero:'Mirelle Thornroot',...U('Wildgrowth','heal','burst_leaf','leaf',6.5,280,210,'Placeholder: bloom that heals allies and roots foes.')},
 8:{hero:'Cedric Vale',...U('Battle Hymn','buff','notes_big','note',6,280,220,'Placeholder: party-wide damage and energy buff.')},
 9:{hero:'Morwen Blackveil',...U('Soul Reap','damage','wisp_big','skull',8.5,300,200,'Placeholder: drains souls from all nearby foes.')},
 10:{hero:'Kael Runebinder',...U('Runic Cascade','damage','glyph_big','rune',8.5,300,210,'Placeholder: chain of detonating runes.')},
 11:{hero:'Vesper Crowe',...U('Witchbane Volley','damage','bolt_big_blood','crossbow',8,320,180,'Placeholder: silver bolts that silence casters.')},
 12:{hero:'Talia Stormcall',...U('Thunder Totem','damage','burst_storm','bolt',8,310,210,'Placeholder: totem calling repeated lightning.')},
 13:{hero:'Orin Ashlance',...U('Impaling Charge','damage','line_big','spear',8.5,260,100,'Placeholder: long charge through a line of foes.')},
 14:{hero:'Selene Frostveil',...U('Frozen Tempest','control','shards_ring','frost',8,320,230,'Placeholder: blizzard that freezes foes.')},
 15:{hero:'Darius Umbral',...U('Abyssal Cleave','damage','arc_big_umbral','dark',9,200,170,'Placeholder: giant dark greatsword cleave.')},
 16:{hero:'Finn Valecourt',...U('Perfect Riposte','damage','line_big','rapier',8.5,200,0,'Placeholder: counter-strike combo on a single foe.')},
 17:{hero:'Brynn Cogwright',...U('Clockwork Blast','damage','bolt_brass','gear',8.5,320,200,'Placeholder: deployed turret barrage.')},
 18:{hero:'Asha Ironfist',...U('Hundred Fists','damage','flurry_big_gold','fist',9,150,150,'Placeholder: hundred-hit fist barrage.')},
 19:{hero:'Rook Wildbane',...U('Wolfpack Rush','summon','line_big_wild','paw',8,260,190,'Placeholder: pack of spectral wolves charges.')}};
// HERO_SKILLS holds ONLY each hero's unique ultimate (generated from the ULTIMATES table). Add other slots here only for deliberate one-off hero overrides.
export const HERO_SKILLS=Object.fromEntries(Object.entries(ULTIMATES).map(([id,u])=>{const {hero,...rest}=u;return[id,{ultimate:rest}]}));
const norm=o=>{if(!o)return o;const r={...o};if(r.icon&&!/^<|\//.test(r.icon)&&!/\.(png|webp|svg)$/.test(r.icon))r.iconId=r.icon,r.icon=iconSvg(r.icon);return r};
const ANIM2ACT={minor:'minor',heavy:'heavy',superHeavy:'super',ultimate:'ult'};
export function resolve(heroId,heroName){const h=HEROES[heroId],cls=CLASS_SKILLS[h&&h.className]||{},o=HERO_SKILLS[heroId]||HERO_SKILLS[heroName]||{},r={};
  for(const s of SLOTS){const src=norm(o[s])||(s==='ultimate'?null:norm(cls[s]));r[s]={...DEFAULT_SKILLS[s],act:ANIM2ACT[s]||DEFAULT_SKILLS[s].act,effect:'damage',...(src||{}),source:o[s]?'hero':src?'class':'default'};
    if(s==='ultimate'&&!r[s].anim)r[s].anim=(h&&profileFor(h.id).fam)||'slash'}
  return r}
