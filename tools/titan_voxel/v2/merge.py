import bpy,sys
a=sys.argv[sys.argv.index('--')+1:]; fam,out=a[0],a[1]
ch=open('/workspace/titan2/post/chunks.txt').read().strip().split('\n')
bpy.ops.wm.open_mainfile(filepath=f'/workspace/titan2/post/{fam}_0.blend')
for i in range(1,len(ch)):
    names=ch[i].split(',')
    for n in names:
        if n in bpy.data.actions: bpy.data.actions.remove(bpy.data.actions[n])
    with bpy.data.libraries.load(f'/workspace/titan2/post/{fam}_{i}.blend') as (f,t): t.actions=[x for x in f.actions if x in names]
for ex in a[2:]:
    fpath,n=ex.split(':'); bpy.data.actions.remove(bpy.data.actions[n])
    with bpy.data.libraries.load(fpath) as (f,t): t.actions=[n]
for x in bpy.data.actions: x.use_fake_user=True
print('ACTS',len(bpy.data.actions),sorted(x.name for x in bpy.data.actions if '__' in x.name or x.name.endswith('_p')))
bpy.ops.wm.save_as_mainfile(filepath=out)
