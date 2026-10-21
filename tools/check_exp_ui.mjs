/* User-approved EXP bar + gold/purple frame regression suite.
 * Checks actual reward-to-persistent-level implementation, not screenshots. */
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {xpToNext,createExperience,EXP_STORE_KEY,START_LEVEL} from '../www/proto3d/combat/experience.js';
const root=new URL('../',import.meta.url);
const read=p=>readFileSync(new URL(p,root),'utf8');
const saved=new Map(),store={getItem:key=>saved.get(key)||null,setItem:(key,v)=>saved.set(key,v)};
assert.equal(START_LEVEL,40);
assert(xpToNext(41)>xpToNext(40),'next-level XP target grows');
const xp=createExperience(store);
assert.equal(xp.get('n:aldric_new').percent,0,'new hero starts empty');
const threshold=xpToNext(40);
const first=xp.award('n:aldric_new',Math.floor(threshold*.7));
assert.equal(first.level,40,'partial XP is not a level up');
assert(Math.abs(first.percent-70)<.1,'purple meter fills proportionally to earned XP');
const up=xp.award('n:aldric_new',threshold);
assert.equal(up.level,41,'XP overflow correctly levels up');
assert.equal(up.levels,1,'one level up reported');
assert.equal(up.xp,Math.floor(threshold*.7),'XP rolls over instead of disappearing');
assert.equal(xp.get('n:selene').level,40,'another hero does not inherit XP');
assert.equal(createExperience(store).get('n:aldric_new').xp,up.xp,'XP survives app reload');
assert(saved.has(EXP_STORE_KEY),'XP stored separately without changing save3d schema');
const max=xp.award('n:aldric_new',1e9);
assert.equal(max.level,200,'character level caps safely');
assert.equal(max.needed,0);
assert.equal(max.percent,100);
assert.equal(max.xp,0);
for(const x of [NaN,-1,undefined,'oops'])assert.equal(xp.award('n:selene',x).level,40,'invalid XP cannot change progression');
const fight=read('www/proto3d/fight.js'),hud=read('www/proto3d/combat/hud.js'),main=read('www/proto3d/main.js');
const ui=read('www/proto3d/varn-ui.css'),mini=read('www/proto3d/minimap.js');
assert(fight.includes("cc.on('reward', reward=>"),'EXP triggered by real rewards');
assert(fight.includes("progress.award(currentId,reward.xp)"),'XP awarded to active hero');
assert(fight.includes("level:saved.level"),'XP saved level restored into combat');
assert(hud.includes('class="vn-exp" role="progressbar"'),'EXP bar rendered in real HUD');
assert(hud.includes("this.expFill.style.transform='scaleX('+fraction+')'"),'EXP scales left to right');
assert(hud.includes('this.expFill.style.transform=\'scaleX(1)\''),'level-up rollover reaches 100%');
assert(hud.includes('this.expValue.textContent='),'XP progress shown numerically');
assert(mini.includes("createMiniMap(")&&main.includes('const miniMap=createMiniMap('),'minimap integrated with real position');
assert(ui.includes('VARNETHRYL ORNATE FRAME FIX') && ui.includes('border-image-slice:92'),'nine-sliced gold-purple ornate frame system applied to menus');
for(const asset of ['exp-frame.svg','minimap-ring.svg','panel-wide.svg','panel-square.svg','label-long.svg']){
 const path='www/assets/hud/'+asset;
 assert(existsSync(new URL(path,root)),path+' exists for offline release');
 const text=read(path);assert(text.startsWith('<svg')&&text.includes('url(#'),'SVG is genuine vector border');
}
console.log('PASS EXP progression, storage, leveling, UI, map, and all gold/amethyst frame assets');
