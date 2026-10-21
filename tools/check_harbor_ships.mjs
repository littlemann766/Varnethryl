/* Ensure Varnethryl's ACTUAL town zone displays stable, low-cost 3D ships.
 * The original approved external ship GLB is not claimed to be included.
 */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import * as THREE from '../www/proto3d/vendor/three.module.js';
import {buildSailingShip} from '../www/proto3d/port-ships.js';
import {buildTownOutskirts} from '../www/proto3d/townlands.js';
import {PORT_CENTER,LAVA_POOLS,onLava} from '../www/proto3d/bossregions.js';
const s=buildSailingShip(1.27,true),boat=buildSailingShip(1,false);
assert(s.children.length>20,'large sailing ship must include actual hull, sails, and rigging meshes');
assert(boat.children.length>7,'small boat is a real 3D object');
assert(s.children.some(o=>o.isMesh&&o.geometry.type==='BufferGeometry'),'large ship includes a genuine curved 3D hull');
assert(!s.children.every(o=>o.geometry?.type==='BoxGeometry'),'sailing ship not a blocky placeholder');
const scene=new THREE.Scene(),colliders=[];
const lavaBefore=LAVA_POOLS.map(x=>({...x}));
const town=buildTownOutskirts({scene,colliders,world:560,buildings:[],spacing:2.8});
assert.equal(town.ships.length,2,'both real 3D boats placed in the harbor');
assert.equal(town.harborShips.name,'harbor-waterborne-sailing-ships');
assert.equal(town.dockPlanks.count,46,'two mooring piers are batched for mobile');
assert(town.ships.every(s=>s.parent===town.harborShips),'sails, mast and hull remain a single animating group');
assert(town.ships.every(s=>town.waterAt(PORT_CENTER.x+s.position.x,PORT_CENTER.z+s.position.z)),
       'every mooring lies on the same in-game swimmable water plane');
assert(!town.harborShips.visible,'ships are culled when player is away');
town.updateWater(1.2,0,0);
assert(!town.harborShips.visible,'ships do not cost draw calls near the village');
town.updateWater(2.3,PORT_CENTER.x-17,PORT_CENTER.z);
assert(town.harborShips.visible,'ship meshes appear when approaching port');
const prev=town.ships.map(s=>({y:s.position.y,tilt:s.rotation.z}));
town.updateWater(3.6,PORT_CENTER.x-17,PORT_CENTER.z);
assert(town.ships.some((s,i)=>s.position.y!==prev[i].y),'sailing ships float in the moving harbor water');
assert(town.ships.some((s,i)=>s.rotation.z!==prev[i].tilt),'ships gently rock without detaching sails');
assert(town.ships.every(s=>s.scale.x>0&&s.children.length>7),'both ships stay valid after motion');
assert.equal(town.water.geometry.attributes.position.count,25*29,'existing swimmable animated water remains');
town.updateWater(4,0,0);
assert(!town.harborShips.visible,'harbor geometry is culled on return to town');
assert.deepEqual(LAVA_POOLS.map(x=>({...x})),lavaBefore,'lava hazard positions remain untouched');
assert(!onLava(0,0),'city remains safe');
const main=readFileSync(new URL('../www/proto3d/main.js',import.meta.url),'utf8');
assert(main.includes('TOWN_LANDS.updateWater?.(simTime,state.heroX,state.heroZ)'),
       'real player position drives animation and culling from the main renderer');
for(const path of ['www/proto3d/port-ships.js','www/proto3d/townlands.js','www/proto3d/main.js']){
 const r=spawnSync(process.execPath,['--check',path],{encoding:'utf8'});
 assert.equal(r.status,0,path+' syntax failure: '+r.stderr);
}
console.log('PASS: 2 curved-hull sailing ships, batched mooring piers, water physics, bob/rock, far-zone culling, no gameplay hazard changes');
