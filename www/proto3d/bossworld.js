/* Stable boss placements shared by world, combat, and QA.
   1 world unit is measured against the central Owner height (1.905 m).
   Boss patrol circles the OUTSIDE of the fortified town and crosses lava.
*/
export const TITAN_LAIR = Object.freeze({x:-397,z:-399});
export const FROST_SUMMIT = Object.freeze({x:-65,z:-325});
export const FROST_RETURN = Object.freeze({x:-65,z:-312});
export const HARBOR_SITE = Object.freeze({x:397,z:400});
export const CITY_SAFE_HALF = 210;
export const BALTHRIX_ROUTE = Object.freeze([
  [-397,-399],[-475,-195],[-420,78],[-265,385],[-10,470],
  [235,438],[453,200],[462,-152],[253,-449],[-42,-460]
]);
export const isTownSafe=(x,z,margin=0)=>Math.abs(x)<CITY_SAFE_HALF+margin&&Math.abs(z)<CITY_SAFE_HALF+margin;
export const wilderness=(x,z,limit=552)=>Math.abs(x)<limit&&Math.abs(z)<limit&&!isTownSafe(x,z,12);
export function balthrixPatrol(seconds=0) {
  const points=BALTHRIX_ROUTE, legs=[],speed=5.2;
  let total=0;
  for(let i=0;i<points.length;i++){const a=points[i],b=points[(i+1)%points.length];const length=Math.hypot(b[0]-a[0],b[1]-a[1]);legs.push(length);total+=length;}
  let d=(((seconds*speed)%total)+total)%total;
  for(let i=0;i<points.length;i++){
    if(d>legs[i]){d-=legs[i];continue;}
    const a=points[i],b=points[(i+1)%points.length],t=d/legs[i];
    return {x:a[0]+(b[0]-a[0])*t,z:a[1]+(b[1]-a[1])*t};
  }
  return {x:points[0][0],z:points[0][1]};
}
