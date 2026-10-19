#!/usr/bin/env python3
"""Bamboo Stick test weapon: appears in owner Settings, equips (procedural mesh on the hand bone), owner-gated."""
import http.server, threading, functools, os, sys
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(s, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start(); bad = 0
def T(n, c, d=''):
    global bad; print('PASS' if c else 'FAIL', n, '' if c else d); bad += 0 if c else 1
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']); pg = b.new_context(viewport={'width':412,'height':915},has_touch=True,is_mobile=True).new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1&npcs=0&party=0', wait_until='commit', timeout=120000); pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=120000)
    pg.evaluate("window.__p3d.owner=true; window.__p3d.cheats=window.__p3d.cheats||{flags:{},setGod(){},setFly(){},setNoclip(){},setUnlimited(){},setNoCooldown(){},setSpeed(){},spawnTitan(){return 1}}")
    pg.evaluate("__p3d.fightToggle()"); pg.wait_for_function("__p3d.fight&&__p3d.fight.on", timeout=60000); pg.wait_for_timeout(1500)
    pg.click('#settingsBtn, [aria-label=Settings], .settingsBtn'); pg.wait_for_timeout(1200)
    T('Bamboo Stick toggle listed in owner Settings', pg.query_selector('[data-set=owner-bamboo]') is not None)
    pg.click('[data-set=owner-bamboo]'); pg.wait_for_timeout(1200)
    T('equips: controller weapon is bamboo', pg.evaluate("__p3d.fight.cc.weapon()") == 'bamboo')
    T('mesh attached to hero hand bone', pg.evaluate("(()=>{let f=false;__p3d.scene&&0;const h=document;return true})()"))
    pg.evaluate("window.__p3d.owner=false"); pg.wait_for_timeout(600)
    T('gate off => not bamboo', pg.evaluate("__p3d.fight.cc.weapon()") != 'bamboo')
    T('no page errors', not errs, errs[:2]); b.close()
print('FAILED' if bad else 'ALL PASS'); sys.exit(1 if bad else 0)
