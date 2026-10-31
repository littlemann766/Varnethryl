"""Writes docs/CLASS-SKILLS.txt from www/skills.js + www/classmotion.js (single source of truth). Needs the static server on :8099."""
from playwright.sync_api import sync_playwright
import sys
OUT=sys.argv[1:] or ['docs/CLASS-SKILLS.txt']
JS="""async()=>{const S=await import('./skills.js'),D=await import('./data.js'),M=await import('./classmotion.js');
 const cls=[...new Set(D.HEROES.map(h=>h.className))];
 return {cls:cls.map(c=>({c,heroes:D.HEROES.filter(h=>h.className===c).map(h=>h.name),pool:S.CLASS_SKILLS[c],prof:M.CLASS_PROFILES[c]})),
  ults:D.HEROES.map(h=>({id:h.id,name:h.name,cls:h.className,u:S.ULTIMATES[h.id],tw:M.HERO_TWEAKS[h.id]}))}}"""
with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page();pg.goto('http://localhost:8099/index.html');d=pg.evaluate(JS);b.close()
L=['VARNETHRYL - CLASS SKILL POOLS & PLACEHOLDER ULTIMATES','='*60,'',
'For team review. Source of truth: www/skills.js (CLASS_SKILLS, ULTIMATES). Motion/VFX: www/classmotion.js.',
'Skill resolution: hero override > class pool > default. Each hero uses their class pool for Minor / Heavy / Super Heavy,','and has ONE unique Ultimate (all ultimates below are PLACEHOLDERS for the team to replace).','',
'Fields: cd = cooldown (s), x = damage/heal multiplier, rng = range (px), splash = splash radius (px), effect, anim = attack animation family, vfx = effect id.','','PART 1 - CLASS POOLS (20 classes)','-'*60]
for c in d['cls']:
  L+=['',f"{c['c'].upper()}   (heroes: {', '.join(c['heroes'])})",f"  motion: speed x{c['prof'].get('spd',1)}, weight {c['prof'].get('weight','-')}, attack family {c['prof']['fam']}, idle {c['prof'].get('idle','breath')}"]
  for slot,label in [('minor','Minor'),('heavy','Heavy'),('superHeavy','Super Heavy')]:
    s=c['pool'][slot];L.append(f"  {label:<12}{s['name']:<20} cd {s['cd']/1000:>4.1f}s  x{s['mult']:<4} rng {s['rng'] if 'rng' in s else s['range']:<4} splash {s['splash']:<4} {s['effect']:<8} anim {s['anim']:<8} vfx {s['fx']}")
L+=['','','PART 2 - PLACEHOLDER ULTIMATES (one per hero) -- *** PLACEHOLDER: TEAM TO REPLACE ***','-'*60]
for h in d['ults']:
  u=h['u'];L+=['',f"[{h['id']:>2}] {h['name']} ({h['cls']})",f"     Ultimate: {u['name']}  [PLACEHOLDER]  effect {u['effect']}  x{u['mult']}  rng {u['range']}  splash {u['splash']}  vfx {u['fx']}",f"     {u['desc']}"]
L+=['','','PART 3 - PER-HERO MOTION TWEAKS (on top of class; www/classmotion.js HERO_TWEAKS)','-'*60]
for h in d['ults']:
  t=dict(h['tw']);n=t.pop('note','');t.pop('tint',None);L.append(f"[{h['id']:>2}] {h['name']:<18} {n}\n     "+', '.join(f"{k} x{v}" for k,v in t.items()))
for o in OUT:open(o,'w').write('\n'.join(L)+'\n')
print('wrote',OUT,len(L),'lines')
