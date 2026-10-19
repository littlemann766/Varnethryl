/* Cinder-only flight state and animation targets. Pure logic; no GLB or Three.js modifications. */
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
export function createCinderFlight() {
  const s = { active: false, alt: 0, verticalSpeed: 0, phase: 'ground' };
  s.reset = () => { s.active = false; s.alt = s.verticalSpeed = 0; s.phase = 'ground'; };
  s.toggle = () => { s.active = !s.active; s.phase = s.active ? 'takeoff' : s.alt > 0 ? 'landing' : 'ground'; };
  s.step = (dt, up = false, down = false) => {
    dt = clamp(dt, 0, 0.05);
    if (s.active) {
      const target = (up && !down) ? 6 : (down && !up) ? -5 : (s.alt < 1.8 ? 3.3 : 0);
      s.verticalSpeed += (target - s.verticalSpeed) * Math.min(1, dt * 3.5);
      s.alt = clamp(s.alt + s.verticalSpeed * dt, 0, 55);
      s.phase = s.alt < 1.8 ? 'takeoff' : 'fly';
    } else if (s.alt > 0) {
      s.phase = 'landing';
      s.verticalSpeed += (-Math.min(7, 2.5 + s.alt * 0.8) - s.verticalSpeed) * Math.min(1, dt * 4);
      s.alt = Math.max(0, s.alt + s.verticalSpeed * dt);
      if (s.alt === 0) { s.verticalSpeed = 0; s.phase = 'ground'; }
    } else s.phase = 'ground';
    return s;
  };
  return s;
}
export function cinderAnimationWeights(flight, speed, modelScale = 1) {
  const a = { idle: 0, walk: 0, run: 0, hover: 0, flap: 0, glide: 0, dive: 0, land: 0 };
  if (flight.phase === 'ground') {
    const v = speed / Math.max(0.01, modelScale);
    const move = clamp(v / 0.85, 0, 1), run = clamp((v - 0.9) / 1.2, 0, 1);
    a.idle = 1 - move; a.walk = move * (1 - run); a.run = move * run;
  } else if (flight.phase === 'landing') {
    a.land = 0.7; a.glide = 0.3;
  } else if (flight.phase === 'takeoff') {
    a.hover = 0.45; a.flap = 0.45; a.glide = 0.1;
  } else if (flight.verticalSpeed < -1.2 && speed > 1) {
    a.dive = 0.45; a.glide = 0.55;
  } else if (speed < 0.8) {
    a.hover = 0.55; a.flap = 0.35; a.glide = 0.10;
  } else {
    // Keep wings spread on their glide pose, with restrained authored flaps.
    a.glide = 0.65; a.flap = 0.35;
  }
  return a;
}
