"""Build a textured GNM scene and render fixed-camera/material review views."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
from wrapper import eyes, materials, appearance, groom
from render_device import configure


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--look', default='look_01')
    parser.add_argument('--views', default='front,macro')
    parser.add_argument('--samples', type=int, default=256)
    parser.add_argument('--review-root', type=Path, default=ROOT/'tests/milestone2')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/gnm/scene_baseline.blend'))
    materials.apply_look(args.look)
    scene = bpy.context.scene
    configure()
    scene.cycles.samples = args.samples
    eyes.reset()
    for name, power, size, specular in [('Key', 8, .22, 1), ('Fill', 1.2, .50, .06), ('Rim', 3, .30, .35)]:
        light = bpy.data.objects[name]
        light.data.energy = power
        light.data.size = size
        light.data.specular_factor = specular
        if name == 'Key':
            light.data.shape = 'RECTANGLE'
            light.data.size_y = .30
        elif name == 'Fill':
            # Keep the secondary reflection above the visible pupil rather
            # than a large pale disc crossing its center.
            light.location = (.30, -.40, .40)
            light.rotation_euler = (-light.location).to_track_quat('-Z', 'Y').to_euler()
            light.data.energy = .6
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .15
    print('STATIC_APPEARANCE', appearance.add_static_details(args.look), flush=True)
    groom_stats = groom.add_scalp_groom(args.look)
    print('SCALP_GROOM', groom_stats, flush=True)
    scene['scalp_groom_stats'] = json.dumps(groom_stats)
    original_camera = scene.camera
    folder = args.review_root/args.look
    folder.mkdir(parents=True, exist_ok=True)
    metadata_path = folder/'review_metadata.json'
    manifest = {entry['view']: entry for entry in json.loads(metadata_path.read_text())} if metadata_path.exists() else {}
    for view in args.views.split(','):
        eyes.reset()
        scene.camera = original_camera
        if view in ('macro', 'macro_left', 'macro_right', 'eye_closeup'):
            camera = original_camera.copy()
            camera.data = original_camera.data.copy()
            camera.name = 'Review_'+view
            scene.collection.objects.link(camera)
            camera.data.lens = 145
            if view == 'eye_closeup':
                camera.data.lens = 300
                camera.location.x = bpy.data.objects['Eye_L'].matrix_world.translation.x
            scene.camera = camera
            if view == 'macro_left':
                eyes.move(-1, 0)
            elif view == 'macro_right':
                eyes.move(1, 0)
        elif view in ('side_left', 'side_right'):
            sign = -1 if view == 'side_left' else 1
            camera = original_camera.copy()
            camera.data = original_camera.data.copy()
            camera.name = 'Review_'+view
            scene.collection.objects.link(camera)
            camera.location = (sign*.32, -.36, .015)
            camera.rotation_euler = (Vector((0, .025, -.025))-camera.location).to_track_quat('-Z', 'Y').to_euler()
            camera.data.lens = 50
            scene.camera = camera
        elif view != 'front':
            raise ValueError('Unknown review view: '+view)
        data = eyes.render(folder/(view+'.png'))
        data['view'] = view
        data['camera_lens_mm'] = scene.camera.data.lens
        data['role'] = 'Calibrated material preview' if view == 'front' else 'Additional material review camera/pose, not an official dataset frame'
        data['pupil_label_semantics'] = scene['pupil_label_semantics']
        data['texture_manifest_sha256'] = hashlib.sha256((ROOT/'textures'/args.look/'manifest.json').read_bytes()).hexdigest()
        data['appearance_code_sha256'] = hashlib.sha256((ROOT/'wrapper/appearance.py').read_bytes()).hexdigest()
        data['materials_code_sha256'] = hashlib.sha256((ROOT/'wrapper/materials.py').read_bytes()).hexdigest()
        data['groom_code_sha256'] = hashlib.sha256((ROOT/'wrapper/groom.py').read_bytes()).hexdigest()
        data['scalp_groom'] = groom_stats
        data['render_builder_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        data['cycles_samples'] = scene.cycles.samples
        data['lighting'] = {name: {'watts': bpy.data.objects[name].data.energy,
                                  'size_m': bpy.data.objects[name].data.size,
                                  'shape': bpy.data.objects[name].data.shape,
                                  'specular_factor': bpy.data.objects[name].data.specular_factor}
                            for name in ('Key', 'Fill', 'Rim')}
        manifest[view] = data
    eyes.reset()
    scene.camera = original_camera
    metadata_path.write_text(json.dumps(list(manifest.values()), indent=2)+'\n')
    # Material Preview survives a file reopen; Blender resets a saved Rendered
    # viewport to Solid. F12 remains the authoritative Cycles material review.
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    bpy.context.view_layer.objects.active = bpy.data.objects['GNM_skin']
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                space.overlay.show_overlays = False
                space.shading.type = 'MATERIAL'
                space.shading.use_scene_lights = True
                space.shading.use_scene_world = True
                space.region_3d.view_perspective = 'CAMERA'
                space.region_3d.view_camera_zoom = 0
    scene['review_note'] = 'Material Preview camera view; F12 for final Cycles skin/hair/eye materials. Static review, not final animation.'
    path = args.output or ROOT/'work/gnm'/('scene_'+args.look+'_realism.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    print('GNM_TEXTURE_SCENE_READY', path, flush=True)


if __name__ == '__main__':
    main()
