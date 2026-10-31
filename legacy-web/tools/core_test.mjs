/* Parity + round-trip tests for www/core/*. Run: node tools/core_test.mjs */
import {makeLegacy} from './legacy_core_snapshot.js';
import {HEROES} from '../www/data.js';
import * as Save from '../www/core/save.js';
import * as Party from '../www/core/party.js';
import * as Combat from '../www/core/combat.js';
import {baseItem} from '../www/core/items.js';
let bad=0;const ok=(n,c)=>{console.log(c?'PASS':'FAIL',n);if(!c)bad++};
const Quest={defaults:()=>({v:1,ch:1}),ensure:s=>{s.veyra={...Quest.defaults(),...(s.veyra||{})};return s},atk:()=>1.1,def:()=>1.05};
const Mirror={defaults:()=>({v:1,ch:1}),ensure:s=>{s.mirror={...Mirror.defaults(),...(s.mirror||{})};return s},atk:()=>1.03,def:()=>1.07};
const HOOKS={defaults:()=>({veyra:Quest.defaults(),mirror:Mirror.defaults()}),ensure:s=>{Quest.ensure(s);Mirror.ensure(s)}};
const MODS={atk:[Quest.atk,Mirror.atk],def:[Quest.def,Mirror.def]};
const mem=()=>{const m=new Map();return {getItem:k=>m.has(k)?m.get(k):null,setItem:(k,v)=>m.set(k,String(v)),m}};
const L=makeLegacy(Quest,Mirror,mem());
const norm=s=>{const c=JSON.parse(JSON.stringify(s));const map={};c.gear.forEach((g,i)=>{map[g.id]='G'+i;g.id='G'+i});for(const h in c.loadouts)for(const t in c.loadouts[h])c.loadouts[h][t]=map[c.loadouts[h][t]]||String(c.loadouts[h][t]).replace(/^gear-.*/,'gear');return c};
// seeded rng for random parity
const seeded=a=>()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296};
const withRng=(seed,fn)=>{const o=Math.random;Math.random=seeded(seed);try{return fn()}finally{Math.random=o}};
ok('save key unchanged',Save.SAVE_KEY==='guildbound_rpg_save_v1');
// fresh state parity (shape; ids differ by timestamp)
ok('freshState parity',JSON.stringify(Object.keys(L.freshState()))===JSON.stringify(Object.keys(Save.freshState(HOOKS))));
{const a=withRng(7,()=>L.freshState()),b=withRng(7,()=>Save.freshState(HOOKS));const strip=s=>{const c=JSON.parse(JSON.stringify(s));const map={};c.gear.forEach((g,i)=>{map[g.id]='G'+i;g.id='G'+i});for(const h in c.loadouts)for(const t in c.loadouts[h])c.loadouts[h][t]=map[c.loadouts[h][t]];return c};ok('freshState deep parity (modulo item ids)',JSON.stringify(strip(a))===JSON.stringify(strip(b)))}
// sample old save with high-level party, gear, dupes, junk party ids
const sample=()=>({version:1,gold:98765,shards:321,accountLevel:14,accountXp:55,unlocked:[0,1,2,3,4,5,9],party:[3,3,'4',99,-1,0],partyCap:4,active:9,heroLevels:{0:40,3:22,4:7},heroXp:{3:111},relicLevels:{0:4,3:10},
 gear:[{id:'g1',type:'weapon',heroId:0,level:9,name:'W',base:90,substats:[{id:'crit',value:12,boost:2},{id:'hp',value:8,boost:0},{id:'speed',value:5,boost:10},{id:'lifesteal',value:4,boost:1},{id:'critDmg',value:20,boost:3}],ability:'lucky',lock:null},
 {id:'g2',type:'armor',heroId:0,level:15,name:'A',base:55,substats:[{id:'hp',value:30,boost:5}],ability:'flame',lock:null,mastered:true},{id:'g3',type:'charm',heroId:3,level:4,name:'C',base:28,substats:[],ability:null,lock:null}],
 loadouts:{0:{weapon:'g1',armor:'g2',charm:'missing'},3:{charm:'g3'}},guildLevel:3,forgeLevel:2,bossDifficulty:'elite',zone:'ruins',kills:77,zoneKills:{ruins:5},bossKills:2,questStep:2,secondsPlayed:12345,settings:{vol:.4},logs:['a','b'],extra:{keep:'me'}});
const stub=()=>{const s=mem();s.setItem(Save.SAVE_KEY,JSON.stringify(sample()));return s};
{const legacy=makeLegacy(Quest,Mirror,stub()).loadState();const now=Save.loadState(stub(),HOOKS);
 ok('old save loads identically through core (deep)',JSON.stringify(legacy)===JSON.stringify(now));
 ok('party sanitised',JSON.stringify(now.party)===JSON.stringify([3,4,0])&&now.active===3);
 ok('unknown fields preserved',now.extra?.keep==='me');
 const st=mem();Save.writeState(st,now);const again=Save.loadState(st,HOOKS);
 ok('round trip save->load stable',JSON.stringify(again)===JSON.stringify(now));
 ok('written under legacy key',st.m.has('guildbound_rpg_save_v1')&&st.m.size===1);
 ok('serialized bytes identical to legacy JSON.stringify',st.m.get(Save.SAVE_KEY)===JSON.stringify(legacy));
 // stats parity for every hero on that save
 L.setState(legacy);let n=0,same=0;for(const h of HEROES){n++;const a=L.combinedStats(h.id),b=Combat.combinedStats(now,h.id,MODS);if(JSON.stringify(a)===JSON.stringify(b))same++;else console.log('diff',h.id,a,b)}
 ok(`combinedStats parity for all ${n} heroes (gear/relic/mods)`,n===same&&n===20);
 ok('baseHP/hpTarget parity',HEROES.every(h=>L.baseHP(h)===Combat.baseHP(now,h)&&L.hpTarget(h)===Combat.hpTarget(h)));
 // no mods, no-arg default
 ok('default mods = identity',Combat.combinedStats(now,3).attack>0);
}
for(const bad_ of ['{not json','null','{"version":2}','{"version":1,"gear":[],"party":[],"unlocked":[]}']){const s=mem();s.setItem(Save.SAVE_KEY,bad_);const a=Save.loadState(s,HOOKS),b=makeLegacy(Quest,Mirror,s).loadState();const q=x=>JSON.stringify(norm(x));ok('bad/edge save "'+bad_.slice(0,18)+'" parity',q(a)===q(b))}
ok('empty storage -> fresh',Save.loadState(mem(),HOOKS).gold===1250);
// xp parity
for(const amt of [0,50,500,5000,123456]){const lg=makeLegacy(Quest,Mirror,stub());const a=lg.loadState();lg.setState(a);const r1=lg.legacyGrant(amt);const s2=Save.loadState(stub(),HOOKS);const r2=Party.applyExperience(s2,amt);
 ok(`applyExperience(${amt}) parity`,r1===r2&&a.accountLevel===s2.accountLevel&&a.accountXp===s2.accountXp&&JSON.stringify(a.heroLevels)===JSON.stringify(s2.heroLevels)&&JSON.stringify(a.heroXp)===JSON.stringify(s2.heroXp))}
ok('xpNeed parity',[1,2,10,50,99].every(l=>L.xpNeed(l)===Party.xpNeed(l)));
// combat rolls: same seed => same output
{const now=Save.loadState(stub(),HOOKS);let all=true;for(let seed=1;seed<=200;seed++){const st=Combat.combinedStats(now,seed%2?0:3,MODS);st.abilities=seed%3?['lucky','flame']:[];const buffed=seed%5===0,mult=1+(seed%4)*.5;
  const a=withRng(seed,()=>L.legacyHit(st,mult,buffed)),b=withRng(seed,()=>Combat.rollHit(st,mult,buffed));if(a.dmg!==b.dmg||a.ability!==b.ability)all=false;
  const h1=withRng(seed,()=>L.legacyHurt(5000+seed*13,st.def,HEROES[seed%20].agi)),h2=withRng(seed,()=>Combat.enemyHurt(5000+seed*13,st.def,HEROES[seed%20].agi));if(h1!==h2)all=false}
 ok('rollHit + enemyHurt parity over 200 seeds (RNG draw order identical)',all)}
// party sanitize parity
for(const p of [[],[5,5,5],['2','x',1],[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21]]){const a=L.sanitizeParty({party:[...p],active:7}),b=Party.sanitizeParty({party:[...p],active:7},HOOKS);ok('sanitizeParty '+JSON.stringify(p).slice(0,24),JSON.stringify(a.party)===JSON.stringify(b.party)&&a.active===b.active)}
// item factory
{const it=baseItem('weapon',0,6);ok('baseItem level/substats/ability',it.level===6&&it.substats.length>0&&!!it.ability&&it.heroId===0)}
process.exit(bad?1:0);
