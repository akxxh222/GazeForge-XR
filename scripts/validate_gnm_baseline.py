"""Independent native-data, calibration and draft-render checks inside Blender."""
import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]
from render_device import configure
from wrapper import eyes


def main(render):
    output = ROOT / 'tests/milestone1'
    output.mkdir(parents=True, exist_ok=True)
    checks = []

    def check(name, passed, details=None):
        checks.append({'test': name, 'passed': bool(passed), 'details': details})

    with np.load(ROOT / 'assets/gnm/gnm_head.npz', allow_pickle=False) as src:
        source_uvs = src['quad_uvs']
        source_quads = src['quads']
        source_vertices = src['template_vertex_positions']
        native_centers = src['template_joint_positions'][2:4]
        group_names = src['vertex_group_names'].tolist()
        groups = {name: src['vertex_groups'][i] for i, name in enumerate(group_names)}
    for component, center in zip(('left_eye', 'right_eye'), native_centers):
        sclera = source_vertices[(groups[component] > .5) & (groups['scleras'] > .5) & (groups['eye_interiors'] > .5)]
        fitted = np.linalg.lstsq(np.c_[2*sclera, np.ones(len(sclera))], np.square(sclera).sum(1), rcond=None)[0][:3]
        radius = np.linalg.norm(sclera-center, axis=1)
        error = float(np.linalg.norm(fitted-center))
        check(component + ': scleral sphere center matches joint pivot', error < 1e-6, {'fit_error_m': error})
        check(component + ': native scleral globe near spherical', np.ptp(radius)/np.median(radius) < .03,
              {'median_radius_m': float(np.median(radius)), 'radius_range_m': [float(radius.min()), float(radius.max())],
               'note': 'Native scleral surface retained, including its small anatomical departure from an ideal sphere; cornea excluded from sphere fit.'})
    transform = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], dtype=np.float32)
    expected_vertices = (source_vertices - native_centers.mean(0)) @ transform.T
    all_faces = []
    for obj in bpy.data.objects:
        if 'gnm_component' not in obj:
            continue
        mesh = obj.data
        face_ids = np.array([v.value for v in mesh.attributes['gnm_quad_id'].data])
        vertex_ids = np.array([v.value for v in mesh.attributes['gnm_vertex_id'].data])
        all_faces.extend(face_ids.tolist())
        actual_uvs = np.array([v.uv[:] for v in mesh.uv_layers.active.data], dtype=np.float32)
        expected_uvs = source_uvs[face_ids].reshape(-1, 2)
        check(obj.name + ': exact native loop UVs', np.array_equal(actual_uvs, expected_uvs))
        faces = np.array([[vertex_ids[i] for i in p.vertices] for p in mesh.polygons])
        check(obj.name + ': original face winding and vertex IDs', np.array_equal(faces, source_quads[face_ids]))
        coords = np.array([v.co[:] for v in mesh.vertices])
        if obj.name.startswith('Eye_'):
            side_index = 0 if obj.name == 'Eye_L' else 1
            center = (native_centers[side_index] - native_centers.mean(0)) @ transform.T
            coords = coords * np.array([-1, -1, 1]) + center
        error = float(np.max(np.abs(coords - expected_vertices[vertex_ids])))
        check(obj.name + ': native rest coordinates preserved', error < 1e-7, {'max_error_m': error})
    check('Every native quad imported exactly once', sorted(all_faces) == list(range(len(source_quads))))
    check('Metric units', bpy.context.scene.unit_settings.scale_length == 1)
    check('Camera locked 40 cm ahead', np.allclose(bpy.context.scene.camera.location, (0, -.4, 0), atol=1e-8))
    check('Eye midpoint at origin', eyes.midpoint().length < 1e-7)
    camera_initial = bpy.context.scene.camera.matrix_world.copy()
    poses = {}
    for name, (h, v) in {'reset': (0, 0), 'left': (-1, 0), 'right': (1, 0), 'up': (0, 1), 'down': (0, -1)}.items():
        eyes.move(h, v)
        state = eyes.state()
        poses[name] = state
        target = np.array(state['fixation_world_m'])
        check(name + ': 35 cm target plane and bounds', np.allclose(target, (.05*h, -.35, .05*v), atol=1e-7))
        for side in ('L', 'R'):
            eye = bpy.data.objects['Eye_' + side]
            center = np.array(eye.matrix_world.translation)
            aim = np.array(eye.matrix_world.to_3x3() @ Vector((0, 1, 0)))
            direction = target - center
            alignment = float(np.dot(aim, direction / np.linalg.norm(direction)))
            check(name + ': ' + side + ' aims at common target', alignment > 1-1e-6)
            actual = np.array(state['eye_center_3D_' + side])
            base = (native_centers[0 if side == 'L' else 1] - native_centers.mean(0)) @ transform.T
            check(name + ': ' + side + ' pivot invariant', np.linalg.norm(actual-base) < 1e-7)
            check(name + ': ' + side + ' rigid transform', np.allclose(np.array(eye.matrix_world.to_3x3()).T @ np.array(eye.matrix_world.to_3x3()), np.eye(3), atol=1e-6))
            point = np.array(state['pupil_center_3D_' + side] + [1])
            q = np.array(state['camera_matrix']) @ point
            check(name + ': ' + side + ' independent projective matrix', np.max(np.abs(q[:2]/q[2] - state['pupil_center_2D_' + side])) < .001)
    for side in ('L', 'R'):
        for name, axis, sign in [('left', 0, -1), ('right', 0, 1), ('up', 1, -1), ('down', 1, 1)]:
            delta = poses[name]['pupil_center_2D_' + side][axis] - poses['reset']['pupil_center_2D_' + side][axis]
            check(name + ': ' + side + ' pupil projection direction', delta*sign > 2, {'shift_px': delta})
    eyes.reset()
    check('Reset restores exact transforms', eyes.state() == poses['reset'])
    eyes.reset()
    check('Repeated reset exact', eyes.state() == poses['reset'])
    check('Camera unchanged throughout controls', np.array_equal(camera_initial, bpy.context.scene.camera.matrix_world))

    timings = []
    device = configure()
    if render:
        scene = bpy.context.scene
        for name in ('reset', 'left', 'right', 'up', 'down'):
            eyes.move(*{'reset': (0, 0), 'left': (-1, 0), 'right': (1, 0), 'up': (0, 1), 'down': (0, -1)}[name])
            scene.render.resolution_percentage = 100 if name == 'reset' else 50
            started = time.perf_counter()
            eyes.render(output / (name + '.png'))
            timings.append({'pose': name, 'seconds': time.perf_counter()-started, 'resolution': int(1024*scene.render.resolution_percentage/100), 'samples': scene.cycles.samples})
        eyes.reset()
        scene.render.resolution_percentage = 100
        for obj in scene.objects:
            if obj.type == 'MESH':
                for slot in obj.material_slots:
                    slot.link = 'OBJECT'
                    slot.material = bpy.data.materials['GNM UV diagnostic checker']
        started = time.perf_counter()
        eyes.render(output / 'native_uv_checker.png')
        timings.append({'pose': 'UV checker', 'seconds': time.perf_counter()-started, 'resolution': 1024, 'samples': scene.cycles.samples})
    report = {'status': 'PASS' if all(c['passed'] for c in checks) else 'FAIL',
              'passed': sum(c['passed'] for c in checks), 'failed': sum(not c['passed'] for c in checks),
              'checks': checks, 'device': device, 'render_timings': timings,
              'model_sha256': hashlib.sha256((ROOT/'assets/gnm/gnm_head.npz').read_bytes()).hexdigest(),
              'visual_status': 'Draft geometry/UV evidence only. Photorealism, eyelids, texture variants and GNM optical label validation remain pending.'}
    (output/('report.json' if render else 'geometry_report.json')).write_text(json.dumps(report, indent=2) + '\n')
    (output/'direction_metadata.json').write_text(json.dumps(poses, indent=2) + '\n')
    print('GNM_BASELINE_REPORT', report['status'], report['passed'], 'passed', report['failed'], 'failed', flush=True)
    if report['failed']:
        raise RuntimeError('GNM baseline checks failed; inspect tests/milestone1/report.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--render', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    main(args.render)
