"""Native GNM blink keys, barycentric lid attachments and editable timeline.

Milestone 3 prototype. Requires visual/intermediate-pose clearance acceptance;
does not mark the wider material or movement milestone complete.
"""
import hashlib
import json
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from wrapper import eyes,lids
from render_device import configure


def driver(owner,path,head,side):
    f=owner.driver_add(path)
    d=f.driver
    d.type='SCRIPTED'
    v=d.variables.new()
    v.name='blink'
    v.type='SINGLE_PROP'
    v.targets[0].id_type='KEY'
    v.targets[0].id=head.data.shape_keys
    v.targets[0].data_path='key_blocks["Blink.'+side+'"].value'
    d.expression='blink'


def surface(head):
    obj=head.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=obj.to_mesh()
    mesh.calc_loop_triangles()
    p=np.array([obj.matrix_world@v.co for v in mesh.vertices],np.float32)
    tris=np.array([t.vertices[:] for t in mesh.loop_triangles],np.int32)
    polygons=np.array([p.vertices[:] for p in mesh.polygons],np.int32)
    obj.to_mesh_clear()
    return p,tris,polygons


def bind_curves(obj,head,tree,triangles,positions):
    data=obj.data
    raw=np.empty(len(data.points)*3,np.float32)
    data.attributes['position'].data.foreach_get('vector',raw)
    raw=raw.reshape(-1,3)
    delta={s:np.zeros_like(raw) for s in ('L','R')}
    inverse=obj.matrix_world.inverted()
    for curve in data.curves:
        start=curve.first_point_index
        root=obj.matrix_world@Vector(raw[start])
        near,normal,index,distance=tree.find_nearest(root)
        tri=triangles[index]
        a,b,c=[Vector(p) for p in positions['rest'][tri]]
        for side in ('L','R'):
            da,db,dc=[Vector(p) for p in positions[side][tri]]
            target=barycentric_transform(near,a,b,c,da,db,dc)
            normal2=(db-da).cross(dc-da).normalized()
            rotation=normal.rotation_difference(normal2)
            for i in range(start,start+curve.points_length):
                world=obj.matrix_world@Vector(raw[i])
                fitted=target+rotation@(world-near)
                delta[side][i]=inverse@fitted-Vector(raw[i])
    group=bpy.data.node_groups.new(obj.name+' | lid attachment','GeometryNodeTree')
    group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    nodes,links=group.nodes,group.links
    inputs=nodes.new('NodeGroupInput')
    output=nodes.new('NodeGroupOutput')
    add=nodes.new('ShaderNodeVectorMath')
    add.operation='ADD'
    for i,side in enumerate(('L','R')):
        attr=data.attributes.new('blink_delta_'+side,'FLOAT_VECTOR','POINT')
        attr.data.foreach_set('vector',delta[side].ravel())
        get=nodes.new('GeometryNodeInputNamedAttribute')
        get.data_type='FLOAT_VECTOR'
        get.inputs['Name'].default_value=attr.name
        scale=nodes.new('ShaderNodeVectorMath')
        scale.operation='SCALE'
        weight=nodes.new('ShaderNodeValue')
        weight.name='Blink.'+side
        weight.outputs[0].default_value=0
        driver(weight.outputs[0],'default_value',head,side)
        links.new(get.outputs['Attribute'],scale.inputs[0])
        links.new(weight.outputs[0],scale.inputs['Scale'])
        links.new(scale.outputs[0],add.inputs[i])
    move=nodes.new('GeometryNodeSetPosition')
    links.new(inputs.outputs['Geometry'],move.inputs['Geometry'])
    links.new(add.outputs[0],move.inputs['Offset'])
    links.new(move.outputs['Geometry'],output.inputs['Geometry'])
    mod=obj.modifiers.new('Native lid attachment','NODES')
    mod.node_group=group
    obj['blink_binding']='Barycentric native subdivided lid surface; per-strand root displacement and normal rotation, linear shape interpolation.'


def bind_mesh(obj,head,tree,triangles,positions):
    if obj.type=='CURVE':
        mesh=bpy.data.meshes.new_from_object(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
        new=bpy.data.objects.new(obj.name+'_bound',mesh)
        bpy.context.scene.collection.objects.link(new)
        new.matrix_world=obj.matrix_world.copy()
        new.parent=head
        obj.hide_render=True
        obj.hide_set(True)
        obj=new
    obj.shape_key_add(name='Basis')
    inverse=obj.matrix_world.inverted()
    for side in ('L','R'):
        key=obj.shape_key_add(name='Blink.'+side)
        for i,v in enumerate(obj.data.vertices):
            world=obj.matrix_world@v.co
            near,n,index,distance=tree.find_nearest(world)
            tri=triangles[index]
            a,b,c=[Vector(p) for p in positions['rest'][tri]]
            da,db,dc=[Vector(p) for p in positions[side][tri]]
            target=barycentric_transform(near,a,b,c,da,db,dc)
            rotation=n.rotation_difference((db-da).cross(dc-da).normalized())
            key.data[i].co=inverse@(target+rotation@(world-near))
        driver(key,'value',head,side)
    obj['blink_binding']='Barycentric native lid surface; keyed displacement/normal transport.'


def main():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/review/lids/IRISX_LIDS_REVIEW.blend'),use_scripts=False)
    scene=bpy.context.scene
    configure()
    scene.cycles.samples=64
    head=bpy.data.objects['GNM_skin']
    source=ROOT/'work/gnm/blink_shapes.npz'
    receipt=json.loads(source.with_suffix('.json').read_text())
    if hashlib.sha256(source.read_bytes()).hexdigest()!=receipt['artifact_sha256']:raise ValueError('Blink input changed')
    ids=np.array([a.value for a in head.data.attributes['gnm_vertex_id'].data])
    with np.load(source,allow_pickle=False) as data:
        for side in ('L','R'):
            key=head.shape_key_add(name='Blink.'+side)
            # The zero-latent semantic wink retains a thin aperture. Endpoint
            # gains are explicit artist corrections, selected using frontal
            # eye-visibility probes and checked in actual Cycles closeups.
            gain={'L':1.16,'R':1.21}[side]
            coords=np.array([p.co[:] for p in head.data.vertices],np.float32)+gain*data['delta_'+side][ids]
            key.data.foreach_set('co',coords.ravel())
            key.slider_min=0
            key.slider_max=1
            head['blink_gain_'+side]=gain
    lids.reset()
    rest,triangles,polygons=surface(head)
    positions={'rest':rest}
    for side in ('L','R'):
        lids.set_opening(0 if side=='L' else 1,0 if side=='R' else 1)
        positions[side],closed_tris,closed_polygons=surface(head)
        # Loop triangulation may choose the other diagonal on a deformed quad.
        # Keep the rest triangles for barycentric binding and verify real
        # polygon connectivity/vertex indexing instead of adaptive diagonals.
        if len(positions[side])!=len(rest) or not np.array_equal(polygons,closed_polygons):
            raise ValueError('Surface topology changed in blink')
    lids.reset()
    tree=BVHTree.FromPolygons(rest.tolist(),triangles.tolist(),all_triangles=True)
    bound=[]
    for obj in list(scene.objects):
        if obj.hide_render:continue
        if obj.type=='CURVES' and obj.name.startswith(('Lid_lashes_','Brow_fibers_')):
            bind_curves(obj,head,tree,triangles,positions)
            bound.append(obj.name)
        elif obj.name.startswith(('Lid_waterline_','Lid_tear_film_','Lid_caruncle_')):
            bind_mesh(obj,head,tree,triangles,positions)
            bound.append(obj.name)
    for side in ('L','R'):
        key=head.data.shape_keys.key_blocks['Blink.'+side]
        for frame,value in [(1,0),(18,0),(21,1),(23,.65),(27,0),(48,0),(51,1),(53,.65),(57,0),(72,0)]:
            key.value=value
            key.keyframe_insert(data_path='value',frame=frame)
    head.data.shape_keys.animation_data.action.name='IrisX | native blink prototype'
    action=head.data.shape_keys.animation_data.action
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for point in curve.keyframe_points:
                        point.handle_left_type='AUTO_CLAMPED'
                        point.handle_right_type='AUTO_CLAMPED'
    scene.render.fps=24
    scene.frame_start=1
    scene.frame_end=72
    scene.frame_set(1)
    eyes.reset()
    scene.camera=bpy.data.objects['RenderCamera']
    scene['milestone3_status']='Blink prototype: native semantic keys and bound lash/brow/waterline geometry. Closure, intermediate clearance and gaze follow remain under review.'
    out=ROOT/'work/milestone3'
    out.mkdir(exist_ok=True)
    path=out/'IRISX_BLINK_PROTOTYPE.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    print('BLINK_PROTOTYPE_SAVED',path,'BOUND',bound,flush=True)
    # Pose diagnostics override the timeline only in this unsaved render copy.
    # The delivered file retains its editable action and neutral frame 1.
    head.data.shape_keys.animation_data.action=None
    scene.camera=bpy.data.objects['Review_eye_closeup']
    records=[]
    for label,opening in [('open',1),('half',.5),('closed',0)]:
        lids.set_opening(opening)
        state=eyes.render(out/(label+'.png'))
        state.update(lids.state())
        state['image_sha256']=hashlib.sha256((out/(label+'.png')).read_bytes()).hexdigest()
        state['view']=label
        records.append(state)
    scene.camera=bpy.data.objects['RenderCamera']
    state=eyes.render(out/'closed_front.png')
    state.update(lids.state())
    state['image_sha256']=hashlib.sha256((out/'closed_front.png').read_bytes()).hexdigest()
    state['view']='closed_front'
    records.append(state)
    (out/'prototype.json').write_text(json.dumps({'scene':str(path.relative_to(ROOT)),'scene_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'source':receipt,'bound_objects':bound,'poses':records,'status':'Initial closure review; not an accepted final motion rig.'},indent=2)+'\n')
    print('BLINK_PROTOTYPE_RENDERED',flush=True)


if __name__=='__main__':main()
