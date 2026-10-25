/* Frost Troll brothers' ice realm. Shared height function makes the mountains walkable.
 * No external texture or model assets: the two existing approved troll GLBs are spawned by fight.js.
 */
import * as THREE from './vendor/three.module.js';
import { makeGate } from './wilds.js';
import { buildFrostCave } from './frost-cave.js';
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
 const ice=new THREE.Color(0x54738f),snow=new THREE.Color(0x9bbbc8),rock=new THREE.Color(0x2a3549),paint=new THREE.Color();
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
 const frozenLake=new THREE.Mesh(new THREE.CircleGeometry(45,48),new THREE.MeshPhongMaterial({color:0x4786a8,transparent:true,opacity:.72,shininess:100,side:THREE.DoubleSide}));
 frozenLake.rotation.x=-Math.PI/2;frozenLake.position.set(91,frostElevation(OX+91,OZ+18)+.18,18);group.add(frozenLake);
 // Replace the outdoor tree line with a traversable, vaulted ice cave.
 // Keep an unobstructed entry and arena for both of the approved Troll GLBs.
 const cave=buildFrostCave(group,HALF,(x,z)=>frostElevation(OX+x,OZ+z),[
   {x:-7,z:155,r:38},{x:-7,z:177,r:25},
   {x:-37,z:-66,r:31},{x:37,z:-66,r:31}
 ]);
 const arch=makeGate(0x9bdfff);arch.position.set(FROST_EXIT.x-OX,frostElevation(FROST_EXIT.x,FROST_EXIT.z),FROST_EXIT.z-OZ);
 group.add(arch);
 const cols=cave.colliders.map(c=>({...c,x:c.x+OX,z:c.z+OZ})); // local cave spires use world-space collision positions
 group.visible=false;
 return{group,cave,portalMesh:arch,colliders:cols,spawn:FROST_SPAWN,exit:FROST_EXIT,brothers:FROST_BROTHERS,heightAt:frostElevation,update:t=>{arch.userData.update?.(t);cave.update(t);}};
}

/* Beth round 2 frost realm dressing: one merged kit mesh added to the realm group (async, after the realm is built). */
export async function dressFrostRealmBeth(FM){
  if(!FM||(typeof location!=='undefined'&&/nobeth/.test(location.search)))return 0;
  const { placeZone, loadZonePlacement } = await import('./beth-zones.js');
  const Z=placeZone(await loadZonePlacement('frost_realm'),{heightAt:frostElevation,origin:[FROST_REALM.cx,FROST_REALM.cz],name:'beth-frost-realm',chunk:1e4});
  FM.group.add(Z.group);return Z.count;
}
