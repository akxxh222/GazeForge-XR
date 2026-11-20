"""Measure both pupils in five new actual direction images and repeated reset."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import cv2
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from validate_expression_capture import apparent_dark_pupil


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--folder',type=Path)
    args=parser.parse_args();root=args.root.resolve();folder=args.folder.resolve() if args.folder else root/'runtime/directions'
    receipt=json.loads((folder/'receipt.json').read_text());checks=[];pixels={}
    def check(name,value):checks.append({'test':name,'passed':bool(value)})
    check('complete six-image diagnostic receipt',receipt['status']=='COMPLETE' and len(receipt['renders'])==6)
    check('exact portable scene',receipt['scene_sha256']==sha(root/'scene.blend'))
    sheet=Image.new('RGB',(1536,550),(20,23,29));draw=ImageDraw.Draw(sheet)
    for index,row in enumerate(receipt['renders']):
        name=row['direction'];path=folder/row['file'];frame=cv2.imread(str(path))
        check(name+' 1024px PNG and checksum',frame is not None and frame.shape==(1024,1024,3) and sha(path)==row['sha256'])
        check(name+' pose stable through render',row['pose']==row['pose_after_render'])
        measured={s:apparent_dark_pupil(frame,row['pose']['pupil_center_2D_'+s]) for s in ('L','R')}
        check(name+' both actual pixel pupils measured',all(measured.values()))
        pixels[name]=measured
        image=Image.open(path).convert('RGB')
        sheet.paste(image.resize((256,256)),(index*256,28))
        sheet.paste(image.crop((310,455,715,580)).resize((256,79)),(index*256,300))
        draw.text((index*256+7,8),name,fill='white')
    directions={}
    for name,axis,sign in [('left',0,-1),('right',0,1),('up',1,-1),('down',1,1)]:
        shifts={s:pixels[name][s]['center_2D'][axis]-pixels['reset'][s]['center_2D'][axis]
                for s in ('L','R') if pixels[name][s] and pixels['reset'][s]}
        check(name+' both measured pupils shift correctly',len(shifts)==2 and all(sign*v>1 for v in shifts.values()))
        directions[name]=shifts
    first=cv2.imread(str(folder/'reset.png'));second=cv2.imread(str(folder/'reset_repeat.png'))
    delta=float(np.mean(np.abs(first.astype(float)-second.astype(float))))
    rows={r['direction']:r for r in receipt['renders']}
    check('repeat reset exact transforms and metadata',rows['reset']['pose']==rows['reset_repeat']['pose'])
    check('repeat reset pixel mean difference under one level',delta<1)
    check('both measured reset centers return',all(pixels['reset'][s] and pixels['reset_repeat'][s]
          and np.linalg.norm(np.array(pixels['reset'][s]['center_2D'])-pixels['reset_repeat'][s]['center_2D'])<.5 for s in ('L','R')))
    sheet=sheet.crop((0,0,1536,410));sheet.save(folder/'contact_sheet.png')
    failed=sum(not c['passed'] for c in checks)
    result={'status':'PASS' if not failed else 'FAIL','passed':len(checks)-failed,'failed':failed,'checks':checks,
            'receipt_sha256':sha(folder/'receipt.json'),'contact_sheet_sha256':sha(folder/'contact_sheet.png'),
            'directions':directions,'pixel_pupils':pixels,'repeated_reset_rgb_mae_8bit':delta,
            'scope':'Five visible directions plus repeated reset at 1024px. Dark-component centroids measured in actual pixels are directional diagnostics, not refracted optical ground truth.'}
    output=root/'runtime/audit';output.mkdir(parents=True,exist_ok=True)
    (output/'directions.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('FIVE_DIRECTION_AUDIT',result['status'],result['passed'],failed)
    if failed:raise SystemExit(1)


if __name__=='__main__':main()
