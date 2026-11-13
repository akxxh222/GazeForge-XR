"""Import the official GNM template without changing its native UVs.

Project adaptation of Apache-2.0 Google GNM model data; see assets/gnm/.
Run in Blender with --factory-startup. Leaves the legacy scene untouched.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]
from render_device import configure
from wrapper import eyes


def digest(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def material(name, color, roughness=.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    mat.diffuse_color = (*color, 1)
    return mat, bsdf


def build(output):
    model_path = ROOT / 'assets/gnm/gnm_head.npz'
    expected = '61d78bbfb4ad8e0b38495804a4caef3214d3df00f8c3f68761e63b41ce3747eb'
    if hashlib.sha256(model_path.read_bytes()).hexdigest() != expected:
        raise ValueError('Download the verified model with scripts/fetch_gnm.ps1')
    with np.load(model_path, allow_pickle=False) as src:
        vertices = src['template_vertex_positions']
        quads = src['quads']
        uv = src['quad_uvs']
        group_names = src['vertex_group_names'].tolist()
        groups = {name: src['vertex_groups'][i] for i, name in enumerate(group_names)}
        joint_names = src['joint_names'].tolist()
        joints = {name: src['template_joint_positions'][i] for i, name in enumerate(joint_names)}
        components = src['mesh_component_names'].tolist()
        source_version = str(src['version'])
    # GNM: +Y up, +Z face forward, meters. Project: +Z up, -Y forward.
    native_to_world = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], dtype=np.float32)
    native_mid = (joints['left_eye'] + joints['right_eye']) / 2
    world_vertices = (vertices - native_mid) @ native_to_world.T
    centers = {side: (joints[name] - native_mid) @ native_to_world.T
               for side, name in [('L', 'left_eye'), ('R', 'right_eye')]}

    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.cycles.seed = 2026
    scene.cycles.use_animated_seed = False
    scene.render.resolution_x = scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.view_settings.view_transform = 'AgX'
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.04, .05, .07, 1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .3

    skin, skin_bsdf = material('GNM draft skin | replace in milestone 2', (.42, .26, .19))
    skin_bsdf.inputs['Subsurface Weight'].default_value = .04
    sclera, _ = material('GNM draft sclera', (.65, .67, .62), .35)
    iris, _ = material('GNM draft iris', (.10, .14, .08), .45)
    pupil, pupil_bsdf = material('GNM pupil aperture', (0, 0, 0), 1)
    pupil_bsdf.inputs['Specular IOR Level'].default_value = 0
    cornea, cornea_bsdf = material('GNM draft cornea', (1, 1, 1), .035)
    cornea_bsdf.inputs['Transmission Weight'].default_value = 1
    cornea_bsdf.inputs['IOR'].default_value = 1.376
    teeth, _ = material('GNM draft teeth and gums', (.5, .36, .29), .4)
    tongue, _ = material('GNM draft tongue', (.26, .06, .06), .6)
    checker, _ = material('GNM UV diagnostic checker', (.5, .5, .5))
    checker.use_fake_user = True
    nodes, links = checker.node_tree.nodes, checker.node_tree.links
    coord = nodes.new('ShaderNodeTexCoord')
    check = nodes.new('ShaderNodeTexChecker')
    check.inputs['Scale'].default_value = 32
    check.inputs['Color1'].default_value = (.035, .12, .15, 1)
    check.inputs['Color2'].default_value = (.7, .85, .82, 1)
    links.new(coord.outputs['UV'], check.inputs['Vector'])
    links.new(check.outputs['Color'], nodes['Principled BSDF'].inputs['Base Color'])

    arm = bpy.data.armatures.new('GazeRig')
    rig = bpy.data.objects.new('GazeRig', arm)
    scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for side, c in centers.items():
        bone = arm.edit_bones.new('eye.' + side)
        bone.head = c
        bone.tail = c + np.array([0, -.025, 0])
        bone.use_deform = False
    bpy.ops.object.mode_set(mode='OBJECT')
    rig.show_in_front = True

    component_reports = []
    for component in components:
        face_ids = np.flatnonzero((groups[component][quads] > .5).all(axis=1))
        vertex_ids = np.unique(quads[face_ids])
        remap = np.full(len(vertices), -1, dtype=np.int32)
        remap[vertex_ids] = np.arange(len(vertex_ids))
        coords = world_vertices[vertex_ids].copy()
        side = {'left_eye': 'L', 'right_eye': 'R'}.get(component)
        if side:
            # Rest eye optical axis local +Y; a neutral world rotation maps it -Y.
            coords -= centers[side]
            coords *= np.array([-1, -1, 1], dtype=np.float32)
        mesh = bpy.data.meshes.new('GNM native ' + component)
        mesh.from_pydata(coords.tolist(), [], remap[quads[face_ids]].tolist())
        mesh.update()
        obj = bpy.data.objects.new('Eye_' + side if side else 'GNM_' + component, mesh)
        scene.collection.objects.link(obj)
        obj['gnm_component'] = component
        native_uv = mesh.uv_layers.new(name='GNM_native_per_region')
        native_uv.data.foreach_set('uv', uv[face_ids].reshape(-1))
        attr = mesh.attributes.new('gnm_vertex_id', 'INT', 'POINT')
        attr.data.foreach_set('value', vertex_ids)
        attr = mesh.attributes.new('gnm_quad_id', 'INT', 'FACE')
        attr.data.foreach_set('value', face_ids)
        mats = [sclera, iris, pupil, cornea] if side else [skin if component == 'skin' else tongue if component == 'tongue' else teeth]
        for mat in mats:
            mesh.materials.append(mat)
        for polygon, native_face in zip(mesh.polygons, quads[face_ids]):
            polygon.use_smooth = True
            if side:
                if np.all(groups['eye_exteriors'][native_face] > .5):
                    polygon.material_index = 3
                elif np.all(groups['pupils'][native_face] > .5):
                    polygon.material_index = 2
                elif np.all(groups['irises'][native_face] > .5):
                    polygon.material_index = 1
        sub = obj.modifiers.new('Native surface subdivision', 'SUBSURF')
        sub.levels = sub.render_levels = 2
        if side:
            constraint = obj.constraints.new('COPY_TRANSFORMS')
            constraint.target = rig
            constraint.subtarget = 'eye.' + side
            pupil_ids = np.flatnonzero((groups[component] > .5) & (groups['pupils'] > .5))
            pupil_center = world_vertices[pupil_ids].mean(0) - centers[side]
            pupil_center *= np.array([-1, -1, 1])
            obj['pupil_center_local'] = pupil_center.tolist()
            obj['pupil_radius_m'] = float(pupil_center[1])
            obj['radius_m'] = float(np.median(np.linalg.norm(coords, axis=1)))
            marker = bpy.data.objects.new('PupilCenter_' + side, None)
            scene.collection.objects.link(marker)
            marker.parent = obj
            marker.location = pupil_center
            marker.empty_display_size = .001
        component_reports.append({'component': component, 'object': obj.name,
                                  'vertices': len(vertex_ids), 'quads': len(face_ids),
                                  'native_uv_sha256': digest(uv[face_ids])})

    target = bpy.data.objects.new('FixationTarget', None)
    scene.collection.objects.link(target)
    target.empty_display_size = .005
    bpy.ops.object.camera_add(location=(0, -.4, 0))
    camera = bpy.context.object
    camera.name = 'RenderCamera'
    camera.rotation_euler = (-camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.lens = 40
    camera.data.sensor_width = 36
    camera.data.clip_start = .01
    scene.camera = camera
    for name, position, power, size, color in [
            ('Key', (-.3, -.4, .28), 22, .4, (1, .9, .8)),
            ('Fill', (.3, -.3, .1), 12, .3, (.8, .9, 1)),
            ('Rim', (.1, .18, .25), 20, .3, (.8, .9, 1))]:
        bpy.ops.object.light_add(type='AREA', location=position)
        light = bpy.context.object
        light.name = name
        light.data.energy = power
        light.data.shape = 'DISK'
        light.data.size = size
        light.data.color = color
        light.rotation_euler = (-light.location).to_track_quat('-Z', 'Y').to_euler()
    scene['team_name'] = 'VITChennai_IrisX'
    scene['gnm_model_sha256'] = expected
    scene['gnm_uv_layout'] = 'Unmodified per-region quad_uvs; separate component materials; eyes independently assigned'
    scene['visual_status'] = 'Milestone 1 draft materials; not photorealistic'
    scene['target_plane_m'] = .35
    scene['target_half_extent_m'] = .05
    scene['render_device'] = configure()
    eyes.reset()
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    manifest = {'model': 'GNM Head', 'version': source_version, 'model_sha256': expected,
                'license': 'Apache-2.0', 'native_vertices': len(vertices), 'native_quads': len(quads),
                'native_quads_sha256': digest(quads), 'native_quad_uvs_sha256': digest(uv),
                'native_to_world_rotation': native_to_world.tolist(),
                'native_eye_midpoint_m': native_mid.tolist(), 'scale': 1.0,
                'identity': 'All-zero native template coefficients',
                'uv_layout': 'Unmodified per-region UVs, disambiguated by component materials',
                'components': component_reports, 'draft_scene': output.relative_to(ROOT).as_posix(),
                'modifications': 'Rigid coordinate conversion, component separation, eye rig, draft materials and subdivision. Original vertex/face IDs and native UVs retained.'}
    (ROOT / 'assets/gnm/native_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('GNM_BASELINE_SAVED', output, scene['render_device'], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'work/gnm/scene_baseline.blend')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    build(args.output.resolve())
