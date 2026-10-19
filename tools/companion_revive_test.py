#!/usr/bin/env python3
"""Thunderstorm (ULTIMATE2): kills EVERY enemy (incl. troll + Titan), downs companions and townsfolk, who revive after a delay (companions at the hero's side); hero HP/death/position unaffected. SHOTS=dir"""
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
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1&party=2&npcs=1', wait_until='commit', timeout=120000)
    pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=120000); pg.wait_for_timeout(1500)
    pg.evaluate("__p3d.fightToggle()"); pg.wait_for_function("__p3d.fight&&__p3d.fight.on&&__p3d.fight.hasSaber", timeout=90000); pg.wait_for_timeout(1500)
    pg.evaluate("__p3d.fight.cc.god=false;__p3d.fight.cc.res.mp=999;__p3d.fight.cc.clearEnemies()")
    pg.evaluate("(async()=>{const f=__p3d.fight;for(let i=0;i<22;i++){await f.spawn(['wolf','raider','wraith','skeleton'][i%4],10+i*4)}await f.spawn('frosttroll',40);await f.spawn('titan',60)})()")
    pg.wait_for_function("__p3d.fight.cc.enemies.length>=24", timeout=120000)
    hp0 = pg.evaluate("__p3d.fight.cc.res.hp"); pos0 = pg.evaluate("[__p3d.state.heroX,__p3d.state.heroZ]")
    chk('22+ enemies incl. troll and Titan', pg.evaluate("__p3d.fight.cc.alive()") >= 24 and pg.evaluate("__p3d.fight.cc.enemies.some(e=>e.def.boss)"))
    chk('cast accepted', pg.evaluate("__p3d.fight.useUltimate2()"))
    pg.wait_for_timeout(1500)
    if SH: pg.screenshot(path=f'{SH}/storm_cast.png')
    try: pg.wait_for_function("__p3d.fight.cc.alive()===0", timeout=90000); ok = True
    except Exception: ok = False
    chk('every enemy died (troll + Titan too)', ok, str(pg.evaluate("__p3d.fight.cc.enemies.filter(e=>e.state!=='defeated').map(e=>[e.def.name,e.hp])")))
    chk('companions/townsfolk downed (hidden)', pg.evaluate("__p3d.crowd.filter(r=>r.down>0).length")>=1, str(pg.evaluate("__p3d.crowd.map(r=>[r.kind,+(r.down||0).toFixed(1)])")))
    chk('hero not hurt, not dead, not moved to start', pg.evaluate("__p3d.fight.cc.dead")==0 and pg.evaluate("__p3d.fight.cc.res.hp")>=hp0-1 and abs(pg.evaluate("__p3d.state.heroX")-pos0[0])<3, str(pg.evaluate("[__p3d.fight.cc.dead,__p3d.fight.cc.res.hp,__p3d.state.heroX,__p3d.state.heroZ]")))
    try: pg.wait_for_function("__p3d.crowd.every(r=>!(r.down>0))", timeout=90000); ok = True
    except Exception: ok = False
    chk('all revived after the delay', ok)
    d = pg.evaluate("__p3d.crowd.filter(r=>r.kind==='party').map(r=>Math.hypot(r.a.x-__p3d.state.heroX,r.a.z-__p3d.state.heroZ))"); chk('companions revived at the hero side', len(d)>0 and all(x<4 for x in d), str([round(x,1) for x in d]))
    chk('companions visible again', pg.evaluate("__p3d.crowd.filter(r=>r.kind==='party').every(r=>!r.root||r.root.visible)"))
    chk('hero alive and in place afterwards', pg.evaluate("__p3d.fight.cc.dead")==0 and abs(pg.evaluate("__p3d.state.heroX")-pos0[0])<3)
    if SH: pg.screenshot(path=f'{SH}/storm_after_revive.png')
    chk('no page errors', not errs, str(errs[:3])); b.close()
print('FAILS', fails); sys.exit(1 if fails else 0)
