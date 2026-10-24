import json,sys,time
from playwright.sync_api import sync_playwright
import os
SPOTS=json.load(open(os.environ.get('SPOTS','/workspace/beth-world/audit/spots.json')))
tag=sys.argv[1]; url=sys.argv[2] if len(sys.argv)>2 else 'http://localhost:8765/proto3d/index.html'
JS_PROF="""()=>{const P=window.__P,s=P.scene,r=P.renderer,cam=P.camera;cam.updateMatrixWorld();
const fr=new P.THREE.Frustum().setFromProjectionMatrix(new P.THREE.Matrix4().multiplyMatrices(cam.projectionMatrix,cam.matrixWorldInverse));
const out=[];s.traverseVisible(o=>{if(!o.isMesh)return;const g=o.geometry;if(!g.boundingSphere)g.computeBoundingSphere();
let vis=true;if(o.frustumCulled!==false&&!o.isInstancedMesh){const bs=g.boundingSphere.clone().applyMatrix4(o.matrixWorld);vis=fr.intersectsSphere(bs);}
const t=(g.index?g.index.count:g.attributes.position.count)/3*(o.isInstancedMesh?o.count:1);
let n=o.name,p=o.parent;while(!n&&p){n=p.name;p=p.parent;}
const mc=o.material&&o.material.color?o.material.color.getHexString():'';out.push({n:n||('anon:'+g.type+':'+mc+(o.isInstancedMesh?':inst':'')),t:Math.round(t),vis,inst:o.isInstancedMesh?o.count:0,mat:(Array.isArray(o.material)?o.material.length:1),mt:(o.material.type||'')});});
return {calls:r.info.render.calls,tris:r.info.render.triangles,meshes:out};}"""
with sync_playwright() as p:
  b=p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
  pg=b.new_page(viewport={'width':960,'height':540})
  pg.on('pageerror',lambda e:print('ERR',str(e)[:200]))
  pg.goto(url); pg.wait_for_function('window.__P&&window.__P.renderer.info.render.frame>3',timeout=180000)
  time.sleep(4)
  try:
    pg.get_by_text('Play Solo').click(timeout=5000)
  except Exception as e: print('noclick',e)
  time.sleep(12)
  for el in ['#loader','#vn-loader','.loader']: pg.evaluate(f"()=>{{const e=document.querySelector('{el}');if(e)e.style.display='none'}}")
  pl=pg.evaluate('()=>window.__BETH_PLACED||null')
  if pl is not None: json.dump(pl,open(f'/workspace/beth-world/audit/{tag}_placed.json','w'))
  res={}
  pg.evaluate("()=>document.querySelectorAll('body > div').forEach(d=>{if(!d.querySelector('canvas'))d.style.visibility='hidden'})") if os.environ.get('NOHUD') else None
  for sp in SPOTS:
    pg.evaluate("""s=>{const P=window.__P;P.state.heroX=s.x;P.state.heroZ=s.z;P.state.yaw=s.yaw||0;P.state.camYaw=s.yaw||0;
      window.__PV_HOOK=()=>{P.state.heroX=s.x;P.state.heroZ=s.z;if(s.cam){P.camera.position.set(...s.cam);P.camera.lookAt(...s.look);}}}""",sp)
    time.sleep(4)
    pr=pg.evaluate(JS_PROF)
    pg.screenshot(path=f"/workspace/beth-world/audit/{tag}_{sp['id']}.png")
    agg={}
    for m in pr['meshes']:
      if not m['vis']:continue
      a=agg.setdefault(m['n'],[0,0]);a[0]+=1;a[1]+=m['t']
    top=sorted(agg.items(),key=lambda kv:-kv[1][1])[:25]
    res[sp['id']]={'calls':pr['calls'],'tris':pr['tris'],'visMeshes':sum(1 for m in pr['meshes'] if m['vis']),'top':top}
    print(sp['id'],pr['calls'],pr['tris'])
  json.dump(res,open(f'/workspace/beth-world/audit/{tag}_profile'+os.environ.get('SFX','')+'.json','w'),indent=1)
  b.close()
