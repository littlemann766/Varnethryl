/* Optional third-person boss camera assist.
 * Activates ONLY while the player has actively locked a live boss target.
 * Returns a small eye-line offset so giant models can fit in portrait view,
 * never changes the user's yaw, orbit pitch, zoom, controls, or save data.
 */
export function bossCameraFocus(heroX,heroZ,target,locked,portrait=false){
 if(!locked||!target?.def?.boss||target.state==='defeated')return null;
 const dx=target.x-heroX,dz=target.z-heroZ;
 if(!Number.isFinite(dx)||!Number.isFinite(dz))return null;
 const distance=Math.hypot(dx,dz);
 if(distance<1||distance>90)return null;
 const strength=Math.max(0,Math.min(1,(90-distance)/55));
 const offset=Math.min(portrait?14:11,distance*(portrait?.28:.23))*strength;
 const height=Math.max(0,Math.min(65,Number(target.heightAbove)||12));
 const rise=Math.min(portrait?7.5:6,height*(portrait?.37:.32))*strength;
 return {x:dx/distance*offset,z:dz/distance*offset,rise};
}
