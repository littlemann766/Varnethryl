import time,json,sys
from playwright.sync_api import sync_playwright
SP=json.load(open('spots.json'));res={}
JS="""()=>{const P=window.__P,r=P.renderer;const isL=o=>o.isMesh&&((o.parent&&o.parent.name==='town-landscaped-outskirts'&&!o.name&&o.userData.keep&&o.material&&(o.material.name==='beth_kit_atlas'||o.material.map))||o.name==='beth-town-trees'||(o.isInstancedMesh&&!o.name&&(o.geometry.type==='ConeGeometry'||o.geometry.type==='CylinderGeometry')&&o.count>200));
 const L=[];P.scene.traverse(o=>{if(isL(o))L.push(o)});const vis=L.map(o=>o.visible);
 r.render(P.scene,P.camera);const c=r.info.render.calls,t=r.info.render.triangles;L.forEach(o=>o.visible=false);r.render(P.scene,P.camera);const c2=r.info.render.calls,t2=r.info.render.triangles;L.forEach((o,i)=>o.visible=vis[i]);
 return {total_calls:c,total_tris:t,landscape_calls:c-c2,landscape_tris:t-t2,meshes:L.length};}"""
with sync_playwright() as p:
  for tag,url in [('before','http://localhost:8766/proto3d/index.html'),('after','http://localhost:8765/proto3d/index.html')]:
    b=p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);pg=b.new_page(viewport={'width':960,'height':540})
    pg.goto(url);pg.wait_for_function('window.__P&&window.__P.renderer.info.render.frame>3',timeout=180000);time.sleep(3)
    pg.get_by_text('Play Solo').click(timeout=5000);time.sleep(12);res[tag]={}
    for s in SP:
      pg.evaluate("s=>{const P=window.__P;window.__PV_HOOK=()=>{P.state.heroX=s.x;P.state.heroZ=s.z}}",s);time.sleep(4)
      res[tag][s['id']]=pg.evaluate(JS);print(tag,s['id'],res[tag][s['id']])
    b.close()
json.dump(res,open('landscape_cost.json','w'),indent=1)
