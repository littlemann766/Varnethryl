#!/usr/bin/env python3
"""4-frame walk-cycle strip for a few heroes (verifies baked GLB clips). usage: walk_strip.py out.png id1 id2 ..."""
import http.server, threading, os, sys, functools, io
from playwright.sync_api import sync_playwright
from PIL import Image
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
ids = sys.argv[2:]; out = sys.argv[1]; rows = []
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader']); pg = b.new_page(viewport={'width': 400, 'height': 600})
    for k in ids:
        row = Image.new('RGB', (1600, 600))
        for i, tt in enumerate((0, .25, .5, .75)):
            pg.goto(f'http://127.0.0.1:{port}/proto3d/viewer.html?c={k}&bare=1&spin=0&t=1&anim=walk&tt={tt}&yaw=1.2'); pg.wait_for_function('window.__ready'); pg.wait_for_timeout(500)
            row.paste(Image.open(io.BytesIO(pg.screenshot())).convert('RGB'), (i * 400, 0))
        rows.append(row.resize((1200, 450)))
    b.close()
s = Image.new('RGB', (1200, 450 * len(rows)));  [s.paste(r, (0, i * 450)) for i, r in enumerate(rows)]; s.save(out)
