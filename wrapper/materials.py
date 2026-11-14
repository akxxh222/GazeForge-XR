"""Apply portable native-GNM texture looks inside Blender."""
import json
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]


def _image(folder, name, data=False):
    path = folder/name
    image = bpy.data.images.load(str(path), check_existing=True)
    image.colorspace_settings.name = 'Non-Color' if data else 'sRGB'
    image.pack()
    return image


def _material(name):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    return material, material.node_tree.nodes.get('Principled BSDF')


def _texture(material, image):
    node = material.node_tree.nodes.new('ShaderNodeTexImage')
    node.image = image
    node.interpolation = 'Linear'
    uv = material.node_tree.nodes.new('ShaderNodeUVMap')
    uv.uv_map = 'GNM_native_per_region'
    material.node_tree.links.new(uv.outputs['UV'], node.inputs['Vector'])
    return node


def apply_look(texture_id='look_01'):
    if texture_id not in {f'look_{i:02d}' for i in range(1, 6)}:
        raise ValueError('Choose a generated texture ID, look_01 through look_05')
    folder = ROOT/'textures'/texture_id
    manifest = json.loads((folder/'manifest.json').read_text())
    head = bpy.data.objects.get('GNM_skin')
    if head is None:
        raise RuntimeError('Load the native GNM baseline scene first')
    skin, bsdf = _material(texture_id+'/Skin')
    albedo = _texture(skin, _image(folder, 'skin_basecolor.png'))
    rough = _texture(skin, _image(folder, 'skin_roughness.png', True))
    height = _texture(skin, _image(folder, 'skin_height.png', True))
    links, nodes = skin.node_tree.links, skin.node_tree.nodes
    links.new(albedo.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(rough.outputs['Color'], bsdf.inputs['Roughness'])
    bsdf.inputs['IOR'].default_value = 1.4
    bsdf.inputs['Subsurface Weight'].default_value = .12
    bsdf.inputs['Subsurface Radius'].default_value = (1, .45, .25)
    bsdf.inputs['Subsurface Scale'].default_value = .0011
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .42
    bump.inputs['Distance'].default_value = .00040
    links.new(height.outputs['Color'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    head.data.materials[0] = skin
    for side in ('L', 'R'):
        eye = bpy.data.objects['Eye_'+side]
        for slot, label, roughness, subsurface in [(0, 'Sclera', .28, .12), (1, 'Iris', .45, .02)]:
            interior, bsdf = _material(texture_id+'/'+label+'_'+side)
            image = _texture(interior, _image(folder, f'eye_{side}_basecolor.png'))
            height = _texture(interior, _image(folder, f'eye_{side}_height.png', True))
            interior.node_tree.links.new(image.outputs['Color'], bsdf.inputs['Base Color'])
            bsdf.inputs['Roughness'].default_value = roughness
            bsdf.inputs['IOR'].default_value = 1.376
            # The air/cornea interface is already represented by the outer
            # shell. Avoid a second air-like highlight on the moist interior.
            bsdf.inputs['Specular IOR Level'].default_value = .08 if slot == 0 else .03
            bsdf.inputs['Subsurface Weight'].default_value = subsurface
            bsdf.inputs['Subsurface Scale'].default_value = .0004
            bump = interior.node_tree.nodes.new('ShaderNodeBump')
            bump.inputs['Strength'].default_value = .18 if slot == 0 else .25
            bump.inputs['Distance'].default_value = .000045 if slot == 0 else .00008
            interior.node_tree.links.new(height.outputs['Color'], bump.inputs['Height'])
            interior.node_tree.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
            eye.data.materials[slot] = interior
        cornea = eye.data.materials[3]
        cornea_bsdf = cornea.node_tree.nodes.get('Principled BSDF')
        cornea_bsdf.inputs['Roughness'].default_value = .035
        cornea_bsdf.inputs['IOR'].default_value = 1.376
    scene = bpy.context.scene
    scene.cycles.samples = 64
    scene.cycles.max_bounces = 12
    scene.cycles.transmission_bounces = 12
    scene.cycles.preview_samples = 128
    scene.cycles.use_preview_denoising = True
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = .01
    scene.cycles.sample_clamp_indirect = 3
    scene.cycles.blur_glossy = .5
    # Required here for direct lighting to reach the opaque eye through its
    # native corneal shell. Disabling refractive caustics darkens the interior.
    scene.cycles.caustics_reflective = True
    scene.cycles.caustics_refractive = True
    scene['texture_look'] = texture_id
    scene['texture_source'] = manifest['source_material']
    scene['texture_status'] = 'Milestone 2 material review; visual acceptance tracked separately'
    scene['visual_status'] = 'Milestone 2 static material refinement; visual acceptance tracked separately'
    scene['pupil_label_semantics'] = 'Geometric 3D aperture centroid and pinhole projection; corneal refraction can shift the apparent rendered pupil'
    return manifest
