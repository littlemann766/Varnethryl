import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {preferSerpentClips,serpentBodyChain,serpentAnimatedBody,serpentHeading} from '../www/proto3d/serpent-locomotion.js';
const clip=n=>({name:n,tracks:[]});
const idle=clip('idle'),walk=clip('walk'),run=clip('run'),slow=clip('slither'),fast=clip('slither_fast');
const snake={idle,walk,run,slither:slow,slither_fast:fast,attack:clip('strike')};
assert.equal(preferSerpentClips('n:vaelthryx_straight_rig',snake),snake);
assert.equal(snake.walk,slow,'Balthrix must animate his native full-body slither instead of walking');
assert.equal(snake.run,fast,'running must animate his faster authored full-body slither');
assert.equal(snake.idle,idle,'idle stays intact for stopping');
const fallback={walk,run,slither:slow};
preferSerpentClips('n:vaelthryx_new6',fallback);
assert.equal(fallback.walk,slow);assert.equal(fallback.run,slow);
const biped={walk,run,slither:slow};
preferSerpentClips('n:owner',biped);
assert.equal(biped.walk,walk);assert.equal(biped.run,run);
const makeBone=(name,parent=null)=>{
  const bone={name,isBone:true,parent,children:[]};
  if(parent)parent.children.push(bone);
  return bone;
};
const root=makeBone('Spine'),chain=[root];
for(let i=0;i<20;i++)chain.push(makeBone(i<10?'Spine'+i:'Tail'+i,chain.at(-1)));
const horn=makeBone('Horn',chain[2]);
const rig={traverse(f){function visit(x){f(x);for(const k of x.children)visit(k)}visit(root)}};
assert.equal(serpentBodyChain(rig).length,21);
assert(!serpentBodyChain(rig).includes(horn),'horns cannot be mistaken for spine');
const tracks=chain.map(b=>({name:b.name+'.quaternion'}));
const report=serpentAnimatedBody([{name:'slither',tracks},{name:'idle',tracks:[]}]);
assert.equal(report[0].bones,21,'authored clip must target multiple connected bones');
assert.equal(report[1].bones,0,'no fake rig movement claims');
const main=readFileSync(new URL('../www/proto3d/main.js',import.meta.url),'utf8');
const fight=readFileSync(new URL('../www/proto3d/fight.js',import.meta.url),'utf8');
const preview=readFileSync(new URL('../www/proto3d/roster-preview.js',import.meta.url),'utf8');
assert(main.includes("import { preferSerpentClips, serpentBodyChain, serpentAnimatedBody } from './serpent-locomotion.js'"));
assert(main.includes('preferSerpentClips(id,act);'),'runtime must choose native slither clips');
assert(main.includes('root.userData.rigAudit.authoredSlither='),'rig audit must expose actual animation coverage');
assert(main.includes("'n:vaelthryx_straight_rig': { walk: 0.30, run: 0.80 }"),
  'native locomotion profile must reflect the heavily upscaled serpent, not stale 10+ m/s native speed');
assert(!main.includes('createSerpentWave(m)'),'no additive twist may be layered on native body animation');
assert(!main.includes('u.serpentWave(animDt'),'companions must not re-aim serpent bones after the mixer');
assert(!fight.includes('u.serpentWave(dt,mv'),'boss must not re-aim serpent bones after the mixer');
assert(fight.includes("e.key==='vaelthryx'") && fight.includes('serpentHeading(r.rotation.y,heading,dt)'),
  'Balthrix body heading must use bounded serpentine turning');
for(const fps of [24,30,60,120]){
  let a=0;const dt=1/fps;
  for(let i=0;i<fps;i++){
    const b=serpentHeading(a,Math.PI,dt);
    assert(Math.abs(Math.atan2(Math.sin(b-a),Math.cos(b-a)))<=1.15*dt+1e-9,
      'giant serpent must not rotate faster than max angular speed');
    a=b;
  }
  assert(Math.abs(a+1.15)<.035 || Math.abs(a-1.15)<.035,
    'one second turns at roughly constant angular speed, independent of FPS');
}
{
  const before=Math.PI-.015,after=-Math.PI+.015;
  const next=serpentHeading(before,after,.05);
  const delta=Math.atan2(Math.sin(next-before),Math.cos(next-before));
  assert(delta>0&&delta<.04,'wraparound must take short heading path instead of full-body spin');
}
assert.equal(serpentHeading(NaN,0,.05),0,'invalid starting yaw resets safely');
assert.equal(serpentHeading(1,NaN,.05),1,'invalid target does not poison the boss transform');
assert.equal(serpentHeading(1,2,NaN),1,'bad frame delta leaves the model stable');
assert(preview.includes('actions.slither || actions.walk || actions.idle'),
  '3D preview must show authored slither, not fake body twisting over idle');
assert(main.includes("group.key === 'ssylthar'"),'Sslythar stays hidden');
console.log('PASS: full-body authored Balthrix gait, native speeds and no destructive post-mixer bone twisting.');
