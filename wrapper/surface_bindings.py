"""Bind small facial attachments to native head shape-key surfaces.

Rest-triangle barycentrics carry roots; normal transport carries fiber shape.
Endpoint deltas blend with the same shape weights as the skin. Intermediate
root error must be measured for each rig; this is not a collision solver.
"""
import bpy
import numpy as np
from mathutils import Vector
from mathutils.geometry import barycentric_transform


def key_driver(owner,path,head,key_name):
    driver=owner.driver_add(path).driver
    driver.type='SCRIPTED'
    variable=driver.variables.new()
    variable.name='weight'
    variable.type='SINGLE_PROP'
    variable.targets[0].id_type='KEY'
    variable.targets[0].id=head.data.shape_keys
    variable.targets[0].data_path=f'key_blocks["{key_name}"].value'
    driver.expression='weight'


def transported(point,near,normal,triangle,rest,pose):
    a,b,c=[Vector(p) for p in rest[triangle]]
    da,db,dc=[Vector(p) for p in pose[triangle]]
    target=barycentric_transform(near,a,b,c,da,db,dc)
    rotation=normal.rotation_difference((db-da).cross(dc-da).normalized())
    return target+rotation@(point-near)


def bind_curves(obj,head,tree,triangles,rest,poses):
    data=obj.data
    raw=np.empty(len(data.points)*3,np.float32)
    data.attributes['position'].data.foreach_get('vector',raw)
    raw=raw.reshape(-1,3)
    deltas={name:np.zeros_like(raw) for name in poses}
    inverse=obj.matrix_world.inverted()
    for curve in data.curves:
        start=curve.first_point_index
        root=obj.matrix_world@Vector(raw[start])
        near,normal,index,distance=tree.find_nearest(root)
        triangle=triangles[index]
        for name,pose in poses.items():
            a,b,c=[Vector(p) for p in rest[triangle]]
            da,db,dc=[Vector(p) for p in pose[triangle]]
            target=barycentric_transform(near,a,b,c,da,db,dc)
            rotation=normal.rotation_difference((db-da).cross(dc-da).normalized())
            for i in range(start,start+curve.points_length):
                p=obj.matrix_world@Vector(raw[i])
                deltas[name][i]=inverse@(target+rotation@(p-near))-Vector(raw[i])
    group=bpy.data.node_groups.new(obj.name+' | expression attachment','GeometryNodeTree')
    group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    nodes,links=group.nodes,group.links
    inputs=nodes.new('NodeGroupInput')
    output=nodes.new('NodeGroupOutput')
    total=None
    for i,(name,delta) in enumerate(deltas.items()):
        attribute=data.attributes.new(f'expression_delta_{i:02d}','FLOAT_VECTOR','POINT')
        attribute.data.foreach_set('vector',delta.ravel())
        get=nodes.new('GeometryNodeInputNamedAttribute')
        get.data_type='FLOAT_VECTOR'
        get.inputs['Name'].default_value=attribute.name
        scale=nodes.new('ShaderNodeVectorMath')
        scale.operation='SCALE'
        weight=nodes.new('ShaderNodeValue')
        weight.name=name
        key_driver(weight.outputs[0],'default_value',head,name)
        links.new(get.outputs['Attribute'],scale.inputs[0])
        links.new(weight.outputs[0],scale.inputs['Scale'])
        if total is None:total=scale.outputs[0]
        else:
            add=nodes.new('ShaderNodeVectorMath')
            add.operation='ADD'
            links.new(total,add.inputs[0])
            links.new(scale.outputs[0],add.inputs[1])
            total=add.outputs[0]
    move=nodes.new('GeometryNodeSetPosition')
    links.new(inputs.outputs['Geometry'],move.inputs['Geometry'])
    links.new(total,move.inputs['Offset'])
    links.new(move.outputs['Geometry'],output.inputs['Geometry'])
    obj.modifiers.new('Native expression attachment','NODES').node_group=group
    obj['expression_binding']='Rest barycentric roots and normal transport, blended by native shape-key weights.'
    return obj


def bind_mesh(obj,head,tree,triangles,rest,poses):
    if obj.type=='CURVE':
        mesh=bpy.data.meshes.new_from_object(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
        new=bpy.data.objects.new(obj.name+'_bound',mesh)
        bpy.context.scene.collection.objects.link(new)
        world=obj.matrix_world.copy()
        new.parent=head
        new.matrix_world=world
        obj.hide_render=True
        obj.hide_set(True)
        obj=new
    obj.shape_key_add(name='Basis')
    inverse=obj.matrix_world.inverted()
    for name,pose in poses.items():
        key=obj.shape_key_add(name=name)
        for i,vertex in enumerate(obj.data.vertices):
            p=obj.matrix_world@vertex.co
            near,normal,index,distance=tree.find_nearest(p)
            key.data[i].co=inverse@transported(p,near,normal,triangles[index],rest,pose)
        key_driver(key,'value',head,name)
    obj['expression_binding']='Rest barycentric surface and normal transport, driven by native shape keys.'
    return obj
