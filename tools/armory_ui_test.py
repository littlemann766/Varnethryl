#!/usr/bin/env python3
"""Armory UI in the game at 412x915: opens from Settings Loadout card, no horizontal overflow, slots/inventory/compare/presets/enhance preview work through engine requests. SHOTS=dir for screenshots."""
import http.server, threading, functools, os
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
    pg = b.new_page(viewport={'width': 412, 'height': 915}, has_touch=True); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text[:150]) if m.type == 'error' else 0)
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1&npcs=0&party=0', wait_until='commit', timeout=120000)
    pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=120000); pg.wait_for_timeout(1500)
    pg.evaluate("__p3d.fightToggle()"); pg.wait_for_function("__p3d.fight&&__p3d.fight.on", timeout=90000); pg.wait_for_timeout(2500)
    i = pg.evaluate("m=>__p3d.modelStatus().models.findIndex(x=>x.id===m)", "aldric"); pg.evaluate("i=>__p3d.selectHero(i)", i); pg.wait_for_timeout(4000)
    chk('fight exposes the armory engine', pg.evaluate("!!__p3d.fight.armory"))
    pg.evaluate("__p3d.fight.cc.gold=100000"); pg.evaluate("__p3d.settings&&__p3d.settings.open&&__p3d.settings.open()")
    pg.wait_for_timeout(800)
    btn = pg.query_selector('#openArmory')
    if btn: btn.scroll_into_view_if_needed(); btn.click()
    else: pg.evaluate("import('./proto3d/armoryui.js').then(m=>m.openArmory(__p3d.fight.armory))")
    pg.wait_for_function("!!document.getElementById('armoryHost')", timeout=20000); pg.wait_for_timeout(800)
    chk('opened from the Settings Loadout card' if btn else 'opened (card button not found; direct)', bool(btn))
    Q_ = lambda s: pg.evaluate("(s)=>document.getElementById('armoryHost').shadowRoot.querySelectorAll(s).length", s)
    print('KEY', pg.evaluate('[__p3d.fight.armory.key, __p3d.fight.armory.items().length, __p3d.fight.cc.hero.id, __p3d.owner]'), flush=True)
    chk('12 gear slots', Q_('.gear-slot') == 12, Q_('.gear-slot'))
    chk('inventory tiles with rarity classes', Q_('.item-tile') >= 10 and Q_('.item-tile[class*="r-"]') >= 10)
    ow = pg.evaluate("(()=>{const h=document.getElementById('armoryHost'),r=h.shadowRoot;return {sw:r.querySelector('.root').scrollWidth,cw:h.clientWidth}})()")
    chk('412 px layout: no horizontal overflow', ow['sw'] <= ow['cw'] + 1, ow)
    if SH: pg.screenshot(path=f'{SH}/armory_412.png')
    click = lambda s: pg.evaluate("(s)=>document.getElementById('armoryHost').shadowRoot.querySelector(s).click()", s)
    click('.item-tile[data-item="iron-helm"]'); pg.wait_for_timeout(200)
    chk('details + compare + enhance preview shown', pg.evaluate("document.getElementById('armoryHost').shadowRoot.getElementById('prev')!==null"))
    click('#act .primary-btn'); pg.wait_for_timeout(200)
    chk('equip request accepted by the engine', pg.evaluate("__p3d.fight.armory.s.equipment.head==='iron-helm'"))
    chk('combat kit updated', pg.evaluate("__p3d.fight.cc.kit.armor.hpPct>__p3d.fight.cc.kit.armor.hpPct-1") and pg.evaluate("__p3d.fight.cc.gear&&__p3d.fight.cc.gear.hpPct>0.2"))
    click('.preset-save[data-save="0"]'); click('.gear-slot[data-slot="head"]'); pg.wait_for_timeout(100); click('#act .primary-btn'); pg.wait_for_timeout(150)
    chk('unequip works', pg.evaluate("__p3d.fight.armory.s.equipment.head===null"))
    click('.preset-card[data-preset="0"]'); pg.wait_for_timeout(150)
    chk('preset loads', pg.evaluate("__p3d.fight.armory.s.equipment.head==='iron-helm'"))
    chk('UI cannot bypass the engine: owner item request refused', pg.evaluate("!__p3d.fight.armory.request({type:'equip',itemId:'sovereign-end'}).ok"))
    click('.item-tile[data-item="iron-helm"]'); pg.wait_for_timeout(150); click('#act .secondary-btn'); pg.wait_for_timeout(150)
    chk('enhance via request spends game gold', pg.evaluate("__p3d.fight.armory.level('iron-helm')===1 && __p3d.fight.cc.gold<100000"))
    if SH: pg.screenshot(path=f'{SH}/armory_412_after.png')
    chk('no page errors', not errs, str(errs[:3])); b.close()
print('FAILED' if fails else 'ALL PASS'); raise SystemExit(1 if fails else 0)
