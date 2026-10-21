/* Owner's weapon - mount to the REAL animated right-hand joint.
 * A layered, luminous violet blade and physical hilt, never a generic stick.
 * The source GLB and its skeleton/animation data are not modified.
 */
const nrm = s => (s||'').toLowerCase().replace(/[^a-z0-9]/g,'');
const rightHandNames = new Set(['righthand','handr','rhand','righthandbone','handright','righthandjoint']);
const rightWristNames = new Set(['rightwrist','wristr','rwrist','rightforearm','lowerarmr','forearmr']);

export function findOwnerGripBone(model) {
  const hands=[], wrists=[];
  model.traverse(node => {
    if (!node.isBone) return;
    const n=nrm(node.name);
    if (rightHandNames.has(n) || /(?:righthand|handright)$/.test(n)) hands.push(node);
    else if(rightWristNames.has(n) || /(?:rightwrist|rightforearm)$/.test(n)) wrists.push(node);
  });
  // Prefer a hand attached to the skinned skeleton, not named decorative meshes.
  return {bone:hands[0]||wrists[0]||null, fallback:!hands.length};
}

export function attachOwnerSaber(THREE, gltfScene) {
  if (!gltfScene?.traverse) return {attached:false,reason:'No scene'};
  const {bone:hand,fallback}=findOwnerGripBone(gltfScene);
  if (!hand) return {attached:false,reason:'No right-hand or wrist bone on this GLB'};
  if (hand.getObjectByName('OwnerPurpleSaber'))
    return {attached:true,reason:'Already mounted',hand:hand.name};

  // Put the grip INSIDE the fist. Use the direction toward the index
  // finger when the rig provides finger joints; otherwise carry it along
  // the hand's local -Z axis, not straight out of its wrist (+Y).
  const finger=[];
  hand.traverse(node => {
    if (node!==hand && node.isBone && /(?:index|middle|finger|thumb)/.test(nrm(node.name)))
      finger.push(node);
  });
  const direction=new THREE.Vector3(0,0,-1);
  if(finger.length){
    hand.updateWorldMatrix(true,true);
    const pt=new THREE.Vector3(),origin=new THREE.Vector3();
    hand.getWorldPosition(origin);finger[0].getWorldPosition(pt);
    pt.sub(origin).transformDirection(hand.matrixWorld.clone().invert());
    if(pt.lengthSq()>.00001)direction.copy(pt.normalize());
  }
  const saber=new THREE.Group();saber.name='OwnerPurpleSaber';
  hand.add(saber);
  // A wrist-only fallback needs a short offset toward the palm.
  saber.position.set(0,fallback?-.07:0,-.025);
  saber.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),direction);

  const metal=new THREE.MeshStandardMaterial({color:0x3d344d,metalness:.82,roughness:.26});
  const trim=new THREE.MeshStandardMaterial({color:0xb3a5c8,metalness:.88,roughness:.22});
  const core=new THREE.MeshBasicMaterial({color:0xffeeff,toneMapped:false});
  const purple=new THREE.MeshBasicMaterial({color:0xa642ff,toneMapped:false});
  const aura=new THREE.MeshBasicMaterial({color:0x9a36ff,transparent:true,opacity:.22,blending:THREE.AdditiveBlending,depthWrite:false,side:THREE.DoubleSide,toneMapped:false});
  const tiny=(geo,mat,name,x,y,z)=>{
    const part=new THREE.Mesh(geo,mat);part.name=name;part.position.set(x,y,z);saber.add(part);return part;
  };
  tiny(new THREE.CylinderGeometry(.031,.034,.22,12),metal,'saber-hilt',0,.10,0);
  for(const y of [.025,.17,.215]){
    tiny(new THREE.CylinderGeometry(.039,.039,.025,12),trim,'saber-metal-ring',0,y,0);
  }
  for(const y of [.045,.085,.125]){
    tiny(new THREE.CylinderGeometry(.0345,.0345,.013,12),metal,'saber-grip',0,y,0);
  }
  tiny(new THREE.CylinderGeometry(.028,.04,.06,12),trim,'saber-emitter',0,.245,0);
  const bladeLen=.98;
  tiny(new THREE.CylinderGeometry(.023,.025,bladeLen,12),purple,'violet-blade',0,.28+bladeLen/2,0);
  tiny(new THREE.CylinderGeometry(.011,.013,bladeLen*.99,12),core,'luminous-white-core',0,.28+bladeLen/2,0);
  const shell=tiny(new THREE.CylinderGeometry(.064,.069,bladeLen+0.015,12),aura,'violet-blade-glow',0,.28+bladeLen/2,0);
  shell.renderOrder=5;
  const tip=tiny(new THREE.SphereGeometry(.023,10,8),core,'bright-blade-tip',0,.28+bladeLen,0);
  tip.renderOrder=6;
  saber.userData.isOwnerSaber=true;
  saber.userData.gripBone=hand.name;
  saber.userData.fingerAligned=!!finger.length;
  return {attached:true,hand:hand.name,fingerAligned:!!finger.length,fallback};
}
