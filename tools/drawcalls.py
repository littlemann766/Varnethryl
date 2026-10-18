#!/usr/bin/env python3
"""Draw calls / triangles at several spots (renderer.info), usage: python3 tools/drawcalls.py"""
import http.server, threading, functools, os
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
R = "()=>{const r=__p3d.renderer;return JSON.stringify({calls:r.info.render.calls,tris:r.info.render.triangles})}"
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']); pg = b.new_page(viewport={'width': 390, 'height': 844})
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html'); pg.wait_for_function('window.__p3d && window.__p3d.frames>5', timeout=90000); pg.wait_for_timeout(1500)
    for n, pt, lv in [('spawn', None, 0), ('village centre', [0, 0], 0), ('guildhall', [0, -14], 0), ('colosseum', [42, 50], 0), ('keep', [0, -40], 0), ('port', [-45, 36], 0), ('inn upstairs', [24, -3], 1)]:
        if pt: pg.evaluate("([x,z,l])=>__p3d.teleport(x,z,l)", [*pt, lv])
        pg.wait_for_timeout(1500); print(n, pg.evaluate(R))
    b.close()
