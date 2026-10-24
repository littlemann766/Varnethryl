/* Owner's 24 October 2026 map revision: regression gate for the brown roads,
 * timed blue Balthrix route and private Owner/CoOwner test boss tools.
 * No Android SDK or 3D renderer needed.
 */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {
 BALTHRIX_ROUTE,BALTHRIX_ROUTE_LENGTH,BALTHRIX_CYCLE_MS,BALTHRIX_ACTIVE_MS,
 balthrixPosition,nearestBalthrixPath,balthrixCorridorDistance,balthrixBermHeight,
 balthrixSpawnWindow,fallenTreeSites,PORT_CENTER,CITY_HALF
} from '../www/proto3d/bossregions.js';
import {TOWN_MAP_ROADS,townElevation} from '../www/proto3d/townlands.js';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
assert.ok(BALTHRIX_ROUTE.length>=35,'hand-drawn perimeter has detailed waypoints');
assert.ok(BALTHRIX_ROUTE_LENGTH>3000&&BALTHRIX_ROUTE_LENGTH<5000,'route length is sensible');
assert.ok(nearestBalthrixPath(PORT_CENTER.x,PORT_CENTER.z).distance>165,
 'Balthrix cannot enter harbor or docks on the natural spline');
for(let i=0;i<500;i++){
 const p=balthrixPosition(i*BALTHRIX_ROUTE_LENGTH/(500*14));
 assert.ok(Math.max(Math.abs(p.x),Math.abs(p.z))<=550,'serpent stays inside the world');
 assert.ok(Math.abs(p.x)>CITY_HALF+10||Math.abs(p.z)>CITY_HALF+10,'no city wall intrusion');
 assert.ok(Math.hypot(p.x-PORT_CENTER.x,p.z-PORT_CENTER.z)>165,'no harbor intrusion at any point');
 assert.ok(Number.isFinite(p.yaw),'valid serpent heading');
}
assert.equal(BALTHRIX_CYCLE_MS,900000,'fifteen-minute world-clock spawn interval');
assert.equal(BALTHRIX_ACTIVE_MS,360000,'six-minute encounter window');
assert.ok(balthrixSpawnWindow(900000).active,'window starts active');
assert.ok(balthrixSpawnWindow(900000+359999).active,'active window end is inclusive');
assert.ok(!balthrixSpawnWindow(900000+360000).active,'boss disappears at window end');
assert.equal(balthrixSpawnWindow(900000+900000).slot,2,'next window has new ID');
const middle=balthrixPosition(BALTHRIX_ROUTE_LENGTH/28);
assert.ok(balthrixCorridorDistance(middle.x,middle.z)<3,'terrain grid aligns with patrol spline');
const shoulderX=middle.x+13*Math.cos(middle.yaw),shoulderZ=middle.z-13*Math.sin(middle.yaw);
assert.ok(balthrixBermHeight(shoulderX,shoulderZ)>0,'raised edge is represented by physical height');
const sites=fallenTreeSites();
assert.ok(sites.length>=8&&sites.length<=22,'bounded tree destruction on Android');
for(const s of sites)assert.ok(Math.hypot(s.x-PORT_CENTER.x,s.z-PORT_CENTER.z)>107);
assert.ok(TOWN_MAP_ROADS.length>=8,'new brown road network surfaced and on minimap');
assert.ok(TOWN_MAP_ROADS.some(p=>p.id==='frost-spiral'&&p.points.length>12),'spiraling road to frost cave');
for(const road of TOWN_MAP_ROADS){
 assert.ok(road.points.length>=2,'route has endpoints');
 for(const [x,z] of road.points)assert.ok(Number.isFinite(x)&&Number.isFinite(z));
}
assert.ok(Number.isFinite(townElevation(-425,392)),'port terrain accessible');
const terrain=read('www/proto3d/townlands.js');
assert.match(terrain,/TOWN_MAP_ROADS\.slice\(3\)\.map/,'additional roads built as geometry');
assert.match(terrain,/balthrixCorridorDistance\(x,z\)>25\+pad/,'scenery cannot grow on trail');
assert.match(terrain,/return terrain\+balthrixBermHeight\(x,z\)/,'terrain physics and berm visually align');
assert.match(terrain,/nearPort-122/,'port mountain flattening active');
const corridor=read('www/proto3d/balthrix-corridor.js');
assert.match(corridor,/BALTHRIX_RAISED_PERIMETER_TRAIL/,'physical drawn trail mesh');
assert.match(corridor,/BALTHRIX_SHOVED_ASIDE_ROCKS/,'rock debris moved to sides');
assert.match(corridor,/new THREE\.InstancedMesh/,'mobile-friendly debris');
assert.match(read('www/proto3d/balthrix-trail.js'),/buildBalthrixCorridor\(parent,heightAt,colliders\)/);
const fight=read('www/proto3d/fight.js');
assert.doesNotMatch(fight,/route\.distance<112/,'no proximity-triggered serpent');
assert.match(fight,/const window=balthrixSpawnWindow\(\)/,'timed spawn checked by world clock');
assert.match(fight,/window\.slot!==roamerSpawnedSlot/,'once per 15-minute slot');
assert.match(fight,/!window\.active&&!roamer\.manuallySummoned/,'natural event ends on schedule');
assert.match(fight,/if\(route\.distance>11\)/,'combat leash prevents port trespassing');
assert.match(fight,/manuallySummoned:true/,'authorized boss can bypass timer');
const owner=read('www/proto3d/cheatpanel.js');
assert.match(owner,/id:'ownerBossPick'/,'all available bosses in Owner panel');
const co=read('www/proto3d/coowner-panel.js');
assert.match(co,/summonBoss\(bossChoice\.value\)/,'CoOwner has explicit summon control');
const server=read('multiplayer/server.mjs');
assert.match(server,/if\(m\.type==='coowner-boss'\)/);
assert.match(server,/if\(!socket\.coOwnerAuthorized\)/,'no unauthenticated summon approval');
assert.match(server,/COOWNER_BOSSES\.has\(m\.boss\)/,'server boss whitelist');
assert.match(server,/socket\.lastBossSummonAt/,'summon requests throttled');
assert.match(read('www/proto3d/multiplayer-client.js'),/m\.type==='coowner-boss-approved'/);
assert.match(read('www/proto3d/main.js'),/onRankBossSpawn:async boss=>/);
console.log('PASS: Owner map roads, raised Balthrix trail, 15-minute spawns, Owner and verified CoOwner boss tools.');
