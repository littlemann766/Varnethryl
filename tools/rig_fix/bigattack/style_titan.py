# Ashen Titan: slow, colossal. Event timings from the Godot sidecar (ashentitan_volcano_11x.json):
#   eruption_slam 2.962 s, fist_impact aoe t=1.288 at glTF (0,0,5.89 m) for a 20.955 m titan -> 0.281 H forward, floor
#   magma_sweep 2.684 s, lava spray from hand_R t=0.976 (wind back ~0.9 s)
FWD = 0.281; FZ = 0.083          # wrist height above floor when the fist is on the ground (fist thickness)
def fist(s, y=-FWD, x=0.115, z=FZ): return ((x if s == 'L' else -x, y, z), 1.0)
def eruption_slam():
    T = 1.288
    r = body(lean=-6); armfk(r, 'L', 10, 8, 15); armfk(r, 'R', 10, 8, 15); key(0, rot=r)
    # 0-0.95: heave both fists up overhead, chest arches back, weight rises onto the balls of the feet
    r = body(lean=-22, head=-12); armfk(r, 'L', 168, 14, 40); armfk(r, 'R', 168, 14, 40)
    key(0.80, hips=(0, 0.02, 0.012), rot=r, jaw=10); key(0.95, hips=(0, 0.025, 0.016), rot=r, jaw=14)
    # 0.95-1.288: the whole torso folds forward and down, knees sink, fists hammer the ground
    r = body(lean=32, head=8); armfk(r, 'L', 110, 10, 20); armfk(r, 'R', 110, 10, 20)
    key(1.14, hips=(0, -0.04, -0.07), rot=r, ik={'armL': fist('L', -FWD*0.9, z=0.25), 'armR': fist('R', -FWD*0.9, z=0.25)}, jaw=20)
    r = body(lean=72, head=24); armfk(r, 'L', 70, 6, 5); armfk(r, 'R', 70, 6, 5)
    key(T, hips=(0, -0.08, -0.21), rot=r, ik={'armL': fist('L'), 'armR': fist('R')}, jaw=26)
    # impact hold: recoil shudder, fists stay buried
    key(T+0.12, hips=(0, -0.08, -0.22), rot=r, ik={'armL': fist('L'), 'armR': fist('R')}, jaw=22)
    key(1.9, hips=(0, -0.075, -0.205), rot=r, ik={'armL': fist('L'), 'armR': fist('R')}, jaw=12)
    # 1.9-2.962: heavy recovery to idle
    r = body(lean=20, head=4); armfk(r, 'L', 30, 8, 20); armfk(r, 'R', 30, 8, 20)
    key(2.45, hips=(0, -0.03, -0.06), rot=r, ik={'armL': fist('L', -FWD*0.8, z=0.18)[:1] + (0.3,), 'armR': fist('R', -FWD*0.8, z=0.18)[:1] + (0.3,)})
    r = body(lean=-6); armfk(r, 'L', 10, 8, 15); armfk(r, 'R', 10, 8, 15)
    end = key(2.962, rot=r); CONTACT['eruption_slam'] = (T, 'fist_impact'); return end
def magma_sweep():
    # long wind back to his right, then a rising backhand-to-forehand scoop that flings lava forward-left (spray at 0.976)
    r = body(lean=-4); armfk(r, 'L', 10, 8, 15); armfk(r, 'R', 10, 8, 15); key(0, rot=r)
    r = body(lean=14, twist=-38, head=-4); armfk(r, 'R', -35, 40, 30, yaw=-20); armfk(r, 'L', 35, 20, 30)
    key(0.85, hips=(0.0, 0.01, -0.05), rot=r, ik={'legR': foot('R', 0.03)})
    r = body(lean=16, twist=24, head=-6); armfk(r, 'R', 75, 18, 12, yaw=10); armfk(r, 'L', -10, 25, 25)
    key(0.976, hips=(0, -0.02, -0.03), rot=r, ik={'legR': foot('R', 0.03)}, jaw=16)
    r = body(lean=8, twist=36, head=-8); armfk(r, 'R', 100, 30, 20, yaw=35); armfk(r, 'L', -15, 25, 25)
    key(1.25, hips=(0, -0.025, -0.02), rot=r, ik={'legR': foot('R', 0.03)}, jaw=10)
    r = body(lean=-4); armfk(r, 'L', 10, 8, 15); armfk(r, 'R', 10, 8, 15)
    end = key(2.684, rot=r); CONTACT['magma_sweep'] = (0.976, 'lava_spray_0'); return end
def attack1():   # titan generic: single right-fist hammer to the ground (contact 0.95 s)
    r = body(lean=-4); armfk(r, 'L', 10, 8, 15); armfk(r, 'R', 10, 8, 15); key(0, rot=r)
    r = body(lean=-12, twist=-22, side=6); armfk(r, 'R', 160, 25, 45); armfk(r, 'L', 25, 15, 20); key(0.6, hips=(0, 0.01, 0.01), rot=r, jaw=8)
    r = body(lean=64, twist=18, side=-6, head=20); armfk(r, 'R', 75, 10, 8); armfk(r, 'L', 10, 30, 30)
    key(0.95, hips=(0.01, -0.06, -0.17), rot=r, ik={'armR': fist('R', -FWD*0.95, x=0.10)}, jaw=20)
    key(1.25, hips=(0.01, -0.06, -0.175), rot=r, ik={'armR': fist('R', -FWD*0.95, x=0.10)}, jaw=10)
    r = body(lean=-4); armfk(r, 'L', 10, 8, 15); armfk(r, 'R', 10, 8, 15)
    end = key(1.9, rot=r); CONTACT['attack1'] = (0.95, 'fist'); return end
def attack2():   # left backhand sweep, torso unwinds right-to-left... mirrored scoop, waist-high
    r = body(lean=-4); armfk(r, 'L', 10, 8, 15); armfk(r, 'R', 10, 8, 15); key(0, rot=r)
    r = body(lean=8, twist=34); armfk(r, 'L', -20, 45, 35, yaw=25); armfk(r, 'R', 30, 20, 30); key(0.7, hips=(0, 0.01, -0.04), rot=r)
    r = body(lean=14, twist=-36, head=-6); armfk(r, 'L', 70, 70, 20, yaw=-55); armfk(r, 'R', -10, 25, 25); key(1.0, hips=(0, -0.02, -0.06), rot=r, jaw=14)
    r = body(lean=8, twist=-44); armfk(r, 'L', 85, 60, 25, yaw=-70); armfk(r, 'R', -15, 25, 25); key(1.2, hips=(0, -0.02, -0.05), rot=r)
    r = body(lean=-4); armfk(r, 'L', 10, 8, 15); armfk(r, 'R', 10, 8, 15)
    return key(1.95, rot=r)
def attack3():   # double-fist stomp-slam: stomp left foot, both fists down beside it
    r = body(lean=-4); armfk(r, 'L', 10, 8, 15); armfk(r, 'R', 10, 8, 15); key(0, rot=r)
    r = body(lean=-10); armfk(r, 'L', 130, 35, 50); armfk(r, 'R', 130, 35, 50); key(0.7, hips=(0, 0.01, 0.02), rot=r, ik={'legL': foot('L', -0.02, 0.10)}, jaw=8)
    r = body(lean=66, head=20); armfk(r, 'L', 75, 15, 8); armfk(r, 'R', 75, 15, 8)
    key(1.05, hips=(0, -0.07, -0.19), rot=r, ik={'legL': foot('L', -0.06), 'armL': fist('L', -FWD*0.9, x=0.16), 'armR': fist('R', -FWD*0.9, x=0.16)}, jaw=24)
    key(1.35, hips=(0, -0.07, -0.195), rot=r, ik={'legL': foot('L', -0.06), 'armL': fist('L', -FWD*0.9, x=0.16), 'armR': fist('R', -FWD*0.9, x=0.16)}, jaw=10)
    r = body(lean=-4); armfk(r, 'L', 10, 8, 15); armfk(r, 'R', 10, 8, 15)
    end = key(2.2, rot=r, ik={'legL': foot('L', -0.03)}); CONTACT['attack3'] = (1.05, 'fists'); return end
VOLC = H > 15
for nm, fn in ([('eruption_slam', eruption_slam), ('magma_sweep', magma_sweep)] if VOLC else []) + [('attack1', attack1), ('attack2', attack2), ('attack3', attack3)]:
    clip(nm, fn)
