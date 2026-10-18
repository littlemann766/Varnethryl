#!/usr/bin/env python3
"""Real-input stair test: a simulated player steers the hero over EVERY ramp (all floors, up AND down) with real keyboard (8-way WASD, quantised like a human) or the
on-screen joystick, at several camera yaws, with followers + NPC + bump system ON. Start 2.8 m before the stair, aim past the far end.
usage: python3 tools/stairs_input_test.py   (ONLY=id,id  MODE=key|joy|both  PARTY=0  YAWS=0,2.2,-0.8  DIRS=up,down)"""
import http.server, threading, functools, os, sys, json, math
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
ONLY = os.environ.get('ONLY', '').split(',') if os.environ.get('ONLY') else None
MODE = os.environ.get('MODE', 'both'); PARTY = os.environ.get('PARTY', '2'); DIRS = os.environ.get('DIRS', 'up,down').split(',')
YAWS = [float(v) for v in os.environ.get('YAWS', '0,2.2,-0.8').split(',')]
fails = 0; total = 0
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']); pg = b.new_page(viewport={'width': 390, 'height': 844}, has_touch=True)
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?party={PARTY}&npcs={1 if PARTY != "0" else 0}'); pg.wait_for_function('window.__p3d && window.__p3d.frames>5', timeout=90000); pg.wait_for_timeout(2500)
    info = json.loads(pg.evaluate("JSON.stringify(__p3d.multi.map(b=>({id:b.id,ramps:b.ramps})))"))
    def W(bid, lx, lz): return pg.evaluate("([id,lx,lz])=>__p3d.multi.find(b=>b.id===id).toW(lx,lz)", [bid, lx, lz])
    box = pg.evaluate("(()=>{const r=document.getElementById('stick').getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2,r.width/2]})()")
    def drive(tx, tz, mode, lg, yg, secs=11):
        held = set(); joy = False
        try:
            t = 0
            while t < secs * 1000:
                st = pg.evaluate("({x:__p3d.state.heroX,z:__p3d.state.heroZ,lv:__p3d.state.level,y:__p3d.state.heroY,cy:__p3d.state.camYaw})")
                if st['lv'] == lg and abs(st['y'] - yg) < .2: return st, t
                dx, dz = tx - st['x'], tz - st['z']; d = math.hypot(dx, dz) or 1; dx /= d; dz /= d
                sy, cy = math.sin(st['cy']), math.cos(st['cy']); ix = dx * cy - dz * sy; iy = -dx * sy - dz * cy
                if mode == 'key':
                    want = set()
                    if iy > .38: want.add('w')
                    if iy < -.38: want.add('s')
                    if ix > .38: want.add('d')
                    if ix < -.38: want.add('a')
                    for k in held - want: pg.keyboard.up(k)
                    for k in want - held: pg.keyboard.down(k)
                    held = want
                else:
                    x, y = box[0] + ix * box[2] * .8, box[1] - iy * box[2] * .8
                    if not joy: pg.mouse.move(box[0], box[1]); pg.mouse.down(); joy = True
                    pg.mouse.move(x, y)
                if os.environ.get('TRACE'): print('   ', round(st['x'],2), round(st['z'],2), st['lv'], round(st['y'],2), sorted(held))
                pg.wait_for_timeout(120); t += 120
            return pg.evaluate("({x:__p3d.state.heroX,z:__p3d.state.heroZ,lv:__p3d.state.level,y:__p3d.state.heroY})"), t
        finally:
            for k in held: pg.keyboard.up(k)
            if joy: pg.mouse.up()
    for bi in info:
        if ONLY and bi['id'] not in ONLY: continue
        for m in bi['ramps']:
            s, c = math.sin(m['ang']), math.cos(m['ang']); h = m['len'] / 2
            for dr in DIRS:
                def pick(sg, base):
                    for dd in (1.0, 0.7, 0.5, 1.3, 1.7, 2.1, 2.6):
                        q = [m['cx'] + sg * s * (h + dd), m['cz'] + sg * c * (h + dd)]; lv_ = m['l0'] if base else m['l1']
                        if pg.evaluate("([p,l])=>__p3d.free(p[0],p[1],l)", [W(bi['id'], *q), lv_]): return q
                    return q
                if dr == 'up': a = pick(-1, True); t = [m['cx'] + s * (h + 1.4), m['cz'] + c * (h + 1.4)]; lv0, lg, yg = m['l0'], m['l1'], m['y1']
                else: a = pick(1, False); t = [m['cx'] - s * (h + 1.4), m['cz'] - c * (h + 1.4)]; lv0, lg, yg = m['l1'], m['l0'], m['y0']
                res = []
                for mode in (['key', 'joy'] if MODE == 'both' else [MODE]):
                    for yw in YAWS:
                        pg.evaluate("([s,l,y])=>{__p3d.teleport(s[0],s[1],l);__p3d.state.target=null;__p3d.state.camYaw=y}", [W(bi['id'], *a), lv0, yw]); pg.wait_for_timeout(300)
                        wt = W(bi['id'], *t); r, ms = drive(wt[0], wt[1], mode, lg, yg)
                        ok = r['lv'] == lg and abs(r['y'] - yg) < .2; total += 1; fails += 0 if ok else 1; res.append(f"{mode}@{yw:+.1f}:" + ('OK' if ok else 'FAIL(lv%s y%.1f @%.1f,%.1f)' % (r['lv'], r['y'], r['x'], r['z'])))
                print('PASS' if all('FAIL' not in x for x in res) else 'FAIL', bi['id'], f"{m['l0']}->{m['l1']} {dr}", ' '.join(res), flush=True)
    b.close()
print('page errors:', errs[:5]); print(f'FAILS {fails}/{total}'); sys.exit(1 if fails else 0)
