/* Frostrealm's cavern shell and icy details. It is a genuine enclosed 3D
 * environment, not a snow field with a cave-shaped entrance. Collision leaves
 * the brothers' arena and the player's path from the entrance completely open. */
import * as THREE from './vendor/three.module.js';

export function buildFrostCave(group, half, elevation, exclusions=[]) {
  const COLS=[];
  const rock=new THREE.MeshLambertMaterial({color:0x202c3b,flatShading:true,side:THREE.DoubleSide});
  const ice=new THREE.MeshPhongMaterial({color:0x638ca8,emissive:0x0e2437,flatShading:true,shininess:88,side:THREE.DoubleSide});
  const glow=new THREE.MeshPhongMaterial({color:0x83c9f3,emissive:0x2d7399,shininess:125,flatShading:true});
  const roofRadius=half+32,roofHeight=68;
  const ceilingAt=(x,z)=>roofHeight*Math.sqrt(Math.max(0,1-(x*x+z*z)/(roofRadius*roofRadius)));
  // The hemisphere closes the entire playable space. An inside-visible surface
  // prevents the bright overworld sky from bleeding through the cave ceiling.
  const vault=new THREE.Mesh(new THREE.SphereGeometry(1,52,22,0,Math.PI*2,0,Math.PI/2),rock);
  vault.name='enclosing-ice-cave-vault';
  vault.scale.set(roofRadius,roofHeight,roofRadius);
  vault.receiveShadow=true;group.add(vault);
  const ringSegments=52,ringHeight=22,verts=[],index=[];
  for(let i=0;i<=ringSegments;i++){
    const a=i*2*Math.PI/ringSegments,rad=half+4+3*Math.sin(i*3.2);
    const x=rad*Math.cos(a),z=rad*Math.sin(a),y=elevation(x,z);
    verts.push(x,y-2,z,x,ringHeight+5*Math.sin(i*.9),z);
    if(i<ringSegments){const n=i*2;index.push(n,n+1,n+2,n+1,n+3,n+2);}
  }
  const wg=new THREE.BufferGeometry();wg.setAttribute('position',new THREE.Float32BufferAttribute(verts,3));wg.setIndex(index);wg.computeVertexNormals();
  const walls=new THREE.Mesh(wg,rock);walls.name='cave-outer-walls';walls.receiveShadow=true;group.add(walls);
  const count=105,icicleCount=165,crystalCount=76,randSeed={v:80220};
  const rand=()=>{let x=randSeed.v|0;x^=x<<13;x^=x>>>17;x^=x<<5;randSeed.v=x;return (x>>>0)/4294967296;};
  const caveMesh=(geom,mat,n,name)=>{
    const mesh=new THREE.InstancedMesh(geom,mat,n);mesh.name=name;mesh.castShadow=true;mesh.receiveShadow=true;mesh.frustumCulled=false;group.add(mesh);return mesh;
  };
  const stalagmites=caveMesh(new THREE.ConeGeometry(1,1,7),ice,count,'cave-floor-ice-spires');
  const icicles=caveMesh(new THREE.ConeGeometry(1,1,7),ice,icicleCount,'ceiling-icicles');
  const crystals=caveMesh(new THREE.OctahedronGeometry(1,0),glow,crystalCount,'ice-crystal-clusters');
  const dummy=new THREE.Object3D();
  const put=(mesh,i,x,y,z,sx,sy,sz,flip=false)=>{
    dummy.position.set(x,y,z);dummy.scale.set(sx,sy,sz);
    dummy.rotation.set(flip?Math.PI:0,rand()*Math.PI*2,0);
    dummy.updateMatrix();mesh.setMatrixAt(i,dummy.matrix);
  };
  const avoid=(x,z,r)=>exclusions.some(p=>Math.hypot(x-p.x,z-p.z)<(p.r||0)+r)||
    // Navigable spine from entry to Frost Troll brothers.
    (Math.abs(x)<30+r && z>-120-r && z<194+r);
  let n=0,k=0,j=0,tries=0;
  while((n<count||k<icicleCount||j<crystalCount)&&tries++<15000){
    const x=(rand()*2-1)*(half-7),z=(rand()*2-1)*(half-7);
    const r=Math.hypot(x,z);
    if(r>half-8)continue;
    const floor=elevation(x,z),ceiling=ceilingAt(x,z);
    if(ceiling-floor<13)continue;
    if(n<count&&!avoid(x,z,8)){
      const size=.7+rand()*2.8,height=3.2+rand()*11;
      put(stalagmites,n++,x,floor+height/2,z,size,height,size);
      if(size>1.8)COLS.push({type:'circle',x,z,r:size*.55});
    }
    if(k<icicleCount){
      const height=2.6+rand()*7.5;
      put(icicles,k++,x,ceiling-height*.48-1.1,z,.3+rand()*1.05,height,.3+rand()*1.05,true);
    }
    if(j<crystalCount&&!avoid(x,z,5)){
      const size=.7+rand()*2,height=size*(2+rand()*3.2);
      put(crystals,j++,x,floor+height*.55,z,size,height,size);
    }
  }
  stalagmites.count=n;icicles.count=k;crystals.count=j;
  for(const mesh of [stalagmites,icicles,crystals])mesh.instanceMatrix.needsUpdate=true;
  // Colored bounce light from clusters; keep shadow casting disabled on phones.
  for(const [x,z] of [[-103,-85],[91,82],[-99,118],[112,-97],[0,-173]]){
    const light=new THREE.PointLight(0x7ab5ed,.75,83,2);
    light.position.set(x,elevation(x,z)+9,z);light.castShadow=false;group.add(light);
  }
  return {colliders:COLS,roof:vault,walls,stalagmites,icicles,crystals,ceilingAt};
}
