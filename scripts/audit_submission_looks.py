"""Verify actual five-look exports, images and source-bound render receipts."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=ROOT)
    args=parser.parse_args();root=args.root.resolve();checks=[]
    def check(name,value):checks.append({'test':name,'passed':bool(value)})
    folder=root/'previews'
    receipt=json.loads((folder/'receipt.json').read_text())
    check('exact scene source',receipt['scene_sha256']==sha(root/'scene.blend'))
    check('all five looks complete',receipt['status']=='COMPLETE' and [r['id'] for r in receipt['looks']]==[f'look_{i:02d}' for i in range(1,6)])
    check('native geometry preserved on every fresh application',all(c['passed'] for c in receipt['checks']))
    check('exact render source',receipt['renderer_sha256']==sha(root/'scripts/render_submission_looks.py'))
    sheet=Image.new('RGB',(1280,1040),(20,23,29));draw=ImageDraw.Draw(sheet)
    colors=[];irises=[];fronts=[]
    for index,look in enumerate(receipt['looks']):
        name=look['id'];source=root/'textures'/name
        manifest=json.loads((source/'manifest.json').read_text())
        check(name+' application manifest hash',look['appearance']['manifest_sha256']==sha(source/'manifest.json'))
        check(name+' application code hash',look['appearance']['application_module_sha256']==sha(root/'wrapper/submission_looks.py'))
        for filename,record in manifest['files'].items():
            path=source/filename
            check(name+' texture hash '+filename,sha(path)==record['sha256'] and path.stat().st_size==record['bytes'])
            with Image.open(path) as image:
                expected=(2048,2048) if filename.startswith('eye_') else (4096,4096)
                check(name+' native export size '+filename,image.size==expected)
        colors.append(manifest['files']['skin_basecolor.png']['sha256'])
        irises.append(manifest['files']['eye_L_iris_basecolor.png']['sha256'])
        check(name+' two expected cameras',[r['camera'] for r in look['renders']]==['RenderCamera','Review_macro'])
        for row in look['renders']:
            path=folder/row['file'];image=Image.open(path)
            check(name+' real PNG '+row['camera'],image.format=='PNG' and image.mode=='RGB' and image.size==(1024,1024) and sha(path)==row['sha256'])
        front=Image.open(folder/look['renders'][0]['file']).convert('RGB')
        macro=Image.open(folder/look['renders'][1]['file']).convert('RGB')
        # Compare the visible face, excluding the constant background. Two
        # pale looks differ primarily in freckles; a whole-frame mean dilutes
        # that real change. This remains a distinctness test, not realism.
        fronts.append(np.asarray(front.crop((350,350,675,800)),np.float32))
        x=index*256
        draw.text((x+8,8),name,fill='white')
        sheet.paste(front.resize((256,256),Image.Resampling.LANCZOS),(x,28))
        sheet.paste(macro.resize((256,256),Image.Resampling.LANCZOS),(x,294))
        # Eye detail crop only enlarges actual pixels; no detail synthesis.
        sheet.paste(macro.crop((200,315,824,627)).resize((256,128),Image.Resampling.LANCZOS),(x,560))
        draw.text((x+8,705),'1024px Cycles / 128 samples',fill='white')
        draw.text((x+8,730),'Native GNM UVs retained',fill='white')
    check('five distinct face maps',len(set(colors))==5)
    check('five distinct iris color maps',len(set(irises))==5)
    pairs=[{'pair':[i+1,j+1],'face_rgb_mae_8bit':float(np.mean(np.abs(fronts[i]-fronts[j])))}
           for i,j in itertools.combinations(range(5),2)]
    check('all look face regions differ in actual pixels',all(row['face_rgb_mae_8bit']>.5 for row in pairs))
    sheet=sheet.crop((0,0,1280,780));comparison=root/'runtime/audit/look_contact.png';comparison.parent.mkdir(parents=True,exist_ok=True);sheet.save(comparison)
    failed=sum(not c['passed'] for c in checks)
    report={'status':'PASS' if not failed else 'FAIL','passed':len(checks)-failed,'failed':failed,
            'checks':checks,'scene_sha256':sha(root/'scene.blend'),'receipt_sha256':sha(folder/'receipt.json'),
            'validator_sha256':sha(Path(__file__)),
            'comparison_sha256':sha(comparison),'face_distinctness':pairs,
            'scope':'Five distinct native maps and ten actual source-bound renders. Photorealism and full-head seam review remain independent visual gates.'}
    output=root/'runtime/audit';output.mkdir(parents=True,exist_ok=True)
    (output/'looks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('FIVE_LOOK_AUDIT',report['status'],report['passed'],failed)
    if failed:raise SystemExit(1)


if __name__=='__main__':main()
