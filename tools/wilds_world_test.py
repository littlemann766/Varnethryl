#!/usr/bin/env python3
"""Regression (1.1.9.4): after crossing the town gate the Wilds world must actually be visible: camera stays with the hero (it was clamped to the town bounds => empty sky), terrain/props exist and render, monsters spawn. Phone-size, landscape+portrait."""
import http.server, threading, functools, os, sys
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
bad = 0
def T(n, c, d=''):
    global bad; print('PASS' if c else 'FAIL', n, '' if c else d); bad += 0 if c else 1
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
    for name, vp in (('landscape', {'width':844,'height':390}), ('portrait', {'width':390,'height':844})):
        pg = b.new_context(viewport=vp, has_touch=True, is_mobile=True).new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(f'http://127.0.0.1:{port}/proto3d.html?npcs=0', wait_until='commit', timeout=120000); pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=120000); pg.wait_for_timeout(1500)
        pg.evaluate("__p3d.teleport(-6,34)"); pg.wait_for_timeout(300); pg.evaluate("__p3d.state.heroX=-6;__p3d.state.heroZ=38")
        pg.wait_for_function("__p3d.zone==='wilds'", timeout=60000); pg.wait_for_timeout(3500)
        r = pg.evaluate("""(()=>{const W=__p3d.wilds,g=W.group,s=__p3d.state,c=__p3d.camRig.pos;let vis=0,tri=0;g.traverse(o=>{if(o.isMesh&&o.visible){vis++;tri+=(o.geometry.index?o.geometry.index.count:o.geometry.attributes.position.count)/3}});
          return {camDist:Math.hypot(c.x-s.heroX,c.z-s.heroZ),finite:[c.x,c.y,c.z].every(Number.isFinite),vis,tri,rendered:__p3d.info().triangles,heroVis:__p3d.hero.visible,mon:__p3d.fight?__p3d.fight.monsters.length:0}})()""")
        print(name, r)
        T(name + ': camera stays with the hero in the Wilds (<40 m, finite)', r['finite'] and r['camDist'] < 40, r)
        T(name + ': Wilds terrain + props exist and are visible (meshes, >100k tris)', r['vis'] > 20 and r['tri'] > 100000, r)
        T(name + ': Wilds actually rendered (>60k triangles on screen)', r['rendered'] > 60000, r)
        T(name + ': hero visible', r['heroVis'], r)
        try: pg.wait_for_function("__p3d.fight&&__p3d.fight.monsters.length>=1", timeout=20000); T(name + ': monsters spawned', True)
        except Exception: T(name + ': monsters spawned', False)
        T(name + ': no page errors', not errs, errs[:2]); pg.context.close()
    b.close()
print('FAILED' if bad else 'ALL PASS'); sys.exit(1 if bad else 0)
