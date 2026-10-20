/* Frost Troll brothers' ice realm. Shared height function makes the mountains walkable.
 * No external texture or model assets: the two existing approved troll GLBs are spawned by fight.js.
 */
import * as THREE from './vendor/three.module.js';
import { makeGate } from './wilds.js';
import { FROST_REALM, smooth01 } from './bossregions.js';
const {cx:OX,cz:OZ,half:HALF}=FROST_REALM;
const peaks=[[-153,-142,38,77],[151,-120,37,86],[-165,110,30,79],[165,123,33,87],[4,-188,26,72]];
export const FROST_SPAWN=Object.freeze({x:OX-7,z:OZ+155});
export const FROST_EXIT=Object.freeze({x:OX-7,z:OZ+177});
export const FROST_BROTHERS=Object.freeze([{key:'frosttroll_a',x:OX-37,z:OZ-66},{key:'frosttroll_b',x:OX+37,z:OZ-66}]);
export function frostElevation(x,z){
 const xx=x-OX,zz=z-OZ;
 let h=1.6*Math.sin(xx/29)*Math.cos(zz/37);
 for(const [cx,cz,am,r] of peaks){
  const dx=(xx-cx)/r,dz=(zz-cz)/r;h+=am*Math.exp(-.5*(dx*dx+dz*dz));
 }
 const portal=Math.hypot(xx+7,zz-170);
 const landing=1-smooth01((portal-16)/42);
 return h*(1-landing*.96)*(1-smooth01((Math.max(Math.abs(xx),Math.abs(zz))-HALF+32)/32));
}
export function buildFrostRealm({scene}){
 const group=new THREE.Group();group.name='frost-realm-two-brothers';group.position.set(OX,0,OZ);scene.add(group);
 const seg=132,N=seg+1,P=new Float32Array(N*N*3),C=new Float32Array(N*N*3),I=[];
 const ice=new THREE.Color(0x9ac7df),snow=new THREE.Color(0xe4f1f5),rock=new THREE.Color(0x7f91b0),paint=new THREE.Color();
 for(let iz=0;iz<=seg;iz++)for(let ix=0;ix<=seg;ix++){
  const x=(ix/seg*2-1)*HALF,z=(iz/seg*2-1)*HALF,y=frostElevation(OX+x,OZ+z),k=(iz*N+ix)*3;
  P[k]=x;P[k+1]=y;P[k+2]=z;
  paint.copy(snow).lerp(ice,.14+.25*Math.abs(Math.sin(x*.06)*Math.cos(z*.06))).lerp(rock,.65*smooth01((y-17)/23));
  C[k]=paint.r;C[k+1]=paint.g;C[k+2]=paint.b;
  if(ix<seg&&iz<seg){const a=iz*N+ix;I.push(a,a+N,a+1,a+1,a+N,a+N+1);}
 }
 const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.BufferAttribute(P,3));geo.setAttribute('color',new THREE.BufferAttribute(C,3));geo.setIndex(I);geo.computeVertexNormals();
 const terrain=new THREE.Mesh(geo,new THREE.MeshLambertMaterial({vertexColors:true,side:THREE.DoubleSide}));
 terrain.name='walkable-frost-terrain';terrain.castShadow=true;terrain.receiveShadow=true;terrain.userData.keep=true;group.add(terrain);
 const frozenLake=new THREE.Mesh(new THREE.CircleGeometry(45,48),new THREE.MeshPhongMaterial({color:0x7ac6e9,transparent:true,opacity:.75,shininess:100,side:THREE.DoubleSide}));
 frozenLake.rotation.x=-Math.PI/2;frozenLake.position.set(91,frostElevation(OX+91,OZ+18)+.18,18);group.add(frozenLake);
 const trunks=new THREE.InstancedMesh(new THREE.CylinderGeometry(.32,.55,4.6,6),new THREE.MeshLambertMaterial({color:0x545764}),76);
 const pines=new THREE.InstancedMesh(new THREE.ConeGeometry(3.6,9,8),new THREE.MeshLambertMaterial({color:0xb2cbd2,flatShading:true}),76);
 const crystals=new THREE.InstancedMesh(new THREE.ConeGeometry(1.6,7.5,6),new THREE.MeshPhongMaterial({color:0x79bddc,emissive:0x164b68,flatShading:true}),40);
 let seed=73513;const rnd=()=>{seed=(Math.imul(seed,1664525)+1013904223)|0;return(seed>>>0)/4294967296;};
 const d=new THREE.Object3D();let k=0,j=0,tries=0;
 while((k<76||j<40)&&tries++<900){
  const x=(rnd()*2-1)*(HALF-10),z=(rnd()*2-1)*(HALF-10),y=frostElevation(OX+x,OZ+z);
  if(Math.hypot(x+7,z-160)<49||Math.hypot(x,z+66)<72||Math.hypot(x-91,z-18)<51)continue;
  if(k<76){const s=.8+rnd()*.8;d.position.set(x,y+2.3*s,z);d.scale.setScalar(s);d.rotation.y=rnd()*Math.PI*2;d.updateMatrix();trunks.setMatrixAt(k,d.matrix);d.position.y=y+9*s;d.updateMatrix();pines.setMatrixAt(k,d.matrix);k++;}
  else if(j<40){const s=.7+rnd()*1.5;d.position.set(x,y+3.2*s,z);d.scale.setScalar(s);d.rotation.y=rnd()*6.28;d.updateMatrix();crystals.setMatrixAt(j++,d.matrix);}
 }
 trunks.count=pines.count=k;crystals.count=j;trunks.castShadow=pines.castShadow=crystals.castShadow=true;
 group.add(trunks,pines,crystals);
 const arch=makeGate(0x9bdfff);arch.position.set(FROST_EXIT.x-OX,frostElevation(FROST_EXIT.x,FROST_EXIT.z),FROST_EXIT.z-OZ);
 group.add(arch);
 const cols=[]; // frosted open world; no artificial blockers on the entrance or the bosses
 group.visible=false;
 return{group,portalMesh:arch,colliders:cols,spawn:FROST_SPAWN,exit:FROST_EXIT,brothers:FROST_BROTHERS,heightAt:frostElevation,update:t=>arch.userData.update?.(t)};
}
