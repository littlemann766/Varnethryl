#!/usr/bin/env python3
"""Screenshots of the full village page at fixed spots: python3 tools/village_shots.py <www-root> <outdir>  (use to compare before/after optimisations)"""
import http.server, threading, functools, sys, os
from playwright.sync_api import sync_playwright
ROOT, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
SPOTS = [('centre', 0, 0, 0), ('keep', 0, -38, 0), ('inn', 24, 0, 0), ('inn_up', 24, -3, 1), ('port', -45, 34, 0), ('temple', 46, -2, 0), ('gate', 0, 52, 0)]
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']); pg = b.new_page(viewport={'width': 900, 'height': 600})
    pg.on('pageerror', lambda e: print('ERR', e))
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html'); pg.wait_for_function('window.__p3d && window.__p3d.frames>5', timeout=120000); pg.wait_for_timeout(2500)
    for n, x, z, l in SPOTS:
        pg.evaluate("([x,z,l])=>__p3d.teleport(x,z,l)", [x, z, l]); pg.wait_for_timeout(2500); pg.screenshot(path=f'{OUT}/{n}.png')
    b.close()
