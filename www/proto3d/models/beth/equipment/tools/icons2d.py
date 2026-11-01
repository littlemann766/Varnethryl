import os,sys,json,math,random
from PIL import Image,ImageDraw
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from edata import *
E_="/tmp/l3/www/proto3d/models/beth/equipment"; I=E_+"/icons"
apps=json.load(open(E_+"/appearances.json"))["appearances"]; defs=json.load(open(E_+"/data/item_definitions.json"))["definitions"]
GC={"ruby":(200,30,40),"sapphire":(40,80,210),"emerald":(30,170,80),"amethyst":(150,70,200),"diamond":(225,235,245),"garnet":(140,20,40),"obsidian":(40,36,48),"topaz":(240,170,40),"moonstone":(190,200,225),"bloodstone":(90,30,30),"frost_crystal":(150,220,250),"void_crystal":(80,20,120)}
def sh(c,k): return tuple(max(0,min(255,int(x*k))) for x in c)
def canvas(): im=Image.new("RGBA",(32,32),(0,0,0,0)); return im,ImageDraw.Draw(im)
def out(im,name): im.resize((128,128),Image.NEAREST).save(f"{I}/{name}.png")
def gem(c,name):
    im,d=canvas(); pts=[(16,5),(25,12),(16,27),(7,12)]; d.polygon(pts,fill=c+(255,)); d.polygon([(16,5),(25,12),(16,14)],fill=sh(c,1.35)+(255,)); d.polygon([(7,12),(16,14),(16,27)],fill=sh(c,0.65)+(255,))
    d.line(pts+[pts[0]],fill=sh(c,0.4)+(255,)); d.point((13,9),fill=(255,255,255,255)); out(im,name)
def ingot(c,name):
    im,d=canvas(); d.polygon([(5,21),(10,13),(27,13),(22,21)],fill=sh(c,1.2)+(255,)); d.polygon([(5,21),(22,21),(22,26),(5,26)],fill=c+(255,)); d.polygon([(22,21),(27,13),(27,18),(22,26)],fill=sh(c,0.7)+(255,)); out(im,name)
def blob(c,name,kind):
    im,d=canvas(); rnd=random.Random(name)
    if kind=="hide": d.polygon([(6,8),(14,5),(24,7),(27,16),(23,26),(12,27),(5,20)],fill=c+(255,)); [d.point((rnd.randrange(8,24),rnd.randrange(8,24)),fill=sh(c,0.7)+(255,)) for _ in range(30)]
    elif kind=="scale": 
        for y in range(3):
            for x in range(3): d.ellipse([6+x*7,6+y*7,14+x*7,14+y*7],fill=sh(c,1.1-0.1*y)+(255,),outline=sh(c,0.6)+(255,))
    elif kind=="dust": d.ellipse([7,14,25,26],fill=sh(c,0.8)+(255,)); [d.point((rnd.randrange(8,24),rnd.randrange(8,24)),fill=sh(c,1.5)+(255,)) for _ in range(40)]
    elif kind=="orb": d.ellipse([8,8,24,24],fill=c+(255,)); d.ellipse([11,10,16,15],fill=sh(c,1.6)+(255,))
    elif kind=="bone": d.line([(8,24),(24,8)],fill=(225,215,190,255),width=4); [d.ellipse([x-3,y-3,x+3,y+3],fill=(235,225,200,255)) for x,y in [(7,25),(25,7),(9,23),(23,9)]]
    elif kind=="feather": d.line([(8,26),(24,6)],fill=sh(c,0.6)+(255,),width=1); d.polygon([(9,24),(14,10),(24,6),(19,20)],fill=c+(255,))
    elif kind=="flask": d.rectangle([14,5,18,11],fill=(180,170,150,255)); d.ellipse([8,10,24,27],fill=c+(255,),outline=(220,220,220,255))
    else: d.rectangle([8,8,24,24],fill=c+(255,))
    out(im,name)
def tablet(glyph_c,name,seed):
    im,d=canvas(); d.rounded_rectangle([7,4,25,28],4,fill=(110,104,98,255),outline=(60,56,52,255)); rnd=random.Random(seed)
    x,y=16,8
    for _ in range(7): nx,ny=x+rnd.choice([-4,0,4]),y+3; d.line([(x,y),(nx,ny)],fill=glyph_c+(255,),width=2); x,y=max(10,min(22,nx)),ny
    out(im,name)
def trinket(c,name,seed):
    im,d=canvas(); rnd=random.Random(seed); k=seed%4
    if k==0: d.ellipse([7,7,25,25],fill=(180,150,80,255),outline=(90,70,40,255)); d.ellipse([12,12,20,20],fill=c+(255,))
    elif k==1: d.polygon([(16,4),(26,16),(16,28),(6,16)],fill=(150,130,90,255)); d.polygon([(16,9),(21,16),(16,23),(11,16)],fill=c+(255,))
    elif k==2: d.rectangle([9,6,23,26],fill=(90,60,40,255),outline=(170,140,80,255)); d.ellipse([12,11,20,19],fill=c+(255,))
    else: d.ellipse([9,4,23,28],fill=c+(255,),outline=(200,180,120,255)); d.line([(16,6),(16,26)],fill=sh(c,1.5)+(255,))
    out(im,name)
MATC={"iron":(120,120,125),"steel":(160,165,175),"silver":(210,215,225),"gold":(235,190,70),"mithril":(170,210,235),"adamantite":(90,140,110),"darksteel":(55,55,65),"starsteel":(200,200,255),"dragonsteel":(170,50,40),"voidsteel":(70,30,100)}
n=0
for d in defs:
    a=d["appearanceId"]; e=apps[a]; nm=os.path.basename(e["icon"])[:-4]
    if e["kind"]!="icon_only" and not (d["slot"]=="off_hand" and "focus" in d["itemId"]): continue
    if os.path.exists(f"{I}/{nm}.png"): continue
    i=d["itemId"]; c=tuple(int(x*255) for x in [(0.5,0.5,0.5)][0])
    if d["category"]=="gem": gem(GC[i.split("_",1)[1].rsplit("_",1)[0]],nm)
    elif d["category"]=="rune": tablet({"flame":(255,120,30),"swiftness":(120,230,200),"protection":(120,170,255),"rebirth":(255,230,120),"destruction":(220,40,40),"echoes":(190,120,255),"hunt":(140,200,80),"guardian":(230,230,230)}[i[5:]],nm,len(i))
    elif d["category"]=="material":
        m=i.replace("mat_","").replace("legacy_","")
        if m in MATC: ingot(MATC[m],nm)
        elif any(k in m for k in("hide","pelt","leather")): blob((140,95,60),nm,"hide")
        elif "scale" in m: blob((80,140,110) if "basilisk" in m else (150,40,40) if "dragon" in m else (60,40,90),nm,"scale")
        elif "feather" in m: blob((240,110,30),nm,"feather")
        elif "bone" in m or "tusk" in m: blob(None,nm,"bone")
        elif any(k in m for k in("dust","essence","fragment","rune","ember","ash")): blob((180,160,230) if "arcane" in m else (240,220,140) if "celestial" in m else (130,60,180) if "void" in m else (120,200,230),nm,"dust")
        elif any(k in m for k in("venom",)): blob((90,190,60),nm,"flask")
        else: blob((230,120,40) if any(k in m for k in("flame","molten","core","magma","heart")) else (150,210,240),nm,"orb")
    elif d["category"]=="consumable": blob((200,40,40) if "heal" in i or "potion" in i else (140,120,90),nm,"flask")
    else: trinket(((200,60,60),(60,120,220),(80,200,120),(220,180,60),(170,90,220))[len(i)%5],nm,len(i)+sum(map(ord,i)))
    n+=1
print("2d icons",n)
