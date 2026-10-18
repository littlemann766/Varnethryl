#!/usr/bin/env python3
"""Headless check of the 3D bump system. Usage: (cd www && python3 -m http.server 9411) then python3 tools/bump_browser_test.py [shots_dir]"""
import sys, json, os
from playwright.sync_api import sync_playwright
BASE = os.environ.get('P3D_URL', 'http://localhost:9411/proto3d.html')
shots = sys.argv[1] if len(sys.argv) > 1 else '/tmp/bumpshots'; os.makedirs(shots, exist_ok=True)
bad = 0
def ok(n, c, d=''):
    global bad; print(('PASS' if c else 'FAIL'), n, d)
    if not c: bad += 1
def calls(pg):
    pg.wait_for_timeout(1200); return pg.evaluate('(()=>{const r=__p3d.renderer;return r.info.render.calls})()')
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    base_calls = None
    for (w, h, mob) in ((1920, 1080, False), (412, 915, True)):
        ctx = b.new_context(viewport={'width': w, 'height': h}, has_touch=mob, is_mobile=mob, service_workers='block')
        pg = ctx.new_page(); errs = []
        pg.on('console', lambda m: errs.append(m.text) if m.type in ('error', 'warning') else None); pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(BASE + '?party=0&npcs=0'); pg.wait_for_function('window.__p3d && window.__p3d.frames > 5', timeout=60000); pg.wait_for_timeout(1500)
        c0 = calls(pg); ok(f'{w}x{h} loads, no actors', c0 > 0, f'draw calls {c0}')
        if base_calls is None: base_calls = c0
        pg.close()
        pg = ctx.new_page(); pg.on('console', lambda m: errs.append(m.text) if m.type in ('error', 'warning') else None); pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(BASE); pg.wait_for_function('window.__p3d && window.__p3d.frames > 5', timeout=60000)
        pg.wait_for_function('__p3d.bump.crowd.length>0 && __p3d.bump.crowd.every(r=>r.root)', timeout=60000); pg.wait_for_timeout(1500)
        c1 = calls(pg); n = pg.evaluate('__p3d.bump.crowd.length')
        ok(f'{w}x{h} default party+NPC load', True, f'{n} actors, draw calls {c1} (hero only {c0}, +{(c1-c0)/max(1,n):.1f}/actor)')
        pg.screenshot(path=f'{shots}/bump-{w}x{h}.png')
        from PIL import Image
        im = Image.open(f'{shots}/bump-{w}x{h}.png').convert('RGB').resize((64, 64)); px = len(set((r >> 4, g >> 4, b2 >> 4) for r, g, b2 in (im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata())))
        ok(f'{w}x{h} canvas not blank (screenshot colour count)', px > 20, f'{px} distinct colours')
        if not mob:
            # bump: put player just behind the first follower, running at it
            pg.evaluate("(()=>{const f=__p3d.bump.crowd[0].a;f.group=null;__p3d.teleport(f.x,f.z+3);__p3d.setCamYaw(0)})()")
            pg.wait_for_timeout(300)
            pg.keyboard.down('w')
            seen = pg.evaluate("""new Promise(res=>{let ev=0,tb=0,slow=0,pk=0,t0=performance.now();const sys=__p3d.bump.sys;(function f(){ev=Math.max(ev,sys.events);slow=Math.min(slow||1,__p3d.bump.player.slowMul||1);for(const r of __p3d.bump.crowd)pk=Math.max(pk,Math.abs(r.a.ptx)+Math.abs(r.a.ptz)+Math.abs(r.a.phop));if(ev>0&&!tb)tb=performance.now();if(performance.now()-t0>9000||tb&&performance.now()-tb>450)res({ev,slow,pk,bumped:__p3d.bump.crowd.map(r=>r.a.bumped),runs:__p3d.bump.player.bumps});else requestAnimationFrame(f)})()})""")
            pg.keyboard.up('w')
            ok('running into a non-party character triggers a bump (followers no longer bump)', seen['ev'] >= 1 and seen['runs'] >= 1 and sum(seen['bumped']) >= 1, json.dumps(seen))
            ok('runner slows briefly (<1) and bumped poses', seen['slow'] < 1 and seen['pk'] > 0.02)
            pg.screenshot(path=f'{shots}/bump-hit-{w}x{h}.png')
            pg.wait_for_timeout(3000)
            c2 = calls(pg); ok('draw calls do not grow during/after bump', c2 <= c1 + 2, f'{c1} -> {c2}')
            fin = pg.evaluate("__p3d.bump.crowd.every(r=>isFinite(r.a.x)&&isFinite(r.a.z)) && isFinite(__p3d.state.heroX)")
            ok('positions finite', fin)
        ok(f'{w}x{h} no console errors/warnings', not errs, '; '.join(errs[:3]))
        ctx.close()
    ok('draw calls with no actors identical to main baseline', base_calls == int(os.environ.get('BASE_CALLS', '-1')), f'{base_calls} vs BASE_CALLS={os.environ.get("BASE_CALLS")}')
print('FAILED %d' % bad if bad else 'ALL PASS'); sys.exit(1 if bad else 0)
