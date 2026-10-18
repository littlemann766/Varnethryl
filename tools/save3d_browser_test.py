#!/usr/bin/env python3
"""Browser check of proto3d <-> 2D shared save. Usage: python3 -m http.server PORT (in www) ; P3D_BASE=http://localhost:PORT python3 tools/save3d_browser_test.py"""
import os, sys, json
from playwright.sync_api import sync_playwright
from PIL import Image
BASE = os.environ.get('P3D_BASE', 'http://localhost:9511'); KEY = 'guildbound_rpg_save_v1'
OLD = json.load(open(os.environ.get('OLD_SAVE', '/workspace/old_save.json')))
bad = 0
def ok(n, c, d=''):
    global bad; print('PASS' if c else 'FAIL', n, d if not c else '')
    if not c: bad += 1
ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
def colors(path):
    im = Image.open(path).convert('RGB').resize((64, 64)); return len(set(im.getdata()))
def open3d(ctx, errs, q=''):
    pg = ctx.new_page(); pg.on('console', lambda m: errs.append(m.text) if m.type in ('error', 'warning') else None); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(BASE + '/proto3d.html' + q); pg.wait_for_function('window.__p3d && window.__p3d.frames > 5', timeout=90000); pg.wait_for_timeout(1500); return pg
def hide(pg):
    pg.evaluate("Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});document.dispatchEvent(new Event('visibilitychange'))")
with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS)
    for (w, h, mob) in ((1920, 1080, False), (412, 915, True)):
        tag = f'{w}x{h}'; errs = []
        ctx = b.new_context(viewport={'width': w, 'height': h}, has_touch=mob, is_mobile=mob, service_workers='block')
        # 1. no save: defaults, baseline calls, nothing written until moved
        pg = open3d(ctx, errs, '?party=0&npcs=0')
        pg.wait_for_timeout(1200); c = pg.evaluate('__p3d.renderer.info.render.calls')
        ok(tag + ' no-save loads; baseline calls', c > 0, str(c)); print('  baseline draw calls', tag, c)
        if not mob: ok('baseline 176 @1920x1080', c == int(os.environ.get('BASE_CALLS', '176')), str(c))
        ok(tag + ' no-save: 20 hero buttons', pg.evaluate('document.querySelectorAll("#heroes button").length') == 20)
        pg.close()
        # 2. corrupt save: defaults, not overwritten
        pg = ctx.new_page(); pg.goto(BASE + '/proto3d.html?party=0&npcs=0'); pg.evaluate(f"localStorage.setItem('{KEY}','{{corrupt')"); pg.close()
        pg = open3d(ctx, errs, '?party=0&npcs=0')
        ok(tag + ' corrupt save: defaults (20 buttons)', pg.evaluate('document.querySelectorAll("#heroes button").length') == 20)
        pg.evaluate('__p3d.teleport(5,20)'); pg.wait_for_timeout(1800); pg.evaluate('__p3d.flushSave()')
        ok(tag + ' corrupt save untouched', pg.evaluate(f"localStorage.getItem('{KEY}')") == '{corrupt')
        pg.close()
        # 3. old 2D save with a custom party -> 3D uses it
        s = dict(OLD); s['party'] = [3, 0, 19]; s['unlocked'] = sorted(set(s['unlocked']) | {3, 0, 19}); s['active'] = 3; s['zone'] = 'ruins'; s['gold'] = 4242
        pg = ctx.new_page(); pg.goto(BASE + '/proto3d.html?nosave=1&party=0&npcs=0'); pg.evaluate(f"localStorage.setItem('{KEY}',JSON.stringify({json.dumps(s)}))"); pg.close()
        pg = open3d(ctx, errs, '?npcs=0')
        pg.wait_for_function('__p3d.bump.crowd.length==2 && __p3d.bump.crowd.every(r=>r.root)', timeout=60000)
        names = pg.evaluate('[...document.querySelectorAll("#heroes button")].map(b=>b.title)')
        ok(tag + ' hero list = saved party', names == ['Sir Aldric', 'Nyx Varrin', 'Rook Wildbane'] or sorted(names) == sorted(['Sir Aldric', 'Nyx Varrin', 'Rook Wildbane']), str(names))
        pg.wait_for_function('__p3d.heroIndex==10', timeout=60000)
        ok(tag + ' selected hero = saved active (Nyx)', pg.evaluate('document.querySelector("#heroes button.on").title') == 'Nyx Varrin')
        fol = sorted(pg.evaluate('__p3d.bump.crowd.map(r=>r.a.id)')); ok(tag + ' followers = other party members', fol == ['aldric', 'rook'], str(fol))
        # move, switch hero, flush
        pg.evaluate('__p3d.teleport(-9,22)'); pg.wait_for_timeout(300)
        pg.evaluate('document.querySelectorAll("#heroes button")[2].dispatchEvent(new PointerEvent("pointerdown",{bubbles:true}))'); pg.wait_for_function('__p3d.heroIndex==13', timeout=60000)
        pg.wait_for_timeout(1500); hide(pg)
        sv = pg.evaluate(f"JSON.parse(localStorage.getItem('{KEY}'))")
        ok(tag + ' saved on visibilitychange: pos + active', sv['active'] == 19 and abs(sv['p3d']['x'] + 9) < 1.5 and sv['p3d']['zone'] == 'village', json.dumps(sv.get('p3d')) + ' active ' + str(sv['active']))
        ok(tag + ' 2D fields preserved', sv['gold'] == 4242 and sv['zone'] == 'ruins' and sv['party'] == [3, 0, 19] and sv['version'] == 1)
        fol = sorted(pg.evaluate('__p3d.bump.crowd.map(r=>r.a.id)')); ok(tag + ' follower swapped to previous hero', fol == ['aldric', 'nyx'], str(fol))
        pg.screenshot(path=f'/tmp/s3d-{tag}.png'); ok(tag + ' pixels not blank', colors(f'/tmp/s3d-{tag}.png') > 20)
        ok(tag + ' no NaN positions', pg.evaluate('isFinite(__p3d.state.heroX)&&isFinite(__p3d.state.heroZ)&&__p3d.bump.crowd.every(r=>isFinite(r.a.x)&&isFinite(r.a.z))'))
        pg.close()
        # 4. real 2D game loads the 3D-written save and re-saves it
        pg = ctx.new_page(); e2 = []; pg.on('console', lambda m: e2.append(m.text) if m.type == 'error' else None); pg.on('pageerror', lambda e: e2.append(str(e)))
        pg.goto(BASE + '/index.html'); pg.wait_for_timeout(2500)
        ok(tag + ' 2D loads 3D-written save without errors', not e2, '; '.join(e2[:3]))
        pg.screenshot(path=f'/tmp/s2d-{tag}.png'); ok(tag + ' 2D pixels not blank', colors(f'/tmp/s2d-{tag}.png') > 20)
        hide(pg); pg.wait_for_timeout(400)
        s2 = pg.evaluate(f"JSON.parse(localStorage.getItem('{KEY}'))")
        ok(tag + ' 2D re-save keeps party/active/gold and p3d', s2['party'] == [3, 0, 19] and s2['active'] == 19 and s2['gold'] == 4242 and s2.get('p3d', {}).get('zone') == 'village', json.dumps({k: s2.get(k) for k in ('party', 'active', 'gold', 'p3d')}))
        pg.close()
        # 5. 3D again restores position from 2D-resaved save
        pg = open3d(ctx, errs, '?npcs=0')
        x = pg.evaluate('__p3d.state.heroX'); ok(tag + ' 3D restores saved position after 2D round trip', abs(x + 9) < 1.5, str(x))
        pg.close()
        # 6. NaN written by a bad p3d field is ignored
        pg = ctx.new_page(); pg.goto(BASE + '/proto3d.html?nosave=1&party=0&npcs=0'); pg.evaluate(f"(()=>{{const s=JSON.parse(localStorage.getItem('{KEY}'));s.p3d={{x:null,z:'abc',zone:'frost'}};localStorage.setItem('{KEY}',JSON.stringify(s))}})()"); pg.close()
        pg = open3d(ctx, errs, '?party=0&npcs=0'); ok(tag + ' bad p3d falls back to default spawn', pg.evaluate('__p3d.state.heroX===0&&__p3d.state.heroZ===14')); pg.close()
        ok(tag + ' no console errors/warnings in 3D', not errs, '; '.join(errs[:3]))
        ctx.close()
print('FAILED %d' % bad if bad else 'ALL PASS'); sys.exit(1 if bad else 0)
