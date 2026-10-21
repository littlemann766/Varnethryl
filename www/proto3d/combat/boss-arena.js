/* Varnethryl boss arena boundaries.
 * A frost brother cannot follow the player out of the ice-cave encounter,
 * and the Titan cannot cross the distant volcanic arena into the village.
 * Balthrix stays exempt: its lore requires roaming the entire overworld.
 * Pure, deterministic math, independently testable without WebGL. */
export const BOSS_LEASH_RADII=Object.freeze({
 frosttroll_a:112,
 frosttroll_b:112,
 titan40:132,
 titan:132,
});
export function bossHome(key,x,z){
 const r=BOSS_LEASH_RADII[key];
 if(!r||!Number.isFinite(x)||!Number.isFinite(z))return null;
 return {homeX:x,homeZ:z,homeRadius:r};
}
export function outsideBossArena(e,x,z){
 return !!(e&&Number.isFinite(e.homeRadius)&&e.homeRadius>0&&
   Math.hypot(x-e.homeX,z-e.homeZ)>e.homeRadius);
}
export function homeDistance(e){
 return Math.hypot(e.x-e.homeX,e.z-e.homeZ);
}
export function telegraphKey(shape,pattern){
 if(shape==='cone')return 'cone:'+Number(pattern?.cos??0).toFixed(4);
 return shape;
}
