"""Finalize native eyelids with anchored corners and live collision/bindings."""
import hashlib
import json
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from wrapper import eyes,lids,expressions,live_surface_binding,ocular_deform
from build_gnm_blink_prototype import surface
from wrapper.lid_anatomy import _roots
from build_gaze_lid_rig import clamp_action


def outer_proxy(eye,outer):
    ids=np.array([a.value for a in eye.data.attributes['gnm_vertex_id'].data])
    faces=np.array([p.vertices[:] for p in eye.data.polygons])
    faces=faces[np.all(outer[ids[faces]],axis=1)]
    used=np.unique(faces)
    inverse=np.full(len(ids),-1,np.int32)
    inverse[used]=np.arange(len(used))
    mesh=bpy.data.meshes.new(eye.name+' | native outer collision shell')
    mesh.from_pydata([eye.data.vertices[int(i)].co[:] for i in used],[],inverse[faces].tolist())
    mesh.update()
    edges=np.sort(np.concatenate([inverse[faces[:,[i,(i+1)%4]]] for i in range(4)]),axis=1)
    _,counts=np.unique(edges,axis=0,return_counts=True)
    if not np.all(counts==2):raise ValueError('Native exterior eye shell must be watertight')
    obj=bpy.data.objects.new('Collision_'+eye.name,mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent=eye
    obj.matrix_parent_inverse=Matrix.Identity(4)
    obj.matrix_basis=Matrix.Identity(4)
    sub=obj.modifiers.new('Native exterior subdivision','SUBSURF')
    sub.levels=2
    sub.render_levels=2
    obj.hide_render=True
    obj.hide_set(True)
    obj['collision_shell']='Closed native eye_exteriors semantic surface; no foreign geometry.'
    return obj


def add_mucosal_rims(head,landmarks):
    """A 0.24-mm moist tissue margin at the native eyelid silhouette."""
    surface=head.evaluated_get(bpy.context.evaluated_depsgraph_get())
    tissue=bpy.data.materials['Lid mucosa | restrained pink tissue']
    for side in ('L','R'):
        upper,lower=[_roots('Lashes_'+lid+'_'+side) for lid in ('upper','lower')]
        low,high=landmarks[side]
        rows=[low]+upper.tolist()+[high]+lower[::-1].tolist()
        curve=bpy.data.curves.new('Native wet lid margin '+side,'CURVE')
        curve.dimensions='3D';curve.resolution_u=1
        curve.bevel_depth=.00012;curve.bevel_resolution=2
        spline=curve.splines.new('POLY');spline.points.add(len(rows)-1)
        for point,p in zip(spline.points,rows):
            ok,hit,normal,index=surface.ray_cast(Vector((p[0],-.2,p[2])),Vector((0,1,0)))
            q=hit if ok and abs(hit.y-p[1])<.003 else Vector(p)
            point.co=(*tuple(q+Vector((0,-.00008,0))),1)
        spline.use_cyclic_u=True
        obj=bpy.data.objects.new('Mucosal_rim_'+side,curve)
        bpy.context.scene.collection.objects.link(obj)
        curve.materials.append(tissue)
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
        bpy.ops.object.convert(target='MESH')
        obj=bpy.context.object
        obj['expression_binding']='Native silhouette mucosal rim; bind to live skin.'
        obj['anatomy']='0.24-mm thick moist tarsal margin; opaque tissue, not a closure mask.'


def add_canthal_tissue(head,landmarks,proxies):
    """Complete the nasal caruncle and small temporal lid commissure."""
    tissue=bpy.data.materials['Lid mucosa | restrained pink tissue'].copy()
    tissue.name='Native canthal mucosa | restrained warm tissue'
    shader=tissue.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value=(.18,.055,.035,1)
    shader.inputs['Roughness'].default_value=.48
    shader.inputs['Subsurface Weight'].default_value=.025
    shader.inputs['Specular IOR Level'].default_value=.16
    for side,sign,proxy in zip(('L','R'),(1,-1),proxies):
        old=bpy.data.objects['Lid_caruncle_'+side];old.hide_render=True;old.hide_set(True)
        low,high=landmarks[side]
        nasal,temporal=(low,high) if side=='L' else (high,low)
        evaluated=proxy.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
        tree=BVHTree.FromPolygons([evaluated.matrix_world@v.co for v in mesh.vertices],[p.vertices[:] for p in mesh.polygons]);evaluated.to_mesh_clear()
        for kind,point,radii,dx in [('caruncle',nasal,(.0011,.00032,.00060),sign*.0008),('commissure',temporal,(.00055,.00020,.00045),-sign*.00035)]:
            center=Vector(point)+Vector((dx,-.00035,0))
            bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=(0,0,0))
            obj=bpy.context.object;obj.name='Lid_'+kind+'_'+side+'_native'
            points=np.array([tuple(center+Vector(tuple(v.co[j]*radii[j] for j in range(3)))) for v in obj.data.vertices])
            # Conform the thin canthal tissue to the curved anterior shell.
            # A rigid ellipsoid cleared as a whole floats at the steep canthus.
            # Preserve its X/Z silhouette and depth ordering with a soft minimum.
            for index,q in enumerate(points):
                hit,n,face,d=tree.ray_cast(Vector((q[0],-.1,q[2])),Vector((0,1,0)))
                if hit is not None:
                    front=float(hit.y)-.00028
                    delta=front-q[1]
                    points[index,1]=front-.5*(delta+(delta*delta+4*.00012**2)**.5)
            obj.data.vertices.foreach_set('co',points.astype(np.float32).ravel())
            obj.data.update();obj.data.materials.append(tissue if kind=='caruncle' else head.data.materials[0])
            for face in obj.data.polygons:face.use_smooth=True
            obj['expression_binding']='Native canthal anatomy, live skin binding.'
            obj['rigid_anatomy_binding']=True
            obj['binding_anchor']=list(point)
            obj['anatomy']='Small nasal caruncle / temporal lid commissure; fitted outside actual native eye shell.'


def match_commissure_uv(head,vertices,triangles,tree):
    evaluated=head.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh();mesh.calc_loop_triangles()
    uv=mesh.uv_layers.active
    uv_triangles=np.array([[uv.data[i].uv[:] for i in t.loops] for t in mesh.loop_triangles])
    name=uv.name;evaluated.to_mesh_clear()
    for obj in bpy.context.scene.objects:
        if not obj.name.startswith('Lid_commissure_') or obj.hide_render:continue
        mapped=[]
        for vertex in obj.data.vertices:
            near,normal,index,distance=tree.find_nearest(vertex.co)
            a,b,c=[Vector(p) for p in vertices[triangles[index]]]
            w=np.array(barycentric_transform(near,a,b,c,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))))
            mapped.append(w@uv_triangles[index])
        layer=obj.data.uv_layers.active or obj.data.uv_layers.new(name=name)
        layer.name=name
        for loop in obj.data.loops:layer.data[loop.index].uv=mapped[loop.vertex_index]
        obj['uv_provenance']='Nearest native evaluated GNM triangle, barycentric corner UV transfer; original head UVs unchanged.'


def author_actions(scene,head,rig,target):
    owners=[head.data.shape_keys,rig,target]
    review=[o.animation_data.action for o in owners]
    for action in review:action.use_fake_user=True
    # Retain the tested six-second combined-gaze action as generate_motion.
    library={'generate_motion':[a.name for a in review]}
    for mode,sign in [('left',-1),('right',1)]:
        for owner in owners:owner.animation_data.action=None
        for frame,h,opening,brow in [(1,0,1,0),(18,.25*sign,1,.08),(36,sign,1,.15),
                                     (66,sign,1,.15),(69,sign,0,.15),(75,sign,1,.15),
                                     (108,sign,1,.08),(132,0,1,0),(144,0,1,0)]:
            eyes.move(h,0)
            lids.set_opening(opening)
            expressions.set_brows(brow)
            target.keyframe_insert(data_path='location',frame=frame)
            for side in ('L','R'):
                rig.pose.bones['eye.'+side].keyframe_insert(data_path='rotation_quaternion',frame=frame)
                for key in ['Blink.'+side,'Brow.Raise.'+side]:head.data.shape_keys.key_blocks[key].keyframe_insert(data_path='value',frame=frame)
        names=[]
        for owner,label in zip(owners,['lids and brows','eyes','target']):
            clamp_action(owner,f'IrisX | {mode} | {label}')
            owner.animation_data.action.use_fake_user=True
            names.append(owner.animation_data.action.name)
        library[mode]=names
    for owner,action in zip(owners,review):owner.animation_data.action=action
    scene['expression_actions']=json.dumps(library)
    scene.frame_set(1)
    return library


def main():
    source=ROOT/'work/milestone3/gaze_lids/IRISX_GAZE_LIDS_RIG.blend'
    bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
    scene=bpy.context.scene
    scene.frame_set(1)
    head=bpy.data.objects['GNM_skin']
    with np.load(ROOT/'assets/gnm/gnm_head.npz',allow_pickle=False) as data:
        names=data['vertex_group_names'].tolist()
        masks={name:data['vertex_groups'][i]>0 for i,name in enumerate(names)}
        template=data['template_vertex_positions']
    ids=np.array([a.value for a in head.data.attributes['gnm_vertex_id'].data])
    base=np.array([v.co[:] for v in head.data.vertices],np.float64)
    corners={}
    landmarks={}
    for side,sign in [('L',1),('R',-1)]:
        candidates=np.flatnonzero(masks['skin_exterior']&masks['eye_sockets']&(template[:,0]*sign>0))
        markers=candidates[[np.argmin(template[candidates,0]),np.argmax(template[candidates,0])]]
        indices=[int(np.flatnonzero(ids==v)[0]) for v in markers]
        key=head.data.shape_keys.key_blocks['Blink.'+side]
        delta=np.array([p.co[:] for p in key.data])-base
        original=delta.copy()
        left,right=sorted(indices,key=lambda i:base[i,0])
        landmarks[side]=(base[left].tolist(),base[right].tolist())
        # Values remain editable control channels; deformation runs after
        # subdivision so the narrow closing seam cannot overshoot its map.
        delta=np.zeros_like(base)
        key.data.foreach_set('co',(base+delta).astype(np.float32).ravel())
        corners[side]={'native_vertex_ids':markers.tolist(),'head_vertex_indices':indices,
                       'before_displacement_m':[float(np.linalg.norm(original[i])) for i in indices],
                       'after_displacement_m':[float(np.linalg.norm(delta[i])) for i in indices]}
    proxies=[]
    for side,label in [('L','left_orbital_region'),('R','right_orbital_region')]:
        proxy=outer_proxy(bpy.data.objects['Eye_'+side],masks['eye_exteriors'])
        proxies.append(proxy.name)
        group=head.vertex_groups.new(name='Collision lid '+side)
        selection=np.flatnonzero(masks[label][ids]&masks['skin_exterior'][ids])
        group.add(selection.tolist(),1.,'REPLACE')
    ocular_deform.build(head,[bpy.data.objects[name] for name in proxies],landmarks,{s:(_roots('Lashes_upper_'+s).tolist(),_roots('Lashes_lower_'+s).tolist()) for s in ('L','R')})
    head.data.update()
    bpy.context.view_layer.update()
    vertices,triangles,_=surface(head)
    tree=BVHTree.FromPolygons(vertices.tolist(),triangles.tolist(),all_triangles=True)
    add_mucosal_rims(head,landmarks)
    add_canthal_tissue(head,landmarks,[bpy.data.objects[name] for name in proxies])
    match_commissure_uv(head,vertices,triangles,tree)
    binding=live_surface_binding.node_group(head)
    rigid_binding=live_surface_binding.node_group(head,translation_only=True)
    attachments=[]
    detail_clearance=None
    for obj in list(scene.objects):
        if obj.hide_render:continue
        if obj.get('expression_binding'):
            attachments.append(live_surface_binding.bind(obj,head,rigid_binding if obj.get('rigid_anatomy_binding') else binding,vertices,triangles,tree))
            if detail_clearance is None:detail_clearance=ocular_deform.build(obj,[bpy.data.objects[name] for name in proxies],{}, {},clearance_only=True)
            else:obj.modifiers.new('Detail ocular clearance','NODES').node_group=detail_clearance
    rig=bpy.data.objects['GazeRig']
    target=bpy.data.objects['FixationTarget']
    actions=author_actions(scene,head,rig,target)
    scene.camera=bpy.data.objects['RenderCamera']
    scene['milestone3_status']='Rig checkpoint: relaxed native lids, ordered ocular clearance, live detail binding, three action bundles. Acceptance evidence: tests/milestone3/final/.'
    scene['canthus_landmarks']=json.dumps(corners)
    scene['collision_contact_tolerance_m']=.00003
    note=bpy.data.texts.new('IRISX_MILESTONE3_RIG.txt')
    note.write('Native GNM rig derivative, Apache-2.0. Original Basis/UVs preserved. Blinks use locally anchored native socket landmarks. Post-subdivision monotone blink map and depth-ordered soft ocular clearance use closed native eye_exteriors proxies. Live Geometry Nodes detail binding samples evaluated head triangles. Left/right/generate_motion action bundles retained. No Python playback handlers. Existing skin/iris/hair credits remain applicable.\n')
    folder=ROOT/'work/milestone3/final'
    folder.mkdir(exist_ok=True)
    path=folder/'IRISX_MILESTONE3.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    receipt={'scene':str(path.relative_to(ROOT)),'scene_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
             'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'module_sha256':{name:hashlib.sha256((ROOT/'wrapper'/name).read_bytes()).hexdigest() for name in ['ocular_deform.py','live_surface_binding.py','expressions.py','lids.py','eyes.py']},
             'corners':corners,'collision_proxies':proxies,'contact_offset_m':.00008,'attachments':attachments,'actions':actions,
             'status':'Final candidate; acceptance audit/render review pending.'}
    (folder/'rig.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('MILESTONE3_FINAL_CANDIDATE',json.dumps(receipt),flush=True)


if __name__=='__main__':main()
