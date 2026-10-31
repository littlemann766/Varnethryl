#!/usr/bin/env python3
"""merge-all audit (412x915 touch): owner roster/default, non-owner gating, cheats on the fight host (heal/kill/spawn Titan/god), settings+camera. Needs VARNETHRYL_OWNER_PASSPHRASE.
Usage: (cd www && python3 -m http.server PORT); P3D_URL=http://localhost:PORT/proto3d.html python3 tools/merge_all_audit.py"""
import os
from playwright.sync_api import sync_playwright
BASE = os.environ.get('P3D_URL', 'http://localhost:9852/proto3d.html'); PASS = os.environ['VARNETHRYL_OWNER_PASSPHRASE'].strip(); bad = 0
def ok(n, c, d=''):
    global bad; print(('PASS' if c else 'FAIL'), n, ('' if c else str(d).replace(PASS, '***')[:300]))
    if not c: bad += 1
def click(pg, s): pg.evaluate("(s)=>{const e=document.querySelector(s);if(!e)throw new Error('missing '+s);e.click()}", s)
def safe(n, f):
    try: f()
    except Exception as e: ok(n, False, repr(e)[:250])
ROSTER = "[...document.querySelectorAll('#hlist .row button:first-child')].map(b=>b.textContent)"
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    # ---- non-owner
    ctx = b.new_context(viewport={'width': 412, 'height': 915}, has_touch=True, is_mobile=True, service_workers='block'); reqs = []; ctx.on('request', lambda r: reqs.append(r.url))
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(BASE + '?party=0&npcs=0'); pg.wait_for_function('window.__p3d && window.__p3d.frames>5', timeout=90000); pg.wait_for_timeout(2500)
    r = pg.evaluate(ROSTER); ok('non-owner: roster is a dropdown list (#hcur + #hlist), no Owner entry', pg.evaluate("!!document.getElementById('hcur')&&!!document.getElementById('hlist')") and not any(x.startswith('Owner') for x in r), r[:5])
    ok('non-owner: owner.glb / saber_owner.glb never fetched', not [u for u in reqs if 'owner.glb' in u or 'saber_owner' in u], [u for u in reqs if 'owner' in u])
    ok('non-owner: hero is not the Owner', pg.evaluate("!/owner/.test(__p3d.glbInfo.loaded.join())"))
    ctx.close()
    # ---- owner
    ctx = b.new_context(viewport={'width': 412, 'height': 915}, has_touch=True, is_mobile=True, service_workers='block'); reqs = []; ctx.on('request', lambda r: reqs.append(r.url))
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(BASE + '?party=0&npcs=0'); pg.wait_for_function('window.__p3d && window.__p3d.frames>5', timeout=90000); pg.wait_for_timeout(1500)
    for _ in range(5): pg.evaluate("(()=>{const v=document.getElementById('ver');for(const t of ['pointerdown','pointerup'])v.dispatchEvent(new PointerEvent(t,{bubbles:true,pointerId:1,pointerType:'touch'}))})()"); pg.wait_for_timeout(60)
    pg.wait_for_selector('#ownerLogin', state='visible', timeout=10000); pg.fill('#ownerPass', PASS); click(pg, '#ownerGo'); pg.wait_for_selector('#ownerPanel', state='visible', timeout=15000); pg.wait_for_timeout(1500)
    def roster():
        r = pg.evaluate(ROSTER); ok('owner: Owner is the FIRST entry of the dropdown', r and r[0].startswith('Owner'), r[:4])
        ok('owner: dropdown list scrolls (overflow-y auto, capped height)', pg.evaluate("(()=>{const l=document.getElementById('hlist');const c=getComputedStyle(l);return c.overflowY==='auto'&&parseFloat(c.maxHeight)>0})()"))
        click(pg, '#hcur'); ok('dropdown opens', pg.evaluate("document.getElementById('heroes').classList.contains('open')"))
    safe('roster', roster)
    def god():
        click(pg, '#ownerPanel h3 button'); pg.evaluate("__p3d.settings.open()"); pg.wait_for_selector('#settingsPanel', state='visible', timeout=10000)
        ok('settings menu + owner section present', pg.evaluate("!!document.querySelector('[data-set=owner-god]')&&!!document.querySelector('[data-set=view-first]')"))
        ok('god ON by default for the owner', pg.evaluate("__p3d.cheat.god===true"))
        pg.evaluate("__p3d.settings.open()")
    safe('settings', god)
    def fight():
        pg.evaluate("__p3d.fightToggle()"); pg.wait_for_function("__p3d.fight&&__p3d.fight.on", timeout=30000); pg.wait_for_timeout(2500)
        ok('owner saber / skin: owner model selected when fighting', pg.evaluate("__p3d.glbInfo.loaded.includes('n:owner')"))
        pg.evaluate("__p3d.cheats.spawnTitan()"); pg.wait_for_function("__p3d.fight.monsters.some(e=>e.key==='titan')", timeout=40000)
        t = pg.evaluate("(()=>{const t=__p3d.fight.monsters.find(e=>e.key==='titan');return {max:t.max,st:t.state}})()"); ok('spawn Ashen Titan cheat: 5,000,000 HP', t['max'] == 5000000, t)
        ok('titan not duplicated by a 2nd spawn', pg.evaluate("__p3d.cheats.spawnTitan()===false"))
        n = pg.evaluate("__p3d.fight.monsters.filter(e=>e.state!=='defeated').length"); ok('kill enemies hook defeats all', pg.evaluate("__p3d.cheats.killEnemies()===true&&__p3d.fight.monsters.every(e=>e.state==='defeated')"), n)
        pg.evaluate("__p3d.fight.hurt(500000)"); h0 = pg.evaluate("__p3d.fight.hp"); ok('heal party restores HP', pg.evaluate("__p3d.cheats.healParty()===true&&__p3d.fight.hp>=%s" % h0) and pg.evaluate("__p3d.fight.hp")>=h0)
        ok('skip quest = clear stub', pg.evaluate("__p3d.cheats.skipQuest()===false"))
        ok('spawn enemy cheat', pg.evaluate("__p3d.cheats.spawnEnemy('wolf')===true"))
    safe('fight', fight)
    ok('owner assets fetched only after owner unlock', any('owner.glb' in u for u in reqs))
    ok('no page errors', not errs, errs[:3]); ctx.close()
print('FAILS:', bad); raise SystemExit(1 if bad else 0)
