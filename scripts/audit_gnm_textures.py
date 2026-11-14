"""Audit generated native-UV maps and measure color continuity at UV seams."""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates

ROOT = Path(__file__).resolve().parents[1]


def seam_samples():
    with np.load(ROOT/'assets/gnm/gnm_head.npz', allow_pickle=False) as model:
        faces, uv = model['quads'], model['quad_uvs']
        skin = model['vertex_groups'][model['vertex_group_names'].tolist().index('skin')]
        selected = np.flatnonzero((skin[faces] > .5).all(1))
        mid = model['template_joint_positions'][2:4].mean(0)
        rotation = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]])
        vertices = (model['template_vertex_positions']-mid) @ rotation.T
    edges = {}
    samples = []
    for face in selected:
        for corner in range(4):
            a, b = int(faces[face, corner]), int(faces[face, (corner+1)%4])
            coords = uv[face, [corner, (corner+1)%4]]
            if a > b:
                a, b = b, a
                coords = coords[::-1]
            key = a, b
            if key in edges:
                other, other_uv = edges[key]
                if np.max(np.abs(coords-other_uv)) > 1e-5:
                    for t in (.2, .5, .8):
                        world = vertices[a]*(1-t)+vertices[b]*t
                        samples.append((coords[0]*(1-t)+coords[1]*t,
                                        other_uv[0]*(1-t)+other_uv[1]*t,
                                        uv[face].mean(0), uv[other].mean(0),
                                        abs(world[0]) < .085 and world[1] < .045 and world[2] > -.14))
            else:
                edges[key] = face, coords
    return samples


def main():
    checks, looks = [], []
    samples = seam_samples()

    def check(name, passed, details=None):
        checks.append({'test': name, 'passed': bool(passed), 'details': details})

    detail_folder = ROOT/'assets/skin_detail'
    detail = json.loads((detail_folder/'manifest.json').read_text())
    check('Scan detail: attribution license recorded', detail['license'] == 'CC-BY-3.0' and 'Perry-Smith' in detail['author'])
    for info in detail['files']:
        check('Scan detail: source checksum '+info['file'],
              hashlib.sha256((detail_folder/info['file']).read_bytes()).hexdigest() == info['sha256'])
    iris_folder = ROOT/'assets/iris'
    iris = json.loads((iris_folder/'manifest.json').read_text())
    check('Iris source: checksum', hashlib.sha256((iris_folder/iris['file']).read_bytes()).hexdigest() == iris['sha256'])
    check('Iris source: generated appearance origin disclosed', 'AI-authored' in iris['source'] and 'ground truth' in iris['role'])
    check('Iris source: valid annulus registration', 0 < iris['pupil_radius_px'] < iris['iris_radius_px'] < min(iris['dimensions'])/2)

    for folder in sorted((ROOT/'textures').glob('look_*')):
        manifest = json.loads((folder/'manifest.json').read_text())
        key = folder.name
        check(key+': source image hash', hashlib.sha256((ROOT/manifest['source_image']).read_bytes()).hexdigest() == manifest['source_sha256'])
        check(key+': source license', manifest['source_license'] == 'CC0-1.0')
        check(key+': scan source attribution retained', manifest.get('skin_detail_source', {}).get('license') == 'CC-BY-3.0')
        check(key+': iris source provenance retained', manifest.get('iris_source', {}).get('sha256') == iris['sha256'])
        for name, info in manifest['files'].items():
            path = folder/name
            check(key+': checksum '+name, hashlib.sha256(path.read_bytes()).hexdigest() == info['sha256'])
            with Image.open(path) as image:
                expected = (4096, 4096) if name.startswith('skin_') else (2048, 2048)
                check(key+': resolution '+name, image.size == expected, list(image.size))
            if name.endswith('_height.png'):
                with path.open('rb') as image:
                    header = image.read(26)
                check(key+': 16-bit height '+name, header[24] == 16)
        check(key+': distinct L/R iris color maps', manifest['files']['eye_L_basecolor.png']['sha256'] != manifest['files']['eye_R_basecolor.png']['sha256'])
        check(key+': distinct L/R iris height maps', manifest['files']['eye_L_height.png']['sha256'] != manifest['files']['eye_R_height.png']['sha256'])
        with Image.open(folder/'skin_basecolor.png') as image:
            rgb = np.array(image.convert('RGB'), dtype=np.float32)/255
        differences, visible = [], []
        for uv_a, uv_b, center_a, center_b, front in samples:
            points = []
            for uv, center in [(uv_a, center_a), (uv_b, center_b)]:
                direction = center-uv
                uv = uv+direction/max(np.linalg.norm(direction), 1e-12)*(.6/4096)
                points.append([(1-uv[1])*4096-.5, uv[0]*4096-.5])
            values = np.array([map_coordinates(rgb[:, :, c], np.array(points).T, order=1, mode='nearest') for c in range(3)]).T
            diff = float(np.sqrt(np.square(values[0]-values[1]).mean()))
            differences.append(diff)
            if front:
                visible.append(diff)
        stats = {'samples': len(differences), 'all_p95_rgb_rms': float(np.quantile(differences, .95)),
                 'all_max_rgb_rms': max(differences), 'front_samples': len(visible),
                 'front_p95_rgb_rms': float(np.quantile(visible, .95)) if visible else 0,
                 'front_max_rgb_rms': max(visible) if visible else 0,
                 'note': 'Measured normalized RGB difference across native UV cut edges; supplemental evidence, not a photorealism score. Includes interior/oral joins.'}
        looks.append({'id': key, 'skin_sha256': manifest['files']['skin_basecolor.png']['sha256'], 'seams': stats})
    check('Five texture looks exported', len(looks) == 5)
    check('Five distinct skin maps', len({a['skin_sha256'] for a in looks}) == 5)
    report = {'status': 'PASS' if all(c['passed'] for c in checks) else 'FAIL',
              'passed': sum(c['passed'] for c in checks), 'failed': sum(not c['passed'] for c in checks),
              'checks': checks, 'looks': looks,
              'visual_status': 'Render review required. Engineering pass does not establish photographic realism or absence of visible seams.'}
    path = ROOT/'tests/milestone2/texture_audit.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2)+'\n')
    print('TEXTURE_AUDIT', report['status'], report['passed'], 'passed', report['failed'], 'failed')
    print(json.dumps(looks, indent=2))
    if report['failed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
