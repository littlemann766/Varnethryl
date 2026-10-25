import json,time,sys
from playwright.sync_api import sync_playwright
MAP={'house1':'bld_house1','house2':'bld_house2','house3':'bld_house3','house4':'bld_house4','farmhouse':'bld_farmhouse','barn':'bld_barn','stables':'bld_stables','windmill':'bld_windmill','lighthouse':'bld_lighthouse','gt0':'bld_gate_tower','thieves':'bld_thieves'}
only=sys.argv[1].split(',') if len(sys.argv)>1 else list(MAP)
with sync_playwright() as p:
  b=p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);pg=b.new_page(viewport={'width':800,'height':600})
  pg.on('pageerror',lambda e:print('ERR',e));pg.on('console',lambda m:print('C',m.text) if m.type=='error' else None)
  pg.goto('http://localhost:8765/proto3d/bldview.html');pg.wait_for_function('window.__ready',timeout=120000);pg.evaluate('__size(800,600)')
  out={}
  for i in only:
    r=pg.evaluate("""async([id,f])=>{const {GLTFLoader}=await import('./vendor/jsm/loaders/GLTFLoader.js');const s=__sub(id);
      if(!s.__beth){const g=await new GLTFLoader().loadAsync('models/beth/buildings/'+f+'.glb');for(const k of ['roof','walls','frame'])s.G[k].visible=false;s.G.ext.children.forEach(m=>{if(m.isMesh&&m.material.map)m.visible=false});s.root.children.forEach(c=>{if(!Object.values(s.G).includes(c)&&c!==g.scene)c.visible=false});
        g.scene.scale.setScalar(1/s.K);g.scene.traverse(o=>{if(o.isMesh){o.castShadow=o.receiveShadow=true;}});s.root.add(g.scene);s.__beth=g.scene;}
      const calls=__show(id,/windmill|lighthouse|gt0/.test(id)?{dist:42,ty:8}:{});const ri=__rinfo();let m=0,t=0;s.__beth.traverse(o=>{if(o.isMesh){m++;t+=o.geometry.index.count/3}});return {calls,tris:ri.tri,bethMeshes:m,bethTris:t};}""",[i,MAP[i]])
    out[i]=r;print(i,r)
    pg.screenshot(path=f'bld_after_{i}_front.png');pg.evaluate("id=>__show(id,/windmill|lighthouse|gt0/.test(id)?{yaw:0.8,dist:42,ty:8}:{yaw:0.8})",i);pg.screenshot(path=f'bld_after_{i}_34.png')
  json.dump(out,open('bld_after.json' if len(sys.argv)<2 else '/tmp/bld_after_part.json','w'),indent=1);b.close()
