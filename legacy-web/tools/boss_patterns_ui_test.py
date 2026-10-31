#!/usr/bin/env python3
"""Boss patterns UI: KEY env = frosttroll | vaelthryx (default vaelthryx). Based on boss_ui_test. Boss UI (hud-heroes): Ashen Titan telegraph shapes + boss HP bar (name, 50% marker, attack name while telegraphing, ENRAGED at <50%). SHOTS=dir for screenshots."""
import http.server, threading, functools, os, sys
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(s, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
K = os.environ.get('KEY', 'vaelthryx'); DIST = 70 if K == 'vaelthryx' else 14
threading.Thread(target=srv.serve_forever, daemon=True).start(); bad = 0; SH = os.environ.get('SHOTS')
def T(n, c, d=''):
    global bad; print('PASS' if c else 'FAIL', n, '' if c else d); bad += 0 if c else 1
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']); pg = b.new_context(viewport={'width':844,'height':390}, has_touch=True, is_mobile=True).new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1&npcs=0&party=0', wait_until='commit', timeout=120000); pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=120000); pg.wait_for_timeout(1500)
    pg.evaluate("__p3d.fightToggle()"); pg.wait_for_function("__p3d.fight&&__p3d.fight.on", timeout=60000); pg.wait_for_timeout(1000)
    pg.evaluate("(()=>{const c=__p3d.fight.cc;c.god=true;c.clearEnemies();})()")
    pg.evaluate("__p3d.fight.spawn('"+K+"', "+str(DIST)+")"); pg.wait_for_function("__p3d.fight.cc.enemies.some(e=>e.key==='"+K+"')", timeout=60000)
    pg.evaluate("(()=>{const c=__p3d.fight.cc,e=c.enemies.find(e=>e.key==='"+K+"');e.aggroR=200;c.tgt.target=e;c.lastTarget=e;window.__ti=e})()")
    seen = {}
    for i in range(400):
        pg.wait_for_timeout(100)
        r = pg.evaluate("(()=>{const e=__ti;return [e.state,e.pat&&e.pat.id,e.pat&&e.pat.shape,!!(e.tele&&e.tele.visible),!!(e.tele2&&e.tele2.visible),document.querySelector('#cb .tp').className,document.querySelector('#cb .tp .sub').textContent]})()")
        if r[0] == 'telegraph' and r[1] and r[1] not in seen:
            seen[r[1]] = r
            if SH: pg.screenshot(path=f'{SH}/{K}_{r[1]}.png')
        if len(seen) >= 3: break
    print({k: v[2:5] for k, v in seen.items()}, pg.evaluate('[__ti.state,__ti.x,__ti.z,__p3d.fight.cc.p.x,__ti.atkCd,__ti.hp]'))
    T(K+' telegraphs at least two different patterns', len(seen) >= 2)
    T('ring telegraph uses the ring mesh; line/cone use the pooled shape mesh', all((v[2] == 'ring' and v[3]) or (v[2] != 'ring' and v[4]) for v in seen.values()))
    T('boss bar visible with ⚠ attack name while telegraphing', any('tel' in v[5] for v in seen.values()) and any(v[6].split('\u2022')[-1].strip().isupper() for v in seen.values()), seen and list(seen.values())[0][5:])
    pg.evaluate("(()=>{__ti.hp=__ti.max*0.4})()"); pg.wait_for_timeout(1500)
    T('enraged: phase 2 + bar tint + ENRAGED label', pg.evaluate("__ti.phase===2 && document.querySelector('#cb .tp').classList.contains('enr') && document.querySelector('#cb .tp .sub').textContent.includes('ENRAGED')"))
    if SH: pg.screenshot(path=f'{SH}/{K}_enraged.png')
    if K == 'vaelthryx': h = pg.evaluate('__ti.top'); T('vaelthryx enemy is ~10x hero tall (top > 20 world units)', h > 20, h)
    T('no page errors', not errs, errs[:2]); b.close()
print('FAILED' if bad else 'ALL PASS'); sys.exit(1 if bad else 0)
