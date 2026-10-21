#!/usr/bin/env python3
"""Android-size smoke test of the real rotating GLB selector, including Frost Troll B."""
import functools, http.server, os, threading
from playwright.sync_api import sync_playwright

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','www'))
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Q,directory=ROOT))
threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
    browser=p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
    for orientation,w,h in [('portrait',412,915),('landscape',800,440)]:
        ctx=browser.new_context(viewport={'width':w,'height':h},has_touch=True,is_mobile=True,service_workers='block')
        page=ctx.new_page()
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(f'http://127.0.0.1:{server.server_address[1]}/proto3d.html?nosave=1&party=0&npcs=0',wait_until='commit',timeout=120000)
        page.wait_for_function('window.__p3d && __p3d.frames > 8',timeout=120000)
        page.locator('#vnHero').click()  # Actual title-screen entry opens selector
        page.wait_for_function("""()=>document.querySelector('#heroes.open .vn-character-stage canvas') &&
             document.querySelector('#heroes.open #hlist .vn-roster-tabs button')""",timeout=30000)
        assert page.locator('.vn-roster-tabs button').count()==3
        assert page.get_by_text('Odyssey',exact=True).count()==0
        bounds=page.evaluate("""()=>{
          const e=document.getElementById('heroes'),r=e.getBoundingClientRect(),
          c=document.querySelector('.vn-character-stage canvas'),cr=c.getBoundingClientRect();
          return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,canvasW:cr.width,canvasH:cr.height};
        }""")
        assert bounds['left']>=0 and bounds['right']<=w+2 and bounds['top']>=0 and bounds['bottom']<=h+2,bounds
        assert bounds['canvasW']>=200 and bounds['canvasH']>=90,bounds
        print(orientation,'selector layout',bounds,flush=True)
        # Previewing must not silently switch the saved or playing hero.
        before=page.evaluate('__p3d.heroIndex')
        button=page.locator('#hlist button[title="Selene Frostveil"]')
        button.scroll_into_view_if_needed()
        button.click()
        page.wait_for_function("""()=>!document.querySelector('.vn-character-choose').disabled &&
           document.querySelector('.vn-character-status').textContent.includes('Selene')""",timeout=45000)
        assert page.evaluate('__p3d.heroIndex')==before
        canvas=page.locator('.vn-character-stage canvas')
        assert canvas.count()==1
        canvas.drag_to(canvas,source_position={'x':70,'y':70},target_position={'x':140,'y':75})
        page.screenshot(path=f'character-roster-{orientation}.png')
        page.locator('.vn-character-choose').click()
        page.wait_for_function('__p3d.heroIndex === 2',timeout=30000)
        assert not page.locator('#heroes').evaluate("(el)=>el.classList.contains('open')")
        # Both brothers must be listed individually and show the distinct approved GLB.
        page.locator('#vnMenuBtn').click()
        page.locator('#vnQuickMenu summary').filter(has_text='Characters').click()
        page.locator('#vnChooseCharacter').click()
        page.get_by_role('tab',name='Enemies & Bosses').click()
        assert page.locator('#hlist button[title="Frost Troll A (3.5×)"]').count()==1
        b=page.locator('#hlist button[title="Frost Troll B (3.5×)"]')
        assert b.count()==1
        b.scroll_into_view_if_needed()
        b.click()
        try:
            page.wait_for_function("""()=>!document.querySelector('.vn-character-choose').disabled &&
              document.querySelector('.vn-character-status').textContent.includes('Frost Troll B')""",timeout=30000)
        except Exception:
            diagnostics=page.evaluate("""()=>({
              status:document.querySelector('.vn-character-status')?.textContent,
              choose:document.querySelector('.vn-character-choose')?.disabled,
              chooseText:document.querySelector('.vn-character-choose')?.textContent,
              rosterOpen:document.getElementById('heroes')?.classList.contains('open'),
              canvas:!!document.querySelector('.vn-character-stage canvas'),
              selectedRow:[...document.querySelectorAll('#hlist .vn-roster-list .row button')]
                .filter(b=>b.title.includes('Frost Troll')).map(b=>({title:b.title,slot:b.dataset.i})),
              models:__p3d.modelStatus(),hero:__p3d.heroIndex})""")
            print('FROST SELECTOR DIAGNOSTIC',diagnostics,'JS ERRORS',errors,flush=True)
            page.screenshot(path=f'frost-troll-b-roster-error-{orientation}.png')
            raise
        assert page.evaluate('__p3d.heroIndex')==2
        page.screenshot(path=f'frost-troll-b-roster-{orientation}.png')
        assert not errors,errors
        print('PASS',orientation,'real 3D previews, confirm-to-select, individual Frost Troll B, no Odyssey',flush=True)
        ctx.close()
    browser.close()
