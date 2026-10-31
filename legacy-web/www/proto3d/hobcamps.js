/* Varnethryl Hobgoblin encampments. Immutable locations are shared with the combat spawner.
   Geometry uses a few reusable meshes, no lights/shadow-map allocations per frame. */
import * as THREE from 'three';
export const HOB_CAMPS = Object.freeze([
  Object.freeze({id:'blackbriar',name:'Blackbriar Warcamp',x:-323,z:-178,guards:4}),
  Object.freeze({id:'thornwatch',name:'Thornwatch Outpost',x:-318,z:276,guards:3}),
  Object.freeze({id:'ironfang',name:'Ironfang Encampment',x:305,z:264,guards:4})
]);
export function buildHobgoblinCamps(scene,heightAt=()=>0) {
  const root=new THREE.Group();root.name='hobgoblin-encampments';scene.add(root);
  const canvas=()=>0; // no texture allocations
  const mats={
    hide:new THREE.MeshLambertMaterial({color:0x48372d,side:THREE.DoubleSide}),
    hide2:new THREE.MeshLambertMaterial({color:0x653d37,side:THREE.DoubleSide}),
    timber:new THREE.MeshLambertMaterial({color:0x433022}),
    iron:new THREE.MeshLambertMaterial({color:0x575d61}),
    ember:new THREE.MeshBasicMaterial({color:0xff813b}),
    ground:new THREE.MeshBasicMaterial({color:0x342a24,transparent:true,opacity:.44,depthWrite:false,side:THREE.DoubleSide}),
    banner:new THREE.MeshLambertMaterial({color:0x822e2a,side:THREE.DoubleSide})
  };
  const tent=new THREE.ConeGeometry(4.6,5.6,4), log=new THREE.CylinderGeometry(.26,.31,4.8,6), pole=new THREE.CylinderGeometry(.11,.16,4.5,5);
  const stake=new THREE.ConeGeometry(.28,2.5,5), campFloor=new THREE.CircleGeometry(15,22);
  const fire=new THREE.SphereGeometry(.68,7,6), flag=new THREE.PlaneGeometry(1.5,2);
  const sites=[];
  for(const site of HOB_CAMPS){
    const g=new THREE.Group();g.name='hob-camp-'+site.id;root.add(g);
    const y=(x,z)=>heightAt(x,z)||0;
    const put=(mesh,x,z,lift=0)=>{mesh.position.set(x,y(x,z)+lift,z);mesh.castShadow=mesh.material!==mats.ember&&mesh.material!==mats.ground;mesh.receiveShadow=true;g.add(mesh);return mesh;};
    const floor=put(new THREE.Mesh(campFloor,mats.ground),site.x,site.z,.13);floor.rotation.x=-Math.PI/2;floor.castShadow=false;
    for(let i=0;i<3;i++){
      const a=i*2*Math.PI/3+.35,x=site.x+Math.cos(a)*8.2,z=site.z+Math.sin(a)*8.2;
      const t=put(new THREE.Mesh(tent,i===1?mats.hide2:mats.hide),x,z,2.8);t.rotation.y=Math.PI/4+a;
      const door=put(new THREE.Mesh(new THREE.PlaneGeometry(1.7,2.5),mats.timber),x-Math.cos(a)*2.9,z-Math.sin(a)*2.9,1.3);door.rotation.y=-a+Math.PI/2;
    }
    for(let i=0;i<10;i++){
      const a=i*2*Math.PI/10,r=12.6,x=site.x+Math.cos(a)*r,z=site.z+Math.sin(a)*r;
      if(i===1||i===2)continue; // open approach for the player
      const st=put(new THREE.Mesh(stake,mats.timber),x,z,1.28);st.rotation.z=.12*Math.sin(i*7);
    }
    for(let i=0;i<3;i++){
      const a=i*2*Math.PI/3+.3,x=site.x+Math.cos(a)*3.1,z=site.z+Math.sin(a)*3.1;
      const l=put(new THREE.Mesh(log,mats.timber),x,z,.3);l.rotation.z=Math.PI/2;l.rotation.y=a+.6;
    }
    put(new THREE.Mesh(fire,mats.ember),site.x,site.z,.72).castShadow=false;
    const px=site.x+10,pz=site.z-7;
    put(new THREE.Mesh(pole,mats.timber),px,pz,2.25);
    const f=put(new THREE.Mesh(flag,mats.banner),px+.82,pz,3.35);f.rotation.y=.18;f.castShadow=true;
    sites.push({site,group:g});
  }
  const cull=(x,z)=>{for(const {site,group} of sites)group.visible=Math.hypot(site.x-x,site.z-z)<170;};
  return {group:root,cull,sites};
}
