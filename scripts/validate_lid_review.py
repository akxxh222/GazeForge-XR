"""Validate the saved lid/preview correction and its actual render evidence."""
import hashlib
import json
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from wrapper import eyes


def digest(mesh):
    arrays=[np.array([v.co[:] for v in mesh.vertices],np.float32),
            np.array([u.uv[:] for u in mesh.uv_layers.active.data],np.float32),
            np.array([p.vertices[:] for p in mesh.polygons],np.int32)]
    return [hashlib.sha256(a.tobytes()).hexdigest() for a in arrays]


def main():
    folder=ROOT/'work/review/lids'
    path=folder/'IRISX_LIDS_REVIEW.blend'
    parent=ROOT/'work/review/cyberpunk/IRISX_ASSET_REVIEW.blend'
    bpy.ops.wm.open_mainfile(filepath=str(parent),use_scripts=False)
    reference={o.name:digest(o.data) for o in bpy.context.scene.objects if o.get('gnm_component')}
    bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False)
    scene=bpy.context.scene
    checks=[]
    def check(name,value):checks.append({'test':name,'passed':bool(value)})
    for name,expected in reference.items():
        actual=digest(bpy.data.objects[name].data)
        for label,a,b in zip(['native Basis','native UVs','native topology'],actual,expected):
            check(name+' '+label+' unchanged from validated parent',a==b)
    head=bpy.data.objects['GNM_skin']
    key=head.data.shape_keys.key_blocks['Lids | margin roll and tarsal fold']
    offset=np.array([p.co[:] for p in key.data])-np.array([p.co[:] for p in head.data.vertices])
    check('lid refinement is enabled and bounded below 1 mm',key.value==1 and 0<float(np.abs(offset).max())<.001)
    check('lid sculpt only changes depth, preserving aperture and canthi in X/Z',np.abs(offset[:,[0,2]]).max()==0)
    for side in ('L','R'):
        mat=bpy.data.objects['Eye_'+side].data.materials[3]
        outputs=[n for n in mat.node_tree.nodes if n.type=='OUTPUT_MATERIAL']
        check(side+' separate linked Cycles/EEVEE corneal outputs',all(any(n.target==target and n.inputs['Surface'].is_linked for n in outputs) for target in ('CYCLES','EEVEE')))
        check(side+' original long lash objects disabled',all(bpy.data.objects['Lashes_'+lid+'_'+side].hide_render for lid in ('upper','lower')))
        check(side+' fine waterline and tear film stay below 45 micrometers radius',all(bpy.data.objects[name+'_'+side].data.bevel_depth<.000045 for name in ('Lid_waterline','Lid_tear_film')))
        check(side+' new caruncle/lashes/waterline follow the head',all(bpy.data.objects[name+'_'+side].parent==head for name in ('Lid_caruncle','Lid_lashes_upper','Lid_lashes_lower','Lid_waterline','Lid_tear_film')))
    surface=BVHTree.FromObject(head,bpy.context.evaluated_depsgraph_get())
    roots=[]
    for obj in [o for o in scene.objects if o.name.startswith('Lid_lashes_')]:
        data=obj.data
        for curve in data.curves:
            p=obj.matrix_world@data.attributes['position'].data[curve.first_point_index].vector
            roots.append(surface.find_nearest(p)[3])
    check('all replacement lash roots remain within 0.30 mm of native lid surface',max(roots)<.00030)
    eyes.reset()
    neutral=eyes.state()
    for h,v in [(-1,0),(1,0),(0,1),(0,-1)]:
        eyes.move(h,v)
        state=eyes.state()
        check(f'gaze {h},{v} preserves both physical centers',all(np.linalg.norm(np.array(state['eye_center_3D_'+s])-neutral['eye_center_3D_'+s])<1e-7 for s in ('L','R')))
    eyes.reset()
    check('gaze reset exactly restores labels',neutral==eyes.state())
    check('calibrated 40 cm camera and 35 cm target retained',scene.camera.name=='RenderCamera' and (scene.camera.location-Vector((0,-.4,0))).length<1e-7 and (bpy.data.objects['FixationTarget'].location-Vector((0,-.35,0))).length<1e-7)
    spaces=[a.spaces.active for screen in bpy.data.screens for a in screen.areas if a.type=='VIEW_3D']
    check('reopens in corrected Material Preview camera view',bool(spaces) and all(s.shading.type=='MATERIAL' and s.region_3d.view_perspective=='CAMERA' and not s.overlay.show_overlays for s in spaces))
    receipt=json.loads((folder/'receipt.json').read_text())
    check('render receipt identifies this exact saved scene',receipt['scene_sha256']==hashlib.sha256(path.read_bytes()).hexdigest())
    for record in receipt['views']:
        image_path=folder/(record['view']+'.png')
        check(record['view']+' render checksum matches receipt',hashlib.sha256(image_path.read_bytes()).hexdigest()==record['image_sha256'])
    eevee=next(r for r in receipt['views'] if r['view']=='eevee_eye')
    scene.camera=bpy.data.objects['Review_eye_closeup']
    image=bpy.data.images.load(str(folder/'eevee_eye.png'),check_existing=False)
    pixels=np.array(image.pixels[:],np.float32).reshape(image.size[1],image.size[0],4)
    eye=bpy.data.objects['Eye_L']
    center=Vector(eye['pupil_center_local'])
    colors=[]
    for sign in (-1,1):
        p=world_to_camera_view(scene,scene.camera,eye.matrix_world@(center+Vector((sign*.0038,0,0))))
        x,y=int(p.x*image.size[0]),int(p.y*image.size[1])
        colors.append(pixels[y-2:y+3,x-2:x+3,:3].mean((0,1)).tolist())
    check('EEVEE iris samples on both sides of pupil contain visible color',all(float(np.dot(c,[.2126,.7152,.0722]))>.025 for c in colors))
    report={'status':'PASS' if all(c['passed'] for c in checks) else 'FAIL','passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),
            'checks':checks,'scene':str(path.relative_to(ROOT)),'scene_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'lid_vertex_count':int((np.abs(offset).max(1)>1e-6).sum()),'max_lid_offset_m':float(np.abs(offset).max()),
            'lash_roots':len(roots),'max_lash_root_distance_m':max(roots),'eevee_iris_probe_rgb_linear':colors,
            'scope':'Saved native data, static eyelid sculpt/attachments, preview output branches, actual EEVEE iris visibility, metric gaze/reset. No blink animation, complete collision certification or reference-level photorealism score.'}
    out=ROOT/'tests/milestone2/lid_review'
    out.mkdir(parents=True,exist_ok=True)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('LID_REVIEW_AUDIT',report['status'],report['passed'],'passed',report['failed'],'failed',flush=True)
    print('LASH_ROOT_MAX_M',max(roots),'EEVEE_IRIS_RGB',colors,flush=True)
    if report['failed']:raise RuntimeError('Lid correction validation failed')


if __name__=='__main__':main()
