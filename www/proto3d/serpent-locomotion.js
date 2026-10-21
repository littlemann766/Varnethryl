/* Varnethryl serpent locomotion — selected authored clips plus a subtle
 * additive traveling wave through the whole skeletal body. The animated rig
 * is never rewritten, and hero/boss attack animations retain their timing.
 *
 * Imported Balthrix has 29 animated spine/tail joints, so the old *fallback
 * only* wave never ran. Applying this overlay after mixer.update gives the
 * entire creature an actual head-to-tail S-shaped slither while advancing. */
export function preferSerpentClips(id, act) {
  if (!/vaelthryx/i.test(String(id)) || !act) return act;
  const slither = act.slither || act.Slither || act.body_wave || act.BodyWave;
  const fast = act.slither_fast || act.slitherFast || act.Slither_fast || act.SlitherFast;
  if (slither) act.walk = slither;
  if (fast) act.run = fast;
  else if (slither) act.run = slither;
  return act;
}

const clamp = (v,lo,hi) => Math.max(lo,Math.min(hi,v));
const isBody = name => /spine|tail|body|neck|head/i.test(name || '');
/* Prefer the longest *connected* body-bone lineage, not all matching
   bones in traversal order (that would mix left/right ribs or horns). */
export function serpentBodyChain(root) {
  if (!root || typeof root.traverse !== 'function') return [];
  const found=[];
  root.traverse(node=>{if(node.isBone&&isBody(node.name))found.push(node);});
  if (!found.length) return [];
  const set=new Set(found),paths=new Map();
  function path(node) {
    if(paths.has(node))return paths.get(node);
    const p=node.parent && set.has(node.parent) ? path(node.parent) : [];
    const result=[...p,node];paths.set(node,result);return result;
  }
  let best=[];
  for(const bone of found){
    const p=path(bone);
    if(p.length>best.length)best=p;
  }
  return best;
}

/* Called AFTER AnimationMixer.update(), so rotations are ADDITIVE and never
   accumulate: the mixer restores each animated pose on every frame. A live
   chase and the roaming patrol receive the same smooth wave.
   Steering is delayed down the spine, producing a trailing tail on corners.
   Attack / stagger suppresses the wave without changing combat hit timing. */
export function createSerpentWave(root,{ maxAngle=.125 }={}) {
  const bones=serpentBodyChain(root);
  if(bones.length<4)return null;
  let phase=0,strength=0,steering=0;
  const lastTime={value:0};
  // Reuse one mathematical delta per joint; no new Three.js allocations.
  return function serpentWave(dt,speed,turnRate=0,attacking=false) {
    dt=clamp(Number.isFinite(dt)?dt:0,0,.06);
    speed=Math.max(0,Number.isFinite(speed)?speed:0);
    turnRate=clamp(Number.isFinite(turnRate)?turnRate:0,-2,2);
    const activity=clamp((speed-.12)/6.5,0,1);
    const target=attacking?0:activity;
    strength+=(target-strength)*(1-Math.exp(-dt*(attacking?13:6)));
    steering+=(turnRate-steering)*(1-Math.exp(-dt*4));
    // Advancing a world unit moves the wave through one length of the snake.
    if(speed>.12)phase+=dt*(1.55+Math.min(7,speed*.42));
    else phase+=dt*.17;
    if(phase>Math.PI*200)phase%=Math.PI*2;
    lastTime.value=phase;
    const count=bones.length;
    for(let i=0;i<count;i++){
      const t=i/(count-1); // neck first, tail last
      const lateral=Math.sin(phase-t*8.4); // moving S-bend
      const trailing=Math.sin(phase*.6-t*4.8-.55);
      const taper=.32+.68*t;
      const angle=clamp((lateral*.78+trailing*.22)*maxAngle*taper*strength-steering*t*.09*strength,-.21,.21);
      // Rotate around the serpent's local up axis. This bends spine + tail
      // left/right, rather than shifting only the texture/sides of its mesh.
      bones[i].quaternion.multiplyQuaternions(bones[i].quaternion,
        // Local vertical quaternion without depending on a Three.js import.
        {x:0,y:Math.sin(angle*.5),z:0,w:Math.cos(angle*.5)});
    }
  };
}
