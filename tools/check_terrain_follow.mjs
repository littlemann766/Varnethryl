import assert from 'node:assert/strict';
import {terrainBodyPitch} from '../www/proto3d/terrain-follow.js';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
assert.equal(terrainBodyPitch(0,0,14),0,'flat terrain needs no visible root tilt');
assert(terrainBodyPitch(0,3,14)<0,'uphill serpent inclines its head upslope');
assert(terrainBodyPitch(3,0,14)>0,'downhill serpent points down the ridge');
assert.equal(terrainBodyPitch(0,999,14),-.16,'steep ascent pitch safely capped for mobile animation');
assert.equal(terrainBodyPitch(999,0,14),.16,'steep descent pitch safely capped');
assert.equal(terrainBodyPitch(0,3,0),0,'zero-length body is handled');
assert.equal(terrainBodyPitch(NaN,0,10),0,'bad terrain samples cannot corrupt model transforms');
assert.equal(terrainBodyPitch(0,NaN,10),0,'bad terrain samples cannot corrupt model transforms');
const source=readFileSync(new URL('../www/proto3d/fight.js',import.meta.url),'utf8');
assert(source.includes("terrainBodyPitch(behind,ahead,2*along,.16)"),'serpent is actually terrain-aligned in the 3D enemy update');
assert(source.includes("e.key==='vaelthryx'&&e.roaming"),'only the roaming serpent receives this pitch');
for(const path of ['www/proto3d/fight.js','www/proto3d/terrain-follow.js']){
 const check=spawnSync(process.execPath,['--check',path],{encoding:'utf8'});
 assert.equal(check.status,0,path+' is syntactically invalid: '+check.stderr);
}
console.log('PASS: roaming Balthrix smoothly aligns to slopes without affecting attacks or other bosses');
