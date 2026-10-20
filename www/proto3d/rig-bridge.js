/**
 * Experimental Beth-to-Meshy humanoid rig bridge.
 *
 * Opt-in conversion only: NEVER replace an existing skinned/animated imported rig.
 * Adds intermediate joints to the original named-bone hierarchy, then binds
 * rigid (unskinned) imported surface meshes with approximate blended weights.
 * This is a first-pass fit requiring artist cleanup before release, not an
 * automatic proof that a character is production-rigged.
 */
export function splitHumanoidRig(THREE, root) {
  const splits = [
    ['spine', 'chest', 'upperSpine', 0.55],
    ['upperArm_L', 'foreArm_L', 'elbow_L', 0.83],
    ['upperArm_R', 'foreArm_R', 'elbow_R', 0.83],
    ['foreArm_L', 'hand_L', 'wrist_L', 0.82],
    ['foreArm_R', 'hand_R', 'wrist_R', 0.82],
    ['thigh_L', 'shin_L', 'knee_L', 0.88],
    ['thigh_R', 'shin_R', 'knee_R', 0.88],
    ['shin_L', 'foot_L', 'ankle_L', 0.85],
    ['shin_R', 'foot_R', 'ankle_R', 0.85]
  ];
  const output = [];
  for (const [pName, cName, extraName, frac] of splits) {
    const parent = root.getObjectByName(pName), child = root.getObjectByName(cName);
    if (!parent?.isBone || !child?.isBone || child.parent !== parent ||
        root.getObjectByName(extraName)) continue;
    const local = child.position.clone();
    const added = new THREE.Bone();
    added.name = extraName;
    added.position.copy(local).multiplyScalar(frac);
    parent.add(added);
    added.add(child);
    child.position.copy(local).multiplyScalar(1 - frac);
    output.push(extraName);
  }
  root.updateMatrixWorld(true);
  return output;
}

function distanceSquaredToSegment(p, a, b) {
  const dx=b.x-a.x, dy=b.y-a.y, dz=b.z-a.z;
  const len=dx*dx+dy*dy+dz*dz;
  const t=len>1e-9 ? Math.max(0,Math.min(1,
    ((p.x-a.x)*dx+(p.y-a.y)*dy+(p.z-a.z)*dz)/len)) : 0;
  const x=p.x-a.x-t*dx, y=p.y-a.y-t*dy, z=p.z-a.z-t*dz;
  return x*x+y*y+z*z;
}

export function bridgeUnskinnedHumanoid(THREE, donor, imported, options = {}) {
  const out = {ok:false, reason:'', scene:null, animations:null, helpers:[],
    convertedMeshes:0, vertices:0};
  if (!donor?.root?.isObject3D || !imported?.isObject3D ||
      typeof donor.clips !== 'function') {
    out.reason = 'Donor must supply a Beth-style rig root and clips';
    return out;
  }
  const targetMeshes = [];
  imported.traverse(obj => {
    if (obj.isMesh && !obj.userData?.isGhost) targetMeshes.push(obj);
  });
  if (!targetMeshes.length) { out.reason='No imported surface meshes'; return out; }
  if (targetMeshes.some(m=>m.isSkinnedMesh)) {
    out.reason='Imported model is already skinned: preserve and retarget its existing rig instead';
    return out;
  }
  if (targetMeshes.some(m=>m.isInstancedMesh || m.geometry?.morphAttributes?.position?.length)) {
    out.reason='Instanced or morph-target meshes require a separate conversion';
    return out;
  }
  const count = targetMeshes.reduce((sum,m)=>sum+(m.geometry?.attributes?.position?.count||0),0);
  if (!count || count > (options.maxVertices || 220000)) {
    out.reason='Vertex count outside prototype range';
    return out;
  }
  // Audit first: these source bones are essential for bipedal weighting.
  for (const name of ['hips','spine','chest','head','upperArm_L','upperArm_R',
    'foreArm_L','foreArm_R','thigh_L','thigh_R','shin_L','shin_R','foot_L','foot_R']) {
    if (!donor.root.getObjectByName(name)?.isBone) {
      out.reason='Missing donor joint: '+name; return out;
    }
  }

  const donorRoot = donor.root;
  out.helpers = splitHumanoidRig(THREE, donorRoot);
  donorRoot.updateMatrixWorld(true);
  const bones = [];
  donorRoot.traverse(o=>{if(o.isBone) bones.push(o);});
  if (bones.length > 100) {out.reason='Too many donor bones';return out;}

  const positions = bones.map(b=>b.getWorldPosition(new THREE.Vector3()));
  const index = new Map(bones.map((b,i)=>[b,i]));
  const segments = [];
  for (let i=0;i<bones.length;i++) {
    const parent = bones[i].parent;
    if (!parent?.isBone || !index.has(parent)) continue;
    if (positions[i].distanceToSquared(positions[index.get(parent)]) < 1e-9) continue;
    segments.push({i, a:positions[index.get(parent)], b:positions[i]});
  }
  if (segments.length < 8) {out.reason='Donor has insufficient limb segments';return out;}
  imported.updateMatrixWorld(true);
  const bounds = new THREE.Box3().setFromObject(imported);
  const size = bounds.getSize(new THREE.Vector3());
  if (!size.y || !Number.isFinite(size.y)) {out.reason='Invalid Meshy bounds';return out;}
  const headY = donorRoot.getObjectByName('head').getWorldPosition(new THREE.Vector3()).y;
  const footY = Math.min(...['foot_L','foot_R'].map(n=>donorRoot.getObjectByName(n).getWorldPosition(new THREE.Vector3()).y));
  const height = Math.max(0.1,headY - footY + 0.17);
  const scale = height / size.y;
  if (!Number.isFinite(scale) || scale < 0.001 || scale > 100) {
    out.reason='Unsupported model units';return out;
  }
  // Work on detached clones; the Meshy model and original Beth mesh stay intact.
  const prepared = targetMeshes.map(orig=>{
    const geometry=orig.geometry.clone();
    geometry.applyMatrix4(orig.matrixWorld);
    geometry.scale(scale,scale,scale);
    geometry.translate(-(bounds.min.x+bounds.max.x)*0.5*scale,
      -bounds.min.y*scale, -(bounds.min.z+bounds.max.z)*0.5*scale);
    return {original:orig, geometry};
  });
  const skinData=[];
  const point = new THREE.Vector3();
  for (const {geometry} of prepared) {
    const pos=geometry.attributes.position, weights=new Float32Array(pos.count*4),
      ids=new Uint16Array(pos.count*4);
    for(let v=0;v<pos.count;v++){
      point.fromBufferAttribute(pos,v);
      const near=segments.map(seg=>({
        bone:seg.i,
        dist:distanceSquaredToSegment(point,seg.a,seg.b)
      })).sort((a,b)=>a.dist-b.dist).slice(0,4);
      let sum=0;
      for(let j=0;j<near.length;j++){
        const influence=1/Math.pow(near[j].dist+0.009,1.4);
        weights[v*4+j]=influence; ids[v*4+j]=near[j].bone;sum+=influence;
      }
      for(let j=0;j<near.length;j++) weights[v*4+j]/=sum;
    }
    geometry.setAttribute('skinIndex',new THREE.Uint16BufferAttribute(ids,4));
    geometry.setAttribute('skinWeight',new THREE.Float32BufferAttribute(weights,4));
    skinData.push(weights);
  }
  // Source geometry is retained but made invisible, so clips continue to
  // animate donor joints while only the imported detailed skin is rendered.
  donorRoot.traverse(obj=>{if(obj.isMesh) obj.visible=false;});
  const skeleton=new THREE.Skeleton(bones);
  skeleton.calculateInverses();
  for (const {original,geometry} of prepared) {
    const skin=new THREE.SkinnedMesh(geometry,original.material);
    skin.name='MeshyRigBridge_'+(original.name||'surface');
    skin.frustumCulled=false;
    skin.castShadow=true;
    skin.receiveShadow=true;
    donorRoot.add(skin);
    skin.updateMatrixWorld(true);
    skin.bind(skeleton,new THREE.Matrix4());
  }
  // Existing clips use the original joint names, which were NOT renamed.
  out.ok=true; out.reason='Experimental automatic weights; manual inspection required';
  out.scene=donorRoot;
  out.animations=donor.clips();
  out.convertedMeshes=prepared.length;
  out.vertices=count;
  return out;
}
