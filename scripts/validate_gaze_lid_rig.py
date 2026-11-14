"""Reopen the gaze/lid rig and audit sampled engineering gates."""
import hashlib
import json
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from wrapper import eyes,lids,expressions
from validate_lid_review import digest
from probe_gaze_lid_rig import attachment_metrics
from wrapper.lid_anatomy import _roots


def coords(head):
    keys=head.data.shape_keys.key_blocks
    base=np.array([p.co[:] for p in keys['Basis'].data],np.float64)
    result=base.copy()
    for key in list(keys)[1:]:
        if key.value:result+=(np.array([p.co[:] for p in key.data])-base)*key.value
    return result


def areas(vertices,faces):
    a,b,c,d=(vertices[faces[:,i]] for i in range(4))
    return (np.linalg.norm(np.cross(b-a,c-a),axis=1)+np.linalg.norm(np.cross(c-a,d-a),axis=1))*.5


def main():
    folder=ROOT/'work/milestone3/gaze_lids'
    path=folder/'IRISX_GAZE_LIDS_RIG.blend'
    source=ROOT/'work/review/lids/IRISX_LIDS_REVIEW.blend'
    bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
    native={o.name:digest(o.data) for o in bpy.context.scene.objects if o.get('gnm_component')}
    bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False)
    scene=bpy.context.scene
    head=bpy.data.objects['GNM_skin']
    checks=[]
    def check(name,value):
        checks.append({'test':name,'passed':bool(value)})
        if not value:print('FAILED',name,flush=True)
    for name,expected in native.items():
        for label,a,b in zip(['Basis','UV','topology'],digest(bpy.data.objects[name].data),expected):check(name+' native '+label,a==b)
    probe=json.loads((folder/'geometry_probe.json').read_text())
    check('geometry probe identifies current exact scene',probe['scene_sha256']==hashlib.sha256(path.read_bytes()).hexdigest())
    for row in probe['poses']:
        name=f"gaze {row['h']},{row['v']} opening {row['opening']}"
        check(name+' all 1447 attachment roots within 0.30 mm',row['attachment_roots']==1447 and row['max_root_distance_m']<.00030)
        check(name+' lash roots clear ocular surface within 30 micrometer contact tolerance',all(v==0 for v in row['lash_roots_inside_eye_count'].values()))
        if row['opening']==0:check(name+' no exposed eye on 81x81 frontal grid',all(v==0 for v in row['visible_eye_samples'].values()))
    check('144-frame 24-fps review timeline',scene.frame_start==1 and scene.frame_end==144 and scene.render.fps==24)
    check('three editable actions survive reopen',all(o.animation_data and o.animation_data.action for o in [head.data.shape_keys,bpy.data.objects['GazeRig'],bpy.data.objects['FixationTarget']]))
    for owner in [head.data.shape_keys]+[m.node_group for o in scene.objects for m in o.modifiers if m.type=='NODES' and o.get('expression_binding')]+[o.data.shape_keys for o in scene.objects if o.type=='MESH' and o.get('expression_binding')]:
        if owner.animation_data:
            check(owner.name+' simple valid native drivers',all(f.driver.is_valid and f.driver.is_simple_expression for f in owner.animation_data.drivers))
    aim_errors=[]
    neutral_centers={s:bpy.data.objects['Eye_'+s].matrix_world.translation.copy() for s in ('L','R')}
    for frame in range(1,145):
        scene.frame_set(frame)
        target=bpy.data.objects['FixationTarget'].location
        for side in ('L','R'):
            eye=bpy.data.objects['Eye_'+side]
            desired=(target-eye.matrix_world.translation).normalized()
            actual=(eye.matrix_world.to_3x3()@Vector((0,1,0))).normalized()
            aim_errors.append(float((desired-actual).length))
            check(f'frame {frame} {side} center invariant',(eye.matrix_world.translation-neutral_centers[side]).length<1e-7)
        check(f'frame {frame} keeps normalized gaze',abs(target.x)<=.050001 and abs(target.z)<=.050001 and abs(target.y+.35)<1e-6)
    check('both eyes aim at target between every timeline key within 1e-5 direction norm',max(aim_errors)<1e-5)
    scene.frame_set(54)
    previous=expressions.state()
    with expressions.manual():
        expressions.reset()
        rest=coords(head)
        faces=np.array([p.vertices[:] for p in head.data.polygons])
        rest_areas=areas(rest,faces)
        # Native canthal vertex probes picked once from original lash endpoints.
        corners=[]
        for side in ('L','R'):
            line=_roots('Lashes_upper_'+side)
            corners.extend(int(np.linalg.norm(rest-point,axis=1).argmin()) for point in line[[0,-1]])
        distortion=[]
        for h,v,opening,brow in [(0,1,1,0),(0,-1,1,0),(-1,1,.5,.35),(1,-1,.5,.35),(0,1,0,.35),(0,-1,0,0),(0,0,1,1)]:
            eyes.move(h,v)
            lids.set_opening(opening)
            expressions.set_brows(brow)
            current=coords(head)
            ratio=areas(current,faces)/np.maximum(rest_areas,1e-12)
            moved=np.linalg.norm(current-rest,axis=1)>.00005
            region=ratio[np.any(moved[faces],axis=1)]
            metrics=attachment_metrics()
            check(f'combined pose {h},{v},{opening},{brow} attachment fit',metrics['max_root_distance_m']<.00030)
            check(f'combined pose {h},{v},{opening},{brow} finite noncollapsed native faces',np.isfinite(ratio).all() and ratio.min()>.02)
            distortion.append({'h':h,'v':v,'opening':opening,'brow':brow,'native_face_area_ratio_min':float(region.min()),
                               'native_face_area_ratio_p99':float(np.quantile(region,.99)),'native_face_area_ratio_max':float(region.max()),
                               'max_canthal_probe_displacement_m':float(np.linalg.norm((current-rest)[corners],axis=1).max()),'attachments':metrics})
        expressions.reset()
        first=expressions.state()
        eyes.move(1,-1)
        lids.set_opening(.25)
        expressions.set_brows(1,0)
        expressions.reset()
        check('combined reset is deterministic',expressions.state()==first)
        check('neutral gaze has zero follow',all(v==0 for v in first['lid_follow'].values()))
        for value in [True,'high',float('nan'),float('inf'),-.1,1.1]:
            before=expressions.state()
            rejected=False
            try:expressions.set_brows(.5,value)
            except (TypeError,ValueError):rejected=True
            check('reject invalid brow '+repr(value)+' atomically',rejected and expressions.state()==before)
    check('manual context restores timeline pose and all actions',expressions.state()==previous)
    try:
        with expressions.manual():
            expressions.reset()
            raise RuntimeError('intentional restore check')
    except RuntimeError:pass
    check('manual context restores timeline after caller exception',expressions.state()==previous)
    check('calibrated camera and target forward distance retained',(bpy.data.objects['RenderCamera'].location-Vector((0,-.4,0))).length<1e-7 and abs(bpy.data.objects['FixationTarget'].location.y+.35)<1e-6)
    scene.frame_set(1)
    output=ROOT/'tests/milestone3/gaze_lids'
    output.mkdir(exist_ok=True)
    report={'status':'PASS' if all(c['passed'] for c in checks) else 'FAIL','passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),
            'checks':checks,'scene_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'geometry_probe':probe,'native_face_metrics':distortion,
            'max_timeline_aim_direction_error_norm':max(aim_errors),
            'scope':'Native data, timeline aim, sampled 9-gaze x 5-opening attachment and lash-root ocular proximity, closure, controls and face areas. Not continuous lid-volume/self-intersection certification, final texture-stretch acceptance or photographic realism.'}
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('GAZE_LID_AUDIT',report['status'],report['passed'],'passed',report['failed'],'failed',flush=True)
    print('AIM_DIRECTION_ERROR_NORM',max(aim_errors),'CANThAL_MAX_M',max(m['max_canthal_probe_displacement_m'] for m in distortion),flush=True)
    if report['failed']:raise RuntimeError('Gaze/lid rig validation failed')


if __name__=='__main__':main()
