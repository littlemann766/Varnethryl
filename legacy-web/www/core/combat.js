/* Combat + stat math. UI-free; mods = {atk:[fn..], def:[fn..]} supplies the Quest/Mirror multipliers. */
import {HEROES,SUBSTAT_POOL} from '../data.js';
import {clamp,sample} from './util.js';
import {nLevel} from './party.js';
export function hpTarget(hero){let x=hero.style;let base=x==='tank'?65000:x==='heal'?34000:x==='melee'?34500:x==='ranged'?29500:x==='support'?31500:28500;if(hero.className==='Rogue')base=26000;if(hero.className==='Paladin')base=51000;if(hero.className==='Dark Knight')base=53000;if(hero.className==='Knight')base=64000;return base}
export function baseHP(state,hero){return Math.round(420+Math.pow(nLevel(state,hero.id)/80,1.7)*(hpTarget(hero)-420))}
export function getLoadout(state,heroId){return state.loadouts[heroId]||{}}
export function equipped(state,heroId){let l=getLoadout(state,heroId);return Object.values(l).map(id=>state.gear.find(it=>it.id===id)).filter(Boolean)}
/* mods.atk / mods.def: arrays of ()=>multiplier, applied left to right (same float order as the original Quest*Mirror chain). */
const NO_MODS={atk:[],def:[]};const mul=(v,fns)=>fns.reduce((a,f)=>a*f(),v);
export function combinedStats(state,heroId,mods=NO_MODS){let h=HEROES[heroId],l=nLevel(state,heroId);let hpPct=0,atkPct=0,defPct=0,crit=0,speed=0,leech=0,critDamage=0;let gear=equipped(state,heroId);for(let item of gear){if(item.type==='armor')defPct+=item.level*.02;else if(item.type==='weapon')atkPct+=item.level*.02;else {atkPct+=item.level*.008;defPct+=item.level*.008}for(let s of item.substats){let p=SUBSTAT_POOL.find(x=>x.id===s.id),v=Math.min(p.cap,s.value+s.boost*p.step);if(s.id==='hp')hpPct+=v;if(s.id==='crit')crit+=v;if(s.id==='speed')speed+=v;if(s.id==='lifesteal')leech+=v;if(s.id==='critDmg')critDamage+=v;}}
 hpPct=clamp(hpPct,0,28);crit=clamp(crit,0,35);speed=clamp(speed,0,35);leech=clamp(leech,0,12);
 let relic=state.relicLevels[heroId]||0;let attackBase=Math.round(95+Math.pow(l,1.72)*3.45+h.str*16+h.mag*7);
 return {hp:Math.round(baseHP(state,h)*(1+hpPct/100)),baseHp:baseHP(state,h),hpPct,attack:Math.round(mul(attackBase*(1+atkPct)*(1+relic*.005),mods.atk)),def:Math.round(mul((55+Math.pow(l,1.48)*4.3+h.def*12)*(1+defPct),mods.def)),crit,speed,leech,critDamage,abilities:gear.map(i=>i.ability).filter(Boolean)};
}
/* Damage roll of hitEnemy up to (and including) the "lucky" ability. RNG draw order is identical to the original:
   variance, crit, ability pick, then lucky only if picked. Returns the unrounded dmg and the ability so the host applies burn/frost/vampiric. */
export function rollHit(stats,mult=1,buffed=false,rng=Math.random){let dmg=stats.attack*(.8+rng()*.4)*mult*(buffed?1.25:1);if(rng()<.06+stats.crit/100)dmg*=1.55+stats.critDamage/100;let ability=sample(stats.abilities.length?stats.abilities:[null],rng);if(ability==='lucky'&&rng()<.10)dmg*=1.3;return {dmg,ability}}
/* Damage an enemy deals to a hero (enemyAttacks). rng is consumed once, for the dodge roll. */
export function enemyHurt(enemyAttack,defense,agi,rng=Math.random){let hurt=Math.max(12,Math.round(enemyAttack*1000/(1000+defense)));let dodge=agi*.005;if(rng()<dodge)hurt=0;return hurt}
