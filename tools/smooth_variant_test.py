#!/usr/bin/env python3
"""Smooth variants: offered as an extra 'Smooth' chip (originals stay default), load on demand, correct height, clips present."""
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
    b = p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']); pg = b.new_page(viewport={'width':844,'height':390}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1&npcs=0&party=0', wait_until='commit', timeout=120000); pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=120000); pg.wait_for_timeout(1500)
    gs = pg.evaluate("__p3d.groups().filter(g=>g.vars.includes('Smooth')).map(g=>g.key)"); T('16 heroes offer a Smooth chip', len(gs) == 16, gs)
    T('originals unchanged: Smooth is never the first/default variant', pg.evaluate("__p3d.groups().every(g=>g.vars[0]!=='Smooth')"))
    T('smooth models not loaded until picked (on demand)', pg.evaluate("__p3d.modelStatus().models.filter(m=>/_smooth/.test(m.id)&&m.state==='loaded').length") == 0)
    for n in ('aldric', 'nyx'):
        i = pg.evaluate("n=>__p3d.modelStatus().models.findIndex(m=>m.id==='n:'+n+'_smooth')", n); pg.evaluate("i=>__p3d.selectHero(i)", i)
        pg.wait_for_function("n=>__p3d.modelStatus().models.find(m=>m.id==='n:'+n+'_smooth').state==='loaded'", arg=n, timeout=60000); pg.wait_for_timeout(1000)
        r = pg.evaluate("(()=>{const u=__p3d.hero.userData;return {clips:Object.keys(u.all||{}),h:u.heightW}})()"); print(n, r)
        T(n + ' smooth loads with clips and ~hero height', all(c in r['clips'] for c in ('idle', 'walk')) and 2.0 < r['h'] < 3.4, r)
    T('no page errors', not errs, errs[:2]); b.close()
print('FAILED' if bad else 'ALL PASS'); sys.exit(1 if bad else 0)
