/* Balthrix aftermath: fallen trunks, splintered stumps and broken branches.
 * Reuses four instanced batches, so the entire patrol's damage adds only a
 * handful of draw calls on Android. All positions share the walkable heightmap. */
import * as THREE from './vendor/three.module.js';
import { fallenTreeSites } from './bossregions.js';
import { buildBalthrixCorridor } from './balthrix-corridor.js';

export function buildBalthrixTrail(parent, heightAt, colliders) {
  const corridor=buildBalthrixCorridor(parent,heightAt,colliders);
  const sites=fallenTreeSites();
  const bark=new THREE.MeshLambertMaterial({color:0x59402a,flatShading:true});
  const charred=new THREE.MeshLambertMaterial({color:0x242022,flatShading:true});
  const broken=new THREE.MeshLambertMaterial({color:0x9b7451,flatShading:true});
  const trunks=new THREE.CylinderGeometry(.68,.92,1,8);
  const sticks=new THREE.CylinderGeometry(.14,.23,1,6);
  const stumpGeo=new THREE.CylinderGeometry(.38,.65,1.6,7);
  const splinterGeo=new THREE.ConeGeometry(.54,1.7,6);
  const normal=sites.filter(s=>!s.burnt),burnt=sites.filter(s=>s.burnt);
  const buildMesh=(geometry,material,count,name)=>{
    const m=new THREE.InstancedMesh(geometry,material,Math.max(1,count));
    m.name=name;m.count=count;m.castShadow=true;m.receiveShadow=true;
    // Main-game static merge must not fold an instanced tree into a single mesh.
    m.userData.keep=true; m.frustumCulled=false; parent.add(m);return m;
  };
  const logs=[buildMesh(trunks,bark,normal.length,'balthrix-fallen-trunks'),
    buildMesh(trunks,charred,burnt.length,'balthrix-charred-trunks')];
  const stumps=buildMesh(stumpGeo,bark,sites.length,'balthrix-shattered-stumps');
  const splinters=buildMesh(splinterGeo,broken,sites.length,'balthrix-splintered-ends');
  const branches=buildMesh(sticks,charred,sites.length*2,'balthrix-broken-branches');
  const dummy=new THREE.Object3D(),up=new THREE.Vector3(0,1,0),dir=new THREE.Vector3();
  const set=(mesh,index,x,y,z,quat,sx,sy,sz)=>{
    dummy.position.set(x,y,z);dummy.quaternion.copy(quat);
    dummy.scale.set(sx,sy,sz);dummy.updateMatrix();mesh.setMatrixAt(index,dummy.matrix);
  };
  const upright=new THREE.Quaternion();let branchIdx=0;
  for(let k=0;k<sites.length;k++){
    const s=sites[k],ux=Math.sin(s.angle),uz=Math.cos(s.angle),half=s.length*.5;
    const yA=heightAt(s.x-ux*half,s.z-uz*half),yB=heightAt(s.x+ux*half,s.z+uz*half);
    dir.set(ux*s.length,yB-yA,uz*s.length).normalize();
    const q=new THREE.Quaternion().setFromUnitVectors(up,dir);
    const bin=s.burnt?1:0,idx=(s.burnt?burnt:normal).indexOf(s);
    const y=(yA+yB)*.5+.72,diam=.75+(k%3)*.14;
    set(logs[bin],idx,s.x,y,s.z,q,diam,s.length,diam);
    const ax=s.x-ux*half,az=s.z-uz*half;
    set(stumps,k,ax, heightAt(ax,az)+.78,az,upright,.85+(k%2)*.22,1,.85+(k%2)*.22);
    set(splinters,k,ax, heightAt(ax,az)+1.85,az,upright,.8,1,.8);
    // Short crossed limbs on each trunk; branches are genuinely lying in 3D.
    for(const sign of [-1,1]){
      const j=k*2+(sign===1?1:0),f=sign*.28;
      const px=s.x+ux*half*f,pz=s.z+uz*half*f;
      const aa=s.angle+sign*1.03,dx=Math.sin(aa),dz=Math.cos(aa);
      const bq=new THREE.Quaternion().setFromUnitVectors(up,dir.set(dx,.08*sign,dz).normalize());
      set(branches,branchIdx++,px+dx*1.1,heightAt(px,pz)+.56,pz+dz*1.1,bq,1,2.9+(j%3),1);
    }
    // Collision approximates the prone trunk, rather than an enormous box.
    // It leaves the ~20 unit patrol corridor unobstructed for Balthrix.
    for(const fraction of [-.35,0,.35]){
      colliders.push({type:'circle',x:s.x+ux*s.length*fraction,z:s.z+uz*s.length*fraction,r:1.0*diam+.3});
    }
    colliders.push({type:'circle',x:ax,z:az,r:.8});
  }
  for(const mesh of [...logs,stumps,splinters,branches])mesh.instanceMatrix.needsUpdate=true;
  return {sites,count:sites.length,meshes:[...corridor.meshes,...logs,stumps,splinters,branches],corridor};
}
