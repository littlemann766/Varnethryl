/* Party + progression rules. UI-free; takes the save state explicitly. */
import {HEROES} from '../data.js';
export function nLevel(state,id){return state.heroLevels[id]||1}
export function xpNeed(level){return Math.round(82+level*28+Math.pow(level,1.35)*15)}
/* Normalise party/active. hooks.ensure(s) (optional) runs the Quest/Mirror save sanitisers, as game.js did. */
export function sanitizeParty(s,hooks={}){let seen=new Set();s.party=(s.party||[]).map(Number).filter(id=>Number.isFinite(id)&&HEROES[id]&&!seen.has(id)&&seen.add(id));if(!s.party.length)s.party=[0];s.active=+s.active;if(!s.party.includes(s.active))s.active=s.party[0];if(hooks.ensure)hooks.ensure(s);return s}
/* Pure XP application (was the state part of grantExperience). Returns the number of account level-ups. */
export function applyExperience(state,amount){state.accountXp+=amount;for(const id of state.party)state.heroXp[id]=(state.heroXp[id]||0)+amount;let lvlups=0;while(state.accountXp>=xpNeed(state.accountLevel)){state.accountXp-=xpNeed(state.accountLevel);state.accountLevel++;lvlups++;}for(const id of state.party){let n=nLevel(state,id),x=state.heroXp[id]||0;while(x>=xpNeed(n)){x-=xpNeed(n);n++;}state.heroXp[id]=x;state.heroLevels[id]=n;}return lvlups}
