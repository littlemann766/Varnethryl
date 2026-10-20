// Checks for the doubled Varnethryl map: run with node tools/check_town_mountains.mjs
// No browser dependencies. Terrain formula is evaluated from its source, so the tests cannot drift from production.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import {spawnSync} from 'node:child_process';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const building=read('www/proto3d/buildings.js'),land=read('www/proto3d/townlands.js'),game=read('www/proto3d/main.js');
assert.match(building,/WORLD_B\s*=\s*200\s*\*\s*PK/, 'map is 2x the previous 280 half extent');
assert.match(building,/run\(-WORLD,\s*-WORLD,\s*-10\.4,\s*-WORLD\)/,'north wall opens to mountain cave');
assert.match(building,/d.id === 'gatehouse' \? CITY_WALL_B - 1.2/,'gatehouse sits on new closer walls');
assert.match(game,/const WORLD = WORLD_B/,'movement clamps to expanded town');
assert.match(game,/TOWN_LANDS\.heightAt\(x,z\)/,'players actually walk on terrain');
assert.match(land,/acc\(shadow\?'cast':'plain',x,z\)\.add\(v\.geo,x,townElevation\(x,z,world\),z/,'scenery sits on the same terrain');
assert.match(land,/const terrain=buildWalkableTerrain\(world\);group\.add\(terrain\)/,'physical terrain mesh in scene');
const a=land.indexOf('const CHUNK ='),b=land.indexOf('// ~41K triangles');
assert(a>=0&&b>a);
const code=land.slice(a,b).replaceAll('export const ','const ').replaceAll('export function ','function ');
const heightAt=runInNewContext(code+'\n townElevation;', {Math});
const H=(x,z)=>heightAt(x,z,560);
assert.equal(H(0,0),0,'city center flat');
assert.equal(H(-6,38),0,'Wilds portal flat');
for(const p of [[0,560],[0,-560],[-560,0],[560,0],[-552,402],[497,548]]){
 assert(Math.abs(H(...p))<.00001,'surrounding walls/gates level '+p.join(','));
}
for(const p of [[-211,111],[-209,-108],[207,124]])assert.equal(H(...p),0,'established fields remain flat');
assert.equal(H(0,450),0,'cardinal road remains level');
let hi=-1e9,lo=1e9,hills=0,valleys=0;
for(let x=-540;x<=540;x+=12)for(let z=-540;z<=540;z+=12){
 const y=H(x,z);assert(Number.isFinite(y),'nonfinite elevation');
 assert(y<=70+.00001&&y>=-20-.00001,'bounded hills, ice summit, volcanic crater and sea floor');
 hi=Math.max(hi,y);lo=Math.min(lo,y);
 if(y>12)hills++;if(y<-.75)valleys++;
}
assert(hi>30,'walkable mountains missing: maximum '+hi);
assert(lo<-1,'walkable valleys missing: minimum '+lo);
assert(hills>200&&valleys>2,'terrain lacks enough mountains/valleys');
for(const p of ['www/proto3d/main.js','www/proto3d/buildings.js','www/proto3d/townlands.js']){
 const test=spawnSync(process.execPath,['--check',p],{encoding:'utf8'});
 assert.equal(test.status,0,p+' syntax error: '+test.stderr);
}
console.log('PASS: 1120×1120 wilderness, 420×420 fortified city, summit cave, lava crater, swimmable port and hill-following companions.');
console.log('Elevation samples (world units): mountain '+hi.toFixed(1)+', valley '+lo.toFixed(1)+'.');
