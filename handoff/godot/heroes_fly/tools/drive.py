import subprocess,json,re,glob,os,sys
B=os.environ['B']
def run(*a,env=None): return subprocess.run([B,'-b','-P',*a],capture_output=True,text=True,env={**os.environ,**(env or {})}).stdout
def st(f,pfx='fly_'):
    m=re.search(r'STR (.*)',run('str2.py','--',f,pfx)); d=json.loads(m.group(1))
    return {re.sub(r'_[A-Za-z0-9]*_Rig$','',k):max(v.values()) for k,v in d.items()}
names=sys.argv[1:]
res=json.load(open('res2.json'))
RW={'lunara','nyx','rook','snowy','wren'}
for n in names:
    src=f'/workspace/rigged/{n}_h.glb'; out=f'out/{n}_fly.glb'
    w=st(src,'walk'); wb=max(w.values()) if w else None
    tried={}
    for k in (0.0,0.2,0.5,1.0):
        o=run('fly.py','--',src,out,env={'SECK':str(k),**({'REWEIGHT':'1'} if n in RW else {})})
        if 'OK' not in o: print('FAIL',n,o[-500:]); break
        tried[k]=st(out)
    base=max(tried[0.0].values()); lim=max(wb or 0, base*1.1)
    k=max([kk for kk,v in tried.items() if max(v.values())<=lim] or [0.0])
    run('fly.py','--',src,out,env={'SECK':str(k),**({'REWEIGHT':'1'} if n in RW else {})})
    m=re.search(r'CLIP (\d+) (.*)',run('clip.py','--',out)); cl=json.loads(m.group(2)) if m else {}
    res[n]=dict(walk=wb,seck=k,fly=tried.get(k),reweight=n in RW,clip=cl); print(n,res[n],flush=True)
    json.dump(res,open('res2.json','w'),indent=1)
