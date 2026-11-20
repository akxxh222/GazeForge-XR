"""Decode rendered modes and verify geometric labels against actual files.

Run with normal Python (numpy, OpenCV and Pillow), after render_expressions.py.
--partial is a progress review; missing deliverables never produce PASS.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
MODES = ('left', 'right', 'generate_motion')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def finite(value):
    if isinstance(value, dict):
        return all(finite(v) for v in value.values())
    if isinstance(value, list):
        return all(finite(v) for v in value)
    return not isinstance(value, (int, float)) or math.isfinite(value)


def projected(matrix, point):
    homogeneous = np.asarray(matrix) @ np.r_[point, 1.]
    return homogeneous[:2] / homogeneous[2]


def optical_axis(quaternion):
    w, x, y, z = quaternion
    return np.array([2 * (x*y-w*z), 1-2*(x*x+z*z), 2*(y*z+w*x)])


def quaternion_rotate(quaternion, vector):
    q = np.asarray(quaternion)
    v = np.asarray(vector)
    return v + 2*np.cross(q[1:], np.cross(q[1:], v)+q[0]*v)


def pupil_in_eye_frame(pose, side):
    q = np.asarray(pose['eye_quaternion_wxyz_'+side]).copy()
    q[1:] *= -1
    delta = np.asarray(pose['pupil_center_3D_'+side])-pose['eye_center_3D_'+side]
    return quaternion_rotate(q, delta)


def xyz_rotation_matrix(angles):
    x, y, z = angles
    cx, cy, cz = math.cos(x), math.cos(y), math.cos(z)
    sx, sy, sz = math.sin(x), math.sin(y), math.sin(z)
    return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array(
        [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])


def apparent_dark_pupil(frame, seed):
    """A bounded image measurement for this capture's dark opaque pupils.

    The geometric projection seeds a small search window only. The returned
    location is measured from actual pixels, not copied from the projection.
    Corneal highlights/occlusion can bias this dark-component centroid, so it
    is a directional diagnostic rather than optical ground truth.
    """
    scale = frame.shape[1] / 720
    radius = round(16 * scale)
    x, y = np.round(seed).astype(int)
    x0, y0 = max(0, x-radius), max(0, y-radius)
    roi = frame[y0:y+radius+1, x0:x+radius+1]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    count, _, stats, centroids = cv2.connectedComponentsWithStats((gray < 15).astype(np.uint8))
    candidates = []
    for index in range(1, count):
        left, top, width, height, area = stats[index]
        center = centroids[index] + [x0, y0]
        distance = np.linalg.norm(center-seed)
        if (12*scale*scale <= area <= 180*scale*scale and .5 <= width/height <= 2
                and distance <= 10*scale and left > 0 and top > 0
                and left+width < roi.shape[1] and top+height < roi.shape[0]):
            candidates.append((area/(1+distance/scale), center, area))
    if not candidates:
        return None
    _, center, area = max(candidates, key=lambda row: row[0])
    return {'center_2D': center.tolist(), 'dark_area_px': int(area)}


def eye_crop(frame, pose, size=256):
    h, w = frame.shape[:2]
    pixels = np.asarray([pose['pupil_center_2D_' + s] for s in ('L', 'R')])
    center = pixels.mean(axis=0)
    radius_x, radius_y = w * .23, h * .105
    left, top = max(0, int(center[0]-radius_x)), max(0, int(center[1]-radius_y))
    right, bottom = min(w, int(center[0]+radius_x)), min(h, int(center[1]+radius_y))
    crop = Image.fromarray(cv2.cvtColor(frame[top:bottom, left:right], cv2.COLOR_BGR2RGB))
    scale = min(size/crop.width, (size//2)/crop.height)
    crop = crop.resize((round(crop.width*scale), round(crop.height*scale)), Image.Resampling.LANCZOS)
    canvas = Image.new('RGB', (size, size//2), (20, 23, 29))
    canvas.paste(crop, ((size-crop.width)//2, (size//2-crop.height)//2))
    return canvas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT/'runtime/capture')
    parser.add_argument('--output', type=Path, default=ROOT/'runtime/audit')
    parser.add_argument('--partial', action='store_true')
    args = parser.parse_args()
    folder, output = args.input.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    checks, missing, modes = [], [], {}

    def check(name, value):
        checks.append({'test': name, 'passed': bool(value)})
        if not value:
            print('FAILED', name, flush=True)

    def geometry(label, pose, contract, centers, local_pupils):
        check(label + ': finite pose', finite(pose))
        h, v = pose['input']['h'], pose['input']['v']
        check(label + ': target plane and bounds', abs(h) <= 1.000001 and abs(v) <= 1.000001
              and np.allclose(pose['fixation_world_m'], [.05*h, -.35, .05*v], atol=1e-7))
        for side in ('L', 'R'):
            center = np.asarray(pose['eye_center_3D_' + side])
            q = np.asarray(pose['eye_quaternion_wxyz_' + side])
            axis = optical_axis(q)
            desired = np.asarray(pose['fixation_world_m']) - center
            desired /= np.linalg.norm(desired)
            check(label + ': fixed center and physical aim ' + side,
                  np.allclose(center, centers[side], atol=1e-7) and abs(np.linalg.norm(q)-1) < 1e-6
                  and np.linalg.norm(axis-desired) < 1e-5)
            q_matrix = np.column_stack([quaternion_rotate(q, basis) for basis in np.eye(3)])
            check(label + ': world XYZ Euler and quaternion agree ' + side,
                  np.max(np.abs(q_matrix-xyz_rotation_matrix(pose['eye_rotation_'+side]))) < 1e-6)
            local_point = pupil_in_eye_frame(pose, side)
            check(label + ': pupil centroid follows rigid eye rotation ' + side,
                  .005 < np.linalg.norm(local_point) < .020
                  and np.allclose(local_point, local_pupils[side], atol=1e-7, rtol=0))
            expected = projected(pose['camera_matrix'], pose['pupil_center_3D_' + side])
            point = np.asarray(pose['pupil_center_2D_' + side])
            resolution = contract['render']['resolution']
            check(label + ': geometric projection ' + side,
                  np.linalg.norm(point-expected) < .001 and 0 <= point[0] < resolution[0] and 0 <= point[1] < resolution[1])

    def provenance(name, receipt):
        config = receipt['config']
        path = Path(config['scene_path'])
        check(name + ': exact scene checksum', path.is_file() and sha(path) == config['scene_sha256'])
        for file, expected in config['code_sha256'].items():
            check(name + ': source checksum ' + file, sha(ROOT/'wrapper'/file) == expected)
        contract = config['contract']
        check(name + ': calibrated 40 cm camera and target bounds',
              abs(contract['camera']['distance_from_eye_midpoint_m']-.4) < 1e-6
              and abs(contract['target_plane_distance_m']-.35) < 1e-9 and contract['target_bounds_m'] == .05)
        check(name + ': physical Cycles capture, deterministic seed and no motion blur',
              contract['render']['engine'] == 'CYCLES' and not contract['render']['animated_seed']
              and not contract['render']['motion_blur'])
        return contract

    for mode in MODES:
        receipt_path = folder/mode/'capture.json'
        if not receipt_path.is_file():
            missing.append(mode)
            continue
        receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
        if receipt['status'] != 'COMPLETE':
            missing.append(mode)
            continue
        contract = provenance(mode, receipt)
        config, records, video = receipt['config'], receipt['frames'], receipt['video']
        count, fps, resolution = config['frame_count'], config['fps'], config['resolution']
        check(mode + ': complete ordered frame manifest', len(records) == count and [r['frame'] for r in records] == list(range(1, count+1)))
        check(mode + ': duration positive and at most fifteen seconds', 0 < count/fps <= 15 and abs(video['duration_s']-count/fps) < 1e-9)
        check(mode + ': timestamps and endpoint-preserving 3D retiming', all(
            abs(r['time_s']-i/fps) < 1e-9 and abs(r['source_frame']-(1+143*i/(count-1))) < 1e-8 for i, r in enumerate(records)))
        path = folder/mode/video['file']
        check(mode + ': video checksum', path.is_file() and sha(path) == video['sha256'])
        capture = cv2.VideoCapture(str(path))
        check(mode + ': decoded fps', abs(capture.get(cv2.CAP_PROP_FPS)-fps) < 1e-6)
        centers = {s: records[0]['pose']['eye_center_3D_' + s] for s in ('L', 'R')}
        local_pupils = {s: pupil_in_eye_frame(records[0]['pose'], s) for s in ('L', 'R')}
        errors, changes, raw_changes, holds, chosen = [], [], [], [], {}
        pixel_pupils = {}
        previous, previous_raw, previous_pose = None, None, None
        selected = [1, 36, 69, 75, 108, 144] if mode != 'generate_motion' else [18, 36, 54, 60, 102, 108]
        decoded_count = 0
        for index, record in enumerate(records):
            label = f'{mode} frame {index+1}'
            geometry(label, record['pose'], contract, centers, local_pupils)
            raw_path = folder/mode/record['file']
            check(label + ': actual rendered PNG checksum and positive runtime',
                  raw_path.is_file() and sha(raw_path) == record['sha256'] and record['render_seconds'] > 0)
            raw = cv2.imread(str(raw_path))
            ok, frame = capture.read()
            if not ok:
                break
            decoded_count += 1
            check(label + ': raw and decoded dimensions', frame.shape[:2] == raw.shape[:2] == (resolution, resolution))
            errors.append(float(np.abs(frame.astype(np.float32)-raw.astype(np.float32)).mean()))
            if record['pose']['opening_L'] > .99 and record['pose']['opening_R'] > .99:
                measured = {s: apparent_dark_pupil(raw, record['pose']['pupil_center_2D_'+s]) for s in ('L', 'R')}
                if all(measured.values()):
                    pixel_pupils[index+1] = measured
            if previous is not None:
                changes.append(float(np.abs(frame.astype(np.float32)-previous.astype(np.float32)).mean()))
                raw_changes.append(float(np.abs(raw.astype(np.float32)-previous_raw.astype(np.float32)).mean()))
                if record['pose'] == previous_pose:
                    holds.append(raw_changes[-1])
            if index+1 in selected:
                chosen[index+1] = frame.copy()
            previous, previous_raw, previous_pose = frame, raw, record['pose']
        extra, _ = capture.read()
        capture.release()
        check(mode + ': all frames decode with no extra frames', decoded_count == count and not extra)
        check(mode + ': decoded frame order agrees with actual rendered sources', len(errors) == count and max(errors, default=100) < 6)
        check(mode + ': visible motion throughout expression transitions', sum(c > .005 for c in changes) > count*.15 and max(changes, default=0) > .03)
        check(mode + ': no large full-frame temporal jump', max(changes, default=100) < 8)
        check(mode + ': stable held poses without seed flicker', not holds or max(holds) < .1)
        poses = [r['pose'] for r in records]
        check(mode + ': starts and ends neutral/open', all(
            abs(p[a]['h']) < 1e-6 and abs(p[a]['v']) < 1e-6 and p['opening_L'] == p['opening_R'] == 1
            for p in (poses[0], poses[-1]) for a in ('input',)))
        check(mode + ': bilateral blink present', any(p['opening_L'] < .01 and p['opening_R'] < .01 for p in poses))
        if mode in ('left', 'right'):
            sign = -1 if mode == 'left' else 1
            check(mode + ': correct viewer-space direction', max(sign*p['input']['h'] for p in poses) > .99
                  and min(sign*p['input']['h'] for p in poses) > -1e-6)
            check(mode + ': geometric pupil projections move in intended direction', all(
                max(sign*(p['pupil_center_2D_'+s][0]-poses[0]['pupil_center_2D_'+s][0]) for p in poses) > 1 for s in ('L', 'R')))
        else:
            check(mode + ': four-direction scan', all(max(p['input'][a]*sign for p in poses) > .99
                  for a, sign in [('h', -1), ('h', 1), ('v', -1), ('v', 1)]))
        pixel_directions = []
        requested = [('h', -1)] if mode == 'left' else ([('h', 1)] if mode == 'right' else [('h', -1), ('h', 1), ('v', 1), ('v', -1)])
        for axis, sign in requested:
            candidates = [n for n in pixel_pupils if poses[n-1]['input'][axis]*sign > .99]
            number = candidates[0] if candidates else None
            shifts = {}
            for side in ('L', 'R'):
                if 1 in pixel_pupils and number is not None:
                    component = 0 if axis == 'h' else 1
                    shifts[side] = pixel_pupils[number][side]['center_2D'][component]-pixel_pupils[1][side]['center_2D'][component]
            image_sign = sign if axis == 'h' else -sign
            check(f'{mode}: pixel-measured pupil direction {axis} {sign:+d}',
                  len(shifts) == 2 and all(image_sign*value > resolution/720 for value in shifts.values()))
            pixel_directions.append({'axis': axis, 'sign': sign, 'frame': number, 'image_pixel_shift': shifts})
        check(mode + ': pixel-measured neutral return', 1 in pixel_pupils and count in pixel_pupils
              and all(np.linalg.norm(np.asarray(pixel_pupils[count][s]['center_2D'])-pixel_pupils[1][s]['center_2D']) < .5 for s in ('L', 'R')))
        sheet = Image.new('RGB', (768, 510), (20, 23, 29))
        draw = ImageDraw.Draw(sheet)
        for i, number in enumerate(selected):
            if number not in chosen:
                continue
            x, y = (i % 3)*256, (i//3)*255
            draw.text((x+8, y+6), f'{mode} | frame {number}', fill='white')
            # Show an honest eye enlargement and the corresponding full view.
            sheet.paste(eye_crop(chosen[number], records[number-1]['pose']), (x, y+24))
            full = Image.fromarray(cv2.cvtColor(chosen[number], cv2.COLOR_BGR2RGB)).resize((96, 96), Image.Resampling.LANCZOS)
            sheet.paste(full, (x+80, y+154))
        sheet.save(output/(mode+'_decoded.png'))
        modes[mode] = {'video_sha256': video['sha256'], 'receipt_sha256': sha(receipt_path),
                       'decoded_frames': decoded_count, 'fps': fps, 'duration_s': decoded_count/fps,
                       'resolution': resolution, 'max_compression_mae_8bit': max(errors, default=None),
                       'changing_adjacent_frames': sum(c > .005 for c in changes),
                       'maximum_temporal_mae_8bit': max(changes, default=None),
                       'identical_pose_pairs': len(holds), 'max_identical_pose_change_8bit': max(holds, default=0),
                       'pixel_measured_directions': pixel_directions,
                       'pixel_measurement_scope': 'Dark-component centroid in raw PNGs, projection-seeded window; directional evidence, not apparent-centroid ground truth',
                       'render_runtime_s': receipt['render_runtime_s']}

    receipt_path = folder/'clockwise/capture.json'
    clockwise = None
    if receipt_path.is_file() and json.loads(receipt_path.read_text(encoding='utf-8'))['status'] == 'COMPLETE':
        receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
        contract = provenance('clockwise', receipt)
        metadata_path = folder/'clockwise/metadata.json'
        metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
        records = metadata['frames']
        check('clockwise: metadata checksum and exact scene', sha(metadata_path) == receipt['metadata_sha256']
              and metadata['scene_sha256'] == receipt['config']['scene_sha256'])
        check('clockwise: exact-input exporter provenance', metadata.get('metadata_exporter_sha256')
              == receipt.get('metadata_exporter_sha256') == sha(ROOT/'wrapper/metadata.py'))
        check('clockwise: ten exact required filenames', [r['image'] for r in records] == [f'renders/frame_{k:02d}.png' for k in range(10)])
        check('clockwise: exactly ten PNGs in official renders directory', len(list((folder/'clockwise/renders').glob('*.png'))) == 10)
        centers = {s: records[0]['eye_center_3D_'+s] for s in ('L', 'R')}
        local_pupils = {s: pupil_in_eye_frame(records[0], s) for s in ('L', 'R')}
        sheet = Image.new('RGB', (1280, 330), (20, 23, 29))
        draw = ImageDraw.Draw(sheet)
        image_pupils = []
        for k, record in enumerate(records):
            theta = 2*math.pi*k/10
            geometry(f'clockwise sample {k}', record, contract, centers, local_pupils)
            check(f'clockwise sample {k}: exact angular order', record['frame'] == k and abs(record['theta']-theta) < 1e-12
                  and abs(record['input']['h']-math.sin(theta)) < 2e-6 and abs(record['input']['v']-math.cos(theta)) < 2e-6)
            check(f'clockwise sample {k}: exact requested normalized controls and separate evaluated observations',
                  all(abs(record['input'][a]-value) < 1e-15 for a, value in
                      [('h', math.sin(theta)), ('v', math.cos(theta))])
                  and all(-1 <= value <= 1 for value in record['input'].values())
                  and record.get('evaluated_input') == receipt['frames'][k]['pose']['input'])
            check(f'clockwise sample {k}: open lids, neutral brows and fixed pupils', record['opening_L'] == record['opening_R'] == 1
                  and all(abs(v-.7) < 1e-6 for v in record['pupil_constriction'].values())
                  and all(v == 0 for v in record['brow_raise'].values()))
            path = folder/'clockwise'/record['image']
            image = cv2.imread(str(path))
            check(f'clockwise sample {k}: actual 1024 PNG checksum', image.shape[:2] == (1024, 1024) and sha(path) == record['image_sha256'])
            measured = {s: apparent_dark_pupil(image, record['pupil_center_2D_'+s]) for s in ('L', 'R')}
            check(f'clockwise sample {k}: both dark pupils measured in actual pixels', all(measured.values()))
            image_pupils.append(measured)
            x, y = (k % 5)*256, (k//5)*165
            draw.text((x+8, y+6), f'{k:02d} | h={math.sin(theta):+.2f} v={math.cos(theta):+.2f}', fill='white')
            sheet.paste(eye_crop(image, record), (x, y+28))
        sheet.save(output/'clockwise_eyes.png')
        check('clockwise: top-first geometric vertical and horizontal direction', all(
            records[0]['pupil_center_2D_'+s][1] < records[5]['pupil_center_2D_'+s][1]
            and records[2]['pupil_center_2D_'+s][0] > records[7]['pupil_center_2D_'+s][0] for s in ('L', 'R')))
        check('clockwise: pixel-measured top/bottom and right/left direction',
              all(all(row.values()) for row in image_pupils) and all(
                  image_pupils[0][s]['center_2D'][1] < image_pupils[5][s]['center_2D'][1]-1
                  and image_pupils[2][s]['center_2D'][0] > image_pupils[7][s]['center_2D'][0]+1 for s in ('L', 'R')))
        clockwise = {'receipt_sha256': sha(receipt_path), 'metadata_sha256': sha(metadata_path),
                     'frames': len(records), 'render_runtime_s': receipt['render_runtime_s'], 'pixel_pupils': image_pupils}
    else:
        missing.append('clockwise')
    if not args.partial:
        check('all three videos and official clockwise capture complete', not missing)
    failed = sum(not c['passed'] for c in checks)
    report = {'status': 'FAIL' if failed else ('PARTIAL' if missing else 'PASS'),
              'passed': sum(c['passed'] for c in checks), 'failed': failed, 'checks': checks,
              'missing': missing, 'modes': modes, 'clockwise': clockwise,
              'validator_sha256': sha(Path(__file__)),
              'scope': 'Actual decoded video/source order, calibrated geometric labels and temporal image metrics. Pinhole labels are not apparent refracted centroids; visual review is separate. Appearance limits are documented separately.'}
    (output/('progress.json' if args.partial else 'report.json')).write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print('IRISX_CAPTURE_AUDIT', report['status'], report['passed'], failed, 'missing', missing)
    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
