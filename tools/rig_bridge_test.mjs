#!/usr/bin/env node
// Pure rig-bridge unit test: no WebGL, no player save, no material rewrite.
import assert from 'node:assert/strict';
import * as THREE from '../www/proto3d/vendor/three.module.js';
import { bridgeUnskinnedHumanoid, splitHumanoidRig } from '../www/proto3d/rig-bridge.js';

function donor() {
  const group=new THREE.Group();
  const byName=new Map();
  function b(name,parent,x=0,y=0,z=0) {
    const node=new THREE.Bone();node.name=name;node.position.set(x,y,z);parent.add(node);byName.set(name,node);return node;
  }
  const root=b('root',group), hips=b('hips',root,0,1,0),
    spine=b('spine',hips,0,.1,0), chest=b('chest',spine,0,.25,0),
    neck=b('neck',chest,0,.2,0);b('head',neck,0,.1,0);
  for(const [side,x] of [['L',.23],['R',-.23]]) {
    const sh=b('shoulder_'+side,chest,x,.16,0);
    const arm=b('upperArm_'+side,sh,0,0,0);
    const fore=b('foreArm_'+side,arm,0,-.29,0);
    b('hand_'+side,fore,0,-.26,0);
    const thigh=b('thigh_'+side,hips,x*.55,-.1,0);
    const shin=b('shin_'+side,thigh,0,-.46,0);
    b('foot_'+side,shin,0,-.43,0);
  }
  const original=new THREE.Mesh(new THREE.SphereGeometry(.12),new THREE.MeshStandardMaterial());
  chest.add(original);
  group.updateMatrixWorld(true);
  return {root:group, clips:()=>[new THREE.AnimationClip('walk',1,[])]};
}
function inputModel() {
  const g=new THREE.Group();
  const m=new THREE.Mesh(new THREE.CylinderGeometry(.22,.18,1.7,10,10),
    new THREE.MeshStandardMaterial({color:0x888899}));
  m.position.y=.85;
  g.add(m);
  return g;
}
{
  const rig=donor(), model=inputModel();
  const result=bridgeUnskinnedHumanoid(THREE,rig,model);
  assert.equal(result.ok,true,result.reason);
  assert.ok(result.helpers.includes('elbow_L'));
  assert.ok(result.helpers.includes('upperSpine'));
  assert.ok(result.helpers.includes('knee_R'));
  const bound=[];
  result.scene.traverse(x=>{if(x.isSkinnedMesh)bound.push(x);});
  assert.equal(bound.length,1);
  const mesh=bound[0];
  assert.ok(mesh.geometry.getAttribute('skinIndex'));
  assert.ok(mesh.geometry.getAttribute('skinWeight'));
  const weights=mesh.geometry.getAttribute('skinWeight');
  for(let i=0;i<weights.count;i++) {
    const sum=weights.getX(i)+weights.getY(i)+weights.getZ(i)+weights.getW(i);
    assert.ok(Math.abs(sum-1)<.00002,'weights must add up to 1 at '+i+': '+sum);
  }
  assert.equal(result.animations[0].name,'walk');
  assert.equal(model.children[0].isMesh,true,'source Meshy model is untouched');
  assert.equal(rig.root.getObjectByName('head').isBone,true);
  assert.equal(splitHumanoidRig(THREE,rig.root).length,0,'splitting twice must be safe');
}
{
  const rig=donor(), model=inputModel();
  const m=model.children[0];model.remove(m);
  const s=new THREE.SkinnedMesh(m.geometry,m.material);
  model.add(s);
  const trial=bridgeUnskinnedHumanoid(THREE,rig,model);
  assert.equal(trial.ok,false,'existing rig must never be overridden');
  assert.match(trial.reason,/already skinned/);
}
console.log('PASS: Beth skeleton augmentation and reversible Meshy surface-skin metadata');
