/* Build the real Frost Cave geometry in Node and validate collision/layout.
 * The visual browser/Android playtest remains a separate release gate. */
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {readFileSync} from 'node:fs';
import * as THREE from '../www/proto3d/vendor/three.module.js';
import {buildFrostCave} from '../www/proto3d/frost-cave.js';
import {FROST_REALM} from '../www/proto3d/bossregions.js';
const group=new THREE.Group(),half=FROST_REALM.half;
const exclusions=[{x:-7,z:155,r:38},{x:-7,z:177,r:25},{x:-37,z:-66,r:31},{x:37,z:-66,r:31}];
const cave=buildFrostCave(group,half,()=>0,exclusions);
assert.equal(cave.roof.name,'enclosing-ice-cave-vault');
assert.equal(cave.walls.name,'cave-outer-walls');
assert.equal(cave.stalagmites.count,105);
assert.equal(cave.icicles.count,165);
assert.equal(cave.crystals.count,76);
assert.equal(cave.lights.length,5,'keep phone lighting budget fixed at five');
assert.equal(cave.lights.filter(l=>l.castShadow).length,0,'no additional shadow-map pass for ice lights');
assert(cave.lights.some(l=>Math.hypot(l.position.x-(-37),l.position.z-(-66))<20),'older troll arena illuminated');
assert(cave.lights.some(l=>Math.hypot(l.position.x-37,l.position.z-(-66))<20),'younger troll arena illuminated');
assert(cave.lights.some(l=>Math.hypot(l.position.x-(-7),l.position.z-177)<20),'portal exit illuminated');
assert.equal(cave.motes.name,'frost-cave-airborne-ice-motes');
assert.equal(cave.motes.geometry.attributes.position.count,168,'one draw-call dust particle budget');
assert.equal(cave.motes.material.depthWrite,false);
assert.equal(cave.motes.castShadow,false);
assert(group.children.includes(cave.motes));
assert(cave.colliders.length>0,'ice formations have real collision');
for(const c of cave.colliders){
 assert.equal(c.type,'circle');
 assert(Number.isFinite(c.x)&&Number.isFinite(c.z)&&Number.isFinite(c.r)&&c.r>0);
 assert(!exclusions.some(p=>Math.hypot(p.x-c.x,p.z-c.z)<p.r+c.r),'boss or portal clearance');
 assert(!(Math.abs(c.x)<30+c.r&&c.z>-120-c.r&&c.z<194+c.r),'walking spine remains clear');
}
const before=cave.motes.position.y;cave.update(4.5);
assert.notEqual(cave.motes.position.y,before,'ice particles animate');
assert(Number.isFinite(cave.crystals.material.emissiveIntensity),'crystal glow remains finite');
assert.equal(cave.motes.geometry.attributes.position.count,168,'no per-frame geometry allocations');
const realm=readFileSync(new URL('../www/proto3d/frostreach.js',import.meta.url),'utf8');
assert(realm.includes('cave.update(t);'),'world renderer drives frost ambience');
assert(realm.includes('cave.colliders.map(c=>({...c,x:c.x+OX,z:c.z+OZ}))'),'ice collision converted to absolute world coordinates');
for(const path of ['www/proto3d/frost-cave.js','www/proto3d/frostreach.js']){
 const check=spawnSync(process.execPath,['--check',path],{encoding:'utf8'});
 assert.equal(check.status,0,path+': '+check.stderr);
}
console.log('PASS: dark Frost Cave has solid crystals, navigable boss arenas, exit lighting, one-draw-call animated ice dust');
