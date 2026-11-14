"""Decode the rendered blink preview and compare it with its raw frame manifest."""
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]


def main():
    folder=ROOT/'work/milestone3'
    manifest=json.loads((folder/'blink_preview.json').read_text())
    video=folder/'blink_preview.mp4'
    capture=cv2.VideoCapture(str(video))
    fps=capture.get(cv2.CAP_PROP_FPS)
    decoded=[]
    while True:
        ok,frame=capture.read()
        if not ok:break
        decoded.append(frame)
    capture.release()
    checks=[]
    def check(name,value):checks.append({'test':name,'passed':bool(value)})
    check('36 frames decode at 24 fps',len(decoded)==36 and abs(fps-24)<1e-6)
    check('all decoded frames are 512x512',len(decoded)>0 and all(f.shape[:2]==(512,512) for f in decoded))
    check('video hash matches render manifest',hashlib.sha256(video.read_bytes()).hexdigest()==manifest['video_sha256'])
    check('video belongs to current saved scene',hashlib.sha256((folder/'IRISX_BLINK_PROTOTYPE.blend').read_bytes()).hexdigest()==manifest['scene_sha256'])
    errors=[]
    raw_valid=[]
    for record,decoded_frame in zip(manifest['frames'],decoded):
        path=folder/record['image']
        raw_valid.append(hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256'])
        raw=cv2.imread(str(path))
        errors.append(float(np.abs(decoded_frame.astype(float)-raw.astype(float)).mean()))
    check('every raw frame matches its manifest hash',len(raw_valid)==36 and all(raw_valid))
    check('decoded order agrees with raw sequence within compression tolerance',len(errors)==36 and max(errors)<6)
    changes=[float(np.abs(a.astype(float)-b.astype(float)).mean()) for a,b in zip(decoded,decoded[1:])]
    check('actual rendered pixels change during blink',bool(changes) and max(changes)>2)
    check('manifest includes closed pose and returns open',manifest['frames'][20]['opening_L']==manifest['frames'][20]['opening_R']==0 and manifest['frames'][-1]['opening_L']==manifest['frames'][-1]['opening_R']==1)
    out=ROOT/'tests/milestone3'
    sheet=Image.new('RGB',(1536,548),(20,23,29))
    draw=ImageDraw.Draw(sheet)
    for column,index in enumerate([17,19,20]):
        sheet.paste(Image.fromarray(cv2.cvtColor(decoded[index],cv2.COLOR_BGR2RGB)),(column*512,36))
        draw.text((column*512+12,10),f"Frame {index+1} | opening {manifest['frames'][index]['opening_L']:.3f}",fill='white')
    sheet.save(out/'blink_decoded_strip.png')
    report={'status':'PASS' if all(c['passed'] for c in checks) else 'FAIL','checks':checks,
            'decoded_frames':len(decoded),'fps':fps,'duration_s':len(decoded)/fps if fps else None,
            'max_compression_mean_absolute_error_8bit':max(errors) if errors else None,
            'max_adjacent_frame_mean_change_8bit':max(changes) if changes else None,
            'render_runtime_s':manifest['runtime_s'],'scope':'Decode, source/order correspondence and changing rendered pixels; not a photorealism or final expression-mode evaluation.'}
    (out/'blink_video_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('BLINK_VIDEO_AUDIT',json.dumps(report),flush=True)
    if report['status']!='PASS':raise RuntimeError('Blink video check failed')


if __name__=='__main__':main()
