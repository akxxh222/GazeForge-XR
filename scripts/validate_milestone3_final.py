"""Reopen and audit the native M3 rig, controls and evaluated motion surfaces."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from wrapper import eyes,lids,expressions
from validate_lid_review import digest
from probe_milestone3_surface import surface_metrics,closure_visibility,outer_tree
from probe_gaze_lid_rig import attachment_metrics


def evaluated_surface(head):
    obj=head.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=obj.to_mesh();mesh.calc_loop_triangles()
    flat=np.empty(len(mesh.vertices)*3,np.float32);mesh.vertices.foreach_get('co',flat)
    triangles=np.empty(len(mesh.loop_triangles)*3,np.int32);mesh.loop_triangles.foreach_get('vertices',triangles)
    points=flat.reshape(-1,3).astype(np.float64)
    connectivity=np.empty(len(mesh.loops),np.int32);mesh.loops.foreach_get('vertex_index',connectivity)
    sizes=np.empty(len(mesh.polygons),np.int32);mesh.polygons.foreach_get('loop_total',sizes)
    topology=hashlib.sha256(connectivity.tobytes()+sizes.tobytes()).hexdigest()
    obj.to_mesh_clear()
    return points,triangles.reshape(-1,3),topology


def detail_clearance():
    """Check complete lashes and canthal tissue, not only fiber roots."""
    deps=bpy.context.evaluated_depsgraph_get();result={}
    for side in ('L','R'):
        tree=outer_tree(side);distances=[]
        for obj in bpy.context.scene.objects:
            anatomy=obj.name.startswith(('Lid_lashes_','Lid_caruncle_','Lid_commissure_','Mucosal_rim_','Lid_waterline_','Lid_tear_film_'))
            matching=obj.name.endswith((side,'_'+side+'_native','_'+side+'_bound'))
            if obj.hide_render or not anatomy or not matching:continue
            evaluated=obj.evaluated_get(deps)
            if obj.type=='CURVES':points=[obj.matrix_world@p.vector for p in evaluated.data.attributes['position'].data]
            else:
                mesh=evaluated.to_mesh();points=[obj.matrix_world@v.co for v in mesh.vertices];evaluated.to_mesh_clear()
            for p in points:
                q,n,index,d=tree.find_nearest(p);distances.append(float((p-q).dot(n)))
        result[side]={'points':len(distances),'minimum_m':min(distances),'inside_beyond_30um':sum(d<-.00003 for d in distances)}
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--reuse-grid',type=Path)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    started=time.perf_counter();folder=ROOT/'work/milestone3/final';path=folder/'IRISX_MILESTONE3.blend'
    cached={};cache_provenance=None
    if args.reuse_grid:
        prior=json.loads(args.reuse_grid.read_text())
        if prior['scene_sha256']!=hashlib.sha256(path.read_bytes()).hexdigest():raise ValueError('Cached measurements do not identify this exact scene')
        cached={(r['h'],r['v'],r['opening']):r for r in prior['poses']}
        cache_provenance={'path':str(args.reuse_grid),'sha256':hashlib.sha256(args.reuse_grid.read_bytes()).hexdigest(),'validator_sha256':prior['validator_sha256'],'scope':'Reused evaluated head surface/eye triangle measurements for the identical immutable scene; controls, details, canthi, native polygon connectivity and timeline are freshly checked.'}
    output=ROOT/'tests/milestone3/final';output.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/review/lids/IRISX_LIDS_REVIEW.blend'),use_scripts=False)
    native={o.name:digest(o.data) for o in bpy.context.scene.objects if o.get('gnm_component')}
    bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False)
    scene=bpy.context.scene;head=bpy.data.objects['GNM_skin'];checks=[];poses=[];timeline=[];distortion=[]
    def check(name,value):
        checks.append({'test':name,'passed':bool(value)})
        if not value:print('FAILED',name,flush=True)
    def save(status='RUNNING'):
        report={'status':status,'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),
                'validator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'checks':checks,'scene_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'poses':poses,'timeline':timeline,
                'reused_grid_measurements':cache_provenance,'texture_deformation':distortion,'runtime_s':time.perf_counter()-started,
                'scope':'Evaluated native lid triangles and closed native outer eyes, complete lash/canthal point probes, native data equality, three actions, controls, sampled closures, canthi and visible surface areas. Discrete geometry samples and rendered review, not mathematical certification for every real-valued input or photographic realism.'}
        (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    for name,expected in native.items():
        for label,current,original in zip(['Basis','UV','topology'],digest(bpy.data.objects[name].data),expected):check(name+' native '+label,current==original)
    check('144-frame 24-fps editable timeline',scene.frame_start==1 and scene.frame_end==144 and scene.render.fps==24)
    check('three complete action bundles survive reopening',set(json.loads(scene['expression_actions']))=={'left','right','generate_motion'} and all(name in bpy.data.actions for bundle in json.loads(scene['expression_actions']).values() for name in bundle))
    check('no frame-change Python playback handler',len(bpy.app.handlers.frame_change_pre)==len(bpy.app.handlers.frame_change_post)==0)
    for group in [m.node_group for obj in scene.objects for m in obj.modifiers if m.type=='NODES']:
        if group.animation_data:check(group.name+' valid simple native drivers',all(f.driver.is_valid and f.driver.is_simple_expression for f in group.animation_data.drivers))
    receipt=json.loads((folder/'rig.json').read_text())
    check('current scene agrees with build receipt',receipt['scene_sha256']==hashlib.sha256(path.read_bytes()).hexdigest())
    for name,expected in receipt['module_sha256'].items():check('current control module '+name,hashlib.sha256((ROOT/'wrapper'/name).read_bytes()).hexdigest()==expected)
    check('authoring script agrees with build receipt',hashlib.sha256((ROOT/'scripts/build_milestone3_final.py').read_bytes()).hexdigest()==receipt['builder_sha256'])
    check('valid simple gaze-follow shape drivers',all(f.driver.is_valid and f.driver.is_simple_expression for f in head.data.shape_keys.animation_data.drivers))
    eye_centers={s:bpy.data.objects['Eye_'+s].matrix_world.translation.copy() for s in ('L','R')}
    scene.frame_set(1)
    with expressions.manual():
        expressions.reset();rest,triangles,rest_topology=evaluated_surface(head)
        rest_areas=np.linalg.norm(np.cross(rest[triangles[:,1]]-rest[triangles[:,0]],rest[triangles[:,2]]-rest[triangles[:,0]]),axis=1)*.5
        tree=BVHTree.FromPolygons(rest.tolist(),triangles.tolist(),all_triangles=True)
        corner_bindings=[]
        for row in json.loads(scene['canthus_landmarks']).values():
            for index in row['head_vertex_indices']:
                q,n,i,d=tree.find_nearest(head.data.vertices[index].co)
                vertices=triangles[i];a,b,c=[Vector(p) for p in rest[vertices]]
                w=barycentric_transform(q,a,b,c,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
                corner_bindings.append((vertices,np.array(w),np.array(q)))
        maximum_corner=0.
        for h,v in [(0,0),(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
            for opening in [1,.75,.5,.25,0]:
                eyes.move(h,v);lids.set_opening(opening);expressions.set_brows(0)
                surface_row={key:value for key,value in cached[(h,v,opening)].items() if key in ['outer_shell','surface_nonadjacent_crossing_pairs','crossing_examples','max_crossing_plane_excursion_m','crossings_beyond_30um','tested_triangles','eye_triangle_crossing_pairs']} if (h,v,opening) in cached else surface_metrics(eye_triangle_test=True)
                row={'h':h,'v':v,'opening':opening,**surface_row,**attachment_metrics(),'details':detail_clearance()}
                check(f'pose {h},{v},{opening} native lid triangles have no nonadjacent crossing',row['surface_nonadjacent_crossing_pairs']==0)
                check(f'pose {h},{v},{opening} both ocular shells clear all selected skin vertices',all(r['inside_beyond_30um']==0 for r in row['outer_shell'].values()))
                check(f'pose {h},{v},{opening} no skin triangle crosses actual outer eye triangles',all(count==0 for count in row['eye_triangle_crossing_pairs'].values()))
                check(f'pose {h},{v},{opening} 1447 attachment roots within 0.30 mm',row['attachment_roots']==1447 and row['max_root_distance_m']<.00030)
                check(f'pose {h},{v},{opening} complete lashes and canthal tissue clear outer eyes',all(r['inside_beyond_30um']==0 for r in row['details'].values()))
                follow=expressions.state()['lid_follow']
                check(f'pose {h},{v},{opening} normalized gaze-follow values',all(abs(follow[direction+'_'+side]-max(0,sign*v)*opening)<1e-5 for side in ('L','R') for direction,sign in [('Up',1),('Down',-1)]))
                points,current_triangles,current_topology=evaluated_surface(head)
                displacement=max(np.linalg.norm(weights@points[indices]-origin) for indices,weights,origin in corner_bindings)
                maximum_corner=max(maximum_corner,float(displacement));row['max_canthal_surface_displacement_m']=float(displacement)
                if opening==0:
                    row['closed_visibility']={s:closure_visibility(s) for s in ('L','R')}
                    check(f'pose {h},{v} no exposed globe on 81x81 opaque anatomy grid',all(r['visible_eye_rays']==0 for r in row['closed_visibility'].values()))
                poses.append(row);print('FINAL_POSE',h,v,opening,'crossings',row['surface_nonadjacent_crossing_pairs'],flush=True);save()
        check('canthal evaluated surface movement stays below 0.75 mm',maximum_corner<.00075)
        for h,v,opening,brow in [(0,0,1,0),(0,0,.5,0),(0,0,0,0),(0,1,.5,1),(0,-1,.5,1),(-1,1,0,1),(1,-1,0,1),(0,0,1,1)]:
            eyes.move(h,v);lids.set_opening(opening);expressions.set_brows(brow)
            points,current_triangles,current_topology=evaluated_surface(head)
            cross=np.cross(points[triangles[:,1]]-points[triangles[:,0]],points[triangles[:,2]]-points[triangles[:,0]])
            area=np.linalg.norm(cross,axis=1)*.5;ratio=area/np.maximum(rest_areas,1e-20)
            moved=np.any(np.linalg.norm(points[triangles]-rest[triangles],axis=2)>.00005,axis=1)
            front=cross[:,1]<-.15*np.maximum(2*area,1e-30)
            centroid=points[triangles].mean(1);surface=BVHTree.FromPolygons(points.tolist(),triangles.tolist(),all_triangles=True)
            visible=[]
            for index in np.flatnonzero(moved&front):
                p=centroid[index];q,n,face,d=surface.ray_cast(Vector((p[0],-.2,p[2])),Vector((0,1,0)))
                if q is not None and abs(q.y-p[1])<1e-5:visible.append(index)
            values=ratio[visible]
            distortion.append({'h':h,'v':v,'opening':opening,'brow':brow,'reference_triangle_list_changed':not np.array_equal(triangles,current_triangles),'native_evaluated_polygon_connectivity_unchanged':current_topology==rest_topology,'moved_triangles':int(moved.sum()),'front_visible_changed_triangles':len(visible),
                               'all_changed_area_ratio_min':float(ratio[moved].min()) if moved.any() else 1.,
                               'front_visible_area_ratio_percentiles':np.quantile(values,[0,.01,.5,.99,1]).tolist() if len(values) else [1]*5})
            check(f'texture pose {h},{v},{opening},{brow} finite evaluated geometry and unchanged topology',np.isfinite(points).all() and current_topology==rest_topology and len(points)==len(rest))
            check(f'texture pose {h},{v},{opening},{brow} no nonadjacent lid crossings',surface_metrics()['surface_nonadjacent_crossing_pairs']==0)
        expressions.reset();first=expressions.state()
        eyes.move(1,-1);lids.set_opening(.2,.6);expressions.set_brows(1,0);expressions.set_pupil_constriction(.1);expressions.reset()
        check('reset restores gaze/lids/brows/pupils deterministically',expressions.state()==first)
        for function,args in [(expressions.set_brows,(.5,float('nan'))),(expressions.set_pupil_constriction,(1.1,)),(lids.set_opening,(.5,-.1)),(expressions.use_action,('invalid',))]:
            before=expressions.state();rejected=False
            try:function(*args)
            except (TypeError,ValueError):rejected=True
            check(function.__name__+' invalid input rejected atomically',rejected and expressions.state()==before)
        lids.set_opening(0,1);check('independent left blink',lids.state()=={'opening_L':0.,'opening_R':1.})
        expressions.set_brows(.2,.8);check('independent brows',all(abs(head.data.shape_keys.key_blocks['Brow.Raise.'+s].value-v)<1e-6 for s,v in [('L',.2),('R',.8)]))
        expressions.reset()
    for mode in ('left','right','generate_motion'):
        expressions.use_action(mode)
        mode_inputs=[];mode_openings=[]
        for frame in range(1,145):
            scene.frame_set(frame);state=expressions.state();geometry=surface_metrics()
            mode_inputs.append(state['input']['h']);mode_openings.append(state['opening_L'])
            errors=[];centers=[]
            for side in ('L','R'):
                eye=bpy.data.objects['Eye_'+side];desired=(bpy.data.objects['FixationTarget'].location-eye.matrix_world.translation).normalized()
                actual=(eye.matrix_world.to_3x3()@Vector((0,1,0))).normalized();errors.append(float((desired-actual).length));centers.append(float((eye.matrix_world.translation-eye_centers[side]).length))
            check(f'{mode} frame {frame} evaluated geometry clears eyes and has no lid crossings',geometry['surface_nonadjacent_crossing_pairs']==0 and all(r['inside_beyond_30um']==0 for r in geometry['outer_shell'].values()))
            check(f'{mode} frame {frame} calibrated centers and binocular aim',max(errors)<1e-5 and max(centers)<1e-7 and all(abs(v)<1.00001 for v in state['input'].values()))
            timeline.append({'mode':mode,'frame':frame,'aim_direction_error_norm':max(errors),'center_error_m':max(centers),'geometry':geometry})
            if frame%12==0:print('FINAL_TIMELINE',mode,frame,flush=True);save()
        check(mode+' contains complete blink closure',min(mode_openings)==0.)
        check(mode+' reaches authored horizontal direction',min(mode_inputs)<-.99 if mode=='left' else max(mode_inputs)>.99 if mode=='right' else min(mode_inputs)<-.99 and max(mode_inputs)>.99)
        check(mode+' ends in neutral open pose',all(abs(v)<1e-6 for v in expressions.state()['input'].values()) and lids.state()=={'opening_L':1.,'opening_R':1.})
        windows=list(range(57,65))+list(range(105,114)) if mode=='generate_motion' else list(range(66,75))
        for frame in windows:
            for subframe in (.25,.5,.75):
                scene.frame_set(frame,subframe=subframe);geometry=surface_metrics()
                check(f'{mode} blink subframe {frame}+{subframe} has no lid crossings or eye penetration',geometry['surface_nonadjacent_crossing_pairs']==0 and all(r['inside_beyond_30um']==0 for r in geometry['outer_shell'].values()))
                timeline.append({'mode':mode,'frame':frame,'subframe':subframe,'geometry':geometry})
        save()
    expressions.use_action('generate_motion');scene.frame_set(60,subframe=.5)
    previous=expressions.state()
    try:
        with expressions.manual():
            expressions.reset();raise RuntimeError('intentional caller failure')
    except RuntimeError:pass
    check('manual context restores actions and subframe pose after caller failure',expressions.state()==previous)
    check('40 cm camera and 35 cm target plane retained',(bpy.data.objects['RenderCamera'].location-Vector((0,-.4,0))).length<1e-7 and abs(bpy.data.objects['FixationTarget'].location.y+.35)<1e-6)
    save('PASS' if all(c['passed'] for c in checks) else 'FAIL')
    print('MILESTONE3_FINAL_AUDIT',sum(c['passed'] for c in checks),'PASS',sum(not c['passed'] for c in checks),'FAIL',time.perf_counter()-started,flush=True)
    if not all(c['passed'] for c in checks):raise RuntimeError('M3 audit has failures; see report')


if __name__=='__main__':main()
