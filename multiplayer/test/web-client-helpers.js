// Interpolate across the -π/π seam. Animation clips never override this
// world-facing heading, including when a remote player turns while idle.
export function remoteFacing(previousYaw,receivedYaw,deltaX,deltaZ,moving){
 const received=Number.isFinite(receivedYaw)?receivedYaw:previousYaw;
 const changed=Math.abs(Math.atan2(Math.sin(received-previousYaw),Math.cos(received-previousYaw)))>.025;
 return moving&&Math.hypot(deltaX,deltaZ)>.17&&!changed
   ?Math.atan2(deltaX,deltaZ):received;
}
export function nextRemoteYaw(current,target,dt){
 if(!Number.isFinite(target)||!Number.isFinite(current))return Number.isFinite(target)?target:0;
 const delta=Math.atan2(Math.sin(target-current),Math.cos(target-current));
 return current+delta*Math.min(1,Math.max(0,dt)*20);
}
