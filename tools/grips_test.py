#!/usr/bin/env python3
"""Signature/optional weapons attach in the hand for hero kits (grip offsets from combat/grips.js), sized in metres, owner path untouched. SHOTS=dir"""
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
M = "(()=>{const w=__p3d.fight.heroWeapon;if(!w)return null;const T=__p3d.THREE,b=new T.Box3().setFromObject(w),v=new T.Vector3();b.getSize(v);const hp=new T.Vector3(),wp=new T.Vector3();w.parent.getWorldPosition(hp);w.getWorldPosition(wp);return {parent:w.parent.name,len:Math.max(v.x,v.y,v.z),d:hp.distanceTo(wp),grip:w.userData.grip}})()"
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
    pg = b.new_page(viewport={'width': 412, 'height': 915}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1&npcs=0&party=0', wait_until='commit', timeout=120000); pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=120000); pg.wait_for_timeout(1500)
    pg.evaluate("__p3d.fightToggle()"); pg.wait_for_function("__p3d.fight&&__p3d.fight.on", timeout=90000); pg.wait_for_timeout(1500)
    T('Owner: no hero-kit weapon (saber path)', pg.evaluate("!__p3d.fight.heroWeapon"))
    def pick(h):
        i = pg.evaluate("m=>__p3d.modelStatus().models.findIndex(x=>x.id===m)", h); pg.evaluate("i=>__p3d.selectHero(i)", i); pg.wait_for_timeout(5000)
    for h, length in (('seraphine', 0.9), ('finn', 0.9)):
        pick(h)
        try: pg.wait_for_function("!!__p3d.fight.heroWeapon", timeout=30000)
        except Exception: pass
        r = pg.evaluate(M); print(h, r, flush=True)
        T(h + ': signature weapon attached to hand_R', bool(r) and r['parent'] == 'hand_R', r)
        T(h + ': grip near the hand (<0.6 wu)', bool(r) and r['d'] < 0.6, r)
        T(h + ': sized in metres (0.4..2.6 wu)', bool(r) and 0.4 < r['len'] < 2.6, r)
        if SH: pg.screenshot(path=f'{SH}/grip_{h}.png')
    pick('elira'); pg.wait_for_timeout(1000)
    T('elira: no signature GLB => nothing attached by default', pg.evaluate("!__p3d.fight.heroWeapon"))
    ok = pg.evaluate("__p3d.fight.armory.request({type:'equip',itemId:'w-longbow'}).ok")
    try: pg.wait_for_function("!!__p3d.fight.heroWeapon", timeout=30000)
    except Exception: pass
    r = pg.evaluate(M); T('elira: optional Beth longbow equips and attaches in hand', ok and bool(r) and r['parent'] == 'hand_R', r)
    if SH: pg.screenshot(path=f'{SH}/grip_elira_longbow.png')
    pg.evaluate("__p3d.fight.armory.request({type:'reset'})"); pg.wait_for_timeout(800); T('reset to default removes the optional weapon', pg.evaluate("!__p3d.fight.heroWeapon"))
    T('no page errors', not errs, errs[:2]); b.close()
print('FAILED' if bad else 'ALL PASS'); sys.exit(1 if bad else 0)
