"""Measure combined-gaze closures, attachment error and ocular proximity."""
import json
import hashlib
import math
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from wrapper import eyes,lids,expressions
from probe_blink_closure import eye_tree,visible_grid


def attachment_metrics():
    deps=bpy.context.evaluated_depsgraph_get()
    head=BVHTree.FromObject(bpy.data.objects['GNM_skin'],deps)
    eye={s:eye_tree(s) for s in ('L','R')}
    errors=[]
    clearance={s:[] for s in ('L','R')}
    for obj in bpy.context.scene.objects:
        if obj.type!='CURVES' or not obj.name.startswith(('Lid_lashes_','Brow_fibers_')) or obj.hide_render:continue
        data=obj.evaluated_get(deps).data
        for curve in data.curves:
            root=obj.matrix_world@data.attributes['position'].data[curve.first_point_index].vector
            errors.append(head.find_nearest(root)[3])
            if obj.name.startswith('Lid_lashes_'):
                side=obj.name[-1]
                p,n,index,distance=eye[side].find_nearest(root)
                clearance[side].append(float((root-p).dot(n)))
    return {'attachment_roots':len(errors),'max_root_distance_m':max(errors),
            'lash_root_eye_signed_clearance_min_m':{s:min(c) for s,c in clearance.items()},
            'lash_roots_inside_eye_count':{s:sum(d<-.00003 for d in c) for s,c in clearance.items()}}


def main():
    folder=ROOT/'work/milestone3/gaze_lids'
    bpy.ops.wm.open_mainfile(filepath=str(folder/'IRISX_GAZE_LIDS_RIG.blend'),use_scripts=False)
    timeline=[]
    for frame in range(1,145):
        bpy.context.scene.frame_set(frame)
        target=bpy.data.objects['FixationTarget'].location
        angles={}
        for side in ('L','R'):
            eye=bpy.data.objects['Eye_'+side]
            actual=(eye.matrix_world.to_3x3()@Vector((0,1,0))).normalized()
            desired=(target-eye.matrix_world.translation).normalized()
            angles[side]=math.degrees(actual.angle(desired,0))
        timeline.append({'frame':frame,'aim_error_degrees':angles})
    rows=[]
    with expressions.manual():
        for h,v in [(0,0),(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
            for opening in [1,.75,.5,.25,0]:
                eyes.move(h,v)
                lids.set_opening(opening)
                expressions.set_brows(0)
                row={'h':h,'v':v,'opening':opening,**attachment_metrics()}
                if opening in [0,1]:row['visible_eye_samples']={s:visible_grid(s,81,81)['visible_eye_rays'] for s in ('L','R')}
                rows.append(row)
                print('GAZE_LID_PROBE',json.dumps(row),flush=True)
    report={'scene_sha256':hashlib.sha256((folder/'IRISX_GAZE_LIDS_RIG.blend').read_bytes()).hexdigest(),
            'poses':rows,'timeline':timeline,'max_timeline_aim_error_degrees':max(r['aim_error_degrees'][s] for r in timeline for s in ('L','R')),
            'scope':'Sampled attachment/ocular proximity. Signed lash-root distances are surface-normal probes, not a continuous collision or volume-intersection proof.'}
    (folder/'geometry_probe.json').write_text(json.dumps(report,indent=2)+'\n')
    print('GAZE_LID_PROBE_DONE','aim degrees',report['max_timeline_aim_error_degrees'],flush=True)


if __name__=='__main__':main()
