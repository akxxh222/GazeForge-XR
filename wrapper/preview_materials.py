"""Engine-specific preview surfaces for the same physical scene geometry.

Material Preview uses EEVEE. Its corneal glazing is a transparent/specular
approximation; Cycles retains the original refractive volume. Fine strands
also need a supported surface shader rather than Cycles-only hair scattering.
"""
import bpy


def _engine_outputs(material):
    nodes=material.node_tree.nodes
    old=next(n for n in nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
    old.target='CYCLES'
    old.label='Cycles | physical material'
    preview=nodes.new('ShaderNodeOutputMaterial')
    preview.target='EEVEE'
    preview.label='Material Preview | EEVEE surface'
    return preview


def glazing(material,ior):
    if material.get('eevee_glazing'):return
    output=_engine_outputs(material)
    nodes,links=material.node_tree.nodes,material.node_tree.links
    clear=nodes.new('ShaderNodeBsdfTransparent')
    gloss=nodes.new('ShaderNodeBsdfGlossy')
    gloss.inputs['Roughness'].default_value=.055
    fresnel=nodes.new('ShaderNodeFresnel')
    fresnel.inputs['IOR'].default_value=ior
    mix=nodes.new('ShaderNodeMixShader')
    links.new(fresnel.outputs[0],mix.inputs[0])
    links.new(clear.outputs[0],mix.inputs[1])
    links.new(gloss.outputs[0],mix.inputs[2])
    links.new(mix.outputs[0],output.inputs['Surface'])
    material.surface_render_method='DITHERED'
    material.use_transparent_shadow=True
    material.use_backface_culling=True
    material['eevee_glazing']='Transparent/Fresnel reflection approximation; Cycles uses original refraction.'


def strands(material,label):
    if material.get('eevee_strands'):return
    output=_engine_outputs(material)
    nodes,links=material.node_tree.nodes,material.node_tree.links
    if 'Vellus' in label:
        # Sub-pixel vellus coverage is not resolved faithfully by EEVEE strips.
        surface=nodes.new('ShaderNodeBsdfTransparent')
        material.surface_render_method='DITHERED'
    else:
        surface=nodes.new('ShaderNodeBsdfPrincipled')
        color=(.025,.012,.006) if 'Scalp' in label or 'Public' in label else (.065,.026,.011)
        if 'Lash' in label:color=(.018,.010,.007)
        if 'stubble' in label:color=(.18,.085,.045)
        surface.inputs['Base Color'].default_value=(*color,1)
        surface.inputs['Roughness'].default_value=.58
        surface.inputs['Specular IOR Level'].default_value=.18
    links.new(surface.outputs[0],output.inputs['Surface'])
    material['eevee_strands']='Supported EEVEE surface; Cycles retains native hair scattering.'


def configure():
    materials=set()
    for side in ('L','R'):
        material=bpy.data.objects['Eye_'+side].data.materials[3]
        if material not in materials:
            glazing(material,1.376)
            materials.add(material)
    for obj in bpy.context.scene.objects:
        if not hasattr(obj.data,'materials'):continue
        for mat in obj.data.materials:
            if mat is None:continue
            if mat.get('strand_shader'):
                strands(mat,obj.name+' '+mat.name)
            elif mat.name.startswith('Tear '):
                glazing(mat,1.333)
    bpy.context.scene.eevee.taa_samples=64
    bpy.context.scene.eevee.taa_render_samples=128
    bpy.context.scene['material_preview_note']='EEVEE transparent corneal glazing and supported strand surfaces; Cycles physical eye/hair outputs preserved.'
