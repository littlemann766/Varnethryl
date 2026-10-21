import assert from 'node:assert/strict';
import * as THREE from '../www/proto3d/vendor/three.module.js';
import {createOwnerFooting} from '../www/proto3d/owner-footing.js';

// A realistic two-legged skinned hierarchy; the left imported Idle lifts a boot.
const model=new THREE.Group();
const legs={};
for(const side of ['L','R']){
  const thigh=new THREE.Bone();thigh.name='thigh_'+side;model.add(thigh);
  const shin=new THREE.Bone();shin.name='shin_'+side;thigh.add(shin);
  const foot=new THREE.Bone();foot.name='foot_'+side;shin.add(foot);
  legs[side]={thigh,shin,foot};
}
const solver=createOwnerFooting(model,THREE);
assert(solver,'Owner bone chain discovered');
const step=(airborne=false,speed=0)=>{
  solver.beforeAnimation();
  // Simulate the authored raw clip: its left foot is suspended 25 cm.
  legs.L.foot.position.y=.25;
  legs.R.foot.position.y=0;
  solver.afterAnimation(speed,1/60,airborne);
  model.updateMatrixWorld(true);
  const a=legs.L.foot.getWorldPosition(new THREE.Vector3());
  const b=legs.R.foot.getWorldPosition(new THREE.Vector3());
  return Math.abs(a.y-b.y);
};
let gap=0;
for(let i=0;i<90;i++)gap=step(false,0);
assert(gap<.035,'Both idle feet must be planted; difference '+gap);
assert(solver.blend>.98,'grounded idle correction fully applied');
for(let i=0;i<110;i++)gap=step(true,0);
assert(gap>.19,'Flight must restore recognizable raised-leg imported stance; difference '+gap);
assert(solver.flightBlend>.99,'full flight blend');
for(let i=0;i<120;i++)gap=step(false,0);
assert(gap<.035,'Landing must plant both feet after smooth blend; difference '+gap);
for(let i=0;i<50;i++)gap=step(false,2);
assert(solver.blend<.02,'Walking must release idle foot-locking');
const bad=new THREE.Group();
assert.equal(createOwnerFooting(bad,THREE),null,'Other heroes without Owner rig unaffected');
console.log('PASS owner grounded idle/raised-leg takeoff/flight/two-foot landing and walk release');
