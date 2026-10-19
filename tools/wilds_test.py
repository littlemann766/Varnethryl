#!/usr/bin/env python3
"""The Wilds: town portal -> wilds (monsters spawn there only, fight HUD works), portal back, followers come along, bounds clamp, draw calls. SHOTS=dir"""
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
    pg = b.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True).new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text[:160]) if m.type == 'error' else 0)
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1&party=2&npcs=1', wait_until='commit', timeout=120000)
    pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=120000); pg.wait_for_timeout(2500)
    chk('starts in town, no monsters', pg.evaluate("__p3d.zone") == 'town' and not pg.evaluate("!!(__p3d.fight&&__p3d.fight.on)"))
    # walk into the town portal (W = toward -z with camYaw 0)
    pg.evaluate("__p3d.teleport(-6,46,0);__p3d.state.camYaw=0"); pg.wait_for_timeout(400); pg.keyboard.down('w')
    try: pg.wait_for_function("__p3d.zone==='wilds'", timeout=120000); ok = True
    except Exception: ok = False
    pg.keyboard.up('w'); chk('walking into the portal enters the Wilds', ok)
    pg.wait_for_function("__p3d.fight&&__p3d.fight.on", timeout=60000); pg.wait_for_timeout(2500)
    s = pg.evaluate("({x:__p3d.state.heroX,z:__p3d.state.heroZ})"); chk('arrived at the Wilds spawn', abs(s['x'] - 994) < 6 and abs(s['z'] - 4) < 6, str(s))
    chk('fight HUD visible in the Wilds', pg.evaluate("getComputedStyle(document.getElementById('cb')).display") == 'block')
    try: pg.wait_for_function("__p3d.fight.monsters.length>=1", timeout=120000); ms = True
    except Exception: ms = False
    chk('monsters spawn in the Wilds', ms, str(pg.evaluate("__p3d.fight.monsters.map(m=>[m.def.name,Math.round(m.x),Math.round(m.z)])")))
    chk('monsters are near the hero (not in town)', pg.evaluate("__p3d.fight.monsters.every(m=>m.x>850)"))
    d = pg.evaluate("(()=>{const f=__p3d.bump.crowd.filter(c=>c.kind==='party');return f.map(c=>Math.hypot(c.a.x-__p3d.state.heroX,c.a.z-__p3d.state.heroZ))})()"); chk('followers came along', len(d) > 0 and all(x < 15 for x in d), str([round(x, 1) for x in d]))
    chk('mobs stand off (idle) until you are within 3 m', pg.evaluate("__p3d.fight.monsters.every(m=>m.state==='idle'||Math.hypot(m.x-__p3d.state.heroX,m.z-__p3d.state.heroZ)<5)"))
    pg.evaluate("(()=>{const f=__p3d.fight,e=f.monsters.find(m=>m.state==='idle');const s=__p3d.state;if(e){s.heroX=e.x;s.heroZ=e.z+2.2}})()"); pg.wait_for_timeout(1500)
    chk('mob aggroes within 3 m', pg.evaluate("__p3d.fight.monsters.some(m=>['chase','telegraph','attack','recover'].includes(m.state))"))
    pg.evaluate("__p3d.fight.cc.god=true")
    pg.wait_for_timeout(1500)
    calls = pg.evaluate("document.getElementById('fps').textContent"); print('stats', calls)
    if SH: pg.screenshot(path=f'{SH}/wilds_arrive.png')
    # look around: teleport inside the Wilds to other biomes for screenshots + draw calls
    mx = 0
    for nm, (x, z) in {'forest': (-60, 0), 'lake': (30, -10), 'rock': (0, 70), 'snow': (80, 30)}.items():
        pg.evaluate("([x,z])=>{__p3d.state.heroX=1000+x;__p3d.state.heroZ=z}", [x, z]); pg.wait_for_timeout(2500)
        c = pg.evaluate("__p3d.renderer.info.render.calls"); mx = max(mx, c); print(nm, 'draw calls', c)
        if SH: pg.screenshot(path=f'{SH}/wilds_{nm}.png')
    chk('draw calls bounded (<450, SwiftShader count incl. shadow pass)', mx < 450, str(mx))
    # bounds clamp
    pg.evaluate("__p3d.state.heroX=1000+400"); pg.wait_for_timeout(600); x = pg.evaluate("__p3d.state.heroX")
    pg.keyboard.down('d'); pg.wait_for_timeout(500); pg.keyboard.up('d'); x = pg.evaluate("__p3d.state.heroX"); chk('walkable area is clamped', x < 1000 + 175, str(x))
    # portal back
    pg.evaluate("__p3d.state.heroX=994;__p3d.state.heroZ=6;__p3d.state.camYaw=0"); pg.wait_for_timeout(500); pg.keyboard.down('w')
    try: pg.wait_for_function("__p3d.zone==='town'", timeout=120000); ok = True
    except Exception: ok = False
    pg.keyboard.up('w'); chk('portal back to town', ok); pg.wait_for_timeout(1500)
    s = pg.evaluate("({x:__p3d.state.heroX,z:__p3d.state.heroZ})"); chk('back near the town portal', abs(s['x'] + 6) < 8 and abs(s['z'] - 42) < 8, str(s))
    chk('fight mode (auto) ended in town', not pg.evaluate("__p3d.fight.on") and pg.evaluate("getComputedStyle(document.getElementById('cb')).display") == 'none')
    d = pg.evaluate("(()=>{const f=__p3d.bump.crowd.filter(c=>c.kind==='party');return f.map(c=>Math.hypot(c.a.x-__p3d.state.heroX,c.a.z-__p3d.state.heroZ))})()"); chk('followers back too', all(x < 15 for x in d), str([round(x, 1) for x in d]))
    n = pg.evaluate("__p3d.bump.crowd.filter(c=>c.kind==='npc').every(c=>Math.abs(c.a.x)<200)"); chk('townsfolk stayed in town', n)
    if SH: pg.screenshot(path=f'{SH}/wilds_back_in_town.png')
    chk('no page errors', not errs, str(errs[:3]))
    b.close()
print('FAILS', fails); sys.exit(1 if fails else 0)
