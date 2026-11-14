"""Add a separate authored fixation/hold demo and render actual Cycles frames."""
import hashlib
import json
from pathlib import Path
import sys
import time

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
from wrapper import expressions, eyes, lids
from build_gaze_lid_rig import clamp_action
from render_device import configure


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    folder = ROOT/'work/review/eye_refinement'
    path = folder/'IRISX_EYE_REFINEMENT.blend'
    before_hash = sha(path)
    bpy.ops.wm.open_mainfile(filepath=str(path), use_scripts=False)
    scene = bpy.context.scene
    owners = [bpy.data.objects['GNM_skin'].data.shape_keys,
              bpy.data.objects['GazeRig'], bpy.data.objects['FixationTarget']]
    for owner in owners:
        owner.animation_data.action = None
    timeline = [(1,0,0,1), (10,0,0,1), (14,-.8,.08,1), (30,-.8,.08,1),
                (34,.8,.08,1), (50,.8,.08,1), (54,0,.8,1), (66,0,.8,1),
                (70,0,-.7,1), (78,0,-.7,1), (80,0,-.7,.5),
                (82,0,-.7,0), (83,0,-.7,0), (86,0,0,1), (96,0,0,1)]
    for frame,h,v,opening in timeline:
        eyes.move(h,v); lids.set_opening(opening); expressions.set_brows(0)
        bpy.data.objects['FixationTarget'].keyframe_insert(data_path='location', frame=frame)
        for side in ('L','R'):
            bpy.data.objects['GazeRig'].pose.bones['eye.'+side].keyframe_insert(data_path='rotation_quaternion', frame=frame)
            for name in ('Blink.', 'Brow.Raise.'):
                bpy.data.objects['GNM_skin'].data.shape_keys.key_blocks[name+side].keyframe_insert(data_path='value', frame=frame)
    names = []
    for owner,label in zip(owners, ('lids and brows', 'eyes', 'target')):
        clamp_action(owner, 'IrisX | natural_review | '+label)
        owner.animation_data.action.use_fake_user = True
        names.append(owner.animation_data.action.name)
    library = json.loads(scene['expression_actions'])
    library['natural_review'] = names
    scene['expression_actions'] = json.dumps(library)
    scene['natural_review_note'] = 'Authored short gaze shifts and held fixations; 96 frames at 24 fps. Original three calibrated actions retained. This is not measured human kinematics.'
    scene.frame_start = 1; scene.frame_end = 96; scene.render.fps = 24
    scene.frame_set(1)
    scene.camera = bpy.data.objects['RenderCamera']
    # Preserve full-size still quality in the editable saved candidate.
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    receipt_path = folder/'render_receipt.json'
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    receipt['appearance_scene_before_demo_sha256'] = before_hash
    receipt['scene_sha256'] = sha(path)
    receipt['demo_builder_sha256'] = sha(Path(__file__))
    receipt['demo_timeline'] = timeline
    receipt_path.write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    configure()
    scene.render.engine = 'CYCLES'
    scene.camera = bpy.data.objects['Review_macro']
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.cycles.seed = 0; scene.cycles.use_animated_seed = False
    scene.render.use_persistent_data = True
    frames = folder/'motion_frames'
    frames.mkdir(exist_ok=True)
    manifest = {'status': 'RUNNING', 'scene_sha256': sha(path), 'frames': [],
                'fps': 24, 'resolution': [512,512], 'samples': 32,
                'scope': 'Actual Cycles eye close-up review with authored fixation holds; no final realism approval.'}
    started = time.perf_counter()
    for frame in range(1,97):
        scene.frame_set(frame)
        output = frames/f'frame_{frame:03d}.png'
        scene.render.filepath = str(output)
        bpy.ops.render.render(write_still=True)
        manifest['frames'].append({'frame': frame, 'file': str(output.relative_to(folder)),
                                   'sha256': sha(output), 'state': expressions.state()})
        (folder/'motion.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
        print('EYE_REVIEW_FRAME', frame, flush=True)
    encoded = bpy.data.scenes.new('IrisX | eye refinement video')
    bpy.context.window.scene = encoded
    encoded.render.resolution_x = encoded.render.resolution_y = 512
    encoded.render.resolution_percentage = 100; encoded.render.fps = 24
    encoded.render.image_settings.media_type = 'VIDEO'
    encoded.render.image_settings.file_format = 'FFMPEG'
    encoded.render.ffmpeg.format = 'MPEG4'; encoded.render.ffmpeg.codec = 'H264'
    encoded.render.ffmpeg.audio_codec = 'NONE'; encoded.render.ffmpeg.constant_rate_factor = 'HIGH'
    encoded.render.filepath = str(folder/'eye_refinement_review.mp4')
    encoded.view_settings.view_transform = 'Standard'; encoded.view_settings.look = 'None'
    editor = encoded.sequence_editor_create()
    strip = editor.strips.new_image('Actual rendered eye frames', filepath=str(frames/'frame_001.png'), channel=1, frame_start=1)
    for frame in range(2,97):
        strip.elements.append(f'frame_{frame:03d}.png')
    encoded.frame_start = 1; encoded.frame_end = 96
    bpy.ops.render.render(animation=True)
    manifest['status'] = 'COMPLETE'; manifest['runtime_s'] = time.perf_counter()-started
    manifest['video_sha256'] = sha(folder/'eye_refinement_review.mp4')
    (folder/'motion.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print('EYE_REVIEW_VIDEO_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
