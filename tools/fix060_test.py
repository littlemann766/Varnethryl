"""Regression tests for the 0.6.0 phone freeze and the Mortimer spawn condition.
Usage: (cd www && python3 -m http.server 8977) then VN_URL=http://localhost:8977/index.html python3 tools/fix060_test.py
1. Negative first-frame dt (rAF timestamp earlier than performance.now() at module start, common on slow phones)
   used to make runtime.x/y/vx/vy NaN: blank world, no movement. Simulated by shifting rAF timestamps back.
2. An exception inside a frame must not stop the render loop.
3. Mortimer is drawn only when V1 is done and V2 is active/done."""
import os, sys
from playwright.sync_api import sync_playwright
URL = os.environ.get('VN_URL', 'http://localhost:8977/index.html')
res = []
def ok(n, c): res.append(bool(c)); print(('PASS' if c else 'FAIL'), n)
SHIFT = "const o=window.requestAnimationFrame.bind(window);let n=0;window.requestAnimationFrame=cb=>o(t=>cb(n++<3?t-120:t));"
SPY = "window.__m=0;const f=CanvasRenderingContext2D.prototype.fillText;CanvasRenderingContext2D.prototype.fillText=function(t,...a){if(t==='Mortimer')window.__m++;return f.call(this,t,...a)};"
with sync_playwright() as p:
    b = p.chromium.launch()
    for shift in (False, True):
        ctx = b.new_context(viewport={'width': 412, 'height': 915}, has_touch=True, is_mobile=True, service_workers='block')
        ctx.add_init_script((SHIFT if shift else '') + SPY)
        pg = ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(URL + '?nobrand'); pg.wait_for_timeout(1500)
        fin = pg.evaluate("[runtime=window.__vn.runtime,'x','y','vx','vy','speed'].slice(1).every(k=>Number.isFinite(window.__vn.runtime[k]))")
        ok(f'shifted-rAF={shift}: position/velocity are finite after load', fin)
        x0 = pg.evaluate("window.__vn.runtime.x")
        s = pg.locator('#stick').bounding_box(); cx, cy = s['x'] + s['width'] / 2, s['y'] + s['height'] / 2
        pg.mouse.move(cx, cy); pg.mouse.down(); pg.mouse.move(cx + 50, cy, steps=4); pg.wait_for_timeout(700); pg.mouse.up()
        ok(f'shifted-rAF={shift}: stick moves the hero', pg.evaluate("window.__vn.runtime.x") - x0 > 20)
        ok(f'shifted-rAF={shift}: no page errors', not errs)
        ctx.close()
    # render loop survives an exception in a frame
    ctx = b.new_context(viewport={'width': 412, 'height': 915}, service_workers='block'); pg = ctx.new_page(); logs = []
    pg.on('console', lambda m: logs.append(m.text) if m.type == 'error' else None)
    pg.goto(URL + '?nobrand'); pg.wait_for_timeout(800)
    pg.evaluate("window.__vn.state.zone='nope'"); pg.wait_for_timeout(300)
    pg.evaluate("window.__vn.state.zone='village'"); t0 = pg.evaluate("window.__vn.runtime.time"); pg.wait_for_timeout(500)
    ok('render loop keeps running after a thrown frame', pg.evaluate("window.__vn.runtime.time") > t0)
    ok('frame error is logged (not swallowed silently)', any('frame error' in l for l in logs))
    ctx.close()
    # Mortimer spawn condition (state is set directly; reachable and unreachable combos)
    ctx = b.new_context(viewport={'width': 412, 'height': 800}, service_workers='block'); ctx.add_init_script(SPY); pg = ctx.new_page()
    pg.goto(URL + '?nobrand'); pg.wait_for_timeout(1000)
    ok('fresh save: no Mortimer', pg.evaluate("window.__m") == 0)
    def present(ch, st, done):
        return pg.evaluate("([ch,st,done])=>{const s=window.__vn.state;s.veyra={...s.veyra,ch,stage:st,done:['V1','V2','V3','V4','V5','V6','V7'].slice(0,done)};window.__vn.Quest.rebind();return window.__vn.Quest.debug.mortimerPresent()}", [ch, st, done])
    ok('locked/V0 quest: no Mortimer', not present(1, 'locked', 0))
    ok('V1 offered (nothing done): no Mortimer', not present(1, 'offer', 0))
    ok('V1 active: no Mortimer', not present(1, 'active', 0))
    ok('V1 done, V2 offered: no Mortimer yet', not present(2, 'offer', 1))
    ok('V2 active: Mortimer walks with the party', present(2, 'active', 1))
    ok('V2 done, V3 offered: Mortimer present', present(3, 'offer', 2))
    ok('V4 active: Mortimer present', present(4, 'active', 3))
    ok('inconsistent save (ch3, only V1 done): no Mortimer', not present(3, 'active', 1))
    ok('inconsistent save (ch1 finished, V1 done): no Mortimer', not present(1, 'finished', 1))
    ok('inconsistent save (ch2 locked, V1 done): no Mortimer', not present(2, 'locked', 1))
    pg.evaluate("window.__m=0"); present(2, 'offer', 1); pg.wait_for_timeout(300); ok('not drawn on the map when absent', pg.evaluate("window.__m") == 0)
    present(2, 'active', 1); pg.evaluate("window.__m=0"); pg.wait_for_timeout(400); ok('drawn on the map when present', pg.evaluate("window.__m") > 0)
    b.close()
print(f'{sum(res)}/{len(res)} passed'); sys.exit(0 if all(res) else 1)
