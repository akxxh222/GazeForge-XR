"""Reproducible native expression captures inside Blender 5.2.

Every output frame evaluates and renders the 3D scene. The three bundled
actions are retimed together; default six-second/24-fps sampling is exactly
the accepted Milestone 3 timeline. No image interpolation is used.
"""
import hashlib
import json
import math
import numbers
from pathlib import Path
import time

import bpy
from mathutils import Vector
from . import eyes, lids, expressions

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENE = ROOT / 'scene.blend'
MODES = ('left', 'right', 'generate_motion')
LOOKS = tuple(f'look_{i:02d}' for i in range(1, 6))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    """Replace a checkpoint atomically so interrupted runs can be resumed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    temporary.replace(path)


def validate_options(mode, texture_id, duration_s, fps, resolution, samples):
    if mode not in MODES:
        raise ValueError('mode must be left, right or generate_motion')
    if texture_id not in LOOKS:
        raise ValueError('texture_id must be look_01 through look_05')
    if isinstance(duration_s, bool) or not isinstance(duration_s, numbers.Real):
        raise TypeError('duration_s must be real')
    if not math.isfinite(duration_s) or not 1 <= duration_s <= 15:
        raise ValueError('duration_s must be finite, between 1 and 15 seconds')
    for name, value, low, high in [('fps', fps, 1, 60), ('resolution', resolution, 128, 4096),
                                    ('samples', samples, 1, 4096)]:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(name + ' must be an integer')
        if not low <= value <= high:
            raise ValueError(f'{name} must be in [{low}, {high}]')
    if abs(duration_s * fps - round(duration_s * fps)) > 1e-8 or duration_s * fps < 2:
        raise ValueError('duration_s * fps must be a whole number of at least two frames')
    return round(duration_s * fps)


def _apply_look(texture_id):
    """Apply the exported maps to the native material regions."""
    if not bpy.context.scene.get('portable_look_schema'):
        raise ValueError('Load the submitted scene before applying a texture look')
    from .submission_looks import apply_look
    return apply_look(texture_id)


def capture_contract():
    scene = bpy.context.scene
    camera = scene.camera
    return {
        'camera': {'name': camera.name, 'world_matrix': [list(r) for r in camera.matrix_world],
                   'lens_mm': camera.data.lens, 'sensor_width_mm': camera.data.sensor_width,
                   'clip_m': [camera.data.clip_start, camera.data.clip_end],
                   'distance_from_eye_midpoint_m': (camera.matrix_world.translation - eyes.midpoint()).length},
        'lights': [{'name': o.name, 'type': o.data.type, 'energy': o.data.energy,
                    'color': list(o.data.color), 'world_matrix': [list(r) for r in o.matrix_world]}
                   for o in sorted(scene.objects, key=lambda o: o.name) if o.type == 'LIGHT'],
        'world': {'name': scene.world.name, 'nodes': [
            {'name': n.name, 'type': n.type, 'inputs': {
                socket.name: (list(socket.default_value) if hasattr(socket.default_value, '__len__') else socket.default_value)
                for socket in n.inputs if hasattr(socket, 'default_value') and not socket.is_linked}}
            for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND']},
        'color_management': {'view_transform': scene.view_settings.view_transform,
                             'look': scene.view_settings.look, 'exposure': scene.view_settings.exposure,
                             'gamma': scene.view_settings.gamma},
        'render': {'engine': scene.render.engine, 'resolution': [scene.render.resolution_x, scene.render.resolution_y],
                   'percentage': scene.render.resolution_percentage, 'samples': scene.cycles.samples,
                   'seed': scene.cycles.seed, 'animated_seed': scene.cycles.use_animated_seed,
                   'denoising': scene.cycles.use_denoising, 'motion_blur': scene.render.use_motion_blur},
        'target_plane_distance_m': .35, 'target_bounds_m': .05,
        'label_semantics': 'Geometric aperture centroid and pinhole projection; not an apparent pupil centroid through refractive cornea',
        'eye_sides': 'Native anatomical labels: L is image right; R is image left',
    }


def _pose():
    state = expressions.state()
    for side in ('L', 'R'):
        eye = bpy.data.objects['Eye_' + side]
        direction = (eye.matrix_world.to_3x3() @ Vector((0, 1, 0))).normalized()
        target = bpy.data.objects['FixationTarget'].location - eye.matrix_world.translation
        state['aim_error_deg_' + side] = math.degrees(direction.angle(target))
    return state


def _prepare(texture_id, resolution, samples, scene_path):
    path = Path(scene_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    # Always load a clean source. Sequential calls cannot accumulate look edits.
    bpy.ops.wm.open_mainfile(filepath=str(path), use_scripts=False)
    scene = bpy.context.scene
    if not scene.get('expression_actions'):
        raise ValueError('Scene must contain the completed native expression action bundles')
    appearance = _apply_look(texture_id)
    from scripts.render_device import configure
    device = configure()
    scene.camera = bpy.data.objects['RenderCamera']
    scene.render.engine = 'CYCLES'
    scene.render.resolution_x = scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = scene.render.pixel_aspect_y = 1
    scene.render.image_settings.media_type = 'IMAGE'
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    scene.render.use_file_extension = True
    scene.render.use_motion_blur = False
    scene.render.use_persistent_data = True
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.seed = 0
    scene.cycles.use_animated_seed = False
    if abs(capture_contract()['camera']['distance_from_eye_midpoint_m'] - .4) > 1e-6:
        raise ValueError('Capture camera is not calibrated to 40 cm')
    return scene, {'scene_sha256': sha(path), 'scene_path': str(path), 'appearance': appearance,
                   'device': device, 'blender_version': bpy.app.version_string,
                   'code_sha256': {name: sha(ROOT / 'wrapper' / name) for name in
                                    ('sequences.py', 'expressions.py', 'eyes.py', 'lids.py')},
                   'contract': capture_contract()}


def _checkpoint(folder, config, resume):
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / 'capture.json'
    if path.exists():
        saved = json.loads(path.read_text(encoding='utf-8'))
        if not resume:
            raise FileExistsError(f'{path} exists; use resume=True or a new output directory')
        if saved['config'] != config:
            raise ValueError('Resume configuration/provenance differs; choose a new output directory')
        return saved
    if any(folder.iterdir()):
        raise FileExistsError('Capture directory is not empty: ' + str(folder))
    return {'status': 'RUNNING', 'config': config, 'frames': [], 'render_runtime_s': 0.}


def _render_frame(scene, folder, receipt, record, resume):
    index = record['frame']
    previous = next((r for r in receipt['frames'] if r['frame'] == index), None)
    path = folder / record['file']
    if resume and previous and path.is_file():
        if previous['pose'] == record['pose'] and sha(path) == previous['sha256']:
            print('IRISX_RESUME', str(path), flush=True)
            return
    started = time.perf_counter()
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    record['sha256'] = sha(path)
    record['render_seconds'] = time.perf_counter() - started
    receipt['frames'] = sorted([r for r in receipt['frames'] if r['frame'] != index] + [record], key=lambda r: r['frame'])
    receipt['render_runtime_s'] += record['render_seconds']
    write_json(folder / 'capture.json', receipt)
    print('IRISX_FRAME', str(path), record['render_seconds'], flush=True)


def _encode(folder, records, fps, resolution, output):
    original = bpy.context.scene
    encoded = bpy.data.scenes.new('IrisX | encode actual frames')
    try:
        bpy.context.window.scene = encoded
        encoded.render.resolution_x = encoded.render.resolution_y = resolution
        encoded.render.resolution_percentage = 100
        encoded.render.fps = fps
        encoded.render.fps_base = 1
        encoded.render.image_settings.media_type = 'VIDEO'
        encoded.render.image_settings.file_format = 'FFMPEG'
        encoded.render.ffmpeg.format = 'MPEG4'
        encoded.render.ffmpeg.codec = 'H264'
        encoded.render.ffmpeg.audio_codec = 'NONE'
        encoded.render.ffmpeg.constant_rate_factor = 'HIGH'
        encoded.render.filepath = str(output)
        encoded.view_settings.view_transform = 'Standard'
        encoded.view_settings.look = 'None'
        editor = encoded.sequence_editor_create()
        strip = editor.strips.new_image('Actual Cycles sequence', filepath=str(folder / records[0]['file']), channel=1, frame_start=1)
        for record in records[1:]:
            strip.elements.append(Path(record['file']).name)
        encoded.frame_start, encoded.frame_end = 1, len(records)
        bpy.ops.render.render(animation=True)
    finally:
        bpy.context.window.scene = original
        bpy.data.scenes.remove(encoded)


def render_expression(mode, texture_id='look_01', duration_s=6, fps=24, output_dir=None,
                      resolution=720, samples=64, resume=False, scene_path=DEFAULT_SCENE):
    """Render one mode, returning its durable frame-to-pose manifest path.

    Positive h means image right. Left/right refer to the viewer's direction.
    A held pose is still rendered on every frame; it is not a copied still.
    """
    count = validate_options(mode, texture_id, duration_s, fps, resolution, samples)
    scene, provenance = _prepare(texture_id, resolution, samples, scene_path)
    expressions.use_action(mode)
    scene.render.fps, scene.render.fps_base = fps, 1
    scene.frame_end = count
    expressions.set_pupil_constriction(.7)
    folder = (Path(output_dir) if output_dir is not None else ROOT / 'work/milestone4').resolve() / mode
    config = {'schema': 'IrisX expression capture 1', 'mode': mode, 'texture_id': texture_id,
              'duration_s': float(duration_s), 'fps': fps, 'frame_count': count,
              'resolution': resolution, 'samples': samples, **provenance}
    receipt = _checkpoint(folder, config, resume)
    for index in range(count):
        source_frame = 1 + 143 * index / (count - 1)
        frame = math.floor(source_frame)
        scene.frame_set(frame, subframe=source_frame-frame)
        record = {'frame': index + 1, 'time_s': index / fps, 'source_frame': source_frame,
                  'file': f'frames/frame_{index + 1:04d}.png', 'pose': _pose()}
        (folder / 'frames').mkdir(exist_ok=True)
        if capture_contract() != provenance['contract']:
            raise RuntimeError('Camera, lighting or render settings changed during capture')
        _render_frame(scene, folder, receipt, record, resume)
    output = folder / (mode + '.mp4')
    _encode(folder, receipt['frames'], fps, resolution, output)
    receipt['video'] = {'file': output.name, 'sha256': sha(output), 'duration_s': count / fps,
                        'frames': count, 'fps': fps, 'resolution': [resolution, resolution]}
    receipt['status'] = 'COMPLETE'
    write_json(folder / 'capture.json', receipt)
    return folder / 'capture.json'


def render_clockwise(texture_id='look_01', output_dir=None, samples=128, resume=False, scene_path=DEFAULT_SCENE):
    """Capture the ten prescribed open-eye 1024px samples, clockwise from top."""
    validate_options('generate_motion', texture_id, 6, 24, 1024, samples)
    scene, provenance = _prepare(texture_id, 1024, samples, scene_path)
    folder = (Path(output_dir) if output_dir is not None else ROOT / 'work/milestone4').resolve() / 'clockwise'
    config = {'schema': 'IrisX clockwise capture 1', 'texture_id': texture_id,
              'samples': samples, 'resolution': 1024, **provenance}
    receipt = _checkpoint(folder, config, resume)
    with expressions.manual():
        for index in range(10):
            theta = 2 * math.pi * index / 10
            expressions.reset()
            eyes.move(math.sin(theta), math.cos(theta))
            record = {'frame': index, 'theta': theta, 'file': f'renders/frame_{index:02d}.png', 'pose': _pose()}
            (folder / 'renders').mkdir(exist_ok=True)
            if capture_contract() != provenance['contract']:
                raise RuntimeError('Camera, lighting or render settings changed during capture')
            _render_frame(scene, folder, receipt, record, resume)
        expressions.reset()
    metadata = {'schema': 'IrisX geometric pupil metadata 1', 'calibration': provenance['contract'],
                'scene_sha256': provenance['scene_sha256'], 'frames': [
                    {**r['pose'], 'frame': r['frame'], 'theta': r['theta'],
                     'image': r['file'], 'image_sha256': r['sha256']} for r in receipt['frames']]}
    write_json(folder / 'metadata.json', metadata)
    receipt['status'] = 'COMPLETE'
    receipt['metadata_sha256'] = sha(folder / 'metadata.json')
    write_json(folder / 'capture.json', receipt)
    return folder / 'capture.json'
