/* proto3d <-> shared save bridge. No DOM/Three.js, so it runs in node tests. Uses www/core/save.js and party.js. */
import {SAVE_KEY,isValidSave,loadState,writeState,freshState} from '../core/save.js';
import {sanitizeParty} from '../core/party.js';
import {HEROES} from '../data.js';
export const P3D_KEY='p3d';
export const P3D_ZONES=['village'];
const fin=n=>typeof n==='number'&&Number.isFinite(n);
/* Returns {status:'none'|'corrupt'|'ok', state}. state is a sanitised copy for status ok, otherwise null. */
export function readSave(storage){let raw=null;try{raw=storage.getItem(SAVE_KEY)}catch(e){return {status:'none',state:null}}
 if(raw==null)return {status:'none',state:null};
 try{if(isValidSave(JSON.parse(raw)))return {status:'ok',state:loadState(storage)}}catch(e){}
 return {status:'corrupt',state:null}}
/* glbNames: 3D hero names in 3D index order. Returns {party:[glbIdx], hero:glbIdx, followers:[glbIdx], pos:{x,z,yaw}|null} or null. */
export function planFromState(state,glbNames,world){if(!state)return null;
 const toGlb=id=>{const h=HEROES[id];return h?glbNames.indexOf(h.name):-1};
 const party=state.party.map(toGlb).filter(i=>i>=0);if(!party.length)return null;
 let hero=toGlb(state.active);if(!party.includes(hero))hero=party[0];
 return {party,hero,followers:party.filter(i=>i!==hero),pos:readPos(state,world)}}
export function readPos(state,world){const p=state&&state[P3D_KEY];if(!p||typeof p!=='object')return null;
 if(p.zone!==undefined&&!P3D_ZONES.includes(p.zone))return null;
 if(!fin(p.x)||!fin(p.z))return null;const lim=(fin(world)?world:60)-1.5;
 if(Math.abs(p.x)>lim||p.z<-lim||p.z>lim)return null;
 return {x:p.x,z:p.z,yaw:fin(p.yaw)?p.yaw:0}}
/* Writes the 3D fields into the latest stored save (so 2D progress made elsewhere is never overwritten). Returns true if written. */
export function writeSnapshot(storage,snap,glbNames){
 if(!snap||!fin(snap.x)||!fin(snap.z))return false;
 const r=readSave(storage);if(r.status==='corrupt')return false;
 const s=r.status==='ok'?r.state:sanitizeParty(freshState());
 if(fin(snap.heroGlb)){const id=HEROES.findIndex(h=>h.name===glbNames[snap.heroGlb]);if(id>=0&&s.party.includes(id))s.active=id}
 s[P3D_KEY]={zone:'village',x:Math.round(snap.x*100)/100,z:Math.round(snap.z*100)/100,yaw:fin(snap.yaw)?Math.round(snap.yaw*1000)/1000:0};
 try{writeState(storage,s);return true}catch(e){return false}}
/* Debounced saver. getSnap() returns the current snapshot; call mark() on change, flush() on pagehide/hidden. */
export function createSaver(storage,glbNames,getSnap,delay=900,timers=globalThis){let h=null,dirty=false;
 const flush=()=>{if(h!==null){timers.clearTimeout(h);h=null}if(!dirty)return false;dirty=false;return writeSnapshot(storage,getSnap(),glbNames)};
 return {mark(){dirty=true;if(h===null)h=timers.setTimeout(()=>{h=null;flush()},delay)},flush,get dirty(){return dirty}}}
