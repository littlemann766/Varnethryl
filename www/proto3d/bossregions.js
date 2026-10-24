/* Varnethryl encounter geography. Shared by terrain, gateways, combat and tests.
 * Coordinates are world units on the 1120-wide original town/outskirts map.
 * The castle village remains the peaceful middle; bosses live beyond its walls.
 */
export const CITY_HALF = 185;
export const TITAN_CENTER = Object.freeze({x: 405, z: -402, radius: 122});
export const FROST_SUMMIT = Object.freeze({x: 0, z: -345, radius: 137, height: 60});
export const FROST_PORTAL = Object.freeze({x: 0, z: -345});
export const PORT_CENTER = Object.freeze({x: -425.6, z: 392});
export const FROST_REALM = Object.freeze({cx: 2250, cz: 0, half: 235});
// Hand-drawn blue patrol approved on 21349.png, 24 Oct 2026.
// World x grows to the east and z to the south; one closed Catmull-Rom loop.
// Intentionally skirt the WEST of the volcano and bend inside the southwest
// outskirts rather than running through Tidewrack's port or the village.
export const BALTHRIX_ROUTE = Object.freeze([
  [-525,-405],[-502,-469],[-448,-505],[-370,-492],[-288,-502],
  [-178,-510],[-73,-525],[29,-534],[115,-514],[153,-482],
  [190,-425],[243,-361],[297,-304],[343,-261],[401,-230],
  [485,-203],[497,-103],[499,16],[509,142],[519,270],
  [520,368],[498,450],[459,499],[371,515],[261,514],
  [150,510],[40,506],[-61,514],[-111,513],[-153,482],
  [-189,435],[-220,368],[-245,308],[-283,259],[-332,214],
  [-390,182],[-468,141],[-518,77],[-521,-30],[-522,-155],[-522,-276]
]);
export const LAVA_POOLS = Object.freeze([
  {x: 402, z: -419, r: 25}, {x: 449, z: -371, r: 16},
  {x: 351, z: -438, r: 14}, {x: 376, z: -358, r: 10},
  {x: 446, z: -439, r: 9}
]);
export const clamp01 = v => Math.max(0, Math.min(1,v));
export const smooth01 = t => {const s=clamp01(t);return s*s*(3-2*s);};
export const dist2 = (x,z,p) => Math.hypot(x-p.x,z-p.z);
export const isCitySafe = (x,z,pad=8) => Math.abs(x)<CITY_HALF+pad && Math.abs(z)<CITY_HALF+pad;
export function lavaAmount(x,z) {return 1-smooth01((dist2(x,z,TITAN_CENTER)-TITAN_CENTER.radius*.55)/(TITAN_CENTER.radius*.5));}
export function onLava(x,z){return LAVA_POOLS.some(p=>dist2(x,z,p)<p.r);}
/* Broad, walkable ice hill: central summit 60 world units high, gradual ascent from the north.
 * The portal is on the broad level cap; players and companions share this same surface.
 */
export function frostHill(x,z){
 const d=dist2(x,z,FROST_SUMMIT);
 return FROST_SUMMIT.height*(1-smooth01((d-13)/(FROST_SUMMIT.radius-13)));
}
export function terrainBiome(x,z){
 if(lavaAmount(x,z)>0.18)return 'rock';
 if(Math.hypot(x-FROST_SUMMIT.x,z-FROST_SUMMIT.z)<170)return 'snow';
 return x<-140&&z<0?'forest':'meadow';
}
/* The roamer follows the user-marked outer perimeter, bypassing the port, volcano crater and city walls. */
// Continuous position and tangent through route corners, preventing abrupt head snapping.
// Catmull-Rom uses the same patrol waypoints; no changes to saved encounter locations.
// Cache spline samples once. Chord-length timing made Balthrix accelerate at
// corners and slow down on curved stretches even when speed was constant.
const BALTHRIX_STEPS = 32;
function balthrixPoint(i,u) {
 const P=BALTHRIX_ROUTE,n=P.length;
 const p0=P[(i+n-1)%n],p1=P[i],p2=P[(i+1)%n],p3=P[(i+2)%n];
 const axis=a=>.5*(2*p1[a]+(-p0[a]+p2[a])*u+
  (2*p0[a]-5*p1[a]+4*p2[a]-p3[a])*u*u+
  (-p0[a]+3*p1[a]-3*p2[a]+p3[a])*u*u*u);
 return {x:axis(0),z:axis(1)};
}
const BALTHRIX_ARC = (() => {
 const samples=[{dist:0,seg:0,u:0}];
 let dist=0,prev=balthrixPoint(0,0);
 for(let i=0;i<BALTHRIX_ROUTE.length;i++)for(let j=1;j<=BALTHRIX_STEPS;j++){
  const u=j/BALTHRIX_STEPS,p=balthrixPoint(i,u);
  dist+=Math.hypot(p.x-prev.x,p.z-prev.z);
  samples.push({dist,seg:i,u});prev=p;
 }
 return {samples,total:dist};
})();
export function balthrixPosition(t,speed=14){
 const {samples,total}=BALTHRIX_ARC;
 if(!Number.isFinite(t)||!Number.isFinite(speed)||total<=0)
  return {x:BALTHRIX_ROUTE[0][0],z:BALTHRIX_ROUTE[0][1],yaw:0};
 const distance=((t*speed)%total+total)%total;
 let lo=0,hi=samples.length-1;
 while(lo+1<hi){const mid=(lo+hi)>>1;if(samples[mid].dist<distance)lo=mid;else hi=mid;}
 const a=samples[lo],b=samples[hi];
 const blend=(distance-a.dist)/Math.max(1e-9,b.dist-a.dist);
 const param=(a.seg+a.u)+(b.seg+b.u-(a.seg+a.u))*blend;
 const seg=Math.floor(param)%BALTHRIX_ROUTE.length,u=param-Math.floor(param);
 const p=balthrixPoint(seg,u);
 // Sample the spline at a fixed physical distance ahead/behind, rather than
 // fixed spline parameters. This stabilizes heading through sharp curves.
 const atDistance=d=>{
  const target=((d%total)+total)%total;
  let low=0,high=samples.length-1;
  while(low+1<high){const mid=(low+high)>>1;if(samples[mid].dist<target)low=mid;else high=mid;}
  const left=samples[low],right=samples[high];
  const mix=(target-left.dist)/Math.max(1e-9,right.dist-left.dist);
  const position=left.seg+left.u+(right.seg+right.u-left.seg-left.u)*mix;
  return balthrixPoint(Math.floor(position)%BALTHRIX_ROUTE.length,position%1);
 };
 const ahead=atDistance(distance+1.5),behind=atDistance(distance-1.5);
 return {x:p.x,z:p.z,yaw:Math.atan2(ahead.x-behind.x,ahead.z-behind.z)};
}

/* Locate a nearby encounter on the SAME curved spline the serpent patrols.
 * Earlier discovery projected onto straight waypoint chords, then placed the
 * real model on a different Catmull-Rom curve. That forced immediate sideward
 * corrections that looked like player-style sliding rather than slithering.
 * Reuse the existing arc-length sample table to keep the world layout intact.
 */
export function nearestBalthrixPath(x,z,speed=14){
 if(!Number.isFinite(x)||!Number.isFinite(z)||!Number.isFinite(speed)||speed<=0)
   return {distance:Infinity,time:0};
 const {samples}=BALTHRIX_ARC;
 let best=Infinity,at=0,previous=balthrixPoint(0,0);
 for(let i=1;i<samples.length;i++){
   const a=samples[i-1],b=samples[i],point=balthrixPoint(b.seg,b.u);
   const dx=point.x-previous.x,dz=point.z-previous.z;
   const u=Math.max(0,Math.min(1,((x-previous.x)*dx+(z-previous.z)*dz)/(dx*dx+dz*dz||1)));
   const px=previous.x+u*dx,pz=previous.z+u*dz,dist=Math.hypot(x-px,z-pz);
   if(dist<best){best=dist;at=a.dist+u*(b.dist-a.dist);}
   previous=point;
 }
 const time=at/speed;
 return {distance:best,time};
}
/* Procedural, deterministic aftermath along Balthrix's existing curved patrol.
 * Positions are kept at least a giant body-width away from the route, so the
 * player can explore the wreckage without trapping the roaming serpent.
 * This is pure geometry data: it can be validated without WebGL or a phone. */
export function fallenTreeSites() {
 const sites=[];
 for(let i=0,t=8;t<250;t+=12.5,i++){
  const p=balthrixPosition(t),side=i%2===0?1:-1,offset=21+(i%4)*2.3;
  const x=p.x+side*Math.cos(p.yaw)*offset;
  const z=p.z-side*Math.sin(p.yaw)*offset;
  const len=10+(i%4)*2.3;
  const angle=p.yaw+side*.73+((i%3)-1)*.18;
  const ux=Math.sin(angle),uz=Math.cos(angle);
  const ends=[[x-ux*len*.53,z-uz*len*.53],[x+ux*len*.53,z+uz*len*.53]];
  if(Math.max(Math.abs(x),Math.abs(z))>535||
   Math.hypot(x-FROST_SUMMIT.x,z-FROST_SUMMIT.z)<165||
   Math.hypot(x-PORT_CENTER.x,z-PORT_CENTER.z)<107||
   Math.hypot(x-TITAN_CENTER.x,z-TITAN_CENTER.z)<100||
   ends.some(([ex,ez])=>isCitySafe(ex,ez,20)||onLava(ex,ez)))continue;
  sites.push(Object.freeze({x,z,length:len,angle,burnt:Math.hypot(x-TITAN_CENTER.x,z-TITAN_CENTER.z)<205}));
 }
 return Object.freeze(sites);
}
