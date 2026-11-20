"""Apply explicitly exported native-UV maps to the M5 review scene."""
import hashlib
import json
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'IrisX portable native look 1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply_look(texture_id='look_01'):
    if texture_id not in tuple(f'look_{i:02d}' for i in range(1, 6)):
        raise ValueError('texture_id must be look_01 through look_05')
    if bpy.context.scene.get('portable_look_schema') != SCHEMA:
        raise ValueError('Load the portable M5 scene before applying these maps')
    folder = ROOT / 'textures' / texture_id
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    for name, record in manifest['files'].items():
        if sha(folder / name) != record['sha256']:
            raise ValueError('Portable texture checksum mismatch: ' + name)
    # Each tagged image node uses the original native UV coordinates. Updating
    # shared material IDs together keeps skin-dependent canthal joins matched.
    replacements = {}
    owners = [bpy.data.objects['GNM_skin'].data.materials[0]]
    owners += [bpy.data.objects['Eye_' + side].data.materials[slot]
               for side in ('L', 'R') for slot in (0, 1)]
    for original in owners:
        if original in replacements:
            continue
        material = original.copy()
        material.name = texture_id + ' | ' + original.name.split(' | ')[-1]
        for node in material.node_tree.nodes:
            filename = node.get('portable_file')
            if filename:
                image = bpy.data.images.load(str(folder / filename), check_existing=False)
                image.colorspace_settings.name = 'sRGB' if 'basecolor' in filename else 'Non-Color'
                image.pack()
                node.image = image
        replacements[original] = material
    for obj in bpy.context.scene.objects:
        if hasattr(obj.data, 'materials'):
            for slot, material in enumerate(obj.data.materials):
                if material in replacements:
                    obj.data.materials[slot] = replacements[material]
    bpy.context.scene['texture_look'] = texture_id
    return {'id': texture_id, 'method': 'Explicit portable native skin/sclera/iris maps; original layered optical rig retained',
            'manifest_sha256': sha(folder / 'manifest.json'), 'application_module_sha256': sha(Path(__file__)),
            'status': manifest['status']}
