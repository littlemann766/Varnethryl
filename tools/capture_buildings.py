#!/usr/bin/env python3
"""Finished-quality captures: 1500x1000, shadows+textures settled (multiple frames + waits), ext/side/back/int + one image per upper level.
usage: ONLY=id,id python3 tools/capture_buildings.py [outdir]"""
import http.server, threading, os, sys, functools, json
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www'); OUT = sys.argv[1] if len(sys.argv) > 1 else '/workspace/shots/buildings'
os.makedirs(OUT, exist_ok=True)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
IDS = os.environ.get('ONLY', '').split(',') if os.environ.get('ONLY') else None
W, H = 1500, 1000
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']); pg = b.new_page(viewport={'width': W, 'height': H})
    pg.on('pageerror', lambda e: print('PAGEERR', e)); pg.on('console', lambda m: print('c:', m.text) if m.type == 'error' else None)
    pg.goto(f'http://127.0.0.1:{port}/proto3d/bldview.html' + ('?b=' + ','.join(IDS) if IDS else '')); pg.wait_for_function('window.__ready', timeout=180000)
    pg.evaluate(f'__size({W},{H})'); pg.wait_for_timeout(1500)
    def shot(i, call, path):
        for _ in range(4): pg.evaluate(call); pg.wait_for_timeout(350)     # settle: shadow map + textures + materials compiled
        pg.screenshot(path=path)
    for i in pg.evaluate('window.__list'):
        if IDS and i not in IDS: continue
        shots = [('ext', '{yaw:0.55,pitch:0.28}'), ('side', '{yaw:-1.05,pitch:0.22}'), ('back', '{yaw:2.6,pitch:0.3}'), ('int', '{inside:true,pitch:1.0}')]
        for n, a in shots:
            call = f"(()=>{{const a={a}; if(a.inside) a.dist=__r('{i}')*1.35; return __show('{i}',a)}})()"
            shot(i, call, f'{OUT}/{i}_{n}.png')
        lv = pg.evaluate(f"(()=>{{const s=__sub('{i}');return Array.from(new Set((s.floors||[]).map(f=>f.level)))}})()")
        for l in lv:
            fy = pg.evaluate(f"(()=>{{const s=__sub('{i}');return s.floors.find(f=>f.level=={l}).y}})()")
            call = f"__show('{i}',{{inside:true,level:{l},pitch:1.05,dist:__r('{i}')*1.3,ty:{fy}}})"
            shot(i, call, f'{OUT}/{i}_up{l}.png')
        print(i, 'done levels', lv, pg.evaluate("__rinfo().calls"))
    b.close()
