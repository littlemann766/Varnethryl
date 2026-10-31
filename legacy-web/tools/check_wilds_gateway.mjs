import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {MOUNTAIN_WILDS_GATE as gate,MOUNTAIN_WILDS_RETURN as back,
 MOUNTAIN_APPROACH,nearMountainWildsGate} from '../www/proto3d/wilds-gateway.js';
import {CITY_HALF,FROST_SUMMIT,FROST_PORTAL,TITAN_CENTER,PORT_CENTER} from '../www/proto3d/bossregions.js';
const load=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
assert(Math.abs(gate.x)>CITY_HALF+25 && Math.abs(gate.z)>CITY_HALF+25,
 'mountain gate belongs beyond the protected town walls');
assert(Math.hypot(gate.x+386,gate.z+292)<100,'gateway must use the northwest existing mountain terrain');
assert(Math.hypot(gate.x-FROST_SUMMIT.x,gate.z-FROST_SUMMIT.z)>180,
 'mountain Wilds cave must not cut into the Frost Troll summit');
assert(Math.hypot(gate.x-TITAN_CENTER.x,gate.z-TITAN_CENTER.z)>190);
assert(Math.hypot(gate.x-PORT_CENTER.x,gate.z-PORT_CENTER.z)>190);
assert(nearMountainWildsGate(gate.x,gate.z) && !nearMountainWildsGate(0,0),
 'proximity test only triggers inside the mountain cave');
assert(Math.hypot(back.x-gate.x,back.z-gate.z)>8,'return spawn must not immediately re-enter portal');
assert(MOUNTAIN_APPROACH.length>=5 && MOUNTAIN_APPROACH.at(-1)[0]>gate.x,
 'town approach must connect to westward mountain entrance');
const town=load('www/proto3d/townlands.js'),wilds=load('www/proto3d/wilds.js'),
 game=load('www/proto3d/main.js'),builder=load('www/proto3d/wilds-gateway.js');
assert(town.includes('buildMountainWildsGateway(group,(x,z)=>townElevation(x,z,world))'),
 'mountain ruins must use physical walkable terrain height');
assert(town.includes('const brokenSealRoad=path(MOUNTAIN_APPROACH'),
 'a terrain following road must connect the mountain gate to the town road');
assert(town.includes('!nearBrokenSealPath(x,z,pad)'),
 'props must not clutter the walkable mountain approach');
assert(wilds.includes('buildWildsReturnRuins(grp,ox-6,oz-2)'),'Wilds must contain an actual return shrine');
assert(game.includes('mountainWildsPortal=m.makePortal('),'mountain cave portal must exist at runtime');
assert(game.includes("lastWildsEntrance=isMountainWilds?'mountain':'town'"),'returns must track which route the player used');
assert(game.includes("lastWildsEntrance==='mountain'?MOUNTAIN_WILDS_RETURN.x"),'mountain returns must be physically separated');
assert(game.includes("isFrostCave?FROST_PORTAL:isMountainWilds?MOUNTAIN_WILDS_GATE:TOWN_PORTAL"),
 'Frost and original town portals must remain usable');
assert(builder.includes('mountain-cave-rock-shell') && builder.includes('broken-seal-ruin-pillar'),
 'a genuine rock-shelled ruin entrance and chamber are required');
for(const p of ['www/proto3d/wilds-gateway.js','www/proto3d/wilds.js',
 'www/proto3d/main.js','www/proto3d/townlands.js']) {
 const result=spawnSync(process.execPath,['--check',p],{encoding:'utf8'});
 assert.equal(result.status,0,p+' syntax error: '+result.stderr);
}
console.log('PASS: mountain ruin chamber, terrain-following road, collision-safe Wilds exit and all legacy portal links');
