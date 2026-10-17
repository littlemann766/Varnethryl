#!/usr/bin/env python3
"""Build the 11 hero GLBs headlessly: serves www/, runs www/proto3d/export.html in Chromium, writes www/proto3d/models/*.glb"""
import base64, http.server, threading, os, sys, functools
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a,**k): pass
h = functools.partial(Q, directory=ROOT)
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), h); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
out = os.path.join(ROOT, 'proto3d', 'models'); os.makedirs(out, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader']); pg = b.new_page()
    pg.on('console', lambda m: print('console:', m.text) if m.type in ('error', 'warning') else None); pg.on('pageerror', lambda e: print('PAGEERR', e))
    pg.goto(f'http://127.0.0.1:{port}/proto3d/export.html'); pg.wait_for_function('window.ready===true', timeout=30000)
    ids = sys.argv[1:] or pg.evaluate('window.ORDER')
    for i in ids:
        data = pg.evaluate('id=>window.exportOne(id)', i); raw = base64.b64decode(data)
        open(os.path.join(out, i + '.glb'), 'wb').write(raw); print(i, len(raw) // 1024, 'KB')
    b.close()
