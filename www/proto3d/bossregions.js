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
export const BALTHRIX_ROUTE = Object.freeze([
  [-435, -205],[-320,-360],[-55,-445],[230,-455],[405,-403], // visits the Titan's lava
  [465,-175],[447,135],[375,400],[105,454],[-190,460],[-445,348],[-485,28]
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
/* The roamer follows one continuous route, including the volcano, and stays outside city walls. */
// Continuous position and tangent through route corners, preventing abrupt head snapping.
// Catmull-Rom uses the same patrol waypoints; no changes to saved encounter locations.
export function balthrixPosition(t,speed=14){
 const P=BALTHRIX_ROUTE,n=P.length;
 const seg=P.map((p,i)=>Math.hypot(P[(i+1)%n][0]-p[0],P[(i+1)%n][1]-p[1]));
 const total=seg.reduce((a,b)=>a+b,0);
 let dist=((t*speed)%total+total)%total;
 for(let i=0;i<n;i++){
  if(dist<=seg[i]){
   const u=dist/seg[i],p0=P[(i+n-1)%n],p1=P[i],p2=P[(i+1)%n],p3=P[(i+2)%n];
   const point=(axis,v)=>0.5*((2*p1[axis])+(-p0[axis]+p2[axis])*v+(2*p0[axis]-5*p1[axis]+4*p2[axis]-p3[axis])*v*v+(-p0[axis]+3*p1[axis]-3*p2[axis]+p3[axis])*v*v*v);
   const x=point(0,u),z=point(1,u),before=Math.max(0,u-0.002),after=Math.min(1,u+0.002);
   const dx=point(0,after)-point(0,before),dz=point(1,after)-point(1,before);
   return {x,z,yaw:Math.atan2(dx,dz)};
  }
  dist-=seg[i];
 }
 return {x:P[0][0],z:P[0][1],yaw:0};
}
