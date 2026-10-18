#!/usr/bin/env python3
"""Playwright test for the 3D prototype. Usage: python3 tools/proto3d_test.py [shots_dir]"""
import sys, subprocess, time, os, json
from pathlib import Path
from playwright.sync_api import sync_playwright
root = Path(__file__).resolve().parents[1] / 'www'
shots = Path(sys.argv[1] if len(sys.argv) > 1 else '/workspace/shots/proto3d'); shots.mkdir(parents=True, exist_ok=True)
PORT = 8765
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT), '-d', str(root)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
errors, results = [], {}
def check(name, ok, detail=''):
    results[name] = ok; print(('PASS' if ok else 'FAIL'), name, detail)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, has_touch=True, is_mobile=True)
        page = ctx.new_page()
        page.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(f'http://localhost:{PORT}/proto3d.html'); page.wait_for_function('window.__p3d && window.__p3d.frames > 5', timeout=30000)
        page.wait_for_timeout(1500)
        check('loads', True, json.dumps(page.evaluate('window.__p3d.info()')))
        st = lambda: page.evaluate('({x:__p3d.state.heroX,z:__p3d.state.heroZ,moving:__p3d.state.moving,col:__p3d.state.collisions})')
        page.screenshot(path=str(shots / '01-portrait-start-390x844.png'))
        # joystick drag up (forward = -z)
        s0 = st(); box = page.locator('#stick').bounding_box(); cx, cy = box['x'] + box['width'] / 2, box['y'] + box['height'] / 2
        page.evaluate(f"""(()=>{{const s=document.getElementById('stick');const f=(t,x,y)=>s.dispatchEvent(new PointerEvent(t,{{pointerId:7,clientX:x,clientY:y,bubbles:true,isPrimary:true}}));window.__jf=f;f('pointerdown',{cx},{cy});f('pointermove',{cx},{cy-45});}})()""")
        page.wait_for_timeout(1500); s1 = st()
        page.screenshot(path=str(shots / '02-portrait-walking-joystick.png'))
        page.evaluate(f"window.__jf('pointerup',{cx},{cy})")
        check('joystick moves hero', (s0['z'] - s1['z']) > 2, f"z {s0['z']:.2f} -> {s1['z']:.2f}")
        page.wait_for_timeout(500)
        # tap to move
        s0 = st(); page.mouse.click(100, 300) if False else page.touchscreen.tap(250, 420); page.wait_for_timeout(2500); s2 = st()
        check('tap-to-move moves hero', abs(s2['x'] - s0['x']) + abs(s2['z'] - s0['z']) > 1.5, f"({s0['x']:.1f},{s0['z']:.1f}) -> ({s2['x']:.1f},{s2['z']:.1f})")
        # collision: guild hall at (0,-19) w13 d7.5 -> solid front wall face z=-15.25 (door gap is only x in [-1,1]); walk north at x=4.5.
        BI = lambda i: page.evaluate("(id)=>{const b=__p3d.multi.find(x=>x.id===id);return {cx:b.cx,cz:b.cz,w:b.footprint.w,d:b.footprint.d,K:b.K,rot:b.rot}}", i)
        g = BI('guildhall'); inn = BI('inn')
        page.evaluate('([x,z])=>{__p3d.teleport(x,z); __p3d.setCamYaw(0)}', [g['cx'] + 6.0 * g['K'], g['cz'] + g['d'] / 2 * g['K'] + 7.0]); 
        page.wait_for_timeout(300)
        page.evaluate("window.__jf('pointerdown',%f,%f); window.__jf('pointermove',%f,%f)" % (cx, cy, cx, cy - 50))
        page.wait_for_timeout(3500); s3 = st()
        page.screenshot(path=str(shots / '03-portrait-blocked-by-guildhall.png'))
        page.evaluate(f"window.__jf('pointerup',{cx},{cy})")
        limit = g['cz'] + g['d'] / 2 * g['K'] + 0.75
        check('building blocks hero', s3['z'] >= limit - 0.05 and s3['col'] > 0, f"z={s3['z']:.2f} (wall face limit {limit:.2f}) collisions={s3['col']}")
        # fountain collision (circle r 3.5 + 0.5): from (0,9) walk north along x=0
        page.evaluate('__p3d.teleport(0,26)'); page.wait_for_timeout(200)
        page.evaluate("window.__jf('pointerdown',%f,%f); window.__jf('pointermove',%f,%f)" % (cx, cy, cx, cy - 50)); page.wait_for_timeout(3000)
        s4 = st(); page.evaluate(f"window.__jf('pointerup',{cx},{cy})")
        check('fountain blocks hero', s4['z'] > 0.5 or abs(s4['x']) > 0.5, f"({s4['x']:.2f},{s4['z']:.2f})")
        # --- walk-in door: inn at (-13,-9) w9 d7 -> door at z=-5.5, x=-13
        page.evaluate('([x,z])=>{__p3d.teleport(x,z); __p3d.setCamYaw(0)}', [inn['cx'], inn['cz'] + inn['d'] / 2 * inn['K'] + 4.0]); page.wait_for_timeout(300)
        page.evaluate("window.__jf('pointerdown',%f,%f); window.__jf('pointermove',%f,%f)" % (cx, cy, cx, cy - 50))
        page.wait_for_timeout(2200); s5 = page.evaluate('({z:__p3d.state.heroZ,x:__p3d.state.heroX,inside:__p3d.state.inside})')
        page.screenshot(path=str(shots / '07-inn-interior-walked-in.png'))
        page.evaluate(f"window.__jf('pointerup',{cx},{cy})")
        check('hero walks through inn door and is inside', s5['inside'] == 'inn' and s5['z'] < inn['cz'] + inn['d'] / 2 * inn['K'] - 0.5, json.dumps(s5))
        # side wall of the inn still blocks (outside, x=-13 -> walk west into wall at x=-17.5)
        page.evaluate('([x,z])=>{__p3d.teleport(x,z); __p3d.setCamYaw(0)}', [inn['cx'] - inn['w'] / 2 * inn['K'] - 5.0, inn['cz']]); page.wait_for_timeout(200)
        page.evaluate("window.__jf('pointerdown',%f,%f); window.__jf('pointermove',%f,%f)" % (cx, cy, cx + 50, cy)); page.wait_for_timeout(2500)
        s6 = st(); page.evaluate(f"window.__jf('pointerup',{cx},{cy})")
        check('inn side wall blocks hero', s6['x'] <= inn['cx'] - inn['w'] / 2 * inn['K'] - 0.75 + 0.05, f"x={s6['x']:.2f}")
        for i, nm in enumerate(['aldric', 'umbral', 'selene']):
            page.evaluate(f'__p3d.setHero({i}); __p3d.teleport(0,14); __p3d.setCamYaw(0)'); page.wait_for_timeout(900)
            page.screenshot(path=str(shots / f'08-gameplay-{nm}-390x844.png'))
        page.evaluate('__p3d.setHero(0)')
        # views
        page.evaluate('__p3d.teleport(-3,12); __p3d.setCamYaw(0.5)'); page.wait_for_timeout(1500)
        page.screenshot(path=str(shots / '04-portrait-plaza-fountain.png'))
        page.evaluate('__p3d.teleport(-8,-1); __p3d.setCamYaw(2.4)'); page.wait_for_timeout(1500)
        page.screenshot(path=str(shots / '05-portrait-inn-view.png'))
        # fps sample
        page.evaluate('__p3d.teleport(0,14); __p3d.setCamYaw(0)'); page.wait_for_timeout(1000)
        f0 = page.evaluate('__p3d.frames'); page.wait_for_timeout(5000); f1 = page.evaluate('__p3d.frames')
        results['headless_fps_swiftshader_390x844_dpr2'] = (f1 - f0) / 5; print('FPS (software GL, 390x844 @dpr2->1.5 cap):', (f1 - f0) / 5)
        results['info'] = page.evaluate('__p3d.info()')
        # landscape
        page.set_viewport_size({'width': 844, 'height': 390}); page.wait_for_timeout(1500)
        page.screenshot(path=str(shots / '06-landscape-844x390.png'))
        f0 = page.evaluate('__p3d.frames'); page.wait_for_timeout(4000); f1 = page.evaluate('__p3d.frames')
        results['headless_fps_landscape'] = (f1 - f0) / 4; print('FPS landscape:', (f1 - f0) / 4)
        b.close()
finally:
    srv.terminate()
check('no console errors/warnings', not errors, '; '.join(errors[:5]))
print(json.dumps(results, indent=1))
sys.exit(0 if all(v for k, v in results.items() if isinstance(v, bool)) else 1)
