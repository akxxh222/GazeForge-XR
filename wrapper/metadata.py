"""Export exact requested controls alongside Blender's evaluated observations."""
import hashlib
import json
import math
from pathlib import Path


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path, value):
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    temporary.replace(path)


def export_clockwise_metadata(receipt_path):
    """Finalize a completed capture without changing rendered observations.

    input is the requested normalized control. evaluated_input is recovered
    from Blender's float32 target and can exceed +/-1 by rounding epsilon.
    Pupil positions, eye rotations and camera projections remain observations.
    Pure Python: callable inside Blender or from normal CPython.
    """
    path = Path(receipt_path).resolve()
    receipt = json.loads(path.read_text(encoding='utf-8'))
    if receipt['status'] != 'COMPLETE' or receipt['config']['schema'] != 'IrisX clockwise capture 1':
        raise ValueError('A completed clockwise capture is required')
    if [r['frame'] for r in receipt['frames']] != list(range(10)):
        raise ValueError('Expected ten ordered clockwise observations')
    frames = []
    for k, record in enumerate(receipt['frames']):
        theta = 2*math.pi*k/10
        requested = {'h': math.sin(theta), 'v': math.cos(theta)}
        evaluated = record['pose']['input']
        if abs(record['theta']-theta) > 1e-12 or any(abs(evaluated[a]-requested[a]) > 2e-6 for a in ('h', 'v')):
            raise ValueError('Observed target disagrees with clockwise input')
        if _sha(path.parent/record['file']) != record['sha256']:
            raise ValueError('Source PNG checksum mismatch: '+record['file'])
        frames.append({**record['pose'], 'frame': k, 'theta': theta,
                       'input': requested, 'evaluated_input': dict(evaluated),
                       'image': record['file'], 'image_sha256': record['sha256']})
    exporter_sha = _sha(Path(__file__))
    metadata = {'schema': 'IrisX geometric pupil metadata 1',
                'calibration': receipt['config']['contract'],
                'scene_sha256': receipt['config']['scene_sha256'],
                'input_convention': 'input: requested h=sin(theta), v=cos(theta) in [-1,1]; evaluated_input: Blender float32 target divided by 0.05 m',
                'metadata_exporter_sha256': exporter_sha, 'frames': frames}
    output = path.parent/'metadata.json'
    _write(output, metadata)
    receipt['metadata_sha256'] = _sha(output)
    receipt['metadata_exporter_sha256'] = exporter_sha
    _write(path, receipt)
    return output
