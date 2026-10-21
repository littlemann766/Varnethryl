/* Frost Troll brothers' underground ice cavern. Entire second map is
 * enclosed: rock ceiling, dark ice walls, hanging icicles, crystalline light.
 * Uses the exact existing boss/spawn/exit coordinates and walkable terrain,
 * so old saves and the Frost Troll encounters remain functional.
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
 const portal=Math.hypot(xx+7,zz-170),landing=1-smooth01((portal-16)/42);
 return h*(1-landing*.96)*(1-smooth01((Math.max(Math.abs(xx),Math.abs(zz))-HALF+32)/32));
}
// Local ceiling coordinates; far above the two 3.5x Troll brothers.
export function frostCaveCeiling(x,z){
 return 81 + 6*Math.sin(x/63)*Math.cos(z/50) + 4*Math.sin((x+z)/23);
}
export const FROST_CAVE_MOOD=Object.freeze({background:0x07131e,fog:0x0a1a29,near:13,far:139,ambient:0.34,sun:0.22});

export function buildFrostRealm({scene}){
 const group=new THREE.Group();group.name='frost-realm-underground-ice-cavern';group.position.set(OX,0,OZ);scene.add(group);
 const seg=132,N=seg+1,P=new Float32Array(N*N*3),C=new Float32Array(N*N*3),I=[];
 const ice=new THREE.Color(0x447c9b),snow=new THREE.Color(0xa5c9d9),
   rock=new THREE.Color(0x27384d),paint=new THREE.Color();
 for(let iz=0;iz<=seg;iz++)for(let ix=0;ix<=seg;ix++){
  const x=(ix/seg*2-1)*HALF,z=(iz/seg*2-1)*HALF,y=frostElevation(OX+x,OZ+z),k=(iz*N+ix)*3;
  P[k]=x;P[k+1]=y;P[k+2]=z;
  paint.copy(ice).lerp(snow,.08+.23*Math.abs(Math.sin(x*.06)*Math.cos(z*.06)))
    .lerp(rock,.72*smooth01((y-13)/31));
  C[k]=paint.r;C[k+1]=paint.g;C[k+2]=paint.b;
  if(ix<seg&&iz<seg){const a=iz*N+ix;I.push(a,a+N,a+1,a+1,a+N,a+N+1);}
 }
 const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.BufferAttribute(P,3));
 geo.setAttribute('color',new THREE.BufferAttribute(C,3));geo.setIndex(I);geo.computeVertexNormals();
 const terrain=new THREE.Mesh(geo,new THREE.MeshLambertMaterial({vertexColors:true,side:THREE.DoubleSide}));
 terrain.name='walkable-frost-terrain';terrain.castShadow=true;terrain.receiveShadow=true;terrain.userData.keep=true;group.add(terrain);
 // Enclose the ENTIRE second map with a continuous stalactite-rock roof and
 // all four vertical ice-rock walls; no open sky or outdoor tundra biome.
 const roofSeg=60,M=roofSeg+1,roofP=new Float32Array(M*M*3),roofColors=new Float32Array(M*M*3),roofInd=[];
 const darkRock=new THREE.Color(0x182839),blueStone=new THREE.Color(0x345a73),rc=new THREE.Color();
 for(let iz=0;iz<=roofSeg;iz++)for(let ix=0;ix<=roofSeg;ix++){
  const x=(ix/roofSeg*2-1)*HALF,z=(iz/roofSeg*2-1)*HALF,k=(iz*M+ix)*3;
  roofP[k]=x;roofP[k+1]=frostCaveCeiling(x,z);roofP[k+2]=z;
  rc.copy(darkRock).lerp(blueStone,.18+.18*Math.sin(x*.042+z*.016)**2);
  roofColors[k]=rc.r;roofColors[k+1]=rc.g;roofColors[k+2]=rc.b;
  if(ix<roofSeg&&iz<roofSeg){const a=iz*M+ix;roofInd.push(a,a+1,a+M,a+1,a+M+1,a+M);}
 }
 const rgeo=new THREE.BufferGeometry();rgeo.setAttribute('position',new THREE.BufferAttribute(roofP,3));
 rgeo.setAttribute('color',new THREE.BufferAttribute(roofColors,3));rgeo.setIndex(roofInd);rgeo.computeVertexNormals();
 const roof=new THREE.Mesh(rgeo,new THREE.MeshLambertMaterial({vertexColors:true,side:THREE.DoubleSide}));
 roof.name='continuous-dark-ice-ceiling';roof.receiveShadow=true;roof.userData.keep=true;group.add(roof);
 const wallPos=[],wallColors=[],wallIndices=[],steps=60;
 for(let side=0;side<4;side++){
  const offset=wallPos.length/3;
  for(let i=0;i<=steps;i++){
   const u=i/steps*2*HALF-HALF;
   const x=side<2?(side===0?-HALF:HALF):u;
   const z=side>=2?(side===2?-HALF:HALF):u;
   const bottom=frostElevation(OX+x,OZ+z)-2,top=frostCaveCeiling(x,z)+.8;
   const noise=1.1*Math.sin(i*.43+side*3);
   for(const h of [bottom,top]){
    wallPos.push(x+(side<2?noise:0),h,z+(side>=2?noise:0));
    rc.copy(darkRock).lerp(blueStone,h===bottom?.45:.15);
    wallColors.push(rc.r,rc.g,rc.b);
   }
   if(i<steps){const a=offset+i*2;wallIndices.push(a,a+1,a+2,a+1,a+3,a+2);}
  }
 }
 const wgeo=new THREE.BufferGeometry();wgeo.setAttribute('position',new THREE.Float32BufferAttribute(wallPos,3));
 wgeo.setAttribute('color',new THREE.Float32BufferAttribute(wallColors,3));wgeo.setIndex(wallIndices);wgeo.computeVertexNormals();
 const walls=new THREE.Mesh(wgeo,new THREE.MeshLambertMaterial({vertexColors:true,side:THREE.DoubleSide}));
 walls.name='four-enclosing-ice-cave-walls';walls.receiveShadow=true;walls.userData.keep=true;group.add(walls);
 const frozenLake=new THREE.Mesh(new THREE.CircleGeometry(45,48),new THREE.MeshPhongMaterial({color:0x3b9dbf,transparent:true,opacity:.79,shininess:120,side:THREE.DoubleSide}));
 frozenLake.rotation.x=-Math.PI/2;frozenLake.position.set(91,frostElevation(OX+91,OZ+18)+.18,18);group.add(frozenLake);
 // One draw call per type: hanging ice, ground stalagmites and glowing crystals.
 const hanging=new THREE.InstancedMesh(new THREE.ConeGeometry(1.7,9.5,6),
   new THREE.MeshPhongMaterial({color:0x608da6,shininess:92,emissive:0x0b202f}),118);
 const rising=new THREE.InstancedMesh(new THREE.ConeGeometry(1.15,6.4,6),
   new THREE.MeshLambertMaterial({color:0x364b61,flatShading:true}),62);
 const crystals=new THREE.InstancedMesh(new THREE.ConeGeometry(1.6,7.5,6),
   new THREE.MeshPhongMaterial({color:0x76c7ef,emissive:0x174f79,shininess:115,flatShading:true}),90);
 let seed=73513;const rnd=()=>{seed=(Math.imul(seed,1664525)+1013904223)|0;return(seed>>>0)/4294967296;};
 const dummy=new THREE.Object3D();let h=0,r=0,j=0,tries=0;
 while((h<118||r<62||j<90)&&tries++<1800){
  const x=(rnd()*2-1)*(HALF-9),z=(rnd()*2-1)*(HALF-9),y=frostElevation(OX+x,OZ+z);
  // Clear the entry chamber, both Troll brothers' arena and the portal.
  const free=Math.hypot(x+7,z-160)>43&&Math.hypot(x,z+66)>61;
  if(!free)continue;
  if(h<118){
   const length=.5+rnd()*1.35;
   dummy.position.set(x,frostCaveCeiling(x,z)-4.75*length,z);
   dummy.rotation.set(0,rnd()*Math.PI*2,Math.PI);
   dummy.scale.set(length,length,length);dummy.updateMatrix();
   hanging.setMatrixAt(h++,dummy.matrix);
  }else if(r<62){
   const size=.6+rnd()*1.25;
   dummy.rotation.set(0,rnd()*Math.PI*2,0);
   dummy.position.set(x,y+3.2*size,z);
   dummy.scale.setScalar(size);dummy.updateMatrix();rising.setMatrixAt(r++,dummy.matrix);
  }else if(j<90){
   const size=.65+rnd()*1.5;
   dummy.rotation.set(0,rnd()*Math.PI*2,0);
   dummy.position.set(x,y+3.75*size,z);
   dummy.scale.setScalar(size);dummy.updateMatrix();crystals.setMatrixAt(j++,dummy.matrix);
  }
 }
 hanging.count=h;rising.count=r;crystals.count=j;
 hanging.castShadow=rising.castShadow=crystals.castShadow=true;
 hanging.name='ceiling-hanging-icicles';rising.name='dark-ice-stalagmites';crystals.name='glowing-blue-ice-crystals';
 group.add(hanging,rising,crystals);
 // Keep the scene dark while preserving silhouettes of both giant bosses.
 const lights=[
  [-85,-67,0x4a92cf,1.5,105],[90,-45,0x5baff7,1.6,110],
  [-7,155,0x75c0f6,1.1,85],[108,33,0x3489b8,1.2,92]
 ];
 for(const [x,z,color,intensity,range] of lights){
  const light=new THREE.PointLight(color,intensity,range,1.8);
  light.position.set(x,17,z);light.name='subterranean-blue-ice-glow';group.add(light);
 }
 const arch=makeGate(0x8ad6ff);
 arch.position.set(FROST_EXIT.x-OX,frostElevation(FROST_EXIT.x,FROST_EXIT.z),FROST_EXIT.z-OZ);
 group.add(arch);
 const cols=[]; // Cave walls visually enclose existing map bounds. Keep the arena path and bosses unblocked.
 group.visible=false;
 return {group,portalMesh:arch,colliders:cols,spawn:FROST_SPAWN,exit:FROST_EXIT,brothers:FROST_BROTHERS,
  roof,walls,lights:lights.length,heightAt:frostElevation,update:t=>arch.userData.update?.(t)};
}
