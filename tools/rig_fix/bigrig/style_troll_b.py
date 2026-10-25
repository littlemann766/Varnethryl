# Frost Troll B "Mog": ice mace. Stiff, sharp, snappy: short wind-ups, straight spine, abrupt stops, little follow-through.
# Hit frames = BOSS_PATTERNS tele: attack1 frostcrash 1.1 s (ring), attack2 avalanche lance 1.6 s (line thrust), attack3 brothersvengeance 1.2 s (cone chop).
def rest():
    r = body(lean=4); armfk(r, 'L', 6, 0, 12); armfk(r, 'R', 30, 4, 50); return r
# arms were re-bound lower, so the troll needs fresh locomotion too (stiff, upright, heavy)
loco('walk', T=1.25, v=0.17, duty=0.62, lift=0.06, bob=0.012, lean=6, swing=16, sway=0.4, yaw=5, elbow=22)
loco('run', T=0.78, v=0.44, duty=0.42, lift=0.11, bob=0.03, lean=14, swing=28, sway=0.5, yaw=7, elbow=45)
def idle():
    n = int(3.0*FPS)
    for i in range(n+1):
        p = i/n; b = math.sin(2*math.pi*p); r = body(lean=4+1.5*b, head=-1*b); armfk(r, 'L', 4+2*b, 0, 12+2*b); armfk(r, 'R', 30+2*b, 4, 50)
        key(i/FPS, hips=(0, 0, -0.004-0.003*b), rot=r)
    return n+1
clip('idle', idle)
def attack1():   # Frost Crash: snap the mace straight up, hard vertical spike into the ice (ring)
    key(0, rot=rest())
    r = body(lean=-6); armfk(r, 'R', 175, 5, 40); armfk(r, 'L', 20, 15, 20); key(0.5, hips=(0, 0, 0.01), rot=r, jaw=6)
    key(0.85, hips=(0, 0, 0.012), rot=r, jaw=6)
    r = body(lean=30, head=8); armfk(r, 'R', 62, 4, 0); armfk(r, 'L', -10, 15, 20); key(1.1, hips=(0, -0.03, -0.07), rot=r, ik={'legR': foot('R', -0.04)}, jaw=16, wrist=WR)
    key(1.4, hips=(0, -0.03, -0.07), rot=r, ik={'legR': foot('R', -0.04)}, jaw=6, wrist=WR)
    end = key(1.8, rot=rest()); CONTACT['attack1'] = (1.1, 'mace'); return end
def attack2():   # Avalanche Lance: coil back, then a straight stiff-armed lunge thrust, mace head driven forward
    key(0, rot=rest())
    r = body(lean=-2, twist=-30); armfk(r, 'R', 40, 25, 110, yaw=-20); armfk(r, 'L', 50, 15, 30); key(1.0, hips=(0, 0.03, -0.03), rot=r, ik={'legR': foot('R', 0.06)})
    key(1.35, hips=(0, 0.035, -0.035), rot=r, ik={'legR': foot('R', 0.06)}, jaw=6)
    r = body(lean=40, twist=18, head=12); armfk(r, 'R', 85, 8, 0, yaw=12); armfk(r, 'L', -30, 20, 20); key(1.6, hips=(0, -0.09, -0.06), rot=r, ik={'legL': foot('L', -0.12), 'legR': foot('R', 0.06)}, jaw=18, wrist=WR)
    key(1.85, hips=(0, -0.09, -0.06), rot=r, ik={'legL': foot('L', -0.12), 'legR': foot('R', 0.06)}, jaw=8, wrist=WR)
    end = key(2.3, rot=rest(), ik={'legL': foot('L', -0.06)}); CONTACT['attack2'] = (1.6, 'mace'); return end
def attack3():   # Brother's Vengeance: sharp diagonal chop high-right to low-left, then a stiff stop
    key(0, rot=rest())
    r = body(lean=-4, twist=-24); armfk(r, 'R', 150, 45, 60, yaw=-20); armfk(r, 'L', 25, 15, 25); key(0.9, hips=(0, 0.01, 0), rot=r, jaw=4)
    r = body(lean=34, twist=26, side=-4); armfk(r, 'R', 80, 10, 8, yaw=30); armfk(r, 'L', -15, 20, 25); key(1.2, hips=(0, -0.03, -0.05), rot=r, jaw=16, wrist=WR)
    key(1.3, hips=(0, -0.03, -0.052), rot=r, jaw=10, wrist=WR)
    end = key(1.8, rot=rest()); CONTACT['attack3'] = (1.2, 'mace'); return end
def hit():
    key(0, rot=rest()); r = body(lean=-10, head=-14); armfk(r, 'R', 10, 15, 40); armfk(r, 'L', -10, 15, 20); key(0.12, hips=(0, 0.02, -0.01), rot=r); return key(0.45, rot=rest())
def death():
    key(0, rot=rest()); r = body(lean=40); armfk(r, 'R', 30, 20, 30); armfk(r, 'L', 30, 20, 30); key(0.7, hips=(0, -0.03, -0.2), rot=r)
    r = body(lean=80); armfk(r, 'R', 80, 20, 10); armfk(r, 'L', 80, 20, 10); key(1.4, hips=(0, -0.12, -0.33), rot=r); return key(1.5, hips=(0, -0.12, -0.33), rot=r)
def skill():
    key(0, rot=rest()); r = body(lean=-12, head=-20); armfk(r, 'R', 120, 30, 30); armfk(r, 'L', 40, 50, 30); key(0.5, rot=r, jaw=28); key(1.1, rot=r, jaw=30); return key(1.45, rot=rest())
for nm, fn in [('attack1', attack1), ('attack2', attack2), ('attack3', attack3), ('hit', hit), ('death', death), ('skill', skill)]: clip(nm, fn)
