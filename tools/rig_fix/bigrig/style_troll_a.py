# Frost Troll A "Krag": rocky stone club. Heavy, committed, big wind-ups, torso carries the club, club head lands on the ground.
# Hit frames = Godot BOSS_PATTERNS tele: attack1 winterhammer 1.1 s, attack2 glacierbreaker 1.5 s, attack3 brotherswrath 1.3 s.
def rest():
    r = body(lean=8); armfk(r, 'L', 8, 4, 15); armfk(r, 'R', 25, 6, 35); return r
def attack1():   # Winterhammer: overhead one-hand smash over the right shoulder into the ground in front
    key(0, rot=rest())
    r = body(lean=-14, twist=-30, side=6, head=-6); armfk(r, 'R', 170, 30, 75, yaw=-15); armfk(r, 'L', 40, 20, 40); key(0.75, hips=(0, 0.02, 0.01), rot=r, ik={'legR': foot('R', 0.04)}, jaw=6)
    key(0.88, hips=(0, 0.025, 0.015), rot=r, ik={'legR': foot('R', 0.04)}, jaw=8)
    r = body(lean=34, twist=12, side=-4, head=10); armfk(r, 'R', 70, 18, 10, yaw=10); armfk(r, 'L', -25, 25, 30); key(1.1, hips=(0, -0.05, -0.09), rot=r, ik={'legR': foot('R', 0.04), 'legL': foot('L', -0.05)}, jaw=18)
    key(1.35, hips=(0, -0.05, -0.095), rot=r, ik={'legR': foot('R', 0.04), 'legL': foot('L', -0.05)}, jaw=8)
    end = key(2.0, rot=rest()); CONTACT['attack1'] = (1.1, 'club'); return end
def attack2():   # Glacier Breaker: two-step charge-up, then a huge straight-down cleave that drags a line forward
    key(0, rot=rest())
    r = body(lean=-4, twist=-18); armfk(r, 'R', 120, 15, 60); armfk(r, 'L', 30, 15, 30); key(0.55, hips=(0, 0, -0.02), rot=r, jaw=4)
    r = body(lean=-20, twist=-8, head=-10); armfk(r, 'R', 185, 12, 80); armfk(r, 'L', 120, 20, 60); key(1.2, hips=(0, 0.03, 0.02), rot=r, ik={'legL': foot('L', -0.03, 0.03)}, jaw=10)
    r = body(lean=40, twist=4, head=12); armfk(r, 'R', 75, 8, 6); armfk(r, 'L', 30, 25, 30); key(1.5, hips=(0, -0.07, -0.11), rot=r, ik={'legL': foot('L', -0.09)}, jaw=22)
    key(1.8, hips=(0, -0.07, -0.115), rot=r, ik={'legL': foot('L', -0.09)}, jaw=10)
    end = key(2.45, rot=rest(), ik={'legL': foot('L', -0.04)}); CONTACT['attack2'] = (1.5, 'club'); return end
def attack3():   # Brother's Wrath: full-body horizontal ring sweep at knee height, right to left, torso fully wound
    key(0, rot=rest())
    r = body(lean=10, twist=-50, side=5); armfk(r, 'R', 30, 70, 30, yaw=-45); armfk(r, 'L', 30, 20, 40); key(0.9, hips=(0, 0, -0.06), rot=r, jaw=6)
    r = body(lean=30, twist=10); armfk(r, 'R', 40, 30, 15, yaw=10); armfk(r, 'L', -10, 30, 30); key(1.3, hips=(0, -0.02, -0.09), rot=r, jaw=20)
    r = body(lean=18, twist=55, side=-5); armfk(r, 'R', 60, 55, 20, yaw=55); armfk(r, 'L', -25, 30, 30); key(1.6, hips=(0, -0.02, -0.08), rot=r, jaw=10)
    end = key(2.3, rot=rest()); CONTACT['attack3'] = (1.3, 'club'); return end
# fresh rig -> fresh loco: heavy rolling lumber, wide sway, knuckles swinging low
loco('walk', T=1.4, v=0.16, duty=0.64, lift=0.05, bob=0.02, lean=10, swing=22, sway=1.0, yaw=9, elbow=28)
loco('run', T=0.85, v=0.40, duty=0.45, lift=0.10, bob=0.04, lean=20, swing=34, sway=0.9, yaw=10, elbow=50)
def idle():
    n = int(3.6*FPS)
    for i in range(n+1):
        p = i/n; b = math.sin(2*math.pi*p); r = body(lean=8+2.5*b, side=1.5*b, head=-2*b); armfk(r, 'L', 8+3*b, 4, 15+3*b); armfk(r, 'R', 25+2*b, 6, 35)
        key(i/FPS, hips=(0, 0, -0.006-0.005*b), rot=r)
    return n+1
def hit():
    key(0, rot=rest()); r = body(lean=-14, twist=10, head=-18); armfk(r, 'R', 15, 20, 45); armfk(r, 'L', -5, 25, 25); key(0.15, hips=(0, 0.03, -0.015), rot=r); return key(0.55, rot=rest())
def death():
    key(0, rot=rest()); r = body(lean=-15, twist=15, head=-20); armfk(r, 'R', 40, 30, 30); armfk(r, 'L', 40, 30, 30); key(0.5, hips=(0, 0.02, -0.03), rot=r, jaw=20)
    r = body(lean=75, twist=-10); armfk(r, 'R', 85, 25, 10); armfk(r, 'L', 85, 25, 10); key(1.5, hips=(0, -0.12, -0.34), rot=r); return key(1.7, hips=(0, -0.12, -0.34), rot=r)
def skill():   # chest-beat roar
    key(0, rot=rest()); r = body(lean=-16, head=-24); armfk(r, 'R', 70, 40, 100); armfk(r, 'L', 70, 40, 100); key(0.5, rot=r, jaw=30)
    r2 = body(lean=-18, head=-26); armfk(r2, 'R', 60, 30, 110); armfk(r2, 'L', 60, 30, 110); key(0.8, rot=r2, jaw=32); key(1.1, rot=r, jaw=30); return key(1.6, rot=rest())
for nm, fn in [('idle', idle), ('hit', hit), ('death', death), ('skill', skill)]: clip(nm, fn)
for nm, fn in [('attack1', attack1), ('attack2', attack2), ('attack3', attack3)]: clip(nm, fn)
