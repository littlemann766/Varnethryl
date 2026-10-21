/* Static artist GLB scenery registry. No Three.js dependency, so route and
 * placement checks can run in Node without graphics or loading big assets. */
import {PORT_CENTER,TITAN_CENTER,FROST_REALM} from './bossregions.js';
export const SCENERY_ASSETS=Object.freeze({
 volcano:'volcano.glb',lavaRock:'lava-rock.glb',ship:'sailing-ship.glb',
 castle:'castle-props.glb',weapon:'medieval-weapon.glb',
 cavern:'ice-cavern.glb',crystals:'ice-crystals.glb'
});
export const SCENERY_SITES=Object.freeze([
 {id:'titan-volcano',zone:'town',asset:'volcano',x:TITAN_CENTER.x+65,z:TITAN_CENTER.z-63,height:22,near:195,rotation:.5},
 {id:'titan-lava-outcrop',zone:'town',asset:'lavaRock',x:TITAN_CENTER.x-57,z:TITAN_CENTER.z+23,height:8,near:150,rotation:.9},
 {id:'volcanic-harbor-ship',zone:'town',asset:'ship',x:PORT_CENTER.x-49,z:PORT_CENTER.z-7,height:29,near:150,rotation:.3,water:true},
 {id:'castle-courtyard-statue',zone:'town',asset:'castle',x:-25,z:-173,height:10,near:115,rotation:-.2},
 {id:'blacksmith-weapon-display',zone:'town',asset:'weapon',x:87,z:27,height:4.8,near:95,rotation:.5},
 {id:'frost-cavern-rockwork',zone:'frost',asset:'cavern',x:FROST_REALM.cx-115,z:FROST_REALM.cz-140,height:30,near:150,rotation:2.1},
 {id:'frost-crystals-north',zone:'frost',asset:'crystals',x:FROST_REALM.cx+101,z:FROST_REALM.cz-102,height:12,near:138,rotation:-.6},
 {id:'frost-crystals-east',zone:'frost',asset:'crystals',x:FROST_REALM.cx+130,z:FROST_REALM.cz+35,height:8,near:135,rotation:1.4}
]);
export const sceneryAssetPath=id=>'proto3d/models-scenery/'+SCENERY_ASSETS[id];
export function scenerySiteErrors(sites=SCENERY_SITES){
 const errors=[],ids=new Set();
 for(const site of sites){
  if(!SCENERY_ASSETS[site.asset])errors.push(site.id+': missing asset');
  if(!['town','frost'].includes(site.zone))errors.push(site.id+': bad zone');
  if(!Number.isFinite(site.x)||!Number.isFinite(site.z)||!(site.height>0))errors.push(site.id+': invalid coordinates/height');
  if(ids.has(site.id))errors.push(site.id+': duplicated site'); ids.add(site.id);
 }
 return errors;
}
