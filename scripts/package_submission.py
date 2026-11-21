"""Create the team ZIP with the required paths at its root."""
import argparse,hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def files(root):
    names=['scene.blend','scene_build.json','native_materials.json','submission.json','metadata.json','README.md','MILESTONES.md','LICENSE','requirements.txt','contact_sheet.png']
    result=[root/n for n in names]
    for folder in ('wrapper','scripts','textures','renders','videos','previews','demo','docs','assets','tests'):
        for p in (root/folder).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and not p.name.startswith('~$') and not p.name.endswith(('.pyc','.log','.blend1')):result.append(p)
    return sorted(result,key=lambda p:p.relative_to(root).as_posix())
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--output',type=Path)
    args=parser.parse_args();root=args.root.resolve();output=(args.output or root/'VITChennai_IrisX.zip').resolve()
    paths=files(root)
    if any(not p.is_file() for p in paths):raise FileNotFoundError('A required submission file is missing')
    if len(paths)!=len(set(paths)):raise ValueError('Duplicate archive member')
    manifest={'team':'VITChennai_IrisX','schema':'IrisX submission hashes 1','files':[{'file':p.relative_to(root).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in paths]}
    (root/'bundle_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for p in paths+[root/'bundle_manifest.json']:archive.write(p,p.relative_to(root).as_posix())
    with zipfile.ZipFile(output) as archive:
        if archive.testzip():raise ValueError('ZIP CRC check failed')
    output.with_suffix(output.suffix+'.sha256').write_text(sha(output)+'  '+output.name+'\n')
    print('PACKAGED',output,len(paths)+1,flush=True)
if __name__=='__main__':main()
