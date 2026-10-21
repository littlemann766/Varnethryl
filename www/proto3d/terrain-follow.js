/* Ground-aligned creature pose. Samples the actual shared terrain height,
 * not independent artificial body elevation; limits pitch on sharp ridges.
 * Authored skeletal slither remains responsible for torso/tail waves. */
export function terrainBodyPitch(backY,frontY,distance,maxPitch=.2){
 if(!Number.isFinite(backY)||!Number.isFinite(frontY)||!Number.isFinite(distance)||distance<=0)return 0;
 const angle=-Math.atan2(frontY-backY,distance);
 const limit=Math.max(0,Math.min(.5,Number.isFinite(maxPitch)?maxPitch:.2));
 return Math.max(-limit,Math.min(limit,angle));
}
