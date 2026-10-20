/* One shared ground-plan for Varnethryl. Game extent remains +/-560 m.
   City fortifications protect the inner district; the mountain wilderness stays playable.
   Harbor is a compact SW-corner settlement with sea-facing quays and a landward gate. */
export const CITY_WALL_HALF = 246;
export const HARBOR = Object.freeze({
  x: -430, z: 422,
  lightX: -480, lightZ: 412,
  bayX: -430, bayZ: 463, bayHalfX: 43, bayHalfZ: 47,
  waterY: 0.09, depth: -3.2,
  fortHalfX: 55, fortHalfZ: 67
});
export const HARBOR_ROAD = Object.freeze([
  [0, CITY_WALL_HALF+3], [-26,268], [-73,289], [-123,305],
  [-173,310], [-221,322], [-276,338], [-328,365], [-378,391], [HARBOR.x, HARBOR.z-20]
]);
export const distToSegment=(x,z,ax,az,bx,bz)=>{
  const dx=bx-ax,dz=bz-az,len=dx*dx+dz*dz;
  const t=len?Math.max(0,Math.min(1,((x-ax)*dx+(z-az)*dz)/len)):0;
  return Math.hypot(x-(ax+dx*t),z-(az+dz*t));
};
export function distToHarborRoad(x,z) {
  let d=Infinity;
  for(let i=1;i<HARBOR_ROAD.length;i++){
    const a=HARBOR_ROAD[i-1],b=HARBOR_ROAD[i];
    d=Math.min(d,distToSegment(x,z,a[0],a[1],b[0],b[1]));
  }
  return d;
}
export function harborWater(x,z){
  return Math.abs(x-HARBOR.bayX)<HARBOR.bayHalfX &&
    Math.abs(z-HARBOR.bayZ)<HARBOR.bayHalfZ;
}
export function harborShoreDistance(x,z){
  const dx=Math.max(0,Math.abs(x-HARBOR.bayX)-HARBOR.bayHalfX);
  const dz=Math.max(0,Math.abs(z-HARBOR.bayZ)-HARBOR.bayHalfZ);
  return Math.hypot(dx,dz);
}
export function harborSafe(x,z){
  // Both the inner town and the independently fortified harbor are free of random hostile spawns.
  return Math.abs(x-HARBOR.x)<HARBOR.fortHalfX+8 &&
    Math.abs(z-HARBOR.z)<HARBOR.fortHalfZ+8;
}
export function outsideTownWalls(x,z){
  return Math.abs(x)>CITY_WALL_HALF+15 || Math.abs(z)>CITY_WALL_HALF+15;
}
export function inTownWilderness(x,z,half=560){
  return Math.max(Math.abs(x),Math.abs(z))<half-10 &&
    outsideTownWalls(x,z) && !harborSafe(x,z) && !harborWater(x,z) &&
    distToHarborRoad(x,z)>12;
}
export function townBuildingSpot(def,spacing){
  if(def.id==='port')return {x:HARBOR.x,z:HARBOR.z};
  if(def.id==='lighthouse')return {x:HARBOR.lightX,z:HARBOR.lightZ};
  if(def.id==='gatehouse')return {x:0,z:CITY_WALL_HALF-1.2};
  return {x:def.cx*spacing,z:def.cz*spacing};
}
