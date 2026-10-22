/* Varnethryl Coliseum PvP preview map.
 * Procedural light-weight scene; replace artwork with refined GLB after it
 * is uploaded to www/proto3d/models-new/coliseum-pvp.glb.
 * All combat is restricted to ground-level arena. Spectator tiers are safe.
 */
import * as THREE from './vendor/three.module.js';
export const COLISEUM_TOWN_PORTAL=Object.freeze({x:42*2.8,z:38*2.8+20});
export const COLISEUM_RETURN=Object.freeze({x:0,z:145});
export const COLISEUM_REGION=Object.freeze({cx:0,cz:0,half:180});
const TAU=Math.PI*2;
export function coliseumHeight(x,z){
  const r=Math.hypot(x,z);
  if(r<60)return 0;
  if(r<95)return (r-60)*.52;
  if(r<112)return 18.2;
  if(r<140)return 18.2*(140-r)/28;
  return 0;
}
export const isColiseumCombat=(x,z)=>Math.hypot(x,z)<59;
export function buildColiseum(scene){
 const group=new THREE.Group();group.name='Varnethryl-PvP-Coliseum-preview';
 const m={
 stone:new THREE.MeshLambertMaterial({color:0x8f8982,side:THREE.DoubleSide}),
 dark:new THREE.MeshLambertMaterial({color:0x4b4848}),
 sand:new THREE.MeshLambertMaterial({color:0xa38c69,side:THREE.DoubleSide}),
 path:new THREE.MeshLambertMaterial({color:0x948b78,side:THREE.DoubleSide}),
 banner:new THREE.MeshLambertMaterial({color:0x8d2630,side:THREE.DoubleSide}),
 gold:new THREE.MeshLambertMaterial({color:0xb98b4e}),
 portal:new THREE.MeshBasicMaterial({color:0x955afa,transparent:true,opacity:.69,depthWrite:false,side:THREE.DoubleSide})
 };
 const add=(geometry,mat,name,x=0,y=0,z=0)=>{const o=new THREE.Mesh(geometry,mat);o.name=name;o.position.set(x,y,z);o.receiveShadow=true;group.add(o);return o;};
 function surface(r0,r1,mat,name,segments=96){
  const pos=[],ind=[];for(let i=0;i<=segments;i++){
   const a=i/segments*TAU;
   for(const r of [r0,r1])pos.push(Math.sin(a)*r,coliseumHeight(Math.sin(a)*r,Math.cos(a)*r)+.045,Math.cos(a)*r);
  }
  for(let i=0;i<segments;i++){const k=2*i;ind.push(k,k+1,k+2,k+1,k+3,k+2);}
  const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));geo.setIndex(ind);geo.computeVertexNormals();return add(geo,mat,name);
 }
 add(new THREE.CylinderGeometry(59.5,59.5,.24,80),m.sand,'PVP_COMBAT_FLOOR',0,-.16,0);
 for(let r=59;r<96;r+=3.7)surface(r,Math.min(r+3.7,96),m.stone,'SPECTATOR_TERRACE_'+Math.round(r),96);
 surface(96,112,m.path,'UPPER_SPECTATOR_CONCOURSE');
 for(let r=112;r<140;r+=4)surface(r,Math.min(r+4,140),m.path,'OUTER_ACCESS_RAMP_'+r);
 surface(140,162,m.sand,'EXTERIOR_GROUND');
 // Tier edge stone curbs at controlled intervals, low enough to step over;
 // player height is taken from the same continuous coliseumHeight function.
 const curbGeo=new THREE.BoxGeometry(2.7,.36,.7),dummy=new THREE.Object3D();
 for(const r of [64,72,80,88,96,110]){
   const N=72,inst=new THREE.InstancedMesh(curbGeo,m.dark,N);
   inst.name='Spectator_seating_edge_r'+r;
   for(let i=0;i<N;i++){const a=i/N*TAU;dummy.position.set(Math.sin(a)*r,coliseumHeight(Math.sin(a)*r,Math.cos(a)*r)+.25,Math.cos(a)*r);dummy.rotation.set(0,a,0);dummy.scale.set(1,1,1);dummy.updateMatrix();inst.setMatrixAt(i,dummy.matrix);}
   group.add(inst);
 }
 // Open colonnade instead of collidable solid wall: paths lead around it.
 const colGeo=new THREE.CylinderGeometry(.85,1.1,10,7),topGeo=new THREE.BoxGeometry(2.1,.5,2.1);
 const pillars=new THREE.InstancedMesh(colGeo,m.stone,64),tops=new THREE.InstancedMesh(topGeo,m.dark,64);
 for(let i=0;i<64;i++){const a=i/64*TAU;const x=Math.sin(a)*111,z=Math.cos(a)*111;
   dummy.position.set(x,23.2,z);dummy.rotation.set(0,a,0);dummy.scale.set(1,1,1);dummy.updateMatrix();pillars.setMatrixAt(i,dummy.matrix);
   dummy.position.y=28.4;dummy.updateMatrix();tops.setMatrixAt(i,dummy.matrix);
 }
 pillars.name='Colonnade_columns';tops.name='Colonnade_capitals';group.add(pillars,tops);
 // Arena platform remains at ground floor. No obstacles in spectator circulation.
 add(new THREE.CylinderGeometry(9,9,.42,40),m.dark,'CENTER_ARENA_PLATFORM',0,.18,0);
 add(new THREE.CylinderGeometry(8.2,8.2,.45,40),m.stone,'CENTER_ARENA_DAIS',0,.58,0);
 const barbGeo=new THREE.BoxGeometry(3,2,1.4);
 for(let i=0;i<8;i++){const a=i*TAU/8,r=39;const o=add(barbGeo,m.dark,'ARENA_COVER_'+i,Math.sin(a)*r,1,Math.cos(a)*r);o.rotation.y=a;}
 // Dramatic two monumental plinths and unblocked viewing parapets.
 for(const a of [Math.PI*.72,Math.PI*1.37]){
   const x=Math.sin(a)*99,z=Math.cos(a)*99;
   add(new THREE.CylinderGeometry(6,7,3,10),m.dark,'WARRIOR_STATUE_PLINTH',x,19.9,z);
   add(new THREE.CylinderGeometry(3.5,4.7,10,8),m.stone,'WARRIOR_STATUE_BLOCKOUT',x,26.1,z);
 }
 for(let i=0;i<18;i++){const a=i/18*TAU,x=Math.sin(a)*108,z=Math.cos(a)*108;const b=add(new THREE.PlaneGeometry(3,5),m.banner,'Spectator_banner_'+i,x,24.5,z);b.rotation.y=a;}
 function portal(x,z,name){
  const g=new THREE.Group();g.name=name;g.position.set(x,coliseumHeight(x,z),z);
  for(const s of [-1,1]){const p=new THREE.Mesh(new THREE.BoxGeometry(1,5,1),m.stone);p.position.set(s*2.6,2.5,0);g.add(p);}
  const cap=new THREE.Mesh(new THREE.BoxGeometry(6.2,.9,1.2),m.dark);cap.position.y=5.3;g.add(cap);
  const gate=new THREE.Mesh(new THREE.PlaneGeometry(4.4,4.6),m.portal);gate.position.y=2.5;g.add(gate);group.add(g);
 }
 portal(COLISEUM_RETURN.x,COLISEUM_RETURN.z,'RETURN_PORTAL_TO_TOWN');
 const entryRing=add(new THREE.RingGeometry(59,60,80),m.gold,'COMBAT_BOUNDARY');entryRing.rotation.x=-Math.PI/2;entryRing.position.y=.12;
 // This preview can be navigated without PvP networking. The upper tier
 // geometry is tagged safe and PvP itself remains a later multiplayer step.
 scene.add(group);
 return {group,colliders:[],spawn:{x:0,z:133},returnPortal:COLISEUM_RETURN,
   heightAt:coliseumHeight,isCombat:isColiseumCombat,
   dispose(){scene.remove(group);group.traverse(o=>{o.geometry?.dispose?.()});Object.values(m).forEach(v=>v.dispose());}};
}
export function buildTownColiseumPortal(scene,heightAt){
 const g=new THREE.Group();g.name='MINI_COLISEUM_TO_PVP_MAP';g.position.set(COLISEUM_TOWN_PORTAL.x,heightAt(COLISEUM_TOWN_PORTAL.x,COLISEUM_TOWN_PORTAL.z),COLISEUM_TOWN_PORTAL.z);
 const mat=new THREE.MeshLambertMaterial({color:0x77717d});
 for(const x of [-2.4,2.4]){const c=new THREE.Mesh(new THREE.CylinderGeometry(.55,.75,5,8),mat);c.position.set(x,2.5,0);g.add(c);}
 const cap=new THREE.Mesh(new THREE.BoxGeometry(6,1,1.6),mat);cap.position.y=5.4;g.add(cap);
 const p=new THREE.Mesh(new THREE.PlaneGeometry(3.7,4.2),new THREE.MeshBasicMaterial({color:0x9d57ed,transparent:true,opacity:.6,side:THREE.DoubleSide,depthWrite:false}));p.position.y=2.3;g.add(p);scene.add(g);return g;
}
