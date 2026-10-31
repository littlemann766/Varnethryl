# Varnethryl — Permanent traversal and building design rules

Approved 23 October 2026 by project owner. Apply to **all existing and future buildings**.

1. Use **climbable ladders**, not stair flights or staircases, for every building's upper-floor access. The same requirement applies to the main town perimeter wall and watchtower access.
2. Do not render a `Climb` prompt, interaction button, or press-to-climb UI. The movement joystick and directional keyboard controls must handle **grab, ascend, pause, reverse, and descend**. Move toward the ladder to grab it, continue toward the top to climb, stop input to pause, and reverse to climb back down.
3. Use `Builder.prototype.stairs()` only as the compatibility entry point for a **ladder connector**; never restore procedural stair flight meshes. `Builder.prototype.gallery()` and `Builder.prototype.fullUpper()` must automatically use ladder hatches. Future structures should register `ladderSites`, not custom stair models.
4. Upper storeys, battlements, and watchtowers remain walkable. Ladder exits must land on actual upper-floor collision surfaces; hatches must not be sealed by slabs or railings.
5. Movement and jumping are independent. All players get **two jumps per landing**. Only a locally verified Owner unlock or a **server-verified CoOwner rank** receives **four jumps per landing**. A title or skin name is not sufficient for CoOwner authorization.
6. A running or moving jump can travel off a battlement or upper-floor edge with normal gravity and a landing reset; stationary walking without jumping keeps normal edge collision safety.
7. Keep ladder visuals efficient on Android (instanced rungs/rails). Other-world maps must not inherit invisible Town collision or ladder meshes.

**Regression gate**: `node tools/check_ladders_jump.mjs` runs in both Android and GitHub Pages workflows. Test on a device before describing it as fully verified.

This policy does not automatically remove existing terrain slopes, roads, or non-building spectator access ramps. Changing those requires a separate playable navigation review.
