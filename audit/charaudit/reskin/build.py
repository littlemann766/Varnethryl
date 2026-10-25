from glb import *; from PIL import Image; import io
for n in ['garruk','rook','talia','cedric','morwen','nyx']:
    new=Image.open(f'new_{n}.png').convert('RGB')
    for s,sz in [('',2048),('_lod1',1024),('_lod2',512)]:
        j,b=load(f'orig/{n}{s}.glb'); k=f'{n}_base{s}'
        old=images(j,b)[k]; im=new if sz==2048 else new.resize((sz,sz),Image.LANCZOS)
        bio=io.BytesIO(); im.save(bio,'PNG' if old[:4]==b'\x89PNG' else 'JPEG',quality=92,optimize=True)
        save(f'out/{n}{s}.glb',j,b,{k:bio.getvalue()})
