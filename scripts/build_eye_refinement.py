"""Render a separate before/after eye candidate, preserving milestone scenes."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
from wrapper import expressions, eye_refinement
from render_device import configure


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--after-only', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    source = ROOT/'work/milestone3/final/IRISX_MILESTONE3.blend'
    folder = ROOT/'work/review/eye_refinement'
    folder.mkdir(parents=True, exist_ok=True)
    receipt = {'source_sha256': sha(source), 'renders': [], 'scope': 'Local visual candidate, not M2 acceptance or updated official capture.'}
    if args.after_only:
        prior = json.loads((folder/'render_receipt.json').read_text(encoding='utf-8'))
        if prior['source_sha256'] != sha(source):
            raise ValueError('Baseline scene changed')
        receipt['renders'] = [r for r in prior['renders'] if r['variant'] == 'before']
        if len(receipt['renders']) != 2 or any(sha(folder/r['file']) != r['sha256'] for r in receipt['renders']):
            raise ValueError('Both pinned baseline renders required')
    receipt['builder_sha256'] = sha(Path(__file__))
    receipt['refiner_sha256'] = sha(ROOT/'wrapper/eye_refinement.py')
    for variant in (('after',) if args.after_only else ('before', 'after')):
        bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
        scene = bpy.context.scene
        configure()
        expressions.use_action('generate_motion')
        scene.render.engine = 'CYCLES'
        scene.render.resolution_x = scene.render.resolution_y = 1024
        scene.render.resolution_percentage = 100
        scene.cycles.samples = 128
        scene.cycles.use_denoising = True
        scene.render.use_persistent_data = True
        if variant == 'after':
            receipt['changes'] = eye_refinement.refine()
            scene.camera = bpy.data.objects['RenderCamera']
            scene.frame_set(1)
            for screen in bpy.data.screens:
                for area in screen.areas:
                    if area.type == 'VIEW_3D':
                        space = area.spaces.active
                        space.shading.type = 'MATERIAL'
                        space.shading.use_scene_lights = True
                        space.shading.use_scene_world = True
                        space.overlay.show_overlays = False
                        space.region_3d.view_perspective = 'CAMERA'
            path = folder/'IRISX_EYE_REFINEMENT.blend'
            bpy.ops.wm.save_as_mainfile(filepath=str(path))
            receipt['scene_sha256'] = sha(path)
        for frame in (1, 43):
            scene.frame_set(frame)
            scene.camera = bpy.data.objects['Review_macro']
            output = folder/f'{variant}_frame_{frame:03d}.png'
            scene.render.filepath = str(output)
            start = time.perf_counter()
            bpy.ops.render.render(write_still=True)
            receipt['renders'].append({'variant': variant, 'frame': frame, 'file': output.name,
                                       'sha256': sha(output), 'seconds': time.perf_counter()-start,
                                       'camera': scene.camera.name, 'state': expressions.state()})
            (folder/'render_receipt.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
            print('EYE_REFINEMENT_RENDER', variant, frame, flush=True)
    print('EYE_REFINEMENT_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
