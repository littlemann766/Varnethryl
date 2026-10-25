import json
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
  b=p.chromium.launch(); pg=b.new_page(); pg.goto('http://localhost:8765/proto3d/scenery-viewer.html')
  r=pg.evaluate("""async()=>{const m=await import('./scenery.js');const C=m.CATALOG||{};const out={};
  for(const k in C)for(const n in C[k]){try{const v=m.makeVariant(k,n,C[k][n].pals[0],1,false);const l=m.makeVariant(k,n,C[k][n].pals[0],1,true);out[k+'/'+n]=[Math.round(v.tris),Math.round(l.tris),+v.h.toFixed(2)];}catch(e){out[k+'/'+n]=String(e)}}return out;}""")
  json.dump(r,open('variant_tris.json','w'),indent=0); print(r); b.close()
