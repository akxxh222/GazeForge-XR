"""Reopen one asset review and audit native data/calibration, not realism."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from wrapper import eyes


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--scene',type=Path,default=ROOT/'work/review/cyberpunk/IRISX_ASSET_REVIEW.blend')
    parser.add_argument('--report',type=Path,default=ROOT/'tests/milestone2/public_asset_review/report.json')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(args.scene),use_scripts=False)
    scene=bpy.context.scene
    checks=[]
    def check(name,value):checks.append({'test':name,'passed':bool(value)})
    with np.load(ROOT/'assets/gnm/gnm_head.npz',allow_pickle=False) as src:
        uv=src['quad_uvs']
        faces=src['quads']
        original=src['template_vertex_positions']
        joint_names=src['joint_names'].tolist()
        joints=src['template_joint_positions']
        groups=src['vertex_groups']
        group_names=src['vertex_group_names'].tolist()
    mid=(joints[joint_names.index('left_eye')]+joints[joint_names.index('right_eye')])/2
    transform=np.array([[1,0,0],[0,0,1],[0,-1,0]])
    original=(original-mid)@transform
    centers={s:(joints[joint_names.index(n)]-mid)@transform for s,n in [('L','left_eye'),('R','right_eye')]}
    for obj in [o for o in scene.objects if o.get('gnm_component')]:
        mesh=obj.data
        vid=np.array([v.value for v in mesh.attributes['gnm_vertex_id'].data])
        fid=np.array([p.value for p in mesh.attributes['gnm_quad_id'].data])
        actual_uv=np.array([a.uv[:] for a in mesh.uv_layers.active.data],dtype=np.float32)
        actual_faces=np.array([[vid[i] for i in p.vertices] for p in mesh.polygons])
        target=original[vid].copy()
        if obj.name.startswith('Eye_'):
            target=(target-centers[obj.name[-1]])*np.array([-1,-1,1])
        check(obj.name+' native UVs exactly unchanged',np.array_equal(actual_uv,uv[fid].reshape(-1,2)))
        check(obj.name+' native topology exactly unchanged',np.array_equal(actual_faces,faces[fid]))
        check(obj.name+' native Basis geometry unchanged',np.max(np.abs(np.array([v.co[:] for v in mesh.vertices])-target))<1e-7)
        if obj.name.startswith('Eye_'):
            keys=mesh.shape_keys.key_blocks
            check(obj.name+' native shape-key Basis equals mesh',np.array_equal(np.array([v.co[:] for v in keys['Basis'].data]),np.array([v.co[:] for v in mesh.vertices])))
            pupil_ids=np.flatnonzero(groups[group_names.index('pupils')][vid]>.5)
            deformed=np.array([v.co[:] for v in keys['Pupil | daylight constriction'].data])
            centroid=deformed[pupil_ids].mean(0)
            check(obj.name+' aperture centroid agrees with geometric label',np.linalg.norm(centroid-np.array(obj['pupil_center_local']))<1e-7)
            exterior=groups[group_names.index('eye_exteriors')][vid]>.5
            check(obj.name+' spherical exterior untouched by constriction',np.max(np.abs(deformed[exterior]-target[exterior]))<1e-7)
            mat=obj.data.materials[1]
            check(obj.name+' adapted iris retains source credit/license',mat.get('author')=='Daniel Bystedt' and mat.get('license')=='CC BY-SA 3.0')

    hair=next(o for o in scene.objects if o.name.startswith('Public_groom_'))
    positions=np.empty(len(hair.data.points)*3,np.float32)
    hair.data.attributes['position'].data.foreach_get('vector',positions)
    positions=positions.reshape(-1,16,3)
    radii=np.empty(len(hair.data.points),np.float32)
    hair.data.attributes['radius'].data.foreach_get('value',radii)
    check('imported scalp curves have finite positions and tapered radii',np.isfinite(positions).all() and np.isfinite(radii).all() and radii.min()>0 and radii.max()<.00005)
    check('imported scalp groom follows rigid head transforms',hair.parent==bpy.data.objects['GNM_skin'])
    surface=BVHTree.FromObject(bpy.data.objects['GNM_skin'],bpy.context.evaluated_depsgraph_get())
    roots,clearance=[],[]
    for i in np.linspace(0,len(positions)-1,512).astype(int):
        line=[hair.matrix_world@Vector(p) for p in positions[i]]
        roots.append(surface.find_nearest(line[0])[3])
        for a,b in zip(line,line[1:]):
            for t in (.25,.5,.75,1):
                p=a.lerp(b,t)
                q,n,face,d=surface.find_nearest(p)
                clearance.append((p-q).dot(n))
    check('512 sampled groom roots within 0.10 mm of scalp',max(roots)<.0001)
    check('sampled segment centers clear the scalp within 1 micrometer numerical tolerance',min(clearance)>-.000001)
    eyes.reset()
    neutral=eyes.state()
    pivots=[bpy.data.objects['Eye_'+s].matrix_world.translation.copy() for s in ('L','R')]
    camera=scene.camera.matrix_world.copy()
    for name,h,v in [('left',-1,0),('right',1,0),('up',0,1),('down',0,-1)]:
        eyes.move(h,v)
        state=eyes.state()
        check(name+' preserves both physical eye centers',all((bpy.data.objects['Eye_'+s].matrix_world.translation-p).length<1e-7 for s,p in zip(('L','R'),pivots)))
        check(name+' geometric projections move in commanded direction',all(
            (state['pupil_center_2D_'+s][0]-neutral['pupil_center_2D_'+s][0])*h>0 if h else
            (state['pupil_center_2D_'+s][1]-neutral['pupil_center_2D_'+s][1])*v<0 for s in ('L','R')))
    eyes.reset()
    check('neutral reset reproduces all geometric labels exactly',neutral==eyes.state())
    check('locked 40 cm calibrated camera',scene.camera.name=='RenderCamera' and scene.camera.data.lens==40 and (scene.camera.location-Vector((0,-.4,0))).length<1e-7 and np.array_equal(camera,np.array(scene.camera.matrix_world)))
    check('neutral fixation stays 35 cm ahead',(bpy.data.objects['FixationTarget'].location-Vector((0,-.35,0))).length<1e-7)
    check('all seven texture images are packed',len([i for i in bpy.data.images if i.name.startswith(('skin_','eye_')) and i.packed_file])==7)
    check('embedded mixed-source asset credits present','IRISX_PUBLIC_ASSET_CREDITS.txt' in bpy.data.texts)
    render_files={}
    for view in ['eye','front','side']:
        path=args.scene.parent/('asset_'+view+'_test.png')
        img=bpy.data.images.load(str(path),check_existing=False)
        check(view+' actual preview is 1024x1024',list(img.size)==[1024,1024])
        render_files[view]={'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size}
    report={'status':'PASS' if all(c['passed'] for c in checks) else 'FAIL',
        'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'checks':checks,
        'scene':str(args.scene.relative_to(ROOT)),'scene_sha256':hashlib.sha256(args.scene.read_bytes()).hexdigest(),
        'groom':{'strand_count':len(positions),'sampled_strands':len(roots),'max_root_distance_m':max(roots),'min_segment_signed_clearance_m':min(clearance)},
        'renders':render_files,'visual_acceptance':'Pending; no photorealism score inferred from engineering checks.',
        'scope':'Native Basis/UV/topology, pupil shape-key centroid, source credits, sampled groom fit, geometric direction/reset and metric capture. No apparent-refraction labels, animated attachment or reference-level realism certification.'}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print('PUBLIC_ASSET_REOPEN',report['status'],report['passed'],'passed',report['failed'],'failed',flush=True)
    print('GROOM_METRICS',report['groom'],flush=True)
    if report['failed']:raise RuntimeError('Review validation failed; inspect report')


if __name__=='__main__':main()
