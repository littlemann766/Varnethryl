// Varnethryl boss-region lore, size, encounter and geography checks (Node-only).
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {HERO_M,HERO_LORE_HEIGHTS,inchesToMeters,CHARS,profileFor,loadScale} from '../www/proto3d/charscale.js';
import {BOSS_PATTERNS,ENEMIES} from '../www/proto3d/combat/data.js';
import {pickPattern} from '../www/proto3d/combat/ai.js';
import {applyPose} from '../www/proto3d/bump.js';
import {CITY_HALF,TITAN_CENTER,FROST_SUMMIT,FROST_REALM,FROST_PORTAL,LAVA_POOLS,PORT_CENTER,isCitySafe,balthrixPosition,nearestBalthrixPath,onLava,frostHill,lavaAmount} from '../www/proto3d/bossregions.js';
const src=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const close=(a,b)=>Math.abs(a-b)<1e-8;
assert(close(HERO_M,1.905),'Owner must be 1.905 m');
assert.equal(Object.keys(HERO_LORE_HEIGHTS).length,20,'all 20 established heroes need lore heights');
for(const [id,inch] of Object.entries(HERO_LORE_HEIGHTS)){
 assert(close(profileFor(id).height,inchesToMeters(inch)),'lore height '+id);
 assert(close(loadScale(id,1.8)*1.8,inchesToMeters(inch)),'uniform scale '+id);
 assert(close(loadScale('n:'+id+'_smooth',1.8)*1.8,inchesToMeters(inch)),'smooth skin scale '+id);
}
for(const id of ['n:owner','n:owner_pika1'])assert(close(profileFor(id).height,HERO_M),'Owner skin remains 1.905 m');
for(const id of ['n:frosttroll_a','n:frosttroll_b']){
 assert(close(profileFor(id).height,3.5*HERO_M),id+' must equal 3.5x Owner');
 assert(close(loadScale(id,11.4)*11.4,3.5*HERO_M),'model height normalized for '+id);
}
for(const [id,mul] of [['n:ashentitan_new',10],['n:ashentitan_20',10],['n:ashentitan_40',10],['n:ashentitan_60',60],['n:vaelthryx_straight_rig',6],['n:vaelthryx_straight_rig_50',50]])
 assert(close(profileFor(id).height,mul*HERO_M),id+' height ratio');
assert(close(profileFor('n:ashentitan_20').height,19.05),'Active lava boss stands 19.05 m');
for(const [id,model] of [['titan40','n:ashentitan_20'],['frosttroll_a','n:frosttroll_a'],['frosttroll_b','n:frosttroll_b'],['vaelthryx','n:vaelthryx_straight_rig']]){
 assert.equal(ENEMIES[id].model,model,'encounter GLB for '+id);
 assert(ENEMIES[id].boss&&BOSS_PATTERNS[id]?.length>=3,'unique combat skills for '+id);
 const e={key:id,def:ENEMIES[id],phase:1,patI:0};
 const k=pickPattern(e);assert(k&&k.name&&k.reach&&k.tele,'attack pattern selected for '+id);
}
assert.equal(CITY_HALF,185,'town walls remain close');
assert.equal(FROST_SUMMIT.height,60,'steep but walkable mountain summit');
assert(frostHill(FROST_PORTAL.x,FROST_PORTAL.z)>59,'frost cave on summit');
assert(frostHill(0,-200)<5,'graded mountain foot');
assert(onLava(TITAN_CENTER.x,TITAN_CENTER.z),'lava pools surround 10x Titan');
assert(lavaAmount(TITAN_CENTER.x,TITAN_CENTER.z)>.95,'volcano terrain covers boss');
assert(!isCitySafe(TITAN_CENTER.x,TITAN_CENTER.z)&&!isCitySafe(FROST_SUMMIT.x,FROST_SUMMIT.z),'both boss regions outside city');
assert(FROST_REALM.cx>1500&&FROST_REALM.half>200,'new separated icy map');
let roamerVisitsVolcano=false;
for(let t=0;t<900;t+=.5){
 const p=balthrixPosition(t);
 assert(!isCitySafe(p.x,p.z),'Balthrix never enters protected city walls');
 if(Math.hypot(p.x-TITAN_CENTER.x,p.z-TITAN_CENTER.z)<32)roamerVisitsVolcano=true;
}
assert(roamerVisitsVolcano,'Balthrix patrol crosses Titan lava region');
// Encounter discovery MUST use the spline's physical arc-length clock, not
// straight chords connecting waypoints. Test positions including curves.
for(let t=0;t<110;t+=.75){
 const p=balthrixPosition(t),nearest=nearestBalthrixPath(p.x,p.z);
 const phase=Math.abs(nearest.time-t);
 assert(nearest.distance<0.15,'nearest Balthrix route should be on curved path');
 assert(phase<0.3,'nearest route phase must match the spline patrol clock');
}
assert.equal(nearestBalthrixPath(NaN,10).distance,Infinity,'invalid roamer coordinates are rejected');
// Regression: the serpent's arc-length patrol should maintain steady travel
// speed and its heading should not snap as it rounds waypoint corners.
let previous=balthrixPosition(0);
for(let t=.1;t<=60;t+=.1){
 const current=balthrixPosition(t);
 const distance=Math.hypot(current.x-previous.x,current.z-previous.z);
 assert(distance>.95&&distance<1.85,'Balthrix patrol speed must remain near 14 units/s');
 const headingDelta=Math.atan2(Math.sin(current.yaw-previous.yaw),Math.cos(current.yaw-previous.yaw));
 assert(Math.abs(headingDelta)<.25,'Balthrix heading must turn continuously');
 previous=current;
}
const main=src('www/proto3d/main.js'),terrain=src('www/proto3d/townlands.js'),ice=src('www/proto3d/frostreach.js'),fight=src('www/proto3d/fight.js'),hud=src('www/proto3d/combat/hud.js');
assert(main.includes("const destination=ZONE.name==='town'?(isFrostCave?'frost':'wilds'):'town';")&&main.includes('Promise.resolve().then(()=>setZone(destination))')&&main.includes('portalTransitionPending=true;'),'bidirectional ice cave portal wired and guarded against overlapping transitions');
assert(main.includes("r.level = state.level; r.ti = null; r.lvT = 0; r.stuckT = 0;"),'teleport followers match hero floor and reset stuck state');
assert(main.includes("resolve(spot, false, 'npc')"),'teleported followers use collision resolution');
assert(main.includes("r.y = surfaceAt(a.x, a.z, r.level)?.y ?? (state.heroY || 0)"),'revived and catch-up followers use surface height');
assert(main.includes("if (document.hidden) setTravelRun(false)"),'backgrounding game clears held sprint state');
assert(main.includes('run.setEffectiveWeight((standing ? 0 : runMix)*ov)'),'missing-idle rigs never blend into running while standing');
assert(main.includes('const animDt = Number.isFinite(dt) ? Math.max(0, Math.min(dt, 0.05)) : 0'),'animation frame stalls are bounded');
assert(main.includes('u.mixer.update(animDt); if (u.sb) u.sb.update(animDt)'),'hero cloth and mixer use bounded animation delta');
assert(main.includes('Short-range obstacle avoidance: test forward and two angled probes'),'companions probe obstacles before steering');
assert(main.includes("try { resolve(probe, false, 'npc'); }"),'companion probes use collision resolver');
assert(main.includes("finally { state.level = previousLevel; }"),'companion probes restore world floor');
assert(main.includes('r.avoidSide = chooseLeft ? -1 : 1'),'companions remember avoidance side');
assert(main.includes('const wideAngle = 1.35'),'companions test wider turns when narrow turns are blocked');
assert(main.includes("}else if (cfg && id === 'n:owner')"),'Owner incompatible cape rigs bypass generic spring-bone fallback');
assert(main.includes('window.__varnethrylRigAudits[id] = report'),'Owner and Balthrix rig audit is exposed for device inspection');
assert(main.includes('Object.assign(root.userData, { glb: true, mixer'),'rig audit survives animation initialization');
assert(main.includes('serpentBones: bones.filter'),'serpent skeleton audit records relevant bone families');
assert(main.includes('serpentAnimatedTracks: g.animations.map'),'serpent audit checks actual animation tracks');
assert(main.includes('root.userData.rigAudit.authoredSlither=clips.filter'),'Balthrix preserves authored full-body slither clips');
assert(!main.includes('createSerpentWave(m)'),'Balthrix no longer receives a destructive additive skeletal twist');
assert(main.includes("'n:vaelthryx_straight_rig': { walk: 0.30, run: 0.80 }"),'Balthrix body animations play at achievable native gait speeds');
assert(main.includes('full-body wave is not verified'),'serpent audit diagnoses clips without spine animation');
assert(main.includes('root.userData.rigAudit.resolved = {'),'rig audit records resolved locomotion capabilities');
assert(main.includes("if (id === 'n:owner' && !act.walk && !act.run)"),'Owner missing locomotion clips are diagnosed');
assert(main.indexOf('if (/vaelthryx/.test(id) && !act.walk && !act.run)') > main.indexOf('if (spd && spd.map)'),'Balthrix missing-clip diagnostic runs after profile mapping');
assert(main.includes('cape physics disabled until a compatible rig is supplied'),'incompatible Owner cape physics is diagnosed');
assert(main.includes('const useWide = Math.max(dl, dr) < look * 0.7'),'wider turns only used when useful');
assert(main.includes("diag('Balthrix rig has no recognized slither/body-wave animation"),'missing Balthrix body-wave clips are reported');
assert(main.includes('serpentine|bodywave|snake'),'additional serpent locomotion clips are recognized');
assert(main.includes("r.vxs = r.vzs = r.a.vx = r.a.vz = 0"),'teleported followers do not retain sprint velocity');
assert(main.includes('TOWN_LANDS.updateWater?.(simTime,state.heroX,state.heroZ)'),'water animation and ship culling use player position');
assert(main.includes('state.swimming'),'hero can swim');
assert(terrain.includes('mesh.castShadow=true')&&terrain.includes('mesh.receiveShadow=true'),'hills cast and receive shadows');
assert(terrain.includes("water.name='harbor-swim-water'"),'water available at port');
assert(ice.includes("ground.castShadow")===false||ice.includes("terrain.castShadow=true"),'ice mountains cast shadows');
assert(ice.includes("frosttroll_b")===false||ice.includes('FROST_BROTHERS'),'ice realm uses both brothers');
assert(fight.includes('startRegionBosses'),'automatic boss spawning at frost');
assert(fight.includes('balthrixPosition(regionClock+(roamer.routePhase||0))'),'roaming Balthrix follows phased patrol');
const ai=src('www/proto3d/combat/ai.js');
assert(ai.includes('const deltaYaw = Math.atan2(Math.sin(targetYaw - currentYaw)'),'boss facing turns smoothly');
assert(ai.includes("e.state !== 'telegraph' && e.state !== 'attack'"),'telegraphed attacks lock their facing');
assert(fight.includes("dHero>52&&roamer.state==='idle'"),'Balthrix patrol never overrides active chase or recovery');
assert(hud.includes('VARNETHRYL ⚜')&&hud.includes("this.slotAbility"),'Varnethryl HUD retains real combat controls');
const controller=src('www/proto3d/combat/controller.js');
const lightning=src('www/proto3d/combat/lightning.js');
// Verify the key combat safeguards stay wired into the actual gameplay modules.
assert(controller.includes("locked.state !== 'defeated'")&&controller.includes('maxRange + locked.def.r'),'ranged skills discard stale/out-of-range locks');
assert(controller.includes('if (e.state === \'defeated\') return;'),'defeated enemies cannot be hit repeatedly');
assert(controller.includes("pt.shape === 'cone'")&&controller.includes("pt.shape === 'line'"),'boss hit detection checks directional telegraphs');
assert(fight.includes('groundY: terrainY')&&lightning.includes('this.groundY(x,z)'),'boss lightning impacts use actual terrain height');
assert(hud.includes('#cb .sl:focus-visible')&&hud.includes('border:2px solid #caa35c'),'medieval combat controls remain keyboard accessible');
assert(hud.includes("const $ = s => r.querySelector(s), $$ = s => Array.from(r.querySelectorAll(s));"),'combat selectors must be unique: $ for single and $$ for multiple elements');
assert(main.includes('performance.now()>=outdoorCombatRetryAt'),'combat startup import errors must not re-trigger every frame');

const bump=src('www/proto3d/bump.js'), buildingsKit=src('www/proto3d/bldkit.js');
assert(bump.includes('root.position.y = baseY + fin(a.phop, 0)'),'animated companions preserve terrain elevation');
// Exercise the exact bug: pose animation must add hop to outdoor terrain height,
// not reset the model to y=0 (which made companions disappear through hills).
const companionMock={rotation:{order:'XYZ',x:0,y:0,z:0},position:{y:0}};
applyPose({ptx:0,ptz:0,pyaw:0,phop:.25},companionMock,null,0,37.5);
assert.equal(companionMock.position.y,37.75,'companion stands on 37.5m slope while reacting to bump');
applyPose({ptx:0,ptz:0,pyaw:0,phop:0},companionMock,null,0,0);
assert.equal(companionMock.position.y,0,'flat village placement remains grounded');

assert(main.includes('applyPose(a, w, r.nd, a.yaw, r.y)'),'followers pass terrain height through pose');
assert(main.includes('crowdSurface(r, a, dt)'),'followers continue sampling shared terrain after moving');
assert(buildingsKit.includes('export function scrubDecorativeFaces('),'malformed colorful town decor is sanitized');
assert(buildingsKit.includes('scrubDecorativeFaces(raw, m.material)'),'village exterior batching filters oversized decoration triangles');
assert(hud.includes('1.3.7 portrait HUD')&&hud.includes('grid-template-rows:repeat(2,auto)'),'portrait combat uses compact right-hand skill pad');
const desktopCss=src('www/proto3d/varn-ui.css');
assert(desktopCss.includes('#diagBtn,body.vn-diagnostic-error #diagBtn'),'3D Status cannot cover joystick');

const armory=src('www/proto3d/combat/armory.js'),menu=src('www/proto3d/varn-menu.js'),settings=src('www/proto3d/settings3d.js');
assert(armory.includes('seen.has(id)')&&armory.includes('used.has(id)'),'equipment load and presets reject duplicate items');
assert(armory.includes('(!it.ownerOnly || this.ownerOk())'),'saved owner equipment remains gated');
assert(hud.includes("addEventListener('blur'")&&hud.includes('api.block(false)'),'held block releases if app loses focus');
assert(hud.includes("aria-label', i === 0 ? 'Basic attack'"),'skill buttons have accessible labels');
assert(menu.includes("document.getElementById('vnQuickMenu')?.setAttribute('hidden', '')"),'title menu closes quick menu');
assert(settings.includes('E.openCheatPanel?.()'),'owner cheat entry still routes through gated panel');


for(const p of ['bossregions.js','frostreach.js','townlands.js','main.js','fight.js','charscale.js','combat/data.js','combat/hud.js']){
 const f='www/proto3d/'+p,v=spawnSync(process.execPath,['--check',f],{encoding:'utf8'});
 assert.equal(v.status,0,f+' syntax: '+v.stderr);
}
console.log('PASS: Lore scale / 40x Titan / 3.5x frost brothers / 6x & 50x Balthrix / lava / mountain portal / icy realm / boss skills / roaming / swimming / HUD / shadows.');

const loader = readFileSync(new URL('../www/proto3d/loader.js', import.meta.url), 'utf8');
const loaderCss = readFileSync(new URL('../www/proto3d/varn-ui.css', import.meta.url), 'utf8');
assert(loader.includes('if(engineReady)finish()'),'cinematic loader exits when engine is ready');
assert(loader.includes('video.hidden=true; // prevent black video placeholder'),'loader hides unavailable film');
assert(loaderCss.includes('Cinematic loader layout'),'loader video has separate cinematic layout');

const titlePage=src('www/proto3d.html'),menuScript=src('www/proto3d/varn-menu.js');

const settingsSrc=src('www/proto3d/settings3d.js'),settingsStyles=src('www/proto3d/varn-ui.css');
const pkg=JSON.parse(src('package.json'));
assert.equal(titlePage.match(/id="vnVersion">([^<]+)</)[1],pkg.version,'in-game version badge must match installed package version');
assert(!settingsSrc.includes('Varnethryl 3D · v1.2.9'),'settings cannot display the obsolete hardcoded version');
assert(settingsSrc.includes("getElementById('vnVersion')?.textContent"),'settings version sourced from active build label');
assert(settingsSrc.includes("document.body.classList.add('vn-settings-open')"),'opening settings enters gameplay-blocking modal state');
assert(settingsSrc.includes("document.body.classList.remove('vn-settings-open')"),'closing settings restores the controls');
assert(settingsStyles.includes('body.vn-settings-open #settingsPanel')&&settingsStyles.includes('z-index:7000!important'),'settings must sit above combat and touch controls');
assert(settingsStyles.includes('body.vn-settings-open::before'),'settings backdrop captures touches outside the settings panel');
for(const key of ['#staminaHud','#moveActions','#stick','#cb','#vnHudEditorPanel'])
 assert(settingsStyles.includes(key),'settings blocks gameplay control '+key);
assert(settingsSrc.includes("const hudEd = () => window.__vnHudEditor || null;"),'settings HUD editor uses active custom layout editor');
assert(src('www/proto3d/hud-layout-editor.js').includes('window.__vnHudEditor={open,close,refresh,reset'), 'settings reset has a functioning HUD reset method');


const hudEditor=src('www/proto3d/hud-layout-editor.js');
assert(titlePage.includes('id="vnEditHud"')&&titlePage.includes('proto3d/hud-layout-editor.js'),'HUD editor is accessible from the actual in-game menu');
assert(hudEditor.includes("document.getElementById('vnEditHud')?.addEventListener('click',open)"),'HUD editor menu starts editable state');
for(const selector of ["'#stick'","'#runBtn'","'#jumpBtn'","'#cb .sl.b'","'#cb .vn-exp'"]){
 assert(hudEditor.includes(selector),'HUD editor missing a required input: '+selector);
}
assert(hudEditor.includes("localStorage.setItem(KEY,JSON.stringify(saved))"),'HUD edits survive reopening the app');
assert(hudEditor.includes("orient=()=>innerWidth>=innerHeight?'landscape':'portrait'"),'portrait and landscape HUD positions saved independently');
assert(hudEditor.includes("document.addEventListener('pointermove'"),'HUD buttons can be moved with touch drag');
assert(hudEditor.includes("data-hud-action=\"larger\"")&&hudEditor.includes("data-hud-action=\"smaller\""),'HUD buttons have working resizing controls');
assert(hudEditor.includes("new MutationObserver"),'newly loaded combat controls restore saved HUD placement');

assert(hud.includes('v1.4.0: quiet gameplay layout') && hud.includes('#cb .cx>.cl, #cb .cl'),'auxiliary combat controls remain in code but disappear visually');
assert(!hudEditor.includes("...['dodge','block','jump','lock','potion','swap'].map"),'hidden utility strip is no longer editable or highlighted');
assert(hudEditor.includes("const KEY='vn.hud.layout.v2'"),'old customized positions do not recreate superseded 6-button layout');
assert(hud.includes('top:max(7px,env(safe-area-inset-top))!important;bottom:auto!important'),'XP frame is pinned to upper HUD');
const screenCss=src('www/proto3d/varn-ui.css');
assert(screenCss.includes('/* v1.4.0 HUD: only the left joystick'),'lower-left layout is reserved for joystick');
assert(screenCss.includes("top:calc(max(7px,env(safe-area-inset-top)) + 77px)!important"),'stamina meter appears beneath top XP');
assert(screenCss.includes('body.vn-hud-editing #staminaHud'),'stamina remains selectable in HUD editor');
assert(screenCss.includes('#moveActions{')&&screenCss.includes('left:auto!important;right:max(10px'),'walk and jump move to right side');
assert(fight.includes("document.getElementById('stick')?.addEventListener('pointerdown'"),'dodge remains available on touch without a second button bar');
assert(fight.includes("const onKey = e =>"),'existing keyboard block, potion, weapon and lock commands remain supported');

assert(main.includes('stick.offsetWidth,stick.offsetHeight'),'movement joystick range changes with user resize');
const water=src('www/proto3d/water-realms.js');
assert(water.includes('export const OCEAN_METERS=1000'),'sailing world is a 1,000 by 1,000 meter sea');
assert(water.includes('OCEAN_METERS*WORLD_UNITS_PER_METER/2'),'ocean world size configurable');
assert(water.includes('const TILE=420') || water.includes('TILE=420'),'ocean islands load by local tiles');
assert(water.includes('tiles.delete(k)')&&water.includes('obstacles.delete(k)'),'ocean tiles unload outside view');
assert(water.includes('hydra_restored_mobile.glb.gz'),'Hydra model path points to restored chest and rock cleanup');
assert(water.includes('tidewrack_sailing_ship.glb.gz'),'sailing world uses owner-supplied vessel');
const offline=src('www/sw.js');
for(const asset of ['water-realms.js','hydra_restored_mobile.glb.gz','tidewrack_sailing_ship.glb.gz']){
 assert(offline.includes(asset),'release offline cache includes water realm asset '+asset);
}
assert.equal(offline.match(/const CACHE = PREFIX \+ '([^']+)'/)[1],pkg.version,'offline cache matches the installed APK version');
assert(water.includes('glbFromGzip')&&water.includes('DecompressionStream'),'compressed models are loaded into Three.js');
assert(water.includes('hydra-unrigged-5-head'),'Hydra is not inaccurately labelled fully rigged');
for(const btn of ['vnTravelSail','vnTravelHydra','vnTravelTown']) assert(titlePage.includes('id="'+btn+'"')&&main.includes("'"+btn+"'"),'menu and game must wire travel button: '+btn);
assert(main.includes("name === 'hydra' || name === 'sailing'"),'separate marine realm traversal is integrated');
assert(main.includes("ZONE.name==='sailing'&&SM?.blocked"),'sailing boat collides with discovered islands');
assert(main.includes("ZONE.name==='hydra'&&HM?.waterAt"),'Hydra water and terrain are part of player movement');
assert(screenCss.includes('body.vn-sailing-zone #moveActions'),'sailing hides irrelevant walking controls');
const ownerPanelSrc=src('www/proto3d/cheatpanel.js');
assert(ownerPanelSrc.includes('z-index:8100'),'Owner map cheats must appear above world/HUD overlays');
assert(main.includes("zones: ['village', 'wilds', 'frost', 'hydra', 'sailing']"),'owner teleport includes all five maps');
for(const id of ["'hydra'","'sailing'","'frost'","'village'"]){
 assert(ownerPanelSrc.includes(id),'owner travel shortcut visible for '+id);
}
for(const id of ['tp-hydra','tp-sailing','tp-frost','tp-main']){
 assert(ownerPanelSrc.includes(id),'owner cheats direct map button '+id);
}
assert(main.includes("['wilds','frost','hydra','sailing'].includes(zone)"),'owner map shortcuts use zone lifecycle instead of unloaded coordinates');
assert(main.includes("lastZone!=='town'&&name!=='town'"),'travel between any non-town maps safely returns through main overworld');
assert(water.includes("function sail(dt,turn,throttle,x,z)"),'ship rudder/throttle is distinct from walking movement');
assert(water.includes("nav.speed+=(target-nav.speed)"),'ship acceleration is smooth rather than instant');
assert(water.includes("blocked(nx,nz,8)"),'ship tests collision with jagged islands');
assert(main.includes("SM.sail(dt,rudder,throttle,state.heroX,state.heroZ)"),'touch and keyboard steering invoke real boat physics');
const combatData=src('www/proto3d/combat/data.js');
for(const head of ['leftsnap','acidbreath','kinglunge','tailsweep','venomburst'])
 assert(combatData.includes("id:'"+head+"'"),'Hydra has attack pattern '+head);
assert(combatData.includes("hydra: E('Five-Headed Hydra'"),'Hydra has a boss-health entry');
assert(main.includes("f.startRegionBosses('hydra')"),'Hydra arena auto-starts its five-attack boss encounter');
assert(main.includes("id==='hydra:mire'"),'Hydra combat hitbox reuses the full intact 3D map model');
assert(water.includes("defeatBoss(){hydraDefeated=true"),'Hydra victory animation and return state');
assert(fight.includes("env.onHydraDefeat?.()"),'Hydra boss victory reports to the map');
const waterParse=spawnSync(process.execPath,['--check','www/proto3d/water-realms.js'],{encoding:'utf8'});
assert.equal(waterParse.status,0,'water realms JavaScript must parse: '+waterParse.stderr);
const hudParse=spawnSync(process.execPath,['--check','www/proto3d/hud-layout-editor.js'],{encoding:'utf8'});
assert.equal(hudParse.status,0,'HUD editor must be syntactically valid: '+hudParse.stderr);

assert(!titlePage.includes('id="vnCamp"'),'hobgoblin camp removed from title menu');
assert(!menuScript.includes("getElementById('vnCamp')"),'no menu teleport to hobgoblin camp');
assert(fight.includes('function hobGrunt(distance)'),'camp grunts generated in combat world');
assert(fight.includes('if(nearest<43)'),'hobgoblin grunt distance is bounded');

const viewer=src('www/proto3d/model-viewer.html');
assert(main.includes("'Playable Characters'")&&main.includes("'Companions'")&&main.includes("'Enemies & Bosses'"),'character roster has three clear categories');
assert(main.includes("setTimeout(()=>{")&&main.includes("vnSkinBubble"),'long press opens in-game skin bubble');
assert(viewer.includes("new URLSearchParams(location.search).get('model')"),'model viewer deep links to requested skin');

assert(fight.includes("hud.say('COMBAT READY'"),'combat starts for selected hero');
assert(!fight.includes('env.selectOwner().then('),'combat does not force Owner hero');
assert(main.includes('fightInitPromise'),'combat initialization is guarded against duplicate imports');
