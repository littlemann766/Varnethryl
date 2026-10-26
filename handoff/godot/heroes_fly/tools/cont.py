import sys,glob,numpy as np
from PIL import Image
bad=[]
for d in sorted(glob.glob(sys.argv[1]+'/fly_*')):
    fs=sorted(glob.glob(d+'/f_*.png'))
    if not fs: continue
    im=[np.asarray(Image.open(f).convert('L').resize((160,180)),dtype=np.float32) for f in fs]
    im.append(im[0])  # loop seam
    df=np.array([np.abs(im[i+1]-im[i]).mean() for i in range(len(im)-1)])
    med=np.median(df); frozen=int((df<0.02).sum()); pops=int((df>4*med+0.5).sum())
    print(f"CONT {d.split('/')[-1]:22s} frames={len(fs)} diff med={med:.3f} min={df.min():.3f} max={df.max():.3f} frozen={frozen} pops={pops} seam={df[-1]:.3f}")
    if frozen or pops: bad.append(d)
print('BAD',bad)
