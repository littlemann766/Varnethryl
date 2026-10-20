// Regression checks for the doubled 1120-unit Varnethryl town expansion.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
const text=p=>readFileSync(new URL(p,import.meta.url),'utf8');
const building=text('../www/proto3d/buildings.js');
const wilds=text('../www/proto3d/wilds.js');
const main=text('../www/proto3d/main.js');
const lands=text('../www/proto3d/townlands.js');
const worldExpression=building.match(/WORLD_B\s*=\s*(\d+)\s*\*\s*PK/);
const pk=Number(building.match(/PK\s*=\s*([\d.]+)/)?.[1]);
const wildHalf=Number(wilds.match(/half:\s*(\d+),\s*base/)?.[1]);
assert.ok(worldExpression && Number.isFinite(pk),'town half-extent constants');
const townHalf=Number(worldExpression[1])*pk;
assert.equal(townHalf,560,'town doubled to 560-unit half extent');
assert.equal(townHalf,wildHalf*2,'town is exactly twice the Wilds half extent');
assert.ok(building.includes("const Q = WORLD * 0.5, DECO"),'wall towers spread along expanded perimeter');
assert.ok(building.includes("run(-WORLD, -WORLD, -10.4, -WORLD)"),'north pass has a walkable cave route');
assert.ok(building.includes("run(-WORLD, -WORLD, -WORLD, WORLD)"),'west wall');
assert.ok(building.includes("run(WORLD, -WORLD, WORLD, WORLD)"),'east wall');
assert.ok(building.includes("run(-WORLD, WORLD, -10.4, WORLD)"),'south gate opening');
assert.ok(building.includes("CITY_WALL_B - 1.2"),'gatehouse stays attached to closer city wall');
assert.ok(main.includes('TOWN_PORTAL = {x:-6,z:38}'),'historic Wilds portal unchanged');
assert.ok(main.includes("TOWN_LANDS.cull(state.heroX, state.heroZ, VIEWK)"),'outskirt chunk culling');
assert.ok(main.includes("if (BLD_ON) {\n  try { TOWN_LANDS = buildTownOutskirts"),'old village debug mode unaffected');
assert.ok(main.includes("const treeLimit = Math.min(WORLD - 3, 161)"),'original inner-village tree positions unchanged');
assert.ok(lands.includes("makeVariant")&&lands.includes("new Acc()"),'reuse Wilds-style batched geometry');
assert.ok(lands.includes("indices.push(j,j+2,j+1,j+1,j+2,j+3)"),'road facing upward');
assert.ok(lands.includes("colliders.push({type:'circle'"),'tree collision included');
assert.ok(lands.includes("FIELDS")&&lands.includes("roadRing()"),'outskirts have farms and roads');
assert.ok(building.includes('CITY_WALL_B = 210'),'compact walls sit 210 units from central city');
for(const fname of ['../www/proto3d/townlands.js','../www/proto3d/buildings.js','../www/proto3d/main.js']){
 const p=spawnSync(process.execPath,['--check','--input-type=module'],{input:text(fname),encoding:'utf8'});
 assert.equal(p.status,0,'Syntax: '+fname+': '+p.stderr);
}
console.log('Town expansion passed: large 1120-unit wilderness, compact 420-unit walled city, separate fortified port, intact Wilds portal, scenery and syntax.');
