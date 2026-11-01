# Equipment v1 polish 5: 3D pickup (world drop) models for artifacts, gems, runes, key materials.
# Grid 24^3, Z up, pivot = bottom centre (rests on the ground). VS=0.012 m -> ~0.29 m drop, readable at loot-beam distance.
import numpy as np,os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from vox import V
N=24; VS=0.012; C=N/2-0.5
GEM={"ruby":(0.78,0.08,0.12),"sapphire":(0.12,0.25,0.80),"emerald":(0.10,0.62,0.28),"amethyst":(0.55,0.22,0.75),"diamond":(0.88,0.93,0.98),
 "garnet":(0.52,0.06,0.10),"obsidian":(0.10,0.08,0.12),"topaz":(0.95,0.62,0.18),"moonstone":(0.80,0.84,0.92),"bloodstone":(0.20,0.34,0.22),
 "frost_crystal":(0.62,0.86,0.98),"void_crystal":(0.30,0.08,0.45)}
RUNE={"flame":(1.0,0.45,0.10),"swiftness":(0.55,0.95,0.70),"protection":(0.45,0.70,1.0),"rebirth":(1.0,0.85,0.40),"destruction":(0.90,0.15,0.10),
 "echoes":(0.70,0.55,1.0),"hunt":(0.55,0.85,0.30),"guardian":(0.85,0.85,0.95)}
METAL={"iron":(0.42,0.40,0.38),"steel":(0.60,0.62,0.66),"silver":(0.80,0.82,0.85),"gold":(0.86,0.66,0.26),"mithril":(0.70,0.85,0.92),
 "adamantite":(0.30,0.45,0.40),"darksteel":(0.16,0.16,0.20),"starsteel":(0.55,0.60,0.85),"dragonsteel":(0.55,0.16,0.10),"voidsteel":(0.22,0.10,0.30)}
GOLD=(0.86,0.66,0.26); STONE=(0.42,0.40,0.38); DSTONE=(0.28,0.27,0.27); BONE=(0.86,0.82,0.70); WOOD=(0.36,0.22,0.12)
def X(): return np.indices((N,N,N))
def shade(rgb,f): return tuple(min(1,c*f) for c in rgb)
def gem(v,col,r=7,z0=1,glow=True):
    x,y,z=X(); cz=z0+r*1.3
    m=(abs(x-C)+abs(y-C))*1.0+abs(z-cz)*0.75<=r; m&=(z>=z0)
    hi=m&(z>cz)&((x+y+z)%3==0); v.g[m]=v.c(col); v.g[hi]=v.c(shade(col,1.35),1 if glow else 0)
    crown=m&(abs(z-cz)<0.6); v.g[crown]=v.c(shade(col,1.6),1)
def ingot(v,col):
    for k in range(5): v.box(4+k//2,19-k//2,7+k//2,16-k//2,1+k,1+k,v.c(shade(col,1-0.05*k)))
    v.box(8,15,9,14,6,6,v.c(shade(col,1.25)));  v.box(10,13,11,12,6,6,v.c(shade(col,0.7)))   # stamp
def rune(v,col):
    v.box(6,17,9,14,1,2,v.c(DSTONE)); x,y,z=X()
    m=((x-C)**2/36+(z-11)**2/100<=1)&(y>=9)&(y<=14)&(z>=1); v.g[m]=v.c(STONE)
    g=v.c(col,1)
    for z_ in range(5,18): v.put(C,8,z_,g)
    v.line((8,8,14),(15,8,8),g); v.line((8,8,8),(15,8,14),g)
def orb(v,col,r=6,veins=None,setting=None):
    if setting: v.box(5,18,5,18,1,2,v.c(setting)); [v.box(5+i*12,6+i*12,5+j*12,6+j*12,3,7,v.c(setting)) for i in (0,1) for j in (0,1)]
    v.ball(C,C,r+3,r,v.c(col))
    if veins:
        x,y,z=X(); m=(v.g>0)&((x*3+y*5+z*7)%11==0)&(z>3); v.g[m]=v.c(veins,1)
def feather(v,col,tip):
    for z in range(1,22):
        w=max(1,int(5*np.sin(np.pi*min(1,(z+2)/22)))); xo=int(2*np.sin(z/6))
        v.box(int(C)-w+xo,int(C)+w+xo,11,12,z,z,v.c(col if z<16 else tip,1 if z>=16 else 0))
        v.put(C+xo,10,z,v.c(BONE))
def scale(v,col):
    x,y,z=X(); m=((x-C)**2+(z-10)**2<=64)&(z>=2)&(abs(y-C-((x-C)**2)/18)<=1); v.g[m]=v.c(col)
    v.g[m&((x+z)%4==0)]=v.c(shade(col,1.4)); v.g[m&(z<4)]=v.c(shade(col,0.6))
def shard(v,col,glow=1,n=3):
    rng=np.random.default_rng(len(str(col)))
    for k in range(n):
        a=np.array([C+rng.integers(-4,5),C+rng.integers(-4,5),1]); b=a+np.array([rng.integers(-4,5),rng.integers(-4,5),10+rng.integers(0,8)])
        v.line(tuple(a),tuple(b),v.c(col,glow),t=1)
    v.box(7,16,7,16,1,1,v.c(DSTONE)); x,y,z=X(); m=(v.g==v.c(col))&((x+y+z)%3==0); v.g[m]=v.c(shade(col,0.75))
def hide(v,col):
    x,y,z=X(); m=((x-C)**2/80+(y-C)**2/50<=1)&(z<=2+((x+y)%5==0)); v.g[m]=v.c(col); v.g[m&(z>2)]=v.c(shade(col,0.7))
    v.box(4,19,10,13,3,4,v.c(WOOD))  # tie
def fang(v,col):
    for z in range(1,20):
        r=max(0.6,3.5*(1-z/20)); xo=z*z/60
        x,y,zz=X(); m=((x-C-xo)**2+(y-C)**2<=r*r)&(zz==z); v.g[m]=v.c(col if z>3 else shade(col,0.7))
def vial(v,liq):
    v.ball(C,C,7,5.5,v.c(liq,1)); x,y,z=X(); v.g[(v.g>0)&((x+z)%4==0)]=v.c((0.80,0.88,0.88)); v.box(10,13,10,13,12,15,v.c((0.75,0.85,0.85))); v.box(10,13,10,13,16,17,v.c(WOOD))
def bone(v):
    v.box(4,19,10,13,3,5,v.c(BONE)); [v.ball(cx,cy,4,2.4,v.c(shade(BONE,0.95))) for cx in (4,19) for cy in (9.5,13.5)]
def pouch(v,dust):
    v.ball(C,C,6,6,v.c((0.40,0.28,0.18)),sq=(1,1,0.9)); v.box(9,14,9,14,11,13,v.c((0.30,0.20,0.12))); v.ball(C,C,15,2.5,v.c(dust,1))
def wisp(v,col):
    for z in range(2,22):
        r=4*np.sin(np.pi*z/22)+0.5; a=z/3
        v.ball(C+2*np.cos(a),C+2*np.sin(a),z,r,v.c(shade(col,0.8+0.02*z),1))
def ore(v,col,vein):
    v.ball(C,C,6,6,v.c(DSTONE),sq=(1.2,1,0.85)); x,y,z=X(); m=(v.g>0)&((x+2*y+3*z)%5==0); v.g[m]=v.c(vein,1)
def flame(v,col):
    v.box(7,16,7,16,1,3,v.c(DSTONE))
    for z in range(4,22): r=max(0.5,5*(1-(z-4)/18)**0.7); v.ball(C+np.sin(z/2),C,z,r,v.c(col if z<14 else shade(col,1.3),1))
def totem(v):
    v.box(8,15,8,15,1,18,v.c(WOOD)); v.box(6,17,9,14,14,15,v.c(BONE)); v.box(9,10,7,7,10,11,v.c((0.6,0.9,1.0),1)); v.box(13,14,7,7,10,11,v.c((0.6,0.9,1.0),1))
    v.box(7,16,7,16,19,20,v.c((0.90,0.95,1.0)))
def sigil(v):
    x,y,z=X(); r=np.sqrt((x-C)**2+(z-11)**2); m=(r<=8)&(r>=5.5)&(abs(y-C)<=1.5); v.g[m]=v.c(GOLD)
    v.box(8,15,10,13,15,20,v.c(GOLD)); v.box(9,14,9,9,16,19,v.c((0.7,0.08,0.1),1))
def eye(v):
    orb(v,(0.95,0.92,0.85),5,setting=GOLD); x,y,z=X(); m=(v.g>0)&(y<C-2)&((x-C)**2+(z-8)**2<=6); v.g[m]=v.c((0.9,0.55,0.1),1)
    v.g[(v.g>0)&(y<C-3)&((x-C)**2+(z-8)**2<=1.5)]=v.c((0.05,0.03,0.03))
ART={"ancient_dragon_scale":lambda v:scale(v,(0.55,0.16,0.10)),"heart_of_the_titan":lambda v:orb(v,(0.45,0.12,0.10),6,veins=(1.0,0.5,0.15)),
 "phoenix_feather":lambda v:feather(v,(0.95,0.35,0.08),(1.0,0.85,0.3)),"eye_of_balthrix":eye,"frost_troll_totem":totem,
 "celestial_fragment":lambda v:shard(v,(0.85,0.90,1.0)),"voidstone":lambda v:orb(v,(0.10,0.06,0.14),6,veins=(0.6,0.2,0.9)),"kings_sigil":sigil}
MAT={**{k:(lambda c:lambda v:ingot(v,c))(c) for k,c in METAL.items()},
 "dragon_scale":lambda v:scale(v,(0.60,0.18,0.10)),"basilisk_scale":lambda v:scale(v,(0.30,0.45,0.22)),"phoenix_feather":lambda v:feather(v,(0.95,0.35,0.08),(1.0,0.85,0.3)),
 "troll_hide":lambda v:hide(v,(0.36,0.42,0.34)),"hydra_fang":lambda v:fang(v,(0.88,0.86,0.74)),"titan_core":lambda v:orb(v,(0.40,0.36,0.32),5,veins=(1.0,0.55,0.15)),
 "serpent_venom":lambda v:vial(v,(0.35,0.85,0.20)),"ancient_bone":bone,"demon_heart":lambda v:orb(v,(0.40,0.04,0.06),5,veins=(1.0,0.2,0.1)),
 "frost_crystal":lambda v:shard(v,(0.62,0.86,0.98)),"arcane_dust":lambda v:pouch(v,(0.65,0.45,1.0)),"soul_fragment":lambda v:wisp(v,(0.55,0.85,0.95)),
 "celestial_essence":lambda v:vial(v,(0.95,0.92,0.70)),"void_essence":lambda v:vial(v,(0.45,0.12,0.70)),"ancient_rune":lambda v:rune(v,(0.85,0.75,0.45)),
 "enchanted_crystal":lambda v:shard(v,(0.70,0.50,1.0)),"elemental_core":lambda v:orb(v,(0.25,0.25,0.30),5,veins=(0.4,0.9,1.0)),
 "molten_ore":lambda v:ore(v,(0.3,0.2,0.2),(1.0,0.45,0.08)),"frozen_heart":lambda v:orb(v,(0.55,0.80,0.95),5,veins=(0.9,0.98,1.0)),"eternal_flame":lambda v:flame(v,(1.0,0.45,0.08)),
 "hydra_heart":lambda v:orb(v,(0.20,0.40,0.22),5,veins=(0.6,1.0,0.3)),"dragon_core":lambda v:orb(v,(0.35,0.10,0.06),5,veins=(1.0,0.6,0.1)),
 "abyssal_scale":lambda v:scale(v,(0.10,0.14,0.30)),"forge_shard":lambda v:shard(v,(1.0,0.55,0.15))}
def all_items():
    for k,f in ART.items(): yield "app_artifact_"+k,f
    for k,c in GEM.items(): yield "app_gem_"+k,(lambda c:lambda v:gem(v,c,glow=k!="obsidian"))(c)
    for k,c in RUNE.items(): yield "app_rune_"+k,(lambda c:lambda v:rune(v,c))(c)
    for k,f in MAT.items(): yield "app_mat_"+k,f
class PV(V):
    # no emissive faces on pickups: emission blows out to white in Blender and Godot bloom; colour carries the identity (loot beam supplies glow)
    def c(s,rgb,glow=0): return V.c(s,tuple(min(1,x*(1.15 if glow else 1)) for x in rgb),0)
def build(f):
    v=PV(N); f(v); return v,VS,(C,C,0)
