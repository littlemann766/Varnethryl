#!/usr/bin/env python3
"""HUD restyle (hudui prototype): gold card, prototype bars, pad positions, skill names; every kit hero shows its own 3 skills + ultimate; Owner shows the Owner cluster. SHOTS=dir."""
import http.server, threading, functools, os, sys, json
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(s, *a, **k): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start(); bad = 0; SH = os.environ.get('SHOTS')
def T(n, c, d=''):
    global bad; print('PASS' if c else 'FAIL', n, '' if c else d); bad += 0 if c else 1
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']); pg = b.new_context(viewport={'width':844,'height':390}, has_touch=True, is_mobile=True).new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1&npcs=0&party=0', wait_until='commit', timeout=120000); pg.wait_for_function('window.__p3d&&__p3d.frames>5', timeout=120000); pg.wait_for_timeout(1500)
    pg.evaluate("window.__p3d.owner=true; window.__p3d.cheats=window.__p3d.cheats||{}"); pg.evaluate("__p3d.fightToggle()"); pg.wait_for_function("__p3d.fight&&__p3d.fight.on", timeout=60000); pg.wait_for_timeout(1500)
    g = pg.evaluate("""(()=>{const r=s=>document.querySelector('#cb '+s).getBoundingClientRect(),cs=s=>getComputedStyle(document.querySelector('#cb '+s));
      return {b0:r('.sl.b0').toJSON(),b1:r('.sl.b1').toJSON(),b2:r('.sl.b2').toJSON(),b3:r('.sl.b3').toJSON(),b4:r('.sl.b4').toJSON(),vit:r('.vit').toJSON(),vitBorder:cs('.vit').borderTopColor,hp:cs('.vit .hp i').backgroundImage,
        names:[...document.querySelectorAll('#cb .sl .nmL')].map(e=>e.textContent),lab:document.querySelector('#cb .vit .lab').textContent,basic:document.querySelectorAll('#cb .sl.b0').length}})()""")
    if SH: pg.screenshot(path=f'{SH}/hud_owner.png')
    T('one Basic Attack control', g['basic'] == 1 and g['names'][0] == 'Basic Attack')
    T('basic is the biggest, bottom-right corner', g['b0']['width'] > g['b1']['width'] * 1.3 and g['b0']['right'] > 800 and g['b0']['bottom'] > 340, g['b0'])
    T('ultimate sits above basic', g['b4']['bottom'] <= g['b0']['top'] + 8 and abs(g['b4']['right'] - g['b0']['right']) < 12, [g['b4'], g['b0']])
    T('skills 1-3 arc left/above basic', all(g[k]['right'] < g['b0']['left'] + 30 for k in ('b1','b2')) and g['b3']['bottom'] < g['b0']['top'] + 30)
    T('all buttons round and inside the viewport', all(abs(g[k]['width'] - g[k]['height']) < 2 and g[k]['left'] >= 0 and g[k]['top'] >= 0 for k in ('b0','b1','b2','b3','b4')))
    T('prototype card: gold border + top-left', g['vit']['top'] < 90 and g['vit']['left'] < 40 and g['vitBorder'] == 'rgb(150, 116, 63)', g)
    T('prototype HP gradient', '118, 33, 38' in g['hp'], g['hp'])
    T('Owner cluster names', g['names'][1:4] == ['Royal Slash', 'Shadow Chains', "Sovereign's Wrath"], g['names'])
    kits = pg.evaluate("(async()=>{const m=await import('./proto3d/combat/herokits.js');return Object.fromEntries(Object.entries(m.KITS).map(([k,v])=>[k,v.skills.map(s=>s.name)]))})()")
    ok = 0; miss = []
    pg.evaluate("window.__p3d.owner=false")   # account owner gate shows the Owner cluster on any hero; kits show for everyone else
    for k, names in kits.items():
        i = pg.evaluate("(k=>__p3d.modelStatus().models.findIndex(m=>m.id.replace(/^[a-z]:/,'').split('_')[0]===k))", k)
        if i < 0: miss.append((k, 'no model')); continue
        pg.evaluate("i=>__p3d.selectHero(i)", i)
        try: pg.wait_for_function("(n=>[...document.querySelectorAll('#cb .sl .nmL')].map(e=>e.textContent)[1]===n)", arg=names[0], timeout=20000)
        except Exception: pass
        got = pg.evaluate("[...document.querySelectorAll('#cb .sl .nmL')].map(e=>e.textContent)")
        if got[1:5] == names[:4]: ok += 1
        else: miss.append((k, got, names))
        if SH and k in ('aldric', 'brynn'): pg.screenshot(path=f'{SH}/hud_{k}.png')
    T(f'every kit hero shows its own kit ({ok}/{len(kits)})', ok == len(kits), miss[:2])
    T('vit label shows name and level', 'LV' in pg.evaluate("document.querySelector('#cb .vit .lab').textContent"))
    pg.set_viewport_size({'width': 390, 'height': 844}); pg.wait_for_timeout(500)
    q = pg.evaluate("(()=>{const r=s=>document.querySelector('#cb '+s).getBoundingClientRect();const a=r('.cl'),c=r('.sl.b2'),v=r('.vit');return {cl:a.toJSON(),b2:c.toJSON(),vit:v.toJSON()}})()")
    if SH: pg.screenshot(path=f'{SH}/hud_portrait.png')
    T('portrait: utility pad does not overlap the skill arc', q['cl']['bottom'] <= q['b2']['top'] + 2 or q['cl']['right'] <= q['b2']['left'], q)
    T('no page errors', not errs, errs[:2]); b.close()
print('FAILED' if bad else 'ALL PASS'); sys.exit(1 if bad else 0)
