import json,sys
from PIL import Image
def run(J,name,cols=None):
    import subprocess,os
    json.dump(J,open(f'/tmp/l3w/{name}.json','w'))
    subprocess.run(f"cd /tmp/l3g && VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json timeout 1200 xvfb-run -a godot --path . -- /tmp/l3w/{name}.json > /tmp/l3w/{name}.log 2>&1",shell=True)
def sheet(files,out,cols,scale=1.0,labels=None):
    from PIL import ImageDraw
    ims=[Image.open(f) for f in files if os.path.exists(f)]
    w,h=ims[0].size; rows=(len(ims)+cols-1)//cols; o=Image.new('RGB',(w*cols,h*rows),(60,56,52)); d=ImageDraw.Draw(o)
    for k,i in enumerate(ims):
        o.paste(i,((k%cols)*w,(k//cols)*h))
        if labels: d.text(((k%cols)*w+6,(k//cols)*h+4),labels[k],fill=(20,20,20))
    if scale!=1: o=o.resize((int(o.width*scale),int(o.height*scale)))
    o.save(out)
import os
