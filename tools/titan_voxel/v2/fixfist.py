import sys,os,math
_a=sys.argv[sys.argv.index('--')+1:]; IN,OUT=_a
sys.argv=sys.argv[:sys.argv.index('--')+1]+[IN,OUT,'x']
os.environ['POLE']='0'
exec(open('/workspace/titan2/post.py').read().split("rep=json.load")[0])
clip=os.environ.get('CLIP','wb_ritual_fissure_release'); fc=int(os.environ.get('FC','27')); HOLD=3; G=-0.025/M2G
SIDES=os.environ.get('SIDES','R')
for s in SIDES:
    act=bpy.data.actions[clip]; T.animation_data.action=act; f0,f1=[int(round(x)) for x in act.frame_range]
    W0={}
    for f in range(f0,f1+1): sc.frame_set(f); W0[f]=getW()
    hs=[rmin(W0[f],'arm_'+s)-G for f in range(fc,fc+HOLD+1)]; lift=-min(hs)
    print('FF lift units',lift,'m',lift*M2G)
    def w(f):
        k=f-fc
        if 0<=k<=HOLD: return 1.0
        if -6<=k<0: return 1-((-k)/6)**2
        if HOLD<k<=HOLD+10: return 1-sstep((k-HOLD)/10)
        return 0.0
    new=bpy.data.actions.new(clip+'_n'); new.use_fake_user=True; T.animation_data.action=new
    res=[]
    for f in range(f0,f1+1):
        W={k:m.copy() for k,m in W0[f].items()}
        if w(f)>0:
            for it in range(4):
                h=rmin(W,'arm_'+s)-G if fc<=f<=fc+HOLD else -lift*w(f)
                if fc<=f<=fc+HOLD:
                    if abs(h)<0.0003: break
                    d=-h
                else:
                    d=lift*w(f); 
                ha=ARMS[s][2]; two_bone(W,*ARMS[s],W[ha].translation+Vector((0,0,d)),keep_rot=W[ha].to_3x3())
                if not(fc<=f<=fc+HOLD): break
        apply(W,f)
        if w(f)>0: res.append((f,round(rmin(W,'arm_'+s)*M2G,3),n_in(W)))
    print('FF',res)
    old=bpy.data.actions[clip]; old.name='x__'; new.name=clip; bpy.data.actions.remove(old)

    
T.animation_data.action=bpy.data.actions['wb_idle']; bpy.ops.wm.save_as_mainfile(filepath=OUT)
