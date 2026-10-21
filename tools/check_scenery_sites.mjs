import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {SCENERY_SITES,SCENERY_ASSETS,scenerySiteErrors,sceneryAssetPath} from '../www/proto3d/scenery-map-data.js';
import {PORT_CENTER,TITAN_CENTER,FROST_REALM,isCitySafe} from '../www/proto3d/bossregions.js';
const root=new URL('../',import.meta.url);
assert.deepEqual(scenerySiteErrors(),[],'all creator-model sites valid');
const keys=Object.keys(SCENERY_ASSETS);
assert.equal(keys.length,7,'7 textured non-animated landscape/prop models');
for (const id of keys)assert(sceneryAssetPath(id).endsWith('.glb'),'only GLB sources');
for(const site of SCENERY_SITES){
 assert(!/(warrior|dragon|armor|equipment)/.test(site.asset),'unanimated characters and untextured assets excluded');
 if(site.zone==='town' && !site.id.includes('castle') && !site.id.includes('blacksmith'))
  assert(!isCitySafe(site.x,site.z),'outer scenery is not in protected city');
 if(site.zone==='frost')assert(Math.hypot(site.x-FROST_REALM.cx,site.z-FROST_REALM.cz)<FROST_REALM.half-20);
}
const find=id=>SCENERY_SITES.find(s=>s.id===id);
assert(Math.hypot(find('volcanic-harbor-ship').x-PORT_CENTER.x,find('volcanic-harbor-ship').z-PORT_CENTER.z)<90,'ship belongs to port water');
assert(Math.hypot(find('titan-lava-outcrop').x-TITAN_CENTER.x,find('titan-lava-outcrop').z-TITAN_CENTER.z)<110,'lava rock belongs to Titan terrain');
assert(SCENERY_SITES.filter(s=>s.asset==='crystals').length===2,'ice crystals reused in frost zone');
const game=readFileSync(new URL('www/proto3d/main.js',root),'utf8');
assert(game.includes('SCENERY.update(ZONE.name'),'optional scenery updates only near current player');
assert(game.includes('get sceneryModels(){return SCENERY.status();}'),'device diagnostic available');
const module=readFileSync(new URL('www/proto3d/scenery-assets.js',root),'utf8');
assert(module.includes('if(loading)return'),'only one heavy model loads at a time');
assert(module.includes("missing',asset"),'missing model tolerates fallback');
assert(module.includes('root.userData.nonBlocking=true'),'scenery does not modify navigation collisions');
console.log('PASS: 7 optional textured creator models mapped to volcano, harbor, castle, smithy and frost; non-animated rigs excluded');
