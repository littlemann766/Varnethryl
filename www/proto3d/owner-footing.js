/* Varnethryl owner idle-foot planting.
 * The imported Idle clip can hold one boot partly off the floor. On idle only,
 * relax both leg chains toward their original rigged standing/bind pose.
 * Applied AFTER AnimationMixer.update and faded out before walking/running.
 * No GLB, cape, weapon, animation clip or save data is modified.
 */
export function createOwnerFooting(model, THREE) {
  if (!model || !THREE || typeof model.getObjectByName !== 'function') return null;
  const names = ['thigh_L', 'shin_L', 'foot_L', 'thigh_R', 'shin_R', 'foot_R'];
  const joints = names.map(name => model.getObjectByName(name));
  if (joints.some(j => !j || !j.isBone)) return null;

  // Capture the neutral pose BEFORE the mixer evaluates the authored Idle clip.
  const rig = joints.map(bone => ({
    bone, neutral: bone.quaternion.clone(), incoming: bone.quaternion.clone(),
    offset: new THREE.Vector3(),
  }));
  const feet = [rig[2], rig[5]];
  const left = new THREE.Vector3(), right = new THREE.Vector3(), adjusted = new THREE.Vector3();
  let idleBlend = 0, corrected = false;
  return {
    names,
    beforeAnimation() {
      // If a rig's Idle clip omits some leg tracks, reset last frame's
      // procedural pose first so smoothing never accumulates endlessly.
      if (!corrected) return;
      for (const j of rig) {
        j.bone.quaternion.copy(j.incoming);
        if (j.offset.lengthSq() > 0) { j.bone.position.sub(j.offset); j.offset.set(0, 0, 0); }
      }
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
      // Correct a small residual raised-boot gap left by imported hip motion.
      // Match ankle heights in WORLD space, never by pushing the whole hero
      // beneath the landscape (that would sink the opposite foot).
      if (typeof model.updateWorldMatrix === 'function') {
        model.updateWorldMatrix(true, true);
        feet[0].bone.getWorldPosition(left);
        feet[1].bone.getWorldPosition(right);
        const raised = left.y > right.y ? feet[0] : feet[1];
        const higher = left.y > right.y ? left : right;
        const lower = left.y > right.y ? right : left;
        const gap = higher.y - lower.y;
        if (gap > 0.018 && raised.bone.parent) {
          adjusted.copy(higher);
          adjusted.y -= Math.min(0.36, gap - 0.012) * weight;
          raised.bone.parent.worldToLocal(adjusted);
          raised.offset.copy(adjusted).sub(raised.bone.position);
          raised.bone.position.add(raised.offset);
        }
      }
      corrected = true;
    },
    get blend() { return idleBlend; },
  };
}
