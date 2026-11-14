"""Correct live preview and refine static lid anatomy in a separate scene."""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from wrapper import eyes,lid_anatomy,preview_materials
from render_device import configure

parser=argparse.ArgumentParser()
parser.add_argument('--samples',type=int,default=128)
parser.add_argument('--views',default='eye,front,eevee_eye')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
source=ROOT/'work/review/cyberpunk/IRISX_ASSET_REVIEW.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
scene=bpy.context.scene
configure()
scene.cycles.samples=args.samples
eyes.reset()
stats=lid_anatomy.refine()
preview_materials.configure()
print('LID_ANATOMY',json.dumps(stats),flush=True)
out=ROOT/'work/review/lids'
out.mkdir(parents=True,exist_ok=True)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active
            space.shading.type='MATERIAL'
            space.shading.use_scene_lights=True
            space.shading.use_scene_world=True
            space.overlay.show_overlays=False
            space.region_3d.view_perspective='CAMERA'
scene['lid_anatomy_stats']=json.dumps(stats)
scene['review_note']='Corrected EEVEE Material Preview and static native lid shape/details. Cycles remains the physical render. Blink/gaze-follow rig remains future work.'
text=bpy.data.texts.new('IRISX_LID_REVIEW.txt')
text.write('Preview fix and original static lid refinement. Native Basis and UVs retained; subtle native lid-sculpt shape key, mucosal rim, tear line, caruncles and clustered lashes. No animated closure or gaze-follow claimed. EEVEE uses transparent/specular corneal glazing and supported strand surfaces; Cycles retains physical refraction and hair scattering. Imported asset credits remain in IRISX_PUBLIC_ASSET_CREDITS.txt.\n')
path=out/'IRISX_LIDS_REVIEW.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(path))
print('LID_REVIEW_SAVED',path,flush=True)
records=[]
for view in filter(None,args.views.split(',')):
    scene.render.engine='BLENDER_EEVEE' if view.startswith('eevee') else 'CYCLES'
    scene.camera=bpy.data.objects['Review_eye_closeup' if view.endswith('eye') else 'RenderCamera']
    start=time.perf_counter()
    record=eyes.render(out/(view+'.png'))
    record.update(view=view,seconds=time.perf_counter()-start,engine=scene.render.engine,
                  image_sha256=hashlib.sha256((out/(view+'.png')).read_bytes()).hexdigest())
    records.append(record)
    (out/'receipt.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scene_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'stats':stats,'views':records,'scene':str(path.relative_to(ROOT))},indent=2)+'\n')
scene.render.engine='CYCLES'
scene.camera=bpy.data.objects['RenderCamera']
eyes.reset()
print('LID_RENDERS_COMPLETE',len(records),flush=True)
