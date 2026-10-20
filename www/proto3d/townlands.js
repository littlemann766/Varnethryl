/* Varnethryl town outskirts: same chunked, low-poly scenery approach as the Wilds.
 * The established buildings/quests and their coordinates stay unchanged.
 * All new scenery is batched per 64-world-unit chunk and culled by proximity. */
import * as THREE from './vendor/three.module.js';
import { makeVariant, makeDetailTexture, makeMaterials, Acc } from './scenery.js';

const CHUNK = 64;
const CORE = 164;           // original town wall was at +/-168 world units
const RING = 194; // preserved level carriageway, with a new mountainous countryside beyond           // scenic carriageway linking the outer districts
const FIELDS = [
  { x: -211, z: 111, w: 48, d: 31, color: 0x866738 },
  { x: -209, z: -108, w: 43, d: 34, color: 0x918047 },
  { x: 207, z: 124, w: 47, d: 31, color: 0x7a713e }
];

// Deterministic terrain surface for the enlarged town map.
// Flat central city, level carriageways/fields/gates, walkable ridges, natural valleys.
// This is the ONLY outdoor height function: mesh, scenery, player and followers share it.
const smooth=(a,b,v)=>{const t=Math.max(0,Math.min(1,(v-a)/(b-a)));return t*t*(3-2*t);};
const ridges=[
  [-386,-292,43,96],[-412,337,55,108],[359,-345,53,102],
  [395,304,46,95],[-328,388,26,73],[306,414,24,72],
  [-443,24,29,87],[456,-38,32,92]
];
const valleys=[[-295,258,19,88],[340,-242,16,80],[-377,-170,13,67],[271,313,12,77]];
export function townElevation(x,z,world=560){
  const ax=Math.abs(x),az=Math.abs(z),radius=Math.hypot(x,z);
  // Preserve the established village, ring road, and farming plots at the original ground level.
  if(radius<=220||Math.min(ax,az)<12)return 0;
  for(const f of FIELDS)if(ax>=0&&Math.abs(x-f.x)<f.w/2+6&&Math.abs(z-f.z)<f.d/2+6)return 0;
  const inner=smooth(220,305,radius),edge=1-smooth(world-105,world-15,Math.max(ax,az));
  if(edge<=0)return 0;
  const roads=smooth(12,41,Math.min(ax,az));
  let h=5+3.8*Math.sin(x/83+z/126)+3.3*Math.cos(z/74-x/135);
  for(const [cx,cz,height,spread] of ridges){
    const dx=(x-cx)/spread,dz=(z-cz)/spread;
    h+=height*Math.exp(-0.5*(dx*dx+dz*dz));
  }
  for(const [cx,cz,depth,spread] of valleys){
    const dx=(x-cx)/spread,dz=(z-cz)/spread;
    h-=depth*Math.exp(-0.5*(dx*dx+dz*dz));
  }
  return Math.max(-12,Math.min(64,h))*inner*edge*roads;
}
// ~41K triangles, one draw call; not a distant prop: heroes can traverse this actual mesh.
function buildWalkableTerrain(world){
  const seg=144,size=seg+1,P=new Float32Array(size*size*3),C=new Float32Array(size*size*3),ind=[];
  const paint=new THREE.Color(), grass=new THREE.Color(0x6ca74e),meadow=new THREE.Color(0x83ad62),
    stone=new THREE.Color(0x8a8c85),snow=new THREE.Color(0xd6d9d6),earth=new THREE.Color(0x897653);
  for(let iz=0;iz<=seg;iz++)for(let ix=0;ix<=seg;ix++){
    const x=(ix/seg*2-1)*world,z=(iz/seg*2-1)*world,y=townElevation(x,z,world),k=(iz*size+ix)*3;
    P[k]=x;P[k+1]=y+0.012;P[k+2]=z;
    const dyx=(townElevation(x+5,z,world)-townElevation(x-5,z,world))/10;
    const dyz=(townElevation(x,z+5,world)-townElevation(x,z-5,world))/10;
    const slope=Math.hypot(dyx,dyz),variation=0.5+0.5*Math.sin(x*.13+Math.cos(z*.11))*Math.sin(z*.15);
    paint.copy(grass).lerp(meadow,.20+.42*variation);
    if(y>16||slope>.42)paint.lerp(stone,Math.min(1,Math.max(smooth(12,40,y),smooth(.32,.83,slope))*.8));
    if(y>49)paint.lerp(snow,smooth(47,61,y)*.72);
    if(y<0)paint.lerp(earth,smooth(0,11,-y)*.22);
    if(Math.min(Math.abs(x),Math.abs(z))<15&&Math.max(Math.abs(x),Math.abs(z))>160)paint.lerp(earth,.7);
    C[k]=paint.r;C[k+1]=paint.g;C[k+2]=paint.b;
  }
  for(let z=0;z<seg;z++)for(let x=0;x<seg;x++){
    const a=z*size+x,b=a+1,c=a+size,d=c+1;
    ind.push(a,c,b,b,c,d);
  }
  const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.BufferAttribute(P,3));
  geo.setAttribute('color',new THREE.BufferAttribute(C,3));geo.setIndex(ind);geo.computeVertexNormals();
  const mesh=new THREE.Mesh(geo,new THREE.MeshLambertMaterial({vertexColors:true,side:THREE.DoubleSide}));
  mesh.name='walkable-hills-mountains-valleys';
  // Critical: mergeStatic() does not preserve existing per-vertex color buffers.
  // Keep this independent vertex-coloured surface or green hills become a near-black flat merge.
  mesh.userData.keep=true;
  mesh.castShadow=true;mesh.receiveShadow=true;
  return mesh;
}

const rng = seed => () => { seed=(seed+0x6D2B79F5)|0; let t=Math.imul(seed^seed>>>15,1|seed);t=(t+Math.imul(t^t>>>7,61|t))^t;return ((t^t>>>14)>>>0)/4294967296; };
const randRange = (rnd,a,b) => a+(b-a)*rnd();
const pick = (rnd,arr) => arr[Math.min(arr.length-1,Math.floor(rnd()*arr.length))];

export function buildTownOutskirts({ scene, colliders, world, buildings, spacing }) {
  // Do not modify the Wilds' map, the established village, or either portal.
  const rnd=rng(20261020), group=new THREE.Group();group.name='town-landscaped-outskirts';scene.add(group);
  const mats=makeMaterials(makeDetailTexture()), cache=new Map(), chunks=new Map(), occupied=[];
  const stats={trees:0,bushes:0,rocks:0,flowers:0,grass:0,orchard:0,fields:0};
  const usable=world-13;
  const terrain=buildWalkableTerrain(world);group.add(terrain);
  const insideField=(x,z,pad=0)=>FIELDS.some(f=>Math.abs(x-f.x)<f.w/2+pad&&Math.abs(z-f.z)<f.d/2+pad);
  const nearBuilding=(x,z,pad=0)=>buildings.some(b=>{
    const bx=b.cx*spacing,bz=b.id==='gatehouse'?world-1.2:b.cz*spacing;
    return Math.abs(x-bx)<26+pad&&Math.abs(z-bz)<26+pad;
  });
  // Clear avenues across the centre, the old village, gatehouse approach and a ring road.
  const route=(x,z,pad=0)=>Math.abs(x)<15+pad||Math.abs(z)<10+pad||
    Math.abs(Math.hypot(x,z)-RING)<8+pad;
  const possible=(x,z,pad=0)=>Math.max(Math.abs(x),Math.abs(z))>CORE+pad &&
    Math.max(Math.abs(x),Math.abs(z))<usable-pad &&
    !route(x,z,pad) && !insideField(x,z,pad) && !nearBuilding(x,z,pad);
  const clear=(x,z,rad)=>occupied.every(p=>Math.hypot(p[0]-x,p[1]-z)>rad+p[2]);
  const acc=(layer,x,z)=>{
    const key=layer+':'+Math.floor(x/CHUNK)+':'+Math.floor(z/CHUNK);
    if(!chunks.has(key))chunks.set(key,{layer,acc:new Acc()});
    return chunks.get(key).acc;
  };
  const put=(kind,name,pal,x,z,s=1,shadow=false)=>{
    const vkey=kind+'/'+name+'/'+pal;
    let v=cache.get(vkey);
    if(!v){v=makeVariant(kind,name,pal,4,true);cache.set(vkey,v);}
    acc(shadow?'cast':'plain',x,z).add(v.geo,x,townElevation(x,z,world),z,rnd()*Math.PI*2,s);
  };
  const claim=(x,z,r)=>occupied.push([x,z,r]);
  // A few lightly textured cultivated plots are visual only; none obstruct player movement.
  const roadMat=new THREE.MeshLambertMaterial({color:0x9b9177});
  function roadRing(){
    const N=96,W=4.2,positions=[],indices=[];
    for(let i=0;i<=N;i++){const a=i*2*Math.PI/N,cs=Math.cos(a),sn=Math.sin(a);
      positions.push((RING-W)*cs,.045,(RING-W)*sn,(RING+W)*cs,.045,(RING+W)*sn);
      if(i<N){const j=i*2;indices.push(j,j+2,j+1,j+1,j+2,j+3);}
    }
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.setIndex(indices);g.computeVertexNormals();
    const m=new THREE.Mesh(g,roadMat);m.receiveShadow=true;m.userData.keep=true;group.add(m);
  }
  roadRing();
  const plotMats=new Map();
  for(const f of FIELDS){
    if(Math.max(Math.abs(f.x),Math.abs(f.z))>=world-28)continue;
    const mat=plotMats.get(f.color)||new THREE.MeshLambertMaterial({color:f.color,side:THREE.DoubleSide});
    plotMats.set(f.color,mat);
    const patch=new THREE.Mesh(new THREE.PlaneGeometry(f.w,f.d),mat);
    patch.rotation.x=-Math.PI/2;patch.position.set(f.x,.047,f.z);patch.receiveShadow=true;patch.userData.keep=true;group.add(patch);
    const lines=7;
    for(let i=0;i<lines;i++){
      const z=f.z-f.d*.43+i*f.d*.86/(lines-1);
      for(let j=0;j<8;j++){
        const x=f.x-f.w*.43+j*f.w*.86/7;
        put('flowers','grass',pick(rnd,['lush','dry']),x,z,randRange(rnd,.6,.98));
      }
    }
    stats.fields++;
  }
  // West orchard, northeastern grove, rocky northwest, flowering eastern meadows.
  const region=(x,z)=>x < -160 && z > -65 && z < 95?'orchard':x > 135 && z < -50?'pine':
    x < -140 && z < -75?'rock':'meadow';
  function sample(count,fn,pad=0){
    let made=0;
    for(let tries=0;tries<count*55&&made<count;tries++){
      const x=randRange(rnd,-usable,usable),z=randRange(rnd,-usable,usable);
      if(!possible(x,z,pad))continue;
      if(fn(x,z,region(x,z))!==false)made++;
    }
    return made;
  }
  sample(740,(x,z,r)=>{
    if(!clear(x,z,3.6))return false;
    const type=r==='orchard'?'apple':r==='pine'?pick(rnd,['pine','pine','cypress']):
      r==='rock'?pick(rnd,['pine','birch','dead']):pick(rnd,['oak','birch','apple','pine']);
    const pal=type==='apple'?pick(rnd,['green','blossom','autumn']):
      type==='pine'?pick(rnd,['spruce','deep','green']):type==='birch'?pick(rnd,['lime','yellow']):
      type==='dead'?'grey':type==='cypress'?'deep':pick(rnd,['green','lime','autumn']);
    const s=randRange(rnd,.85,1.5);
    put('trees',type,pal,x,z,s,true);claim(x,z,2.9*s);
    // Simple circular trunk collider, keeping long clear roads, doors and orchard paths navigable.
    colliders.push({type:'circle',x,z,r:.42*s+.15});
    stats.trees++;if(r==='orchard')stats.orchard++;
  },2);
  sample(360,(x,z,r)=>{if(!clear(x,z,1.3))return false;
    put('bushes',pick(rnd,['round','hedge','spiky']),pick(rnd,['green','deep','lime']),x,z,randRange(rnd,.7,1.2));
    claim(x,z,1.15);stats.bushes++;
  },1);
  sample(210,(x,z,r)=>{if(!clear(x,z,1.7))return false;
    const b=r==='rock'?'boulder':pick(rnd,['stone','cluster','slab']);
    const s=randRange(rnd,.8,1.45);
    put('rocks',b,pick(rnd,['grey','warm','slate','mossy']),x,z,s);
    if(b==='boulder')colliders.push({type:'circle',x,z,r:s*.8});
    claim(x,z,1.6);stats.rocks++;
  },1);
  sample(890,(x,z)=>{
    put('flowers',pick(rnd,['daisy','tulip','lavender','bellflower']),pick(rnd,['white','yellow','pink','purple','blue','red']),x,z,randRange(rnd,.7,1.15));stats.flowers++;
  });
  sample(1900,(x,z)=>{put('flowers','grass',pick(rnd,['green','lush','dry']),x,z,randRange(rnd,.75,1.3));stats.grass++;});
  // Instanced-style batch: one vertex-colored mesh per chunk/layer, not thousands of draw calls.
  const meshes=[];
  for(const {layer,acc:A} of chunks.values()){
    const geo=A.geo(true);if(!geo)continue;
    const mesh=new THREE.Mesh(geo,mats.solid);
    mesh.castShadow=layer==='cast';mesh.receiveShadow=true;
    mesh.frustumCulled=true;mesh.userData.keep=true;group.add(mesh);meshes.push(mesh);
  }
  for(const v of cache.values()){v.geo.dispose();if(v.glow)v.glow.dispose();}
  let lastCell='';
  function cull(x,z,k=1){
    const cell=Math.floor(x/12)+':'+Math.floor(z/12)+':'+Math.round(k*10);
    if(cell===lastCell)return;lastCell=cell;
    for(const mesh of meshes){
      const sphere=mesh.geometry.boundingSphere;
      const d=Math.hypot(sphere.center.x-x,sphere.center.z-z)-sphere.radius;
      mesh.visible=d<140*Math.max(1,k);
    }
  }
  return {group,cull,stats,terrain,heightAt:(x,z)=>townElevation(x,z,world),chunkCount:meshes.length,fieldCount:stats.fields};
}
