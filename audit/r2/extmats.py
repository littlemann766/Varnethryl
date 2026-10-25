from playwright.sync_api import sync_playwright
import json,sys
with sync_playwright() as p:
  b=p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);pg=b.new_page()
  pg.goto('http://localhost:8765/proto3d/bldview.html');pg.wait_for_function('window.__ready',timeout=120000)
  for id in sys.argv[1].split(','):
    r=pg.evaluate("""id=>{const s=__sub(id);const out=[];for(const k of ['ext','roof']){s.G[k].children.forEach(m=>{if(!m.isMesh)return;const G=m.geometry;G.computeBoundingBox();const bb=G.boundingBox;
      out.push([k,m.material.name||'',m.material.color?m.material.color.getHexString():'',!!m.material.map,Math.round((G.index?G.index.count:G.attributes.position.count)/3),bb.min.toArray().map(v=>+v.toFixed(1)),bb.max.toArray().map(v=>+v.toFixed(1))])})}return out}""",id)
    print(id);[print('  ',x) for x in r]
  b.close()
