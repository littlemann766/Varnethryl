/* Varnethryl: Frostbound Cavern.
   Separate walkable realm for the Frost Troll brothers, linked to the snowy summit
   of the enlarged overworld. Stable coordinates; never changes town saves. */
import * as THREE from './vendor/three.module.js';
export const FROST_REALM = Object.freeze({ cx: 1910, cz: 0, half: 220 });
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const smooth=(a,b,v)=>{const t=clamp((v-a)/(b-a),0,1);return t*t*(3-2*t);};
export function frostHeight(x,z) {
  const dx=x-FROST_REALM.cx,dz=z-FROST_REALM.cz,r=Math.hypot(dx,dz);
  const noise=1.45*Math.sin(dx/19)*Math.sin(dz/23)+1.4*Math.sin((dx+dz)/41);
  const hills=10*smooth(57,115,r)+37*smooth(120,217,r);
  // Spawn and portal lie on a safe, nearly level valley floor; the ridges and
  // outer ice walls are naturally climbable instead of billboard mountains.
  return r<34?0:Math.max(-2,noise*smooth(34,59,r)+hills);
}
const iceMat=new THREE.MeshLambertMaterial({vertexColors:true,side:THREE.DoubleSide});
function iceGround(){
  const N=112,L=FROST_REALM.half,V=new Float32Array((N+1)**2*3),C=new Float32Array(V.length),idx=[];
  const a=new THREE.Color(),pale=new THREE.Color(0xc6eff4),blue=new THREE.Color(0x73bbce),
    white=new THREE.Color(0xf3f9fd),slate=new THREE.Color(0x64869c);
  for(let z=0;z<=N;z++)for(let x=0;x<=N;x++){
    const wx=FROST_REALM.cx+(x/N*2-1)*L,wz=FROST_REALM.cz+(z/N*2-1)*L,y=frostHeight(wx,wz),i=(z*(N+1)+x)*3;
    V[i]=wx;V[i+1]=y;V[i+2]=wz;
    a.copy(blue).lerp(pale,.45+.27*Math.sin(wx*.076)*Math.sin(wz*.064));
    if(y>15)a.lerp(white,smooth(14,45,y)*.66);
    if(y>41)a.lerp(slate,smooth(40,55,y)*.35);
    C[i]=a.r;C[i+1]=a.g;C[i+2]=a.b;
  }
  for(let z=0;z<N;z++)for(let x=0;x<N;x++){const i=z*(N+1)+x;idx.push(i,i+N+1,i+1,i+1,i+N+1,i+N+2);}
  const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.BufferAttribute(V,3));geo.setAttribute('color',new THREE.BufferAttribute(C,3));geo.setIndex(idx);geo.computeVertexNormals();
  const m=new THREE.Mesh(geo,iceMat);m.receiveShadow=true;m.castShadow=true;m.userData.keep=true;m.name='frostbound-climbable-ice-terrain';return m;
}
export function buildFrostRealm({scene}){
  const root=new THREE.Group();root.name='Frostbound Cavern · Frost Troll A and Frost Troll B';root.visible=false;scene.add(root);
  const colliders=[],mats=[
    new THREE.MeshLambertMaterial({color:0xa6dce9,emissive:0x143f51,emissiveIntensity:.2,flatShading:true}),
    new THREE.MeshLambertMaterial({color:0xd9f4f9,flatShading:true}),
    new THREE.MeshLambertMaterial({color:0x558ca6,flatShading:true})];
  root.add(iceGround());
  // Ice crystal formations ring the arena. Leave the spawn, two bosses and
  // direct approaches free of colliders so companions can follow.
  for(let j=0;j<44;j++){
    const t=j*2.3999632,rad=95+(j%7)*12,x=FROST_REALM.cx+Math.cos(t)*rad,z=FROST_REALM.cz+Math.sin(t)*rad;
    const tall=5+(j*13%17),rock=new THREE.Mesh(new THREE.ConeGeometry(1.8+j%3,tall,5),mats[j%3]);
    rock.position.set(x,frostHeight(x,z)+tall*.5,z);rock.rotation.z=Math.sin(t)*.21;rock.castShadow=true;rock.receiveShadow=true;root.add(rock);
    colliders.push({type:'circle',x,z,r:2.2+j%3});
  }
  // Two distinct frozen thrones, one for each brother (they spawn in front of them).
  for(const [x,z] of [[-37,70],[37,70]]){
    const base=new THREE.Mesh(new THREE.CylinderGeometry(9,10,2.4,8),mats[2]);base.position.set(FROST_REALM.cx+x,frostHeight(FROST_REALM.cx+x,FROST_REALM.cz+z)+1.2,FROST_REALM.cz+z);base.castShadow=true;base.receiveShadow=true;root.add(base);
    for(const d of [-5,5]){const sp=new THREE.Mesh(new THREE.ConeGeometry(2,12,5),mats[0]);sp.position.set(FROST_REALM.cx+x+d,6,FROST_REALM.cz+z+5);sp.castShadow=true;root.add(sp);}
  }
  // Snowflakes drift across the ice without allocating new meshes every frame.
  const count=320,geo=new THREE.BufferGeometry(),buf=new Float32Array(count*3),vel=new Float32Array(count);
  for(let i=0;i<count;i++){const j=i*3;buf[j]=FROST_REALM.cx+(i*47%370)-185;buf[j+1]=3+(i*29%38);buf[j+2]=FROST_REALM.cz+(i*71%370)-185;vel[i]=1+(i%8)*.31;}
  geo.setAttribute('position',new THREE.BufferAttribute(buf,3).setUsage(THREE.DynamicDrawUsage));
  const snow=new THREE.Points(geo,new THREE.PointsMaterial({color:0xf7ffff,size:.58,transparent:true,opacity:.8,depthWrite:false}));snow.frustumCulled=false;root.add(snow);
  const update=dt=>{if(!root.visible)return;for(let i=0;i<count;i++){const j=i*3;buf[j]+=dt*vel[i]*.23;buf[j+1]-=dt*vel[i];if(buf[j+1]<1){buf[j+1]=38;buf[j]=FROST_REALM.cx+(i*53%365)-182;}if(buf[j]>FROST_REALM.cx+185)buf[j]-=370;}geo.attributes.position.needsUpdate=true;};
  return {group:root,colliders,update,heightAt:frostHeight,center:FROST_REALM,spawn:{x:FROST_REALM.cx,z:FROST_REALM.cz-45},portal:{x:FROST_REALM.cx,z:FROST_REALM.cz-61},
    brothers:[{key:'frostbrother_a',x:FROST_REALM.cx-37,z:FROST_REALM.cz+48},{key:'frostbrother_b',x:FROST_REALM.cx+37,z:FROST_REALM.cz+48}]};
}
