#!/usr/bin/env python3
# test 36: strict 30 fps keys (Lucian speed36 a12a359 removed the stretched 24 fps stopgap clips).
# test 34: every hero voxel GLB: clip durations match the test 33 originals (1b7e415) within 1 frame and keys are at 30 fps.
# Keys must be at 30 fps (or at the test 33 file's own key rate, e.g. the 24 fps villain/Rook-LOD1 clips retimed back to
# their test 33 length; a clip retimed to exactly its test 33 length may keep its own key spacing). Clips new since test 33 (jump/swim) only get the 30 fps check. Usage: python3 tests/clip_speed_check.py  (exit 0 = pass)
import json,struct,subprocess,glob,os,sys,io
def parse(b):
    l=struct.unpack('<I',b[12:16])[0]; j=json.loads(b[20:20+l]); return j,b[20+l+8:]
def clips(b):
    j,bn=parse(b); out={}
    for a in j.get('animations',[]):
        dur=0; step=None
        for s in a['samplers']:
            acc=j['accessors'][s['input']]; dur=max(dur,acc['max'][0])
            if step is None and acc['count']>2:
                bv=j['bufferViews'][acc['bufferView']]; o=bv.get('byteOffset',0)+acc.get('byteOffset',0); t=struct.unpack_from('<3f',bn,o); step=t[1]-t[0]
        out[a['name']]=(dur,step)
    return out
fails=0; n=0
for f in sorted(glob.glob('voxel/*_voxel*.glb')):
    new=clips(open(f,'rb').read())
    try: old=clips(subprocess.run(['git','show','1b7e415:'+f],capture_output=True,check=True).stdout)
    except subprocess.CalledProcessError: old={}
    for c,(d,st) in new.items():
        n+=1; bad=[]
        ost=old.get(c,(0,None))[1]
        if st is not None and abs(st-1/30)>1e-3: bad.append('fps %.1f'%(1/st))   # test 36: speed36 fixed the source, no stretch allowance
        if c in old and abs(old[c][0]-d)>1/30+1e-4: bad.append('dur %.3f vs t33 %.3f (x%.2f)'%(d,old[c][0],old[c][0]/max(d,1e-6)))
        if bad: fails+=1; print('FAIL',f,c,', '.join(bad))
print('CLIPSPEED %d clips, %d failed -> %s'%(n,fails,'PASS' if fails==0 else 'FAIL')); sys.exit(1 if fails else 0)
