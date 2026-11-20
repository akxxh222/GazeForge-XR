"""Verify archive hashes and root layout, then extract to a fresh directory."""
import argparse
import hashlib
import json
from pathlib import Path,PurePosixPath
import zipfile


def main():
    parser=argparse.ArgumentParser();parser.add_argument('archive',type=Path)
    parser.add_argument('--extract',required=True,type=Path);parser.add_argument('--report',required=True,type=Path)
    args=parser.parse_args();target=args.extract.resolve()
    if target.exists():raise FileExistsError('Use a fresh extraction directory; existing work is never removed')
    checks=[]
    def check(name,value):
        checks.append({'test':name,'passed':bool(value)})
        if not value:raise ValueError(name)
    with zipfile.ZipFile(args.archive) as z:
        names=z.namelist()
        check('unique archive paths',len(names)==len(set(names)))
        check('relative contained archive paths',all(not PurePosixPath(n).is_absolute() and
              '\\' not in n and ':' not in n and '..' not in PurePosixPath(n).parts and
              (target/n).resolve().is_relative_to(target) for n in names))
        check('archive CRC',z.testzip() is None)
        manifest=json.loads(z.read('bundle_manifest.json'))
        expected={r['file'] for r in manifest['files']}|{'bundle_manifest.json'}
        check('exact manifest member set',set(names)==expected)
        for record in manifest['files']:
            data=z.read(record['file'])
            check('size and SHA256 '+record['file'],len(data)==record['bytes'] and hashlib.sha256(data).hexdigest()==record['sha256'])
        required={'scene.blend','wrapper/eyes.py','metadata.json','README.md','submission.json'}
        required|={f'renders/frame_{i:02d}.png' for i in range(10)}
        required|={f'videos/{mode}.mp4' for mode in ('left','right','generate_motion')}
        check('official root layout and three videos',required<=set(names))
        marker=json.loads(z.read('submission.json'))
        check('team and submission status',marker['team']=='VITChennai_IrisX' and marker['status']=='SUBMISSION_READY')
        z.extractall(target)
    # Read all extracted files, rather than assuming extraction succeeded.
    check('all extracted hashes',all(hashlib.sha256((target/r['file']).read_bytes()).hexdigest()==r['sha256'] for r in manifest['files']))
    report={'status':'PASS','scope':'Archive integrity, allowlisted root layout and clean extraction only; appearance limits are documented separately',
            'archive_sha256':hashlib.sha256(args.archive.read_bytes()).hexdigest(),'bytes':args.archive.stat().st_size,
            'members':len(names),'passed':len(checks),'failed':0,'checks':checks,'extracted_to':str(target)}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('ARCHIVE_VERIFIED',len(names),'members;',len(checks),'checks')


if __name__=='__main__':main()
