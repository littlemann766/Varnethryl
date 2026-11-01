# Medieval inventory UI art (pixel-art, 2x upscaled nearest) + rarity borders + loot-beam strips + 2D icons for non-mesh items.
import os,sys,json,math,random
from PIL import Image,ImageDraw,ImageFilter
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from edata import *
U="/tmp/l3/www/proto3d/models/beth/equipment/ui"; I="/tmp/l3/www/proto3d/models/beth/equipment/icons"; os.makedirs(U,exist_ok=True); os.makedirs(I,exist_ok=True)
def hexc(h): return tuple(int(h[i:i+2],16) for i in (1,3,5))
def mix(a,b,t): return tuple(int(a[i]*(1-t)+b[i]*t) for i in range(3))
def sh(c,k): return tuple(max(0,min(255,int(x*k))) for x in c)
BORDER={ # frame metal, accent, inner glow
 "uncommon":((96,96,100),(70,66,60),None),"common":((92,100,84),(62,140,70),None),"rare":((52,56,66),(190,150,70),(60,120,230)),
 "epic":((56,52,66),(235,190,80),(160,80,235)),"legendary":((70,58,40),(255,210,90),(255,190,60)),"masterwork":((40,26,26),(230,70,30),(255,90,20))}
def border(r,S=64):
    m,acc,glow=BORDER[r]; i=RARITIES.index(r); im=Image.new("RGBA",(S,S),(0,0,0,0)); d=ImageDraw.Draw(im); rnd=random.Random(i)
    for k in range(4): d.rectangle([k,k,S-1-k,S-1-k],outline=sh(m,[0.6,1.15,1.0,0.7][k])+(255,))
    if glow:
        for k in range(3): d.rectangle([4+k,4+k,S-5-k,S-5-k],outline=glow+(int(150-k*45),))
    # corners
    cs=6+i
    for (x,y) in [(0,0),(S-cs,0),(0,S-cs),(S-cs,S-cs)]:
        d.rectangle([x,y,x+cs-1,y+cs-1],fill=sh(acc,0.9)+(255,),outline=sh(acc,0.55)+(255,))
        d.point((x+cs//2,y+cs//2),fill=sh(acc,1.3)+(255,))
        if i>=4: d.point((x+cs//2-1,y+cs//2),fill=(255,255,240,255))
    if i>=1:  # rivets along edges
        for t in range(cs+4,S-cs-3,8):
            for (x,y) in [(t,1),(t,S-2),(1,t),(S-2,t)]: d.point((x,y),fill=sh(acc if i>=2 else m,1.4)+(255,))
    if i>=3:  # gilt mid studs
        for (x,y) in [(S//2,0),(S//2,S-3),(0,S//2),(S-3,S//2)]: d.rectangle([x-1,y,x+1,y+2],fill=acc+(255,))
    if i==4:  # filigree
        for t in range(cs,S-cs,3): d.point((t,3),fill=acc+(255,)); d.point((t,S-4),fill=acc+(255,)); d.point((3,t),fill=acc+(255,)); d.point((S-4,t),fill=acc+(255,))
    if i==5:  # molten cracks
        for _ in range(14):
            x,y=rnd.choice([(rnd.randrange(S),rnd.randrange(4)),(rnd.randrange(S),S-1-rnd.randrange(4)),(rnd.randrange(4),rnd.randrange(S)),(S-1-rnd.randrange(4),rnd.randrange(S))])
            d.point((x,y),fill=(255,150,40,255))
    return im.resize((S*2,S*2),Image.NEAREST)
def bg(r,S=64):
    m,acc,glow=BORDER[r]; base=mix((34,28,24),glow or m,0.18); im=Image.new("RGBA",(S,S),base+(255,)); d=ImageDraw.Draw(im); rnd=random.Random(3)
    for y in range(S):
        for x in range(S):
            dd=math.hypot(x-S/2,y-S/2)/(S/2); c=sh(base,1.25-0.45*dd+rnd.uniform(-0.04,0.04)); im.putpixel((x,y),c+(255,))
    return im.resize((S*2,S*2),Image.NEAREST)
for r in RARITIES:
    border(r).save(f"{U}/border_{r}.png"); bg(r).save(f"{U}/tile_bg_{r}.png")
    # loot beam strip (32x256, additive): colour core fading up
    c=hexc(RCOL[r]); im=Image.new("RGBA",(32,256),(0,0,0,0))
    for y in range(256):
        for x in range(32):
            a=max(0,1-abs(x-15.5)/16)**2*(1-y/256)**0.8; im.putpixel((x,255-y),mix(c,(255,255,255),0.35*max(0,1-abs(x-15.5)/4))+(int(255*a),))
    im.save(f"{U}/beam_{r}.png")
# slot frames with silhouettes (14 slots)
GLYPH={"helmet":[(4,3,11,9),(3,7,12,12)],"chest":[(3,3,12,13)],"shoulders":[(1,4,6,8),(9,4,14,8)],"gloves":[(5,3,10,12)],"legs":[(4,2,7,14),(8,2,11,14)],"boots":[(4,2,7,11),(3,11,8,13),(8,2,11,11),(8,11,13,13)],
 "belt":[(2,7,13,9),(7,6,9,10)],"cloak":[(4,2,11,3),(3,3,12,14)],"amulet":[(7,8,9,11)],"ring1":[(5,6,10,11)],"ring2":[(5,6,10,11)],"main_hand":[(7,1,8,11),(5,11,10,12),(7,12,8,14)],"off_hand":[(3,2,12,9),(4,9,11,12),(6,12,9,14)],"class_item":[(5,3,10,13)]}
for s,boxes in GLYPH.items():
    S=64; im=Image.new("RGBA",(S,S),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rectangle([0,0,S-1,S-1],fill=(38,32,28,235)); 
    for k in range(3): d.rectangle([k,k,S-1-k,S-1-k],outline=sh((92,80,64),[0.6,1.1,0.8][k])+(255,))
    for (x0,y0,x1,y1) in boxes: d.rectangle([8+x0*3,8+y0*3,8+x1*3,8+y1*3],fill=(70,62,54,200))
    if s in("ring1","ring2","amulet"): d.ellipse([8+5*3,8+6*3,8+10*3,8+11*3],outline=(90,80,68,220),width=3)
    for (x,y) in [(3,3),(S-4,3),(3,S-4),(S-4,S-4)]: d.point((x,y),fill=(160,140,110,255))
    im.resize((128,128),Image.NEAREST).save(f"{U}/slot_{s}.png")
# panel (paper doll backdrop) + tooltip frame
W,H=180,240; im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im); rnd=random.Random(9)
for y in range(H):
    for x in range(W):
        c=sh((58,40,28),0.9+0.15*math.sin(y*0.7+x*0.05)+rnd.uniform(-0.05,0.05)); im.putpixel((x,y),c+(250,))
for k in range(5): d.rectangle([k,k,W-1-k,H-1-k],outline=sh((110,92,70),[0.5,1.0,1.2,0.9,0.6][k])+(255,))
for (x,y) in [(6,6),(W-10,6),(6,H-10),(W-10,H-10)]: d.rectangle([x,y,x+3,y+3],fill=(170,140,80,255))
im.resize((W*2,H*2),Image.NEAREST).save(f"{U}/panel_equipment.png")
W,H=120,70; im=Image.new("RGBA",(W,H),(22,18,16,240)); d=ImageDraw.Draw(im)
for k in range(3): d.rectangle([k,k,W-1-k,H-1-k],outline=sh((120,100,70),[0.6,1.1,0.7][k])+(255,))
im.resize((W*2,H*2),Image.NEAREST).save(f"{U}/tooltip_frame.png")
json.dump({"_note":"UI art for Lucky (art only; UI code is Lucky's). All pixel art at 2x, nearest filtering. 9-slice margins in px at 2x.","rarity":{r:{"border":f"res://equipment/ui/border_{r}.png","tile_bg":f"res://equipment/ui/tile_bg_{r}.png","beam":f"res://equipment/ui/beam_{r}.png","color":RCOL[r],"name_color":RCOL[r]} for r in RARITIES},
 "slots":{s:f"res://equipment/ui/slot_{s}.png" for s in GLYPH},"panel":{"file":"res://equipment/ui/panel_equipment.png","nine_slice":[16,16,16,16]},"tooltip":{"file":"res://equipment/ui/tooltip_frame.png","nine_slice":[8,8,8,8]},
 "border_nine_slice":[14,14,14,14],"icon_size":128,"paperdoll_layout_px_at_2x":{"helmet":[146,24],"amulet":[230,40],"cloak":[62,40],"shoulders":[62,120],"chest":[146,120],"gloves":[62,200],"belt":[146,200],"legs":[146,280],"boots":[146,360],"ring1":[230,200],"ring2":[230,280],"main_hand":[62,360],"off_hand":[230,360],"class_item":[230,120]}},
 open(f"{U}/ui_theme.json","w"),indent=1)
print("ui ok")
