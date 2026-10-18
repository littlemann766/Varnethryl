/* Gear items: tiers, substat rolls, advancement. Moved verbatim from game.js (no DOM). */
import {HEROES,TIERS,SUBSTAT_POOL,ABILITIES} from '../data.js';
import {rand,sample} from './util.js';
let nextId=1;
export function tier(it){return TIERS[Math.floor(it.level/3)]||TIERS[0]}
export function makeRoll(exclude=[]){let pool=SUBSTAT_POOL.filter(s=>!exclude.includes(s.id));if(!pool.length)return null;let p=sample(pool);return {id:p.id,value:Math.round(rand(p.min,p.max)*100)/100,boost:0}}
export function advanceItem(it){it.level++;let t=tier(it);while(it.substats.length<t.slots){let r=makeRoll(it.substats.map(s=>s.id));if(r)it.substats.push(r);else break;} if(it.level>=3&&!it.ability)it.ability=sample(ABILITIES).id;if(it.level===15)it.mastered=true}
export const baseItem=(kind,heroId,lv=0)=>{
 const h=HEROES[heroId],names={weapon:h.weapon,armor:`${h.className} Battle Armor`,charm:`${h.className} Sigil`};
 const it={id:`gear-${Date.now().toString(36)}-${nextId++}`,type:kind,heroId,level:0,name:names[kind],base:kind==='weapon'?90:kind==='armor'?55:28,substats:[],ability:null,lock:null};
 while(it.level<lv)advanceItem(it);return it;
};
