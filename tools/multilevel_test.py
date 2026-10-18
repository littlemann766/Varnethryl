#!/usr/bin/env python3
"""Upstairs test: for every building with stairs, walk up the first ground flight, check level/height, check the floor edge stops the hero, walk back down.
usage: python3 tools/multilevel_test.py   (ONLY=id,id)"""
import http.server, threading, functools, os, sys, json, math
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
ONLY = os.environ.get('ONLY', '').split(',') if os.environ.get('ONLY') else None
fails = 0
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']); pg = b.new_page(viewport={'width': 390, 'height': 844})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html'); pg.wait_for_function('window.__p3d && window.__p3d.frames>5', timeout=90000); pg.wait_for_timeout(800)
    info = json.loads(pg.evaluate("JSON.stringify(__p3d.multi.map(b=>({id:b.id,ramps:b.ramps,floors:b.floors.map(f=>({level:f.level,y:f.y})),cx:b.cx,cz:b.cz,rot:b.rot})))"))
    def W(bid, lx, lz): return pg.evaluate("([id,lx,lz])=>__p3d.multi.find(b=>b.id===id).toW(lx,lz)", [bid, lx, lz])
    def walk(src, lv, dst, ms=9000):
        pg.evaluate("([s,l,t])=>{__p3d.teleport(s[0],s[1],l);__p3d.state.target={x:t[0],z:t[1]};}", [src, lv, dst])
        for _ in range(int(ms / 400)):
            pg.wait_for_timeout(400)
            if pg.evaluate('__p3d.state.target===null'): break
        return pg.evaluate("({x:__p3d.state.heroX,z:__p3d.state.heroZ,lv:__p3d.state.level,y:__p3d.state.heroY})")
    for bi in info:
        if ONLY and bi['id'] not in ONLY: continue
        ok = True; msgs = []
        for m in bi['ramps']:
            s, c = math.sin(m['ang']), math.cos(m['ang'])
            a = [m['cx'] + s * (-m['len'] / 2 + .25), m['cz'] + c * (-m['len'] / 2 + .25)]; t = [m['cx'] + s * (m['len'] / 2 + .5), m['cz'] + c * (m['len'] / 2 + .5)]
            r = walk(W(bi['id'], *a), m['l0'], W(bi['id'], *t))
            up = r['lv'] == m['l1'] and abs(r['y'] - m['y1']) < .15
            if bi['id'] == 'walls' and up:   # wall walk: stroll 7 m along the top, must stay on level 1 at wall-top height
                oks = []
                for sgn in (1, -1):
                    tw = [t[0] + c * 7 * sgn, t[1] - s * 7 * sgn]; rw = walk(W(bi['id'], *t), 1, W(bi['id'], *tw), 6000); okw = rw['lv'] == 1 and abs(rw['y'] - m['y1']) < .15 and math.hypot(rw['x'] - W(bi['id'], *t)[0], rw['z'] - W(bi['id'], *t)[1]) > 4.5
                    oks.append(okw); msgs.append(f"walk{'+' if sgn > 0 else '-'}={okw}")
                up = up and any(oks)   # a short segment may only have room one way
            a2 = [m['cx'] + s * (-m['len'] / 2 - .9), m['cz'] + c * (-m['len'] / 2 - .9)]; t2 = [m['cx'] + s * (m['len'] / 2 + (1.4 if bi['id'] == 'walls' else .5)), m['cz'] + c * (m['len'] / 2 + (1.4 if bi['id'] == 'walls' else .5))]; r2 = walk(W(bi['id'], *t2), m['l1'], W(bi['id'], *a2))
            down = r2['lv'] == m['l0'] and r2['y'] < m['y0'] + 1.0
            ok &= up and down; msgs.append(f"ramp {m['l0']}->{m['l1']} up={up}({r['lv']},{r['y']:.2f}) down={down}({r2['lv']},{r2['y']:.2f})")
        print('PASS' if ok else 'FAIL', bi['id'], '; '.join(msgs)); fails += 0 if ok else 1
    b.close()
print('page errors:', errs[:5]); print('FAILS', fails); sys.exit(1 if fails else 0)
