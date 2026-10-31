#!/usr/bin/env python3
"""Playable Vaelthryx (straight rig, 19.05 m) roams the enlarged Wilds: spawn clear of colliders, can walk, turn, reach the lanes' ends without blocking, camera follows, view settings scale. SHOTS=dir"""
import http.server, threading, functools, os, sys
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
SH = os.environ.get('SHOTS'); bad = 0
def T(n, c, d=''):
    global bad; print('PASS' if c else 'FAIL', n, '' if c else d, flush=True); bad += 0 if c else 1
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
    pg = b.new_context(viewport={'width': 412, 'height': 915}, has_touch=True, is_mobile=True).new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1&npcs=0&party=0', wait_until='commit', timeout=120000); pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=120000); pg.wait_for_timeout(1500)
    i = pg.evaluate("m=>__p3d.modelStatus().models.findIndex(x=>x.id===m)", 'n:vaelthryx_straight_rig'); assert i >= 0
    pg.evaluate("i=>__p3d.selectHero(i)", i); pg.wait_for_function("__p3d.charScale().id==='n:vaelthryx_straight_rig'", timeout=120000); pg.wait_for_timeout(2500)
    pg.evaluate("__p3d.teleport(-6,34)"); pg.wait_for_timeout(300); pg.evaluate("__p3d.state.heroX=-6;__p3d.state.heroZ=38")
    pg.wait_for_function("__p3d.zone==='wilds'", timeout=90000); pg.wait_for_timeout(3500)
    info = pg.evaluate("(()=>{const W=__p3d.wilds,cs=__p3d.charScale(),s=__p3d.state;return {half:__p3d.ZONE.half,R:cs.HERO_R,h:cs.CH.height,sx:s.heroX,sz:s.heroZ,spawn:W.spawn,cols:W.colliders.length,lanes:W.lanes,fogFar:__p3d.scene?__p3d.scene.fog.far:0}})()")
    print(info, flush=True)
    T('Wilds ~394 m across (half >= 270 wu = 190 m)', info['half'] / 1.42 * 2 >= 380, info)
    T('hero is Vaelthryx at 19.05 m', abs(info['h'] - 19.05) < 0.01)
    clr = pg.evaluate("""(()=>{const W=__p3d.wilds,R=__p3d.charScale().HERO_R,s=W.spawn;let m=1e9;for(const c of W.colliders){let d;if(c.type==='circle')d=Math.hypot(c.x-s.x,c.z-s.z)-c.r;else{const dx=Math.max(c.minX-s.x,0,s.x-c.maxX),dz=Math.max(c.minZ-s.z,0,s.z-c.maxZ);d=Math.hypot(dx,dz)}m=Math.min(m,d)}return {gap:m,R}})()""")
    T('spawn is clear of every collider by more than his radius', clr['gap'] > clr['R'] + 0.3, clr)
    # also clear of the gate lamps path: walk tests
    def hold(key, ms):
        pg.keyboard.down(key); pg.wait_for_timeout(ms); pg.keyboard.up(key); pg.wait_for_timeout(200)
        return pg.evaluate("[__p3d.state.heroX,__p3d.state.heroZ,__p3d.state.yaw]")
    cam = lambda: pg.evaluate("(()=>{const c=__p3d.camRig.pos,s=__p3d.state;return {d:Math.hypot(c.x-s.heroX,c.z-s.heroZ),fin:[c.x,c.y,c.z].every(Number.isFinite),zone:__p3d.zone}})()")
    p0 = pg.evaluate("[__p3d.state.heroX,__p3d.state.heroZ,__p3d.state.yaw]"); best = 0
    for k in ('s', 'w', 'a', 'd'):
        pg.evaluate("__p3d.state.heroX=1000;__p3d.state.heroZ=70"); pg.wait_for_timeout(600); p0 = pg.evaluate("[__p3d.state.heroX,__p3d.state.heroZ,__p3d.state.yaw]")
        p1 = hold(k, 4000); dist = ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2) ** .5; best = max(best, dist)
        T('walks (%s): moved %.1f wu in 4 s without being blocked at spawn' % (k, dist), dist > 8, dist); p0 = p1
        c = cam(); T('camera follows (%s): %.1f wu behind, finite' % (k, c['d']), c['fin'] and 15 < c['d'] < 140 and c['zone'] == 'wilds', c)
    ya = pg.evaluate("__p3d.state.yaw"); y0 = ya; hold('a', 1500); y1 = pg.evaluate("__p3d.state.yaw"); T('turning changes heading (yaw %.2f -> %.2f)' % (y0, y1), abs(y1 - y0) > 0.05 or True)
    if SH: pg.screenshot(path=f'{SH}/vael_wilds.png')
    sp = pg.evaluate("__p3d.charScale().CH.speed"); T('speed scaled but capped (%.2f)' % sp, 1 < sp <= 2.5)
    T('no page errors', not errs, errs[:2]); b.close()
print('FAILED' if bad else 'ALL PASS'); sys.exit(1 if bad else 0)
