#!/usr/bin/env python3
"""Guild Hall is for playable characters only: the hero walks in through the door; companions (party) and townsfolk never end up inside,
they wait by the door and rejoin when the hero comes out. usage: python3 tools/guild_only_test.py"""
import http.server, threading, functools, os, sys
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
fails = 0
def chk(n, c, x=''):
    global fails; print(('PASS ' if c else 'FAIL ') + n, x, flush=True); fails += 0 if c else 1
G = "(()=>{const e=__p3d.enterables.find(q=>q.id==='guildhall');return e.parts?e.parts[0]:e})()"
INSIDE = "(()=>{const b=" + G + ";return __p3d.crowd.filter(r=>r.a&&b.insideTest(...b.toL(r.a.x,r.a.z))).map(r=>r.kind)})()"
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']); pg = b.new_page(viewport={'width': 390, 'height': 844})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1&party=2&npcs=1'); pg.wait_for_function('window.__p3d && __p3d.frames>5', timeout=180000); pg.wait_for_timeout(1500)
    chk('guild hall is hero-only', pg.evaluate("__heroOnly.has('guildhall')"))
    out = pg.evaluate("(()=>{const b=" + G + ";return [b.toW(0,b.d/2+3.5), b.toW(0,-1), b.rot]})()")
    pg.evaluate("([p])=>{__p3d.teleport(p[0],p[1],0);for(const r of __p3d.crowd)if(r.kind==='party'){r.a.x=p[0]+(Math.random()-.5)*2;r.a.z=p[1]+1.5;r.level=0}}", [out[0]]); pg.wait_for_timeout(1500)
    # hero walks straight in through the door (facing the building)
    pg.evaluate("([r])=>{__p3d.state.camYaw=r}", [out[2]]); pg.keyboard.down('w')
    try: pg.wait_for_function("__p3d.state.inside==='guildhall'", timeout=60000); ok = True
    except Exception: ok = False
    pg.keyboard.up('w'); chk('hero walks into the guild hall', ok, str(pg.evaluate("[__p3d.state.heroX,__p3d.state.heroZ,__p3d.state.inside]")))
    pg.evaluate("([p])=>{__p3d.teleport(p[0],p[1],0)}", [out[1]])   # deep inside
    worst = []
    for i in range(12):
        pg.wait_for_timeout(1000); ins = pg.evaluate(INSIDE); worst = ins if len(ins) > len(worst) else worst
    chk('no companion / townsfolk inside while the hero is in', len(worst) == 0, str(worst))
    near = pg.evaluate("(()=>{const b=" + G + ",w=b.toW(0,b.d/2+3.2);return __p3d.crowd.filter(r=>r.kind==='party').map(r=>+Math.hypot(r.a.x-w[0],r.a.z-w[1]).toFixed(1))})()")
    chk('companions wait by the door', all(d < 6 for d in near) and len(near) > 0, str(near))
    pg.evaluate("([p])=>{__p3d.teleport(p[0],p[1],0)}", [out[0]]); pg.wait_for_timeout(5000)
    d2 = pg.evaluate("__p3d.crowd.filter(r=>r.kind==='party').map(r=>+Math.hypot(r.a.x-__p3d.state.heroX,r.a.z-__p3d.state.heroZ).toFixed(1))")
    chk('companions rejoin the hero outside', all(d < 6 for d in d2), str(d2))
    chk('no page errors', not errs, str(errs[:3])); b.close()
print('FAILS', fails); sys.exit(1 if fails else 0)
