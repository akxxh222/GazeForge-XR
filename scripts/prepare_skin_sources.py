"""Safely extract data-only skin source files; record license/material metadata."""
import hashlib
import json
import zipfile
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
destination = (ROOT/'work/source_skins').resolve()
destination.mkdir(parents=True, exist_ok=True)
record = json.loads((ROOT/'work/downloads/skins02_download.json').read_text(encoding='utf-8-sig'))
files = []
with zipfile.ZipFile(ROOT/'work/downloads/skins02_cc0.zip') as archive:
    bad = archive.testzip()
    if bad:
        raise ValueError('Corrupt skin archive member: ' + bad)
    for item in archive.infolist():
        relative = Path(item.filename.replace('\\', '/'))
        target = (destination/relative).resolve()
        if not target.is_relative_to(destination):
            raise ValueError('Archive path escapes source directory')
        if item.is_dir() or target.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.mhmat', '.txt', '.json', '.md'}:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = archive.read(item)
        target.write_bytes(payload)
        entry = {'file': target.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(payload).hexdigest(), 'bytes': len(payload)}
        if target.suffix.lower() in {'.png', '.jpg', '.jpeg'}:
            with Image.open(target) as image:
                entry['dimensions'] = list(image.size)
        if target.suffix.lower() == '.mhmat':
            entry['material_metadata'] = [line.strip() for line in payload.decode('utf8', errors='replace').splitlines()
                                          if line.strip().split(' ', 1)[0] in {'name', 'author', 'license', 'diffuseTexture', 'normalmapTexture', 'bumpmapTexture'}]
        files.append(entry)
manifest = ROOT/'assets/source_skins/manifest.json'
manifest.parent.mkdir(parents=True, exist_ok=True)
record['files'] = files
catalog = json.loads((destination/'packs/skins02.json').read_text())
if any(asset.get('license') != 'CC0' for asset in catalog.values()):
    raise ValueError('Unexpected license in the skin catalog; review before reuse')
record['materials'] = catalog
record['submission_status'] = 'Source assets only. Native-UV transfer, seams and visual quality unverified; not included as completed texture looks.'
manifest.write_text(json.dumps(record, indent=2) + '\n')
print('SKIN_SOURCES_READY', len(files), 'data files')
for entry in files:
    if 'material_metadata' in entry:
        print(entry['file'], '; '.join(entry['material_metadata']))
