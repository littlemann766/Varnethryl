/* Curved, fully three-dimensional medieval sailing ships for Tidewrack Harbor.
 * Procedural fallback until the approved external ship GLB is imported.
 * No box-shaped hulls, false flat bow cones or 2D cutout silhouettes. */
import * as THREE from './vendor/three.module.js';

export function buildSailingShip(scale=1, large=true) {
  const ship=new THREE.Group();ship.name=large?'tidewrack-three-mast-galleon':'tidewrack-boat';
  const wood=new THREE.MeshLambertMaterial({color:0x443027,side:THREE.DoubleSide});
  const trim=new THREE.MeshLambertMaterial({color:0x9a794b});
  const sail=new THREE.MeshLambertMaterial({color:0xd5c5a3,side:THREE.DoubleSide});
  const rope=new THREE.MeshLambertMaterial({color:0x554231});
  const frame=new THREE.MeshLambertMaterial({color:0x3a241e});
  function part(g,m,pos=[0,0,0]){const p=new THREE.Mesh(g,m);p.position.set(...pos);p.castShadow=true;p.receiveShadow=true;p.userData.keep=true;ship.add(p);return p;}
  // A closed, tapered boat hull with actual curved port/starboard and keel.
  const n=20,c=12,L=large?13:9,W=large?2.5:1.65,depth=large?2.3:1.25;
  const points=[],ind=[];
  for(let i=0;i<=n;i++){
    const t=i/n,z=(t-.5)*L,beam=Math.pow(Math.max(.001,Math.sin(Math.PI*t)),.55)*W+.09;
    for(let j=0;j<=c;j++){
      const a=-Math.PI/2+j*Math.PI/c;
      points.push(beam*Math.sin(a),1.62-depth*Math.cos(a),z);
      if(i<n&&j<c){const u=i*(c+1)+j;ind.push(u,u+c+1,u+1,u+1,u+c+1,u+c+2);}
    }
  }
  const hullGeo=new THREE.BufferGeometry();hullGeo.setAttribute('position',new THREE.Float32BufferAttribute(points,3));hullGeo.setIndex(ind);hullGeo.computeVertexNormals();part(hullGeo,wood);
  // Raised curved gunwale and deck prevent the ship looking like a hollow tube.
  for(const side of [-1,1]){
    const pts=[];
    for(let i=1;i<n;i++){const t=i/n,z=(t-.5)*L,beam=Math.pow(Math.max(.001,Math.sin(Math.PI*t)),.55)*W+.09;pts.push(new THREE.Vector3(side*beam,1.64,z));}
    part(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts),24,.095,5),trim);
  }
  part(new THREE.BoxGeometry(W*1.4,.16,L*.66),frame,[0,1.4,0]);
  // Bow stem rises at the prow; a small aft deck establishes the galleon profile.
  const bow=part(new THREE.CylinderGeometry(.15,.25,3.1,7),trim,[0,1.82,L*.47]);bow.rotation.x=-.5;
  part(new THREE.BoxGeometry(W*1.55,.2,L*.19),wood,[0,2.1,-L*.33]);
  const masts=large?[[-L*.24,8.4,3.8],[L*.1,11.8,4.6],[L*.35,7.8,3.2]]:[[0,5.5,2.7]];
  const line=(from,to,thick=.035)=>{
    const a=new THREE.Vector3(...from),b=new THREE.Vector3(...to),dif=b.clone().sub(a);
    const rod=part(new THREE.CylinderGeometry(thick,thick,dif.length(),5),rope);
    rod.position.copy(a.add(b).multiplyScalar(.5));rod.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),dif.normalize());return rod;
  };
  for(const [z,h,width] of masts){
    part(new THREE.CylinderGeometry(.13,.19,h,8),frame,[0,1.45+h*.5,z]);
    for(const [level,sh] of [[.55,.34],[.84,.23]]){
      const y=1.5+h*level, sailH=h*sh, upper=Math.max(.8,width*(level>.7?.7:1));
      // Sail has real bowed vertex geometry, not a flat PlaneGeometry.
      const ps=[],ix=[],sx=9,sy=7;
      for(let j=0;j<=sy;j++)for(let i=0;i<=sx;i++){
        const u=i/sx,v=j/sy,xx=(u-.5)*upper,yy=y+(v-.5)*sailH;
        const billow=.7*Math.sin(Math.PI*u)*Math.sin(Math.PI*v);
        ps.push(xx,yy,z+.22+billow);
        if(i<sx&&j<sy){const q=j*(sx+1)+i;ix.push(q,q+sx+1,q+1,q+1,q+sx+1,q+sx+2);}
      }
      const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(ps,3));g.setIndex(ix);g.computeVertexNormals();part(g,sail);
      line([-upper/2,y+sailH/2,z],[upper/2,y+sailH/2,z],.065);
    }
    line([0,1.6+h,z],[-W,1.6,-L*.48],.022);
    line([0,1.6+h,z],[W,1.6,L*.45],.022);
  }
  const flag=part(new THREE.PlaneGeometry(.95,.65),new THREE.MeshLambertMaterial({color:0x293a64,side:THREE.DoubleSide}),[.5,1.5+(masts[0]?.[1]||6),masts[0]?.[0]||0]);
  // All pieces are built at stable native scale; keep them separate from the
  // static scenery merger so harbor-water bobbing can animate the model.
  ship.scale.setScalar(scale);ship.userData.keep=true;
  return ship;
}

/* Moored hull and every attached mast/sail rock together; exported separately
 * so the same production motion can be verified in Node without a DOM/canvas. */
export function animateMooredShip(ship,t){
  const p=ship?.userData?.mooring;
  if(!p||!Number.isFinite(t))return false;
  ship.position.y=ship.userData.baseY+.105*Math.sin(t*.82+p.phase);
  ship.rotation.x=.013*Math.sin(t*.55+p.phase);
  ship.rotation.z=.025*Math.sin(t*.76+p.phase);
  ship.rotation.y=p.yaw+.012*Math.sin(t*.35+p.phase);
  return true;
}


/* The owner's individual 3D sailing-ship FBX (supplied as a ZIP) was converted
 * to a textured, self-contained glTF binary at the path below.
 *
 * Import ONE actual ship at the main harbor mooring, and retain the existing
 * procedural boat as both fallback and secondary docked vessel. The imported
 * model is checked for finite geometry and normalized to the current harbor
 * footprint so it won't block the road, break physics, or appear hundreds of
 * metres tall when an FBX exporter changes units.
 *
 * Separate source/model uploader is needed when the binary isn't yet present
 * on the deployed branch. Do not claim a GLB loaded unless success is true.
 */
export const TIDEWRACK_SHIP_GLB='proto3d/models-new/tidewrack_sailing_ship.glb.gz';
let approvedShipPromise=null;
function shipAsset(){
  // Harbor and open-ocean both reuse the user's approved textured GLB.
  // A compressed asset is deployed to keep APK size and cellular data low.
  if(!approvedShipPromise)approvedShipPromise=(async()=>{
    const response=await fetch(TIDEWRACK_SHIP_GLB+'?v=1.5.0');
    if(!response.ok)throw Error('Ship HTTP '+response.status);
    const bytes=await response.arrayBuffer(),head=new Uint8Array(bytes,0,Math.min(4,bytes.byteLength));
    let glb=bytes;
    if(head[0]===0x1f&&head[1]===0x8b){
      if(!('DecompressionStream'in window))throw Error('Gzip GLB unsupported by this browser');
      glb=await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
    }else if(!(head[0]===0x67&&head[1]===0x6c&&head[2]===0x54&&head[3]===0x46)){
      throw Error('Invalid original ship GLB header');
    }
    const {GLTFLoader}=await import('./vendor/jsm/loaders/GLTFLoader.js');
    return await new Promise((resolve,reject)=>new GLTFLoader().parse(glb,'',resolve,reject));
  })().catch(e=>{approvedShipPromise=null;throw e;});
  return approvedShipPromise;
}
export async function installImportedShip(ship,{large=true}={}){
  if(!ship||!ship.isGroup)return false;
  if(ship.userData.importedShip===true)return true;
  try{
    const gltf=await shipAsset();
    if(!gltf?.scene)throw new Error('No scene in sailing ship GLB');
    const model=gltf.scene.clone(true);
    model.updateMatrixWorld(true);
    const bounds=new THREE.Box3().setFromObject(model);
    const size=bounds.getSize(new THREE.Vector3()),center=bounds.getCenter(new THREE.Vector3());
    if (![size.x,size.y,size.z,center.x,center.y,center.z].every(Number.isFinite)
        ||size.y<0.001||size.x<0.001||size.z<0.001)throw new Error('Invalid ship geometry bounds');
    // Ship FBX exporter normalized everything to roughly one metre.
    // Existing harbor dimensions expect a 12 m tall galleon.
    const height=large?10.8:6.4,scale=height/size.y;
    model.scale.setScalar(scale);
    // Keep the imported mesh attached to the animated mooring group.
    model.position.set(-center.x*scale,-bounds.min.y*scale-.30,-center.z*scale);
    model.rotation.y=Math.PI*.5;
    model.traverse(o=>{if(o.isMesh){o.castShadow=false;o.receiveShadow=true;}});
    model.name='original-user-sailing-ship-3d';
    model.userData.keep=true;
    const fallbackChildren=ship.children.slice();
    ship.add(model);
    for(const part of fallbackChildren)part.visible=false;
    ship.userData.importedShip=true;
    ship.userData.importedShipModel=model;
    ship.userData.originalShipFallback=fallbackChildren;
    return true;
  }catch(e){
    // A missing or invalid shipped binary never blanks out Tidewrack Harbor.
    ship.userData.importedShip=false;
    ship.userData.importError=String(e?.message||e);
    console.warn('Tidewrack: original sailing ship GLB unavailable; using curved-hull fallback',e);
    return false;
  }
}
