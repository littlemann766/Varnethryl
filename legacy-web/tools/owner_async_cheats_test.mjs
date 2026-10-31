// Every asynchronous Owner action must surface its actual result instead of
// an optimistic "done" before the map / monster operation has completed.
import assert from 'node:assert/strict';
import {createCheats,createFlags} from '../www/proto3d/cheats.js';
const store=new Map();
const storage={getItem:k=>store.get(k)??null,setItem:(k,v)=>store.set(k,v),removeItem:k=>store.delete(k)};
let ok=false;
const env={storage,flags:createFlags(),zones:['village','sailing'],
  places:()=>[{id:'inn',x:8,z:14}],
  teleport:async()=>{await Promise.resolve();return ok;},
  hooks:{
   spawnEnemy:async()=>{await Promise.resolve();return ok;},
   healParty:async()=>{await Promise.resolve();return ok;},
   killEnemies:()=>false
  }};
const c=createCheats(env);
assert.equal(await c.teleportZone('sailing'),false,'failed ocean GLB load cannot be reported as teleport success');
assert.equal(await c.teleportPlace('inn'),false,'blocked building travel cannot be reported as success');
assert.equal(await c.spawnEnemy('wolf'),false,'failed monster spawn cannot be reported as success');
assert.equal(await c.healParty(),false,'failed heal cannot be reported as success');
assert.equal(c.skipQuest(),false,'unimplemented 3D quest skip must not be claimed successful');
ok=true;
assert.equal(await c.teleportZone('sailing'),true,'successful ship load allows travel');
assert.equal(await c.teleportPlace('inn'),true,'successful building path allows travel');
assert.equal(await c.spawnEnemy('wolf'),true,'confirmed spawned monster reports success');
assert.equal(await c.healParty(),true,'actual heal reports success');
c.setGod(true);c.setFly(true);c.setNoCooldown(true);c.setUnlimited(true);
c.reset();
assert.equal(c.flags.god,false);
assert.equal(c.flags.fly,false);
assert.equal(c.flags.noCooldown,false);
assert.equal(c.flags.unlimited,false);
assert.ok(storage.getItem('varnethryl-save')!==null||c.used,'Owner effects track cheat use');
console.log('Owner asynchronous buttons: 3D travel, healing, spawning, quest availability and manual reset PASS');
