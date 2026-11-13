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
from wrapper import eyes, materials, appearance
from render_device import configure


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--look', default='look_01')
    parser.add_argument('--views', default='front,macro')
    parser.add_argument('--samples', type=int, default=64)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/gnm/scene_baseline.blend'))
    materials.apply_look(args.look)
    scene = bpy.context.scene
    configure()
    scene.cycles.samples = args.samples
    eyes.reset()
    for name, power, size in [('Key', 7, .20), ('Fill', 2, .40), ('Rim', 6, .30)]:
        light = bpy.data.objects[name]
        light.data.energy = power
        light.data.size = size
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .15
    print('STATIC_APPEARANCE', appearance.add_static_details(args.look), flush=True)
    original_camera = scene.camera
    folder = ROOT/'tests/milestone2'/args.look
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
        manifest[view] = data
    eyes.reset()
    scene.camera = original_camera
    metadata_path.write_text(json.dumps(list(manifest.values()), indent=2)+'\n')
    path = ROOT/'work/gnm'/('scene_'+args.look+'.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    print('GNM_TEXTURE_SCENE_READY', path, flush=True)


if __name__ == '__main__':
    main()
