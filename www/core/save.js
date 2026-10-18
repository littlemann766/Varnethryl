/* Save format + load/save. Key and shape are unchanged (guildbound_rpg_save_v1, version 1). */
import {baseItem} from './items.js';
import {sanitizeParty} from './party.js';
export const SAVE_KEY='guildbound_rpg_save_v1';
/* hooks: {defaults:()=>({veyra,mirror}), ensure:s=>void}; supplied by the host (Quest/Mirror live in the 2D UI layer). */
export function freshState(hooks={}){let inv=[baseItem('weapon',0),baseItem('armor',0),baseItem('charm',0),baseItem('weapon',1),baseItem('weapon',2)];const d=hooks.defaults?hooks.defaults():{};return {version:1,gold:1250,shards:55,accountLevel:1,accountXp:0,unlocked:[0,1,2],party:[0,1,2],partyCap:3,active:0,heroLevels:{0:1,1:1,2:1},heroXp:{},relicLevels:{},gear:inv,loadouts:{0:{weapon:inv[0].id,armor:inv[1].id,charm:inv[2].id},1:{weapon:inv[3].id},2:{weapon:inv[4].id}},guildLevel:1,forgeLevel:1,bossDifficulty:'standard',zone:'village',kills:0,zoneKills:{},bossKills:0,questStep:0,secondsPlayed:0,settings:{},veyra:d.veyra,mirror:d.mirror,logs:['Welcome to Liongate. Your guild adventure begins!']}}
export function isValidSave(s){return !!(s && s.version===1 && Array.isArray(s.gear)&&Array.isArray(s.party)&&Array.isArray(s.unlocked))}
/* storage: anything with getItem (localStorage). Returns a sanitised state, or a fresh one on missing/corrupt data. */
export function loadState(storage,hooks={}){try{let s=JSON.parse(storage.getItem(SAVE_KEY));if(isValidSave(s))return sanitizeParty({...freshState(hooks),...s},hooks);}catch(e){console.warn('Could not read save',e)}return freshState(hooks)}
export function serializeState(state){return JSON.stringify(state)}
export function writeState(storage,state){storage.setItem(SAVE_KEY,serializeState(state))}
