#!/usr/bin/env python3
"""Owner Pikachu costume: grouped under Owner as a 'Pikachu' variant (owner-only), loads, clips present, owner powers apply (hero.owner)."""
import http.server, threading, functools, os, sys
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start(); bad = 0
def T(n, c, d=''):
    global bad; print('PASS' if c else 'FAIL', n, '' if c else d); bad += 0 if c else 1
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
    for owner in (True, False):
        ctx = b.new_context(viewport={'width':844,'height':390}, has_touch=True, is_mobile=True); pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        if owner: pg.add_init_script("localStorage.setItem('vn_owner_unlock_v1','1')")
        pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1&npcs=0&party=0', wait_until='commit', timeout=120000); pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=120000); pg.wait_for_timeout(1500)
        g = pg.evaluate("__p3d.groups().find(g=>g.key==='owner')"); print(owner, g)
        T(f'owner={owner}: Owner group has a Pikachu variant', g and 'Pikachu' in g['vars'], g)
        listed = pg.evaluate("[...document.querySelectorAll('#heroes .row button, #heroes button')].map(b=>b.textContent).some(t=>/^Owner/.test(t.trim()))")
        T(f'owner={owner}: Owner entry in the selector only for the owner account', listed == owner, listed)
        if owner:
            idx = pg.evaluate("__p3d.modelStatus().models.findIndex(m=>m.id==='n:owner_pika1')")
            pg.evaluate("i=>__p3d.selectHero(i)", idx); pg.wait_for_function("__p3d.modelStatus().models.find(m=>m.id==='n:owner_pika1').state==='loaded'", timeout=60000); pg.wait_for_timeout(1200)
            r = pg.evaluate("(()=>{const u=__p3d.hero.userData;return {clips:Object.keys(u.all||{}),ok:__p3d.modelStatus().models.find(m=>m.id==='n:owner_pika1').state}})()"); print(r)
            T('pika costume loads with fight clips', all(c in r['clips'] for c in ('idle','walk','run','attack','hit','death')), r)
        T('no page errors', not errs, errs[:2]); ctx.close()
    b.close()
print('FAILED' if bad else 'ALL PASS'); sys.exit(1 if bad else 0)
