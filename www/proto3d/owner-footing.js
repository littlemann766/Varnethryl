/* Varnethryl owner idle-foot planting.
 * The imported Idle clip can hold one boot partly off the floor. On idle only,
 * relax both leg chains toward their original rigged standing/bind pose.
 * Applied AFTER AnimationMixer.update and faded out before walking/running.
 * No GLB, cape, weapon, animation clip or save data is modified.
 */
export function createOwnerFooting(model) {
  if (!model || typeof model.getObjectByName !== 'function') return null;
  const names = ['thigh_L', 'shin_L', 'foot_L', 'thigh_R', 'shin_R', 'foot_R'];
  const joints = names.map(name => model.getObjectByName(name));
  if (joints.some(j => !j || !j.isBone)) return null;

  // Capture the neutral pose BEFORE the mixer evaluates the authored Idle clip.
  const rig = joints.map(bone => ({
    bone, neutral: bone.quaternion.clone(), incoming: bone.quaternion.clone(),
  }));
  let idleBlend = 0, corrected = false;
  return {
    names,
    beforeAnimation() {
      // If a rig's Idle clip omits some leg tracks, reset last frame's
      // procedural pose first so smoothing never accumulates endlessly.
      if (!corrected) return;
      for (const j of rig) j.bone.quaternion.copy(j.incoming);
      corrected = false;
    },
    afterAnimation(speed, dt) {
      const v = Number.isFinite(speed) ? Math.max(0, speed) : 0;
      // Feet plant at rest, but regular authored locomotion wins before the
      // hero has built up a meaningful walking speed.
      const target = v <= 0.09 ? 1 : v >= 0.72 ? 0 : (0.72 - v) / (0.72 - 0.09);
      const seconds = Number.isFinite(dt) ? Math.max(0, Math.min(dt, 0.1)) : 0;
      const t = 1 - Math.exp(-seconds * 9);
      idleBlend += (target - idleBlend) * t;
      if (idleBlend < 0.0005) { idleBlend = 0; return; }
      const weight = Math.min(1, idleBlend * 0.98);
      for (const j of rig) {
        j.incoming.copy(j.bone.quaternion);
        j.bone.quaternion.slerp(j.neutral, weight);
      }
      corrected = true;
    },
    get blend() { return idleBlend; },
  };
}
