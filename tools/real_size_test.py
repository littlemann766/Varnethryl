#!/usr/bin/env python3
"""Real-size play: picking a character in the dropdown applies its charscale.js profile (collision radius, speed, camera distance/zoom clamp, reach); measured model height must match the config (baked scale, never rescaled). SHOTS=dir for screenshots."""
import http.server, threading, functools, os, sys, json
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(s, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start(); bad = 0; SH = os.environ.get('SHOTS')
def T(n, c, d=''):
    global bad; print('PASS' if c else 'FAIL', n, '' if c else d); bad += 0 if c else 1
K = 1.4205
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']); pg = b.new_context(viewport={'width':412,'height':915}, has_touch=True, is_mobile=True).new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1&npcs=0&party=0', wait_until='commit', timeout=120000); pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=120000); pg.wait_for_timeout(1500)
    def pick(mid):
        i = pg.evaluate("m=>__p3d.modelStatus().models.findIndex(x=>x.id===m)", mid); assert i >= 0, mid
        pg.evaluate("i=>__p3d.selectHero(i)", i); pg.wait_for_function("m=>__p3d.charScale().id===m", arg=mid, timeout=120000); pg.wait_for_timeout(2500)
        return pg.evaluate("__p3d.charScale()")
    def cam():
        pg.wait_for_timeout(1500); return pg.evaluate("(()=>{const r=__p3d.camRig;return {d:r.camDist,zt:r.zoomTarget,prof:r.prof.camDist}})()")
    base = pick('aldric'); T('hero: Aldric real height 1.88 m (v1.1.15), radius cap rule, speed ~x1', base['CH']['height'] == 1.88 and abs(base['CH']['speed'] - 0.993) < 1e-6 and abs(base['HERO_R'] - 0.75) < 0.02, base['CH'])
    cb = cam(); print('hero cam', cb, 'height', base['heroH'])
    res = {}
    for mid, h in [('n:vaelthryx_new', 2.0), ('n:vaelthryx_new6', 14.3), ('n:vaelthryx_straight_rig', 19.05), ('n:frosttroll_b', 5.715), ('n:ashentitan_new', 11.4)]:
        s = pick(mid); res[mid] = s; c = cam()
        T(mid + ': profile applied on pick (height/speed/radius)', s['CH']['height'] == h and (s['CH']['speed'] > 1 and s['HERO_R'] > base['HERO_R'] if h > 3 else s['CH']['speed'] > 0), s['CH'])
        T(mid + ': measured model height matches config within 12 percent (baked scale, not rescaled): %.1f m vs %.1f m' % (s['heroH'] / K, h), abs(s['heroH'] / K - h) / h < 0.12, s['heroH'])
        T(mid + ': camera is further out than the hero camera and the hero stays in view', (c['d'] / c['zt'] > cb['d'] / cb['zt'] if c['prof'] > 1.2 else True) and s['heroH'] < c['d'] * 2.2, (c, cb))
        T(mid + ': zoom clamp comes from the profile', abs(pg.evaluate("__p3d.camRig.setZoom(5)") - s['CH']['camMax']) < 1e-6 and abs(pg.evaluate("__p3d.camRig.setZoom(0.01)") - s['CH']['camMin']) < 1e-6)
        if SH: pg.screenshot(path=f"{SH}/real_{mid.split(':')[1]}.png")
    back = pick('aldric'); T('picking the hero again restores the default profile + camera', back['CH']['height'] == 1.88 and abs(back['HERO_R'] - base['HERO_R']) < 1e-6 and abs(pg.evaluate("__p3d.camRig.setZoom(5)") - 1.7) < 1e-6)
    print({k: [round(x / K, 2) for x in v['dims']] for k, v in res.items()})
    print({k: round(v['heroH'] / K, 2) for k, v in res.items()}, 'hero', round(base['heroH'] / K, 2))
    T('no page errors', not errs, errs[:3]); b.close()
print('FAILED' if bad else 'ALL PASS'); sys.exit(1 if bad else 0)
