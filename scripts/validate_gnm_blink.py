"""Reopen and audit the blink prototype; sampled geometry, not realism grading."""
import hashlib
import json
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from wrapper import eyes,lids
from validate_lid_review import digest
from probe_blink_closure import visible_grid


def main():
    source=ROOT/'work/review/lids/IRISX_LIDS_REVIEW.blend'
    path=ROOT/'work/milestone3/IRISX_BLINK_PROTOTYPE.blend'
    bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
    original={o.name:digest(o.data) for o in bpy.context.scene.objects if o.get('gnm_component')}
    bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False)
    scene=bpy.context.scene
    head=bpy.data.objects['GNM_skin']
    keys=head.data.shape_keys
    checks=[]
    def check(name,value):
        checks.append({'test':name,'passed':bool(value)})
        if not value:print('FAILED',name,flush=True)
    for name,expected in original.items():
        for label,a,b in zip(['Basis','UV','topology'],digest(bpy.data.objects[name].data),expected):
            check(name+' native '+label+' preserved',a==b)
    action=keys.animation_data.action
    check('editable blink action survives reopening',action is not None and action.name=='IrisX | native blink prototype')
    check('timeline is 72 frames at 24 fps',scene.frame_start==1 and scene.frame_end==72 and scene.render.fps==24)
    timeline=[]
    for frame in range(1,73):
        scene.frame_set(frame)
        timeline.append({'frame':frame,**lids.state()})
    check('timeline opening stays in normalized range',all(0<=r[k]<=1 for r in timeline for k in ('opening_L','opening_R')))
    check('timeline closes twice and restores open at end',all(timeline[f-1]['opening_L']==timeline[f-1]['opening_R']==v for f,v in [(1,1),(21,0),(27,1),(51,0),(57,1),(72,1)]))
    check('timeline includes changing intermediate poses',any(0<r['opening_L']<1 for r in timeline))
    scene.frame_set(1)
    keys.animation_data.action=None
    eyes.reset()
    lids.reset()
    neutral=eyes.state()
    poses=[]
    for opening in [1,.75,.5,.25,0]:
        lids.set_opening(opening)
        surface=BVHTree.FromObject(head,bpy.context.evaluated_depsgraph_get())
        roots=[]
        drivers=[]
        for obj in scene.objects:
            if obj.name.startswith('Lid_lashes_') and obj.type=='CURVES' and not obj.hide_render:
                evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
                for curve in evaluated.data.curves:
                    p=obj.matrix_world@evaluated.data.attributes['position'].data[curve.first_point_index].vector
                    roots.append(surface.find_nearest(p)[3])
                for mod in obj.modifiers:
                    if mod.type=='NODES' and mod.node_group.animation_data:
                        drivers.extend(f.driver.is_valid for f in mod.node_group.animation_data.drivers)
        row={'opening':opening,'lash_root_count':len(roots),'max_lash_root_distance_m':max(roots),
             'eye_visibility':{s:visible_grid(s,81,81)['visible_eye_rays'] for s in ('L','R')}}
        poses.append(row)
        check(f'opening {opening}: 207 roots within 0.30 mm of moving lid',len(roots)==207 and max(roots)<.00030)
        check(f'opening {opening}: lash node drivers work with autoexec disabled',len(drivers)==8 and all(drivers))
        check(f'opening {opening}: no eye center drift',all(np.linalg.norm(np.array(eyes.state()['eye_center_3D_'+s])-neutral['eye_center_3D_'+s])<1e-7 for s in ('L','R')))
        print('BLINK_POSE',row,flush=True)
    check('full closure occludes both eyes on sampled frontal grid',all(poses[-1]['eye_visibility'][s]==0 for s in ('L','R')))
    check('visible aperture decreases as lids close',all(poses[i]['eye_visibility'][s]>=poses[i+1]['eye_visibility'][s] for i in range(len(poses)-1) for s in ('L','R')))
    for h,v in [(-1,0),(1,0),(0,1),(0,-1)]:
        eyes.move(h,v)
        check(f'gaze {h},{v}: both physical centers preserved',all(np.linalg.norm(np.array(eyes.state()['eye_center_3D_'+s])-neutral['eye_center_3D_'+s])<1e-7 for s in ('L','R')))
    eyes.reset()
    lids.reset()
    check('eyes and lids reset deterministically',eyes.state()==neutral and lids.state()=={'opening_L':1.,'opening_R':1.})
    lids.set_opening(0,1)
    check('independent left wink',lids.state()=={'opening_L':0.,'opening_R':1.})
    lids.set_opening(1,0)
    check('independent right wink',lids.state()=={'opening_L':1.,'opening_R':0.})
    for value in [True,'closed',float('nan'),float('inf'),-.1,1.1]:
        rejected=False
        before=lids.state()
        try:lids.set_opening(.5,value)
        except (ValueError,TypeError):rejected=True
        check('reject invalid opening '+repr(value)+' without partial update',rejected and lids.state()==before)
    receipt=json.loads((path.parent/'prototype.json').read_text())
    check('scene checksum matches render receipt',receipt['scene_sha256']==hashlib.sha256(path.read_bytes()).hexdigest())
    for record in receipt['poses']:
        image_path=path.parent/(record['view']+'.png')
        check(record['view']+' actual render checksum',hashlib.sha256(image_path.read_bytes()).hexdigest()==record['image_sha256'])
    lids.reset()
    keys.animation_data.action=action
    scene.frame_set(1)
    report={'status':'PASS' if all(c['passed'] for c in checks) else 'FAIL','passed':sum(c['passed'] for c in checks),
            'failed':sum(not c['passed'] for c in checks),'checks':checks,'poses':poses,'timeline':timeline,
            'scene':str(path.relative_to(ROOT)),'scene_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'scope':'Native data, reopening/action, normalized controls, sampled frontal closure and lash attachments. Does not certify continuous corneal clearance, self intersections, gaze-follow or photographic realism.'}
    folder=ROOT/'tests/milestone3'
    folder.mkdir(exist_ok=True)
    (folder/'blink_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('BLINK_AUDIT',report['status'],report['passed'],'passed',report['failed'],'failed',flush=True)
    if report['failed']:raise RuntimeError('Blink prototype checks failed')


if __name__=='__main__':main()
