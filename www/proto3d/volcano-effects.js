/* Ashen Titan territory — one batched volcanic scenery layer.
 * This builds decorative basalt shards and free-floating ember motes only.
 * The existing shared terrain determines walking height; LAVA_POOLS remains
 * the sole authoritative damage footprint in bossregions.js. Never create
 * new untested colliders or new damaging regions just for visuals.
 */
import * as THREE from './vendor/three.module.js';
import { TITAN_CENTER, LAVA_POOLS } from './bossregions.js';

const emberCount=128, basaltCount=42, nearRadius=225;
const fract=n=>n-Math.floor(n);
const seeded=n=>fract(Math.sin(n*83.937+17.23)*43758.5453);
export function makeVolcanoEffects({group,poolMeshes,heightAt}){
  const crater=new THREE.Group();
  crater.name='ashen-titan-volcano-environment';
  group.add(crater);
  // A single instanced basalt silhouette grows along the broken outer rim.
  // These are set farther from the central Titan combat platform; scenery
  // remains non-blocking until its route collisions are verified on devices.
  const shardGeometry=new THREE.ConeGeometry(1,1,5);
  const shardMaterial=new THREE.MeshLambertMaterial({color:0x27222b,flatShading:true});
  const shards=new THREE.InstancedMesh(shardGeometry,shardMaterial,basaltCount);
  shards.name='titan-basalt-rim-spires';
  shards.castShadow=false;shards.receiveShadow=true;
  const dummy=new THREE.Object3D();
  for(let i=0;i<basaltCount;i++){
    const angle=i*Math.PI*2/basaltCount+.09*seeded(i+5);
    const radius=87+seeded(i+17)*31;
    const x=TITAN_CENTER.x+Math.cos(angle)*radius,z=TITAN_CENTER.z+Math.sin(angle)*radius;
    const height=4.0+seeded(i+211)*14;
    const width=1.2+seeded(i+51)*3.8;
    dummy.position.set(x,heightAt(x,z)+height*.48,z);
    dummy.scale.set(width,height,width*(.8+seeded(i+81)*.4));
    dummy.rotation.set(.08*Math.sin(i),angle,.1*Math.cos(i));
    dummy.updateMatrix();shards.setMatrixAt(i,dummy.matrix);
  }
  shards.instanceMatrix.needsUpdate=true;
  shards.computeBoundingSphere();
  crater.add(shards);
  // One dynamic draw call, no new per-frame meshes and no shadow maps.
  // Embers float upward from the actual (unchanged) damaging lava pools.
  const positions=new Float32Array(emberCount*3);
  const base=new Float32Array(emberCount*3);
  const phases=new Float32Array(emberCount);
  for(let i=0;i<emberCount;i++){
    const pool=LAVA_POOLS[i%LAVA_POOLS.length];
    const a=seeded(i+37)*2*Math.PI;
    const rad=pool.r*(.12+.7*seeded(i+101));
    const x=pool.x+Math.cos(a)*rad,z=pool.z+Math.sin(a)*rad;
    const k=i*3;
    base[k]=x;base[k+1]=heightAt(x,z)+.4;base[k+2]=z;
    positions[k]=x;positions[k+1]=base[k+1];positions[k+2]=z;
    phases[i]=seeded(i+311);
  }
  const emberGeo=new THREE.BufferGeometry();
  const attribute=new THREE.BufferAttribute(positions,3);
  attribute.setUsage(THREE.DynamicDrawUsage);
  emberGeo.setAttribute('position',attribute);
  // Material is additive so points glow even without increasing all sun light.
  const emberMat=new THREE.PointsMaterial({
    color:0xff8d46,size:1.05,sizeAttenuation:true,
    transparent:true,opacity:.72,depthWrite:false,
    blending:THREE.AdditiveBlending
  });
  const embers=new THREE.Points(emberGeo,emberMat);
  embers.name='titan-crater-floating-embers';
  embers.castShadow=false;embers.frustumCulled=false;crater.add(embers);
  const glowLights=[];
  for(const [x,z] of [[402,-419],[449,-371]]){
    const light=new THREE.PointLight(0xff632a,1.0,77,2);
    light.position.set(x,heightAt(x,z)+9,z);
    light.castShadow=false;crater.add(light);glowLights.push(light);
  }
  const mat=poolMeshes[0]?.material;
  let active=false,lastUpdate=NaN;
  function update(t,heroX,heroZ){
    const near=Number.isFinite(heroX)&&Number.isFinite(heroZ)&&
      Math.hypot(heroX-TITAN_CENTER.x,heroZ-TITAN_CENTER.z)<nearRadius;
    active=near;
    crater.visible=near;
    if(!near || !Number.isFinite(t))return false;
    // Pulsating lava emission and local glow WITHOUT altering lava damage
    // or geometry; no large permanent scene-wide brightness changes.
    if(mat)mat.emissiveIntensity=1.10+.24*(.5+.5*Math.sin(t*1.8));
    for(let i=0;i<glowLights.length;i++)
      glowLights[i].intensity=.85+.24*Math.sin(t*1.15+i*1.8);
    for(let i=0;i<emberCount;i++){
      const p=(t*.085+phases[i])%1,k=i*3;
      positions[k]=base[k]+Math.sin(t*1.12+i*2.35)*p*1.8;
      positions[k+1]=base[k+1]+1+p*12;
      positions[k+2]=base[k+2]+Math.cos(t*.87+i*1.17)*p*1.8;
    }
    attribute.needsUpdate=true;lastUpdate=t;
    return true;
  }
  crater.visible=false;
  return {group:crater,embers,shards,glowLights,update,
    get active(){return active;},get lastUpdate(){return lastUpdate;},
    counts:{embers:emberCount,basalt:basaltCount}};
}
