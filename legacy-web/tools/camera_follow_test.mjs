import { followYaw, sanitizePrefs, DEFAULT_PREFS, clampZoom, ZOOM_MIN, ZOOM_MAX } from '../www/proto3d/camprefs.js';
let ok = 0, bad = 0; const T = (n, c) => { c ? ok++ : bad++; console.log(c ? 'PASS' : 'FAIL', n); };
T('default camera mode is follow (behind character)', DEFAULT_PREFS.camMode === 'follow' && sanitizePrefs({}).camMode === 'follow');
T('free camera option persists', sanitizePrefs({ camMode: 'free' }).camMode === 'free' && sanitizePrefs({ camMode: 'bogus' }).camMode === 'follow');
T('pinch zoom clamped', clampZoom(99) === ZOOM_MAX && clampZoom(0.01) === ZOOM_MIN);
let y = 0; for (let i = 0; i < 600; i++) y = followYaw(y, 3, -6, 1 / 60);
T('camera settles directly behind a hero running away at an angle', Math.abs(y - Math.atan2(-3, 6)) < 0.01);
let yy = 0, mx = 0, prev = 0, flips = 0, last = 0; for (let i = 0; i < 600; i++) { const n = followYaw(yy, 3, -6, 1 / 60); const d = n - yy; if (d * last < -1e-9) flips++; if (Math.abs(d) > 0) last = d; mx = Math.max(mx, Math.abs(d) * 60); yy = n; }
T('no wobble (never reverses direction) and rate-capped <= 1.8 rad/s', flips === 0 && mx <= 1.8 + 1e-9);
T('standing still / walking toward the camera does not move it', followYaw(0.7, 0, 0, 0.016) === 0.7 && followYaw(0, 0, 6, 0.016) === 0);
const w = followYaw(0, 6, 0, 0.016); T('moving across the view (fwd component <0.5) leaves yaw alone', w === 0);
T('wraps the short way round', Math.abs(followYaw(3.1, -0.3, 6, 1 / 60) - 3.1) < 0.05);
console.log(ok + ' pass, ' + bad + ' fail'); process.exit(bad ? 1 : 0);
