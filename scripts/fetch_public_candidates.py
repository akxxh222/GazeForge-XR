"""Download public asset candidates as inert data for license/Blender inspection."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'blender_hair_demo_page.html': 'https://www.blender.org/download/demo-files/',
    'hair_nodes-female_hair_styles.blend': 'https://download.blender.org/demo/geometry-nodes/hair_nodes-female_hair_styles.blend',
    'just_an_eye_page.html': 'https://aminmissaoui.gumroad.com/l/CJQXj',
    'blendswap_eye_page.html': 'https://blendswap.com/blend/31370',
    'blendswap_original_eye_page.html': 'https://blendswap.com/blend/2350',
    'bystedt_fox_eyes.blend': 'https://download.blender.org/demo/splash/blender-2.90-splash.blend',
    'makehuman_eyes/brown_eye.png': 'https://opengameart.org/sites/default/files/brown_eye.png',
    'makehuman_eyes/green_eye.png': 'https://opengameart.org/sites/default/files/green_eye.png',
}
EXPECTED = {
    'hair_nodes-female_hair_styles.blend': '1ad6202095c1793678fee7d69a7e9f8b5fdb6e5c293d300eb1062d2d437e8d48',
    'bystedt_fox_eyes.blend': '80b29f6dcd099460a60ae100503188474145495222bd88fea1b4df0bf0383041',
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', nargs='+', choices=list(SOURCES), help='Download only these source files')
    args = parser.parse_args()
    folder = ROOT/'work/public_candidates'
    folder.mkdir(parents=True, exist_ok=True)
    entries = []
    for name, url in SOURCES.items():
        if args.only and name not in args.only:
            continue
        path = folder/name
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(request, timeout=90) as response:
                data = response.read()
            digest = hashlib.sha256(data).hexdigest()
            if name in EXPECTED and digest != EXPECTED[name]:
                raise ValueError('Source checksum changed; inspect before importing')
            path.write_bytes(data)
            entry = {'file': name, 'url': url, 'bytes': len(data), 'sha256': digest}
        except Exception as error:
            entry = {'file': name, 'url': url, 'error': str(error)}
        entries.append(entry)
        print(json.dumps(entry), flush=True)
    (folder/'download_receipt.json').write_text(json.dumps(entries, indent=2)+'\n')


if __name__ == '__main__':
    main()
