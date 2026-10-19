#!/usr/bin/env python3
"""Companions/followers fight: they close in on a nearby enemy, hit it several times (modest damage), kill it, then return to follow the hero; the hero is never harmed and a downed companion does not attack. SHOTS=dir"""
import http.server, threading, functools, os, sys
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
SH = os.environ.get('SHOTS'); fails = 0
def chk(n, c, x=''):
    global fails; print(('PASS ' if c else 'FAIL ') + n, x, flush=True); fails += 0 if c else 1
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
    pg = b.new_page(viewport={'width': 390, 'height': 844}, has_touch=True); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text[:150]) if m.type == 'error' else 0)
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1&party=2&npcs=0', wait_until='commit', timeout=120000)
    pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=120000); pg.wait_for_timeout(1500)
    pg.evaluate("__p3d.fightToggle()"); pg.wait_for_function("__p3d.fight&&__p3d.fight.on&&__p3d.fight.hasSaber", timeout=90000); pg.wait_for_timeout(1500)
    pg.evaluate("__p3d.fight.cc.god=true;__p3d.fight.cc.clearEnemies();window.__ally=0;window.__hero=0;__p3d.fight.cc.on('damage',d=>{if(d.ally)__ally++;else if(!d.toPlayer)__hero++})")
    pg.evaluate("(async()=>{await __p3d.fight.spawn('wolf',6)})()"); pg.wait_for_function("__p3d.fight.cc.enemies.length>=1", timeout=60000); pg.evaluate("window.__w=__p3d.fight.cc.enemies[0];window.__wh=0;__p3d.fight.cc.on('damage',d=>{if(d.ally&&d.e===__w)__wh++})")
    hp0 = pg.evaluate("__p3d.fight.cc.res.hp")
    chk('followers present', pg.evaluate("__p3d.crowd.filter(r=>r.kind==='party').length") >= 2)
    # keep the hero out of the fight: only companions attack
    try: pg.wait_for_function("__ally>=1", timeout=60000); ok = True
    except Exception: ok = False
    chk('companions start attacking', ok)
    if SH: pg.screenshot(path=f'{SH}/companions_fight.png')
    try: pg.wait_for_function("__w.state==='defeated'", timeout=150000); ok = True
    except Exception: ok = False
    n = pg.evaluate("__wh"); chk('companions killed the wolf over several hits', ok and n >= 3, f'hits={n}')
    chk('the hero dealt none of it', pg.evaluate("__hero") == 0)
    chk('hero HP unchanged, not dead', pg.evaluate("__p3d.fight.cc.res.hp") >= hp0 and pg.evaluate("__p3d.fight.cc.dead") == 0)
    pg.evaluate("__p3d.fight.cc.clearEnemies()"); pg.wait_for_timeout(500)
    try: pg.wait_for_function("__p3d.crowd.filter(r=>r.kind==='party').every(r=>Math.hypot(r.a.x-__p3d.state.heroX,r.a.z-__p3d.state.heroZ)<7)", timeout=60000); ok = True
    except Exception: ok = False
    chk('followers return to the hero after combat', ok)
    # a downed companion does not attack
    pg.evaluate("__p3d.downAllies();window.__ally=0;(async()=>{await __p3d.fight.spawn('wolf',4)})()"); pg.wait_for_timeout(2500)
    chk('downed companions do not attack', pg.evaluate("__ally") == 0 and pg.evaluate("__p3d.crowd.filter(r=>r.kind==='party'&&r.down>0).length") >= 1)
    if SH: pg.screenshot(path=f'{SH}/companions_downed.png')
    chk('no page errors', not errs, str(errs[:3])); b.close()
print('FAILS', fails); sys.exit(1 if fails else 0)
