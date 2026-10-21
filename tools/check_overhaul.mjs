/* Safety tests for the staged 3D overhaul. Run with node tools/check_overhaul.mjs.
 * Tests are read-only; do not require an APK, credentials or a WebGL display. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {fallenTreeSites,balthrixPosition,isCitySafe,onLava,PORT_CENTER,FROST_SUMMIT,TITAN_CENTER} from '../www/proto3d/bossregions.js';
const source=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const hud=source('www/proto3d/combat/hud.js');
const main=source('www/proto3d/main.js');
const fight=source('www/proto3d/fight.js');
const terrain=source('www/proto3d/townlands.js');
const frost=source('www/proto3d/frostreach.js');
const cave=source('www/proto3d/frost-cave.js');
const ship=source('www/proto3d/port-ships.js');
const trail=source('www/proto3d/balthrix-trail.js');
const camera=source('www/proto3d/camrig.js');
const building=source('www/proto3d/buildings.js');

// Critical combat failure: querySelector returns ONE button, not an array.
// Both slots and labels must use querySelectorAll's array wrapper.
assert(hud.includes("$$('.sl').forEach"),'skill labels must select ALL 5 buttons');
assert(hud.includes("$$('.sl').map"),'skill array must select ALL 5 buttons');
assert(!hud.includes("this.slots = $('.sl').map"),'fatal HUD initialization regression');
assert(main.includes("document.getElementById('vnEnter')?.addEventListener('click'"),'ordinary Enter activates combat');
assert(main.includes("fightToggle(true).then(f=>f.startAuto())"),'all heroes receive combat HUD on entry');
assert(main.includes("!FIGHT.on||!FIGHT.auto"),'wilderness promotes training mode into auto encounters');
assert(camera.includes('const orbitAngle ='),'third-person camera uses real spherical pitch orbit');
assert(main.includes('camRig.look(0, -(e.clientY - t.ly) * 0.005'),'vertical touch orbit is actually connected');
assert(fight.includes("u.serpentWave(dt,mv)"),'Balthrix enemy rig updates a spine/body wave');
assert(fight.includes('14*Math.max(0,dt)'),'Balthrix patrol advances per frame instead of jerky time chunks');
assert(fight.includes('if (on) { if (isAuto === true) auto = true; return; }'),'existing active combat must be promotable');
assert(main.includes("group.key === 'ssylthar'"),'unreleased Sslythar remains hidden');
assert(main.includes('const hiddenSerpentSlot ='),'unreleased Sslythar saved/URL selection is guarded');
assert.match(main, /^const SPEEDS = \{/m, 'actual runtime SPEEDS declaration is required: comments must not swallow it');
assert(main.includes('savedPlan.hero = activeSlot(savedPlan.hero)'),'stored Sslythar avatar is not resurrected in live gameplay');
assert(main.includes('if (!playableSlot(i)) return;'),'Sslythar cannot be selected or added as a companion');
assert(main.includes("EXTRA.push(['n:vaelthryx_straight_rig_50'"),'stable existing boss slot retained');

// Make sure the serpent's aftermath avoids all mission-critical safe areas.
const sites=fallenTreeSites();
assert(sites.length>=8&&sites.length<=22,'reasonable phone-safe number of fallen trees: '+sites.length);
for(const s of sites){
 assert(Number.isFinite(s.x)&&Number.isFinite(s.z)&&Number.isFinite(s.angle),'finite wreckage positions');
 assert(!isCitySafe(s.x,s.z,20),'damage cannot obstruct safe village');
 assert(!onLava(s.x,s.z),'wood cannot obstruct lava pools');
 assert(Math.hypot(s.x-PORT_CENTER.x,s.z-PORT_CENTER.z)>=107,'harbor approach stays clear');
 assert(Math.hypot(s.x-FROST_SUMMIT.x,s.z-FROST_SUMMIT.z)>=165,'summit route stays clear');
 assert(Math.hypot(s.x-TITAN_CENTER.x,s.z-TITAN_CENTER.z)>=100,'Titan arena stays clear');
 assert(s.length>=9&&s.length<=18,'logs are believable size');
}
assert(trail.includes("InstancedMesh"),'wreckage is GPU instanced');
assert(trail.includes("colliders.push"),'wreckage has physical collision');
assert(terrain.includes('buildBalthrixTrail(group,'),'wreckage appears in actual town map');
assert(terrain.includes('stats.fallenTrees=trail.count'),'wreckage counted and inspected');
assert(terrain.includes("const trail=buildBalthrixTrail"),'wreckage placed before forest scatter');

// Cave is truly enclosed. Preserve the original portal/arena positions.
assert(cave.includes('enclosing-ice-cave-vault'),'cave roof closes sky');
assert(cave.includes('cave-floor-ice-spires')&&cave.includes('ceiling-icicles'),'ice stalagmites and ceiling icicles present');
assert(frost.includes('buildFrostCave(group,HALF,'),'ice realm actually builds new cave');
assert(frost.includes('const cols=cave.colliders'),'ice pillars share player physics');
assert(frost.includes('x:c.x+OX,z:c.z+OZ'),'ice colliders are in absolute world coordinates');
assert(terrain.includes('FROST_PORTAL.z+18'),'summit door recessed beyond cave entrance');
assert(main.includes('FROST_PORTAL.x,TOWN_LANDS?TOWN_LANDS.heightAt(FROST_PORTAL.x,FROST_PORTAL.z)'),'portal remains at existing world coordinate');

// Existing 3D harbor now has swept hulls with physical depth and curved sails.
assert(ship.includes('hullGeo.computeVertexNormals()'),'ship uses true curved mesh normals');
assert(ship.includes('const billow='),'sails have three-dimensional billow');
assert(building.includes('buildSailingShip(.8,true)'),'harbor visibly uses large 3D ship');
assert(building.includes('buildSailingShip(.38*sc,false)'),'small boats also use 3D hulls');

// Run parser checks in addition to these content / plan invariants.
for(const p of ['www/proto3d/main.js','www/proto3d/fight.js',
 'www/proto3d/combat/hud.js','www/proto3d/frostreach.js','www/proto3d/frost-cave.js',
 'www/proto3d/townlands.js','www/proto3d/bossregions.js','www/proto3d/camrig.js',
 'www/proto3d/balthrix-trail.js','www/proto3d/buildings.js','www/proto3d/port-ships.js']){
 const test=spawnSync(process.execPath,['--check',p],{encoding:'utf8'});
 assert.equal(test.status,0,p+' has invalid JavaScript: '+test.stderr);
}
console.log('PASS: combat HUD, world-entry activation, Sslythar concealment, '+sites.length+' fallen trees, icy cave, summit tunnel and 3D harbor.');
