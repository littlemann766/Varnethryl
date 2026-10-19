/* On-screen button editor (DOM only, no draw calls). Each button gets a persisted {x, y, s} (px offset + scale) applied as a CSS transform,
 * so it works on top of whatever layout the button already has. Edit mode: drag to move, pinch (two fingers on a button) or the size slider to resize.
 * Stored per device in localStorage. Pure helpers are exported for node tests. */
export const LAYOUT_KEY = 'vn_btnlayout_v1', S_MIN = 0.6, S_MAX = 2;
const num = (v, d) => (Number.isFinite(+v) ? +v : d);
export function sanitizeLayout(raw) {
  const out = {}; if (!raw || typeof raw !== 'object') return out;
  for (const k of Object.keys(raw)) { if (!/^[a-z0-9_]{1,16}$/.test(k)) continue; const v = raw[k] || {};
    out[k] = { x: Math.max(-2000, Math.min(2000, num(v.x, 0))), y: Math.max(-2000, Math.min(2000, num(v.y, 0))), s: Math.max(S_MIN, Math.min(S_MAX, num(v.s, 1))) }; }
  return out;
}
export const loadLayout = (st) => { try { return sanitizeLayout(JSON.parse(st.getItem(LAYOUT_KEY))); } catch (e) { return {}; } };
export const saveLayout = (st, l) => { try { st.setItem(LAYOUT_KEY, JSON.stringify(sanitizeLayout(l))); } catch (e) { /* storage blocked */ } };
export const xform = (p) => 'translate(' + p.x.toFixed(0) + 'px,' + p.y.toFixed(0) + 'px) scale(' + p.s.toFixed(2) + ')';

/* root: container whose descendants matching `sel` are editable; each needs data-a. */
export function createButtonEditor({ root, storage, sel = '.pad button[data-a]' }) {
  let layout = loadLayout(storage), editing = false, selected = null; const ptr = new Map(); let g = null;
  const btns = () => [...root.querySelectorAll(sel)], get = (id) => layout[id] || (layout[id] = { x: 0, y: 0, s: 1 });
  const apply = (b) => { const p = layout[b.dataset.a]; b.style.transform = p ? xform(p) : ''; };
  const applyAll = () => btns().forEach(apply);
  const save = () => saveLayout(storage, layout);
  const style = document.createElement('style');
  style.textContent = '#cmb.editing .pad button{display:block!important;outline:2px dashed #ffe066;outline-offset:3px;touch-action:none}#cmb.editing .pad button.sel{outline-color:#7dff8a;outline-style:solid}';
  document.head.appendChild(style);
  root.addEventListener('pointerdown', (e) => {
    if (!editing) return; const b = e.target.closest && e.target.closest(sel); if (!b) return;
    e.preventDefault(); e.stopPropagation(); selected = b.dataset.a; btns().forEach((x) => x.classList.toggle('sel', x === b));
    ptr.set(e.pointerId, { x: e.clientX, y: e.clientY }); try { b.setPointerCapture(e.pointerId); } catch (er) { /* synthetic */ }
    const p = get(selected); g = { b, p0: { x: p.x, y: p.y, s: p.s }, pts: [...ptr.values()].map((q) => ({ ...q })), d0: 0 };
    if (ptr.size === 2) { const [a, c] = [...ptr.values()]; g.d0 = Math.hypot(a.x - c.x, a.y - c.y) || 1; g.p0 = { x: p.x, y: p.y, s: p.s }; }
    if (ptr.size === 1) g.start = { x: e.clientX, y: e.clientY };
  }, true);
  root.addEventListener('pointermove', (e) => {
    if (!editing || !g || !ptr.has(e.pointerId)) return; e.preventDefault(); ptr.set(e.pointerId, { x: e.clientX, y: e.clientY }); const p = get(g.b.dataset.a);
    if (ptr.size >= 2 && g.d0) { const [a, c] = [...ptr.values()]; p.s = Math.max(S_MIN, Math.min(S_MAX, g.p0.s * Math.hypot(a.x - c.x, a.y - c.y) / g.d0)); }
    else if (g.start) { p.x = Math.max(-2000, Math.min(2000, g.p0.x + e.clientX - g.start.x)); p.y = Math.max(-2000, Math.min(2000, g.p0.y + e.clientY - g.start.y)); }
    apply(g.b);
  }, true);
  const up = (e) => { if (!ptr.has(e.pointerId)) return; ptr.delete(e.pointerId); if (!ptr.size && g) { g = null; save(); } else if (g && ptr.size === 1) { const p = get(g.b.dataset.a); g.p0 = { x: p.x, y: p.y, s: p.s }; const [q] = [...ptr.values()]; g.start = { x: q.x, y: q.y }; g.d0 = 0; } };
  root.addEventListener('pointerup', up, true); root.addEventListener('pointercancel', up, true);
  const bar = document.createElement('div'); bar.id = 'btnEditBar';
  bar.style.cssText = 'position:fixed;left:50%;top:max(60px,calc(env(safe-area-inset-top) + 52px));transform:translateX(-50%);z-index:80;display:none;gap:8px;align-items:center;padding:8px 10px;background:#000c;border:1px solid #fff6;border-radius:12px;color:#fff;font:600 13px system-ui;pointer-events:auto;touch-action:manipulation';
  const sl = document.createElement('input'); sl.type = 'range'; sl.min = S_MIN; sl.max = S_MAX; sl.step = 0.05; sl.value = 1; sl.id = 'btnEditSize'; sl.style.width = '110px';
  const mk = (t, id) => { const b = document.createElement('button'); b.type = 'button'; b.id = id; b.textContent = t; b.style.cssText = 'min-height:40px;min-width:44px;border-radius:10px;border:1px solid #fff5;background:#243050;color:#fff;font:inherit'; return b; };
  const bReset = mk('Reset', 'btnEditReset'), bDone = mk('Done', 'btnEditDone');
  const lab = document.createElement('span'); lab.textContent = 'Tap a button'; lab.id = 'btnEditLab';
  bar.append(lab, sl, bReset, bDone); document.body.appendChild(bar);
  const refresh = () => { lab.textContent = selected ? 'Size: ' + selected : 'Tap a button'; sl.value = selected && layout[selected] ? layout[selected].s : 1; };
  root.addEventListener('pointerdown', () => setTimeout(refresh, 0), true);
  sl.addEventListener('input', () => { if (selected) api.setScale(selected, +sl.value); else sl.value = 1; });
  bReset.addEventListener('click', () => { api.reset(); refresh(); }); bDone.addEventListener('click', () => api.enable(false));
  applyAll();
  const api = {
    get editing() { return editing; }, get selected() { return selected; }, get layout() { return layout; },
    enable(on) { editing = !!on; root.classList.toggle('editing', editing); bar.style.display = editing ? 'flex' : 'none'; if (editing) refresh(); if (!editing) { selected = null; btns().forEach((x) => x.classList.remove('sel')); g = null; ptr.clear(); } },
    setScale(id, s) { if (!id) return; get(id).s = Math.max(S_MIN, Math.min(S_MAX, num(s, 1))); btns().filter((b) => b.dataset.a === id).forEach(apply); save(); },
    scaleOf(id) { return id && layout[id] ? layout[id].s : 1; },
    reset() { layout = {}; btns().forEach((b) => { b.style.transform = ''; }); save(); },
    applyAll,
  };
  return api;
}
