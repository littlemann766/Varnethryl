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
export function balthrixPosition(t,speed=14){
 const P=BALTHRIX_ROUTE,seg=P.map((p,i)=>Math.hypot(P[(i+1)%P.length][0]-p[0],P[(i+1)%P.length][1]-p[1])),total=seg.reduce((a,b)=>a+b,0);
 let dist=((t*speed)%total+total)%total;
 for(let i=0;i<P.length;i++){
   if(dist<=seg[i]){const a=P[i],b=P[(i+1)%P.length],u=dist/seg[i];
     return {x:a[0]+(b[0]-a[0])*u,z:a[1]+(b[1]-a[1])*u,yaw:Math.atan2(b[0]-a[0],b[1]-a[1])};}
   dist-=seg[i];
 }
 return {x:P[0][0],z:P[0][1],yaw:0};
}
