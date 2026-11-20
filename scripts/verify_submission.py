"""Verify the supplied files, decoded videos and geometric pupil labels."""
import argparse,hashlib,json,math,sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--output',type=Path)
    args=parser.parse_args();root=args.root.resolve();checks=[]
    def check(name,value):
        checks.append({'test':name,'passed':bool(value)})
        if not value:print('FAIL',name)
    manifest=json.loads((root/'bundle_manifest.json').read_text())
    for row in manifest['files']:
        name=Path(row['file']);path=(root/name).resolve()
        contained=path.is_relative_to(root) and not name.is_absolute()
        check(row['file']+' path',contained)
        check(row['file']+' hash',contained and path.is_file() and sha(path)==row['sha256'])
    expected={f'frame_{i:02d}.png' for i in range(10)}
    check('ten official images, one version each',{p.name for p in (root/'renders').glob('*.png')}==expected)
    for p in sorted((root/'renders').glob('*.png'))+sorted((root/'previews').glob('*.png')):
        with Image.open(p) as image:check(str(p.relative_to(root))+' 1024-square render',image.size==(1024,1024) and image.mode=='RGB')
    for mode in ('left','right','generate_motion'):
        cap=cv2.VideoCapture(str(root/'videos'/(mode+'.mp4')));fps=cap.get(cv2.CAP_PROP_FPS);count=0;size=None
        while True:
            ok,frame=cap.read()
            if not ok:break
            size=frame.shape[:2];count+=1
        cap.release();check(mode+' full video decodes',count==144 and abs(fps-24)<.001 and size==(720,720))
    metadata=json.loads((root/'metadata.json').read_text());frames=metadata['frames']
    check('one metadata record for each image',len(frames)==10)
    centers={s:np.array(frames[0]['eye_center_3D_'+s]) for s in ('L','R')}
    midpoint=(centers['L']+centers['R'])/2
    for k,row in enumerate(frames):
        theta=2*math.pi*k/10
        check(f'frame {k} clockwise input',row['frame']==k and abs(row['theta']-theta)<1e-10 and abs(row['input']['h']-math.sin(theta))<1e-6 and abs(row['input']['v']-math.cos(theta))<1e-6)
        matrix=np.asarray(row['camera_matrix'],float)
        check(f'frame {k} finite projection',matrix.shape==(3,4) and np.isfinite(matrix).all())
        target=np.asarray(row['fixation_world_m']);delta=target-midpoint
        check(f'frame {k} 35cm target plane and bounds',abs(delta[1]+.35)<1e-6 and max(abs(delta[0]),abs(delta[2]))<=.050001)
        for side in ('L','R'):
            p=np.r_[row['pupil_center_3D_'+side],1];q=matrix@p;uv=q[:2]/q[2]
            check(f'frame {k} pupil projection {side}',np.max(abs(uv-np.asarray(row['pupil_center_2D_'+side])))<1e-4)
            center=np.asarray(row['eye_center_3D_'+side]);check(f'frame {k} pivot {side}',np.max(abs(center-centers[side]))<1e-7)
            w,x,y,z=row['eye_quaternion_wxyz_'+side]
            axis=np.array([2*(x*y-w*z),1-2*(x*x+z*z),2*(y*z+w*x)])
            direction=target-center;direction/=np.linalg.norm(direction)
            check(f'frame {k} common target {side}',np.linalg.norm(axis-direction)<1e-5)
    media=list((root/'renders').glob('*.png'))+list((root/'previews').glob('*.png'))+list((root/'videos').glob('*.mp4'))
    hashes={}
    for p in media:hashes.setdefault(sha(p),[]).append(str(p.relative_to(root)))
    duplicates=[v for v in hashes.values() if len(v)>1]
    check('no duplicate rendered files or video versions',not duplicates)
    check('one editable scene',len(list(root.glob('*.blend')))==1 and not list(root.rglob('*.blend1')))
    check('five native texture looks',len(list((root/'textures').glob('look_*/manifest.json')))==5)
    failed=sum(not c['passed'] for c in checks)
    report={'status':'PASS' if not failed else 'FAIL','passed':len(checks)-failed,'failed':failed,'checks':checks,'duplicate_media':duplicates,
            'scene_sha256':sha(root/'scene.blend'),'scope':'Existing submission bytes, rendered media, ordered labels, fixed pivots and common-target projection. Visual quality is assessed separately.'}
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print('SUBMISSION',report['status'],report['passed'],failed)
    if failed:raise SystemExit(1)
if __name__=='__main__':main()
