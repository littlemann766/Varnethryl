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
// Balthrix uses the OUTER wilderness, skirting hills and the volcano's rim.
// This closed loop also stays clear of the walled port's northern and western
// ramparts. Its exact spline is shared by roaming AI and the visible trail.
export const BALTHRIX_ROUTE = Object.freeze([
  [-486,-96],[-486,-266],[-455,-421],[-323,-476],[-142,-489],
  [75,-494],[260,-487],[441,-455],[497,-286],[506,-92],
  [505,115],[493,288],[447,467],[276,493],[85,503],
  [-116,503],[-289,497],[-454,515],[-532,506],[-535,391],[-531,234],[-516,145]
]);
export const BALTHRIX_TRAIL_HALF_WIDTH = 18; // 36-unit broad trampled route

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
/* The roamer follows one continuous route, including the volcano, and stays outside city walls. */
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
// World-space points have exact agreement with Balthrix's constant-speed
// spline; they are used for terrain dressing and exclusion of trees/rocks.
export const BALTHRIX_TRAIL = Object.freeze(BALTHRIX_ARC.samples
  .slice(0,-1).map(s=>Object.freeze(balthrixPoint(s.seg,s.u))));
const TRAIL_CELL=48, TRAIL_MARGIN=BALTHRIX_TRAIL_HALF_WIDTH+17;
const trailCells=new Map();
for(let i=0;i<BALTHRIX_TRAIL.length;i++){
  const a=BALTHRIX_TRAIL[i],b=BALTHRIX_TRAIL[(i+1)%BALTHRIX_TRAIL.length];
  const minX=Math.floor((Math.min(a.x,b.x)-TRAIL_MARGIN)/TRAIL_CELL),
    maxX=Math.floor((Math.max(a.x,b.x)+TRAIL_MARGIN)/TRAIL_CELL),
    minZ=Math.floor((Math.min(a.z,b.z)-TRAIL_MARGIN)/TRAIL_CELL),
    maxZ=Math.floor((Math.max(a.z,b.z)+TRAIL_MARGIN)/TRAIL_CELL);
  for(let x=minX;x<=maxX;x++)for(let z=minZ;z<=maxZ;z++){
    const key=x+':'+z;
    if(!trailCells.has(key))trailCells.set(key,[]);
    trailCells.get(key).push([a,b]);
  }
}
export function balthrixTrailDistance(x,z){
  const segs=trailCells.get(Math.floor(x/TRAIL_CELL)+':'+Math.floor(z/TRAIL_CELL));
  if(!segs)return Infinity;
  let best=Infinity;
  for(const [a,b] of segs){
    const dx=b.x-a.x,dz=b.z-a.z,l2=dx*dx+dz*dz||1;
    const t=Math.max(0,Math.min(1,((x-a.x)*dx+(z-a.z)*dz)/l2));
    best=Math.min(best,Math.hypot(x-a.x-t*dx,z-a.z-t*dz));
  }
  return best;
}
export function nearestBalthrixRoamTime(x,z,speed=14){
  let best=Infinity,time=0;
  const S=BALTHRIX_ARC.samples;
  for(let i=0;i<S.length-1;i++){
    const p=balthrixPoint(S[i].seg,S[i].u),q=balthrixPoint(S[i+1].seg,S[i+1].u);
    const dx=q.x-p.x,dz=q.z-p.z,l2=dx*dx+dz*dz||1;
    const f=Math.max(0,Math.min(1,((x-p.x)*dx+(z-p.z)*dz)/l2));
    const d=Math.hypot(x-p.x-f*dx,z-p.z-f*dz);
    if(d<best){best=d;time=(S[i].dist+(S[i+1].dist-S[i].dist)*f)/speed;}
  }
  return {distance:best,time};
}

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
