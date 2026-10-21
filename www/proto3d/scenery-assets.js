/* Optional, original creator GLBs used as scenic dressing in designated zones.
 * No boss/NPC rig is overwritten, no city collisions are changed, and a
 * missing asset never prevents the established procedural game from loading.
 * 45-55k triangles per source model: only load nearby assets, one at a time.
 */
import * as THREE from './vendor/three.module.js';
import {GLTFLoader} from './vendor/jsm/loaders/GLTFLoader.js';
import {SCENERY_ASSETS,SCENERY_SITES,sceneryAssetPath} from './scenery-map-data.js';
export {SCENERY_ASSETS,SCENERY_SITES,sceneryAssetPath,scenerySiteErrors} from './scenery-map-data.js';

export function createSceneryAssets({scene,townElevation,frostElevation,version='1.2.8',onEvent=()=>{}}){
  const loader=new GLTFLoader(),groups={town:new THREE.Group(),frost:new THREE.Group()};
  for(const z of ['town','frost']){
    groups[z].name='optional-creator-scenery-'+z;
    groups[z].visible=false;
    groups[z].userData.keepAlways=true;
    scene.add(groups[z]);
  }
  const models=new Map(),items=new Map(),failures=new Map();
  let activeZone='town',loading=false,lastTick=-1;

  function createOne(site,template){
    // The site transform is independent of other copies of a shared model.
    const root=new THREE.Group(),model=template.clone(true);
    model.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;o.frustumCulled=true;}});
    const bounds=new THREE.Box3().setFromObject(model),dims=bounds.getSize(new THREE.Vector3());
    if(!Number.isFinite(dims.y)||dims.y<=1e-6)throw Error('Missing vertical bounds');
    const scale=site.height/dims.y;
    model.scale.multiplyScalar(scale);
    model.position.set(-(bounds.min.x+bounds.max.x)*.5*scale,-bounds.min.y*scale,
      -(bounds.min.z+bounds.max.z)*.5*scale);
    root.name=site.id;root.add(model);
    const y=site.water?.15:(site.zone==='frost'?frostElevation(site.x,site.z):townElevation(site.x,site.z));
    root.position.set(site.x,y,site.z);
    root.rotation.y=site.rotation||0;
    root.visible=false;
    root.userData.sceneryAsset=site.asset;
    root.userData.nonBlocking=true;
    groups[site.zone].add(root);
    items.set(site.id,root);
    return root;
  }

  function queue(asset){
    if(loading||models.has(asset)||failures.has(asset))return false;
    const filename=SCENERY_ASSETS[asset];if(!filename)return false;
    loading=true;
    loader.load(sceneryAssetPath(asset)+'?v='+encodeURIComponent(version),gltf=>{
      try{
        if(!gltf.scene)throw Error('GLB has no scene');
        models.set(asset,gltf.scene);
        for(const site of SCENERY_SITES.filter(s=>s.asset===asset))createOne(site,gltf.scene);
        onEvent('loaded',asset);
      }catch(err){failures.set(asset,String(err?.message||err));onEvent('failed',asset);}
      finally{loading=false;}
    },undefined,err=>{
      failures.set(asset,String(err?.message||err));
      onEvent('missing',asset); // Normal fallback is original map geometry.
      loading=false;
    });
    return true;
  }
  const dist=(s,x,z)=>Math.hypot(s.x-x,s.z-z);
  function update(zone,heroX,heroZ,now=0){
    activeZone=zone;
    groups.town.visible=zone==='town';groups.frost.visible=zone==='frost';
    if(zone!=='town'&&zone!=='frost')return;
    for(const site of SCENERY_SITES){
      const node=items.get(site.id);
      if(node)node.visible=site.zone===zone&&dist(site,heroX,heroZ)<site.near+45;
    }
    if(now-lastTick<0.45)return;
    lastTick=now;
    if(loading)return;
    const candidate=SCENERY_SITES.filter(s=>s.zone===zone&&
      !models.has(s.asset)&&!failures.has(s.asset)&&dist(s,heroX,heroZ)<s.near)
      .sort((a,b)=>dist(a,heroX,heroZ)-dist(b,heroX,heroZ))[0];
    if(candidate)queue(candidate.asset);
  }
  function status(){
    return {zone:activeZone,loaded:[...models.keys()],missing:Object.fromEntries(failures),
      visible:[...items].filter(([_,r])=>r.visible&&groups[activeZone]?.visible).map(([id])=>id)};
  }
  function dispose(){
    groups.town.removeFromParent();groups.frost.removeFromParent();
    // Models remain shared GLB cache; don't dispose shared materials from
    // player character assets. Clear only our own references.
    items.clear();models.clear();failures.clear();
  }
  return {groups,update,status,dispose};
}
