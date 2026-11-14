"""Read-only pupil-axis and binocular timing diagnosis for the saved scene."""
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wrapper import expressions


def main():
    source = ROOT / 'work/milestone3/final/IRISX_MILESTONE3.blend'
    bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
    scene = bpy.context.scene
    # Transform-only diagnosis: avoid recomputing the independent skin/hair
    # collision and surface-binding networks at all 1719 sampled poses.
    keep = {'GazeRig', 'FixationTarget', 'Eye_L', 'Eye_R'}
    for obj in scene.objects:
        if obj.name not in keep:
            obj.hide_viewport = True
        else:
            for modifier in obj.modifiers:
                modifier.show_viewport = False
    rows = []
    intrinsic = {}
    for side in ('L', 'R'):
        eye = bpy.data.objects['Eye_' + side]
        ids = sorted({i for face in eye.data.polygons if face.material_index == 2 for i in face.vertices})
        center = sum((eye.data.vertices[i].co for i in ids), Vector()) / len(ids)
        intrinsic[side] = {
            'pupil_surface_centroid_local_m': list(center),
            'centroid_axis_offset_deg': math.degrees(center.angle(Vector((0, 1, 0)))),
            'constraints': [{'type': c.type, 'target': c.target.name if c.target else None,
                             'subtarget': getattr(c, 'subtarget', '')} for c in eye.constraints],
        }
    for mode in ('left', 'right', 'generate_motion'):
        expressions.use_action(mode)
        for index in range(573):
            frame = 1 + index / 4
            scene.frame_set(int(frame), subframe=frame-int(frame))
            depsgraph = bpy.context.evaluated_depsgraph_get()
            target = bpy.data.objects['FixationTarget'].evaluated_get(depsgraph).matrix_world.translation
            entry = {'mode': mode, 'frame': frame, 'target_m': list(target)}
            directions = []
            for side in ('L', 'R'):
                eye = bpy.data.objects['Eye_' + side].evaluated_get(depsgraph)
                center = eye.matrix_world.translation
                axis = (eye.matrix_world.to_3x3() @ Vector((0, 1, 0))).normalized()
                wanted = (target-center).normalized()
                pupil = Vector(intrinsic[side]['pupil_surface_centroid_local_m']).normalized()
                actual = (eye.matrix_world.to_3x3() @ pupil).normalized()
                entry[side] = {
                    'center_m': list(center), 'axis': list(axis),
                    'axis_target_error_deg': math.degrees(math.atan2(axis.cross(wanted).length, axis.dot(wanted))),
                    'pupil_axis_target_error_deg': math.degrees(math.atan2(actual.cross(wanted).length, actual.dot(wanted))),
                    'yaw_deg': math.degrees(math.atan2(axis.x, -axis.y)),
                    'pitch_deg': math.degrees(math.atan2(axis.z, math.hypot(axis.x, axis.y))),
                }
                directions.append(axis)
            entry['vergence_deg'] = math.degrees(directions[0].angle(directions[1]))
            rows.append(entry)
    summaries = {}
    for mode in ('left', 'right', 'generate_motion'):
        samples = [r for r in rows if r['mode'] == mode]
        opposite = []
        for a, b in zip(samples, samples[1:]):
            steps = [b[s]['yaw_deg']-a[s]['yaw_deg'] for s in ('L', 'R')]
            if min(abs(v) for v in steps) > .00001 and steps[0]*steps[1] < 0:
                opposite.append(b['frame'])
        summaries[mode] = {
            'samples': len(samples), 'opposite_horizontal_step_frames': opposite,
            'max_axis_target_error_deg': max(r[s]['axis_target_error_deg'] for r in samples for s in ('L','R')),
            'max_pupil_axis_target_error_deg': max(r[s]['pupil_axis_target_error_deg'] for r in samples for s in ('L','R')),
            'neutral': samples[0],
        }
    report = {'source': str(source), 'intrinsic': intrinsic, 'modes': summaries,
              'scope': 'Saved pupil Basis geometry and quarter-frame eye transforms. Unrelated surfaces hidden for transform diagnosis; no collision/optical appearance claim or assertion about edited GUI state.'}
    output = ROOT / 'work/diagnostics/binocular_coordination.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('IRISX_BINOCULAR_DIAGNOSIS', json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
