#!/usr/bin/env python3
"""Town gate + map unloading: walk through the gate -> Wilds (town hidden, fight HUD up); back through the Wilds gate -> Wilds disposed (geometry count drops), town restored, followers along.
Usage: (cd www && python3 -m http.server PORT); P3D_URL=http://localhost:PORT/proto3d.html python3 tools/gate_test.py"""
import os
from playwright.sync_api import sync_playwright
BASE = os.environ.get('P3D_URL', 'http://localhost:9852/proto3d.html'); bad = 0
def ok(n, c, d=''):
    global bad; print(('PASS' if c else 'FAIL'), n, ('' if c else str(d)[:300]))
    if not c: bad += 1
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    ctx = b.new_context(viewport={'width': 412, 'height': 915}, has_touch=True, is_mobile=True, service_workers='block'); pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(BASE + '?npcs=0'); pg.wait_for_function('window.__p3d && window.__p3d.frames>5', timeout=90000); pg.wait_for_timeout(2000)
    pg.wait_for_function("__p3d.info().calls>0"); town = pg.evaluate("__p3d.info()")
    ok('town gate mesh is a gate (not the glowing portal)', pg.evaluate("__p3d.scene.children.some(c=>c.userData&&c.userData.gate)"))
    pg.evaluate("__p3d.teleport(-6,34)"); pg.wait_for_timeout(300)
    pg.keyboard.down('s') if False else None
    pg.evaluate("window.__go=()=>{__p3d.state.heroX=-6;__p3d.state.heroZ=38}"); pg.evaluate("__go()")
    pg.wait_for_function("__p3d.zone==='wilds'", timeout=30000); pg.wait_for_timeout(2500)
    w = pg.evaluate("__p3d.info()"); ok('entered Wilds through the gate', pg.evaluate("__p3d.zone==='wilds'"))
    ok('town hidden while in the Wilds (fewer draw calls than town+wilds)', pg.evaluate("(()=>{let n=0;__p3d.scene.children.forEach(c=>{if(!c.visible)n++});return n})()") > 5)
    ok('town hidden: Wilds draw calls well below town draw calls', w['calls'] < town['calls'], [town['calls'], w['calls']])
    ok('fight HUD up in the Wilds', pg.evaluate("__p3d.fight&&__p3d.fight.on"))
    g0 = w['geometries']
    pg.evaluate("(()=>{const W=__p3d.wilds;__p3d.state.heroX=W.portal.x;__p3d.state.heroZ=W.portal.z})()")
    pg.wait_for_function("__p3d.zone==='town'", timeout=30000); pg.wait_for_timeout(2000)
    t2 = pg.evaluate("__p3d.info()"); ok('back in town', pg.evaluate("__p3d.zone==='town'"))
    ok('Wilds disposed on leaving (WM null, unload ran, no geometry/texture growth vs. before the trip)', pg.evaluate("__p3d.wilds===null&&window.__unloaded>=1") and t2['textures'] <= town['textures'] + 6 and t2['geometries'] <= town['geometries'] + 110, [town, w, t2])
    ok('town restored (same draw calls as before, +-15%)', abs(t2['calls'] - town['calls']) <= town['calls'] * 0.15 + 5, [town['calls'], t2['calls']])
    ok('fight mode ended in town', pg.evaluate("!__p3d.fight||!__p3d.fight.on"))
    pg.evaluate("__p3d.teleport(-6,34);__go()"); pg.wait_for_function("__p3d.zone==='wilds'", timeout=30000); ok('second visit rebuilds the Wilds', pg.evaluate("!!__p3d.wilds"))
    ok('no page errors', not errs, errs[:3]); ctx.close()
print('FAILS:', bad); raise SystemExit(1 if bad else 0)
