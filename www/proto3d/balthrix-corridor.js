/* Owner-approved Balthrix perimeter trench. One curved GPU ribbon with raised,
 * walkable earthen berms; spaced debris is instanced so the 1 km map is mobile-safe.
 * All placement uses the same spline as his animation/encounter controller.
 */
import * as THREE from './vendor/three.module.js';
import {BALTHRIX_ROUTE_LENGTH,balthrixPosition,PORT_CENTER,FROST_SUMMIT,
  balthrixCorridorDistance} from './bossregions.js';

export function buildBalthrixCorridor(group,heightAt,colliders){
 const count=Math.ceil(BALTHRIX_ROUTE_LENGTH/4);
 const sections=[-15,-12,-9,-7,-4,0,4,7,9,12,15],positions=[],colors=[],indices=[];
 const dirt=new THREE.Color('#55412e'),track=new THREE.Color('#443425'),
   shoulder=new THREE.Color('#7c6244'),outer=new THREE.Color('#526048');
 const colorAt=d=>d<6?track:d<10?dirt:d<13?shoulder:outer;
 for(let i=0;i<=count;i++){
  const p=balthrixPosition(i*BALTHRIX_ROUTE_LENGTH/count/14),nX=Math.cos(p.yaw),nZ=-Math.sin(p.yaw);
  for(let j=0;j<sections.length;j++){
   const off=sections[j],x=p.x+nX*off,z=p.z+nZ*off;
   const h=heightAt(x,z)+.12;
   positions.push(x,h,z);
   const tint=.94+.06*Math.sin(i*.82+j*1.7);
   const col=colorAt(Math.abs(off));
   colors.push(col.r*tint,col.g*tint,col.b*tint);
  }
  if(i<count)for(let j=0;j<sections.length-1;j++){
   const a=i*sections.length+j,b=a+sections.length;
   indices.push(a,b,a+1,a+1,b,b+1);
  }
 }
 const geometry=new THREE.BufferGeometry();
 geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
 geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
 geometry.setIndex(indices);geometry.computeVertexNormals();
 const ribbon=new THREE.Mesh(geometry,new THREE.MeshLambertMaterial({
   vertexColors:true,side:THREE.DoubleSide,flatShading:true}));
 ribbon.name='BALTHRIX_RAISED_PERIMETER_TRAIL';
 ribbon.receiveShadow=true;ribbon.userData.keep=true;group.add(ribbon);
 // Broken boulders have been shoved OUT of the centre of the serpent track.
 const sites=[];
 for(let i=0;i<58;i++){
  const p=balthrixPosition((i+.31)*BALTHRIX_ROUTE_LENGTH/58/14),
    side=i%2===0?1:-1,spread=18+(i%5)*1.65,
    x=p.x+side*Math.cos(p.yaw)*spread,
    z=p.z-side*Math.sin(p.yaw)*spread;
  if(Math.hypot(x-PORT_CENTER.x,z-PORT_CENTER.z)<142||
      Math.hypot(x-FROST_SUMMIT.x,z-FROST_SUMMIT.z)<147||
      Math.max(Math.abs(x),Math.abs(z))>544||
      balthrixCorridorDistance(x,z)<13)continue;
  sites.push({x,z,angle:i*1.89,scale:.8+(i%4)*.23});
 }
 const rock=new THREE.InstancedMesh(new THREE.DodecahedronGeometry(1,0),
   new THREE.MeshLambertMaterial({color:0x71706c,flatShading:true}),sites.length);
 const shard=new THREE.InstancedMesh(new THREE.ConeGeometry(.7,1.7,5),
   new THREE.MeshLambertMaterial({color:0x52463b,flatShading:true}),sites.length);
 for(const [i,o] of sites.entries()){
   const t=new THREE.Object3D();
   t.position.set(o.x,heightAt(o.x,o.z)+o.scale*.7,o.z);
   t.rotation.set(.18,o.angle,.16);
   t.scale.set(o.scale*1.3,o.scale*.8,o.scale);t.updateMatrix();rock.setMatrixAt(i,t.matrix);
   t.position.set(o.x+2,heightAt(o.x+2,o.z)+.7,o.z+1.2);
   t.scale.set(.8,1,.9);t.updateMatrix();shard.setMatrixAt(i,t.matrix);
   if(i%3===0)colliders.push({type:'circle',x:o.x,z:o.z,r:1.15*o.scale});
 }
 rock.name='BALTHRIX_SHOVED_ASIDE_ROCKS';shard.name='BALTHRIX_SPLINTERED_DEBRIS';
 rock.userData.keep=shard.userData.keep=true;
 rock.castShadow=shard.castShadow=true;
 rock.instanceMatrix.needsUpdate=shard.instanceMatrix.needsUpdate=true;
 group.add(rock,shard);
 // Light broken branches and crushed splinters cross the scuffed middle, but
 // no invisible wall collider blocks the monster's 20-unit movement channel.
 const scraps=new THREE.InstancedMesh(new THREE.CylinderGeometry(.14,.2,1,5),
   new THREE.MeshLambertMaterial({color:0x393026,flatShading:true}),44);
 scraps.name='BALTHRIX_CRUSHED_PATH_DEBRIS';
 scraps.userData.keep=true;scraps.castShadow=false;
 const dummy=new THREE.Object3D();
 for(let i=0;i<44;i++){
   const p=balthrixPosition((i+.5)*BALTHRIX_ROUTE_LENGTH/44/14),
     lateral=((i*7)%13)-6,x=p.x+Math.cos(p.yaw)*lateral,
     z=p.z-Math.sin(p.yaw)*lateral;
   dummy.position.set(x,heightAt(x,z)+.19,z);
   dummy.rotation.set(Math.PI/2,p.yaw+(i%4)*.44,0);
   dummy.scale.set(.7,2.1+(i%4)*.55,.9);dummy.updateMatrix();
   scraps.setMatrixAt(i,dummy.matrix);
 }
 scraps.instanceMatrix.needsUpdate=true;group.add(scraps);
 return {meshes:[ribbon,rock,shard,scraps],rockCount:sites.length,length:BALTHRIX_ROUTE_LENGTH};
}
