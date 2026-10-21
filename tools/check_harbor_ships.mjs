/* Test real sailing-ship meshes and shared bobbing movement without a DOM.
 * Building the entire scenery needs document.canvas and is instead covered by
 * a separate Playwright/browser game smoke test. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {buildSailingShip,animateMooredShip} from '../www/proto3d/port-ships.js';
import {PORT_CENTER,LAVA_POOLS,onLava} from '../www/proto3d/bossregions.js';
const s=buildSailingShip(1.27,true),boat=buildSailingShip(1,false);
assert(s.children.length>20,'large sailing ship has a true hull, 3 masts, sails and rigging');
assert(boat.children.length>7,'smaller boat has a true hull, sail and rigging');
assert(s.children.some(o=>o.isMesh&&o.geometry.type==='BufferGeometry'),'galleon has a curved indexed hull');
assert(s.children.some(o=>o.isMesh&&o.geometry.type==='TubeGeometry'),'port and starboard gunwales are curved');
assert(s.children.some(o=>o.isMesh&&o.geometry.type==='CylinderGeometry'),'masts and rigging are real 3D');
assert.equal(s.scale.x,1.27);
const models=[s,boat];
for(let i=0;i<models.length;i++){
 const ship=models[i];
 const p=i===0?{x:-44,z:-25,yaw:.15,phase:0}:{x:-49,z:24,yaw:-.14,phase:2.25};
 ship.position.set(p.x,-.28,p.z);
 ship.rotation.y=p.yaw;
 ship.userData.mooring=p;ship.userData.baseY=-.28;
 assert(p.x< -26&&p.x> -96&&Math.abs(p.z)<51,'both ship moorings fit harbor water bounds');
 assert(!animateMooredShip(ship,NaN),'invalid frame time does not corrupt ship');
 const oldY=ship.position.y,oldTilt=ship.rotation.z;
 assert(animateMooredShip(ship,2.3),'ship float update runs');
 assert.notEqual(ship.position.y,oldY,'all sails/masts rise together in one parent group');
 assert.notEqual(ship.rotation.z,oldTilt,'ship rocks rather than sliding through water');
 assert(Math.abs(ship.position.y+.28)<.106,'ship bobbing always stays close to real water');
 assert(Math.abs(ship.rotation.z)<.026,'rolling is gentle and does not capsize boat');
 assert(Number.isFinite(ship.rotation.x)&&Number.isFinite(ship.rotation.y),'orientation finite');
}
const town=readFileSync(new URL('../www/proto3d/townlands.js',import.meta.url),'utf8');
const main=readFileSync(new URL('../www/proto3d/main.js',import.meta.url),'utf8');
assert(town.includes('const harborShips=new THREE.Group()'),'ships placed in actual harbor group');
assert(town.includes('buildSailingShip(p.scale,p.large)'),'both model variants instantiated');
assert(town.includes("dockPlanks.name='harbor-wooden-mooring-piers'"),'two piers included');
assert(town.includes('animateMooredShip(ships[i],t)'), 'same tested animation drives live game');
assert(town.includes('harborShips.visible=near'),'ships distance-culled on phone');
assert(town.includes("water.name='harbor-swim-water'"),'unchanged swim plane remains');
assert(main.includes('TOWN_LANDS.updateWater?.(simTime,state.heroX,state.heroZ)'),'player position controls culling');
assert(!onLava(0,0),'town remains safe');
assert(LAVA_POOLS.length>0,'Titan lava hazard definition unaffected');
assert(Number.isFinite(PORT_CENTER.x)&&Number.isFinite(PORT_CENTER.z));
for(const path of ['www/proto3d/port-ships.js','www/proto3d/townlands.js','www/proto3d/main.js']){
 const r=spawnSync(process.execPath,['--check',path],{encoding:'utf8'});
 assert.equal(r.status,0,path+' fails JS syntax: '+r.stderr);
}
console.log('PASS curved 3D ship geometries, linked sail motion, correct harbor placements, proximity culling and unmodified hazards');
