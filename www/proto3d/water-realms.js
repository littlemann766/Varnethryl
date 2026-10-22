/* Varnethryl: separate Hydra Mire and compact 1,000 x 1,000 m Tidewrack sea.
   1 game unit ~= .704 m (1 m ~= 1.42 units). Only the nearby ocean terrain
   is instantiated, and the full chart uses deterministic island positions. */
import * as THREE from './vendor/three.module.js';
export const WORLD_UNITS_PER_METER=1.42;
export const OCEAN_METERS=1000; // 1 km by 1 km while sailing gameplay is refined
export const OCEAN=Object.freeze({cx:17500,cz:0,half:OCEAN_METERS*WORLD_UNITS_PER_METER/2});
export const MIRE=Object.freeze({cx:12500,cz:0,half:190});
const TWOPI=Math.PI*2;
function rnd(seed){let a=seed|0;return ()=>{a=(a+0x6d2b79f5)|0;let t=Math.imul(a^(a>>>15),1|a);t^=t+Math.imul(t^(t>>>7),61|t);return ((t^(t>>>14))>>>0)/4294967296;};}
const material=(color,roughness=1)=>new THREE.MeshStandardMaterial({color,roughness,metalness:0.02});
const dark=material(0x444b50),cliff=material(0x677278),moss=material(0x566657),shore=material(0x898d84);
// Rock materials are shared by every streamed island and both maps. Never
// dispose one while an adjacent island (or a future map visit) still uses it.
const cachedRockMaterials=new Set([dark,cliff,moss,shore]);
function makeSpire(parent,x,z,height,radius,angle=0){
 const g=new THREE.ConeGeometry(radius,height,5,1);
 const o=new THREE.Mesh(g,Math.round(height)%3===0?cliff:dark);
 o.position.set(x,height*.47-.5,z);o.rotation.set(.1*Math.sin(angle),angle,.12*Math.cos(angle));
 o.castShadow=true;o.receiveShadow=true;parent.add(o);return o;
}
function seaWater(){
 // The water follows the camera/boat. Waves shift UVs without thousands of
 // per-frame mesh updates or an immense 9km square allocation on mobile.
 const canvas=document.createElement('canvas');canvas.width=128;canvas.height=128;
 const c=canvas.getContext('2d');const im=c.createImageData(128,128),r=rnd(9234);
 for(let i=0;i<im.data.length;i+=4){let w=r();im.data[i]=25+w*12;im.data[i+1]=70+w*25;im.data[i+2]=95+w*26;im.data[i+3]=255;}
 c.putImageData(im,0,0);
 const tex=new THREE.CanvasTexture(canvas);tex.wrapS=tex.wrapT=THREE.RepeatWrapping;tex.repeat.set(42,42);tex.colorSpace=THREE.SRGBColorSpace;
 const mesh=new THREE.Mesh(new THREE.PlaneGeometry(1800,1800,1,1),new THREE.MeshStandardMaterial({color:0x529db1,map:tex,roughness:.31,metalness:.12,transparent:true,opacity:.95,side:THREE.DoubleSide}));
 mesh.rotation.x=-Math.PI/2;mesh.position.y=0;mesh.receiveShadow=true;mesh.name='sailing-water-window';return {mesh,tex};
}
function island(parent,x,z,r,sizeSeed,colliders){
 const rand=rnd(sizeSeed),h=5+rand()*9;
 const rise=new THREE.Mesh(new THREE.CylinderGeometry(r*.68,r, h,9,1),dark);
 rise.position.set(x,h*.34-2.5,z);rise.castShadow=true;rise.receiveShadow=true;parent.add(rise);
 const crest=new THREE.Mesh(new THREE.CylinderGeometry(r*.54,r*.72,1.3,9),shore);
 crest.position.set(x,h*.72-2.2,z);crest.receiveShadow=true;parent.add(crest);
 for(let j=0;j<4;j++){const a=rand()*TWOPI,rr=r*(.62+rand()*.65);makeSpire(parent,x+Math.cos(a)*rr,z+Math.sin(a)*rr,5+rand()*21,2+rand()*5,a);}
 // Visible reefs and islands stop a sailing ship; leave plenty of open ocean.
 colliders.push({type:'circle',x,z,r:r*.83});
}
async function glbFromGzip(url){
 if(!('DecompressionStream'in window))throw new Error('This Android WebView does not support compressed GLB models');
 const response=await fetch(url+'?v=1.5.8');if(!response.ok)throw new Error('GLB HTTP '+response.status);
 const bytes=await response.arrayBuffer(),head=new Uint8Array(bytes,0,Math.min(4,bytes.byteLength));
 // Some hosts decode .gz on the HTTP layer. Accept either raw GLB or gzip
 // exactly once so the original ship and Hydra load on both web and Android.
 const decoded=head[0]===0x67&&head[1]===0x6c&&head[2]===0x54&&head[3]===0x46
   ?bytes:head[0]===0x1f&&head[1]===0x8b
     ?await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer()
     :null;
 if(!decoded)throw new Error('Unrecognized compressed GLB format');
 const {GLTFLoader}=await import('./vendor/jsm/loaders/GLTFLoader.js');
 return await new Promise((ok,bad)=>new GLTFLoader().parse(decoded,'',ok,bad));
}
function dispose(root){const seen=new Set();root.traverse(o=>{if(o.geometry&&!seen.has(o.geometry)){seen.add(o.geometry);o.geometry.dispose();}const ms=Array.isArray(o.material)?o.material:o.material?[o.material]:[];for(const m of ms){if(seen.has(m)||cachedRockMaterials.has(m))continue;seen.add(m);for(const k of Object.keys(m)){const t=m[k];if(t?.isTexture&&!seen.has(t)){seen.add(t);t.dispose();}}m.dispose();}});}
export function buildHydraMire(scene){
 const root=new THREE.Group();root.name='hydra-mire-zone';root.position.set(MIRE.cx,0,MIRE.cz);scene.add(root);
 const colliders=[],m=material(0x53656b),walk=material(0x737975);
 const water=new THREE.Mesh(new THREE.CircleGeometry(173,64),new THREE.MeshStandardMaterial({color:0x316d79,metalness:.1,roughness:.38,transparent:true,opacity:.85,side:THREE.DoubleSide}));
 water.rotation.x=-Math.PI/2;water.position.y=.02;root.add(water);
 const platform=new THREE.Mesh(new THREE.CylinderGeometry(60,67,2.4,36),walk);platform.position.y=.05;platform.receiveShadow=true;platform.castShadow=true;platform.name='walkable-hydra-ground';root.add(platform);
 const altar=new THREE.Mesh(new THREE.CylinderGeometry(18,23,1,24),m);altar.position.y=1.8;altar.receiveShadow=true;root.add(altar);
 const entry=new THREE.Mesh(new THREE.CylinderGeometry(9,11,1.6,16),walk);entry.position.set(0,0,117);root.add(entry);
 // Above-water walkable stepping slabs lead from the shore to the arena.
 for(let i=0;i<5;i++){const z=100-i*8;const slab=new THREE.Mesh(new THREE.BoxGeometry(13,1.5,13),walk);slab.position.set(i%2?1:-1,.15,z);slab.receiveShadow=true;root.add(slab);}
 const rand=rnd(5041);
 for(let i=0;i<31;i++){
  const a=(i/31)*TWOPI,dist=81+rand()*79,x=Math.cos(a)*dist,z=Math.sin(a)*dist,ht=4+rand()*23;
  makeSpire(root,x,z,ht,3+rand()*7,a);colliders.push({type:'circle',x:x+MIRE.cx,z:z+MIRE.cz,r:3.2});
 }
 const ruin=new THREE.Group();ruin.position.set(-39,1.6,57);root.add(ruin);
 for(const a of [-1,1]){const p=new THREE.Mesh(new THREE.BoxGeometry(3,8,3),m);p.position.set(a*5,4,0);ruin.add(p);}
 const lintel=new THREE.Mesh(new THREE.BoxGeometry(14,2,4),m);lintel.position.set(0,8,0);ruin.add(lintel);
 // Five-headed Hydra: original mesh, selectively cleaned ground and intact
 // chest; this remains an unrigged visual placeholder pending five-neck skinning.
 const hydraHolder=new THREE.Group();hydraHolder.name='hydra-unrigged-5-head';hydraHolder.position.set(0,2.3,-11);root.add(hydraHolder);
 let hydraReady=false,hydraDefeated=false,hydraDeathTime=null,disposed=false;
 glbFromGzip('proto3d/models-new/hydra_restored_mobile.glb.gz').then(gltf=>{
  const model=gltf.scene;
   // Exit can happen while a large compressed model is still loading.
   // Drop the late result rather than attaching it to an abandoned arena.
   if(disposed){dispose(model);return;}
   const b=new THREE.Box3().setFromObject(model);const ht=b.max.y-b.min.y;
  if(!Number.isFinite(ht)||ht<.01)throw new Error('Hydra model bounds are invalid');
  const scalar=18/ht;model.scale.setScalar(scalar);
  model.position.set(-(b.min.x+b.max.x)*scalar/2,-b.min.y*scalar,-(b.min.z+b.max.z)*scalar/2);
  model.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});
  hydraHolder.add(model);hydraReady=true;
 }).catch(e=>{if(!disposed)console.warn('Hydra Mire model could not load',e);});
 colliders.push({type:'circle',x:MIRE.cx,z:MIRE.cz-11,r:11}); // Hydra torso collision
 const exit={x:MIRE.cx,z:MIRE.cz+117},spawn={x:MIRE.cx,z:MIRE.cz+105};
 return{group:root,colliders,spawn,exit,half:MIRE.half,updates:0,get hydraReady(){return hydraReady;},
   heightAt(x,z){const r=Math.hypot(x-MIRE.cx,z-MIRE.cz);return r<60?1.25:r<70?.2:r<111&&Math.abs(x-MIRE.cx)<9?.9:r<125&&Math.abs(x-MIRE.cx)<12?.7:-.65;},
   waterAt(x,z){const r=Math.hypot(x-MIRE.cx,z-MIRE.cz);return r>70&&!(r<125&&Math.abs(x-MIRE.cx)<12);},
   defeatBoss(){hydraDefeated=true;hydraDeathTime=null;},
  resetBoss(){hydraDefeated=false;hydraDeathTime=null;hydraHolder.visible=true;},
  update(t){
    if(disposed)return;
    if(hydraDefeated){
      if(hydraDeathTime===null)hydraDeathTime=t;
      const age=Math.max(0,t-hydraDeathTime);
      hydraHolder.position.y=2.3-Math.min(16,age*5);
      hydraHolder.visible=age<3.25;
    }else{
      hydraHolder.visible=true;
      hydraHolder.position.y=2.3+.035*Math.sin(t*.8);
    }
  },dispose(){disposed=true;scene.remove(root);dispose(root);}};
}
export function buildSailingOcean(scene){
 const root=new THREE.Group();root.name='tidewrack-open-ocean';scene.add(root);
 const water=seaWater();root.add(water.mesh);
 const vessel=new THREE.Group();vessel.name='player-sailing-ship';vessel.position.set(OCEAN.cx,0,OCEAN.cz+OCEAN.half-180);root.add(vessel);
 let shipReady=false,shipLoadError='',disposed=false;
 const ready=glbFromGzip('proto3d/models-new/tidewrack_sailing_ship.glb.gz').then(gltf=>{
  const imported=gltf.scene;
   if(disposed){dispose(imported);throw Error('Sailing realm unloaded before ship was ready');}
   // Refuse to board an empty or non-renderable GLB scene. A valid parser
   // response isn't proof that the file contains visible ship geometry.
   let meshCount=0;
   imported.traverse(o=>{if(o.isMesh && o.geometry?.attributes?.position?.count>0)meshCount++;});
   if(meshCount===0)throw Error('Approved sailing GLB contains no renderable ship meshes');
   const bounds=new THREE.Box3().setFromObject(imported);const dim=bounds.getSize(new THREE.Vector3());
  if(![dim.x,dim.y,dim.z].every(Number.isFinite)||dim.y<.005||dim.x<.005||dim.z<.005)
    throw Error('Ship model has invalid dimensions');
  const scale=13.5/dim.y;
  imported.scale.setScalar(scale);
  imported.position.set(-(bounds.min.x+bounds.max.x)/2*scale,-bounds.min.y*scale-.7,-(bounds.min.z+bounds.max.z)/2*scale);
  imported.rotation.y=Math.PI*.5;
  imported.name='user-supplied-sailing-ship';
  imported.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});
  vessel.add(imported);shipReady=true;
 }).catch(e=>{
   shipLoadError=String(e?.message||e);
   if(!disposed)console.error('Approved sailing ship failed to load; stay in town',e);
   throw e; // Realm transition awaits this: no crew stranded on empty ocean.
 });
 // Deck positions are ship-local and therefore follow the hull's position,
 // turning and wave-induced roll. Slot 0 is the helmsman, 1-3 companions.
 // Separate Y values account for the raised stern of the medieval galleon.
 const crewSlots=[
   new THREE.Vector3(0,2.35,-3.0),
   new THREE.Vector3(-1.28,1.95,-.65),
   new THREE.Vector3(1.28,1.95,-.65),
   new THREE.Vector3(0,1.95,2.4)
 ];
 function crewSpot(slot,out=new THREE.Vector3()){
   const pos=crewSlots[Math.max(0,Math.min(3,slot|0))];
   vessel.updateMatrixWorld(true);
   return vessel.localToWorld(out.copy(pos));
 }
 const tiles=new Map(),obstacles=new Map(),TILE=240,VIEW_RADIUS=2,colliders=[];
 const spawn={x:OCEAN.cx,z:OCEAN.cz+OCEAN.half-175};
 // Rudder steering: left/right rotates the hull; forward/reverse controls sail
 // speed. This avoids the previous sideways character-strafing boat movement.
 const nav={heading:0,speed:0,throttle:0};
 // A real tapered, broken V-shaped foam trail: multiple narrow ribbon strips
 // with fading foam colors. No solid plane, sprite, or giant white rectangle.
 const wake=new THREE.Group();wake.name='player-ship-wake';root.add(wake);
 const wakeMat=new THREE.MeshBasicMaterial({color:0xd9f2ef,vertexColors:true,transparent:true,
   opacity:0,depthWrite:false,side:THREE.DoubleSide,polygonOffset:true,polygonOffsetFactor:-1});
 for(const [start,drift,len,phase] of [[0,0,30,.8],[-1.2,-4.6,32,1.9],[1.2,4.6,32,2.7],[-1.9,-2.2,18,3.5],[1.9,2.2,18,4.6]]){
   const vertices=[],colors=[],indices=[],n=24;
   for(let j=0;j<=n;j++){
     const p=j/n,z=6+len*p;
     const x=start+drift*p+.23*Math.sin(phase+p*14)*p;
     const thickness=(.12+.31*p)*(1-.73*p);
     const fade=Math.max(0,1-p)*(.73+.27*Math.cos(j*.8+phase)**2);
     for(const edge of [-1,1]){
       vertices.push(x+edge*thickness,0,z);
       colors.push(.55*fade,.9*fade,fade);
     }
     if(j<n&&j%6!==4){const a=2*j;indices.push(a,a+2,a+1,a+1,a+2,a+3);}
   }
   const geo=new THREE.BufferGeometry();
   geo.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));
   geo.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
   geo.setIndex(indices);geo.computeVertexNormals();
   const foam=new THREE.Mesh(geo,wakeMat);foam.name='tapered-foam-streak';foam.frustumCulled=false;wake.add(foam);
 }
 wake.visible=false;
 function blocked(x,z,pad=5){
   for(const arr of obstacles.values())for(const c of arr)
     if(Math.hypot(x-c.x,z-c.z)<c.r+pad)return true;
   return false;
 }
 function sail(dt,turn,throttle,x,z){
   if(!shipReady)return{x,z,heading:nav.heading,speed:0,blocked:true};
   const step=Math.max(0,Math.min(.05,Number(dt)||0));
   const rudder=THREE.MathUtils.clamp(Number(turn)||0,-1,1);
   const power=THREE.MathUtils.clamp(Number(throttle)||0,-1,1);
   nav.throttle=power;
   // A galleon takes time to accelerate and coasts when sails are furled.
   const target=power>=0?power*19:power*5;
   nav.speed+=(target-nav.speed)*Math.min(1,step*(power===0?1.5:.65));
   const steering=Math.min(1,Math.abs(nav.speed)/9);
   // The hull faces -Z at heading zero. Starboard rudder should turn
   // the bow toward +X (negative yaw), port toward -X (positive yaw).
   // Inverting in reverse preserves realistic helm pivot behavior.
   nav.heading-=rudder*step*.64*steering*(nav.speed<-.2?-1:1);
   const dd=nav.speed*step;
   const mx=-Math.sin(nav.heading)*dd,mz=-Math.cos(nav.heading)*dd;
   const nx=x+mx,nz=z+mz,edge=OCEAN.half-12;
   if(Math.abs(nx-OCEAN.cx)>edge||Math.abs(nz-OCEAN.cz)>edge||blocked(nx,nz,8)){
     nav.speed*=.3;
     return{x,z,heading:nav.heading,speed:nav.speed,blocked:true};
   }
   return{x:nx,z:nz,heading:nav.heading,speed:nav.speed,blocked:false};
 }
 // One deterministic island layout feeds BOTH streaming 3D geometry and the
 // full-ocean chart. An unloaded island must not vanish from the overview.
 // Do not independently randomize minimap rocks: use this exact RNG order.
 function islandLayout(tx,tz){
   const seed=((tx*73856093)^(tz*19349663)^9201)|0,r=rnd(seed),result=[];
   if(Math.hypot(tx*TILE,tz*TILE-(OCEAN.half-175))<=260)return result;
   const count=r()>.60?1+Math.floor(r()*2):0;
   for(let i=0;i<count;i++){
     const x=OCEAN.cx+(tx+r()-.5)*TILE,z=OCEAN.cz+(tz+r()-.5)*TILE;
     const half=OCEAN.half-45;
     if(Math.abs(x-OCEAN.cx)>half||Math.abs(z-OCEAN.cz)>half)continue;
     if(Math.hypot(x-spawn.x,z-spawn.z)<310)continue;
     result.push({x,z,r:18+r()*35,seed:seed+i*83});
   }
   return result;
 }
 function tile(tx,tz){
  const k=tx+','+tz;if(tiles.has(k))return;
  const group=new THREE.Group();group.name='ocean-island-tile-'+k;root.add(group);const hits=[];
  for(const p of islandLayout(tx,tz))island(group,p.x,p.z,p.r,p.seed,hits);
  tiles.set(k,group);obstacles.set(k,hits);
 }
 // Cached lightweight map geometry covers the full 1 km square without loading
 // remote tiles into the scene or changing boat collision / performance.
 let fullIslandChart=null;
 function mapFeatures(full=false){
   if(!full)return [...obstacles.values()].flat();
   if(!fullIslandChart){
     const all=[],limit=Math.ceil(OCEAN.half/TILE)+1;
     for(let tz=-limit;tz<=limit;tz++)for(let tx=-limit;tx<=limit;tx++){
       for(const p of islandLayout(tx,tz))all.push({type:'circle',x:p.x,z:p.z,r:p.r*.83});
     }
     fullIslandChart=all;
   }
   return fullIslandChart;
 }
 function update(t,x,z,yaw){
  if(disposed)return;
  vessel.position.set(x,.35+.19*Math.sin(t*1.1),z);
  vessel.rotation.set(.027*Math.sin(t*.67),yaw+Math.PI,.034*Math.sin(t*.91));
  water.mesh.position.x=x;water.mesh.position.z=z;water.tex.offset.set(t*.0017,t*.0009);
  wake.position.set(x,.075,z);
  wake.rotation.set(0,yaw,0);
  wakeMat.opacity=Math.min(.62,Math.max(0,Math.abs(nav.speed)/19*.52));
  wake.visible=shipReady&&Math.abs(nav.speed)>.55;
  const ix=Math.floor((x-OCEAN.cx)/TILE),iz=Math.floor((z-OCEAN.cz)/TILE);
  const keys=new Set();
  for(let dz=-VIEW_RADIUS;dz<=VIEW_RADIUS;dz++)for(let dx=-VIEW_RADIUS;dx<=VIEW_RADIUS;dx++){
   const xx=ix+dx,zz=iz+dz;if(Math.abs((xx+.5)*TILE)>OCEAN.half+TILE||Math.abs((zz+.5)*TILE)>OCEAN.half+TILE)continue;
   const k=xx+','+zz;keys.add(k);tile(xx,zz);
  }
  for(const [k,g] of tiles)if(!keys.has(k)){root.remove(g);dispose(g);tiles.delete(k);obstacles.delete(k);}
 }
 update(0,spawn.x,spawn.z,0);
 return{group:root,ship:vessel,colliders,spawn,half:OCEAN.half,ready,
   get shipReady(){return shipReady;},get shipLoadError(){return shipLoadError;},
   get navigation(){return {...nav};},
   // Same positions as the streamed 3D island collision geometry.
   mapFeatures,crewSpot,sail,blocked,
   update,dispose(){disposed=true;scene.remove(root);dispose(root);}};
}