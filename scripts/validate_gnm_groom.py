"""Reopen the delivered static review scenes and check fit/calibration data.

These are geometric/portability checks, not a visual realism score.
"""
import argparse
import json
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wrapper import eyes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scene', type=Path)
    parser.add_argument('--report', type=Path, default=ROOT/'tests/milestone2/groom_report.json')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    with np.load(ROOT/'assets/gnm/gnm_head.npz', allow_pickle=False) as source:
        native_uv = source['quad_uvs']
        native_faces = source['quads']
        original = source['template_vertex_positions']
        names = source['joint_names'].tolist()
        joints = source['template_joint_positions']
        mid = (joints[names.index('left_eye')]+joints[names.index('right_eye')])/2
    original = (original-mid)@np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]])
    checks, metrics = [], {}

    def check(name, condition):
        checks.append({'test': name, 'passed': bool(condition)})

    paths = [args.scene.resolve()] if args.scene else [ROOT/'work/gnm'/f'scene_look_{i:02d}_realism.blend' for i in range(1, 6)]
    for path in paths:
        bpy.ops.wm.open_mainfile(filepath=str(path))
        scene = bpy.context.scene
        look = scene['texture_look']
        prefix = look+': '
        head = bpy.data.objects['GNM_skin']
        for obj in (head, bpy.data.objects['Eye_L'], bpy.data.objects['Eye_R']):
            mesh = obj.data
            ids = np.array([v.value for v in mesh.attributes['gnm_quad_id'].data])
            vertices = np.array([v.value for v in mesh.attributes['gnm_vertex_id'].data])
            uv = np.array([v.uv[:] for v in mesh.uv_layers.active.data], dtype=np.float32)
            check(prefix+obj.name+' exact native UVs', np.array_equal(uv, native_uv[ids].reshape(-1, 2)))
            check(prefix+obj.name+' unchanged native topology',
                  np.array_equal(np.array([[vertices[i] for i in p.vertices] for p in mesh.polygons]), native_faces[ids]))
            if obj == head:
                coords = np.array([v.co[:] for v in mesh.vertices])
                check(prefix+'unchanged head rest geometry', np.max(np.abs(coords-original[vertices])) < 1e-7)

        hair = bpy.data.objects['Scalp_swept_back_hair']
        positions = np.empty(len(hair.data.points)*3, dtype=np.float32)
        hair.data.attributes['position'].data.foreach_get('vector', positions)
        positions = positions.reshape(-1, 12, 3)
        radii = np.empty(len(hair.data.points), dtype=np.float32)
        hair.data.attributes['radius'].data.foreach_get('value', radii)
        check(prefix+'finite positive native hair data', hair.type == 'CURVES' and np.isfinite(positions).all()
              and np.isfinite(radii).all() and radii.min() > 0 and radii.max() < .00005)
        check(prefix+'scalp groom follows rigid head object', hair.parent == head)
        deps = bpy.context.evaluated_depsgraph_get()
        skin = BVHTree.FromObject(head, deps)
        root_errors, clearance = [], []
        for index in np.linspace(0, len(positions)-1, 512).astype(int):
            strand = [hair.matrix_world @ Vector(p) for p in positions[index]]
            near, normal, face, distance = skin.find_nearest(strand[0])
            root_errors.append(distance)
            for a, b in zip(strand, strand[1:]):
                for t in (.25, .50, .75, 1):
                    point = a.lerp(b, t)
                    near, normal, face, distance = skin.find_nearest(point)
                    clearance.append((point-near).dot(normal))
        check(prefix+'512 scalp roots remain within 0.10 mm of skin', max(root_errors) < .00010)
        check(prefix+'sampled strand interiors clear the skin within 0.03 mm tolerance', min(clearance) > -.00003)
        metrics[look] = {'strand_count': len(positions), 'sampled_strands': len(root_errors),
                         'sampled_interior_positions': len(clearance),
                         'max_root_distance_m': max(root_errors), 'min_signed_clearance_m': min(clearance)}

        neutral = eyes.state()
        camera = scene.camera.matrix_world.copy()
        pivots = [bpy.data.objects['Eye_'+s].matrix_world.translation.copy() for s in ('L', 'R')]
        for name, h, v in [('left', -1, 0), ('right', 1, 0), ('up', 0, 1), ('down', 0, -1)]:
            eyes.move(h, v)
            check(prefix+name+' preserves binocular pivots', all((bpy.data.objects['Eye_'+s].matrix_world.translation-p).length < 1e-7
                  for s, p in zip(('L', 'R'), pivots)))
        eyes.reset()
        check(prefix+'neutral gaze and geometric labels reset exactly', neutral == eyes.state())
        check(prefix+'fixed calibrated camera preserved', scene.camera.name == 'RenderCamera' and scene.camera.data.lens == 40
              and (scene.camera.location-Vector((0, -.4, 0))).length < 1e-7
              and np.array_equal(np.array(camera), np.array(scene.camera.matrix_world)))
        check(prefix+'35 cm neutral fixation preserved', (bpy.data.objects['FixationTarget'].location-Vector((0, -.35, 0))).length < 1e-7)
        check(prefix+'seven material images still packed', len([i for i in bpy.data.images if i.name.startswith(('skin_', 'eye_')) and i.packed_file]) == 7)
        viewports = [a.spaces.active for screen in bpy.data.screens for a in screen.areas if a.type == 'VIEW_3D']
        check(prefix+'opens in Material Preview camera view without rig overlays', bool(viewports) and all(s.shading.type == 'MATERIAL'
              and not s.overlay.show_overlays and s.region_3d.view_perspective == 'CAMERA' for s in viewports))
        check(prefix+'viewport denoising and refractive lighting enabled', scene.cycles.use_preview_denoising
              and scene.cycles.preview_samples >= 128 and scene.cycles.caustics_refractive)

    report = {'status': 'PASS' if all(c['passed'] for c in checks) else 'FAIL',
              'passed': sum(c['passed'] for c in checks), 'failed': sum(not c['passed'] for c in checks),
              'checks': checks, 'measured_groom_fit': metrics,
              'scope': 'Reopened static groom, sampled surface clearance, native UV/topology and calibration. Does not certify photorealism, deformation binding, blink motion or apparent refracted pupil labels.'}
    args.report.write_text(json.dumps(report, indent=2)+'\n')
    print('GROOM_REOPEN_AUDIT', report['status'], report['passed'], 'passed', report['failed'], 'failed', flush=True)
    if report['failed']:
        raise RuntimeError('Saved scene check failed')


if __name__ == '__main__':
    main()
