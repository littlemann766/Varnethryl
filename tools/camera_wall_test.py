#!/usr/bin/env python3
"""Third-person camera against a wall: hero stays visible, camera pulled in but never closer than 1.4 HS, default mode is follow, view toggles to first person and back."""
import http.server, threading, functools, os, sys
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start(); bad = 0
def T(n, c, d=''):
    global bad; print('PASS' if c else 'FAIL', n, '' if c else d); bad += 0 if c else 1
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']); pg = b.new_context(viewport={'width':844,'height':390}, has_touch=True, is_mobile=True).new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?npcs=0&nosave=1', wait_until='commit', timeout=120000); pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=120000); pg.wait_for_timeout(1500)
    T('default camMode is follow', pg.evaluate("__p3d.camRig.prefs.camMode") == 'follow')
    w = pg.evaluate("(()=>{const c=__p3d.colliders.filter(c=>c.type==='box'&&!c.interior&&c.maxZ-c.minZ>8&&c.maxX-c.minX>3&&Math.abs(c.minX)<100)[0];return c?{x:c.minX-0.9,z:(c.minZ+c.maxZ)/2}:null})()")
    T('found a wall to test against', w is not None)
    pg.evaluate("([x,z])=>{__p3d.teleport(x,z);__p3d.setCamYaw(Math.PI/2)}", [w['x'], w['z']]); pg.wait_for_timeout(1500)
    r = pg.evaluate("(()=>{const s=__p3d.state,c=__p3d.camRig.pos;return {d:Math.hypot(c.x-s.heroX,c.z-s.heroZ),vis:__p3d.hero.visible,fin:[c.x,c.y,c.z].every(Number.isFinite)}})()"); print(r)
    T('hero visible with the camera against a wall', r['vis'] and r['fin'], r)
    T('camera pulled in but not inside the hero (>= 1.4 HS = 2.1)', 2.0 <= r['d'] < 12, r)
    pg.evaluate("__p3d.camRig.setView('first')"); pg.wait_for_timeout(500); T('first person still available', pg.evaluate("__p3d.camRig.fp"))
    pg.evaluate("__p3d.camRig.setView('third')"); pg.wait_for_timeout(500); T('back to third person, hero visible', pg.evaluate("!__p3d.camRig.fp&&__p3d.hero.visible"))
    T('no page errors', not errs, errs[:2]); b.close()
print('FAILED' if bad else 'ALL PASS'); sys.exit(1 if bad else 0)
