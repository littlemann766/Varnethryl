/* Edit this catalogue to add future characters without changing the game engine. */
export const HEROES = [
 ['Sir Aldric','Knight','Tank',9,10,4,2,'Longsword','Broadsword, Mace, Warhammer','Lionheart Crest','Shieldbreaker','melee'],
 ['Lady Elira','Ranger','Ranged DPS',4,5,10,3,'Longbow','Shortbow, Recurve Bow, Crossbow','Eagle-Eye Quiver','Piercing Volley','ranged'],
 ['Brother Thorne','Cleric','Healer',3,6,4,9,'Holy Staff','Mace, Scepter, Wand','Sacred Reliquary','Divine Renewal','heal'],
 ['Nyx Varrin','Rogue','Assassin',5,4,10,4,'Dual Daggers','Shortsword, Throwing Knives','Shadowfang Emblem','Shadow Flurry','melee'],
 ['Rowan Firebrand','Mage','Spellcaster',2,3,5,10,'Fire Staff','Wand, Spellbook, Scepter','Emberheart Crystal','Meteor Burst','mage'],
 ['Dame Seraphine','Paladin','Vanguard Support',8,9,4,6,'Holy Mace','Warhammer, Sword, Flail','Divine Sunstone','Radiant Aegis','tank'],
 ['Garruk Stonefist','Berserker','Melee DPS',10,6,5,1,'Greataxe','Greatsword, Dual Axes, Maul','Bloodrage Totem','Bloodstorm','melee'],
 ['Mirelle Thornroot','Druid','Summoner',3,5,6,10,'Nature Staff','Totem, Wand, Sickle','Heartwood Seed','Wildgrowth','heal'],
 ['Cedric Vale','Bard','Buffer',4,4,7,8,'Enchanted Lute','Harp, Flute, Rapier','Harmonic Pendant','Battle Hymn','support'],
 ['Morwen Blackveil','Necromancer','Debuffer',2,4,5,10,'Skull Staff','Scepter, Ritual Dagger, Tome','Soulbound Phylactery','Soul Reap','mage'],
 ['Kael Runebinder','Runemaster','Arcane Utility',3,5,4,10,'Rune Staff','Runic Wand, Spellbook','Ancient Rune Core','Runic Cascade','mage'],
 ['Vesper Crowe','Witch Hunter','Anti-Mage',5,5,8,2,'Crossbow','Daggers, Hand Crossbow, Sword','Witchbane Sigil','Witchbane Volley','ranged'],
 ['Talia Stormcall','Shaman','Elemental Support',3,4,6,9,'Storm Staff','Totem, Ritual Mace','Spiritbound Charm','Thunder Totem','support'],
 ['Orin Ashlance','Spearman','Reach Fighter',7,7,6,1,'Spear','Pike, Halberd, Javelin','Warlord’s Pennant','Impaling Charge','melee'],
 ['Selene Frostveil','Cryomancer','Control Mage',2,4,5,10,'Ice Staff','Frost Wand, Scepter, Spellbook','Eternal Frost Crystal','Frozen Tempest','mage'],
 ['Darius Umbral','Dark Knight','Bruiser Tank',9,8,4,4,'Dark Greatsword','Great Axe, Cursed Blade','Umbral Seal','Abyssal Cleave','tank'],
 ['Finn Valecourt','Duelist','Precision DPS',5,4,9,2,'Rapier','Sabre, Estoc, Shortsword','Champion’s Insignia','Perfect Riposte','melee'],
 ['Brynn Cogwright','Engineer','Trap Utility',4,6,6,5,'Mechanical Crossbow','Repeater, Hand Crossbow, Traps','Arcane Gear Core','Clockwork Blast','ranged'],
 ['Asha Ironfist','Monk','Martial Striker',7,5,9,3,'Hand Wraps','Knuckles, Bo Staff, Claws','Iron Spirit Beads','Hundred Fists','melee'],
 ['Rook Wildbane','Beastmaster','Companion Tactician',6,6,7,3,'Hunting Spear','Bow, Hunting Knife, Short Spear','Alpha Fang Charm','Wolfpack Rush','ranged']
].map((a,id)=>({id,name:a[0],className:a[1],role:a[2],str:a[3],def:a[4],agi:a[5],mag:a[6],weapon:a[7],alternates:a[8].split(', '),relic:a[9],skill:a[10],style:a[11],image:`assets/heroes/${id}.webp`,sprite:`assets/sprites/${id}.png`}));

export const ZONES = [
 {id:'village',name:'Liongate Village',subtitle:'Guild headquarters · Safe haven',level:1,kind:'safe',portal:{right:'forest'},color:'#3c7054'},
 {id:'forest',name:'Whispering Wilds',subtitle:'Wolves, thieves and forgotten trails',level:1,kind:'wild',portal:{left:'village',right:'ruins'},color:'#244b3c'},
 {id:'ruins',name:'Ashen Ruins',subtitle:'Ancient soldiers and forbidden magic',level:6,kind:'ruins',portal:{left:'forest',right:'boss'},color:'#55505a'},
 {id:'boss',name:'The Titan Vault',subtitle:'Dungeon boss encounter · High-level challenge',level:20,kind:'boss',portal:{left:'ruins'},color:'#4b3543'}
];
export const TIERS=[
 {at:0,name:'Uncommon',color:'#a8b2be',slots:0},
 {at:3,name:'Rare',color:'#439ff3',slots:2},
 {at:6,name:'Epic',color:'#bc7af0',slots:3},
 {at:9,name:'Mythic',color:'#48d6c5',slots:4},
 {at:12,name:'Legendary',color:'#f0b64e',slots:5},
 {at:15,name:'Masterwork',color:'#f15d67',slots:5}
];
export const SUBSTAT_POOL=[
 {id:'hp',name:'Max HP',suffix:'%',min:1,max:6,step:.42,cap:12},
 {id:'crit',name:'Critical Chance',suffix:'%',min:.7,max:3.5,step:.22,cap:7},
 {id:'critDmg',name:'Critical Damage',suffix:'%',min:2,max:8,step:.65,cap:16},
 {id:'speed',name:'Attack Speed',suffix:'%',min:1,max:5,step:.4,cap:11},
 {id:'dodge',name:'Dodge Chance',suffix:'%',min:.5,max:2.5,step:.21,cap:5},
 {id:'lifesteal',name:'Life Steal',suffix:'%',min:.2,max:1.4,step:.12,cap:3},
 {id:'reduction',name:'Damage Reduction',suffix:'%',min:.5,max:2.5,step:.2,cap:5},
 {id:'cooldown',name:'Cooldown Reduction',suffix:'%',min:.5,max:3,step:.25,cap:6}
];
export const ABILITIES=[
 {id:'flame',name:'Flame Touch',desc:'Occasionally inflict burning damage.',tag:'burn'},
 {id:'frost',name:'Frost Touch',desc:'Occasionally slow an enemy.',tag:'slow'},
 {id:'vampiric',name:'Vampiric Touch',desc:'Occasionally restore HP on hit.',tag:'heal'},
 {id:'lucky',name:'Lucky Strike',desc:'Occasionally deal bonus damage.',tag:'crit'},
 {id:'guardian',name:'Guardian',desc:'Occasionally shield an ally.',tag:'shield'},
 {id:'quickstep',name:'Quickstep',desc:'Occasionally gain attack speed.',tag:'haste'},
 {id:'arcane',name:'Arcane Surge',desc:'Occasionally accelerate special abilities.',tag:'cooldown'},
 {id:'iron',name:'Iron Skin',desc:'Occasionally reduce incoming damage.',tag:'defense'},
 {id:'second',name:'Second Wind',desc:'Occasionally recover HP when low.',tag:'healing'},
 {id:'treasure',name:'Treasure Hunter',desc:'Small bonus chance for PvE loot.',tag:'loot'}
];
export const WEAPON_ART={0:0,1:1,2:2,3:3,4:4,5:5,6:6,7:7,8:8,9:9,10:13,11:3,12:10,13:11,14:10,15:6,16:12,17:1,18:3,19:11};
export const ENEMIES={
 forest:[{name:'Wild Wolf',hp:1050,attack:54,xp:60,gold:36,color:'#ad9987'},{name:'Forest Raider',hp:1450,attack:74,xp:90,gold:60,color:'#d59066'},{name:'Vine Wraith',hp:1700,attack:86,xp:120,gold:78,color:'#75bca1'}],
 ruins:[{name:'Ash Skeleton',hp:8400,attack:340,xp:230,gold:240,color:'#b8c6b6'},{name:'Rune Sentinel',hp:15500,attack:540,xp:380,gold:390,color:'#829db6'}],
 boss:[{name:'The Ashen Titan',hp:250000,attack:2100,xp:2400,gold:5200,color:'#d9787d',boss:true}]
};
