#!/usr/bin/env python3
"""Render exterior (front 3/4, side/back) + interior (cutaway, from above) PNGs per building via www/proto3d/bldview.html.
usage: render_buildings.py [outdir]   (ONLY=id,id limits; the sheet-vs-3D comparison is tools/compare_buildings.py)"""
import http.server, threading, os, sys, functools, json
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www'); OUT = sys.argv[1] if len(sys.argv) > 1 else '/workspace/shots/buildings'
os.makedirs(OUT, exist_ok=True)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
IDS = os.environ.get('ONLY', '').split(',') if os.environ.get('ONLY') else None
W, H = 900, 640
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']); pg = b.new_page(viewport={'width': W, 'height': H})
    pg.on('pageerror', lambda e: print('PAGEERR', e)); pg.on('console', lambda m: print('c:', m.text) if m.type == 'error' else None)
    pg.goto(f'http://127.0.0.1:{port}/proto3d/bldview.html' + ('?b=' + ','.join(IDS) if IDS else '')); pg.wait_for_function('window.__ready', timeout=180000)
    pg.evaluate(f'__size({W},{H})'); info = {}
    for i in pg.evaluate('window.__list'):
        if IDS and i not in IDS: continue
        shots = [('ext', '{yaw:0.55,pitch:0.28}'), ('side', '{yaw:-1.05,pitch:0.22}'), ('back', '{yaw:2.6,pitch:0.3}'), ('int', '{inside:true,pitch:1.0,dist:0}')]
        for n, a in shots:
            calls = pg.evaluate(f"(()=>{{const a={a}; if(a.inside) a.dist=__r('{i}')*1.35; return __show('{i}',a)}})()")
            pg.wait_for_timeout(120); pg.screenshot(path=f'{OUT}/{i}_{n}.png')
            if n == 'ext': info[i] = {'draw_calls': calls}
        info[i].update(pg.evaluate(f"__info('{i}')")); print(i, info[i])
    json.dump(info, open(f'{OUT}/stats.json', 'w'), indent=1); b.close()
