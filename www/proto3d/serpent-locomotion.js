/* Varnethryl serpent locomotion: prefer authored spine-animated clips.
 * This changes clip selection only, never edits the model, skeleton, or saves.
 * Returns the same actions object so all combat and idle clip references survive. */
export function preferSerpentClips(id, act) {
  if (!/vaelthryx/i.test(String(id)) || !act) return act;
  const slither = act.slither || act.Slither || act.body_wave || act.BodyWave;
  const fast = act.slither_fast || act.slitherFast || act.Slither_fast || act.SlitherFast;
  if (slither) act.walk = slither;
  if (fast) act.run = fast;
  else if (slither) act.run = slither;
  return act;
}
