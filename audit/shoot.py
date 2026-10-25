import sys
from playwright.sync_api import sync_playwright
url,out,w=sys.argv[1],sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else 1780
with sync_playwright() as p:
  b=p.chromium.launch(args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);pg=b.new_page(viewport={'width':w,'height':400})
  pg.on('console',lambda m:print(m.text) if m.type=='error' else None);pg.on('pageerror',lambda e:print('ERR',e))
  pg.goto(url);pg.wait_for_function('window.__done',timeout=200000);pg.screenshot(path=out,full_page=True);b.close()
