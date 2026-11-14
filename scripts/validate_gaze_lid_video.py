"""Decode the gaze/lid review clip and audit actual pose/frame evidence."""
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    folder=ROOT/'work/milestone3/gaze_lids'
    receipt=json.loads((folder/'render_receipt.json').read_text())
    video=receipt['video']
    capture=cv2.VideoCapture(str(folder/'gaze_lids_preview.mp4'))
    fps=capture.get(cv2.CAP_PROP_FPS)
    decoded=[]
    while True:
        ok,frame=capture.read()
        if not ok:break
        decoded.append(frame)
    capture.release()
    checks=[]
    def check(name,value):checks.append({'test':name,'passed':bool(value)})
    check('current scene matches render receipt',sha(folder/'IRISX_GAZE_LIDS_RIG.blend')==receipt['scene_sha256'])
    check('video matches receipt hash',sha(folder/'gaze_lids_preview.mp4')==video['sha256'])
    check('all 144 frames decode at 24 fps',len(decoded)==144 and abs(fps-24)<1e-6)
    check('duration is six seconds',fps>0 and abs(len(decoded)/fps-6)<1e-6)
    check('all frames are 384 square',len(decoded)>0 and all(f.shape[:2]==(384,384) for f in decoded))
    for view in receipt['views']:
        check(view['view']+' actual still checksum',sha(folder/(view['view']+'.png'))==view['sha256'])
    errors=[]
    hashes=[]
    for record,frame in zip(video['poses'],decoded):
        path=folder/'frames'/f"frame_{record['frame']:03d}.png"
        hashes.append(sha(path)==record['sha256'])
        errors.append(float(np.abs(frame.astype(float)-cv2.imread(str(path)).astype(float)).mean()))
    check('all raw frames match saved pose hashes',len(hashes)==144 and all(hashes))
    check('decoded frame ordering matches raw renders',len(errors)==144 and max(errors)<6)
    changes=[float(np.abs(a.astype(float)-b.astype(float)).mean()) for a,b in zip(decoded,decoded[1:])]
    check('rendered pixels change continuously through scan',sum(c>.025 for c in changes)>90 and max(changes)>1)
    poses=video['poses']
    check('timeline reaches left/right/up/down',all(any(p['state']['input'][axis]*sign>.99 for p in poses) for axis,sign in [('h',-1),('h',1),('v',-1),('v',1)]))
    check('two full blinks are rendered',all(poses[f-1]['state']['opening_L']==poses[f-1]['state']['opening_R']==0 for f in [60,108]))
    check('neutral open pose returns at end',all(abs(v)<1e-6 for v in poses[-1]['state']['input'].values()) and poses[-1]['state']['opening_L']==poses[-1]['state']['opening_R']==1)
    sheet=Image.new('RGB',(1152,816),(20,23,29))
    draw=ImageDraw.Draw(sheet)
    for index,(frame,label) in enumerate([(18,'Left'),(36,'Right'),(54,'Up / brow'),(60,'Up / closed'),(102,'Down'),(108,'Down / closed')]):
        x,y=(index%3)*384,(index//3)*408
        draw.text((x+10,y+7),f'{label} | frame {frame}',fill='white')
        sheet.paste(Image.fromarray(cv2.cvtColor(decoded[frame-1],cv2.COLOR_BGR2RGB)),(x,y+24))
    output=ROOT/'tests/milestone3/gaze_lids'
    sheet.save(output/'decoded_strip.png')
    report={'status':'PASS' if all(c['passed'] for c in checks) else 'FAIL','passed':sum(c['passed'] for c in checks),
            'failed':sum(not c['passed'] for c in checks),'checks':checks,'decoded_frames':len(decoded),'fps':fps,
            'max_compression_mean_absolute_error_8bit':max(errors),'changed_adjacent_frames':sum(c>.025 for c in changes),
            'max_adjacent_mean_change_8bit':max(changes),'render_runtime_s':receipt['runtime_s'],
            'scope':'Actual continuous 3D review clip, still checksums, decoded order and changing gaze/blink poses. Low-resolution diagnostic, not a final expression-mode video or realism approval.'}
    (output/'video_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('GAZE_LID_VIDEO',json.dumps(report),flush=True)
    if report['failed']:raise RuntimeError('Gaze/lid video checks failed')


if __name__=='__main__':main()
