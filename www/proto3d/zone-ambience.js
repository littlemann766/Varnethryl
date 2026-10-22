/* Zone atmosphere presets. Pure math: world ambience only, no user state.
 * Keep daylight outside the cave. The volcano receives a warm, local haze;
 * in Frost Realm, the sunlight is actually dimmed rather than relying on
 * cave wall materials to fight global sun/sky brightness. */
const clamp01=x=>Math.min(1,Math.max(0,Number.isFinite(x)?x:0));
const smooth=x=>{const t=clamp01(x);return t*t*(3-2*t);};
export const DAYLIGHT=Object.freeze({fogColor:0xdde8ee,fogNear:70,fogFar:180,sun:2.2,fill:1.25,sunColor:0xfff0d0,darkSky:false});
export const FROST_CAVE=Object.freeze({fogColor:0x0d1829,fogNear:27,fogFar:165,sun:0.17,fill:0.35,sunColor:0x779cce,darkSky:true});
export const VOLCANO=Object.freeze({fogColor:0x786257,fogNear:57,fogFar:172,sun:1.9,fill:1.12,sunColor:0xffbd8d,darkSky:false});
export const HYDRA_MIRE=Object.freeze({fogColor:0x4b6872,fogNear:85,fogFar:320,sun:1.02,fill:0.85,sunColor:0xc5d9e6,darkSky:false});
export const TIDEWRACK_OCEAN=Object.freeze({fogColor:0x80b5c6,fogNear:375,fogFar:1120,sun:2.3,fill:1.35,sunColor:0xffe5cb,darkSky:false});
export function zoneAtmosphere(zone,x=0,z=0,titan={x:405,z:-402},scale=1){
 const view=Math.max(1,Math.min(2.2,Number.isFinite(scale)?scale:1));
 if(zone==='frost')return {...FROST_CAVE,fogNear:FROST_CAVE.fogNear*view,fogFar:FROST_CAVE.fogFar*view,heat:0};
 if(zone==='hydra')return {...HYDRA_MIRE,fogNear:HYDRA_MIRE.fogNear*view,fogFar:HYDRA_MIRE.fogFar*view,heat:0};
 if(zone==='sailing')return {...TIDEWRACK_OCEAN,fogNear:TIDEWRACK_OCEAN.fogNear*view,fogFar:TIDEWRACK_OCEAN.fogFar*view,heat:0};
 const distance=Math.hypot(x-titan.x,z-titan.z);
 const heat=zone==='town'?smooth((220-distance)/135):0;
 if(heat<=0)return {...DAYLIGHT,fogNear:DAYLIGHT.fogNear*view,fogFar:DAYLIGHT.fogFar*view,heat:0};
 // Hex colors interpolate in THREE at the render layer. Fog bounds and
 // light levels are already smoothed here, so mobile work is constant.
 return {
 fogColor:heat>.42?VOLCANO.fogColor:DAYLIGHT.fogColor,
 fogNear:(DAYLIGHT.fogNear+(VOLCANO.fogNear-DAYLIGHT.fogNear)*heat)*view,
 fogFar:(DAYLIGHT.fogFar+(VOLCANO.fogFar-DAYLIGHT.fogFar)*heat)*view,
 sun:DAYLIGHT.sun+(VOLCANO.sun-DAYLIGHT.sun)*heat,
 fill:DAYLIGHT.fill+(VOLCANO.fill-DAYLIGHT.fill)*heat,
 sunColor:heat>.42?VOLCANO.sunColor:DAYLIGHT.sunColor,
 heat,darkSky:false
 };
}
