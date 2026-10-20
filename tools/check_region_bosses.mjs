// Regression checks for new Varnethryl overworld/frost bosses.
// Node --input-type=module / ESM: no THREE or DOM required for combat+scale contracts.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {HERO_M,CHARS,profileFor,loadScale} from '../www/proto3d/charscale.js';
import {ENEMIES,BOSS_PATTERNS} from '../www/proto3d/combat/data.js';
import {TITAN_LAIR,FROST_SUMMIT,BALTHRIX_ROUTE,balthrixPatrol,isTownSafe,wilderness} from '../www/proto3d/bossworld.js';
const f=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const main=f('www/proto3d/main.js'),lands=f('www/proto3d/townlands.js'),
      frost=f('www/proto3d/frostrealm.js'),fight=f('www/proto3d/fight.js'),
      walls=f('www/proto3d/buildings.js'),hud=f('www/proto3d/combat/hud.js');
assert.equal(HERO_M,1.905);
assert.equal(profileFor('n:frosttroll_a').height,HERO_M*3);
assert.equal(profileFor('n:frosttroll_b').height,HERO_M*3);
assert.equal(profileFor('n:ashentitan_40').height,HERO_M*40);
for(const x of [20,40,60])assert.equal(profileFor('n:ashentitan_'+x).height,x*HERO_M);
assert.equal(profileFor('n:ashentitan_new').height,6*HERO_M);
assert.equal(ENEMIES.titan.model,'n:ashentitan_40');
assert.equal(ENEMIES.vaelthryx.model,'n:vaelthryx_straight_rig');
for(const id of ['frostbrother_a','frostbrother_b']){
 assert.equal(ENEMIES[id].boss,true);assert.equal(ENEMIES[id].scale,3);
 assert.ok(BOSS_PATTERNS[id].length>=3);assert.ok(BOSS_PATTERNS[id].some(x=>x.phase===2));
}
assert.notDeepEqual(BOSS_PATTERNS.frostbrother_a.map(x=>x.id),BOSS_PATTERNS.frostbrother_b.map(x=>x.id));
assert.equal(TITAN_LAIR.x,-397);assert.equal(FROST_SUMMIT.z,-325);
assert.ok(BALTHRIX_ROUTE.length>=8);
for(const [x,z] of BALTHRIX_ROUTE)assert.ok(wilderness(x,z),'Balthrix must remain outside city '+x+','+z);
for(const seconds of [0,20,60,300,900]){
 const p=balthrixPatrol(seconds);assert.ok(Number.isFinite(p.x)&&Number.isFinite(p.z));
 assert.ok(!isTownSafe(p.x,p.z),'Balthrix crosses protected walls at '+seconds+': '+JSON.stringify(p));
}
assert.match(main,/buildWalls\(ectx, CITY_WALL_B, GATE_W\)/);
assert.match(main,/const EXTRA_SCALE = \{\}/,'Frost Troll B must not be shrunk twice');
assert.match(main,/EXTRA\.push\(\['n:ashentitan_' \+ factor/,'new Titan skin variants appended after save indices');
assert.match(main,/FM\.brothers/,'Frost Trolls start as a joint boss battle');
assert.match(main,/FROST_CAVE/,'summit cave portal');
assert.match(main,/FIGHT\.hurt\(100\)/,'lava must damage the player');
assert.match(fight,/overworldBosses\(dt\)/,'overworld encounters enabled');
assert.match(fight,/roamerAt\(overlandTime\)/,'Balthrix continuously patrols');
assert.match(fight,/env\.floorAt\?env\.floorAt\(e\.x,e\.z\)/,'monsters follow terrain elevation');
assert.match(lands,/mesh\.castShadow=true;mesh\.userData\.keep=true/,'mountain shadows and no flat-merge blackout');
assert.match(lands,/swimmable-corner-harbor/);
assert.match(frost,/frostbound-climbable-ice-terrain/);
assert.match(hud,/VARNETHRYL BATTLE ARTS/,'Varnethryl-themed skill HUD');
for(const p of ['www/proto3d/main.js','www/proto3d/fight.js','www/proto3d/townlands.js','www/proto3d/frostrealm.js','www/proto3d/buildings.js','www/proto3d/combat/hud.js']){
 const v=spawnSync(process.execPath,['--check',p],{encoding:'utf8'});
 assert.equal(v.status,0,p+' syntax failure: '+v.stderr);
}
console.log('PASS: 1.905m Owner, 3x Frost Troll brothers, 40x Ashen Titan (+6/20/60), Balthrix patrol, cave ice realm, lava, harbor swimming, medieval HUD, syntax.');
