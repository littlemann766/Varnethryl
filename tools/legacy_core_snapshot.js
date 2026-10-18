/* Verbatim snapshot of the pre-0.6.5 game.js logic (origin/main 5082257), used only by core_test.mjs for parity checks. */
import {HEROES,TIERS,SUBSTAT_POOL,ABILITIES} from '../www/data.js';
export function makeLegacy(Quest,Mirror,localStorage){
const clamp=(n,a,b)=>Math.max(a,Math.min(b,n)); const rand=(a,b)=>a+Math.random()*(b-a); const sample=a=>a[Math.floor(Math.random()*a.length)];
const key='guildbound_rpg_save_v1';let nextId=1;let state;
const baseItem=(kind,heroId,lv=0)=>{
 const h=HEROES[heroId],names={weapon:h.weapon,armor:`${h.className} Battle Armor`,charm:`${h.className} Sigil`};
 const it={id:`gear-${Date.now().toString(36)}-${nextId++}`,type:kind,heroId,level:0,name:names[kind],base:kind==='weapon'?90:kind==='armor'?55:28,substats:[],ability:null,lock:null};
 while(it.level<lv)advanceItem(it);return it;
};
function tier(it){return TIERS[Math.floor(it.level/3)]||TIERS[0]}
function makeRoll(exclude=[]){let pool=SUBSTAT_POOL.filter(s=>!exclude.includes(s.id));if(!pool.length)return null;let p=sample(pool);return {id:p.id,value:Math.round(rand(p.min,p.max)*100)/100,boost:0}}
function advanceItem(it){it.level++;let t=tier(it);while(it.substats.length<t.slots){let r=makeRoll(it.substats.map(s=>s.id));if(r)it.substats.push(r);else break;} if(it.level>=3&&!it.ability)it.ability=sample(ABILITIES).id;if(it.level===15)it.mastered=true}
function freshState(){let inv=[baseItem('weapon',0),baseItem('armor',0),baseItem('charm',0),baseItem('weapon',1),baseItem('weapon',2)];return {version:1,gold:1250,shards:55,accountLevel:1,accountXp:0,unlocked:[0,1,2],party:[0,1,2],partyCap:3,active:0,heroLevels:{0:1,1:1,2:1},heroXp:{},relicLevels:{},gear:inv,loadouts:{0:{weapon:inv[0].id,armor:inv[1].id,charm:inv[2].id},1:{weapon:inv[3].id},2:{weapon:inv[4].id}},guildLevel:1,forgeLevel:1,bossDifficulty:'standard',zone:'village',kills:0,zoneKills:{},bossKills:0,questStep:0,secondsPlayed:0,settings:{},veyra:Quest.defaults(),mirror:Mirror.defaults(),logs:['Welcome to Liongate. Your guild adventure begins!']}}
function sanitizeParty(s){let seen=new Set();s.party=(s.party||[]).map(Number).filter(id=>Number.isFinite(id)&&HEROES[id]&&!seen.has(id)&&seen.add(id));if(!s.party.length)s.party=[0];s.active=+s.active;if(!s.party.includes(s.active))s.active=s.party[0];Quest.ensure(s);Mirror.ensure(s);return s}
function loadState(){try{let s=JSON.parse(localStorage.getItem(key));if(s && s.version===1 && Array.isArray(s.gear)&&Array.isArray(s.party)&&Array.isArray(s.unlocked))return sanitizeParty({...freshState(),...s});}catch(e){console.warn('Could not read save',e)}return freshState()}
function nLevel(id){return state.heroLevels[id]||1}
function hpTarget(hero){let x=hero.style;let base=x==='tank'?65000:x==='heal'?34000:x==='melee'?34500:x==='ranged'?29500:x==='support'?31500:28500;if(hero.className==='Rogue')base=26000;if(hero.className==='Paladin')base=51000;if(hero.className==='Dark Knight')base=53000;if(hero.className==='Knight')base=64000;return base}
function baseHP(hero){return Math.round(420+Math.pow(nLevel(hero.id)/80,1.7)*(hpTarget(hero)-420))}
function getLoadout(heroId){return state.loadouts[heroId]||{}}
function equipped(heroId){let l=getLoadout(heroId);return Object.values(l).map(id=>state.gear.find(it=>it.id===id)).filter(Boolean)}
function combinedStats(heroId){let h=HEROES[heroId],l=nLevel(heroId);let hpPct=0,atkPct=0,defPct=0,crit=0,speed=0,leech=0,critDamage=0;let gear=equipped(heroId);for(let item of gear){if(item.type==='armor')defPct+=item.level*.02;else if(item.type==='weapon')atkPct+=item.level*.02;else {atkPct+=item.level*.008;defPct+=item.level*.008}for(let s of item.substats){let p=SUBSTAT_POOL.find(x=>x.id===s.id),v=Math.min(p.cap,s.value+s.boost*p.step);if(s.id==='hp')hpPct+=v;if(s.id==='crit')crit+=v;if(s.id==='speed')speed+=v;if(s.id==='lifesteal')leech+=v;if(s.id==='critDmg')critDamage+=v;}}
 hpPct=clamp(hpPct,0,28);crit=clamp(crit,0,35);speed=clamp(speed,0,35);leech=clamp(leech,0,12);
 let relic=state.relicLevels[heroId]||0;let attackBase=Math.round(95+Math.pow(l,1.72)*3.45+h.str*16+h.mag*7);
 return {hp:Math.round(baseHP(h)*(1+hpPct/100)),baseHp:baseHP(h),hpPct,attack:Math.round(attackBase*(1+atkPct)*(1+relic*.005)*Quest.atk()*Mirror.atk()),def:Math.round((55+Math.pow(l,1.48)*4.3+h.def*12)*(1+defPct)*Quest.def()*Mirror.def()),crit,speed,leech,critDamage,abilities:gear.map(i=>i.ability).filter(Boolean)};
}
function xpNeed(level){return Math.round(82+level*28+Math.pow(level,1.35)*15)}
function legacyGrant(amount){state.accountXp+=amount;for(const id of state.party)state.heroXp[id]=(state.heroXp[id]||0)+amount;let lvlups=0;while(state.accountXp>=xpNeed(state.accountLevel)){state.accountXp-=xpNeed(state.accountLevel);state.accountLevel++;lvlups++;}for(const id of state.party){let n=nLevel(id),x=state.heroXp[id]||0;while(x>=xpNeed(n)){x-=xpNeed(n);n++;}state.heroXp[id]=x;state.heroLevels[id]=n;}return lvlups}
function legacyHit(stats,mult,buffed){let dmg=stats.attack*(.8+Math.random()*.4)*mult*(buffed?1.25:1);if(Math.random()<.06+stats.crit/100)dmg*=1.55+stats.critDamage/100;let ability=sample(stats.abilities.length?stats.abilities:[null]);if(ability==='lucky'&&Math.random()<.10)dmg*=1.3;return {dmg,ability}}
function legacyHurt(attack,defense,agi){let hurt=Math.max(12,Math.round(attack*1000/(1000+defense)));let dodge=agi*.005;if(Math.random()<dodge)hurt=0;return hurt}
return {freshState,sanitizeParty,loadState,combinedStats,baseHP,hpTarget,xpNeed,legacyGrant,legacyHit,legacyHurt,baseItem,advanceItem,tier,setState:s=>{state=s},get state(){return state}};
}
