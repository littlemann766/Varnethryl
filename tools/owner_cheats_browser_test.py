#!/usr/bin/env python3
"""Headless check of the owner cheat panel at 1920x1080 and 412x915.
Usage: (cd www && python3 -m http.server PORT) ; P3D_URL=http://localhost:PORT/proto3d.html [MAIN_URL=<baseline server of main>] python3 tools/owner_cheats_browser_test.py
The owner passphrase is read from env VARNETHRYL_OWNER_PASSPHRASE and is only typed into the page, never printed."""
import os, sys, json
from playwright.sync_api import sync_playwright
BASE = os.environ.get('P3D_URL', 'http://localhost:9511/proto3d.html')
MAIN = os.environ.get('MAIN_URL')
PASS = os.environ['VARNETHRYL_OWNER_PASSPHRASE'].strip()
bad = 0
def ok(n, c, d=''):
    global bad; print(('PASS' if c else 'FAIL'), n, ('' if c else str(d).replace(PASS, '***'))[:300])
    if not c: bad += 1
def avg_calls(pg):
    pg.wait_for_timeout(1500); return pg.evaluate('__p3d.renderer.info.render.calls')
def load(ctx, url, errs):
    pg = ctx.new_page(); pg.on('console', lambda m: errs.append(m.text) if m.type in ('error', 'warning') else None); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(url); pg.wait_for_function('window.__p3d && window.__p3d.frames > 5', timeout=90000); pg.wait_for_timeout(1500); return pg
def gesture(pg, mob):
    if mob:
        for _ in range(5): pg.evaluate("(()=>{const v=document.getElementById('ver');for(const t of ['pointerdown','pointerup'])v.dispatchEvent(new PointerEvent(t,{bubbles:true,pointerId:1,pointerType:'touch'}))})()"); pg.wait_for_timeout(60)
    else: pg.keyboard.press('`')
def vis(pg, sel): return pg.evaluate("(s)=>{const e=document.querySelector(s);if(!e)return false;const r=e.getBoundingClientRect(),cs=getComputedStyle(e);return cs.display!=='none'&&cs.visibility!=='hidden'&&r.width>0&&r.height>0}", sel)
def hold(pg, key, ms): pg.keyboard.down(key); pg.wait_for_timeout(ms); pg.keyboard.up(key)
def click(pg, sel): pg.evaluate("(s)=>document.querySelector(s).click()", sel)
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    base_calls = {}
    if MAIN:
        for (w, h, mob) in ((1920, 1080, False), (412, 915, True)):
            ctx = b.new_context(viewport={'width': w, 'height': h}, has_touch=mob, is_mobile=mob, service_workers='block'); e = []
            pg = load(ctx, MAIN + '?party=0&npcs=0', e); base_calls[w] = avg_calls(pg); ctx.close()
    for (w, h, mob) in ((1920, 1080, False), (412, 915, True)):
        tag = f'{w}x{h}'; errs = []
        ctx = b.new_context(viewport={'width': w, 'height': h}, has_touch=mob, is_mobile=mob, service_workers='block')
        reqs = []; ctx.on('request', lambda r: reqs.append(r.url))
        pg = load(ctx, BASE + '?party=0&npcs=0', errs)
        # ---- invisible by default
        ok(f'{tag} no owner UI in the DOM by default', pg.evaluate("!document.getElementById('ownerPanel')&&!document.getElementById('ownerLogin')&&!document.getElementById('ownerFly')&&!document.getElementById('ownerBadge')"))
        ok(f'{tag} panel code not even downloaded', not any(('cheatpanel' in u or 'cheats.js' in u or 'ownergate' in u) for u in reqs), [u for u in reqs if 'cheat' in u])
        ok(f'{tag} no cheat API exposed before unlock', pg.evaluate("__p3d.cheats===undefined"))
        ok(f'{tag} version label present and matches package.json', pg.evaluate("document.getElementById('ver').textContent") == 'v' + json.load(open(os.path.join(os.path.dirname(__file__), '..', 'package.json')))['version'])
        c0 = avg_calls(pg)
        if MAIN: ok(f'{tag} draw calls with panel closed == main baseline', c0 == base_calls[w], f'{c0} vs {base_calls[w]}')
        # ---- wrong passphrase
        gesture(pg, mob); pg.wait_for_selector('#ownerLogin', state='visible', timeout=10000)
        ok(f'{tag} gesture shows only the passphrase prompt', vis(pg, '#ownerLogin') and not vis(pg, '#ownerPanel'))
        pg.fill('#ownerPass', 'not-the-passphrase'); click(pg, '#ownerGo'); pg.wait_for_function("document.getElementById('ownerLoginMsg').textContent.length>0")
        ok(f'{tag} wrong passphrase: panel stays hidden, no unlock stored', not vis(pg, '#ownerPanel') and pg.evaluate("localStorage.getItem('vn_owner_unlock_v1')===null"))
        ok(f'{tag} typing in the prompt does not move the hero (keys isolated)', (pg.fill('#ownerPass', ''), pg.focus('#ownerPass'), pg.keyboard.type('wasd'), pg.evaluate("__p3d.state.speed<0.5"))[3])
        for _ in range(2): pg.fill('#ownerPass', 'wrong-again'); click(pg, '#ownerGo'); pg.wait_for_timeout(700)
        pg.fill('#ownerPass', PASS); click(pg, '#ownerGo'); pg.wait_for_timeout(900)
        ok(f'{tag} right passphrase refused while throttled', not vis(pg, '#ownerPanel') and 'Too many' in pg.evaluate("document.getElementById('ownerLoginMsg').textContent"))
        ctx.close()
        # ---- fresh profile: unlock for real
        ctx = b.new_context(viewport={'width': w, 'height': h}, has_touch=mob, is_mobile=mob, service_workers='block'); errs2 = []
        pg = load(ctx, BASE + '?party=0&npcs=0', errs2)
        gesture(pg, mob); pg.wait_for_selector('#ownerLogin', state='visible', timeout=10000)
        pg.fill('#ownerPass', PASS); click(pg, '#ownerGo'); pg.wait_for_selector('#ownerPanel', state='visible', timeout=15000)
        ok(f'{tag} right passphrase opens the panel', vis(pg, '#ownerPanel') and not vis(pg, '#ownerLogin'))
        ok(f'{tag} passphrase field is cleared after submit', pg.evaluate("document.getElementById('ownerPass').value===''"))
        ok(f'{tag} panel fits the viewport (touch friendly)', pg.evaluate("(()=>{const r=document.getElementById('ownerPanel').getBoundingClientRect();return r.left>=0&&r.right<=innerWidth+1&&r.bottom<=innerHeight+1&&[...document.querySelectorAll('#ownerPanel button')].every(b=>b.getBoundingClientRect().height>=34)})()"))
        ok(f'{tag} cheat API available after unlock', pg.evaluate("typeof __p3d.cheats==='object'"))
        pg.screenshot(path=f'/tmp/ownershots/panel-{tag}.png') if os.path.isdir('/tmp/ownershots') else None
        ok(f'{tag} draw calls unchanged while panel is OPEN', avg_calls(pg) == c0, f'{avg_calls(pg)} vs {c0}')
        # ---- god
        click(pg, '[data-cheat=god]'); ok(f'{tag} god mode: damage becomes 0', pg.evaluate("__p3d.cheats.mitigate(5000)===0 && __p3d.cheats.flags.god===true"))
        ok(f'{tag} badge shows when cheats are active', vis(pg, '#ownerBadge'))
        ok(f'{tag} save marked cheated', pg.evaluate("JSON.parse(localStorage.getItem('guildbound_rpg_save_v1')).cheated===true"))
        # ---- fly
        click(pg, '[data-cheat=fly]'); click(pg, '#ownerPanel h3 button'); pg.wait_for_timeout(200)
        ok(f'{tag} panel closes and fly buttons appear', not vis(pg, '#ownerPanel') and vis(pg, '#ownerFly'))
        y0 = pg.evaluate('__p3d.hero.position.y')
        UP = "document.querySelectorAll('#ownerFly button')[0]"; DN = "document.querySelectorAll('#ownerFly button')[1]"
        def ptr(sel, typ, pid): pg.evaluate(sel + ".dispatchEvent(new PointerEvent('%s',{bubbles:true,pointerId:%d,pointerType:'touch'}))" % (typ, pid))
        if mob: ptr(UP, 'pointerdown', 7)
        else: pg.keyboard.down('e')
        pg.wait_for_function('__p3d.cheat.alt>4', timeout=40000)
        if mob: ptr(UP, 'pointerup', 7)
        else: pg.keyboard.up('e')
        y1 = pg.evaluate('__p3d.hero.position.y'); ok(f'{tag} fly: up control raises the hero (mesh y follows)', y1 > y0 + 3, f'{y0}->{y1}')
        ok(f'{tag} camera follows altitude', pg.evaluate("__p3d.state.heroY+__p3d.cheat.alt>3"))
        a1 = pg.evaluate('__p3d.cheat.alt')
        if mob: ptr(DN, 'pointerdown', 8)
        else: pg.keyboard.down('q')
        pg.wait_for_function('(a)=>__p3d.cheat.alt<a-2', arg=a1, timeout=40000)
        if mob: ptr(DN, 'pointerup', 8)
        else: pg.keyboard.up('q')
        y2 = pg.evaluate('__p3d.hero.position.y'); ok(f'{tag} fly: down control lowers the hero', y2 < y1 - 1.5, f'{y1}->{y2}')
        # fly over a building: pass through a solid box while high
        sel = pg.evaluate("""(()=>{const P=__p3d;for(const c of P.colliders){if(c.type!=='box'||c.lv!==undefined)continue;const w=c.maxX-c.minX,d=c.maxZ-c.minZ;if(w>1.5||d<4)continue;const cz=(c.minZ+c.maxZ)/2;if(Math.abs(cz)>45||c.minX<-45||c.maxX>45)continue;let clear=true;for(let x=c.minX-2.5;x<=c.maxX+2.5;x+=0.25){const inside=x>c.minX-0.6&&x<c.maxX+0.6;if(!inside&&!P.free(x,cz)){clear=false;break}}if(clear)return {minX:c.minX,maxX:c.maxX,cz}}return null})()""")
        ok(f'{tag} found a solid building box to test with', sel is not None)
        def run(mode):
            pg.evaluate("(s)=>{__p3d.teleport(s.minX-2,s.cz);__p3d.setCamYaw(0);__p3d.cheat.alt=%s}" % ('12' if mode == 'fly' else '0'), sel); pg.wait_for_timeout(500)
            pg.keyboard.down('d')
            try: pg.wait_for_function("(s)=>__p3d.state.heroX>s.maxX+0.5", arg=sel, timeout=12000)
            except Exception: pass
            pg.keyboard.up('d'); return pg.evaluate("__p3d.state.heroX")
        x = run('fly'); ok(f'{tag} fly high: crosses a solid building', x > sel['maxX'] + 0.4, f'x={x} box={sel}')
        click(pg, '[data-cheat=fly]') if vis(pg, '#ownerPanel') else (gesture(pg, mob), pg.wait_for_selector('#ownerPanel', state='visible'), click(pg, '[data-cheat=fly]'))
        pg.wait_for_function("__p3d.cheat.alt===0", timeout=30000); ok(f'{tag} fly off: back on the ground', pg.evaluate("__p3d.hero.position.y")<0.5, pg.evaluate("__p3d.hero.position.y"))
        x = run('ground'); ok(f'{tag} normal: building blocks the hero', x < sel['minX'] + 0.2, f'x={x} box={sel}')
        # ---- noclip
        click(pg, '[data-cheat=noclip]'); x = run('noclip'); ok(f'{tag} noclip: walks through the building', x > sel['maxX'] + 0.4, f'x={x} box={sel}')
        click(pg, '[data-cheat=noclip]'); x = run('ground'); ok(f'{tag} noclip off: blocked again', x < sel['minX'] + 0.2, f'x={x}')
        # ---- speed
        def dist():
            pg.evaluate("__p3d.teleport(-6,14);__p3d.setCamYaw(0)"); pg.wait_for_timeout(400); a = pg.evaluate("[__p3d.state.heroX,__p3d.frames]"); pg.keyboard.down('d')
            pg.wait_for_function("(f)=>__p3d.frames>f+14", arg=a[1], timeout=30000); pg.keyboard.up('d'); return pg.evaluate("__p3d.state.heroX") - a[0]
        d1 = dist(); pg.evaluate("__p3d.cheats.setSpeed(4)"); d4 = dist()
        ok(f'{tag} speed x4 covers much more ground (same frame count)', d4 > d1 * 2.2 and d1 > 0.3, f'{d1:.2f} vs {d4:.2f}')
        pg.evaluate("__p3d.cheats.setSpeed(1)")
        # ---- other cheats via panel buttons
        if not vis(pg, '#ownerPanel'): gesture(pg, mob); pg.wait_for_selector('#ownerPanel', state='visible')
        g0 = pg.evaluate("JSON.parse(localStorage.getItem('guildbound_rpg_save_v1')).gear.length"); click(pg, '[data-cheat=item]'); ok(f'{tag} spawn item button', pg.evaluate("JSON.parse(localStorage.getItem('guildbound_rpg_save_v1')).gear.length") == g0 + 1)
        click(pg, '[data-cheat=inf]'); ok(f'{tag} infinite gold button', pg.evaluate("JSON.parse(localStorage.getItem('guildbound_rpg_save_v1')).gold")==999999999)
        pg.fill('#ownerLevel', '50'); click(pg, '[data-cheat=lvl-p]'); ok(f'{tag} set party level button', pg.evaluate("(()=>{const s=JSON.parse(localStorage.getItem('guildbound_rpg_save_v1'));return s.party.every(i=>s.heroLevels[i]===50)})()"))
        click(pg, '[data-cheat="xp+"]'); click(pg, '[data-cheat=heal]'); click(pg, '[data-cheat=kill]'); click(pg, '[data-cheat=skipq]')
        ok(f'{tag} heal/kill/skip stubs are safe and counted', pg.evaluate("JSON.stringify(__p3d.cheats.stubCalls)")=='{"healParty":1,"killEnemies":1,"skipQuest":1}')
        pg.select_option('#ownerPlace', 'inn'); click(pg, '[data-cheat=tpb]'); pg.wait_for_timeout(300)
        ok(f'{tag} teleport to Inn lands near it, on free ground', pg.evaluate("(()=>{const s=__p3d.state;return Math.hypot(s.heroX-24,s.heroZ+8)<30&&__p3d.free(s.heroX,s.heroZ,0)})()"), pg.evaluate("[__p3d.state.heroX,__p3d.state.heroZ]"))
        n = pg.evaluate("document.querySelectorAll('#ownerPlace option').length"); ok(f'{tag} every building listed for teleport', n >= 28, n)
        click(pg, '[data-cheat=bump]'); ok(f'{tag} bump toggle off reaches the bump system', pg.evaluate("__p3d.bump.sys.bumpOn===false"))
        click(pg, '[data-cheat=reset]'); click(pg, '#ownerPanel h3 button')
        ok(f'{tag} reset restores flags', pg.evaluate("(()=>{const c=__p3d.cheat;return !c.god&&!c.fly&&!c.noclip&&c.speedMul===1&&c.bump&&c.alt===0&&__p3d.bump.sys.bumpOn})()"))
        pg.evaluate('__p3d.teleport(0,14);__p3d.setCamYaw(0)'); pg.wait_for_timeout(2500)
        c1 = avg_calls(pg); ok(f'{tag} draw calls unchanged after using every cheat (panel closed)', c1 == c0, f'{c1} vs {c0}')
        ok(f'{tag} no console errors/warnings', not errs2, '; '.join(errs2[:3]))
        # ---- persistence: reload keeps owner unlocked, cheats start off, cheated flag stays
        pg.close(); pg = load(ctx, BASE + '?party=0&npcs=0', errs2)
        ok(f'{tag} after reload: cheats are off, flag persists, UI hidden', pg.evaluate("(()=>{const c=__p3d.cheat;return !c.god&&!c.fly&&!c.noclip&&c.speedMul===1&&!document.getElementById('ownerPanel')&&JSON.parse(localStorage.getItem('guildbound_rpg_save_v1')).cheated===true})()"))
        gesture(pg, mob); pg.wait_for_selector('#ownerPanel', state='visible', timeout=15000)
        ok(f'{tag} owner stays unlocked across reloads (no prompt)', not vis(pg, '#ownerLogin'))
        click(pg, '[data-cheat=lock]'); gesture(pg, mob); pg.wait_for_selector('#ownerLogin', state='visible', timeout=10000)
        ok(f'{tag} Lock owner re-arms the passphrase prompt', not vis(pg, '#ownerPanel'))
        # ---- 2D loads the cheated save
        e2 = []; pg2 = ctx.new_page(); pg2.on('pageerror', lambda e: e2.append(str(e))); pg2.on('console', lambda m: e2.append(m.text) if m.type == 'error' else None)
        pg2.goto(BASE.replace('proto3d.html', 'index2d.html')); pg2.wait_for_timeout(2500)
        ok(f'{tag} 2D game still loads with a cheated save, keeps the flag', not e2 and pg2.evaluate("JSON.parse(localStorage.getItem('guildbound_rpg_save_v1')).cheated===true"), e2[:2])
        ctx.close()
print('FAILED %d' % bad if bad else 'ALL PASS'); sys.exit(1 if bad else 0)
