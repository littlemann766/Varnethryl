"""Measures rAF frame times of the Liongate world in headless Chromium for each graphics quality. Needs server on :8099."""
from playwright.sync_api import sync_playwright
import statistics as st
JS="""async()=>{const t=[];let l=performance.now();await new Promise(r=>{let n=0;const f=now=>{t.push(now-l);l=now;if(++n<240)requestAnimationFrame(f);else r()};requestAnimationFrame(f)});return t.slice(10)}"""
with sync_playwright() as p:
  b=p.chromium.launch()
  for name,w,h,mob in [('web-1280x720',1280,720,False),('phone-844x390',844,390,True),('phone-390x844',390,844,True)]:
    for q in ['high','medium','low']:
      ctx=b.new_context(viewport={'width':w,'height':h},has_touch=mob,is_mobile=mob,device_scale_factor=2 if mob else 1,service_workers='block')
      pg=ctx.new_page();pg.goto('http://localhost:8099/index.html');pg.wait_for_timeout(2500)
      pg.evaluate("q=>{window.__vn.Settings.get().graphics=q}",q);pg.wait_for_timeout(500)
      t=pg.evaluate(JS);t.sort()
      print(f"{name:14} {q:6} mean {st.mean(t):5.1f}ms  p50 {t[len(t)//2]:5.1f}  p95 {t[int(len(t)*.95)]:5.1f}  max {t[-1]:5.1f}")
      ctx.close()
  b.close()
