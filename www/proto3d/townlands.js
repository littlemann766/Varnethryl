/* Varnethryl town outskirts: same chunked, low-poly scenery approach as the Wilds.
 * The established buildings/quests and their coordinates stay unchanged.
 * All new scenery is batched per 64-world-unit chunk and culled by proximity. */
import * as THREE from './vendor/three.module.js';
import { makeVariant, makeDetailTexture, makeMaterials, Acc } from './scenery.js';
import { CITY_HALF, FROST_SUMMIT, FROST_PORTAL, TITAN_CENTER, PORT_CENTER, LAVA_POOLS, BALTHRIX_TRAIL, BALTHRIX_TRAIL_HALF_WIDTH, balthrixTrailDistance, smooth01, frostHill, lavaAmount } from './bossregions.js';

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
  // Preserve the city and nearby building foundations; port and lighthouse have graded level platforms.
  const frostD=Math.hypot(x-FROST_SUMMIT.x,z-FROST_SUMMIT.z), frost=frostHill(x,z);
  if(radius<=220)return 0;
  const nearPort=Math.hypot(x-PORT_CENTER.x,z-PORT_CENTER.z);
  const nearLight=Math.hypot(x+157*2.8,z-119*2.8);
  const flatten=Math.min(smooth01((nearPort-59)/28),smooth01((nearLight-26)/22));
  const corridor=smooth01((Math.min(ax,az)-12)/29);
  for(const f of FIELDS)if(ax>=0&&Math.abs(x-f.x)<f.w/2+6&&Math.abs(z-f.z)<f.d/2+6)return 0;
  const inner=smooth(220,305,radius),edge=1-smooth(world-105,world-15,Math.max(ax,az));
  if(edge<=0)return 0;
  const roads=corridor;
  let h=5+3.8*Math.sin(x/83+z/126)+3.3*Math.cos(z/74-x/135);
  for(const [cx,cz,height,spread] of ridges){
    const dx=(x-cx)/spread,dz=(z-cz)/spread;
    h+=height*Math.exp(-0.5*(dx*dx+dz*dz));
  }
  for(const [cx,cz,depth,spread] of valleys){
    const dx=(x-cx)/spread,dz=(z-cz)/spread;
    h-=depth*Math.exp(-0.5*(dx*dx+dz*dz));
  }
  let terrain=Math.max(-12,Math.min(64,h))*inner*edge*roads*flatten;
  // Broad summit overrides the north-south flat road only where the climb is intentional.
  const iceBlend=1-smooth01((frostD-112)/55);
  terrain=terrain*(1-iceBlend)+frost;
  // Ashen Titan's volcanic massif: genuine traversable slope, high jagged rim
  // and lowered crater. This is the single shared physics/render surface.
  const dx=x-TITAN_CENTER.x,dz=z-TITAN_CENTER.z,d=Math.hypot(dx,dz);
  if(d<148){
    const blend=1-smooth(115,148,d);
    const angle=Math.atan2(dz,dx);
    const shoulder=65*(1-smooth(20,135,d));
    const crater=30*(1-smooth(0,36,d));
    const ribs=5*Math.sin(angle*9+d*.065)*smooth(8,37,d)*(1-smooth(62,135,d));
    const volcano=Math.max(0,shoulder-crater+ribs);
    terrain=terrain*(1-blend)+volcano*blend;
  }
  return terrain;
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
    const ice=1-smooth01((Math.hypot(x-FROST_SUMMIT.x,z-FROST_SUMMIT.z)-35)/115);
    if(ice>0)paint.lerp(snow,Math.min(0.97,ice*.93));
    const volc=lavaAmount(x,z);
    if(volc>0){
      const d=Math.hypot(x-TITAN_CENTER.x,z-TITAN_CENTER.z);
      const ash=1-smooth(115,150,d);
      paint.lerp(new THREE.Color(0x201f28),Math.min(1,Math.max(volc*.92,ash*.96)));
      // Fire-red mineral seams along the crater and jagged rim.
      if(d<45&&d>20&&Math.sin(Math.atan2(z-TITAN_CENTER.z,x-TITAN_CENTER.x)*11)>0.7)
        paint.lerp(new THREE.Color(0x81382b),.33);
    }
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
  // KEEP the vertex-colored mesh out of mergeStatic (it otherwise discarded its vertex colors and turned the landscape black).
  mesh.name='walkable-hills-mountains-valleys';mesh.receiveShadow=true;mesh.castShadow=true;mesh.userData.keep=true;return mesh;
}

/* Balthrix's old stomping/slithering track: raised, scarred earth banks,
 * bare central dirt, and fallen timber on the outer edge. This mesh follows
 * actual terrain elevations at every strip vertex, including volcano slopes.
 * It is decorative only; navmesh/collision and terrain physics remain intact. */
function buildBalthrixTrail(group,world){
  const points=BALTHRIX_TRAIL,N=points.length,h=BALTHRIX_TRAIL_HALF_WIDTH;
  const widths=[-h-6,-h,-h*.64,0,h*.64,h,h+6];
  const color=new THREE.Color(),earth=new THREE.Color(0x63452e),
    center=new THREE.Color(0x795239),edge=new THREE.Color(0x846b4b),
    bank=new THREE.Color(0x64563e);
  const P=[],C=[],I=[];
  for(let i=0;i<=N;i++){
    const cur=points[i%N],left=points[(i+N-1)%N],right=points[(i+1)%N];
    const tx=right.x-left.x,tz=right.z-left.z,len=Math.hypot(tx,tz)||1;
    const nx=-tz/len,nz=tx/len;
    for(let j=0;j<widths.length;j++){
      const w=widths[j],x=cur.x+nx*w,z=cur.z+nz*w;
      const b=(j===0||j===6)?1.45:(j===1||j===5)?.38:0;
      const grain=.09*Math.sin(i*.65+j*2.1);
      P.push(x,townElevation(x,z,world)+.14+b+grain,z);
      color.copy(j===3?center:j===0||j===6?bank:j===1||j===5?edge:earth);
      color.multiplyScalar(.93+.09*Math.sin(i*.31+j*.71));
      C.push(color.r,color.g,color.b);
      if(i<N&&j<widths.length-1){
        const a=i*widths.length+j,bb=a+widths.length;
        I.push(a,bb,a+1,a+1,bb,bb+1);
      }
    }
  }
  const geo=new THREE.BufferGeometry();
  geo.setAttribute('position',new THREE.Float32BufferAttribute(P,3));
  geo.setAttribute('color',new THREE.Float32BufferAttribute(C,3));
  geo.setIndex(I);geo.computeVertexNormals();
  const surface=new THREE.Mesh(geo,new THREE.MeshLambertMaterial({vertexColors:true,side:THREE.DoubleSide}));
  surface.name='balthrix-perimeter-scarred-brown-trail';
  surface.userData.keep=true;surface.receiveShadow=true;group.add(surface);
  // Knocked-over timber is deliberately light-weight and non-colliding.
  const trunkGeo=new THREE.CylinderGeometry(.55,.85,7,7),timberMat=new THREE.MeshLambertMaterial({color:0x4d3628});
  const logs=new THREE.InstancedMesh(trunkGeo,timberMat,Math.floor(N/17));
  const dummy=new THREE.Object3D(),up=new THREE.Vector3(0,1,0);
  let n=0;
  for(let i=0;i<N&&n<logs.count;i+=17){
    const p=points[i],prev=points[(i+N-1)%N],next=points[(i+1)%N];
    const dx=next.x-prev.x,dz=next.z-prev.z,len=Math.hypot(dx,dz)||1;
    const side=i%2?1:-1,x=p.x-side*dz/len*(h+7),z=p.z+side*dx/len*(h+7);
    dummy.position.set(x,townElevation(x,z,world)+.75,z);
    dummy.quaternion.setFromUnitVectors(up,new THREE.Vector3(dx/len,.12,dz/len).normalize());
    dummy.scale.setScalar(.65+(i%6)*.045);dummy.updateMatrix();
    logs.setMatrixAt(n++,dummy.matrix);
  }
  logs.count=n;logs.castShadow=true;logs.receiveShadow=true;logs.name='balthrix-fallen-timber';logs.userData.keep=true;
  group.add(logs);
  return surface;
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
  const balthrixTrail=buildBalthrixTrail(group,world);
  // Distant low-poly mountain range outside the playable boundary: visual
  // backdrop only (no colliders or simulation). Sixteen affordable draw calls.
  const farMountains=new THREE.Group();farMountains.name='distant-mountain-silhouettes';group.add(farMountains);
  const farStone=new THREE.MeshLambertMaterial({color:0x556679,flatShading:true,side:THREE.DoubleSide});
  const farSnow=new THREE.MeshLambertMaterial({color:0x9baaba,flatShading:true,side:THREE.DoubleSide});
  const farRock=new THREE.ConeGeometry(1,1,7);
  for(let i=0;i<16;i++){
    const a=i*2*Math.PI/16,offset=world+50+(i%3)*31;
    const x=Math.cos(a)*offset,z=Math.sin(a)*offset;
    const height=72+(i*37%61),radius=53+(i*19%34);
    const mountain=new THREE.Mesh(farRock,farStone);
    mountain.position.set(x,height*.5-8,z);mountain.scale.set(radius,height,radius*.82);
    mountain.rotation.y=a*.57;mountain.receiveShadow=true;mountain.castShadow=false;
    farMountains.add(mountain);
    const crown=new THREE.Mesh(farRock,farSnow);
    crown.position.set(x,height-8-height*.18,z);crown.scale.set(radius*.27,height*.36,radius*.22);
    crown.rotation.y=mountain.rotation.y;farMountains.add(crown);
  }
  const lavaMat=new THREE.MeshLambertMaterial({color:0xff5b18,emissive:0xe23b08,emissiveIntensity:1.25,side:THREE.DoubleSide});
  const poolMeshes=[];
  for(const pool of LAVA_POOLS){
    const seg=40,points=[pool.x,townElevation(pool.x,pool.z,world)+.16,pool.z],indices=[];
    for(let i=0;i<=seg;i++){const a=i*2*Math.PI/seg,rr=pool.r*(.93+.05*Math.sin(i*3.8));
      const x=pool.x+Math.cos(a)*rr,z=pool.z+Math.sin(a)*rr;points.push(x,townElevation(x,z,world)+.18,z);
      if(i)indices.push(0,i,i+1);
    }
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(points,3));g.setIndex(indices);g.computeVertexNormals();
    const m=new THREE.Mesh(g,lavaMat);m.name='lava-pool';m.userData.keep=true;m.receiveShadow=true;group.add(m);poolMeshes.push(m);
  }
  const pathsMat=new THREE.MeshLambertMaterial({color:0x958675,side:THREE.DoubleSide});
  // Surfaced roads interpolate actual terrain height: no floating paths through hills.
  function path(points,width=7.4,mat=pathsMat){
    const curve=new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(p[0],0,p[1])));
    const N=160,verts=[],indices=[];
    for(let i=0;i<=N;i++){
      const t=i/N,p=curve.getPoint(t),d=curve.getTangent(t),len=Math.hypot(d.x,d.z)||1;
      const nx=-d.z/len,nz=d.x/len;
      for(const side of [-1,1]){
        const x=p.x+side*nx*width/2,z=p.z+side*nz*width/2;
        verts.push(x,townElevation(x,z,world)+.095,z);
      }
      if(i<N){const k=i*2;indices.push(k,k+2,k+1,k+1,k+2,k+3);}
    }
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(verts,3));g.setIndex(indices);g.computeVertexNormals();
    const m=new THREE.Mesh(g,mat);m.receiveShadow=true;m.userData.keep=true;group.add(m);return m;
  }
  const harborRoad=path([[0,CITY_HALF+8],[-82,210],[-165,247],[-245,285],[-325,332],[-365,379],[-403,382],[PORT_CENTER.x,PORT_CENTER.z-15]],9.2);
  const mountainRoad=path([[0,-CITY_HALF-12],[-45,-231],[-80,-285],[-57,-337],[-18,-386],[30,-374],[25,-348],[FROST_PORTAL.x,FROST_PORTAL.z+7]],7.4,new THREE.MeshLambertMaterial({color:0x7b847f,side:THREE.DoubleSide}));
  // A dark cave mouth at the summit. The interactive portal is attached by main.js at ground height.
  const cave=new THREE.Group();cave.position.set(FROST_PORTAL.x,townElevation(FROST_PORTAL.x,FROST_PORTAL.z,world),FROST_PORTAL.z-2);
  cave.name='frost-summit-cave';cave.userData.keep=true;
  const cr=new THREE.MeshLambertMaterial({color:0x343945,flatShading:true,side:THREE.DoubleSide});
  for(const [x,y,z,s] of [[-7,4,0,5.2],[7,4,0,5.1],[-5,9,-3,5.8],[5,9,-3,5.8],[0,12,-3,6.4],[-11,2,-4,4.6],[11,2,-4,4.6]]){
    const rock=new THREE.Mesh(new THREE.DodecahedronGeometry(s,0),cr);rock.position.set(x,y,z);
    rock.castShadow=true;rock.receiveShadow=true;cave.add(rock);
  }
  group.add(cave);
  // The harbor is a small separately walled village with a gated eastern road approach.
  const harbor=new THREE.Group();harbor.name='walled-harbor';harbor.position.set(PORT_CENTER.x,0,PORT_CENTER.z);
  const hm=new THREE.MeshLambertMaterial({color:0x96989e}),wood=new THREE.MeshLambertMaterial({color:0x634d3d});
  function piece(w,h,l,x,y,z,mat=hm){
    const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,l),mat);m.position.set(x,y,z);m.castShadow=m.receiveShadow=true;harbor.add(m);
  }
  const W=68,D=64;
  // West-facing harbor mouth: a pier opens onto the sea, not a solid wall.
  // Retain the two side ramparts and the original eastern road gate.
  piece(2.6,6,D-15,-W,3,-(D+15)/2);
  piece(2.6,6,D-15,-W,3,(D+15)/2);
  piece(W*2,6,2.6,0,3,-D);piece(W*2,6,2.6,0,3,D);
  piece(2.6,6,D-18,W,3,-D/2-9);piece(2.6,6,D-18,W,3,D/2+9);
  for(const x of [-W,W])for(const z of [-D,D]){
    const tower=new THREE.Mesh(new THREE.CylinderGeometry(4.5,5.3,11,10),hm);
    tower.position.set(x,5.5,z);tower.castShadow=tower.receiveShadow=true;harbor.add(tower);
    const cap=new THREE.Mesh(new THREE.ConeGeometry(5.6,5.5,10),wood);cap.position.set(x,13.5,z);cap.castShadow=true;harbor.add(cap);
  }
  const archTop=new THREE.Mesh(new THREE.BoxGeometry(4,1.7,34),hm);archTop.position.set(W,8.1,0);archTop.castShadow=true;harbor.add(archTop);
  // Real corner harbor: weathered coastal stone, wooden piers, mooring posts
  // and rope; the lava and obsidian props belong ONLY at Ashen Titan.
  const plank=new THREE.MeshLambertMaterial({color:0x80674a});
  const piling=new THREE.MeshLambertMaterial({color:0x564735});
  const rope=new THREE.MeshLambertMaterial({color:0xb2a37e});
  // Walk-out dock through the new west-facing opening. No new collision boxes:
  // the player can enter the water from either side of the wooden pier.
  piece(44,.35,9,-66,.6,0,plank);
  for(const x of [-84,-72,-60,-48]){
    for(const z of [-4.6,4.6]){
      const post=new THREE.Mesh(new THREE.CylinderGeometry(.58,.72,3.2,8),piling);
      post.position.set(x,-.55,z);post.castShadow=true;harbor.add(post);
      const cap=new THREE.Mesh(new THREE.CylinderGeometry(.72,.72,.2,8),rope);
      cap.position.set(x,1.2,z);harbor.add(cap);
    }
  }
  for(const z of [-22,22]){
    piece(28,.27,5,-62,.51,z,plank);
    for(const x of [-73,-51]){
      const post=new THREE.Mesh(new THREE.CylinderGeometry(.5,.65,2.1,7),piling);
      post.position.set(x,-.35,z);
      post.castShadow=true;harbor.add(post);
    }
  }
  harbor.userData.region='coastal-corner-harbor';
  group.add(harbor);
  // Solid harbor ramparts; a broad road-sized opening remains on the east.
  const cx=PORT_CENTER.x,cz=PORT_CENTER.z;
  for(const [x,z,w,depth] of [
   [cx-W,cz-(D+15)/2,2.6,D-15],[cx-W,cz+(D+15)/2,2.6,D-15],
   [cx,cz-D,W*2,2.6],[cx,cz+D,W*2,2.6],
   [cx+W,cz-D/2-9,2.6,D-18],[cx+W,cz+D/2+9,2.6,D-18]
  ])colliders.push({type:'box',minX:x-w/2,maxX:x+w/2,minZ:z-depth/2,maxZ:z+depth/2});
  // Water is a real animated, swimmable surface; unlike lava it doesn't damage the player.
  const waterGeo=new THREE.PlaneGeometry(93,110,24,28);
  const waterMat=new THREE.MeshPhongMaterial({color:0x237fa4,emissive:0x0a3547,transparent:true,opacity:.84,shininess:105,side:THREE.DoubleSide,depthWrite:false});
  const water=new THREE.Mesh(waterGeo,waterMat);
  water.rotation.x=-Math.PI/2;water.position.set(PORT_CENTER.x-49,.17,PORT_CENTER.z);
  water.receiveShadow=true;water.userData.keep=true;water.name='harbor-swim-water';group.add(water);
  const wp=waterGeo.attributes.position,original=wp.array.slice();
  const waterAt=(x,z)=>x<PORT_CENTER.x-26 && x>PORT_CENTER.x-96 && Math.abs(z-PORT_CENTER.z)<51;
  function updateWater(t){
    for(let i=0;i<wp.count;i++){const ix=i*3,x=original[ix],y=original[ix+1];
      wp.array[ix+2]=.17*Math.sin(x*.19+t*1.6)+.11*Math.sin(y*.24-t*1.15);}
    wp.needsUpdate=true;
    if((Math.floor(t*10)%4)===0)waterGeo.computeVertexNormals();
  }
  const insideField=(x,z,pad=0)=>FIELDS.some(f=>Math.abs(x-f.x)<f.w/2+pad&&Math.abs(z-f.z)<f.d/2+pad);
  const nearBuilding=(x,z,pad=0)=>buildings.some(b=>{
    const bx=b.cx*spacing,bz=b.id==='gatehouse'?CITY_HALF-1.2:b.cz*spacing;
    return Math.abs(x-bx)<26+pad&&Math.abs(z-bz)<26+pad;
  });
  // Clear avenues across the centre, the old village, gatehouse approach and a ring road.
  const route=(x,z,pad=0)=>Math.abs(x)<15+pad||Math.abs(z)<10+pad||
    Math.abs(Math.hypot(x,z)-RING)<8+pad;
  const possible=(x,z,pad=0)=>Math.max(Math.abs(x),Math.abs(z))>CORE+pad &&
    Math.max(Math.abs(x),Math.abs(z))<usable-pad &&
    !route(x,z,pad) && !insideField(x,z,pad) && !nearBuilding(x,z,pad) &&
    balthrixTrailDistance(x,z)>BALTHRIX_TRAIL_HALF_WIDTH+8+pad &&
    Math.hypot(x-FROST_SUMMIT.x,z-FROST_SUMMIT.z)>46+pad &&
    Math.hypot(x-TITAN_CENTER.x,z-TITAN_CENTER.z)>76+pad &&
    Math.hypot(x-PORT_CENTER.x,z-PORT_CENTER.z)>65+pad;
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
    colliders.push({type:'circle',x,z,r:.42*s+.15,cameraTop:townElevation(x,z,world)+15*s,tree:true});
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
  return {group,cull,stats,terrain,balthrixTrail,poolMeshes,harborRoad,mountainRoad,cave,harbor,water,waterAt,updateWater,heightAt:(x,z)=>townElevation(x,z,world),chunkCount:meshes.length,fieldCount:stats.fields};
}
