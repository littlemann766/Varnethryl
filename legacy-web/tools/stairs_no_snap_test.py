#!/usr/bin/env python3
"""Floors never change by force: with the hero on an upper floor, a follower far away on the ground floor must NOT be teleported/level-flipped up (only its own walk along the stair surface may change its floor)."""
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
    b = p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']); pg = b.new_context(viewport={'width':844,'height':390}).new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1&npcs=0&party=2', wait_until='commit', timeout=120000); pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=120000); pg.wait_for_timeout(2500)
    n = pg.evaluate("__p3d.bump.crowd.filter(r=>r.kind==='party').length"); T('party followers present', n >= 1, n)
    pg.evaluate("(()=>{const s=__p3d.state;s.level=1;const f=__p3d.bump.crowd.find(r=>r.kind==='party');f.level=0;f.lvT=0;f.a.x=s.heroX+40;f.a.z=s.heroZ;window.__f=f;window.__h=[s.heroX,s.heroZ]})()")
    pg.wait_for_timeout(16000)
    r = pg.evaluate("(()=>{const f=window.__f,s=__p3d.state;return {lvl:f.level,d:Math.hypot(f.a.x-s.heroX,f.a.z-s.heroZ)}})()"); print(r)
    T('follower on ground floor is NOT snapped up to the hero floor or teleported next to an upstairs hero', r['lvl'] == 0 and r['d'] > 8, r)
    T('no page errors', not errs, errs[:2]); b.close()
print('FAILED' if bad else 'ALL PASS'); sys.exit(1 if bad else 0)
