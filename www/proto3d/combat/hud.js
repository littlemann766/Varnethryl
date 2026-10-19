/* CombatHUD: presentation only. Subscribes to CombatController events and reads its state; never computes damage.
   Perf: all nodes are built once; per frame we only write a style/text when the displayed value changed. Floating numbers come from a fixed pool. */
import { ABILITIES } from './data.js';
const CSS = `
#cb{position:fixed;inset:0;z-index:40;display:none;pointer-events:none;font:700 12px system-ui,sans-serif;color:#fff;user-select:none;-webkit-user-select:none}
#cb *{box-sizing:border-box}#cb button{pointer-events:auto;touch-action:none;font:inherit;color:#fff;cursor:pointer}
#cb .tp{position:absolute;left:50%;top:max(52px,calc(env(safe-area-inset-top) + 46px));transform:translateX(-50%);width:min(210px,52vw);padding:4px 8px 6px;border:1px solid #fff6;border-radius:8px;background:#000b;display:none;text-align:center}
#cb .tp .nm{font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}#cb .tp .sub{font-size:10px;color:#ccd;margin-bottom:3px}
#cb .tp.boss{top:max(4px,env(safe-area-inset-top));width:min(560px,92vw);padding:3px 10px 5px}#cb .tp.boss .nm{font-size:15px;letter-spacing:.12em;color:#ffb070}
#cb .bar{position:relative;height:12px;border:1px solid #000;border-radius:6px;background:#2a2a2a;overflow:hidden}#cb .tp.boss .bar{height:16px}
#cb .bar i{position:absolute;left:0;top:0;bottom:0;width:100%;transform-origin:left;will-change:transform}
#cb .bar b{position:absolute;inset:0;text-align:center;font-size:9px;line-height:11px;text-shadow:0 1px 1px #000}#cb .tp.boss .bar b{line-height:15px;font-size:11px}
#cb .hp i{background:linear-gradient(#ff6b6b,#c21f1f)}#cb .mp i{background:linear-gradient(#6bb8ff,#1f5fd0)}#cb .sp i{background:linear-gradient(#7dff8a,#1fa83a)}
#cb .vit{position:absolute;left:max(10px,env(safe-area-inset-left));bottom:max(184px,calc(env(safe-area-inset-bottom) + 178px));width:min(176px,44vw);display:flex;gap:6px;align-items:center}
#cb .por{flex:none;width:42px;height:42px;border-radius:50%;border:2px solid #fff;background:radial-gradient(#4a6ea8,#1b2a48);display:flex;align-items:center;justify-content:center;font:900 18px system-ui;position:relative}
#cb .por small{position:absolute;bottom:-5px;right:-5px;background:#000c;border:1px solid #fff8;border-radius:8px;font:700 9px system-ui;padding:0 3px}
#cb .bars{flex:1;display:flex;flex-direction:column;gap:3px}
#cb .ab{position:absolute;left:50%;bottom:max(4px,env(safe-area-inset-bottom));transform:translateX(-50%);display:flex;gap:4px}
#cb .sl{position:relative;width:46px;height:46px;border-radius:9px;border:2px solid #fffa;background:#102034dd;padding:0;overflow:hidden}
#cb .sl .ic{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font:400 22px system-ui;padding-bottom:6px}
#cb .sl .k{position:absolute;left:2px;top:0;font-size:9px;color:#ffe9a8}#cb .sl .c{position:absolute;right:2px;top:0;font-size:9px}#cb .sl .c.mp{color:#8cf}#cb .sl .c.sp{color:#9f9}
#cb .sl .n{position:absolute;left:0;right:0;bottom:0;font:700 8px system-ui;background:#000a;text-align:center;line-height:11px;white-space:nowrap;overflow:hidden}
#cb .sl .cdv{position:absolute;left:0;right:0;bottom:0;height:0;background:#000c;transform-origin:bottom}#cb .sl .ct{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font:900 15px system-ui;text-shadow:0 1px 2px #000}
#cb .sl.off{filter:grayscale(1) brightness(.55)}#cb .sl.nores{border-color:#f66}#cb .sl:active:not(.off){background:#2a6fb0}
#cb .cl{position:absolute;right:max(8px,env(safe-area-inset-right));bottom:max(56px,calc(env(safe-area-inset-bottom) + 52px));display:grid;grid-template-columns:repeat(2,50px);gap:6px}
#cb .cl button{position:relative;width:50px;height:50px;border-radius:50%;border:2px solid #fffb;background:#0c2438dd;font-size:9px;line-height:1.05;padding:0;overflow:hidden}
#cb .cl button .g{display:block;font:400 19px system-ui;line-height:20px}#cb .cl button.on{background:#2aa;border-color:#9ff}
#cb .cl button .cdv{position:absolute;left:0;right:0;bottom:0;height:0;background:#000b}#cb .cl button .q{position:absolute;right:3px;top:2px;font-size:9px;color:#ffe9a8}
#cb .fn{position:absolute;transform:translate3d(-50px,-50px,0);font:900 20px system-ui;color:#ffe066;text-shadow:0 0 3px #000,0 2px 2px #000;white-space:nowrap;display:none;will-change:transform,opacity}
#cb .fn.crit{color:#ff9d2e;font-size:27px}#cb .fn.pl{color:#ff5a5a}#cb .fn.heal{color:#7dff8a}
#cb .oh{position:absolute;left:0;top:0;width:54px;height:7px;border:1px solid #000;border-radius:4px;background:#500;overflow:hidden;display:none;will-change:transform}#cb .oh i{display:block;height:100%;width:100%;background:#e33;transform-origin:left}
#cb .oh.lock{border-color:#ffd54a;box-shadow:0 0 6px #ffd54a}
#cb .msg{position:absolute;left:50%;top:34%;transform:translate(-50%,-50%);font:900 24px system-ui;text-shadow:0 2px 8px #000;display:none;text-align:center}
#cb .flash{position:absolute;inset:0;background:radial-gradient(transparent 40%,#f00a);opacity:0;transition:opacity .25s}
#cb .top{position:absolute;right:max(10px,env(safe-area-inset-right));top:max(78px,calc(env(safe-area-inset-top) + 72px));display:flex;flex-direction:column;gap:4px;align-items:flex-end;text-shadow:0 1px 2px #000}
#cb .top button{min-height:26px;padding:3px 9px;border-radius:10px;border:1px solid #fff7;background:#000a;font-size:11px}
#cb .stat{position:absolute;left:max(10px,env(safe-area-inset-left));top:max(76px,calc(env(safe-area-inset-top) + 70px));font-size:11px;text-shadow:0 1px 2px #000;line-height:1.35}
@media (orientation:landscape) and (max-height:520px){#cb .cl{grid-template-columns:repeat(3,48px);bottom:max(10px,env(safe-area-inset-bottom))}#cb .cl button{width:48px;height:48px}#cb .ab{bottom:max(4px,env(safe-area-inset-bottom))}#cb .sl{width:44px;height:44px}#cb .vit{bottom:max(184px,calc(env(safe-area-inset-bottom) + 178px))}}
`;
const NUM_POOL = 24, OH_POOL = 10;
export class CombatHUD {
  /* api: {use(i), dodge(), block(on), jump(), lock(), switchTarget(), potion(), swap(), exit(), summon()} - plain callbacks into the host.
     project(x,y,z,out) -> true if on screen (out[0],out[1] px). Heights are supplied by the host per entity (e.top). */
  constructor(cc, api, project) {
    this.cc = cc; this.api = api; this.project = project; this.cache = {}; this.nums = []; this.ohs = []; this.numI = 0; this.sc = [0, 0];
    const st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);
    const r = this.root = document.createElement('div'); r.id = 'cb';
    r.innerHTML = '<div class="flash"></div><div class="tp"><div class="nm"></div><div class="sub"></div><div class="bar hp"><i></i><b></b></div></div>' +
      '<div class="stat"></div><div class="top"><button type="button" data-a="summon">Summon Titan</button><button type="button" data-a="exit">Exit fight</button></div>' +
      '<div class="vit"><div class="por"><span>?</span><small>1</small></div><div class="bars"><div class="bar hp"><i></i><b></b></div><div class="bar mp"><i></i><b></b></div><div class="bar sp"><i></i><b></b></div></div></div>' +
      '<div class="ab">' + ABILITIES.map((a, i) => '<button type="button" class="sl" data-s="' + i + '"><span class="ic">' + a.icon + '</span><span class="k">' + (i + 1) + '</span><span class="c ' + (a.cost.mp ? 'mp' : 'sp') + '">' + (a.cost.mp || a.cost.sp || '') + '</span><span class="n">' + a.name + '</span><span class="cdv"></span><span class="ct"></span></button>').join('') + '</div>' +
      '<div class="cl"><button type="button" data-a="dodge"><span class="g">\u21BA</span>Dodge<span class="q">Spc</span><span class="cdv"></span></button><button type="button" data-a="block"><span class="g">\u26E8</span>Block<span class="q">RMB</span></button>' +
      '<button type="button" data-a="jump"><span class="g">\u2191</span>Jump<span class="q">J</span></button><button type="button" data-a="lock"><span class="g">\u25CE</span>Lock<span class="q">Q</span></button>' +
      '<button type="button" data-a="potion"><span class="g">\u2697</span>Potion<span class="q">R</span><span class="cdv"></span></button><button type="button" data-a="swap"><span class="g">\u2694</span>Weapon<span class="q">E</span></button></div><div class="msg"></div>';
    document.body.appendChild(r);
    const $ = s => r.querySelector(s), $$ = s => Array.from(r.querySelectorAll(s));
    this.tp = $('.tp'); this.tpNm = $('.tp .nm'); this.tpSub = $('.tp .sub'); this.tpBar = $('.tp .bar i'); this.tpTxt = $('.tp .bar b');
    const vb = n => ({ i: $('.vit .' + n + ' i'), b: $('.vit .' + n + ' b') }); this.vhp = vb('hp'); this.vmp = vb('mp'); this.vsp = vb('sp');
    this.por = $('.por span'); this.lvl = $('.por small'); this.stat = $('.stat'); this.msg = $('.msg'); this.flash = $('.flash'); this.sumBtn = $('[data-a=summon]');
    this.slots = $$('.sl').map(b => ({ b, cdv: b.querySelector('.cdv'), ct: b.querySelector('.ct'), cd: -1, st: '' }));
    this.btn = {}; $$('.cl button').forEach(b => { this.btn[b.dataset.a] = { b, cdv: b.querySelector('.cdv'), cd: -1 }; });
    for (let i = 0; i < NUM_POOL; i++) { const e = document.createElement('div'); e.className = 'fn'; r.appendChild(e); this.nums.push({ e, t: 9 }); }
    for (let i = 0; i < OH_POOL; i++) { const e = document.createElement('div'); e.className = 'oh'; e.innerHTML = '<i></i>'; r.appendChild(e); this.ohs.push({ e, f: e.firstChild, on: false, last: -1 }); }
    const stop = e => { e.preventDefault(); e.stopPropagation(); };
    r.addEventListener('pointerdown', e => {
      const b = e.target.closest('button'); if (!b) return; stop(e);
      if (b.dataset.s !== undefined) api.use(+b.dataset.s); else { const a = b.dataset.a; if (a === 'block') { this.blockPtr = e.pointerId; api.block(true); } else api[a] && api[a](); }
    });
    const up = e => { if (this.blockPtr === e.pointerId) { this.blockPtr = null; api.block(false); } };
    addEventListener('pointerup', up); addEventListener('pointercancel', up);
    r.addEventListener('contextmenu', e => e.preventDefault());
    cc.on('damage', d => this.onDamage(d)).on('heal', h => this.floatAt(h.x, 2.4 * cc.HS, h.z, '+' + h.n, 'heal')).on('hero', () => this.heroInfo())
      .on('denied', d => this.say(d.why, 900)).on('playerDown', () => this.say('You fell...', 2200)).on('reward', rw => this.say('+' + rw.xp + ' XP   +' + rw.gold + ' gold', 1300));
    this.heroInfo();
  }
  show(v) { this.root.style.display = v ? 'block' : 'none'; const d = document.getElementById('diagBtn'); if (d) { if (v) { this._dd = d.style.display; d.style.display = 'none'; } else if (this._dd !== undefined) d.style.display = this._dd; } }   /* #diagBtn sits under the first ability slot */
  heroInfo() { const h = this.cc.hero; this.por.textContent = (h.name || '?')[0]; this.lvl.textContent = h.level; this.cache.k = ''; }
  say(t, ms) { this.msg.textContent = t; this.msg.style.display = 'block'; clearTimeout(this._mt); this._mt = setTimeout(() => { this.msg.style.display = 'none'; }, ms || 1500); }
  floatAt(x, y, z, txt, cls) {
    const n = this.nums[this.numI++ % NUM_POOL]; if (!this.project(x, y, z, this.sc)) return;
    n.e.className = 'fn ' + (cls || ''); n.e.textContent = txt; n.x = this.sc[0]; n.y = this.sc[1]; n.t = 0; n.e.style.display = 'block';
  }
  onDamage(d) {
    const e = d.e;
    if (d.toPlayer) { this.floatAt(this.cc.p.x, 2.8 * this.cc.HS, this.cc.p.z, '-' + d.dmg, 'pl'); this.flash.style.opacity = '1'; setTimeout(() => { this.flash.style.opacity = '0'; }, 110); }
    else this.floatAt(e.x, (e.top || 2.4 * this.cc.HS) , e.z, (d.crit ? 'CRIT ' : '') + d.dmg, d.crit ? 'crit' : '');
  }
  setv(c, key, v, fn) { if (this.cache[key] !== v) { this.cache[key] = v; fn(v); } }
  bar(o, key, cur, max) { const f = Math.round(Math.max(0, cur) / max * 200) / 200; this.setv(null, key + 'f', f, v => { o.i.style.transform = 'scaleX(' + v + ')'; }); const t = Math.ceil(cur); this.setv(null, key + 't', t, v => { o.b.textContent = v + ' / ' + max; }); }
  /* once per frame */
  update(dt, enemies) {
    const cc = this.cc, R = cc.res;
    this.bar(this.vhp, 'hp', R.hp, R.max.hp); this.bar(this.vmp, 'mp', R.mp, R.max.mp); this.bar(this.vsp, 'sp', R.sp, R.max.sp);
    // target panel
    const t = cc.shownTarget();
    if (t) {
      this.setv(null, 'tid', t.id + (t.def.boss ? 'b' : ''), () => { this.tp.className = 'tp' + (t.def.boss ? ' boss' : ''); this.tpNm.textContent = t.def.name; this.tpSub.textContent = 'Lv ' + t.def.level + ' \u2022 ' + t.def.cls + (cc.tgt.locked ? ' \u2022 LOCKED' : ''); this.tp.style.display = 'block'; });
      this.setv(null, 'tlk', cc.tgt.locked, () => { this.tpSub.textContent = 'Lv ' + t.def.level + ' \u2022 ' + t.def.cls + (cc.tgt.locked ? ' \u2022 LOCKED' : ''); });
      const f = Math.round(t.hp / t.max * 400) / 400; this.setv(null, 'tf' + t.id, f, v => { this.tpBar.style.transform = 'scaleX(' + v + ')'; }); this.setv(null, 'tt' + t.id, Math.ceil(t.hp), v => { this.tpTxt.textContent = v + ' / ' + t.max; });
    } else if (this.cache.tid) { this.cache.tid = 0; this.tp.style.display = 'none'; }
    // ability bar
    for (let i = 0; i < 6; i++) {
      const a = ABILITIES[i], s = this.slots[i], left = cc.cd.left(a.id), use = cc.slotUsable(i), noRes = !R.can(a.cost);
      const q = Math.round(left * 10) / 10; if (q !== s.cd) { s.cd = q; s.cdv.style.height = left > 0 ? Math.round(cc.cd.frac(a.id) * 100) + '%' : '0'; s.ct.textContent = left > 0.05 ? (left >= 10 ? Math.ceil(left) : left.toFixed(1)) : ''; }
      const st = (use ? '' : 'off ') + (use && noRes && left <= 0 ? 'nores' : ''); if (st !== s.st) { s.st = st; s.b.className = 'sl ' + st; }
    }
    for (const k of ['dodge', 'potion']) { const o = this.btn[k], l = Math.round(cc.cd.left(k) * 5) / 5; if (l !== o.cd) { o.cd = l; o.cdv.style.height = l > 0 ? Math.round(cc.cd.frac(k) * 100) + '%' : '0'; } }
    this.setv(null, 'lockon', cc.tgt.locked, v => { this.btn.lock.b.classList.toggle('on', v); });
    this.setv(null, 'blk', cc.blocking, v => { this.btn.block.b.classList.toggle('on', v); });
    this.setv(null, 'pot', cc.potions, v => { this.btn.potion.b.querySelector('.q').textContent = 'x' + v; });
    this.setv(null, 'stat', cc.kills + '|' + cc.xp + '|' + cc.gold + '|' + cc.hero.saber, () => { this.stat.innerHTML = 'Kills ' + cc.kills + ' &bull; XP ' + cc.xp + ' &bull; Gold ' + cc.gold + (cc.hero.saber ? '' : '<br>Pick the Owner for the lightsaber'); });
    // floating numbers (transform only)
    for (const n of this.nums) { if (n.t >= 9) continue; n.t += dt; if (n.t > 0.9) { n.t = 9; n.e.style.display = 'none'; continue; } n.e.style.transform = 'translate3d(' + (n.x - 20) + 'px,' + (n.y - 56 * n.t) + 'px,0)'; n.e.style.opacity = n.t < 0.5 ? 1 : (0.9 - n.t) / 0.4; }
    // overhead bars (nearest few, pooled)
    let k = 0;
    for (const e of enemies) {
      if (e.state === 'defeated' || k >= OH_POOL) continue;
      if (!this.project(e.x, e.top || 2.4 * cc.HS, e.z, this.sc)) continue;
      if (e.def.boss) continue;
      const o = this.ohs[k++]; if (!o.on) { o.on = true; o.e.style.display = 'block'; }
      o.e.style.transform = 'translate3d(' + (this.sc[0] - 27) + 'px,' + this.sc[1] + 'px,0)';
      const f = Math.round(e.hp / e.max * 50) / 50; if (f !== o.last) { o.last = f; o.f.style.transform = 'scaleX(' + f + ')'; }
      const lk = cc.tgt.target === e; if (lk !== o.lk) { o.lk = lk; o.e.classList.toggle('lock', lk); }
    }
    for (; k < OH_POOL; k++) { const o = this.ohs[k]; if (o.on) { o.on = false; o.e.style.display = 'none'; } }
  }
}
