#!/usr/bin/env python3
"""Doors + inside view (camera, roof fade, wall cut) for every hero size, sizes read from charscale.js (see heroscale.py).
Tiny/normal heroes (Pip, Phoenix, Wren, the Owner) walk in through the door and get the inside view; a giant that cannot fit
(taller than the building or wider than the door, per charscale) keeps the OUTSIDE view (roof and walls stay) wherever it stands.
usage: HEROES=pip,phoenix,wren,owner,troll,vaelthryx ONLY=inn,townhall,library,smithy python3 tools/hero_sizes_test.py"""
import http.server, threading, functools, os, sys, json, math
from playwright.sync_api import sync_playwright
import heroscale
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
fails = 0
def chk(n, c, x=''):
    global fails; print(('PASS ' if c else 'FAIL ') + n, x, flush=True); fails += 0 if c else 1
HEROES = os.environ.get('HEROES', 'pip,phoenix,wren,owner,troll,vaelthryx').split(',')
IDS = os.environ.get('ONLY', 'inn,townhall,library,smithy').split(',')
B = "(id=>{for(const e of __p3d.enterables)for(const b of(e.parts||[e]))if(b.id===id)return b})"
VS = "(id)=>{const b=" + B + "(id),v=b.viewState(),c=b.ctx.cam.position,s=__p3d.state;v.camD=Math.hypot(c.x-s.heroX,c.z-s.heroZ);v.camUp=c.y-(s.heroY||0);v.ins=s.inside;v.fit=b.K;return v}"
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']); pg = b.new_page(viewport={'width': 390, 'height': 844})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1&party=0&npcs=0'); pg.wait_for_function('window.__p3d && __p3d.frames>5', timeout=180000); pg.wait_for_timeout(1500)
    for hero in HEROES:
        prof = heroscale.apply(pg, hero); pg.wait_for_timeout(400)
        print('HERO', hero, json.dumps(prof), flush=True)
        for bid in IDS:
            bi = pg.evaluate("(id)=>{const b=" + B + "(id);const f=b.footprint?b.footprint.d/2:b.radius/b.K;return {out:b.toW(0,f+3.5),inn:b.toW(0,b.footprint?b.id_-1.4:0),mid:b.toW(0,0),rot:b.rot,h:b.h*b.K,dw:(b.DW||2.2)*b.K}}", bid)
            fits = not (prof['heightW'] > bi['h'] or 2 * prof['radiusW'] > bi['dw'])
            pg.evaluate("([s,t,r])=>{__p3d.teleport(s[0],s[1],0);__p3d.state.camYaw=r;__p3d.state.target={x:t[0],z:t[1]}}", [bi['out'], bi['inn'], bi['rot']])
            for _ in range(24):
                pg.wait_for_timeout(500)
                if pg.evaluate('__p3d.state.target===null'): break
            pg.wait_for_timeout(1500); v = pg.evaluate(VS, bid)
            tag = f"{hero:9s} {bid:9s} (h {prof['height']:.2f} m, fits={fits})"
            if fits:
                chk(tag + ' walks in through the door', v['ins'] == bid, str(v['ins']))
                chk(tag + ' inside view: roof faded out, upper floors hidden, camera near hero and above it', v['inside'] and not v['roofGroupVisible'] and v['roofShown'] is not True and not v['fading'] and all(not x for l, x in v['up'].items() if int(l) > 0) and v['camD'] < 40 and v['camUp'] > 0, json.dumps({k: v[k] for k in ('inside', 'roofShown', 'fading', 'up', 'camD', 'camUp')}))
            else:   # giant: put it in the middle of the building (it may not get through the door) -> still the outside view
                pg.evaluate("([p])=>__p3d.teleport(p[0],p[1],0)", [bi['mid']]); pg.wait_for_timeout(1500); v = pg.evaluate(VS, bid)
                chk(tag + ' giant keeps the outside view (roof + walls shown, no cutaway)', not v['inside'] and v['roofGroupVisible'] and v['roofShown'] is not False and all(o > .95 for o in v['sides'].values()), json.dumps({k: v[k] for k in ('inside', 'roofShown', 'sides', 'camD', 'camUp')}))
            pg.evaluate("([p])=>__p3d.teleport(p[0],p[1],0)", [bi['out']]); pg.wait_for_timeout(2500); o = pg.evaluate(VS, bid)
            chk(tag + ' outside again: roof restored', not o['inside'] and o['roofGroupVisible'] and o['roofShown'] is not False and not o['fading'], json.dumps({k: o[k] for k in ('inside', 'roofShown', 'roofGroupVisible', 'fading')}))
    pg.evaluate("__p3d.applyChar('')")
    chk('no page errors', not errs, str(errs[:3])); b.close()
print('FAILS', fails); sys.exit(1 if fails else 0)
