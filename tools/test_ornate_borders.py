#!/usr/bin/env python3
"""Regression for ornate frames on actual mobile WebKit-like Chromium layouts.
Checks no stretched source backgrounds, corners stay at constant border widths,
menus remain scrollable/usable and screenshot artifacts aid manual visual review.
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import http.server,threading,functools,os,sys
ROOT=Path(__file__).resolve().parents[1]/'www'
OUT=Path(__file__).resolve().parents[1]/'border-screenshots'
OUT.mkdir(exist_ok=True)
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
failures=[]
def check(label,passed,detail=''):
 print(('PASS ' if passed else 'FAIL ')+label+(' '+str(detail)[:150] if detail else ''),flush=True)
 if not passed:failures.append(label)
def bounds(page,selector):
 return page.evaluate("""sel=>{const e=document.querySelector(sel),b=e.getBoundingClientRect(),s=getComputedStyle(e);
   return {x:b.x,y:b.y,width:b.width,height:b.height,left:b.left,right:b.right,top:b.top,bottom:b.bottom,
           border:s.borderTopWidth,borderImage:s.borderImageSource,background:s.backgroundImage,scrollHeight:e.scrollHeight,clientHeight:e.clientHeight}}""",selector)
with sync_playwright() as p:
 browser=p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
 for w,h in [(412,915),(320,568),(844,390)]:
  ctx=browser.new_context(viewport={'width':w,'height':h},device_scale_factor=1,has_touch=True,is_mobile=True,service_workers='block')
  page=ctx.new_page()
  page.goto(f'http://127.0.0.1:{server.server_address[1]}/proto3d.html?nosave=1&party=0&npcs=0',wait_until='domcontentloaded',timeout=90000)
  page.wait_for_timeout(350)
  card=bounds(page,'#vnMenu .vn-card')
  check(f'{w}x{h} main panel uses 9-slice image, not stretched full image',
        'panel-wide.svg' in card['borderImage'] and 'panel-wide.svg' not in card['background'],card)
  check(f'{w}x{h} main panel fits width',card['width']<=w-8 and card['left']>=-1 and card['right']<=w+1)
  check(f'{w}x{h} main panel fits height',card['height']<=h-4 and card['top']>=-1)
  check(f'{w}x{h} first and last actions stay within panel',
        page.evaluate("""()=>{const b=document.querySelector('#vnMenu .vn-card').getBoundingClientRect();
             const controls=[...document.querySelectorAll('#vnMenu button,#vnMenu a')];
             return controls.every(e=>{const q=e.getBoundingClientRect();return q.left>=b.left && q.right<=b.right && q.top>=b.top-2;});}"""))
  page.screenshot(path=str(OUT/f'ornate-menu-{w}x{h}.png'))
  page.evaluate("""()=>{document.getElementById('vnMenu').hidden=true;
                      document.body.classList.remove('vn-menu-open');
                      document.getElementById('vnQuickMenu').hidden=false}""")
  quick=bounds(page,'#vnQuickMenu')
  check(f'{w}x{h} quick menu keeps its corners','panel-wide.svg' in quick['borderImage'] and 'panel-wide.svg' not in quick['background'])
  check(f'{w}x{h} quick menu fits phone',quick['width']<=w and quick['right']<=w+1 and quick['left']>=-1)
  head=bounds(page,'#vnQuickMenu .vn-qhead')
  check(f'{w}x{h} heading has fixed 9-sliced border','label-long.svg' in head['borderImage'] and 'label-long.svg' not in head['background'])
  check(f'{w}x{h} close button inside heading',
        page.evaluate("""()=>{const h=document.querySelector('#vnQuickMenu .vn-qhead').getBoundingClientRect();
          const b=document.querySelector('#vnQuickClose').getBoundingClientRect();
          return b.left>=h.left&&b.right<=h.right&&b.top>=h.top&&b.bottom<=h.bottom;}"""))
  page.screenshot(path=str(OUT/f'ornate-quick-{w}x{h}.png'))
  # Force a large settings panel to validate the CSS even before settings opens.
  page.evaluate("""()=>{let el=document.querySelector('#settingsPanel');
    if(!el){el=document.createElement('section');el.id='settingsPanel';document.body.appendChild(el);}
    el.style.display='block';el.innerHTML='<h3>Settings</h3>'+Array.from({length:9},(_,i)=>'<div class="card">Setting '+i+'</div>').join('');
    }""")
  panel=bounds(page,'#settingsPanel')
  check(f'{w}x{h} settings frame is nine-sliced and scrollable','panel-wide.svg' in panel['borderImage'] and 'panel-wide.svg' not in panel['background'])
  check(f'{w}x{h} settings remain within viewport',panel['left']>=-1 and panel['right']<=w+1 and panel['bottom']<=h+1)
  page.screenshot(path=str(OUT/f'ornate-settings-{w}x{h}.png'))
  ctx.close()
 browser.close()
server.shutdown()
print('Screenshots:',OUT,flush=True)
print('FAILURES',len(failures),failures,flush=True)
sys.exit(bool(failures))
