/* Owner HUD icons (v2): one self-contained inline SVG per button, full-bleed circle (ring included). Purple/black/silver/gold royal palette matching the Owner saber
   (purple blade, white-hot core). Static, no external files, 1 small filter each. Gradient/filter ids are unique per icon (ids are document-global). */
const G = '#e3b559', GL = '#fff0b8', S = '#dfe4f0', SD = '#8f98b2', P = '#8b4dff', PL = '#c9a4ff', K = '#07050d';
const head = id => '<svg viewBox="0 0 100 100" aria-hidden="true"><defs>' +
  '<radialGradient id="' + id + 'r" cx="35%" cy="25%" r="85%"><stop offset="0" stop-color="#4a2f78"/><stop offset=".5" stop-color="#17102b"/><stop offset="1" stop-color="' + K + '"/></radialGradient>' +
  '<linearGradient id="' + id + 'b" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#5b22d9"/><stop offset=".6" stop-color="' + PL + '"/><stop offset="1" stop-color="#fff"/></linearGradient>' +
  '<linearGradient id="' + id + 'm" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e8e9f2"/><stop offset="1" stop-color="#7c849c"/></linearGradient>' +
  '<filter id="' + id + 'g" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>';
const ring = (id, hot) => '<circle cx="50" cy="50" r="48.5" fill="url(#' + id + 'r)"/>' +
  (hot ? '<circle cx="50" cy="50" r="46" fill="#ff5a1f" fill-opacity=".16"/>' : '') +
  '<circle cx="50" cy="50" r="47" fill="none" stroke="' + (hot ? '#ffb347' : G) + '" stroke-width="2.6"/><circle cx="50" cy="50" r="43" fill="none" stroke="' + SD + '" stroke-width=".7" stroke-dasharray="1.2 2.6"/>' +
  '<circle cx="50" cy="50" r="40.5" fill="none" stroke="' + (hot ? '#ff6a2a' : P) + '" stroke-opacity=".7" stroke-width="1.2"/>' +
  [[50, 3.6], [96.4, 50], [50, 96.4], [3.6, 50]].map(p => '<path d="M' + p[0] + ' ' + (p[1] - 3.4) + 'l2.8 3.4-2.8 3.4-2.8-3.4z" fill="' + (hot ? '#ffd27a' : GL) + '" stroke="' + K + '" stroke-width=".6" transform="rotate(0)"/>').join('');
const blade = (id, x1, y1, x2, y2) => '<g filter="url(#' + id + 'g)"><line x1="' + x1 + '" y1="' + y1 + '" x2="' + x2 + '" y2="' + y2 + '" stroke="#5b22d9" stroke-width="7.5" stroke-linecap="round"/><line x1="' + x1 + '" y1="' + y1 + '" x2="' + x2 + '" y2="' + y2 + '" stroke="url(#' + id + 'b)" stroke-width="4.4" stroke-linecap="round"/><line x1="' + x1 + '" y1="' + y1 + '" x2="' + x2 + '" y2="' + y2 + '" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/></g>';
const hilt = (id, x, y, ang) => '<g transform="rotate(' + ang + ' ' + x + ' ' + y + ')"><rect x="' + (x - 2) + '" y="' + y + '" width="4" height="12" rx="1.6" fill="url(#' + id + 'm)" stroke="' + K + '" stroke-width=".7"/><path d="M' + (x - 8) + ' ' + y + 'l8-3.4 8 3.4-8 3z" fill="' + G + '" stroke="' + K + '" stroke-width=".8"/><circle cx="' + x + '" cy="' + (y + 13) + '" r="2.6" fill="' + G + '" stroke="' + K + '" stroke-width=".7"/></g>';
export const OWNER_ICON = {
  basic: head('ob') + ring('ob') + blade('ob', 33, 59, 70, 24) + blade('ob', 67, 59, 30, 24) + hilt('ob', 33, 59, 45) + hilt('ob', 67, 59, -45) + '<circle cx="50" cy="41" r="2.2" fill="#fff" filter="url(#obg)"/></svg>',
  royal: head('or') + ring('or') +
    '<g filter="url(#org)"><path d="M17 69C27 36 56 20 85 27 64 34 46 50 36 76Z" fill="url(#orb)" stroke="' + S + '" stroke-width="1.4" stroke-linejoin="round"/><path d="M26 71C36 46 56 33 78 29" fill="none" stroke="#fff" stroke-width="1.4" stroke-linecap="round"/></g>' +
    '<path d="M22 79C32 60 46 52 60 48M28 84C40 70 52 64 64 62" fill="none" stroke="' + PL + '" stroke-opacity=".8" stroke-width="1.6" stroke-linecap="round"/>' +
    '<path d="M38 24l3.5 6 4.5-5.5 4.5 5.5 3.5-6 1.5 10h-18z" fill="' + G + '" stroke="' + K + '" stroke-width=".8" stroke-linejoin="round" transform="translate(-4 -6)"/></svg>',
  chains: head('oc') + ring('oc') +
    '<path d="M26 82c4-8 10-8 12-16M70 84c-3-8-9-10-9-18" fill="none" stroke="' + P + '" stroke-opacity=".75" stroke-width="2.6" stroke-linecap="round"/>' +
    '<g filter="url(#ocg)" transform="rotate(-35 50 50)" fill="none" stroke-linejoin="round">' + [[50, 20, 1], [50, 38, 0], [50, 56, 1], [50, 74, 0]].map(l => l[2] ? '<rect x="42.5" y="' + (l[1] - 8) + '" width="15" height="22" rx="7.5" stroke="' + K + '" stroke-width="6.2"/><rect x="42.5" y="' + (l[1] - 8) + '" width="15" height="22" rx="7.5" stroke="url(#ocm)" stroke-width="3.6"/>' : '<rect x="45.5" y="' + (l[1] - 8) + '" width="9" height="22" rx="4.5" stroke="' + K + '" stroke-width="6.2"/><rect x="45.5" y="' + (l[1] - 8) + '" width="9" height="22" rx="4.5" stroke="' + PL + '" stroke-width="3.2"/>').join('') + '</g>' +
    '<path d="M70 26l6 3-3 6M24 30l6-3 2 6" fill="none" stroke="' + G + '" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  wrath: head('ow') + ring('ow') +
    '<g stroke="' + PL + '" stroke-opacity=".7" stroke-width="1.4" stroke-linecap="round" fill="none"><path d="M18 40l10 2M20 62l9-4M80 38l-10 3M82 60l-10-3M50 12v8M50 88v-8"/></g>' +
    '<g filter="url(#owg)"><path d="M58 11 29 54h18l-7 35 32-46H52z" fill="url(#owb)" stroke="' + GL + '" stroke-width="1.8" stroke-linejoin="round"/><path d="M56 22 40 48M50 60l-4 18" stroke="#fff" stroke-width="1.2" stroke-linecap="round" fill="none"/></g></svg>',
  unholy: head('ou') + ring('ou', 1) +
    '<defs><radialGradient id="oum" cx="40%" cy="38%"><stop offset="0" stop-color="#ffe9a0"/><stop offset=".35" stop-color="#ff8a1f"/><stop offset=".75" stop-color="#9b1d12"/><stop offset="1" stop-color="#2a0a0c"/></radialGradient><linearGradient id="ouf" x1="1" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#ffd24a"/><stop offset=".5" stop-color="#ff5a1f"/><stop offset="1" stop-color="#ff5a1f" stop-opacity="0"/></linearGradient></defs>' +
    '<g filter="url(#oug)"><path d="M60 52C46 52 28 44 12 20 34 26 44 24 52 38 56 30 60 30 70 28 62 36 66 44 60 52Z" fill="url(#ouf)"/><path d="M58 50C46 52 34 50 24 38 38 42 48 42 56 46Z" fill="#fff3b0" fill-opacity=".85"/></g>' +
    '<g filter="url(#oug)"><path d="M64 36 79 41 84 56 76 70 60 73 47 64 46 48 54 38Z" fill="url(#oum)" stroke="#ffd27a" stroke-width="1.6" stroke-linejoin="round"/><path d="M58 44l9 8-3 9M72 48l-4 5M52 56l8 2" stroke="#ffe9a0" stroke-width="1.4" stroke-linecap="round" fill="none"/></g>' +
    '<path d="M30 70l-5 8M40 78l-3 9M82 28l6-5M88 40l7-2" stroke="#ffb347" stroke-width="2" stroke-linecap="round"/></svg>',
};
OWNER_ICON.holy = OWNER_ICON.unholy;   // tinted gold/white by CSS (Unholy is tinted purple/black)
