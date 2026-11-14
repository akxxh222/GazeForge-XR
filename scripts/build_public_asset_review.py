"""Build one static public-asset review, preserving native GNM Basis and UVs.

Prerequisites: fetch_public_candidates.py, extract_public_hair.py and
fit_public_groom.py. Source attribution is embedded in the saved file.
This remains a Milestone 2 review, not the five-look submission builder.
"""
import bpy
import json
import sys
import argparse
import hashlib
import time
from pathlib import Path
from mathutils import Vector
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from render_device import configure
from wrapper import eyes
from wrapper.appearance import _strand_material

parser=argparse.ArgumentParser()
parser.add_argument('--style',choices=['curly','cyberpunk'],default='cyberpunk')
parser.add_argument('--samples',type=int,default=256)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
source_file=ROOT/'work/public_candidates/bystedt_fox_eyes.blend'
if hashlib.sha256(source_file.read_bytes()).hexdigest()!='80b29f6dcd099460a60ae100503188474145495222bd88fea1b4df0bf0383041':
    raise ValueError('Pinned eye shader source checksum does not match')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/public_candidates'/args.style/'candidate.blend'),use_scripts=False)
scene=bpy.context.scene
configure()
scene.cycles.samples=args.samples
hair=bpy.data.objects['Public_groom_'+args.style]
hair.data.materials.clear()
dark=_strand_material('Public groom | dark brown Cycles fibers',.98,.16,.38)
hs=dark.node_tree.nodes.get('Principled Hair BSDF')
hs.inputs['Coat'].default_value=.05
hs.inputs['Radial Roughness'].default_value=.44
hs.model='HUANG'
hs.inputs['Aspect Ratio'].default_value=.85
# Art-directed lobe weights prevent a broad silver sheen at this fixed light.
hs.inputs['Reflection'].default_value=.32
hs.inputs['Transmission'].default_value=.50
hs.inputs['Secondary Reflection'].default_value=.40
hair.data.materials.append(dark)
hair['modifications']+=' Replaced source engine-specific shader with modern Cycles Huang melanin shader and art-directed scattering weights.'
skin=bpy.data.objects['GNM_skin'].data.materials[0]
for n in skin.node_tree.nodes:
    if n.type=='BUMP':
        n.inputs['Strength'].default_value=.32
        n.inputs['Distance'].default_value=.00022
for side in ('L','R'):
    brow=bpy.data.objects['Brow_fibers_'+side].data.materials[0]
    bs=brow.node_tree.nodes.get('Principled Hair BSDF')
    bs.inputs['Melanin'].default_value=.90
    bs.inputs['Roughness'].default_value=.46
    eye=bpy.data.objects['Eye_'+side]
    with bpy.data.libraries.load(str(source_file),link=False) as (source,loaded):
        loaded.materials=['eyes']
    mat=loaded.materials[0]
    mat.name='Bystedt adapted human iris '+side+' | CC BY-SA 3.0'
    nodes,links=mat.node_tree.nodes,mat.node_tree.links
    mat.node_tree.animation_data_clear()
    # Each imported material shares its two coordinate groups. Transform their
    # UV input only once, without editing the native target mesh or UV layer.
    for group in (n.node_tree for n in nodes if n.type=='GROUP'):
        if group.get('GNM_remapped'):continue
        group.animation_data_clear()
        for coord in [n for n in group.nodes if n.type=='TEX_COORD']:
            for link in list(coord.outputs['UV'].links):
                target=link.to_socket
                scale=group.nodes.new('ShaderNodeVectorMath')
                scale.operation='MULTIPLY_ADD'
                scale.inputs[1].default_value=(2.6,2.6,1)
                scale.inputs[2].default_value=(-.8,-.8,0)
                group.links.new(coord.outputs['UV'],scale.inputs[0])
                group.links.new(scale.outputs[0],target)
        group['GNM_remapped']=True
    for name in ['Group','Group.007','Group.011','Group.012']:
        nodes[name].inputs['heght width bias'].default_value=0
    # Reduce the fox palette's hue scatter and broad spots for human hazel.
    nodes['Mix.020'].inputs[0].default_value=.025
    nodes['Mix.012'].inputs[0].default_value=.25
    nodes['Mix.021'].inputs[0].default_value=.70
    hue=nodes.new('ShaderNodeHueSaturation')
    hue.inputs['Saturation'].default_value=.78
    hue.inputs['Value'].default_value=.90
    links.new(nodes['Mix.016'].outputs['Result'],hue.inputs['Color'])
    # An irregular-looking but smooth peripheral darkening on the original UV.
    uv=nodes.new('ShaderNodeUVMap')
    uv.uv_map='GNM_native_per_region'
    distance=nodes.new('ShaderNodeVectorMath')
    distance.operation='DISTANCE'
    distance.inputs[1].default_value=(.5,.5,0)
    links.new(uv.outputs[0],distance.inputs[0])
    ramp=nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position=.167
    ramp.color_ramp.elements[0].color=(1,1,1,1)
    ramp.color_ramp.elements[1].position=.187
    ramp.color_ramp.elements[1].color=(.18,.18,.18,1)
    links.new(distance.outputs['Value'],ramp.inputs[0])
    multiply=nodes.new('ShaderNodeMixRGB')
    multiply.blend_type='MULTIPLY'
    multiply.inputs[0].default_value=1
    links.new(hue.outputs[0],multiply.inputs[1])
    links.new(ramp.outputs[0],multiply.inputs[2])
    # Keep only source iris color; disable fox emission and install a physically
    # opaque iris beneath the native transparent cornea.
    bsdf=nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value=.48
    bsdf.inputs['Specular IOR Level'].default_value=.02
    links.new(multiply.outputs[0],bsdf.inputs['Base Color'])
    output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL')
    links.new(bsdf.outputs[0],output.inputs['Surface'])
    mat['author']='Daniel Bystedt'
    mat['license']='CC BY-SA 3.0'
    mat['source']='https://download.blender.org/demo/splash/blender-2.90-splash.blend'
    mat['modifications']='Native GNM UV coordinate remap; round masks; restrained human hazel palette and reduced broad spots; iris-only color output; removed fox emission; native-UV limbal gradient; modern Cycles interior BSDF.'
    eye.data.materials[1]=mat
    # An authored pupil constriction shape key retains every original rest
    # vertex and native UV. Bone centers and optical axis remain unchanged.
    eye.shape_key_add(name='Basis')
    key=eye.shape_key_add(name='Pupil | daylight constriction')
    center=Vector(eye['pupil_center_local'])
    uv_by_vertex={}
    for p in eye.data.polygons:
        if p.material_index==3:continue
        for l in p.loop_indices:
            idx=eye.data.loops[l].vertex_index
            uv_by_vertex[idx]=eye.data.uv_layers.active.data[l].uv.copy()
    for i,uv in uv_by_vertex.items():
        r=(uv-Vector((.5,.5))).length
        t=max(0,min(1,(r-.04985)/(.18492-.04985)))
        scale=.70+.30*(t*t*(3-2*t))
        key.data[i].co.x=center.x+(key.data[i].co.x-center.x)*scale
        key.data[i].co.z=center.z+(key.data[i].co.z-center.z)*scale
    key.value=1
    eye['pupil_constriction']='Authored 0.70 radial aperture shape key; native Basis vertices/UVs unchanged.'
eyes.reset()
out=ROOT/'work/review'/args.style
out.mkdir(parents=True,exist_ok=True)
records=[]
for label,camera in [('eye','Review_eye_closeup'),('front','RenderCamera'),('side','Review_side_left')]:
    scene.camera=bpy.data.objects[camera]
    start=time.perf_counter()
    record=eyes.render(out/('asset_'+label+'_test.png'))
    record.update(view=label,seconds=time.perf_counter()-start,samples=args.samples,
                  builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    records.append(record)
(out/'render_receipt.json').write_text(json.dumps(records,indent=2)+'\n')
scene.camera=bpy.data.objects['RenderCamera']
scene['public_asset_review']='Imported Bystedt hair/iris adaptation. Static Milestone 2 review; not final submission.'
notice=bpy.data.texts.new('IRISX_PUBLIC_ASSET_CREDITS.txt')
notice.write('VITChennai_IrisX static Milestone 2 review\n\n'
    'Iris color network: Daniel Bystedt, Splash Fox / Blender 2.90 splash, CC BY-SA 3.0.\n'
    'https://download.blender.org/demo/splash/blender-2.90-splash.blend\n'
    'https://creativecommons.org/licenses/by-sa/3.0/\n'
    'Modified: native GNM UV remap, round masks, human hazel palette, limbal gradient, no fox emission, modern Cycles BSDF. Adapted iris material retains CC BY-SA 3.0.\n\n'
    'Scalp groom: Daniel Bystedt, official Blender Hair Styles demo, CC BY-SA (source does not state a version).\n'
    'https://download.blender.org/demo/geometry-nodes/hair_nodes-female_hair_styles.blend\n'
    'Modified: frozen evaluated curves, metric/root fitting to native GNM, short trim, taper and replacement melanin shader. Retain source BY-SA notice; resolve version before final redistributable bundle.\n\n'
    'GNM Head 3.0: copyright 2026 Google LLC, Apache-2.0. Basis vertices and native UVs unchanged; authored radial pupil constriction is a shape key.\n'
    'Skin: CC0 MakeHuman diffuse sources plus Lee Perry-Smith / Infinite-Realities scan detail, CC BY 3.0. Full source hashes and modifications: assets/LICENSES.md and assets/skin_detail/.\n'
    'This scene is not entirely CC0 or MIT. Imported asset terms remain separate from MIT project code.\n'
    'F12 shows actual Cycles materials. Material Preview may differ in corneal/hair rendering. Static review; visual acceptance, deformation binding and animation remain open.\n')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'IRISX_ASSET_REVIEW.blend'))
print('ASSET_HERO_SAVED',flush=True)
