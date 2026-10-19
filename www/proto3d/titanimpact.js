// Tree impacts are opt-in for the oversized Ashen Titan test variants only.
export function titanTestFactor(id) {
  const m = /^n:ashentitan_(20|40|60)x$/.exec(id || '');
  return m ? Number(m[1]) : 0;
}
export function titanTreeReach(id, heightW) {
  return titanTestFactor(id) ? Math.min(11, Math.max(2.7, heightW * 0.11)) : 0;
}
export function treeInReach(tree, x, z, reach) {
  return reach > 0 && !tree.fallen && (tree.x - x) ** 2 + (tree.z - z) ** 2 < (reach + 0.35 * tree.s) ** 2;
}
