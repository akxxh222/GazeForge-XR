"""Geometry Nodes attachment to the evaluated native head, including collision.

Rest barycentric triangle indices and tangent coordinates bind each fiber root
or small mesh point. The node graph samples the live head vertex positions;
it does not approximate motion by blending captured endpoint displacements.
"""
import bpy
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform


def node_group(head,translation_only=False):
    group=bpy.data.node_groups.new('IrisX | '+('canthal translation attachment' if translation_only else 'live evaluated surface attachment'),'GeometryNodeTree')
    group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    nodes,links=group.nodes,group.links
    source=nodes.new('GeometryNodeObjectInfo')
    source.transform_space='RELATIVE'
    source.inputs['Object'].default_value=head
    source.inputs['As Instance'].default_value=False
    position=nodes.new('GeometryNodeInputPosition')
    def attr(name,kind='FLOAT_VECTOR'):
        get=nodes.new('GeometryNodeInputNamedAttribute')
        get.data_type=kind
        get.inputs['Name'].default_value=name
        return get.outputs['Attribute']
    def vector(operation,a,b=None):
        node=nodes.new('ShaderNodeVectorMath')
        node.operation=operation
        links.new(a,node.inputs[0])
        if b is not None:links.new(b,node.inputs['Scale'] if operation=='SCALE' else node.inputs[1])
        return node.outputs[0]
    def separate(socket):
        node=nodes.new('ShaderNodeSeparateXYZ')
        links.new(socket,node.inputs[0])
        return list(node.outputs)
    points=[]
    for i in range(3):
        sample=nodes.new('GeometryNodeSampleIndex')
        sample.data_type='FLOAT_VECTOR'
        sample.domain='POINT'
        links.new(source.outputs['Geometry'],sample.inputs['Geometry'])
        links.new(position.outputs[0],sample.inputs['Value'])
        links.new(attr('bind_index_'+str(i),'INT'),sample.inputs['Index'])
        points.append(sample.outputs['Value'])
    a,b,c=points
    tangent=vector('NORMALIZE',vector('SUBTRACT',b,a))
    normal=vector('NORMALIZE',vector('CROSS_PRODUCT',vector('SUBTRACT',b,a),vector('SUBTRACT',c,a)))
    bitangent=vector('CROSS_PRODUCT',normal,tangent)
    bary=separate(attr('bind_barycentric'))
    offset=separate(attr('bind_frame_offset'))
    terms=[vector('SCALE',p,w) for p,w in zip(points,bary)]
    terms += [attr('bind_frame_offset')] if translation_only else [vector('SCALE',p,w) for p,w in zip([tangent,bitangent,normal],offset)]
    result=terms[0]
    for term in terms[1:]:result=vector('ADD',result,term)
    start=nodes.new('NodeGroupInput')
    end=nodes.new('NodeGroupOutput')
    move=nodes.new('GeometryNodeSetPosition')
    links.new(start.outputs['Geometry'],move.inputs['Geometry'])
    links.new(result,move.inputs['Position'])
    links.new(move.outputs['Geometry'],end.inputs['Geometry'])
    return group


def bind(obj,head,group,vertices,triangles,tree):
    world=obj.matrix_world.copy()
    if obj.type=='CURVES':
        raw=np.empty(len(obj.data.points)*3,np.float32)
        obj.data.attributes['position'].data.foreach_get('vector',raw)
        points=np.array([world@Vector(p) for p in raw.reshape(-1,3)],np.float32)
        for mod in list(obj.modifiers):obj.modifiers.remove(mod)
        obj.data.attributes['position'].data.foreach_set('vector',points.ravel())
        clusters=[range(c.first_point_index,c.first_point_index+c.points_length) for c in obj.data.curves]
    elif obj.type=='MESH':
        obj.shape_key_clear()
        points=np.array([world@v.co for v in obj.data.vertices],np.float32)
        obj.data.vertices.foreach_set('co',points.ravel())
        clusters=[range(len(points))] if obj.get('rigid_anatomy_binding') else [range(i,i+1) for i in range(len(points))]
        for mod in list(obj.modifiers):obj.modifiers.remove(mod)
    else:raise TypeError('Only native curves or meshes are supported')
    obj.parent=head
    obj.matrix_world=Matrix.Identity(4)
    count=len(points)
    indices=np.zeros((count,3),np.int32)
    weights=np.zeros((count,3),np.float32)
    offsets=np.zeros((count,3),np.float32)
    for cluster in clusters:
        near,normal,index,distance=tree.find_nearest(Vector(obj['binding_anchor'] if obj.get('rigid_anatomy_binding') else points[cluster.start]))
        triangle=triangles[index]
        a,b,c=[Vector(p) for p in vertices[triangle]]
        tangent=(b-a).normalized()
        normal=(b-a).cross(c-a).normalized()
        bitangent=normal.cross(tangent)
        bary=barycentric_transform(near,a,b,c,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
        for i in cluster:
            offset=Vector(points[i])-near
            indices[i]=triangle
            weights[i]=bary
            offsets[i]=tuple(offset) if obj.get('rigid_anatomy_binding') else (offset.dot(tangent),offset.dot(bitangent),offset.dot(normal))
    for i in range(3):
        attribute=obj.data.attributes.new('bind_index_'+str(i),'INT','POINT')
        attribute.data.foreach_set('value',indices[:,i])
    for name,array in [('bind_barycentric',weights),('bind_frame_offset',offsets)]:
        attribute=obj.data.attributes.new(name,'FLOAT_VECTOR','POINT')
        attribute.data.foreach_set('vector',array.ravel())
    obj.modifiers.new('Live native surface attachment','NODES').node_group=group
    obj['live_surface_binding']='Rest triangles, barycentrics and local tangent coordinates sampled on the evaluated collision-corrected head.'
    return {'object':obj.name,'points':count,'clusters':len(clusters)}
