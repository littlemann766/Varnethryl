import json,sys,time
from playwright.sync_api import sync_playwright
url=sys.argv[1]
with sync_playwright() as p:
  b=p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);pg=b.new_page(viewport={'width':960,'height':540})
  pg.goto(url);pg.wait_for_function('window.__P&&window.__P.renderer.info.render.frame>3',timeout=180000);time.sleep(3)
  r=pg.evaluate("""()=>{const out={};window.__P.scene.traverse(o=>{if(!o.isMesh)return;const g=o.geometry;const t=(g.index?g.index.count:g.attributes.position.count)/3*(o.isInstancedMesh?o.count:1);
   let ch=[],p=o;while(p){if(p.name)ch.push(p.name);p=p.parent;}const k=(ch.slice(0,2).join('<')||'anon')+'|'+o.material.type+'|'+(o.material.name||'')+(o.material.map?'|map':'');
   const a=out[k]=out[k]||[0,0];a[0]++;a[1]+=Math.round(t);});return out;}""")
  for k,v in sorted(r.items(),key=lambda kv:-kv[1][1])[:40]:print(v,k)
  b.close()
