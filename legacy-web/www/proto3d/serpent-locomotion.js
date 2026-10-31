/* Varnethryl serpent locomotion.
 * Balthrix's approved skeleton already contains authored 'slither' and
 * 'slither_fast' animation clips that move its entire 29-joint body.
 * Do NOT add per-joint runtime Y rotations after those clips. The old overlay
 * accumulated off-axis deformation along the spine, visibly twisting the
 * model instead of propelling a snake naturally. Let the rigged clips play. */
/* Keep a giant serpent's body turning no faster than its long spine can bend.
 * The signed shortest-angle delta also avoids an abrupt full revolution when
 * the patrol spline crosses the -pi / +pi compass boundary. This changes only
 * the creature ROOT; never manipulate the model's skinned joints after its
 * authored slither animation has played.
 */
export function serpentHeading(current,target,dt,maxRadiansPerSecond=1.15){
  if(!Number.isFinite(target))return Number.isFinite(current)?current:0;
  if(!Number.isFinite(current))return target;
  const elapsed=Number.isFinite(dt)?Math.max(0,Math.min(.1,dt)):0;
  const rate=Number.isFinite(maxRadiansPerSecond)?Math.max(0,maxRadiansPerSecond):0;
  const delta=Math.atan2(Math.sin(target-current),Math.cos(target-current));
  const step=Math.sign(delta)*Math.min(Math.abs(delta),rate*elapsed);
  const angle=current+step;
  return Math.atan2(Math.sin(angle),Math.cos(angle));
}
export function preferSerpentClips(id, act) {
  if (!/vaelthryx/i.test(String(id)) || !act) return act;
  const slither = act.slither || act.Slither || act.body_wave || act.BodyWave;
  const fast = act.slither_fast || act.slitherFast || act.Slither_fast || act.SlitherFast;
  if (slither) act.walk = slither;
  if (fast) act.run = fast;
  else if (slither) act.run = slither;
  return act;
}

export function serpentBodyChain(root) {
  if (!root || typeof root.traverse !== 'function') return [];
  const found=[];
  root.traverse(node=>{if(node.isBone && /spine|tail|body|neck|head/i.test(node.name||''))found.push(node);});
  const set=new Set(found), memo=new Map();
  function path(node) {
    if(memo.has(node))return memo.get(node);
    const p=node.parent && set.has(node.parent) ? path(node.parent) : [];
    const result=[...p,node];memo.set(node,result);return result;
  }
  let best=[];
  for (const bone of found){const p=path(bone);if(p.length>best.length)best=p;}
  return best;
}

/* Sanity-check all body joints that receive rotation/translation tracks.
 * No pose mutations. Report evidence that the selected authored clips bend
 * a multi-joint serpent, rather than an idle clip with a misleading name. */
export function serpentAnimatedBody(animations=[]) {
  const results=[];
  for(const clip of animations) {
    const bones=new Set();
    for(const track of clip.tracks||[]){
      const name=track.name||'';
      if (/spine|tail|body|neck|head/i.test(name) && /\.(quaternion|position|rotation)$/.test(name))
        bones.add(name.replace(/\.(quaternion|position|rotation)$/,''));
    }
    results.push({clip:clip.name,bones:bones.size});
  }
  return results;
}
