/* Minimal combat HUD (DOM only, zero draw calls): own HP bar, target bar, pooled overhead enemy bars, pooled floating numbers, phone buttons.
 * Presentation only: it reads the CombatController and never computes damage. Every node is built once; per frame we write a style/text only when it changed. */
const CSS = '#cmb{position:fixed;inset:0;z-index:45;pointer-events:none;font:700 12px system-ui,sans-serif;color:#fff;-webkit-user-select:none;user-select:none;display:none}'
 + '#cmb *{box-sizing:border-box}'
 + '#cmb .bar{position:relative;height:13px;border:1px solid #000;border-radius:7px;background:#2a2a2a;overflow:hidden}#cmb .bar i{position:absolute;inset:0;transform-origin:left;background:linear-gradient(#ff6b6b,#c21f1f)}#cmb .bar b{position:absolute;inset:0;text-align:center;font-size:9px;line-height:12px;text-shadow:0 1px 1px #000}'
 + '#cmb .me{position:absolute;left:max(12px,env(safe-area-inset-left));bottom:max(196px,calc(env(safe-area-inset-bottom) + 190px));width:min(190px,46vw)}#cmb .me .bar i{background:linear-gradient(#7dff8a,#1fa83a)}#cmb .me .sp i{background:linear-gradient(#ffe066,#c9a200)}#cmb .me .sp{height:8px;margin-top:3px}'
 + '#cmb .tp{position:absolute;left:50%;top:calc(max(8px,env(safe-area-inset-top)) + 46px);transform:translateX(-50%);width:min(220px,50vw);padding:3px 8px 5px;border:1px solid #fff6;border-radius:8px;background:#000a;display:none}#cmb .tp .nm{font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}'
 + '#cmb .bs{position:absolute;left:50%;top:calc(max(8px,env(safe-area-inset-top)) + 100px);transform:translateX(-50%);width:min(420px,78vw);display:none}#cmb .bs .nm{text-align:center;font:900 13px system-ui;text-shadow:0 1px 3px #000;margin-bottom:2px}#cmb .bs .bar{height:16px;border-width:2px;border-color:#e8c26a}#cmb .bs .bar i{background:linear-gradient(#d65a5a,#7a1414)}#cmb .bs .bar b{font-size:11px;line-height:14px}'
 + '#cmb .oh{position:absolute;left:0;top:0;width:56px;height:8px;border:1px solid #000;border-radius:4px;background:#500;overflow:hidden;display:none;will-change:transform}#cmb .oh i{display:block;height:100%;width:100%;transform-origin:left;background:#e33}#cmb .oh.lock{border-color:#ffd54a;box-shadow:0 0 6px #ffd54a}'
 + '#cmb .fn{position:absolute;left:0;top:0;font:900 20px system-ui;color:#ffe066;text-shadow:0 0 3px #000,0 2px 2px #000;white-space:nowrap;display:none;will-change:transform,opacity}#cmb .fn.pl{color:#ff5a5a}#cmb .fn.heal{color:#7dff8a}#cmb .fn.big{font-size:27px;color:#ff9d2e}'
 + '#cmb .msg{position:absolute;left:50%;top:30%;transform:translate(-50%,-50%);font:900 24px system-ui;text-shadow:0 2px 8px #000;display:none;text-align:center}'
 + '#cmb .pad{position:absolute;right:max(136px,calc(env(safe-area-inset-right) + 132px));bottom:max(40px,calc(env(safe-area-inset-bottom) + 34px));display:flex;gap:10px;align-items:flex-end}'
 + '#cmb .pad button{pointer-events:auto;touch-action:none;color:#fff;font:700 11px system-ui;border-radius:50%;border:2px solid #fffc;background:#2a0c0cdd;width:54px;height:54px;padding:0;line-height:1.05}#cmb .pad button.atk{width:78px;height:78px;font-size:14px;background:#7a1010e6;border-color:#ffb0b0}#cmb .pad button.on{background:#2aa;border-color:#9ff}#cmb .pad button:active{filter:brightness(1.4)}#cmb .pad .g{display:block;font:400 20px system-ui}#cmb .pad button.own{display:none;position:absolute;bottom:88px;width:46px;height:46px;font-size:9px;background:#3a1060e6}#cmb .pad button[data-a=u1]{right:0}#cmb .pad button[data-a=u5]{right:54px}'
 + '#cmb .flash{position:absolute;inset:0;background:radial-gradient(transparent 45%,#f00a);opacity:0;transition:opacity .25s}';
import { createButtonEditor } from './btnedit.js';
const NUMS = 16, OHS = 8;

export function createCombatHud(cc, api, project) {
  const style = document.createElement('style'); style.textContent = CSS; document.head.appendChild(style);
  const root = document.createElement('div'); root.id = 'cmb';
  root.innerHTML = '<div class="flash"></div><div class="tp"><div class="nm"></div><div class="bar"><i></i><b></b></div></div>'
    + '<div class="me"><div class="bar hp"><i></i><b></b></div><div class="bar sp"><i></i></div></div><div class="msg"></div><div class="bs"><div class="nm"></div><div class="bar"><i></i><b></b></div></div>'
    + '<div class="pad"><button type="button" class="own" data-a="u1"><span class="g">\u2735</span>Push</button><button type="button" class="own" data-a="u5"><span class="g">\u2604</span>Storm</button><button type="button" data-a="lock"><span class="g">\u25CE</span>Lock</button><button type="button" data-a="dodge"><span class="g">\u21BA</span>Dodge</button><button type="button" class="atk" data-a="atk"><span class="g">\u2694</span>ATTACK</button></div>';
  document.body.appendChild(root);
  const $ = (s) => root.querySelector(s), h = { tp: $('.tp'), nm: $('.tp .nm'), ti: $('.tp .bar i'), tb: $('.tp .bar b'), mi: $('.me .hp i'), mb: $('.me .hp b'), si: $('.me .sp i'), msg: $('.msg'), bs: $('.bs'), bsn: $('.bs .nm'), bsi: $('.bs .bar i'), bsb: $('.bs .bar b'), flash: $('.flash'), lock: $('[data-a=lock]'), own: root.querySelectorAll('.own') };
  const cache = {}, set = (k, v, fn) => { if (cache[k] !== v) { cache[k] = v; fn(v); } };
  const nums = [], ohs = []; let ni = 0, msgT = 0, sc = [0, 0];
  for (let i = 0; i < NUMS; i++) { const d = document.createElement('div'); d.className = 'fn'; root.appendChild(d); nums.push({ d, t: -1, x: 0, y: 0, z: 0 }); }
  for (let i = 0; i < OHS; i++) { const d = document.createElement('div'); d.className = 'oh'; d.innerHTML = '<i></i>'; root.appendChild(d); ohs.push({ d, i: d.firstChild, last: -1 }); }
  const press = (el, down, up) => { el.addEventListener('pointerdown', (e) => { e.preventDefault(); e.stopPropagation(); down(); }); if (up) for (const t of ['pointerup', 'pointercancel', 'pointerleave']) el.addEventListener(t, up); };
  press($('[data-a=atk]'), () => api.use(0)); press($('[data-a=dodge]'), () => api.dodge()); press(h.lock, () => api.lock());
  press($('[data-a=u1]'), () => api.use(2)); press($('[data-a=u5]'), () => api.use(5));
  let st = null; try { st = localStorage; } catch (e) { st = null; }
  const editor = createButtonEditor({ root, storage: st || { getItem() { return null; }, setItem() {} } });
  const fmt = (n) => (n >= 1e6 ? (n / 1e6).toFixed(1) + 'M' : n >= 1e4 ? Math.round(n / 1e3) + 'k' : String(Math.round(n)));
  const hud = {
    root, editor, show(v) { root.style.display = v ? 'block' : 'none'; },
    say(t, ms) { h.msg.textContent = t; h.msg.style.display = 'block'; msgT = (ms || 1500) / 1000; },
    floatAt(x, y, z, text, cls) { const n = nums[ni++ % NUMS]; n.d.textContent = text; n.d.className = 'fn ' + (cls || ''); n.d.style.display = 'block'; n.t = 0; n.x = x; n.y = y; n.z = z; },
    hurtFlash() { h.flash.style.opacity = 0.9; setTimeout(() => { h.flash.style.opacity = 0; }, 120); },
    update(dt, enemies, owner) {
      const r = cc.res; set('hp', Math.round(r.hp / r.max.hp * 1000), (v) => { h.mi.style.transform = 'scaleX(' + v / 1000 + ')'; });
      set('hpt', cc.god ? 'GOD ' + fmt(r.hp) : fmt(r.hp) + ' / ' + fmt(r.max.hp), (v) => { h.mb.textContent = v; });
      set('sp', Math.round(r.sp / r.max.sp * 100), (v) => { h.si.style.transform = 'scaleX(' + v / 100 + ')'; });
      set('lockon', !!cc.tgt.locked, (v) => { h.lock.classList.toggle('on', v); });
      set('own', !!owner, (v) => { for (const b of h.own) b.style.display = v ? 'block' : 'none'; });
      const t = cc.shownTarget();
      set('tp', !!t, (v) => { h.tp.style.display = v ? 'block' : 'none'; });
      if (t) { set('tnm', t.def.name + ' Lv' + t.def.level, (v) => { h.nm.textContent = v; }); set('thp', Math.round(t.hp / t.max * 1000), (v) => { h.ti.style.transform = 'scaleX(' + v / 1000 + ')'; }); set('tht', fmt(t.hp) + ' / ' + fmt(t.max), (v) => { h.tb.textContent = v; }); }
      let boss = null; for (const e of enemies) if (e.def.boss && e.state !== 'defeated') { boss = e; break; }
      set('bs', !!boss, (v) => { h.bs.style.display = v ? 'block' : 'none'; });
      if (boss) { set('bsn', boss.def.name + ' Lv' + boss.def.level, (v) => { h.bsn.textContent = v; }); set('bsh', Math.round(boss.hp / boss.max * 1000), (v) => { h.bsi.style.transform = 'scaleX(' + v / 1000 + ')'; }); set('bst', fmt(boss.hp) + ' / ' + fmt(boss.max), (v) => { h.bsb.textContent = v; }); }
      if (msgT > 0) { msgT -= dt; if (msgT <= 0) h.msg.style.display = 'none'; }
      for (const n of nums) { if (n.t < 0) continue; n.t += dt; const u = n.t / 1.0; if (u >= 1 || !project(n.x, n.y + u * 1.6, n.z, sc)) { n.t = -1; n.d.style.display = 'none'; continue; } n.d.style.transform = 'translate3d(' + (sc[0] - 20).toFixed(0) + 'px,' + (sc[1] - 12).toFixed(0) + 'px,0)'; n.d.style.opacity = u < 0.6 ? 1 : 1 - (u - 0.6) / 0.4; }
      let k = 0;
      for (const e of enemies) {
        if (k >= OHS) break; const o = ohs[k];
        const show = e.state !== 'defeated' && !e.def.boss && (e.hp < e.max || cc.shownTarget() === e) && project(e.x, e.top || 2.5, e.z, sc);
        if (!show) continue; k++;
        o.d.style.display = 'block'; o.d.style.transform = 'translate3d(' + (sc[0] - 28).toFixed(0) + 'px,' + (sc[1] - 8).toFixed(0) + 'px,0)'; o.d.classList.toggle('lock', cc.tgt.locked && cc.tgt.target === e);
        const v = Math.round(e.hp / e.max * 100); if (o.last !== v) { o.last = v; o.i.style.transform = 'scaleX(' + v / 100 + ')'; }
      }
      for (; k < OHS; k++) if (ohs[k].d.style.display !== 'none') ohs[k].d.style.display = 'none';
    },
  };
  return hud;
}
