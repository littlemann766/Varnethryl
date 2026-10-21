import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {bossCameraFocus} from '../www/proto3d/boss-camera-focus.js';
const enemy={x:0,z:-44,def:{boss:true},state:'chase',heightAbove:26};
const out=bossCameraFocus(0,0,enemy,true,true);
assert(out,'explicit lock-on to real boss produces framing');
assert(Math.abs(out.x)<1e-8 && out.z<0,'framing shifts toward the actual boss');
assert(out.rise>0&&out.rise<=7.5,'portrait raises view without tilting endlessly');
assert(Math.hypot(out.x,out.z)<=14,'portrait maintains the playable hero onscreen');
assert.equal(bossCameraFocus(0,0,enemy,false,true),null,'no auto-follow unless player locks the boss');
assert.equal(bossCameraFocus(0,0,{...enemy,def:{boss:false}},true,true),null,'normal monsters preserve the chosen camera');
assert.equal(bossCameraFocus(0,0,{...enemy,state:'defeated'},true,true),null,'defeated boss cannot capture camera');
assert.equal(bossCameraFocus(0,0,{...enemy,z:-130},true,true),null,'remote boss cannot capture camera');
assert.equal(bossCameraFocus(0,0,{...enemy,z:0},true,true),null,'overlapping model cannot cause divide-by-zero');
assert.equal(bossCameraFocus(0,0,{...enemy,x:NaN},true,true),null,'invalid GLB positions are ignored');
assert(bossCameraFocus(0,0,enemy,true,false).rise<=6,'landscape has smaller framing adjustment');
const main=readFileSync(new URL('../www/proto3d/main.js',import.meta.url),'utf8');
const rig=readFileSync(new URL('../www/proto3d/camrig.js',import.meta.url),'utf8');
assert(main.includes("ci.bossFocus = camRig.fp ? null : bossCameraFocus("),'first person never changes');
assert(main.includes("FIGHT.cc?.tgt?.locked"),'only user lock-on drives the focus');
assert(rig.includes("if(c.bossFocus){"),'camera rig consumes the focus');
assert(rig.includes("r.look = (dx, dy) =>"),'free-orbit look control is still available');
assert(rig.includes("r.zoomBy = (factor) =>"),'pinch/wheel zoom stays available');
for(const p of ['www/proto3d/boss-camera-focus.js','www/proto3d/main.js','www/proto3d/camrig.js']){
 const run=spawnSync(process.execPath,['--check',p],{encoding:'utf8'});
 assert.equal(run.status,0,p+': '+run.stderr);
}
console.log('PASS lock-on giant framing, voluntary-only, first person, free orbit, and zoom protection');
