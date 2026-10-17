// Varnethryl skill table. Data-driven: every hero has four slots (minor, heavy, superHeavy, ultimate).
// Until the design team writes the real skills, every hero uses the generic defaults below.
// To plug in a hero's skills, add an entry to HERO_SKILLS keyed by HEROES index (or hero name):
//   HERO_SKILLS[0] = { minor:{name:'Shield Bash',cd:4000,mult:1.5,range:110,icon:'<svg…>'}, heavy:{…}, superHeavy:{…}, ultimate:{…} };
// Any field you omit falls back to the default for that slot.
// Fields: name, cd (ms), mult (damage/heal multiplier), range (px), splash (px radius, 0 = single target),
//         act (animation timing key: minor|heavy|super|ult), charge (ultimate only: charge needed, default 100), icon (SVG markup or image URL).
const svg=(p)=>`<svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${p}</svg>`;
export const ICONS={
  basic:svg('<path d="M5 19 17 7M14 5l5 0 0 5M5 19l-1 1M8 16l-2 2"/>'),
  minor:svg('<path d="M12 3l3 6 6 1-4.5 4.2L18 21l-6-3.4L6 21l1.5-6.8L3 10l6-1z"/>'),
  heavy:svg('<path d="M4 20 14 10M12 4l8 8M9 7l8 8"/><path d="M15 3l6 6"/>'),
  superHeavy:svg('<path d="M12 2v6M12 16v6M2 12h6M16 12h6M5 5l4 4M15 15l4 4M19 5l-4 4M9 15l-4 4"/><circle cx="12" cy="12" r="2"/>'),
  ultimate:svg('<path d="M12 2l2.6 6.9 7.4.4-5.8 4.6 2 7.1L12 17l-6.2 4 2-7.1L2 9.3l7.4-.4z"/>')};
export const SLOTS=['minor','heavy','superHeavy','ultimate'];
export const DEFAULT_SKILLS={
  minor:     {name:'Quick Skill', cd:4000,  mult:1.5, range:200, splash:0,   act:'minor', icon:ICONS.minor},
  heavy:     {name:'Heavy Strike',cd:8000,  mult:2.4, range:150, splash:0,   act:'heavy', icon:ICONS.heavy},
  superHeavy:{name:'Super Heavy', cd:15000, mult:4.2, range:170, splash:110, act:'super', icon:ICONS.superHeavy},
  ultimate:  {name:'Ultimate',    cd:0,     mult:8,   range:260, splash:170, act:'ult',   icon:ICONS.ultimate, charge:100}};
export const HERO_SKILLS={};
export function resolve(heroId,heroName){const o=HERO_SKILLS[heroId]||HERO_SKILLS[heroName]||{};const r={};
  for(const s of SLOTS)r[s]={...DEFAULT_SKILLS[s],...(o[s]||{})};return r}
