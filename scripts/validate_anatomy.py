"""Check eyelid/canthal clearance, full closure and packed texture provenance."""
import hashlib,json,sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from wrapper import eyes,lids,expressions
def tree(obj):
    obj=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=obj.to_mesh()
    result=BVHTree.FromPolygons([obj.matrix_world@v.co for v in mesh.vertices],[list(p.vertices) for p in mesh.polygons])
    obj.to_mesh_clear();return result
def main():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'scene.blend'),use_scripts=False)
    checks=[];poses=[]
    def check(name,value):checks.append({'test':name,'passed':bool(value)})
    allowed={hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'textures').rglob('*.png')}
    packed=[]
    for image in bpy.data.images:
        if image.source!='FILE':continue
        digest=hashlib.sha256(image.packed_file.data).hexdigest() if image.packed_file else None
        check(image.name+' packed exported texture',digest in allowed)
        packed.append({'name':image.name,'sha256':digest})
    with expressions.manual():
        for h,v in [(0,0),(-1,0),(1,0),(0,1),(0,-1)]:
            for opening in (1.,.5,0.):
                expressions.reset();eyes.move(h,v);lids.set_opening(opening);bpy.context.view_layer.update()
                row={'h':h,'v':v,'opening':opening,'minimum_detail_clearance_m':{},'uncovered_closed_eye_rays':{}}
                for side in ('L','R'):
                    outer=tree(bpy.data.objects['Collision_Eye_'+side]);distances=[]
                    for obj in bpy.context.scene.objects:
                        if obj.hide_render or not obj.name.startswith(('Lid_lashes_','Lid_caruncle_','Lid_commissure_','Mucosal_rim_','Lid_waterline_','Lid_tear_film_')) or not obj.name.endswith((side,'_'+side+'_native','_'+side+'_bound')):continue
                        evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
                        if obj.type=='CURVES':points=[obj.matrix_world@p.vector for p in evaluated.data.attributes['position'].data]
                        else:
                            mesh=evaluated.to_mesh();points=[obj.matrix_world@p.co for p in mesh.vertices];evaluated.to_mesh_clear()
                        for point in points:
                            near,n,_,_=outer.find_nearest(point);distances.append((point-near).dot(n))
                    row['minimum_detail_clearance_m'][side]=min(distances)
                    check(f'{h},{v},{opening} {side} lashes and canthi clear eyes',min(distances)>-.00003)
                    if opening==0:
                        anatomy=[bpy.data.objects['GNM_skin']]+[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render and o.name.startswith(('Mucosal_rim_','Lid_caruncle_','Lid_waterline_','Lid_commissure_'))]
                        trees=[tree(o) for o in anatomy];eye=tree(bpy.data.objects['Eye_'+side]);center=bpy.data.objects['Eye_'+side].matrix_world.translation
                        count=0
                        for x in np.linspace(center.x-.016,center.x+.016,81):
                            for z in np.linspace(center.z-.012,center.z+.012,81):
                                origin=Vector((x,-.2,z));direction=Vector((0,1,0));hit=eye.ray_cast(origin,direction)
                                if hit[0] is None:continue
                                hits=[t.ray_cast(origin,direction) for t in trees]
                                depth=min((p[3] for p in hits if p[0] is not None),default=float('inf'))
                                count+=hit[3]+1e-6<depth
                        row['uncovered_closed_eye_rays'][side]=int(count)
                        check(f'{h},{v} {side} full blink closes eye',count==0)
                poses.append(row)
    check('original 64000 strand groom',len(bpy.data.objects['IrisX_original_groom'].data.curves)==64000)
    check('no imported demo groom remains',not any(o.name.startswith('Public_groom') for o in bpy.data.objects))
    result={'status':'PASS' if all(r['passed'] for r in checks) else 'FAIL','passed':sum(r['passed'] for r in checks),'failed':sum(not r['passed'] for r in checks),
        'scene_sha256':hashlib.sha256((ROOT/'scene.blend').read_bytes()).hexdigest(),'checks':checks,'poses':poses,'packed_images':packed,
        'scope':'15 manual gaze/opening poses, full helper-point clearance, 81x81 frontal closure rays, original groom and packed texture allowlist.'}
    folder=ROOT/'runtime/audit';folder.mkdir(parents=True,exist_ok=True);(folder/'anatomy.json').write_text(json.dumps(result,indent=2)+'\n')
    print('ANATOMY_CHECKS',result['status'],result['passed'],result['failed'],flush=True)
    if result['failed']:raise SystemExit(1)
if __name__=='__main__':main()
