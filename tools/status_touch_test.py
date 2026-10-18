#!/usr/bin/env python3
"""Touch test: tapping '3D status' opens a readable panel (model list/size/build); roster has Darius+Selene."""
import http.server, threading, functools, os
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
    pg = b.new_page(viewport={'width':390,'height':844}, has_touch=True, is_mobile=True); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html'); pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=90000); pg.wait_for_timeout(4000)
    r = pg.evaluate("(()=>{const e=document.getElementById('diagBtn').getBoundingClientRect();const t=document.elementFromPoint(e.x+e.width/2,e.y+e.height/2);return [e.x+e.width/2,e.y+e.height/2,t&&t.id]})()"); print('btn', r)
    pg.touchscreen.tap(r[0], r[1]); pg.wait_for_timeout(600)
    vis = pg.evaluate("(()=>{const d=document.getElementById('diag');return d&&getComputedStyle(d).display!=='none'?d.innerText:''})()")
    print(vis[:600]); ok = 'darius' in vis.lower() and 'build' in vis.lower()
    print('heroes', pg.evaluate("[...document.querySelectorAll('#heroes button')].map(b=>b.title)"), 'hero', pg.evaluate("__p3d.heroIndex"), 'follow', pg.evaluate("__p3d.bump.crowd.length"))
    print('errs', errs); print('PASS' if ok and not errs else 'FAIL'); b.close()
