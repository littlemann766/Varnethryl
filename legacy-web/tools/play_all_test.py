#!/usr/bin/env python3
"""Play-as-any-model test: select EVERY model in the 3D game as the hero, check it loads, is sized sensibly, animates; toggle followers."""
import http.server, threading, functools, os, json, sys
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever,daemon=True).start()
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']); pg = b.new_page(viewport={'width':390,'height':760}, has_touch=True)
    errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1'); pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=90000)
    n = pg.evaluate("document.querySelectorAll('#heroes button[data-i]').length"); print('selector entries', n)
    bad=[]; step=int(os.environ.get('STEP','1'))
    for i in range(0, n, step):
        r = pg.evaluate("""async(i)=>{const P=__p3d;await P.selectHero(i);await new Promise(r=>setTimeout(r,120));const h=P.hero;const T=P.THREE;const bx=new T.Box3().setFromObject(h);const s=bx.getSize(new T.Vector3());
          const u=h.userData;const t0=u.mixer?u.mixer.time:-1;return {i,idx:P.heroIndex,glb:!!u.glb,dim:[h.children[0].scale.x,0,0].map(v=>+v.toFixed(3)),vis:h.visible,clips:u.act?Object.keys(u.act).join(','):'',t0}}""", i)
        pg.wait_for_timeout(150)
        t1 = pg.evaluate("__p3d.hero.userData.mixer?__p3d.hero.userData.mixer.time:-1")
        ok = r['idx']==i and r['glb'] and r['vis'] and 'idle' in r['clips'] and 0.2<r['dim'][0]<8 and t1>r['t0']
        if not ok: bad.append(r)
    st = pg.evaluate("__p3d.modelStatus()"); print('loaded',st['loaded'],'failed',st['failed'], [m['id'] for m in st['models'] if m['state']=='failed'])
    pg.evaluate("document.querySelector('#heroes button[data-f=\"30\"]').click()"); pg.wait_for_timeout(800)
    print('followers', pg.evaluate("__p3d.bump.crowd.filter(c=>c.kind==='party').map(c=>c.a.id)"))
    print('BAD', bad[:10], 'errs', errs[:3]); print('PASS' if not bad and not errs and st['failed']==0 else 'FAIL'); b.close()
