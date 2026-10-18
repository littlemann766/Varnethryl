/* Owner gate for the Varnethryl cheat panel. No DOM, no Three.js: runs in node tests and in the browser.
 *
 * TWO MODES
 *  'local'  (default, today): the owner types a secret passphrase. It is checked with PBKDF2-SHA256 against the salted hash below.
 *           Only the salt + hash are in the repo; the plaintext lives off-repo with the owner. A correct entry stores an unlock
 *           token in localStorage (key UNLOCK_KEY). Wrong entries are throttled (3 free tries, then 30 s doubling up to 1 h).
 *  'server' (later): when Firebase auth + the backend exist, call setServerOwnerProvider(async () => claims) once after sign-in.
 *           The provider must return the ID-token claims the BACKEND verified (or a boolean). From then on only
 *           ownerFromClaims(claims) decides ownership and the local passphrase/token is ignored entirely.
 *           Steps to switch: (1) backend sets custom claim {owner:true} (or put the owner UID in OWNER_UID_ALLOWLIST below);
 *           (2) in sync.js after sign-in: ownerGate.setServerOwnerProvider(() => auth.currentUser.getIdTokenResult().then(r => r.claims));
 *           (3) the backend must ALSO reject/flag saves carrying cheated:true. Client-side gating cannot stop a determined user.
 */
export const GATE = Object.freeze({ v: 1, salt: 'a656269d0204f85a5f3dd2960afecb80', hash: '698ef54900e9b9607825ebadb85da1cafcd9ed88cfdb40d6716feb33ea614508', iter: 210000 });
export const OWNER_UID_ALLOWLIST = Object.freeze([]);
export const UNLOCK_KEY = 'vn_owner_unlock_v1';
export const THROTTLE_KEY = 'vn_owner_attempts_v1';
export const FREE_TRIES = 3, LOCK_BASE_MS = 30000, LOCK_MAX_MS = 3600000, MAX_PASS_LEN = 128;

const enc = new TextEncoder();
export const toHex = (buf) => Array.from(new Uint8Array(buf), (b) => b.toString(16).padStart(2, '0')).join('');
export const fromHex = (h) => { const out = new Uint8Array(h.length >> 1); for (let i = 0; i < out.length; i++) out[i] = parseInt(h.substr(i * 2, 2), 16); return out; };
/* constant-time string compare (equal-length hex strings) */
export function constEq(a, b) { if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) return false; let r = 0; for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i); return r === 0; }

export async function derive(pass, saltHex, iter, subtle) {
  const s = subtle || globalThis.crypto.subtle, key = await s.importKey('raw', enc.encode(pass), 'PBKDF2', false, ['deriveBits']);
  return toHex(await s.deriveBits({ name: 'PBKDF2', hash: 'SHA-256', salt: fromHex(saltHex), iterations: iter }, key, 256));
}
export async function sha256Hex(text, subtle) { return toHex(await (subtle || globalThis.crypto.subtle).digest('SHA-256', enc.encode(text))); }
/* The persisted unlock token. Derived from the stored hash, so a leftover token from an older gate version stops working. */
export const unlockToken = (params, subtle) => sha256Hex(params.hash + ':unlock:v' + params.v, subtle);

/* Pure helper for the server flow: claims come from the backend-verified ID token. */
export function ownerFromClaims(claims, allowlist) {
  if (claims === true) return true;
  if (!claims || typeof claims !== 'object') return false;
  const list = allowlist || OWNER_UID_ALLOWLIST, uid = claims.uid || claims.user_id || claims.sub;
  return claims.owner === true || (typeof uid === 'string' && list.includes(uid));
}

function memStore() { const m = new Map(); return { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => { m.set(k, String(v)); }, removeItem: (k) => { m.delete(k); } }; }

/* opts: {storage, now, subtle, params}; all injectable for tests. */
export function createGate(opts) {
  const o = opts || {}, params = o.params || GATE, now = o.now || (() => Date.now());
  let storage = o.storage; if (!storage) { try { storage = globalThis.localStorage; } catch (e) { storage = null; } } if (!storage) storage = memStore();
  const subtle = o.subtle || (globalThis.crypto && globalThis.crypto.subtle);
  let provider = null;
  const get = (k) => { try { return storage.getItem(k); } catch (e) { return null; } };
  const put = (k, v) => { try { storage.setItem(k, v); } catch (e) { /* storage full or blocked: unlock simply will not persist */ } };
  const del = (k) => { try { storage.removeItem(k); } catch (e) { /* ignore */ } };
  const readAttempts = () => { try { const a = JSON.parse(get(THROTTLE_KEY)); if (a && Number.isFinite(a.fails) && Number.isFinite(a.until)) return { fails: Math.max(0, a.fails | 0), until: a.until }; } catch (e) { /* corrupt: treat as clean */ } return { fails: 0, until: 0 }; };
  const retryMs = () => Math.max(0, readAttempts().until - now());
  const gate = {
    get mode() { return provider ? 'server' : 'local'; },
    /* Switch to server-verified ownership. fn: async () => backend-verified claims | boolean. Pass null to go back to local mode. */
    setServerOwnerProvider(fn) { provider = typeof fn === 'function' ? fn : null; },
    retryMs,
    status() { const a = readAttempts(); return { mode: gate.mode, fails: a.fails, locked: a.until > now(), retryMs: Math.max(0, a.until - now()) }; },
    async isOwner() {
      if (provider) { try { return ownerFromClaims(await provider()); } catch (e) { return false; } }
      const t = get(UNLOCK_KEY); if (!t) return false;
      return constEq(t, await unlockToken(params, subtle));
    },
    /* Returns {ok, reason?, retryMs?}. Never reveals or stores the passphrase. */
    async unlock(pass) {
      if (provider) return { ok: false, reason: 'server-mode' };
      const a = readAttempts(), t = now();
      if (a.until > t) return { ok: false, reason: 'throttled', retryMs: a.until - t };
      if (typeof pass !== 'string' || !pass.length || pass.length > MAX_PASS_LEN) return gate.fail(a, t);
      let got = ''; try { got = await derive(pass.trim(), params.salt, params.iter, subtle); } catch (e) { return { ok: false, reason: 'crypto-unavailable' }; }
      if (constEq(got, params.hash)) { del(THROTTLE_KEY); put(UNLOCK_KEY, await unlockToken(params, subtle)); return { ok: true }; }
      return gate.fail(a, t);
    },
    fail(a, t) {
      const fails = a.fails + 1, over = fails - FREE_TRIES, wait = over >= 0 ? Math.min(LOCK_MAX_MS, LOCK_BASE_MS * Math.pow(2, over)) : 0;
      put(THROTTLE_KEY, JSON.stringify({ fails, until: wait ? t + wait : 0 }));
      return { ok: false, reason: wait ? 'throttled' : 'wrong', retryMs: wait, triesLeft: Math.max(0, FREE_TRIES - fails) };
    },
    lock() { del(UNLOCK_KEY); },
  };
  return gate;
}

let shared = null;
/* One gate per page, so sync.js can later call getOwnerGate().setServerOwnerProvider(...) and the panel sees it. */
export function getOwnerGate() { return shared || (shared = createGate()); }
