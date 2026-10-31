#!/usr/bin/env python3
"""Pairwise footprint overlap check for the village buildings (rotated rects + margin). usage: MARGIN=1.5 python3 tools/spacing_check.py"""
import http.server, threading, functools, os, json, math
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
M = float(os.environ.get('MARGIN', '1.0'))
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']); pg = b.new_page()
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?party=0&npcs=0'); pg.wait_for_function('window.__p3d&&window.__p3d.frames>3', timeout=90000)
    bs = json.loads(pg.evaluate("JSON.stringify(__p3d.enterables.flatMap(e=>e.parts||[e]).filter(b=>b.footprint||b.radius).filter(b=>!/^(walls|wt|gt)/.test(b.id)).map(b=>({id:b.id,cx:b.cx,cz:b.cz,rot:b.rot,w:b.footprint?b.footprint.w*b.K:2*(b.radius||4),d:b.footprint?b.footprint.d*b.K:2*(b.radius||4),round:!b.footprint})))"))
    b.close()
def poly(o):
    c, s = math.cos(o['rot']), math.sin(o['rot']); hw, hd = o['w'] / 2 + M / 2, o['d'] / 2 + M / 2
    return [(o['cx'] + x * c + z * s, o['cz'] - x * s + z * c) for x, z in ((-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd))]
def axes(P): return [(-(P[(i+1)%4][1]-P[i][1]), P[(i+1)%4][0]-P[i][0]) for i in range(4)]
def hit(A, B):
    for ax in axes(A) + axes(B):
        pa = [x*ax[0]+z*ax[1] for x, z in A]; pb = [x*ax[0]+z*ax[1] for x, z in B]
        if max(pa) <= min(pb) or max(pb) <= min(pa): return False
    return True
n = 0
for i in range(len(bs)):
    for j in range(i+1, len(bs)):
        if hit(poly(bs[i]), poly(bs[j])): n += 1; print('OVERLAP', bs[i]['id'], bs[j]['id'], [round(bs[i]['w'],1), round(bs[i]['d'],1)], [round(bs[j]['w'],1), round(bs[j]['d'],1)])
print('overlaps', n)
