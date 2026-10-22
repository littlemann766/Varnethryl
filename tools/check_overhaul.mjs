/* Safety tests for the staged 3D overhaul. Run with node tools/check_overhaul.mjs.
 * Tests are read-only; do not require an APK, credentials or a WebGL display. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {fallenTreeSites,balthrixPosition,isCitySafe,onLava,PORT_CENTER,FROST_SUMMIT,TITAN_CENTER} from '../www/proto3d/bossregions.js';
const source=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const hud=source('www/proto3d/combat/hud.js');
const editor=source('www/proto3d/hud-layout-editor.js');
const cheatPanel=source('www/proto3d/cheatpanel.js');
assert(!hud.includes('data-a="summon">Summon Titan')&&!hud.includes('data-a="exit">Exit fight'),
  'remove the two obsolete top-screen combat buttons');
assert(!hud.includes('<div class="top">'),'no empty combat top-control group');
assert(!editor.includes("'#cb .top','Combat options'"),'HUD customization excludes deleted buttons');
assert(cheatPanel.includes("act('spawn-titan', 'Spawn Ashen Titan'"),'owner still summons Titan from cheat menu');
const nav=source('www/proto3d.html');
const menu=source('www/proto3d/varn-menu.js');
const ui=source('www/proto3d/varn-ui.css');
assert(nav.includes('class="vn-quick-actions"'),'game menu has compact primary actions');
for(const id of ['vnQuickResume','vnChooseCharacter','vnOpenSettings','vnQuickTravel','vnCombatToggle','vnEditHud','vnTravelSail','vnTravelHydra','vnTravelTown','vnApprovedBosses','vnModelsToggle','vnStatusOpen','vnTitleBtn']){
  assert(nav.includes('id="'+id+'"'),'existing game menu command preserved: '+id);
}
assert(menu.includes('if(section.open)for(const other of sections)'),'game menu accordion closes other categories');
assert(menu.includes("document.getElementById('vnQuickResume')?.addEventListener('click',closeQuick)"),'resume action closes cluttered menu');
assert(ui.includes('#vnQuickMenu .vn-quick-actions{display:grid'),'main game menu is two-column and compact');
const main=source('www/proto3d/main.js');
const fight=source('www/proto3d/fight.js');
const terrain=source('www/proto3d/townlands.js');
const frost=source('www/proto3d/frostreach.js');
const cave=source('www/proto3d/frost-cave.js');
const ship=source('www/proto3d/port-ships.js');
const trail=source('www/proto3d/balthrix-trail.js');
const camera=source('www/proto3d/camrig.js');
const building=source('www/proto3d/buildings.js');
const marine=source('www/proto3d/water-realms.js');
const minimap=source('www/proto3d/minimap.js');
assert(minimap.includes("root.dataset.mode='live-topdown'"),'minimap uses real top-down terrain');
assert(minimap.includes('e.height?.(zone,x,z)'),'minimap samples actual terrain elevation');
assert(minimap.includes('e.water?.(zone,x,z)'),'minimap samples current water');
assert(minimap.includes('env.islands?.(overview)'),'minimap shows streamed islands locally and deterministic distant islands in FULL view');
assert(main.includes('miniMap.invalidate(); // redraw the real top-down'),'zone travel refreshes the map');
assert(marine.includes('if(!full)return [...obstacles.values()].flat();'),'local chart keeps streamed islands live');
assert(marine.includes('for(const p of islandLayout(tx,tz))island('),'3D islands use same layout as map chart');
assert(marine.includes('function mapFeatures(full=false)'),'full-ocean chart computes future unloaded islands');
assert(minimap.includes("overview?cfg.cx:(state.heroX||0)"),'FULL chart stays centred on map bounds, not hero');
assert(minimap.includes('Math.SQRT2*1.07'),'full zone view fits all square corners inside the circular minimap');
assert(minimap.includes('ctx.translate(player[0],player[1])'),'player location is plotted at world coordinates');
assert(main.includes('zoneTransitionQueue.then(()=>setZoneNow(name))'),'travel requests must be serialized');
assert(main.includes("if(qp.has('party'))for(const id of defaultFollowers)"),'explicit party override must fill missing saved follower berths');
assert(main.includes("fromSave&&!qp.has('party')"),'ordinary saved party remains unchanged without a party override');
assert(fight.includes("if (env.zone?.() === 'sailing') { if (on) stop(); return; }"),'combat cannot be enabled while sailing');
assert(fight.includes("if (env.zone?.() === 'sailing') { stop(); return; }"),'in-flight combat is disarmed on ship frame');
assert(main.includes("if(name==='sailing'&&FIGHT?.on)FIGHT.stop();"),'ocean entry forcibly disarms deferred combat');
assert(main.includes("if(name==='town'&&lastZone==='sailing'&&FIGHT)FIGHT.startAuto();"),
 'combat HUD must be restored when walking off the sailing ship');
assert(main.includes("await setZoneNow('town');return setZoneNow(name);"),'nested world travel must not reenter the queued promise');
assert(main.includes('zonePending(){return zoneTransitionCount;}'),'test runner can verify all travel requests have finished');
assert(main.includes("if(ZONE.name==='town' && totalFrames%9===0)hideInactiveHeroModels()"),'town must suppress inactive cached heroes');
assert(main.includes('!w || rec.retired || !crowd.includes(rec)'), 'retired follower downloads must never spawn ghost people');
assert(marine.includes("const vessel=new THREE.Group();vessel.name='player-sailing-ship'"),'sailing uses empty container with only the supplied GLB');
assert(marine.includes('export const OCEAN_METERS=1000'),'sailing zone resized to 1 km square');
assert(marine.includes('TILE=240,VIEW_RADIUS=2'),'island stream spans the smaller sea');
assert(marine.includes('const ready=glbFromGzip('),'sailing realm exposes approved-ship ready promise');
assert(main.includes('try{await target.ready;}catch(err)'),'sailing portal waits for original ship to load');
assert(main.includes('target.dispose();')&&main.includes('Tidewrack ship could not load'),'a failed ship leaves player safely in town');
assert(!marine.includes('buildSailingShip('),'the procedural stand-in cannot appear on the sailing map');
assert(marine.includes("foam.name='tapered-foam-streak'"),'sailing uses irregular tapered foam geometry');
assert(!marine.includes('new THREE.PlaneGeometry(5.5,23)'),'legacy white rectangle wake removed');
assert(marine.includes('cachedRockMaterials.has(m)'), 'streamed ocean tiles must not dispose shared rock materials');
assert(marine.includes('nav.heading-=rudder*step*.64*steering*'), 'right rudder must turn starboard, not port');
assert(marine.includes('if(disposed){dispose(model);return;}'), 'late Hydra model loads must be discarded after exit');
assert(marine.includes("if(disposed){dispose(imported);throw Error('Sailing realm unloaded before ship was ready');}"),
  'late sailing model loads must be discarded after exit');

// Critical combat failure: querySelector returns ONE button, not an array.
// Both slots and labels must use querySelectorAll's array wrapper.
assert(hud.includes("$('.sl').forEach"),'skill labels must select ALL 5 buttons');
assert(hud.includes('#cb .cx>.sl .nmL{display:none!important}'),'narrow skill labels must not overlap');
assert(hud.includes('skill-name-callout'),'touch and focus must reveal full skill names');
assert(hud.includes("body:has(#vnMiniMap.expanded) #cb .top"),'owner actions must clear expanded minimap');
assert(hud.includes("$$('.sl').map"),'skill array must select ALL 5 buttons');
assert(!hud.includes("this.slots = $('.sl').map"),'fatal HUD initialization regression');
assert(main.includes("document.getElementById('vnEnter')?.addEventListener('click'"),'ordinary Enter activates combat');
assert(main.includes("fightToggle(true).then(f=>f.startAuto())"),'all heroes receive combat HUD on entry');
assert(main.includes("!FIGHT.on||!FIGHT.auto"),'wilderness promotes training mode into auto encounters');
assert(camera.includes('const orbitAngle ='),'third-person camera uses real spherical pitch orbit');
assert(main.includes('camRig.look(0, -(e.clientY - t.ly) * 0.005'),'vertical touch orbit is actually connected');
assert(!fight.includes('u.serpentWave(dt,mv'),'Balthrix must not corkscrew his 29 animated spine/tail joints with a post-mixer overlay');
assert(fight.includes('serpentHeading(r.rotation.y,heading,dt)'),'serpent root yaw uses frame-rate independent turn limit');
assert(fight.includes("import { serpentHeading } from './serpent-locomotion.js';"),'shared serpent turning is testable');

const wrenCloth=JSON.parse(source('www/proto3d/models-new/wren_cl_arms.cloth.json'));
const wrenWings=wrenCloth.groups.filter(g=>g.kind==='wing');
assert.equal(wrenWings.length,2,'Wren has independently authored left and right wing joints');
assert(wrenWings.every(g=>g.enabled===false),'no wing spring may fight Wren baked wing animations');
assert(main.includes("const matchingGroups=id==='n:wren_new3'"),"Wren 3D model must filter out wing springs");
assert(main.includes("}else if (id === 'n:wren_new3')"),'a missing cloth JSON must never reactivate generic wing springs');
const appVersion=JSON.parse(source('package.json')).version;
assert(main.includes("const ASSET_V = '"+appVersion+"'"),
  'model cache must match current '+appVersion+' Android/Web release');

assert(fight.includes('14*Math.max(0,dt)'),'Balthrix patrol advances per frame instead of jerky time chunks');
assert(fight.includes('nearestBalthrixPath(state.heroX,state.heroZ)'),'Balthrix encounter placement uses the same curved spline as its movement');
assert(!fight.includes('nearestRoamTime('),'old straight-waypoint route estimate must not return');
assert(fight.includes('roamer.roamSpeed=Math.min(14,'),'Balthrix eases into patrol without sudden full-speed sliding');
assert(fight.includes('if (on) { if (isAuto === true) auto = true; return; }'),'existing active combat must be promotable');
assert(main.includes("group.key === 'ssylthar'"),'unreleased Sslythar remains hidden');
assert(main.includes('const hiddenSerpentSlot ='),'unreleased Sslythar saved/URL selection is guarded');
assert(main.includes('const seen = new Set(), rosterGroups = []'),'roster must not shadow Three GLTFLoader with a local gl array');
assert(main.includes("gl.parse(buffer,'',g=>"),'character preview must use the GLTFLoader instance, not a roster list');
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
assert(ship.includes('tidewrack_sailing_ship.glb'),'Tidewrack loads the uploaded original 3D ship');
assert(ship.includes('export async function installImportedShip('),'Tidewrack can switch ships on GLB load');
assert(ship.includes('ship.userData.originalShipFallback=fallbackChildren'),'Tidewrack procedural ship is kept as fallback');
assert(terrain.includes('installImportedShip(ships[0],{large:true})'),'actual ship attached to main mooring');
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
