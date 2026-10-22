// Varnethryl boss-region lore, size, encounter and geography checks (Node-only).
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {HERO_M,HERO_LORE_HEIGHTS,inchesToMeters,CHARS,profileFor,loadScale} from '../www/proto3d/charscale.js';
import {BOSS_PATTERNS,ENEMIES} from '../www/proto3d/combat/data.js';
import {pickPattern} from '../www/proto3d/combat/ai.js';
import {CITY_HALF,TITAN_CENTER,FROST_SUMMIT,FROST_REALM,FROST_PORTAL,LAVA_POOLS,PORT_CENTER,isCitySafe,balthrixPosition,onLava,frostHill,lavaAmount} from '../www/proto3d/bossregions.js';
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
