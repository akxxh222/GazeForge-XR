"""Decode the eye review and make evidence linked to actual rendered sources."""
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from validate_expression_capture import optical_axis

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    folder = ROOT/'work/review/eye_refinement'
    output = ROOT/'tests/eye_refinement'
    output.mkdir(parents=True, exist_ok=True)
    receipt = json.loads((folder/'render_receipt.json').read_text(encoding='utf-8'))
    motion = json.loads((folder/'motion.json').read_text(encoding='utf-8'))
    checks = []
    def check(name, value):
        checks.append({'test': name, 'passed': bool(value)})
    check('motion receipt complete with 96 actual frames', motion['status']=='COMPLETE' and len(motion['frames'])==96)
    check('current scene matches both receipts', motion['scene_sha256']==receipt['scene_sha256']==sha(folder/'IRISX_EYE_REFINEMENT.blend'))
    video = folder/'eye_refinement_review.mp4'
    check('MP4 checksum', sha(video)==motion['video_sha256'])
    capture = cv2.VideoCapture(str(video))
    check('24fps and 512-square video', capture.get(cv2.CAP_PROP_FPS)==24 and
          capture.get(cv2.CAP_PROP_FRAME_WIDTH)==capture.get(cv2.CAP_PROP_FRAME_HEIGHT)==512)
    page = Image.new('RGB', (1536, 1152), '#171a20')
    draw = ImageDraw.Draw(page)
    errors, changes, previous = [], [], None
    for index, record in enumerate(motion['frames']):
        pose = record['state']
        first = motion['frames'][0]['state']
        check(f'frame {index+1} both physical eye centers fixed', all(
            np.linalg.norm(np.asarray(pose['eye_center_3D_'+s])-first['eye_center_3D_'+s]) < 1e-7 for s in ('L','R')))
        aim_errors = []
        for side in ('L','R'):
            desired = np.asarray(pose['fixation_world_m'])-pose['eye_center_3D_'+side]
            desired /= np.linalg.norm(desired)
            aim_errors.append(np.linalg.norm(optical_axis(pose['eye_quaternion_wxyz_'+side])-desired))
        check(f'frame {index+1} binocular axes aim at shared target', max(aim_errors)<1e-5)
        check(f'frame {index+1} normalized bounds and 35cm target plane', all(abs(pose['input'][a])<=1.000001 for a in ('h','v'))
              and abs(pose['fixation_world_m'][1]+.35)<1e-6)
        ok, decoded = capture.read()
        check(f'frame {index+1} decoded', ok)
        path = folder/record['file']
        check(f'frame {index+1} source checksum', sha(path)==record['sha256'])
        if not ok:
            break
        raw = cv2.imread(str(path))
        errors.append(float(np.abs(raw.astype(float)-decoded.astype(float)).mean()))
        if previous is not None:
            changes.append(float(np.abs(decoded.astype(float)-previous.astype(float)).mean()))
        previous = decoded
        # All 96 frames are displayed in chronological order, not keyframes only.
        thumb = Image.fromarray(cv2.cvtColor(decoded, cv2.COLOR_BGR2RGB)).resize((128,128))
        x,y = index%12*128, index//12*144
        page.paste(thumb, (x,y+16)); draw.text((x+3,y+2), str(index+1), fill='white')
    extra, _ = capture.read(); capture.release()
    check('exactly 96 decoded frames', len(errors)==96 and not extra)
    check('decoded order matches source pixels', len(errors)==96 and max(errors)<6)
    check('visible changing poses', sum(v>.005 for v in changes)>20)
    states = [r['state'] for r in motion['frames']]
    check('both eyelids close and reopen', any(s['opening_L']==s['opening_R']==0 for s in states) and states[-1]['opening_L']==states[-1]['opening_R']==1)
    check('starts and ends at center', all(abs(states[i]['input'][k])<1e-6 for i in (0,-1) for k in ('h','v')))
    page.save(output/'all_frames.png')
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 25)
    comparison = Image.new('RGB',(1600,720),'#171a20')
    draw = ImageDraw.Draw(comparison)
    for row,frame in enumerate((1,43)):
        for col,variant in enumerate(('before','after')):
            image_path = folder/f'{variant}_frame_{frame:03d}.png'
            record = next(r for r in receipt['renders'] if r['file']==image_path.name)
            check(image_path.name+' source checksum', sha(image_path)==record['sha256'])
            with Image.open(image_path) as image:
                crop = image.crop((10,295,1014,680)).resize((800,307),Image.Resampling.LANCZOS)
            comparison.paste(crop,(col*800,row*360+44))
            draw.text((col*800+12,row*360+9), f'{variant.title()} | original scan frame {frame}',font=font,fill='white')
    comparison.save(output/'comparison.png')
    report = {'status':'PASS' if all(c['passed'] for c in checks) else 'FAIL',
              'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),
              'checks':checks,'max_compression_mae_255':max(errors,default=None),
              'scene_sha256':receipt['scene_sha256'],'video_sha256':sha(video),
              'all_frames_sha256':sha(output/'all_frames.png'),'comparison_sha256':sha(output/'comparison.png'),
              'auditor_sha256':sha(Path(__file__)),
              'scope':'Full decode/source order, duration, actual visible motion, recorded pose semantics and before/after evidence. Visual judgment remains separate.'}
    (output/'media.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('EYE_REVIEW_MEDIA',report['status'],report['passed'],report['failed'])
    if report['failed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
