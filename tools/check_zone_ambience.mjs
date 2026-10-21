/* Zone atmosphere and source integration regression.
 * Smoke tests cannot prove visual darkness; these protect numeric bounds
 * and actual wiring so phone playtests see the intended conditions. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {zoneAtmosphere,DAYLIGHT,FROST_CAVE,VOLCANO} from '../www/proto3d/zone-ambience.js';
const P=(zone,x,z,s=1)=>zoneAtmosphere(zone,x,z,{x:405,z:-402},s);
const day=P('town',0,0),frost=P('frost',0,0),ash=P('town',405,-402),wild=P('wilds',405,-402);
assert.equal(day.sun,DAYLIGHT.sun);
assert.equal(frost.sun,FROST_CAVE.sun);
assert(frost.sun<day.sun*.15,'Frost Cave sunlight genuinely dimmed');
assert(frost.fill<day.fill*.5,'global hemisphere fill must be dimmed inside cave');
assert(frost.fogFar<day.fogFar,'ice cave has a short atmospheric sightline');
assert.equal(frost.darkSky,true,'ice cave must not expose daylight blue sky');
assert.equal(day.darkSky,false,'town restores its original daytime sky');
assert.equal(ash.sun,VOLCANO.sun,'volcano should show an actual warm visual shift');
assert(ash.fogFar<day.fogFar,'volcano needs hazy visibility');
assert.equal(wild.sun,day.sun,'Wilds never accidentally get volcano lighting');
assert.equal(P('frost',0,0,1.7).fogFar,FROST_CAVE.fogFar*1.7,'larger characters retain scaled view');
for(const obj of [day,frost,ash,wild])for(const key of ['fogNear','fogFar','sun','fill']){
 assert(Number.isFinite(obj[key])&&obj[key]>=0);
}
const main=readFileSync(new URL('../www/proto3d/main.js',import.meta.url),'utf8');
const cave=readFileSync(new URL('../www/proto3d/frost-cave.js',import.meta.url),'utf8');
const realm=readFileSync(new URL('../www/proto3d/frostreach.js',import.meta.url),'utf8');
assert(main.includes('updateZoneAmbience(dt);'),'per-frame atmosphere is wired into the main game loop');
assert(main.includes('updateZoneAmbience(.1,true);'),'portal transitions immediately initialize the right lighting');
assert(main.includes('scene.background=goal.darkSky?caveSky:outdoorSky'),'exiting cave restores the original sky');
assert(cave.includes('enclosing-ice-cave-vault')&&realm.includes('buildFrostCave('),'real ice cave mesh remains present');
assert(main.includes("group.key === 'ssylthar'"),'Sslythar stays out of public character roster');
for(const path of ['www/proto3d/main.js','www/proto3d/zone-ambience.js']){
 const test=spawnSync(process.execPath,['--check',path],{encoding:'utf8'});
 assert.equal(test.status,0,path+': '+test.stderr);
}
console.log('PASS cave darkness, original sky restoration, volcanic haze, giant fog scaling, correct transitions');
