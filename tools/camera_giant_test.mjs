// Giant camera regression: trees must not be treated as infinitely tall walls.
import assert from 'node:assert/strict';
import {segmentClearT,cameraColliderBlocks} from '../www/proto3d/camprefs.js';
const tree={type:'circle',x:9,z:0,r:1.1,cameraTop:13};
const wall={type:'box',minX:9,maxX:10,minZ:-3,maxZ:3};
const ray=(obstacle,aY,bY)=>segmentClearT([obstacle],0,0,23,0,.5,(c,t)=>cameraColliderBlocks(c,t,aY,bY));
assert(ray(tree,5,9)<1,'Human camera still collides with nearby trunk');
assert.equal(ray(tree,45,55),1,'Giant camera above canopy does not collide with trunk');
assert(ray(wall,45,55)<1,'Unannotated masonry walls still stop camera');
assert.equal(ray(tree,100,150),1,'50x giant camera skips lower scenery');
assert(cameraColliderBlocks(tree,.5,2,9),'low sightline blocked');
assert(!cameraColliderBlocks(tree,.5,40,51),'high sightline passes');
console.log('PASS giant camera over trees; walls still block; perspective height tests');
