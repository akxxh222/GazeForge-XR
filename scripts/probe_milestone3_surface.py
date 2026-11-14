"""Outer-shell surface and nonadjacent-triangle intersection diagnostics."""
import json
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

_selection_cache={}
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from wrapper import eyes,lids,expressions
from probe_blink_closure import visible_grid
from probe_gaze_lid_rig import attachment_metrics


def outer_tree(side,with_geometry=False):
    obj=bpy.data.objects['Collision_Eye_'+side].evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=obj.to_mesh()
    mesh.calc_loop_triangles()
    points=np.array([obj.matrix_world@v.co for v in mesh.vertices])
    triangles=np.array([t.vertices[:] for t in mesh.loop_triangles],np.int32)
    tree=BVHTree.FromPolygons(points.tolist(),triangles.tolist(),all_triangles=True)
    obj.to_mesh_clear()
    return (tree,points,triangles) if with_geometry else tree


def edge_crosses_triangle(a,b,t):
    direction=b-a
    edge1,edge2=t[1]-t[0],t[2]-t[0]
    cross=np.cross(direction,edge2)
    determinant=np.dot(edge1,cross)
    if abs(determinant)<1e-17:return False
    inverse=1/determinant
    offset=a-t[0]
    u=np.dot(offset,cross)*inverse
    q=np.cross(offset,edge1)
    v=np.dot(direction,q)*inverse
    distance=np.dot(edge2,q)*inverse
    return 1e-6<distance<1-1e-6 and u>1e-6 and v>1e-6 and u+v<1-1e-6


def surface_metrics(self_test=True,eye_triangle_test=False):
    head=bpy.data.objects['GNM_skin']
    evaluated=head.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=evaluated.to_mesh()
    mesh.calc_loop_triangles()
    flat=np.empty(len(mesh.vertices)*3,np.float32)
    mesh.vertices.foreach_get('co',flat)
    matrix=np.array(evaluated.matrix_world)
    p=flat.reshape(-1,3).astype(np.float64)@matrix[:3,:3].T+matrix[:3,3]
    signature=(head.as_pointer(),len(mesh.vertices))
    if signature not in _selection_cache:
        group_ids={s:head.vertex_groups['Collision lid '+s].index for s in ('L','R')}
        selected={s:[] for s in ('L','R')}
        for vertex in mesh.vertices:
            for item in vertex.groups:
                if item.weight>.999:
                    for side,index in group_ids.items():
                        if item.group==index:selected[side].append(vertex.index)
        _selection_cache[signature]=selected
    selected=_selection_cache[signature]
    clearance={}
    for side,indices in selected.items():
        tree=outer_tree(side)
        distances=[]
        for index in indices:
            near,normal,face,distance=tree.find_nearest(Vector(p[index]))
            distances.append(float((Vector(p[index])-near).dot(normal)))
        clearance[side]={'vertices':len(indices),'min_signed_distance_m':min(distances),
                          'inside_beyond_30um':sum(d<-.00003 for d in distances),'within_30um_contact':sum(d<.00003 for d in distances)}
    result={'outer_shell':clearance}
    if self_test:
        mask=np.zeros(len(p),bool)
        mask[selected['L']+selected['R']]=True
        flat_tri=np.empty(len(mesh.loop_triangles)*3,np.int32)
        mesh.loop_triangles.foreach_get('vertices',flat_tri)
        tris=flat_tri.reshape(-1,3)
        tris=tris[np.all(mask[tris],axis=1)]
        used=np.unique(tris)
        inverse=np.full(len(p),-1,np.int32);inverse[used]=np.arange(len(used))
        tree=BVHTree.FromPolygons(p[used].tolist(),inverse[tris].tolist(),all_triangles=True,epsilon=0.)
        candidates=tree.overlap(tree)
        triangle_sets=[set(t) for t in tris]
        intersections=[]
        excursions=[]
        for i,j in candidates:
            if i>=j or not triangle_sets[i].isdisjoint(triangle_sets[j]):continue
            a,b=p[tris[i]],p[tris[j]]
            if any(edge_crosses_triangle(t[k],t[(k+1)%3],u) for t,u in [(a,b),(b,a)] for k in range(3)):
                intersections.append([int(i),int(j)])
                def plane_dist(t,u):
                    normal=np.cross(t[1]-t[0],t[2]-t[0])
                    normal/=max(np.linalg.norm(normal),1e-30)
                    return float(np.max(np.abs((u-t[0])@normal)))
                excursions.append(max(plane_dist(a,b),plane_dist(b,a)))
        result['surface_nonadjacent_crossing_pairs']=len(intersections)
        result['crossing_examples']=intersections[:12]
        result['max_crossing_plane_excursion_m']=max(excursions,default=0.)
        result['crossings_beyond_30um']=sum(d>.00003 for d in excursions)
        result['tested_triangles']=len(tris)
    if eye_triangle_test:
        result['eye_triangle_crossing_pairs']={}
        for side in ('L','R'):
            ocular,ep,et=outer_tree(side,with_geometry=True)
            crossings=0
            for a,b in tree.overlap(ocular):
                t,u=p[tris[a]],ep[et[b]]
                if any(edge_crosses_triangle(v[k],v[(k+1)%3],w) for v,w in [(t,u),(u,t)] for k in range(3)):crossings+=1
            result['eye_triangle_crossing_pairs'][side]=crossings
    evaluated.to_mesh_clear()
    return result


def closure_visibility(side,columns=81,rows=81):
    # The visible anatomy comprises native skin and opaque moist margins.
    # Preserve the skin-only result separately so auxiliary coverage is explicit.
    from probe_blink_closure import eye_tree
    deps=bpy.context.evaluated_depsgraph_get()
    objects=[bpy.data.objects['GNM_skin']]+[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render and o.name.startswith(('Mucosal_rim_','Lid_caruncle_','Lid_waterline_','Lid_commissure_'))]
    trees=[BVHTree.FromObject(o,deps) for o in objects]
    eye=eye_tree(side);center=bpy.data.objects['Eye_'+side].matrix_world.translation
    visible=[]
    for x in np.linspace(center.x-.016,center.x+.016,columns):
        for z in np.linspace(center.z-.012,center.z+.012,rows):
            origin=Vector((x,-.2,z));direction=Vector((0,1,0))
            e=eye.ray_cast(origin,direction)
            if e[0] is None:continue
            hits=[t.ray_cast(origin,direction) for t in trees]
            distance=min((h[3] for h in hits if h[0] is not None),default=float('inf'))
            if e[3]+1e-6<distance:visible.append([float(x),float(z)])
    return {'visible_eye_rays':len(visible),'visible_xz_m':visible,'grid':[columns,rows]}


def main():
    folder=ROOT/'work/milestone3/final'
    bpy.ops.wm.open_mainfile(filepath=str(folder/'IRISX_MILESTONE3.blend'),use_scripts=False)
    rows=[]
    with expressions.manual():
        for h,v,opening in [(0,0,1),(0,0,.5),(0,0,0),(0,1,.5),(0,1,0),(0,-1,.5),(0,-1,0)]:
            eyes.move(h,v)
            lids.set_opening(opening)
            row={'h':h,'v':v,'opening':opening,**surface_metrics(),**attachment_metrics()}
            if opening==0:
                row['skin_only_visible_eye_samples']={s:visible_grid(s,81,81)['visible_eye_rays'] for s in ('L','R')}
                row['visible_eye_samples']={s:closure_visibility(s)['visible_eye_rays'] for s in ('L','R')}
            rows.append(row)
            print('SURFACE_PROBE',json.dumps(row),flush=True)
    (folder/'surface_probe.json').write_text(json.dumps(rows,indent=2)+'\n')


if __name__=='__main__':main()
