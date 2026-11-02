import json,subprocess,os
from PIL import Image,ImageDraw
ATT=json.load(open('/tmp/l3/www/proto3d/models/beth/loot/gear/gear_attach.json'))['heroes']
FAM={'darius':'plate','orin':'plate','rook':'scale','finn':'chain','elira':'chain','wren':'leather','rowan':'cloth','talia':'cloth'}
FULL=["helm","cloak","chest","belt","shoulder_L","shoulder_R","glove_L","glove_R","leg_L","leg_R","boot_L","boot_R"]
def pieces(h): return [p for p in FULL if not (FAM[h]=='cloth' and p.split('_')[0] in ('chest','leg'))]
def job(h,r,shots):
    j={"hero":h,"family":FAM[h],"rarity":r,"weapon":"x","weapon2":"","shield":"","shots":shots,"slots":[],
       "weapon_mesh":f"res://equipment/meshes/weapons/{ATT[h]['weapon_family']}_{r}.glb","fitted":{"dir":"res://fitted","pieces":pieces(h)}}
    if h=='darius': j["rig"]="res://heroes/darius_voxel_noweapon.glb"
    return j
def run(J,name):
    p=f'/tmp/l3w/{name}.json'; json.dump(J,open(p,'w'))
    subprocess.run(f'cd /tmp/l3g && timeout 700 godot --headless --path . --import >/dev/null 2>&1; VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json timeout 770 xvfb-run -a godot --path . -- {p} > /tmp/l3w/{name}.log 2>&1',shell=True)
def sheet(F,out,cols,labels,scale=0.6):
    ims=[Image.open(f).convert('RGB') if os.path.exists(f) else Image.new('RGB',(420,560),(255,0,255)) for f in F]
    w,h=int(420*scale),int(560*scale); rows=(len(ims)+cols-1)//cols; S=Image.new('RGB',(w*cols,h*rows)); d=ImageDraw.Draw(S)
    for i,im in enumerate(ims):
        x,y=(i%cols)*w,(i//cols)*h; S.paste(im.resize((w,h)),(x,y)); d.text((x+3,y+3),labels[i],fill=(0,0,0))
    S.save(out)
H=['darius','orin','rook','finn','elira','wren','rowan','talia']
K=['front','back','side','helm_front','helm_34','walk1','walk2','attack1','attack2']
def full(h,outdir,rs=('rare','legendary','masterwork')):
    os.makedirs(outdir+'/raw',exist_ok=True); ac='attack' if h=='darius' else 'attack1'; J=[]
    for r in rs:
        b=f'{outdir}/raw/{h}_{r}_'
        S=[dict(clip='rest',yaw=0,out=b+'front.png'),dict(clip='rest',yaw=180,out=b+'back.png'),dict(clip='rest',yaw=90,out=b+'side.png'),
           dict(clip='rest',yaw=0,helm=2.2,out=b+'helm_front.png'),dict(clip='rest',yaw=35,helm=2.2,out=b+'helm_34.png'),
           dict(clip='walk',t=0.25,yaw=60,out=b+'walk1.png'),dict(clip='walk',t=0.75,yaw=-60,out=b+'walk2.png'),
           dict(clip=ac,t=0.35,yaw=40,out=b+'attack1.png'),dict(clip=ac,t=0.6,yaw=-40,out=b+'attack2.png')]
        J.append(job(h,r,S))
    run(J,'j_'+h)
    F=[f'{outdir}/raw/{h}_{r}_{k}.png' for r in rs for k in K]; sheet(F,f'{outdir}/{h}_sheet.png',9,[f'{r} {k}' for r in rs for k in K],0.4)
def overview(O,out):
    F=[];L=[]
    for h in H:
        for r in ('legendary','masterwork'):
            for k in ('front','side','helm_front','helm_34'):
                F.append(f'{O}{h}/raw/{h}_{r}_{k}.png');L.append(f'{h} {r[0]} {k}')
    sheet(F,out,8,L,0.45)
