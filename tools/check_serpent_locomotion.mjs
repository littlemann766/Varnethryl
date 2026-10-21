import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {preferSerpentClips,serpentBodyChain,createSerpentWave} from '../www/proto3d/serpent-locomotion.js';
const clip=n=>({name:n});
const idle=clip('idle'),walk=clip('walk'),run=clip('run'),slow=clip('slither'),fast=clip('slither_fast');
const snake={idle,walk,run,slither:slow,slither_fast:fast,attack:clip('strike')};
assert.equal(preferSerpentClips('n:vaelthryx_straight_rig',snake),snake);
assert.equal(snake.walk,slow,'Balthrix must slither instead of walking');
assert.equal(snake.run,fast,'running uses fast slither, not biped running');
assert.equal(snake.idle,idle,'serpent idle stays intact');
assert.equal(snake.attack.name,'strike','boss attack clip stays intact');
const fallback={walk,run,slither:slow};
preferSerpentClips('n:vaelthryx_new6',fallback);
assert.equal(fallback.walk,slow);
assert.equal(fallback.run,slow,'fast slither optional');
const biped={walk,run,slither:slow};
preferSerpentClips('n:owner',biped);
assert.equal(biped.walk,walk,'normal player walk animations are never changed');
assert.equal(biped.run,run,'normal player run animations are never changed');
const main=readFileSync(new URL('../www/proto3d/main.js',import.meta.url),'utf8');
assert(main.includes("import { preferSerpentClips } from './serpent-locomotion.js'"));
assert(main.includes('preferSerpentClips(id,act);'),'the clip preference is actually used');
assert(main.includes("group.key === 'ssylthar'"),'Sslythar remains hidden');

// Connected-spine wave, not a wobble on decorative parts or the creature root.
// A synthetic serpent with 12 contiguous body bones and a side horn proves
// the wave moves across multiple bones and responds to actual forward speed.
function makeBone(name,parent=null){
  const bone={name,isBone:true,parent,children:[],
    quaternion:{x:0,y:0,z:0,w:1,set(x,y,z,w){this.x=x;this.y=y;this.z=z;this.w=w;}}};
  if(parent)parent.children.push(bone);return bone;
}
const skull=makeBone('BodyRoot'),chain=[skull];
for(let i=0;i<12;i++)chain.push(makeBone(i<4?'Spine'+i:'Tail'+(i-4),chain.at(-1)));
const horn=makeBone('Horn',chain[2]);
const rig={traverse(f){function visit(b){f(b);b.children.forEach(visit);}visit(skull);}};
const chosen=serpentBodyChain(rig);
assert.equal(chosen.length,13,'full connected spine and tail are selected');
assert(!chosen.includes(horn),'decorative horns must never steer the body');
const wave=createSerpentWave(rig);
assert.equal(typeof wave,'function','a connected rig supports real full-body slither');
for(let i=0;i<30;i++)wave(1/60,8,.35,false);
const rotated=chain.filter(b=>Math.abs(b.quaternion.y)>.001);
assert(rotated.length>=10,'body wave must bend many consecutive joints, not just mesh sides');
assert(Math.abs(chain[3].quaternion.y-chain[11].quaternion.y)>.005,
  'head, midsection and tail must not rotate together as a single rigid statue');
for(const b of chain)assert(Math.abs(Math.hypot(b.quaternion.x,b.quaternion.y,b.quaternion.z,b.quaternion.w)-1)<.005,
  'body quaternions must stay normalized');
const stillRig={traverse(f){f(skull);}};
assert.equal(createSerpentWave(stillRig),null,'unrigged creatures cannot claim to slither');
assert(sourceIsBounded(wave),'slither handles a NaN frame safely');
function sourceIsBounded(gait){gait(NaN,NaN,NaN,true);return chain.every(b=>[b.quaternion.x,b.quaternion.y,b.quaternion.z,b.quaternion.w].every(Number.isFinite));}
const serpentSource=readFileSync(new URL('../www/proto3d/main.js',import.meta.url),'utf8');
const fightSource=readFileSync(new URL('../www/proto3d/fight.js',import.meta.url),'utf8');
const previewSource=readFileSync(new URL('../www/proto3d/roster-preview.js',import.meta.url),'utf8');
assert(serpentSource.includes('createSerpentWave(m)'),'the live boss rig needs its whole-body wave enabled');
assert(fightSource.includes('u.serpentWave(dt,mv,dyaw/Math.max(.016,dt),'),'the roaming boss must trail turns through its tail');
assert(previewSource.includes('actor.model.userData.serpentWave(dt,7.5,0,false)'),
  'the character preview should demonstrate the same moving serpent body');

console.log('PASS: dedicated slow/fast serpent clips, no changes to other heroes or hidden dragon');
