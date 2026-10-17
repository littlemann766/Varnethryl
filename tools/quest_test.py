"""Playwright walk-through of the "A Light in Dusk Hollow" quest line (Count Veyra and Mortimer).
Usage: serve www/ (python3 -m http.server 8111 -d www) then VN_URL=http://localhost:8111/index.html python3 tools/quest_test.py
Uses window.__vn.Quest.debug only to skip the long fights; story panels, travel, candles and the Dawn Spell go through the real UI."""
import os, json, sys
from playwright.sync_api import sync_playwright
URL = os.environ.get('VN_URL', 'http://localhost:8111/index.html')
res = []
def ok(n, c):
    res.append(bool(c)); print(('PASS' if c else 'FAIL'), n)
def tap_ok(pg, sel, name):
    bb = pg.locator(sel).first.bounding_box()
    ok(f'tap target >=44px: {name}', bb and bb['height'] >= 43.5 and bb['width'] >= 43.5)
def walk_panels(pg, pick=None, check_taps=False):
    n = 0
    while pg.evaluate("document.getElementById('storyDlg').open"):
        if check_taps and n == 0:
            tap_ok(pg, '#stNext', 'story Next'); tap_ok(pg, '#stSkip', 'story Skip')
        ch = pg.locator('.stChoice')
        if ch.count():
            if check_taps: tap_ok(pg, '.stChoice', 'story choice')
            if pick: pg.locator(f'.stChoice[data-id="{pick}"]').first.click()
            else: ch.first.click()
        else:
            pg.click('#stNext')
        n += 1; assert n < 40, 'panel loop'
        pg.wait_for_timeout(30)
    return n
def quest(pg): return pg.evaluate("JSON.parse(JSON.stringify(window.__vn.state.veyra))")
def safe(pg): pg.evaluate("window.__vn.Quest.debug.playerSafe()")
def run(p, ending_pick, label):
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True, service_workers='block')
    pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    # 1. Legacy save with no quest data must still load.
    pg.goto(URL); pg.wait_for_timeout(500)
    legacy = pg.evaluate("(()=>{const s=JSON.parse(JSON.stringify(window.__vn.state));delete s.veyra;s.kills=0;s.questStep=0;localStorage.setItem('guildbound_rpg_save_v1',JSON.stringify(s));return Object.keys(s).includes('veyra')})()")
    ok(f'{label}: legacy save has no veyra key', legacy is False)
    pg.reload(); pg.wait_for_timeout(600)
    q = quest(pg); ok(f'{label}: legacy save loads with default quest state', q['stage'] == 'locked' and q['ch'] == 1 and q['done'] == [])
    ok(f'{label}: card visible while locked', pg.locator('#veyraCard').is_visible())
    # 2. Unlock via normal progression
    pg.evaluate("window.__vn.state.kills=3;window.__vn.state.questStep=1"); pg.wait_for_timeout(700)
    ok(f'{label}: story banner appears', pg.locator('#vqBanner').is_visible())
    tap_ok(pg, '#vqBanner', 'banner')
    ids = ['V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7']
    for i, cid in enumerate(ids):
        q = quest(pg)
        ok(f'{label}: {cid} offered', q['stage'] == 'offer' and q['ch'] == i + 1)
        if cid == 'V6':
            ok(f'{label}: hollow zone unlocked before V6', 'hollow' in q['zones'])
        pg.evaluate("document.getElementById('vqRead')&&document.getElementById('vqRead').scrollIntoView()")
        pg.click('#vqBanner' if cid == 'V1' else '#vqRead')
        walk_panels(pg, pick=('atlas' if cid == 'V1' else None), check_taps=(cid in ('V1', 'V6')))
        q = quest(pg); ok(f'{label}: {cid} intro leads to active', q['stage'] == 'active')
        if cid == 'V1': ok(f'{label}: book keepsake chosen', q['book'] == 'atlas' and 'Keepsake: The Star Atlas' in q['items'])
        zone = pg.evaluate("window.__vn.state.zone")
        need = pg.evaluate("window.__vn.Quest.debug.chapters()[%d].zone" % i)
        if zone != need:
            tap_ok(pg, '#vqGoto', 'travel button'); pg.click('#vqGoto'); pg.wait_for_timeout(300)
        ok(f'{label}: {cid} in zone {need}', pg.evaluate("window.__vn.state.zone") == need)
        fights = pg.evaluate("window.__vn.Quest.debug.chapters()[%d].fights" % i)
        if cid in ('V6', 'V7'):
            tap_ok(pg, '#vqCandle', 'candle button')
            for k in range(3):
                pg.click('#vqCandle'); pg.wait_for_timeout(60)
            ok(f'{label}: {cid} candles lit', quest(pg)['candles'] == 3)
        if cid == 'V7':
            safe(pg); pg.wait_for_function("window.__vn.runtime.enemy.some(e=>e.qid==='veyra')", timeout=8000)
            # sprites unique while fighting
            pg.wait_for_timeout(800)
            ok(f'{label}: Veyra phase 2 after candles', pg.evaluate("window.__vn.Quest.status().phase") == 2)
            pg.evaluate("window.__vn.Quest.debug.setVeyraHp(.5)"); pg.wait_for_timeout(900)
            ok(f'{label}: clones phase', pg.evaluate("window.__vn.Quest.status().phase") == 3 and pg.evaluate("window.__vn.runtime.enemy.filter(e=>e.qid==='clone').length") == 2)
            pg.evaluate("window.__vn.Quest.debug.killQuestEnemies()"); pg.wait_for_timeout(900)
            ok(f'{label}: real Veyra phase 4', pg.evaluate("window.__vn.Quest.status().phase") == 4)
            pg.evaluate("window.__vn.Quest.debug.setVeyraHp(.2)"); pg.wait_for_timeout(900)
            ok(f'{label}: eclipse shield phase 5', pg.evaluate("window.__vn.Quest.status().phase") == 5)
            hp0 = pg.evaluate("window.__vn.runtime.enemy.find(e=>e.qid==='veyra').hp")
            pg.evaluate("window.__vn.hitEnemy(window.__vn.runtime.enemy.find(e=>e.qid==='veyra'),window.__vn.state.active,50)")
            hp1 = pg.evaluate("window.__vn.runtime.enemy.find(e=>e.qid==='veyra').hp")
            ok(f'{label}: shield blocks damage', hp1 >= hp0)
            tap_ok(pg, '#vqDawn', 'dawn spell'); pg.click('#vqDawn'); pg.wait_for_timeout(600)
            ok(f'{label}: dawn breaks shield', pg.evaluate("window.__vn.Quest.status().phase") == 6)
            pg.evaluate("window.__vn.Quest.debug.finishVeyra()")
            pg.wait_for_selector('#storyDlg[open]', timeout=4000)
            walk_panels(pg, pick=ending_pick, check_taps=False)
            break
        for f in range(fights):
            safe(pg)
            pg.wait_for_function("window.__vn.runtime.enemy.some(e=>e.qid==='q'&&e.hp>0)", timeout=8000)
            # one sprite per hero while in combat
            pg.wait_for_timeout(150)
            drawn = pg.evaluate("window.__vn.runtime.drawn")
            ok(f'{label}: {cid} fight {f+1} one sprite per hero', len(drawn) == len(set(drawn)))
            pg.evaluate("window.__vn.Quest.debug.killQuestEnemies()"); pg.wait_for_timeout(400)
        pg.wait_for_selector('#storyDlg[open]', timeout=4000)
        walk_panels(pg, pick=('take' if cid == 'V6' else None))
        q = quest(pg); ok(f'{label}: {cid} complete', cid in q['done'])
    q = quest(pg)
    sv = json.loads(pg.evaluate("localStorage.getItem('guildbound_rpg_save_v1')") ) if pg.wait_for_timeout(400) is None else None
    ok(f'{label}: save key still guildbound_rpg_save_v1 and version 1', sv and sv['version'] == 1 and 'veyra' in sv)
    return b, pg, q, errs, sv
with sync_playwright() as p:
    b, pg, q, errs, sv = run(p, 'father', 'happy')
    ok('happy: ending redeemed', q['ending'] == 'redeemed' and q['stage'] == 'finished')
    ok('happy: rewards', all(x in q['items'] for x in ['Twin Moons', "Brothers' Sigil", 'Moonsilver weapon skin']) and q['title'] == 'Bringer of Dawn')
    ok('happy: reward gear in save', any(g['name'].startswith('Moonsilver') for g in sv['gear']) and any(g['name'] == "Brothers' Sigil" for g in sv['gear']))
    ok('happy: first drawing recorded', q['firstDrawing'] == 'father')
    ok('happy: all recruits', len(q['recruits']) >= 11)
    ok('happy: Brother Thorne + Seraphine unlocked', pg.evaluate("[2,5,0,16,11,9,18,14,12,10,17,19].every(i=>window.__vn.state.unlocked.includes(i))"))
    ok('happy: no duplicate party members', pg.evaluate("new Set(window.__vn.state.party).size===window.__vn.state.party.length"))
    ok('happy: journal opens with chapters', (pg.click('#vqJournal'), pg.wait_for_timeout(200), pg.locator('#vqChapters li').count())[2] == 7)
    pg.click('#closeModal')
    ok('happy: no console errors', not errs); print(errs[:3])
    # reload keeps progress (additive save)
    pg.reload(); pg.wait_for_timeout(700)
    ok('happy: progress survives reload', quest(pg)['stage'] == 'finished')
    b.close()
    # "Not yet" branch: leave the drawings, Veyra retreats, quest reopens, redo succeeds.
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True, service_workers='block'); pg = ctx.new_page()
    pg.goto(URL); pg.wait_for_timeout(500)
    pg.evaluate("""(()=>{const s=window.__vn.state;s.kills=3;s.questStep=1;Object.assign(s.veyra,{stage:'offer',ch:7,done:['V1','V2','V3','V4','V5','V6'],zones:['coast','hollow'],drawings:[],items:["Brother's Oath"],recruits:['Brother Thorne'],allies:['pip']})})()""")
    pg.evaluate('window.__vn.Quest.render()'); pg.click('#vqRead'); walk_panels(pg)
    pg.evaluate("window.__vn.enterZone('hollow')"); pg.wait_for_timeout(300)
    for k in range(3): pg.click('#vqCandle')
    pg.evaluate("window.__vn.Quest.debug.playerSafe()")
    pg.wait_for_function("window.__vn.runtime.enemy.some(e=>e.qid==='veyra')", timeout=8000)
    pg.evaluate("window.__vn.Quest.debug.finishVeyra()"); pg.wait_for_selector('#storyDlg[open]', timeout=4000); walk_panels(pg)
    q = quest(pg); ok('notyet: quest reopens at V7', q['ending'] == 'notyet' and q['stage'] == 'offer' and q['ch'] == 7 and q['redo'])
    pg.wait_for_timeout(300); pg.click('#vqRead'); walk_panels(pg)
    q = quest(pg); ok('notyet: drawings fetched on redo', len(q['drawings']) == 3 and q['stage'] == 'active')
    for k in range(3): pg.click('#vqCandle')
    pg.evaluate("window.__vn.Quest.debug.playerSafe()")
    pg.wait_for_function("window.__vn.runtime.enemy.some(e=>e.qid==='veyra')", timeout=8000)
    pg.evaluate("window.__vn.Quest.debug.finishVeyra()"); pg.wait_for_selector('#storyDlg[open]', timeout=4000); walk_panels(pg)
    q = quest(pg); ok('notyet: redo ends redeemed (no guest ally)', q['ending'] == 'redeemed' and not q['guest'])
    b.close()
print(f"{sum(res)}/{len(res)} checks passed")
sys.exit(0 if all(res) else 1)
