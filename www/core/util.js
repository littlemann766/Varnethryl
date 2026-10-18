/* Shared UI-free helpers. rng defaults to Math.random so behaviour matches the original game.js. */
export const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
export const rand=(a,b,rng=Math.random)=>a+rng()*(b-a);
export const sample=(a,rng=Math.random)=>a[Math.floor(rng()*a.length)];
