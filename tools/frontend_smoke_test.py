#!/usr/bin/env python3
"""Front-end smoke test: load -> title -> character select -> loading -> game -> pause, plus the hidden 5-tap cheats gesture
on the title screen. Runs landscape desktop, phone portrait and phone landscape; screenshots go to SHOTS (default /workspace/shots/gameui).
Usage: (cd www && python3 -m http.server 9511) ; P3D_URL=http://localhost:9511/proto3d.html python3 tools/frontend_smoke_test.py"""
import os, sys
from playwright.sync_api import sync_playwright
BASE = os.environ.get('P3D_URL', 'http://localhost:9511/proto3d.html'); SH = os.environ.get('SHOTS', '/workspace/shots/gameui'); os.makedirs(SH, exist_ok=True)
bad = 0
def ok(n, c, d=''):
    global bad; print(('PASS' if c else 'FAIL'), n, '' if c else str(d)[:300]); bad += (not c)
def scr(pg): return pg.evaluate("document.body.dataset.fe")
def vis(pg, s): return pg.evaluate("(s)=>{const e=document.querySelector(s);if(!e)return false;const r=e.getBoundingClientRect(),c=getComputedStyle(e);return c.display!=='none'&&c.visibility!=='hidden'&&r.width>0}", s)
with sync_playwright() as p:
    ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']; b = p.chromium.launch(args=ARGS)
    for (w, h, mob, tag) in ((1280, 720, False, 'desktop'), (412, 915, True, 'phone-portrait'), (915, 412, True, 'phone-landscape')):
        if os.environ.get('ONLY') and tag not in os.environ['ONLY'].split(','): continue
        b.close(); b = p.chromium.launch(args=ARGS)   # fresh browser per viewport: SwiftShader leaks GPU memory across contexts
        ctx = b.new_context(viewport={'width': w, 'height': h}, has_touch=mob, is_mobile=mob, service_workers='block'); errs = []
        pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(BASE)
        pg.wait_for_function("window.__fe", timeout=60000); ok(f'{tag} loading screen shown first', pg.evaluate('__fe.hist[0]') == 'load', pg.evaluate('__fe.hist'))
        if tag == 'desktop' and scr(pg) == 'load': pg.screenshot(path=f'{SH}/1-loading.png')
        pg.wait_for_function("document.body.dataset.fe==='title'", timeout=180000); ok(f'{tag} load -> title', scr(pg) == 'title')
        ok(f'{tag} game HUD hidden on title', not vis(pg, '#hud'))
        y0 = pg.evaluate('__p3d.state.camYaw'); pg.wait_for_timeout(2500); ok(f'{tag} title camera drifts', pg.evaluate('__p3d.state.camYaw') != y0)
        pg.wait_for_function('__p3d.wanderers >= 4', timeout=60000)
        f0 = pg.evaluate('__p3d.frames'); w0 = pg.evaluate('__p3d.wanderPos'); pg.wait_for_function(f'__p3d.frames > {f0} + 25', timeout=90000); w1 = pg.evaluate('__p3d.wanderPos')
        ok(f'{tag} wanderers walk around', sum(1 for a, b in zip(w0, w1) if abs(a[0]-b[0]) + abs(a[1]-b[1]) > 0.1) >= 2, (w0, w1))
        print('INFO', tag, 'title draw calls', pg.evaluate('__p3d.renderer.info.render.calls'))
        ok(f'{tag} title wanderers 4-8', 4 <= pg.evaluate('__p3d.wanderers') <= 8, pg.evaluate('__p3d.wanderers'))
        pg.screenshot(path=f'{SH}/2-title-{tag}.png')
        if tag == 'desktop': pg.screenshot(path=f'{SH}/2b-title-wanderers.png')
        # hidden cheats gesture: 5 quick taps on the version label
        for _ in range(5):
            pg.evaluate("(()=>{const v=document.getElementById('fe-ver');for(const t of ['pointerdown','pointerup'])v.dispatchEvent(new PointerEvent(t,{bubbles:true,pointerId:1,pointerType:'touch'}))})()"); pg.wait_for_timeout(60)
        pg.wait_for_timeout(2500)
        ok(f'{tag} 5-tap cheats gesture opens the owner gate', pg.evaluate("!!(document.getElementById('ownerLogin')||document.getElementById('ownerPanel'))"))
        if tag == 'desktop': pg.screenshot(path=f'{SH}/3-cheats-gate.png')
        pg.reload(); pg.wait_for_function("document.body.dataset.fe==='title'", timeout=180000)
        pg.click('#fe-title [data-a=play]'); pg.wait_for_timeout(1500)
        w0 = pg.evaluate('__p3d.wanderPos'); pg.wait_for_timeout(2000); w1 = pg.evaluate('__p3d.wanderPos')
        ok(f'{tag} wander paused while a menu covers the screen', sum(abs(a[0]-b[0]) + abs(a[1]-b[1]) for a, b in zip(w0, w1)) < 1.0, (w0, w1))
        ok(f'{tag} character select', scr(pg) == 'sel' and pg.evaluate("document.querySelectorAll('#fe-roster button').length") > 0)
        n = pg.evaluate("document.querySelectorAll('#fe-roster button').length")
        if n > 1: pg.click('#fe-roster button[data-i="1"]'); pg.wait_for_timeout(1500)
        ok(f'{tag} stats/size/skills panel', 'm' in pg.inner_text('#fe-size') and pg.evaluate("document.querySelectorAll('#fe-skills div').length") >= 6 and pg.inner_text('#fe-stats') != '')
        pg.wait_for_function('__fe.preview.on && __fe.preview.id', timeout=60000); pv0 = pg.evaluate('__fe.preview')
        ok(f'{tag} 3D preview renders the real model with idle', pv0['canvas'] and pv0['h'] > 0.5 and pv0['idle'], pv0)
        ok(f'{tag} preview canvas has pixels', pg.evaluate("(()=>{const c=document.getElementById('fe-pv');return c.width>50&&c.height>50})()"))
        if n > 2:
            pg.click('#fe-roster button[data-i="2"]'); pg.wait_for_function(f"__fe.preview.id && __fe.preview.id !== {pv0['id']!r}", timeout=60000)
            ok(f'{tag} preview switches model live', pg.evaluate('__fe.preview.id') != pv0['id'], pg.evaluate('__fe.preview'))
        y0 = pg.evaluate('__fe.preview.yaw'); bb = pg.locator('#fe-pv').bounding_box(); cx, cy = bb['x'] + bb['width'] / 2, bb['y'] + bb['height'] / 2
        pg.mouse.move(cx, cy); pg.mouse.down(); pg.mouse.move(cx + 120, cy, steps=6); pg.mouse.up(); y1 = pg.evaluate('__fe.preview.yaw')
        ok(f'{tag} drag spins the model', y1 - y0 > 0.8, (y0, y1))
        pg.wait_for_timeout(4000); ok(f'{tag} auto-rotates when idle', pg.evaluate('__fe.preview.yaw') > y1 + 0.2, (y1, pg.evaluate('__fe.preview.yaw')))
        pg.screenshot(path=f'{SH}/4-select-{tag}.png')
        pg.click('#fe-sel [data-a=begin]'); pg.wait_for_timeout(100)
        ok(f'{tag} no model on loading screen (preview disposed)', not pg.evaluate('__fe.preview.on') and not pg.evaluate('__fe.preview.canvas'), pg.evaluate('__fe.preview')); pg.wait_for_timeout(500); ok(f'{tag} loading with tips', scr(pg) == 'load' and pg.inner_text('#fe-tip') != '')
        pg.wait_for_function("document.body.dataset.fe==='game'", timeout=60000); pg.wait_for_timeout(1500)
        ok(f'{tag} title-only wanderers removed in game (party/NPCs unchanged)', pg.evaluate('__p3d.titleExtrasN') == 0, pg.evaluate('__p3d.titleExtrasN'))
        ok(f'{tag} in game, HUD visible', vis(pg, '#hud') and vis(pg, '#fe-pbtn'))
        if tag != 'desktop': pg.screenshot(path=f'{SH}/5-game-{tag}.png')
        pg.click('#fe-pbtn'); pg.wait_for_timeout(800); f0 = pg.evaluate('__p3d.frames'); pg.wait_for_timeout(1500)
        ok(f'{tag} pause stops the loop', scr(pg) == 'pause' and pg.evaluate('__p3d.frames') == f0, (f0, pg.evaluate('__p3d.frames')))
        pg.screenshot(path=f'{SH}/6-pause-{tag}.png')
        pg.click('#fe-pause [data-a=set]'); pg.wait_for_timeout(500); ok(f'{tag} settings', scr(pg) == 'set')
        if tag == 'desktop': pg.screenshot(path=f'{SH}/7-settings.png')
        pg.click('#fe-set [data-a=close]'); pg.click('#fe-pause [data-a=resume]'); pg.wait_for_timeout(1500)
        ok(f'{tag} resume runs again', scr(pg) == 'game' and pg.evaluate('__p3d.frames') > f0)
        pg.click('#fe-pbtn'); pg.click('#fe-pause [data-a=quit]'); pg.wait_for_function("document.body.dataset.fe==='title'"); pg.wait_for_timeout(500); pg.wait_for_timeout(1300); pg.click('#fe-title [data-a=cred]'); pg.wait_for_timeout(500)
        ok(f'{tag} credits', scr(pg) == 'cred')
        if tag == 'desktop': pg.screenshot(path=f'{SH}/8-credits.png')
        ok(f'{tag} no page errors', not errs, errs)
        ctx.close()
    # existing test URLs (with params) must not show the front end
    ctx = b.new_context(service_workers='block'); pg = ctx.new_page(); pg.goto(BASE + '?party=0&npcs=0')
    pg.wait_for_function('window.__p3d && __p3d.frames > 3', timeout=120000); ok('front end off when URL has params', not pg.evaluate("!!document.getElementById('fe')"))
    b.close()
print('FAILURES', bad); sys.exit(1 if bad else 0)
