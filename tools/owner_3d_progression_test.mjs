/* Owner progression regression: old save and live 3D XP must both change.
 * The Owner menu invokes these hooks; CoOwner cannot call this client-gated API.
 */
import assert from 'node:assert/strict';
import { createCheats, createFlags } from '../www/proto3d/cheats.js';
import { createExperience, EXP_STORE_KEY } from '../www/proto3d/combat/experience.js';
import { SAVE_KEY, loadState } from '../www/core/save.js';
const db=new Map();
const storage={getItem:k=>db.get(k)??null,setItem:(k,v)=>db.set(k,v),removeItem:k=>db.delete(k)};
const progress=createExperience(storage);
const ids=['n:owner','selene','aldric'];
const hooks={
 addCombatXp:amount=>progress.award(ids[0],amount).gained===amount,
 setCombatLevel:(level,scope)=>{
   for(const id of (scope==='party'?ids:[ids[0]])) progress.setLevel(id,level);
   return true;
 }
};
const c=createCheats({storage,flags:createFlags(),hooks});
assert.equal(c.addXp(0),false,'zero XP rejected');
assert.equal(await c.addXp(50000),true,'Owner +50k XP succeeds');
assert.ok(progress.get(ids[0]).total===50000,'real 3D combat XP changed');
assert.equal(loadState(storage).accountLevel>1||Object.values(loadState(storage).heroXp).some(x=>x>0),true,'original profile XP retained');
assert.equal(await c.setLevel(12,'active'),true,'active hero level cheat succeeds');
assert.equal(progress.get(ids[0]).level,12,'3D hero level is applied');
assert.equal(progress.get('selene').level,40,'companion level unchanged when set active');
assert.equal(createExperience(storage).get(ids[0]).level,12,'3D level 12 persists across app reload');
assert.equal(await c.setLevel(60,'party'),true,'party level cheat succeeds');
assert.ok(ids.every(id=>progress.get(id).level===60),'3D hero and companions are both leveled');
assert.ok(ids.every(id=>createExperience(storage).get(id).level===60),'levels persist in 3D progression storage');
assert.ok(!!db.get(EXP_STORE_KEY),'3D progression persisted separately');
assert.equal(!!JSON.parse(db.get(SAVE_KEY)).cheated,true,'cheated flag remains sticky');
console.log('PASS Owner profile and 3D combat progression synchronized, persistent, and isolated');
