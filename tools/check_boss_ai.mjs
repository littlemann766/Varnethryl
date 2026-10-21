/* Boss behaviour regression: pure AI + stable source integration.
 * node tools/check_boss_ai.mjs */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {EnemyAIController} from '../www/proto3d/combat/ai.js';
import {bossHome,outsideBossArena,telegraphKey} from '../www/proto3d/combat/boss-arena.js';
import {BOSS_PATTERNS,ENEMIES} from '../www/proto3d/combat/data.js';

const owner=()=>({x:0,z:0,dead:false});
const arena=bossHome('frosttroll_a',10,20);
assert.deepEqual(arena,{homeX:10,homeZ:20,homeRadius:112});
assert.equal(bossHome('vaelthryx',10,20),null,'Balthrix must keep roaming freely');
assert(outsideBossArena({...arena},arena.homeX+arena.homeRadius+1,20));
assert(!outsideBossArena({...arena},arena.homeX+arena.homeRadius-1,20));
assert.notEqual(telegraphKey('cone',{cos:.28}),telegraphKey('cone',{cos:.13}), 'different cone attacks have different hitbox warnings');
assert.equal(telegraphKey('line',{width:3}),telegraphKey('line',{width:5}));
assert.equal(telegraphKey('ring',{}),'ring');
assert(ENEMIES.frosttroll_b.trollTint===true,'ice-blue younger Frost Troll model variant');

const ai=new EnemyAIController(),steps=[];
const env={HS:1.5,RM:1,move(e,dx,dz){steps.push(Math.hypot(dx,dz));e.x+=dx;e.z+=dz;}};
const e={key:'frosttroll_a',def:ENEMIES.frosttroll_a,x:12,z:20,yaw:0,
 hp:20,max:100,phase:2,state:'telegraph',tStateT:.2,atkCd:0,flash:0,
 pat:BOSS_PATTERNS.frosttroll_a[1],...arena};
let landed=ai.update(e,{x:150,z:20,dead:false},.1,env);
assert.equal(landed,null,'no delayed attack when player exits arena mid-telegraph');
assert.equal(e.state,'return','frost brother disengages and walks home');
assert.equal(e.pat,null,'telegraphed attack cancelled when player flees');
assert(steps.length>0,'boss begins walking, not teleporting');
for(let i=0;i<140&&e.state==='return';i++)ai.update(e,{x:160,z:20,dead:false},.1,env);
assert.equal(e.state,'idle','boss reaches home');
assert.equal(e.hp,100,'abandoned fight resets health');
assert.equal(e.phase,1,'abandoned fight resets enrage');
assert.equal(e.patI,0,'attack sequence restarts after retreat');
assert(Math.hypot(e.x-arena.homeX,e.z-arena.homeZ)<1.7,'boss returns near its original start point');
ai.update(e,{x:arena.homeX+3,z:arena.homeZ,dead:false},.1,env);
assert.equal(e.state,'chase','player re-entering arena can restart the fight');
e.state='idle';
ai.update(e,{x:arena.homeX+arena.homeRadius+2,z:arena.homeZ,dead:false},.1,env);
assert.equal(e.state,'idle','arena boundary prevents immediate aggro');

const roamer={key:'vaelthryx',def:ENEMIES.vaelthryx,x:0,z:0,yaw:0,hp:10,max:100,phase:1,state:'chase',tStateT:0,atkCd:0,flash:0};
ai.update(roamer,{x:230,z:0,dead:false},.1,env);
assert.equal(roamer.state,'chase','Balthrix remains an unrestricted overworld boss');
for(const [key,radius] of Object.entries({frosttroll_a:112,frosttroll_b:112,titan40:132,titan:132})){
 assert.equal(bossHome(key,0,0).homeRadius,radius);
}
const txt=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const fight=txt('www/proto3d/fight.js'),cc=txt('www/proto3d/combat/controller.js');
assert(fight.includes("generation!==spawnEpoch"),'stale async GLBs cannot spawn after a portal');
assert(fight.includes('spawnEpoch++'),'fight stop invalidates pending spawns');
assert(fight.includes('regionClock>=frostSpawnT'),'Frost brothers respawn after player death');
assert(fight.includes("telegraphKey(shape,pt)"),'boss warning geometry selects attack-specific angle');
assert(fight.includes('const GL_CONES=new Map()'),'only one cone geometry per angle');
assert(fight.includes("e.state === 'return'"),'retreating bosses animate their locomotion');
assert(fight.includes("(ev.e?.def?.name || 'THE BOSS')"),'enrage message names actual boss');
assert(cc.includes("this.emit('bossRetreat'"),'combat clears lock-on when boss leaves arena');
assert(cc.includes("this.emit('bossReset'"),'combat emits boss reset only when returned');
for(const p of ['www/proto3d/combat/ai.js','www/proto3d/combat/boss-arena.js','www/proto3d/combat/controller.js','www/proto3d/fight.js','www/proto3d/combat/data.js']){
 const result=spawnSync(process.execPath,['--check',p],{encoding:'utf8'});
 assert.equal(result.status,0,p+' parse failure: '+result.stderr);
}
console.log('PASS: boss leashes, telegraph geometry keys, retreat/home reset, re-aggro, free-roaming Balthrix, spawn race protection and Frost respawns');
