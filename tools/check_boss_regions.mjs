// Varnethryl boss-region lore, size, encounter and geography checks (Node-only).
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {HERO_M,HERO_LORE_HEIGHTS,inchesToMeters,CHARS,profileFor,loadScale} from '../www/proto3d/charscale.js';
import {BOSS_PATTERNS,ENEMIES} from '../www/proto3d/combat/data.js';
import {pickPattern} from '../www/proto3d/combat/ai.js';
import {CITY_HALF,TITAN_CENTER,FROST_SUMMIT,FROST_REALM,FROST_PORTAL,LAVA_POOLS,PORT_CENTER,isCitySafe,balthrixPosition,onLava,frostHill,lavaAmount} from '../www/proto3d/bossregions.js';
const src=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const close=(a,b)=>Math.abs(a-b)<1e-8;
assert(close(HERO_M,1.905),'Owner must be 1.905 m');
assert.equal(Object.keys(HERO_LORE_HEIGHTS).length,20,'all 20 established heroes need lore heights');
for(const [id,inch] of Object.entries(HERO_LORE_HEIGHTS)){
 assert(close(profileFor(id).height,inchesToMeters(inch)),'lore height '+id);
 assert(close(loadScale(id,1.8)*1.8,inchesToMeters(inch)),'uniform scale '+id);
 assert(close(loadScale('n:'+id+'_smooth',1.8)*1.8,inchesToMeters(inch)),'smooth skin scale '+id);
}
for(const id of ['n:owner','n:owner_pika1'])assert(close(profileFor(id).height,HERO_M),'Owner skin remains 1.905 m');
for(const id of ['n:frosttroll_a','n:frosttroll_b']){
 assert(close(profileFor(id).height,3.5*HERO_M),id+' must equal 3x Owner');
 assert(close(loadScale(id,11.4)*11.4,3.5*HERO_M),'model height normalized for '+id);
}
for(const [id,mul] of [['n:ashentitan_new',6],['n:ashentitan_20',15],['n:ashentitan_40',15],['n:ashentitan_60',60],['n:vaelthryx_straight_rig',10],['n:vaelthryx_straight_rig_50',50]])
 assert(close(profileFor(id).height,mul*HERO_M),id+' height ratio');
assert(close(profileFor('n:ashentitan_20').height,28.575),'Active lava boss stands 28.575 m');
for(const [id,model] of [['titan40','n:ashentitan_20'],['frosttroll_a','n:frosttroll_a'],['frosttroll_b','n:frosttroll_b'],['vaelthryx','n:vaelthryx_straight_rig']]){
 assert.equal(ENEMIES[id].model,model,'encounter GLB for '+id);
 assert(ENEMIES[id].boss&&BOSS_PATTERNS[id]?.length>=3,'unique combat skills for '+id);
 const e={key:id,def:ENEMIES[id],phase:1,patI:0};
 const k=pickPattern(e);assert(k&&k.name&&k.reach&&k.tele,'attack pattern selected for '+id);
}
assert.equal(CITY_HALF,185,'town walls remain close');
assert.equal(FROST_SUMMIT.height,60,'steep but walkable mountain summit');
assert(frostHill(FROST_PORTAL.x,FROST_PORTAL.z)>59,'frost cave on summit');
assert(frostHill(0,-200)<5,'graded mountain foot');
assert(onLava(TITAN_CENTER.x,TITAN_CENTER.z),'lava pools surround 40x Titan');
assert(lavaAmount(TITAN_CENTER.x,TITAN_CENTER.z)>.95,'volcano terrain covers boss');
assert(!isCitySafe(TITAN_CENTER.x,TITAN_CENTER.z)&&!isCitySafe(FROST_SUMMIT.x,FROST_SUMMIT.z),'both boss regions outside city');
assert(FROST_REALM.cx>1500&&FROST_REALM.half>200,'new separated icy map');
let roamerVisitsVolcano=false;
for(let t=0;t<900;t+=.5){
 const p=balthrixPosition(t);
 assert(!isCitySafe(p.x,p.z),'Balthrix never enters protected city walls');
 if(Math.hypot(p.x-TITAN_CENTER.x,p.z-TITAN_CENTER.z)<32)roamerVisitsVolcano=true;
}
assert(roamerVisitsVolcano,'Balthrix patrol crosses Titan lava region');
const main=src('www/proto3d/main.js'),terrain=src('www/proto3d/townlands.js'),ice=src('www/proto3d/frostreach.js'),fight=src('www/proto3d/fight.js'),hud=src('www/proto3d/combat/hud.js');
assert(main.includes("setZone(ZONE.name==='town'?(isFrostCave?'frost':'wilds'):'town')"),'bidirectional ice cave portal wired');
assert(main.includes('TOWN_LANDS.updateWater?.(simTime)'),'water animation runs');
assert(main.includes('state.swimming'),'hero can swim');
assert(terrain.includes('mesh.castShadow=true')&&terrain.includes('mesh.receiveShadow=true'),'hills cast and receive shadows');
assert(terrain.includes("water.name='harbor-swim-water'"),'water available at port');
assert(ice.includes("ground.castShadow")===false||ice.includes("terrain.castShadow=true"),'ice mountains cast shadows');
assert(ice.includes("frosttroll_b")===false||ice.includes('FROST_BROTHERS'),'ice realm uses both brothers');
assert(fight.includes('startRegionBosses'),'automatic boss spawning at frost');
assert(fight.includes('balthrixPosition(regionClock+(roamer.routePhase||0))'),'roaming Balthrix follows phased patrol');
assert(hud.includes('VARNETHRYL ⚜')&&hud.includes("this.slotAbility"),'Varnethryl HUD retains real combat controls');
for(const p of ['bossregions.js','frostreach.js','townlands.js','main.js','fight.js','charscale.js','combat/data.js','combat/hud.js']){
 const f='www/proto3d/'+p,v=spawnSync(process.execPath,['--check',f],{encoding:'utf8'});
 assert.equal(v.status,0,f+' syntax: '+v.stderr);
}
console.log('PASS: Lore scale / 40x Titan / 3x frost brothers / 10x & 50x Balthrix / lava / mountain portal / icy realm / boss skills / roaming / swimming / HUD / shadows.');
