/* Persistent Varnethryl experience: pure progression rules, no THREE/DOM.
 * Each established hero/skin shares one progress record; no save schema migration.
 * XP is awarded only from CombatController's one-time 'reward' event. */
import { heroKey } from './herokits.js';
export const EXP_STORE_KEY='vn_p3d_experience_v1';
export const START_LEVEL=40;
const MAX_LEVEL=200,MAX_XP=1_000_000_000;
export const xpToNext=level=>{
 const L=Math.max(1,Math.min(MAX_LEVEL,Math.floor(Number(level)||1)));
 return L>=MAX_LEVEL?0:Math.round(250+24*L+0.52*L*L);
};
const clamp=(n,a,b,d)=>Number.isFinite(n)?Math.min(b,Math.max(a,Math.floor(n))):d;
const cleanId=id=>heroKey(String(id||'')).replace(/[^a-z0-9_-]/gi,'').slice(0,64)||'hero';
export function createExperience(storage,baseLevel=START_LEVEL){
 const starting=clamp(baseLevel,1,MAX_LEVEL,START_LEVEL);
 let all=Object.create(null);
 try{
  const raw=JSON.parse(storage?.getItem(EXP_STORE_KEY)||'null');
  if(raw&&typeof raw==='object'&&!Array.isArray(raw)&&raw.version===1&&raw.heroes&&typeof raw.heroes==='object'){
    for(const [id,p] of Object.entries(raw.heroes)){
     if(!id||id==='__proto__'||!p||typeof p!=='object')continue;
     const level=clamp(p.level,1,MAX_LEVEL,starting);
     const xp=clamp(p.xp,0,level>=MAX_LEVEL?0:Math.max(0,xpToNext(level)-1),0);
     all[cleanId(id)]={level,xp,total:clamp(p.total,0,MAX_XP,0)};
    }
  }
 }catch(_){}
 const save=()=>{try{storage?.setItem(EXP_STORE_KEY,JSON.stringify({version:1,heroes:all}));}catch(_){}};
 const get=id=>{
  const k=cleanId(id);
  if(!all[k])all[k]={level:starting,xp:0,total:0};
  const p=all[k],needed=xpToNext(p.level);
  return {id:k,level:p.level,xp:p.xp,needed,total:p.total,percent:needed?Math.min(100,Math.max(0,p.xp/needed*100)):100};
 };
 const award=(id,amount)=>{
  const prev=get(id),n=clamp(amount,0,MAX_XP,0);
  if(!n)return {...prev,gained:0,levels:0};
  const p=all[prev.id];p.total=Math.min(MAX_XP,p.total+n);p.xp+=n;
  let levels=0;
  while(p.level<MAX_LEVEL&&p.xp>=xpToNext(p.level)){
   p.xp-=xpToNext(p.level);p.level++;levels++;
  }
  if(p.level>=MAX_LEVEL)p.xp=0;
  save();
  return {...get(id),gained:n,levels};
 };
 const setLevel=(id,level)=>{
  const prev=get(id),p=all[prev.id];
  p.level=clamp(level,1,MAX_LEVEL,prev.level);
  p.xp=0;
  save();
  return get(id);
 };
 return {get,award,setLevel,save};
}
