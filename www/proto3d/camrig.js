/* Camera rig for the 3D game: third person (zoomable, wall-safe) and first person. Owns zoom/pitch/view state and the input for them
 * (mouse wheel, pinch, + / - keys, V to switch view). main.js calls update() once per frame and syncHero() to hide the player's own model.
 * No extra draw calls: it only moves the existing camera. Collision is a 2D segment test against the same colliders the hero uses. */
import * as THREE from './vendor/three.module.js';
import { ZOOM_MIN, ZOOM_MAX, clampZoom, segmentClearT, cameraColliderBlocks } from './camprefs.js';
import { worldProfile } from './charscale.js';

export const FP_FOV = 72, FP_NEAR = 0.12, TP_NEAR = 0.5, PITCH_MAX = 1.2, MIN_TP_DIST_T = 0.02;
const typing = (t) => !!t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT');

/* env: {camera, canvas, colliders, HS, WORLD, prefs, onPrefs?:(prefs)=>void} */
export function createCamRig(env) {
  const { camera, canvas, colliders, HS, WORLD } = env, prefs = env.prefs;
  const pos = new THREE.Vector3(0, 8 * HS, 30), look = new THREE.Vector3(), want = new THREE.Vector3(), lk = new THREE.Vector3();
  let prof = worldProfile('', HS);   // active character real-size profile (charscale.js): camera distance/height multipliers + zoom clamp
  const zc = (z) => Math.max(prof.camMin, Math.min(prof.camMax, clampZoom(z)));
  const r = { prefs, zoom: clampZoom(prefs.zoom), zoomTarget: clampZoom(prefs.zoom), pitch: 0, pinching: false, hidden: false, hideHero: false, pos, look, camDist: 0 };
  let clearDistance = Infinity; // collision recovery eases out; obstruction pulls in immediately
  const changed = () => { prefs.zoom = r.zoomTarget; if (env.onPrefs) env.onPrefs(prefs); };
  Object.defineProperty(r, 'fp', { get: () => prefs.view === 'first' });
  r.setView = (v) => { const nv = v === 'first' ? 'first' : 'third'; if (prefs.view === nv) return nv; prefs.view = nv; r.snap = true; r.pitch = 0; changed(); return nv; };
  r.toggleView = () => r.setView(r.fp ? 'third' : 'first');
  r.setZoom = (z) => { r.zoomTarget = zc(z); changed(); return r.zoomTarget; };
  r.setProfile = (p) => { prof = p; r.prof = p; r.zoomTarget = zc(r.zoomTarget); clearDistance = Infinity; r.snap = true; };   // on character pick: new clamps; the saved zoom pref is kept (not overwritten)
  r.prof = prof;
  /* factor > 1 zooms out, < 1 zooms in; scaled by the zoom-sensitivity pref */
  r.zoomBy = (factor) => { if (r.fp) return r.zoomTarget; return r.setZoom(r.zoomTarget * Math.pow(factor, prefs.zoomSens)); };
  r.look = (dx, dy) => { r.pitch = Math.max(-PITCH_MAX, Math.min(PITCH_MAX, r.pitch + dy)); };
  r.snap = true;

  canvas.addEventListener('wheel', (e) => { e.preventDefault(); r.zoomBy(Math.exp(Math.max(-120, Math.min(120, e.deltaY)) * 0.0016)); }, { passive: false });
  const ptr = new Map(); let d0 = 0, z0 = 1;
  const dist2 = () => { const a = Array.from(ptr.values()); return Math.hypot(a[0].x - a[1].x, a[0].y - a[1].y) || 1; };
  canvas.addEventListener('pointerdown', (e) => { ptr.set(e.pointerId, { x: e.clientX, y: e.clientY }); if (ptr.size === 2) { r.pinching = true; d0 = dist2(); z0 = r.zoomTarget; } });
  canvas.addEventListener('pointermove', (e) => { const p = ptr.get(e.pointerId); if (!p) return; p.x = e.clientX; p.y = e.clientY; if (ptr.size === 2 && r.pinching && !r.fp) r.setZoom(z0 * Math.pow(d0 / dist2(), prefs.zoomSens)); });
  const up = (e) => { ptr.delete(e.pointerId); if (ptr.size < 2) setTimeout(() => { if (ptr.size < 2) r.pinching = false; }, 120); };
  canvas.addEventListener('pointerup', up); canvas.addEventListener('pointercancel', up);
  addEventListener('keydown', (e) => {
    if (typing(e.target) || e.ctrlKey || e.metaKey || e.altKey) return;
    if (e.key === '+' || e.key === '=' || e.code === 'NumpadAdd') r.zoomBy(0.88);
    else if (e.key === '-' || e.key === '_' || e.code === 'NumpadSubtract') r.zoomBy(1 / 0.88);
    else if (e.key === 'v' || e.key === 'V') r.toggleView();
  });

  /* c: {heroX, heroZ, hy (feet y incl. floor + fly), dispY, alt, camYaw, legacyZoom, portrait, dt, snap, inside} ; returns nothing, moves the camera */
  r.update = (c) => {
    const fp = r.fp, dt = c.dt, snap = c.snap || r.snap; r.snap = false;
    r.zoom += (r.zoomTarget - r.zoom) * (snap ? 1 : Math.min(1, dt * 10));
    const wantFov = fp ? FP_FOV : (innerWidth / innerHeight < 1 ? 58 : 48), wantNear = fp ? FP_NEAR : TP_NEAR;
    if (Math.abs(camera.fov - wantFov) > 0.01 || camera.near !== wantNear) { camera.fov = wantFov; camera.near = wantNear; camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); }
    const sy = Math.sin(c.camYaw), cy = Math.cos(c.camYaw);
    if (fp) {
      const cp = Math.cos(r.pitch), sp = Math.sin(r.pitch);
      // Keep the first-person view attached to the character's airborne body rather than
      // leaving the camera on the ground while the mesh jumps. The jump arc is
      // computed in main.js by the same physics that moves the character.
      const jumpRise = Math.max(0, Number.isFinite(c.jumpHeight) ? c.jumpHeight : 0);
      const eyeHeight = Math.max(HS * 1.55 * prof.camHeight, prof.heightW * .82);
      pos.set(c.heroX - sy * 0.12 * HS * prof.camHeight, c.dispY + c.alt + jumpRise + eyeHeight, c.heroZ - cy * 0.12 * HS * prof.camHeight);
      look.set(pos.x - sy * cp * 10, pos.y + sp * 10, pos.z - cy * cp * 10);
      camera.position.copy(pos); camera.lookAt(look); r.camDist = 0; r.hideHero = true; return;
    }
    const z = c.legacyZoom || 1, close = z < 1, f = r.zoom;
    const dist = HS * (close ? (c.portrait ? 7.0 : 6.0) * (z / 0.3) : (c.portrait ? 10.5 : 9)) * f * prof.camDist;
    // For giants, frame their *body*, not a point at human chest height.
    const height = Math.max(HS * (close ? 2.2 : (c.portrait ? 7.2 : 6.2)) * f * prof.camHeight, prof.heightW * .72);
    want.set(c.heroX + sy * dist, height + c.hy, c.heroZ + cy * dist);
    lk.set(c.heroX, Math.max(HS * (close ? 1.05 : 1.6) * prof.camHeight,prof.heightW * .55) + c.hy, c.heroZ);
    const k = snap ? 1 : 1 - Math.pow(0.0015, dt);
    pos.lerp(want, k); look.lerp(lk, k);
    /* Walls still block the camera, but tiny trunks below a giant's sightline
       must not yank a hundred-metre camera into the character every frame. */
    const full = Math.hypot(pos.x-c.heroX,pos.z-c.heroZ) || 1;
    const t = segmentClearT(colliders,c.heroX,c.heroZ,pos.x,pos.z,
      0.55*Math.min(prof.camDist,2), (obstacle,hitT) =>
        cameraColliderBlocks(obstacle,hitT,lk.y,pos.y));
    const obstacleDist = t<1 ? Math.max(0.1,full*Math.max(MIN_TP_DIST_T,t-.012)) : Infinity;
    // A collision may retract instantly for safety; release smoothly over
    // ~0.35 s so two adjacent tree trunks don't make the view oscillate.
    clearDistance = snap ? obstacleDist : Math.min(obstacleDist,
      clearDistance + Math.max(0,dt)*Math.max(4,dist)*3.0);
    if (!Number.isFinite(clearDistance) && t>=1) clearDistance=Infinity;
    if (clearDistance<full) {
      const frac=Math.max(MIN_TP_DIST_T,clearDistance/full);
      pos.x=c.heroX+(pos.x-c.heroX)*frac;
      pos.z=c.heroZ+(pos.z-c.heroZ)*frac;
      pos.y=lk.y+(pos.y-lk.y)*frac;
      // If a wall is closer than the large body's radius, lift the camera
      // rather than letting it sit inside the model's head/torso.
      const minBodyDistance=Math.max(HS*1.4,prof.heightW*.43);
      if (clearDistance<minBodyDistance) pos.y+=Math.min(prof.heightW*.4,Math.max(0,minBodyDistance-clearDistance)*.6);
    }
    const lim = (c.zh || WORLD) - 0.8, zx = c.zx || 0, zz = c.zz || 0;   /* clamp to the CURRENT map (the Wilds sit at x=1000: clamping to the town's bounds threw the camera 850 m away = empty world) */
    pos.x = Math.max(zx - lim, Math.min(zx + lim, pos.x)); pos.z = Math.max(zz - lim, Math.min(zz + lim, pos.z));
    if (pos.y < c.hy + 0.6 * prof.camHeight) pos.y = c.hy + 0.6 * prof.camHeight;
    camera.position.copy(pos); camera.lookAt(look);
    r.camDist = Math.hypot(pos.x - c.heroX, pos.z - c.heroZ);
    r.hideHero = false;   /* third person: the hero is never hidden */
  };
  /* hide / restore the player's own model (first person, or the camera pressed right up against the hero) */
  r.syncHero = (hero) => { if (r.hideHero) { hero.visible = false; r.hidden = true; } else if (r.hidden) { hero.visible = true; r.hidden = false; } };
  r.ZOOM_MIN = ZOOM_MIN; r.ZOOM_MAX = ZOOM_MAX;
  return r;
}
