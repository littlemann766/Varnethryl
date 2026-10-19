# Cinder flight candidate — v1.1.15 (NOT merged)

This change is isolated on `feature/cinder-natural-flight`. The production `main` branch remains at v1.1.14.

## What changed
- Wing stability: Cinder (NEW) uses the GLB's authored flap/hover/glide/dive/land clips without the generic spring-bone solver tugging on wing joints.
- Flight: a separate Take off / Land button, Ascend/Descend touch controls and the F / Space-E / Q-C keyboard controls. Smooth climb/descent and cross-faded flight poses.
- Reduced excessive wing closure by giving the open-wing glide clip greater weight than the flap clip during cruising.
- Added lightweight flame-colored embers anchored to both wing tips and tail, without modifying the model skeleton.
- Small ground hops while Cinder walks/runs.
- Version and offline cache updated to 1.1.15; new flight controller precached for offline play.

## Known limitations
- In-engine, real-device validation is **still required**. JavaScript parsing and automated logic tests do not prove Cinder looks right in motion.
- The improvements to wing motion and ember effects target the **Cinder (NEW)** model (`n:cinder_new`). The older `Cinder` GLB has only idle/walk clips and cannot use these authored flight blends yet.
- Embers are point particles, not final full-feather flame rendering.
- Cinder flight is a candidate feature; flight collision and landing against roofs/trees still require hands-on verification.

## Test before merging
1. Back up your saved game, select **Cinder (NEW)** and wait for the GLB to finish loading.
2. Tap **Take off**. Hold **Ascend** and **Descend**, then tap **Land** and verify that Cinder touches down.
3. Cruise and turn. Check for rubbery flap motion, wings touching above his head, jitter, and flickering.
4. Walk and run before takeoff. Check the small hops; reselect another hero and ensure their behavior is unchanged.
5. Inspect embers on the wing tips and tail. Test the same flow on Android, including game reopening/offline mode.
6. If any step fails, leave this branch unmerged; the v1.1.14 main version is unaffected.

Automated checks: `node tools/cinderflight_test.mjs`, `node tools/save3d_test.mjs` and existing `tools/*test*.mjs`.
