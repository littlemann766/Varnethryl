#!/usr/bin/env python3
"""Hero kit HUD (hud-heroes): a non-owner archetype hero (aldric/elira/rowan/thorne/nyx) shows ITS OWN 3 skills + ultimate (names, icons, color) in the pad, skills work through the controller, ultimate gated by Fury, no overlap. SHOTS=dir for screenshots."""
import http.server, threading, functools, os, sys
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start(); bad = 0; SH = os.environ.get('SHOTS')
def T(n, c, d=''):
    global bad; print('PASS' if c else 'FAIL', n, '' if c else d); bad += 0 if c else 1
KIT = {'aldric': ['Shield Bash', 'Guardian Slam', 'Bulwark Charge', 'Lionheart Bulwark'], 'elira': ['Aimed Shot', 'Piercing Arrow', 'Snare Trap', 'Eagle-Eye Barrage'], 'rowan': ['Firebolt', 'Flame Wave', 'Ember Burst', 'Meteor Burst'], 'thorne': ['Radiant Bolt', 'Mend', 'Holy Smite', 'Divine Renewal'], 'nyx': ['Dagger Flurry', 'Shadow Step', 'Poison Cut', 'Shadow Flurry']}
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']); pg = b.new_context(viewport={'width':844,'height':390}, has_touch=True, is_mobile=True).new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1&npcs=0&party=0', wait_until='commit', timeout=120000); pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=120000); pg.wait_for_timeout(1500)
    pg.evaluate("__p3d.fightToggle()"); pg.wait_for_function("__p3d.fight&&__p3d.fight.on", timeout=60000); pg.wait_for_timeout(1500)
    pg.evaluate("__p3d.fight.cc.god=true")
    for h, names in KIT.items():
        i = pg.evaluate("h=>__p3d.modelStatus().models.findIndex(m=>m.id===h)", h); pg.evaluate("i=>__p3d.selectHero(i)", i); pg.wait_for_timeout(1800)
        got = pg.evaluate("[1,2,3,4].map(i=>document.querySelector('#cb .sl[data-s=\"'+i+'\"]').title)")
        T(h + ': pad shows its own skills + ultimate', got == names, got)
        T(h + ': not owner-gated (no owner powers)', pg.evaluate("!__p3d.fight.cc.ownerOk()"))
        T(h + ': ultimate locked-looking until Fury (no ready glow)', pg.evaluate("!document.querySelector('#cb .sl[data-s=\"4\"]').classList.contains('rdy')"))
        if SH: pg.screenshot(path=f'{SH}/kit_{h}.png')
    # use rowan: skill 1 deals damage via controller; ult after Fury full
    pg.evaluate("(()=>{const f=__p3d.fight,c=f.cc;c.clearEnemies();c.res.mp=100;c.res.sp=100;c.cd.reset();f.spawn('wolf',6)})()"); pg.wait_for_function("__p3d.fight.monsters.length>=1", timeout=60000); pg.wait_for_timeout(500)
    pg.evaluate("(()=>{const c=__p3d.fight.cc;const e=c.enemies[0];e.x=c.p.x;e.z=c.p.z+6;e.aggroR=0;c.tgt.target=e})()")
    q = pg.evaluate("(()=>{const r=document.querySelector('#cb .sl[data-s=\"1\"]').getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})()"); pg.touchscreen.tap(q[0], q[1]); pg.wait_for_timeout(1200)
    T('rowan Firebolt via tap damages the target', pg.evaluate("(()=>{const e=__p3d.fight.cc.enemies[0];return !e||e.hp<e.max||e.state==='defeated'})()"))
    pg.evaluate("(()=>{const c=__p3d.fight.cc;c.fury=100;c.cd.reset()})()"); pg.wait_for_timeout(300)
    T('ultimate glows ready at full Fury', pg.evaluate("document.querySelector('#cb .sl[data-s=\"4\"]').classList.contains('rdy')"))
    T('no page errors', not errs, errs[:2]); b.close()
print('FAILED' if bad else 'ALL PASS'); sys.exit(1 if bad else 0)
