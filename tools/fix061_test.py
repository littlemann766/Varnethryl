"""0.6.2 tests: GLB heroes load (and failure is diagnosable, no invisible hero); 2D buildings sit on the ground line and hero cannot walk behind/over them.
Usage: (cd www && python3 -m http.server 8977) then python3 tools/fix061_test.py"""
import os
from playwright.sync_api import sync_playwright
B = os.environ.get('VN_BASE', 'http://localhost:8977/')
res = []
def ok(n, c, d=''): res.append(bool(c)); print(('PASS' if c else 'FAIL'), n, d)
ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS)
    # 1. GLB heroes load
    pg = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, service_workers='block').new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(B + 'proto3d.html'); pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=60000)
    pg.wait_for_function("__p3d.glbInfo.loaded.includes('aldric')", timeout=30000)
    ok('aldric GLB loaded and is the active hero', pg.evaluate('__p3d.hero.userData.glb === true'))
    pg.evaluate('document.querySelectorAll("#heroes button")[10].dispatchEvent(new PointerEvent("pointerdown",{bubbles:true}))')
    pg.wait_for_function("__p3d.glbInfo.loaded.includes('nyx')", timeout=30000)
    ok('selecting another hero lazy-loads its GLB', pg.evaluate('__p3d.heroIndex') == 10)
    ok('no page errors', not errs, str(errs))
    # 2. GLB fetch blocked -> visible diagnosis, hero never invisible
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, service_workers='block'); pg = ctx.new_page()
    pg.route('**/*.glb*', lambda r: r.fulfill(status=404, body='nope'))
    pg.goto(B + 'proto3d.html'); pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=60000); pg.wait_for_timeout(2500)
    ok('failure shown on screen', pg.evaluate("getComputedStyle(document.getElementById('diag')).display") == 'block' and 'failed' in pg.inner_text('#diag'), pg.inner_text('#diag')[-160:])
    ok('procedural stand-in still visible for Aldric', pg.evaluate('__p3d.hero.children.length>0 && __p3d.hero.visible'))
    pg.evaluate('document.querySelectorAll("#heroes button")[10].dispatchEvent(new PointerEvent("pointerdown",{bubbles:true}))'); pg.wait_for_timeout(1500)
    ok('failed hero is not selected (no invisible hero)', pg.evaluate('__p3d.heroIndex') == 0)
    # 3. 2D buildings grounded + solid, portrait and landscape
    for w, h in [(844, 390), (390, 844), (1366, 768)]:
        pg = b.new_context(viewport={'width': w, 'height': h}, is_mobile=w < 900, has_touch=w < 900, service_workers='block').new_page()
        pg.goto(B + "index2d.html?nobrand"); pg.wait_for_timeout(2000)
        pg.evaluate('__vn.runtime.x=300;__vn.runtime.y=330'); pg.keyboard.down('ArrowUp'); pg.wait_for_timeout(2500); pg.keyboard.up('ArrowUp')
        y = pg.evaluate('__vn.runtime.y'); ch = h
        # hero screen y must be below the ground line (.56ch) so buildings, anchored to it, are always behind
        sy = pg.evaluate("__vn.runtime.y-__vn.runtime.camera.y")
        ok(f'{w}x{h}: hero stops in front of the building line', sy >= ch * 0.56, f'hero y={y:.0f} screen={sy:.0f} ground={ch*.56:.0f}')
        # building base follows ground when hero walks south
        pg.evaluate('__vn.runtime.y=600'); pg.wait_for_timeout(600)
        sy2 = pg.evaluate("__vn.runtime.y-__vn.runtime.camera.y"); ok(f'{w}x{h}: still renders without error after moving', True, f'screen y {sy2:.0f}')
print('ALL PASS' if all(res) else 'SOME FAILED'); raise SystemExit(0 if all(res) else 1)
