#!/usr/bin/env python3
"""Ladders: keyboard walk-in, joystick walk-in, Climb button, E key; climb down; followers follow up and down; no auto-climb when standing/walking past."""
import http.server, threading, functools, os, sys, math
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
SH = os.environ.get('SHOTS'); fails = 0
def chk(n, c, extra=''):
    global fails
    print(('PASS ' if c else 'FAIL ') + n, extra, flush=True); fails += 0 if c else 1
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
    pg = b.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True).new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1&party=2&npcs=0', wait_until='commit', timeout=120000)
    pg.wait_for_function('window.__p3d&&__p3d.frames>5&&__p3d.ladders&&__p3d.ladders.list.length==3', timeout=120000); pg.wait_for_timeout(2000)
    n = pg.evaluate("__p3d.ladders.list.length"); chk('3 ladder structures', n == 3)
    ST = "({x:__p3d.state.heroX,z:__p3d.state.heroZ,lv:__p3d.state.level,y:__p3d.state.heroY,c:__p3d.state.climbing})"
    def L(i): return pg.evaluate("i=>{const l=__p3d.ladders.list[i];return {x:l.x,z:l.z,half:l.half,H:l.H,bx:l.baseX,bz:l.baseZ,level:l.level,id:l.id}}", i)
    def tp(x, z, lv=0): pg.evaluate("([x,z,l])=>{__p3d.teleport(x,z,l);__p3d.state.camYaw=0}", [x, z, lv]); pg.wait_for_timeout(300)
    def follow_ok(): return pg.evaluate("(()=>{const f=__p3d.bump.crowd.filter(c=>c.kind==='party');return f.length>0&&f.every(c=>c.level===__p3d.state.level&&Math.abs(c.y-__p3d.state.heroY)<1.2)})()")
    # 1) standing next to / walking past a ladder does NOT climb
    a = L(0); tp(a['bx'] + 3.0, a['bz'] + 0.5); pg.wait_for_timeout(1500); s = pg.evaluate(ST); chk('standing near: no auto climb', s['lv'] == 0 and not s['c'])
    # 2) keyboard: walk into the ladder (camYaw 0 -> W moves -z, toward the ladder)
    tp(a['bx'], a['bz'] + 2.5); pg.keyboard.down('w'); ok = False
    for i in range(200):
        pg.wait_for_timeout(100); s = pg.evaluate(ST)
        if s['lv'] == a['level']: ok = True; break
    pg.keyboard.up('w'); s = pg.evaluate(ST); chk('keyboard walk-in climbs up', ok and abs(s['y'] - a['H']) < 0.3, str(s))
    if SH: pg.screenshot(path=f'{SH}/ladder_top.png')
    # followers
    try: pg.wait_for_function("(()=>{const f=__p3d.bump.crowd.filter(c=>c.kind==='party');return f.length>0&&f.every(c=>c.level===__p3d.state.level&&Math.abs(c.y-__p3d.state.heroY)<1.2)})()", timeout=60000); fo = True
    except Exception: fo = False
    chk('followers climbed up', fo, str(pg.evaluate("__p3d.bump.crowd.filter(c=>c.kind==='party').map(c=>[c.level,+c.y.toFixed(1)])")))
    # 3) walk on the platform, edge is blocked (cannot walk off into the air)
    pg.keyboard.down('s'); pg.wait_for_timeout(500); pg.keyboard.up('s')
    # climb down: move toward the ladder edge (+z) at the top
    pg.keyboard.down('s'); ok = False
    try: pg.wait_for_function("__p3d.state.level==0&&!__p3d.state.climbing", timeout=120000); ok = True
    except Exception: pass
    pg.keyboard.up('s'); s = pg.evaluate(ST); chk('keyboard climbs down', ok and s['y'] < 0.3, str(s))
    try: pg.wait_for_function("(()=>{const f=__p3d.bump.crowd.filter(c=>c.kind==='party');return f.length>0&&f.every(c=>c.level===0&&Math.abs(c.y-__p3d.state.heroY)<1.2)})()", timeout=60000); fd = True
    except Exception: fd = False
    chk('followers climbed down', fd)
    # 4) Climb button (touch) and E key on a second ladder
    c = L(1); tp(c['bx'], c['bz'] + 0.5); pg.wait_for_timeout(500); vis = pg.evaluate("getComputedStyle(document.getElementById('climbBtn')).display"); chk('climb button visible near ladder', vis == 'block')
    if SH: pg.screenshot(path=f'{SH}/ladder_button.png')
    r = pg.evaluate("(()=>{const r=document.getElementById('climbBtn').getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})()"); pg.touchscreen.tap(r[0], r[1])
    try: pg.wait_for_function("__p3d.state.level==%d" % c['level'], timeout=20000); tb = True
    except Exception: tb = False
    chk('touch Climb button climbs', tb)
    pg.keyboard.down('e'); pg.wait_for_timeout(500); pg.keyboard.up('e')
    try: pg.wait_for_function("__p3d.state.level==0", timeout=20000); eb = True
    except Exception: eb = False
    chk('E key climbs down', eb)
    # 5) joystick walk-in on the third ladder
    d = L(2); tp(d['bx'], d['bz'] + 2.5)
    box = pg.evaluate("(()=>{const r=document.getElementById('stick').getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2,r.width/2]})()")
    pg.mouse.move(box[0], box[1]); pg.mouse.down(); pg.mouse.move(box[0], box[1] - box[2] * .8); ok = False
    try: pg.wait_for_function("__p3d.state.level==%d" % d['level'], timeout=120000); ok = True
    except Exception: pass
    pg.mouse.up(); chk('joystick walk-in climbs', ok)
    chk('no page errors', not errs, str(errs[:3]))
    b.close()
print('FAILS', fails); sys.exit(1 if fails else 0)
