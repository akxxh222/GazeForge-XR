"""Local eye appearance candidate; native Basis, UVs and rigid aim retained."""
import hashlib
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]


def refine(rest_closure=.075):
    """Install a packed CC0 iris and modest relaxed-lid rest correction.

    This is a review variant. The blink control remains 0..1, with a relaxed
    open rest and the original fully closed endpoint. No eye aim is offset.
    """
    source = ROOT/'assets/eye_refinement/green_eye.png'
    expected = 'b9864ac4f4fa484b24e18f6aba030d70dbc8820cbbacfbe63a974c76772c2009'
    if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
        raise ValueError('Pinned CC0 MakeHuman iris source differs')
    if not 0 <= rest_closure <= .15:
        raise ValueError('Rest closure must be within [0, .15]')
    image = bpy.data.images.load(str(source), check_existing=True)
    image.pack()
    for side in ('L', 'R'):
        eye = bpy.data.objects['Eye_'+side]
        mat = bpy.data.materials.new('IrisX | CC0 radial green iris '+side)
        mat.use_nodes = True
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        shader = nodes.get('Principled BSDF')
        shader.inputs['Roughness'].default_value = .48
        shader.inputs['Specular IOR Level'].default_value = .025
        uv = nodes.new('ShaderNodeUVMap')
        uv.uv_map = 'GNM_native_per_region'
        offset = nodes.new('ShaderNodeVectorMath'); offset.operation = 'SUBTRACT'
        offset.inputs[1].default_value = (.5, .5, 0)
        links.new(uv.outputs['UV'], offset.inputs[0])
        radius = nodes.new('ShaderNodeVectorMath'); radius.operation = 'LENGTH'
        links.new(offset.outputs['Vector'], radius.inputs[0])
        radial = nodes.new('ShaderNodeMath'); radial.operation = 'MULTIPLY_ADD'
        # Register both annulus boundaries, preventing a painted black ring
        # from enlarging the actual native pupil aperture.
        slope = (.1145-.0355)/(.18492-.04985)
        radial.inputs[1].default_value = slope
        radial.inputs[2].default_value = .0355-.04985*slope
        links.new(radius.outputs['Value'], radial.inputs[0])
        unit = nodes.new('ShaderNodeVectorMath'); unit.operation = 'NORMALIZE'
        links.new(offset.outputs[0], unit.inputs[0])
        scale = nodes.new('ShaderNodeVectorMath'); scale.operation = 'SCALE'
        links.new(unit.outputs[0], scale.inputs[0]); links.new(radial.outputs[0], scale.inputs['Scale'])
        add = nodes.new('ShaderNodeVectorMath'); add.operation = 'ADD'
        add.inputs[1].default_value = (.70645327, .70427737, 0)
        links.new(scale.outputs[0], add.inputs[0])
        texture = nodes.new('ShaderNodeTexImage'); texture.image = image
        texture.interpolation = 'Linear'; texture.extension = 'EXTEND'
        links.new(add.outputs[0], texture.inputs['Vector'])
        hue = nodes.new('ShaderNodeHueSaturation')
        hue.inputs['Hue'].default_value = .46
        hue.inputs['Saturation'].default_value = .42
        hue.inputs['Value'].default_value = 1.1
        links.new(texture.outputs['Color'], hue.inputs['Color'])
        links.new(hue.outputs['Color'], shader.inputs['Base Color'])
        mat['author'] = 'MakeHuman system assets; native GNM registration by VITChennai_IrisX'
        mat['license'] = 'CC0-1.0'
        mat['source'] = 'https://opengameart.org/content/makehuman-system-assets-eyes'
        mat['source_sha256'] = expected
        mat['modifications'] = 'Shader-space annulus registration, restrained saturation/hue; no native UV edits. Iris color only; original pupil and corneal geometry retained.'
        eye.data.materials[1] = mat
        sclera = eye.data.materials[0].copy()
        sclera.name = 'IrisX | warm sclera '+side
        eye.data.materials[0] = sclera
        shader = sclera.node_tree.nodes.get('Principled BSDF')
        original = shader.inputs['Base Color'].links[0].from_socket
        mix = sclera.node_tree.nodes.new('ShaderNodeMixRGB')
        mix.blend_type = 'MIX'; mix.inputs[0].default_value = .38
        mix.inputs[2].default_value = (.72, .75, .70, 1)
        sclera.node_tree.links.new(original, mix.inputs[1])
        sclera.node_tree.links.new(mix.outputs[0], shader.inputs['Base Color'])
        shader.inputs['Subsurface Weight'].default_value = .08
        shader.inputs['Subsurface Scale'].default_value = .0003
        for node in sclera.node_tree.nodes:
            if node.type == 'BUMP':
                node.inputs['Strength'].default_value = .08
                node.inputs['Distance'].default_value = .000025
    # Shared outer shell keeps its physical IOR; tune only its surface finish.
    corneas = {bpy.data.objects['Eye_'+s].data.materials[3] for s in ('L', 'R')}
    replacements = {}
    for cornea in corneas:
        copy = cornea.copy(); copy.name = 'IrisX | restrained corneal surface'
        copy.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value = .025
        replacements[cornea] = copy
    for side in ('L', 'R'):
        eye = bpy.data.objects['Eye_'+side]
        eye.data.materials[3] = replacements[eye.data.materials[3]]
    modifier = next(m for m in bpy.data.objects['GNM_skin'].modifiers
                    if m.type == 'NODES' and 'relaxed lids' in m.node_group.name)
    group = modifier.node_group.copy()
    group.name = 'IrisX | refined relaxed lids and ordered clearance'
    modifier.node_group = group
    for node in list(group.nodes):
        if node.type == 'VALUE' and node.label in {'Blink.L', 'Blink.R'}:
            destinations = [link.to_socket for link in list(node.outputs[0].links)]
            multiply = group.nodes.new('ShaderNodeMath'); multiply.operation = 'MULTIPLY'
            multiply.inputs[1].default_value = 1-rest_closure
            add = group.nodes.new('ShaderNodeMath'); add.operation = 'ADD'
            add.inputs[1].default_value = rest_closure
            group.links.new(node.outputs[0], multiply.inputs[0])
            group.links.new(multiply.outputs[0], add.inputs[0])
            for destination in destinations:
                group.links.new(add.outputs[0], destination)
    bpy.context.view_layer.update()
    bpy.context.scene['eye_refinement'] = f'Local review candidate: CC0 iris, warm sclera and relaxed rest ({rest_closure}); physical pivots/aim/UV/Basis retained. Full blink endpoint retained. Visual acceptance pending.'
    return {'iris_source_sha256': expected, 'iris_license': 'CC0-1.0',
            'rest_closure': rest_closure, 'blink_remap': 'rest + (1-rest)*blink',
            'geometry_scope': 'Native Basis/UV and physical eye pivots unchanged; evaluated lid rest changes.'}
