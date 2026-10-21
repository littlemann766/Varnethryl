/* Varnethryl: The Broken Seal. A second, fully walkable town/Wilds
 * crossing set into the existing northwest mountain's traversable slope.
 * This does NOT replace the Frost Troll summit, old town gate, or save slots.
 * Model provenance: built against the shipped procedural terrain. No claim
 * that a separately uploaded mountain GLB has been installed. */
import * as THREE from './vendor/three.module.js';

export const MOUNTAIN_WILDS_GATE=Object.freeze({x:-315,z:-284});
export const MOUNTAIN_WILDS_RETURN=Object.freeze({x:-303,z:-284});
export const MOUNTAIN_APPROACH=Object.freeze([
  [-80,-285],[-145,-286],[-205,-284],[-265,-283],[-295,-284],[-312,-284]
]);
export const nearMountainWildsGate=(x,z,r=6)=>Number.isFinite(x)&&Number.isFinite(z)&&
  Math.hypot(x-MOUNTAIN_WILDS_GATE.x,z-MOUNTAIN_WILDS_GATE.z)<r;

const mats=()=>({
  slate:new THREE.MeshLambertMaterial({color:0x414b55,flatShading:true,side:THREE.DoubleSide}),
  cliff:new THREE.MeshLambertMaterial({color:0x59616c,flatShading:true,side:THREE.DoubleSide}),
  ash:new THREE.MeshLambertMaterial({color:0x757575,flatShading:true}),
  trim:new THREE.MeshStandardMaterial({color:0x8c7b63,metalness:.24,roughness:.8}),
  rune:new THREE.MeshStandardMaterial({color:0xb38bdf,emissive:0x582591,emissiveIntensity:.72,roughness:.38}),
  crystal:new THREE.MeshStandardMaterial({color:0xa574f4,emissive:0x531baa,emissiveIntensity:.95,roughness:.21,flatShading:true})
});
function addMesh(group,geo,mat,name,x,y,z,sx=1,sy=1,sz=1){
  const mesh=new THREE.Mesh(geo,mat);mesh.name=name;mesh.position.set(x,y,z);
  mesh.scale.set(sx,sy,sz);mesh.castShadow=false;mesh.receiveShadow=true;
  // Startup's global static-batcher is allowed to merge plain rock and paving,
  // but not portal arch lintels or animated emissive runes/crystals.
  // Retaining only these small accents keeps the Android draw-call count low.
  if (/arch-lintel|purple-crystal|purple-ward|floor-runes|ancient-seal/.test(name))
    mesh.userData.keep=true;
  group.add(mesh);return mesh;
}
function ruinArch(g, M, x, floor, broken=false){
  const pillar=new THREE.BoxGeometry(1.65,5.5,1.7);
  for(const side of [-1,1]){
    const h=broken && side===1 ? 3.4:5.5;
    addMesh(g,pillar,M.slate,'broken-seal-ruin-pillar',x,floor+h/2,side*6.3,1,h/5.5,1);
    addMesh(g,new THREE.BoxGeometry(2.2,.7,2.2),M.trim,'broken-seal-arch-cap',x,floor+h+.27,side*6.3);
  }
  if(!broken)addMesh(g,new THREE.BoxGeometry(2,1.25,12.8),M.cliff,
    'mountain-portal-arch-lintel',x,floor+6.1,0);
}
function strut(g,M,x,floor,z,rotation,size){
  const rubble=addMesh(g,new THREE.DodecahedronGeometry(1,0),M.cliff,
    'broken-seal-ruined-boulder',x,floor+size*.48,z,size,size*.88,size*.85);
  rubble.rotation.set(.12,rotation,.1);return rubble;
}
export function buildMountainWildsGateway(group,heightAt){
  const G=new THREE.Group();G.name='the-broken-seal-mountain-wilds-gateway';G.userData.keep=true;
  G.position.set(MOUNTAIN_WILDS_GATE.x,heightAt(MOUNTAIN_WILDS_GATE.x,MOUNTAIN_WILDS_GATE.z),MOUNTAIN_WILDS_GATE.z);
  group.add(G);
  const M=mats(), here=(dx,dz)=>heightAt(MOUNTAIN_WILDS_GATE.x+dx,MOUNTAIN_WILDS_GATE.z+dz)-G.position.y;
  const colliders=[];
  // A dry-stone passage leads into the hill. Every segment sits on the same
  // physical terrain function as the hero and the branch road.
  // No collision surfaces cross the central 10-unit-wide walking lane.
  const rockGeo=new THREE.DodecahedronGeometry(1,0),dummy=new THREE.Object3D();
  const rockN=48,rocks=new THREE.InstancedMesh(rockGeo,M.cliff,rockN);
  rocks.name='mountain-cave-rock-shell';rocks.castShadow=false;rocks.receiveShadow=true;
  let n=0;
  const rock=(x,z,dx,dy,dz,idx)=>{
    const floor=here(x,z),rx=.18*Math.sin(idx*3.8);
    dummy.position.set(x,floor+dy*.58,z);dummy.rotation.set(rx,idx*.7,idx*.28);
    dummy.scale.set(dx,dy,dz);dummy.updateMatrix();rocks.setMatrixAt(n++,dummy.matrix);
  };
  // Interlocking natural rock shoulders on both sides; walk-through opening.
  for(let i=0;i<12;i++){
    const x=-14+i*2.65;
    for(const side of [-1,1]){
      const size=5.8+(i%3)*.55;
      rock(x,side*(8.5+Math.sin(i*1.3)*.6),4.9,size,4.8,2*i+(side+1)/2);
    }
  }
  // Rough vaulted ceiling with two layers; it is high enough that the camera
  // can orbit above the character without clipping on an ordinary hero.
  for(let i=0;i<12;i++){
    const x=-13+i*2.6,base=here(x,0);
    dummy.position.set(x,base+10.4+Math.sin(i*.8)*.45,0);
    dummy.rotation.set(.05,0,Math.sin(i)*.08);
    dummy.scale.set(5.6,2.25,6.1);dummy.updateMatrix();rocks.setMatrixAt(n++,dummy.matrix);
  }
  for(let i=0;i<12;i++){
    const x=-13+i*2.6,base=here(x,0);
    dummy.position.set(x,base+13.1,-3.2+i%2*6.4);
    dummy.rotation.set(.11,0,Math.sin(i)*.12);
    dummy.scale.set(4.6,3.1,5.4);dummy.updateMatrix();rocks.setMatrixAt(n++,dummy.matrix);
  }
  rocks.count=n;rocks.instanceMatrix.needsUpdate=true;G.add(rocks);
  // The entrance and chamber remain open: roofs and flanking rocks do not
  // add blocking circular colliders inside the route center.
  ruinArch(G,M,19,here(19,0),true);
  ruinArch(G,M,7,here(7,0));
  ruinArch(G,M,-7,here(-7,0));
  // Uneven damaged stone flagstones, terrain-following and wide enough for
  // followers. Players cross the original shared terrain below them.
  const floorGeo=new THREE.BoxGeometry(2.9,.13,10.0);
  for(let i=0;i<13;i++){
    const x=-13+i*2.75,y=here(x,0);
    const s=addMesh(G,floorGeo,i%4===0?M.cliff:M.ash,'broken-seal-floor-stones',
      x,y+.045,0);s.rotation.y=Math.sin(i*2.1)*.023;
  }
  // Outer ruin courtyard, never on the road itself.
  for(let i=0;i<8;i++){
    const x=16+(i%4)*6, side=i<4?-1:1,z=side*(11+(i%3)*2.2);
    const h=2.8+(i%3)*1.2,y=here(x,z);
    const m=addMesh(G,new THREE.CylinderGeometry(.85,1.05,h,7),M.slate,
      'mountain-ruins-fallen-column',x,y+h/2,z);m.rotation.z=i%2?.15:-.14;
    colliders.push({type:'circle',x:MOUNTAIN_WILDS_GATE.x+x,z:MOUNTAIN_WILDS_GATE.z+z,r:1.18});
    if(i%2===0)strut(G,M,x+2,here(x+2,z+3*side),z+3*side,.4,1.8);
  }
  for(let i=0;i<9;i++){
    const x=17+i*4,z=(i%2?-1:1)*(18+(i%3)*3);
    strut(G,M,x,here(x,z),z,i*.21,1+(i%4)*.28);
  }
  // Purple crystal wards, one soft light for Android, runes and roof glow.
  const crystalGeo=new THREE.OctahedronGeometry(1,0);
  for(const x of [-8,5,19])for(const side of [-1,1]){
    const z=side*6.15,y=here(x,z),h=1.9+(x===5?.4:0);
    addMesh(G,crystalGeo,M.crystal,'broken-seal-purple-crystal-ward',x,y+1.1,z,.55,h,.55);
  }
  const sigil=addMesh(G,new THREE.RingGeometry(3.2,4.2,28),M.rune,
    'broken-seal-stone-floor-runes',0,here(0,0)+.19,0);
  sigil.rotation.x=-Math.PI/2;
  const glow=new THREE.PointLight(0x9b5bff,1.35,34,2);
  glow.name='mountain-gateway-purple-light';glow.position.set(0,here(0,0)+5,0);
  glow.castShadow=false;G.add(glow);
  const update=t=>{glow.intensity=1.2+.18*Math.sin(t*1.4);M.crystal.emissiveIntensity=.81+.14*Math.sin(t*1.8)};
  return {group:G,colliders,update,gate:MOUNTAIN_WILDS_GATE};
}
export function buildWildsReturnRuins(group,x,z){
  // Existing Wilds portal and its old coordinates remain intact.
  const M=mats(),G=new THREE.Group();G.name='the-broken-seal-wilds-return-ruins';G.position.set(x,0,z);group.add(G);
  const colliders=[];
  for(const side of [-1,1]){
    for(let i=0;i<3;i++){
      const zz=side*(5.6+i*2.6),xx=-3.4+i*3.4;
      const height=4.9-i*.75,mesh=addMesh(G,new THREE.CylinderGeometry(.68,.86,height,7),
        M.slate,'wilds-ruined-return-pillars',xx,height/2,zz);
      mesh.rotation.z=i===2?side*.28:0;
      colliders.push({type:'circle',x:x+xx,z:z+zz,r:.85});
    }
    addMesh(G,new THREE.DodecahedronGeometry(1,0),M.cliff,
      'wilds-return-crumbled-arch',6,1.25,side*7,2.1,1.5,1.2);
    addMesh(G,new THREE.OctahedronGeometry(.8,0),M.crystal,
      'wilds-return-purple-ward',-1,2.7,side*5.6);
  }
  const ring=addMesh(G,new THREE.RingGeometry(2.9,3.4,32),M.rune,
    'wilds-portal-ancient-seal',0,.075,0);
  ring.rotation.x=-Math.PI/2;
  return {group:G,colliders};
}
