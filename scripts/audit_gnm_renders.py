"""Check material preview files against the current texture/shader/render sources."""
import hashlib
import json
import math
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite(value):
    if isinstance(value, dict):
        return all(finite(v) for v in value.values())
    if isinstance(value, list):
        return all(finite(v) for v in value)
    return not isinstance(value, (int, float)) or math.isfinite(value)


def main():
    checks = []

    def check(name, result):
        checks.append({'test': name, 'passed': bool(result)})

    expected_sources = {'appearance_code_sha256': sha(ROOT/'wrapper/appearance.py'),
                        'materials_code_sha256': sha(ROOT/'wrapper/materials.py'),
                        'groom_code_sha256': sha(ROOT/'wrapper/groom.py'),
                        'render_builder_sha256': sha(ROOT/'scripts/build_gnm_look.py')}
    for i in range(1, 6):
        key = f'look_{i:02d}'
        folder = ROOT/'tests/milestone2'/key
        metadata = json.loads((folder/'review_metadata.json').read_text())
        expected = {'front', 'macro', 'macro_left', 'macro_right', 'eye_closeup', 'side_left', 'side_right'} if i == 1 else {'front', 'macro'}
        check(key+': complete review metadata', {r['view'] for r in metadata} == expected and len(metadata) == len(expected))
        sources = {**expected_sources, 'texture_manifest_sha256': sha(ROOT/'textures'/key/'manifest.json')}
        for record in metadata:
            view = record['view']
            with Image.open(folder/(view+'.png')) as image:
                check(key+'/'+view+': actual 1024 RGB PNG', image.format == 'PNG' and image.size == (1024, 1024) and image.mode == 'RGB')
            check(key+'/'+view+': current texture, appearance, shader and render source',
                  all(record.get(k) == v for k, v in sources.items()))
            check(key+'/'+view+': refractive label semantics declared', 'refraction' in record['pupil_label_semantics'])
            labels = [record['camera_matrix']]+[record[k] for k in record if k.startswith(('pupil_center_', 'eye_rotation_', 'eye_center_'))]
            check(key+'/'+view+': finite geometric labels', finite(labels))
        check(key+': front calibrated lens', next(r for r in metadata if r['view'] == 'front')['camera_lens_mm'] == 40)
    report = {'status': 'PASS' if all(c['passed'] for c in checks) else 'FAIL',
              'passed': sum(c['passed'] for c in checks), 'failed': sum(not c['passed'] for c in checks),
              'checks': checks, 'scope': 'Actual preview files and provenance; visual acceptance remains a separate render review.'}
    (ROOT/'tests/milestone2/render_audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print('RENDER_AUDIT', report['status'], report['passed'], 'passed', report['failed'], 'failed')
    if report['failed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
