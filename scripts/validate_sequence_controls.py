"""Exercise expression inputs, portability and retimed poses without rendering."""
import json
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wrapper import sequences, expressions
from scripts.validate_lid_review import digest


def main():
    checks, modes, looks = [], {}, {}

    def check(name, value):
        checks.append({'test': name, 'passed': bool(value)})
        if not value:
            print('FAILED', name, flush=True)

    defaults = dict(mode='left', texture_id='look_01', duration_s=6, fps=24, resolution=720, samples=64)
    for name, values in {
        'mode': ['Left', 'unknown', None], 'texture_id': ['missing', '../look_01', None],
        'duration_s': [True, '6', float('nan'), float('inf'), 0, 15.01, 1.01],
        'fps': [True, 0, 61, 24.5], 'resolution': [True, 127, 4097, 720.5],
        'samples': [True, 0, 4097, 64.5],
    }.items():
        for value in values:
            before = bpy.data.filepath
            output = ROOT / 'work/milestone4/invalid_input_must_not_exist'
            rejected = False
            try:
                options = {**defaults, name: value, 'output_dir': output}
                sequences.render_expression(**options)
            except (TypeError, ValueError):
                rejected = True
            check(f'{name}={value!r} rejected before scene/output mutation',
                  rejected and bpy.data.filepath == before and not output.exists())
    scene, provenance = sequences._prepare('look_01', 720, 64, sequences.DEFAULT_SCENE)
    components = [o.name for o in scene.objects if o.get('gnm_component')]
    native = {name: digest(bpy.data.objects[name].data) for name in components}
    for mode in sequences.MODES:
        expressions.use_action(mode)
        reference = sequences.capture_contract()
        center = {s: bpy.data.objects['Eye_' + s].matrix_world.translation.copy() for s in ('L', 'R')}
        rows, max_aim, max_shift = [], 0., 0.
        for frame in range(1, 145):
            scene.frame_set(frame)
            state = sequences._pose()
            h, v = state['input']['h'], state['input']['v']
            check(f'{mode} frame {frame}: bounds, fixed plane and bilateral aim',
                  abs(h) <= 1.000001 and abs(v) <= 1.000001
                  and abs(state['fixation_world_m'][1] + .35) < 1e-6
                  and max(state['aim_error_deg_' + s] for s in ('L', 'R')) < .05)
            check(f'{mode} frame {frame}: fixed camera, lights and render settings',
                  sequences.capture_contract() == reference)
            for side in ('L', 'R'):
                shift = (bpy.data.objects['Eye_' + side].matrix_world.translation - center[side]).length
                max_shift = max(max_shift, shift)
                max_aim = max(max_aim, state['aim_error_deg_' + side])
            rows.append({'frame': frame, 'h': h, 'v': v, 'opening_L': state['opening_L'], 'opening_R': state['opening_R']})
        check(mode + ': both physical centers fixed', max_shift < 1e-7)
        check(mode + ': starts/ends neutral and open', all(abs(rows[i][a]) < 1e-6 for i in (0, -1) for a in ('h', 'v'))
              and all(rows[i]['opening_' + s] == 1 for i in (0, -1) for s in ('L', 'R')))
        check(mode + ': at least one bilateral closure', any(r['opening_L'] < .001 and r['opening_R'] < .001 for r in rows))
        if mode in ('left', 'right'):
            sign = -1 if mode == 'left' else 1
            check(mode + ': reaches intended direction without opposite excursion',
                  max(sign * r['h'] for r in rows) > .99 and min(sign * r['h'] for r in rows) > -1e-6)
        else:
            check(mode + ': scans four cardinal directions',
                  all(max(r[a] * sign for r in rows) > .99 for a, sign in [('h', -1), ('h', 1), ('v', -1), ('v', 1)]))
        # Different output frame counts evaluate fractional source poses, not
        # duplicate pre-rendered pictures. Verify deterministic evaluation.
        for frame in (1., 27.345, 58.75, 96.125, 144.):
            whole = int(frame)
            scene.frame_set(whole, subframe=frame-whole)
            first = sequences._pose()
            scene.frame_set(1)
            scene.frame_set(whole, subframe=frame-whole)
            check(f'{mode}: deterministic source frame {frame}', first == sequences._pose())
        modes[mode] = {'poses': rows, 'maximum_aim_error_deg': max_aim, 'maximum_center_shift_m': max_shift}
    # Apply all five native look IDs in clean scenes and check optical and
    # canthal sharing. Appearance quality remains the separate M2 visual gate.
    for look in sequences.LOOKS:
        scene, receipt = sequences._prepare(look, 720, 64, sequences.DEFAULT_SCENE)
        head = bpy.data.objects['GNM_skin']
        for name in components:
            check(look + ' unchanged native Basis/UV/topology ' + name,
                  digest(bpy.data.objects[name].data) == native[name])
        check(look + ' canthal skin uses the same current material',
              all(o.data.materials[0] == head.data.materials[0] for o in scene.objects
                  if o.name.startswith('Lid_commissure_') and not o.hide_render))
        check(look + ' attributed iris and native cornea retained',
              all(bpy.data.objects['Eye_' + s].data.materials[1].get('license') == 'CC BY-SA 3.0'
                  and 'cornea' in bpy.data.objects['Eye_' + s].data.materials[3].name.lower() for s in ('L', 'R')))
        expected_prefix = look if look != 'look_01' else 'look_01'
        check(look + ' correct skin image channels loaded', all(
            Path(n.image.filepath).parent.name == expected_prefix for n in head.data.materials[0].node_tree.nodes
            if n.type == 'TEX_IMAGE' and n.image))
        looks[look] = receipt['appearance']
    report = {'status': 'PASS' if all(c['passed'] for c in checks) else 'FAIL',
              'passed': sum(c['passed'] for c in checks), 'failed': sum(not c['passed'] for c in checks),
              'checks': checks, 'scene_sha256': provenance['scene_sha256'],
              'validator_sha256': sequences.sha(Path(__file__)), 'modes': modes, 'looks': looks,
              'scope': 'API rejection, actual timeline poses, deterministic retiming, calibration and native look application. M3 collision evidence is separate; this is not a photorealism score.'}
    sequences.write_json(ROOT / 'tests/milestone4/controls.json', report)
    print('IRISX_SEQUENCE_CONTROLS', report['status'], report['passed'], report['failed'], flush=True)
    if report['failed']:
        raise RuntimeError('Sequence control checks failed')


if __name__ == '__main__':
    main()
