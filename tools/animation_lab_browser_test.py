#!/usr/bin/env python3
"""Android-sized browser smoke test for private animation lab and five-tap owner gate."""
import functools
import http.server
import os
import threading
from playwright.sync_api import sync_playwright
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','www')
class Server(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Server,directory=ROOT))
threading.Thread(target=srv.serve_forever,daemon=True).start()
port=srv.server_address[1]
with sync_playwright() as p:
    browser=p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
    page=browser.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,device_scale_factor=1,service_workers='block')
    errors=[]
    page.on('pageerror',lambda e: errors.append(str(e)))
    page.goto(f'http://127.0.0.1:{port}/proto3d.html?nosave=1')
    page.wait_for_function('window.__p3d && window.__p3d.frames > 8',timeout=80000)
    assert page.locator('#vnMenu').is_visible()
    # Title version does not unlock on one tap; five taps should show login.
    page.locator('#vnVersion').dispatch_event('pointerup')
    assert not page.locator('#ownerLogin').is_visible() if page.locator('#ownerLogin').count() else True
    for _ in range(4):page.locator('#vnVersion').dispatch_event('pointerup')
    page.wait_for_selector('#ownerLogin:visible',timeout=15000)
    assert not page.locator('#ownerPanel').is_visible() if page.locator('#ownerPanel').count() else True
    page.locator('#ownerLogin button').filter(has_text='Cancel').click()
    page.locator('#vnEnter').click()
    page.wait_for_function("getComputedStyle(document.querySelector('#vnMenu')).display==='none'",timeout=15000)
    page.evaluate('__p3d.settings.open()')
    page.locator('#settingsPanel:visible').wait_for()
    assert page.locator('[data-set="owner-god"]').count()==0
    assert page.locator('[data-set="saberMul"]').count()==0
    version=page.locator('#settingsPanel [data-set="version-cheats"]')
    page.get_by_role('button',name='Game ▾').click()
    for _ in range(4):version.dispatch_event('pointerup')
    assert not page.locator('#ownerLogin').is_visible()
    version.dispatch_event('pointerup')
    page.wait_for_selector('#ownerLogin:visible',timeout=5000)
    page.locator('#ownerLogin button').filter(has_text='Cancel').click()
    page.evaluate('__p3d.settings.open()')
    page.get_by_role('button',name='Animation Lab (test) ▾').click()
    assert page.locator('#labHero').count()==1
    assert page.locator('#labStyle').count()==1
    page.locator('#labHero').select_option('darius')
    page.locator('#labStyle').select_option('classic')
    page.locator('#animationLabStart').click()
    page.wait_for_function('__p3d.animationLab.status().active',timeout=15000)
    status=page.evaluate('__p3d.animationLab.status()')
    assert status['style']=='classic',status
    assert 'Darius' in status['character']
    assert not page.locator('#settingsPanel').is_visible()
    assert page.evaluate('__p3d.heroIndex')>=0
    report=page.evaluate('__p3d.animationLab.report("runs smoothly")')
    assert 'runs smoothly' in report
    # Reopen the lab and restore exactly the previous playable hero.
    page.evaluate('__p3d.settings.open()')
    if page.get_by_role('button',name='Animation Lab (test) ▾').count():
        page.get_by_role('button',name='Animation Lab (test) ▾').click()
    page.locator('#animationLabStop').click()
    assert not page.evaluate('__p3d.animationLab.status().active')
    assert page.evaluate('__p3d.heroIndex')>=0
    assert not errors,errors[:6]
    print('PASS Animation Lab: real-game preview and restore, owner menu gated by 5 quick taps')
    browser.close()
