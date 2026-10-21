/* Ashen Titan lava visual-effect regression.
 * This constructs the ACTUAL THREE meshes used in the overworld, no WebGL
 * canvas required. Checks gameplay hazard definitions are not rewritten. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import * as THREE from '../www/proto3d/vendor/three.module.js';
import {makeVolcanoEffects} from '../www/proto3d/volcano-effects.js';
import {onLava,LAVA_POOLS,TITAN_CENTER,isCitySafe} from '../www/proto3d/bossregions.js';
const group=new THREE.Group();
const mat=new THREE.MeshLambertMaterial({emissive:0xe23b08,emissiveIntensity:1.25});
const poolMeshes=LAVA_POOLS.map(()=>({material:mat}));
const before=LAVA_POOLS.map(p=>({...p}));
const fx=makeVolcanoEffects({group,poolMeshes,heightAt:(x,z)=>12+.006*x+.002*z});
assert.equal(fx.counts.embers,128);
assert.equal(fx.counts.basalt,42);
assert.equal(fx.shards.count,42);
assert.equal(fx.embers.geometry.attributes.position.count,128);
assert.equal(fx.glowLights.length,2,'only two low-cost volcanic point lights');
assert(fx.glowLights.every(l=>l.castShadow===false),'no added shadow-map passes');
assert.equal(fx.group.name,'ashen-titan-volcano-environment');
assert.equal(fx.shards.name,'titan-basalt-rim-spires');
assert.equal(fx.embers.name,'titan-crater-floating-embers');
assert.equal(fx.embers.material.depthWrite,false);
assert(group.children.includes(fx.group));
assert(!fx.group.visible,'out-of-range volcano effects start culled');
assert(!fx.update(2,0,0),'never light up the protected village');
assert(!fx.active && fx.lastUpdate!==fx.lastUpdate,'far away does not update GPU particle data');
const original=fx.embers.geometry.attributes.position.array.slice();
assert(fx.update(2,TITAN_CENTER.x+80,TITAN_CENTER.z),'approaching Titan activates lava atmosphere');
assert(fx.active&&fx.group.visible);
assert.equal(fx.lastUpdate,2);
const result=fx.embers.geometry.attributes.position.array;
assert(result.some((n,i)=>n!==original[i]),'embers rise and drift around real lava pools');
assert(result.every(Number.isFinite),'all moving ember coordinates finite');
const intensity=mat.emissiveIntensity;
fx.update(4,TITAN_CENTER.x,TITAN_CENTER.z);
assert.notEqual(mat.emissiveIntensity,intensity,'lava glow pulses over time');
assert(mat.emissiveIntensity>=1.1 && mat.emissiveIntensity<=1.35,'lava emission stays phone-safe');
assert.equal(fx.shards.instanceMatrix.count,42*16);
assert.equal(fx.shards.instanceMatrix.array.every(Number.isFinite),true,'instanced basalt transforms remain valid');
assert(!fx.update(5,0,0));
assert.equal(fx.group.visible,false,'volcano ember batch culled outside encounter');
assert.deepEqual(LAVA_POOLS.map(p=>({...p})),before,'original lava hazards remain exactly unchanged');
assert(onLava(LAVA_POOLS[0].x,LAVA_POOLS[0].z),'lava is still dangerous where it was');
assert(!onLava(0,0)&&isCitySafe(0,0),'the city stays entirely safe');
const lands=readFileSync(new URL('../www/proto3d/townlands.js',import.meta.url),'utf8');
const main=readFileSync(new URL('../www/proto3d/main.js',import.meta.url),'utf8');
assert(lands.includes('makeVolcanoEffects({group,poolMeshes,heightAt:'),'effects are built into live world');
assert(lands.includes('updateVolcano')&&main.includes('TOWN_LANDS.updateVolcano?.(simTime,state.heroX,state.heroZ)'),'real frame update drives lava');
assert(!main.includes("TOWN_LANDS.updateVolcano?.(simTime);"),'volcano never runs without player position culling');
for(const p of ['www/proto3d/volcano-effects.js','www/proto3d/townlands.js','www/proto3d/main.js']){
 const check=spawnSync(process.execPath,['--check',p],{encoding:'utf8'});
 assert.equal(check.status,0,p+' parse failure '+check.stderr);
}
console.log('PASS volcanic basalt instancing, lava pulses, animated embers, phone draw-call budget, culling and unchanged lava hitboxes');
