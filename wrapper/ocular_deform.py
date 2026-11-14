"""Native post-subdivision blink map and ordered ocular clearance fields.

The closure map retains a positive vertical derivative. Ocular clearance
retains depth ordering instead of projecting several tissue layers onto one
surface. Both are saved Geometry Nodes; playback requires no Python handler.
"""
import bpy


def build(head, proxies, landmarks, profiles,clearance_only=False):
    group=bpy.data.node_groups.new('IrisX | '+('detail ocular clearance' if clearance_only else 'relaxed lids and ordered clearance'),'GeometryNodeTree')
    group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    nodes,links=group.nodes,group.links
    def wire(value,socket):
        if isinstance(value,(float,int,tuple,list)):socket.default_value=value
        else:links.new(value,socket)
    def math(op,a,b=None):
        node=nodes.new('ShaderNodeMath');node.operation=op
        wire(a,node.inputs[0])
        if b is not None:wire(b,node.inputs[1])
        return node.outputs[0]
    def xyz(value):
        node=nodes.new('ShaderNodeSeparateXYZ');wire(value,node.inputs[0]);return list(node.outputs)
    def combine(x,y,z):
        node=nodes.new('ShaderNodeCombineXYZ')
        for value,socket in zip([x,y,z],node.inputs):wire(value,socket)
        return node.outputs[0]
    def smooth(value):
        t=math('MINIMUM',1.,math('MAXIMUM',0.,value))
        return math('MULTIPLY',math('MULTIPLY',t,t),math('SUBTRACT',3.,math('MULTIPLY',2.,t)))
    start=nodes.new('NodeGroupInput');end=nodes.new('NodeGroupOutput')
    geometry=start.outputs['Geometry']
    for side in (() if clearance_only else ('L','R')):
        position=nodes.new('GeometryNodeInputPosition').outputs[0]
        x,y,z=xyz(position)
        low,high=landmarks[side]
        u=math('DIVIDE',math('SUBTRACT',x,float(low[0])),float(high[0]-low[0]))
        def profile(line):
            node=nodes.new('ShaderNodeFloatCurve')
            mapping=node.mapping
            mapping.initialize()
            mapping.use_clip=False
            curve=mapping.curves[0]
            rows=[low]+[p for p in line if low[0]<p[0]<high[0]]+[high]
            curve.points[0].location=(0,float(low[2]))
            curve.points[-1].location=(1,float(high[2]))
            for p in rows[1:-1]:curve.points.new(float((p[0]-low[0])/(high[0]-low[0])),float(p[2]))
            for point in curve.points:point.handle_type='VECTOR'
            mapping.update()
            links.new(math('MINIMUM',1.,math('MAXIMUM',0.,u)),node.inputs['Value'])
            return node.outputs[0]
        top=profile(profiles[side][0]);bottom=profile(profiles[side][1])
        seam=math('ADD',math('MULTIPLY',.3,top),math('MULTIPLY',.7,bottom))
        upper=math('MULTIPLY',math('MULTIPLY',.999,math('SUBTRACT',seam,top)),math('SUBTRACT',1.,smooth(math('DIVIDE',math('SUBTRACT',z,top),.014))))
        lower=math('MULTIPLY',math('MULTIPLY',.999,math('SUBTRACT',seam,bottom)),math('SUBTRACT',1.,smooth(math('DIVIDE',math('SUBTRACT',bottom,z),.010))))
        middle=math('MULTIPLY',.999,math('SUBTRACT',seam,z))
        above=math('GREATER_THAN',z,top);below=math('LESS_THAN',z,bottom)
        delta=math('ADD',math('MULTIPLY',above,upper),math('ADD',math('MULTIPLY',below,lower),math('MULTIPLY',math('SUBTRACT',1.,math('ADD',above,below)),middle)))
        front=smooth(math('DIVIDE',math('SUBTRACT',.010,y),.015))
        control=nodes.new('ShaderNodeValue');control.label='Blink.'+side
        driver=control.outputs[0].driver_add('default_value').driver
        variable=driver.variables.new();variable.name='blink';variable.type='SINGLE_PROP'
        variable.targets[0].id_type='KEY';variable.targets[0].id=head.data.shape_keys
        variable.targets[0].data_path='key_blocks["Blink.'+side+'"].value'
        driver.expression='blink'
        dz=math('MULTIPLY',control.outputs[0],math('MULTIPLY',front,delta))
        move=nodes.new('GeometryNodeSetPosition');links.new(geometry,move.inputs['Geometry'])
        links.new(combine(x,y,math('ADD',z,dz)),move.inputs['Position'])
        geometry=move.outputs['Geometry']
    for side,proxy in zip(('L','R'),proxies):
        position=nodes.new('GeometryNodeInputPosition').outputs[0]
        x,y,z=xyz(position)
        source=nodes.new('GeometryNodeObjectInfo');source.transform_space='RELATIVE'
        source.inputs['Object'].default_value=proxy
        ray=nodes.new('GeometryNodeRaycast');ray.data_type='FLOAT'
        links.new(source.outputs['Geometry'],ray.inputs['Target Geometry'])
        links.new(combine(x,-.10,z),ray.inputs['Source Position'])
        ray.inputs['Ray Direction'].default_value=(0,1,0);ray.inputs['Ray Length'].default_value=.2
        front=xyz(ray.outputs['Hit Position'])[1]
        allowance=.00012 if clearance_only else .00008
        softness=.00008 if clearance_only else .0006
        d=math('SUBTRACT',math('SUBTRACT',front,allowance),y)
        # Rationalized soft minimum, with positive slope for either sign of d.
        root=math('SQRT',math('ADD',math('MULTIPLY',d,d),4*softness**2))
        clipped=math('SUBTRACT',math('SUBTRACT',front,allowance),math('MULTIPLY',.5,math('ADD',d,root)))
        if clearance_only:weight=ray.outputs['Is Hit']
        else:
            attr=nodes.new('GeometryNodeInputNamedAttribute');attr.data_type='FLOAT'
            attr.inputs['Name'].default_value='Collision lid '+side
            weight=math('MULTIPLY',ray.outputs['Is Hit'],attr.outputs['Attribute'])
        yy=math('ADD',y,math('MULTIPLY',weight,math('SUBTRACT',clipped,y)))
        move=nodes.new('GeometryNodeSetPosition');links.new(geometry,move.inputs['Geometry'])
        links.new(combine(x,yy,z),move.inputs['Position']);geometry=move.outputs['Geometry']
    links.new(geometry,end.inputs['Geometry'])
    head.modifiers.new('Relaxed closure and depth-ordered clearance','NODES').node_group=group
    return group
