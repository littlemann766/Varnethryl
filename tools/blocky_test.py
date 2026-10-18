#!/usr/bin/env python3
"""Blocky-default test: every character with a builder shows its blocky body by default, toggles to GLB and back without a size jump."""
import http.server, threading, functools, os
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
H = """async(i)=>{const P=__p3d;await P.selectHero(i);await new Promise(r=>setTimeout(r,200));const h=P.hero,T=P.THREE;h.updateMatrixWorld(true);
 let mn=1e9,mx=-1e9;h.traverse(o=>{if(!(o.isMesh&&o.geometry)||o.userData.isGhost)return;let b;if(o.isSkinnedMesh){o.skeleton.update();o.computeBoundingBox();b=o.boundingBox}else{o.geometry.computeBoundingBox();b=o.geometry.boundingBox}if(!b)return;
  for(const y of[b.min.y,b.max.y]){const v=new T.Vector3(0,y,0).applyMatrix4(o.matrixWorld);if(isFinite(v.y)){mn=Math.min(mn,v.y);mx=Math.max(mx,v.y)}}});
 return {blocky:!!h.userData.blocky,glb:!!h.userData.glb,h:+(mx-mn).toFixed(2)}}"""
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']); pg = b.new_page(viewport={'width':390,'height':760}, has_touch=True)
    errs=[]; pg.on('pageerror', lambda e: errs.append(str(e))); pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1'); pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=90000)
    ids = pg.evaluate("__p3d.modelStatus().models.map(m=>[m.id,m.mode])"); bad=[]; n=0
    for i,(id,mode) in enumerate(ids):
        if mode!='blocky': continue
        n+=1; a=pg.evaluate(H,i); pg.evaluate(f"__p3d.toggleModel({i})"); pg.wait_for_timeout(2500); g=pg.evaluate(H,i)
        pg.evaluate(f"__p3d.toggleModel({i})"); pg.wait_for_timeout(500); c=pg.evaluate(H,i)
        ok = a['blocky'] and g['glb'] and not g['blocky'] and c['blocky'] and abs(a['h']-g['h'])/max(a['h'],.1)<0.35
        print(('ok ' if ok else 'BAD'), id, 'blocky', a, 'glb', g)
        if not ok: bad.append(id)
    print('blocky chars', n, 'bad', bad, 'errs', errs[:3]); print('PASS' if n>=40 and not bad and not errs else 'FAIL'); b.close()
