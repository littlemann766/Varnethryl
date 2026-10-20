// Non-destructive regression checks for Varnethryl's 10x/50x Balthrix variants.
// Run: node tools/check_balthrix_scale.mjs
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { HERO_M, MAX_HEIGHT_M, profileFor, loadScale, fitsDoor } from '../www/proto3d/charscale.js';
const b10='n:vaelthryx_straight_rig',b50='n:vaelthryx_straight_rig_50';
const near=(a,b)=>Math.abs(a-b)<0.00001;
assert.equal(HERO_M,1.905);
assert.ok(MAX_HEIGHT_M>=50*HERO_M);
assert.ok(near(profileFor(b10).height,19.05));
assert.ok(near(profileFor(b50).height,95.25));
for(const native of [0.18,0.65]){
  assert.ok(near(native*loadScale(b10,native),19.05),'10x measured-height scaling');
  assert.ok(near(native*loadScale(b50,native),95.25),'50x measured-height scaling');
}
assert.equal(fitsDoor(b50,3,2),false);
const main=readFileSync(new URL('../www/proto3d/main.js',import.meta.url),'utf8');
assert.ok(main.indexOf("EXTRA.push(['n:vaelthryx_straight_rig_50'")>main.indexOf('for (const n of SMOOTH_NAMES)'),'50x variant must follow all existing save slots');
assert.ok(main.includes(".replace(/_straight_rig(?:_50)?$/, '')"),'50x and 10x share a dropdown');
assert.match(main,/loadScale\(id,\s*hgt\)/,'height comes from the actual GLB');
const boss=readFileSync(new URL('../www/proto3d/combat/data.js',import.meta.url),'utf8');
assert.ok(boss.includes("'n:vaelthryx_straight_rig'"),'existing 10x boss model unchanged');
assert.ok(boss.includes("Balthrix the Crystal Sovereign"),'user-facing boss name');
const asset=new URL('../www/proto3d/models-new/vaelthryx_straight_rig.glb',import.meta.url);
assert.ok(existsSync(asset),'existing serpent model present');
const viewer=readFileSync(new URL('../www/balthrix-scale.html',import.meta.url),'utf8');
assert.ok(viewer.includes("vaelthryx_straight_rig.glb"));
assert.ok(viewer.includes("bounds.max.y-bounds.min.y"),'viewer fits actual mesh height');
function syntax(code,label,module=false){
 const args=['--check',...(module?['--input-type=module']:[])];
 const p=spawnSync(process.execPath,args,{input:code,encoding:'utf8'});
 assert.equal(p.status,0,label+' syntax error:\n'+p.stderr);
}
for(const path of ['../www/proto3d/charscale.js','../www/proto3d/main.js','../www/proto3d/combat/data.js']){
 syntax(readFileSync(new URL(path,import.meta.url),'utf8'),path,true);
}
const match=viewer.match(/<script type="module">([\s\S]*?)<\/script>/);
assert.ok(match,'viewer module script present');
syntax(match[1],'viewer module',true);
console.log('Balthrix checks passed: exact 10x/50x, shared rig, stable saved indices, JS/viewer syntax.');
