"""Reapply each texture look to a fresh native baseline and check portability."""
import hashlib
import json
import sys
from pathlib import Path
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wrapper import eyes, materials


def main():
    checks = []
    with np.load(ROOT/'assets/gnm/gnm_head.npz', allow_pickle=False) as source:
        native_uvs = source['quad_uvs']
    for index in range(1, 6):
        look = f'look_{index:02d}'
        bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/gnm/scene_baseline.blend'))
        materials.apply_look(look)
        eyes.reset()
        for obj in bpy.data.objects:
            if 'gnm_component' not in obj:
                continue
            ids = np.array([v.value for v in obj.data.attributes['gnm_quad_id'].data])
            actual = np.array([d.uv[:] for d in obj.data.uv_layers.active.data], dtype=np.float32)
            checks.append({'test': look+': fresh '+obj.name+' native UVs unchanged', 'passed': bool(np.array_equal(actual, native_uvs[ids].reshape(-1, 2)))})
            checks.append({'test': look+': '+obj.name+' has only the native UV layer', 'passed': len(obj.data.uv_layers) == 1})
        used = [image for image in bpy.data.images if image.name.startswith(('skin_', 'eye_'))]
        checks.append({'test': look+': seven material images packed', 'passed': len(used) == 7 and all(bool(image.packed_file) for image in used)})
        checks.append({'test': look+': geometric versus apparent pupil semantics declared', 'passed': 'refraction' in bpy.context.scene['pupil_label_semantics']})
        checks.append({'test': look+': calibrated camera preserved', 'passed': np.allclose(bpy.context.scene.camera.location, (0, -.4, 0)) and bpy.context.scene.camera.data.lens == 40})
        before = eyes.state()
        eyes.move(1, 1)
        eyes.reset()
        checks.append({'test': look+': deterministic geometric reset', 'passed': eyes.state() == before})
    report = {'status': 'PASS' if all(c['passed'] for c in checks) else 'FAIL',
              'passed': sum(c['passed'] for c in checks), 'failed': sum(not c['passed'] for c in checks),
              'checks': checks, 'fresh_scene': 'work/gnm/scene_baseline.blend reloaded independently for every look',
              'scope': 'Direct native-UV material portability. Does not validate final visual realism, animated lids or refracted apparent pupil centers.'}
    (ROOT/'tests/milestone2/portability_report.json').write_text(json.dumps(report, indent=2)+'\n')
    print('MATERIAL_PORTABILITY', report['status'], report['passed'], 'passed', report['failed'], 'failed', flush=True)
    if report['failed']:
        raise RuntimeError('Texture portability check failed')


if __name__ == '__main__':
    main()
