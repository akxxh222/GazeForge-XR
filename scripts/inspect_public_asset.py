"""Inventory an untrusted .blend opened with --disable-autoexec; no drivers executed."""
import argparse
import json
from pathlib import Path
import sys
import bpy

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])

def modifier_inputs(modifier):
    try:
        return {k: str(modifier[k]) for k in modifier.keys() if k != '_RNA_UI'}
    except TypeError:
        return {}

objects = []
for obj in bpy.data.objects:
    entry = {'name': obj.name, 'type': obj.type, 'location': list(obj.location),
             'scale': list(obj.scale), 'dimensions': list(obj.dimensions),
             'hide_render': obj.hide_render, 'parent': obj.parent.name if obj.parent else None,
             'collections': [c.name for c in obj.users_collection],
             'materials': [s.material.name if s.material else None for s in obj.material_slots]}
    if obj.type == 'CURVES':
        entry['curves'] = len(obj.data.curves)
        entry['points'] = len(obj.data.points)
        entry['surface'] = obj.data.surface.name if obj.data.surface else None
        entry['attributes'] = [(a.name, a.data_type, a.domain) for a in obj.data.attributes]
    elif obj.type == 'MESH':
        entry['vertices'] = len(obj.data.vertices)
        entry['uvs'] = [u.name for u in obj.data.uv_layers]
    elif obj.type == 'CAMERA':
        entry['lens'] = obj.data.lens
    entry['modifiers'] = [{'name': m.name, 'type': m.type,
                           'node_group': m.node_group.name if m.type == 'NODES' and m.node_group else None,
                           'inputs': modifier_inputs(m)} for m in obj.modifiers]
    objects.append(entry)
data = {'filepath': bpy.data.filepath,
        'scenes': [{'name': s.name, 'camera': s.camera.name if s.camera else None, 'engine': s.render.engine} for s in bpy.data.scenes],
        'objects': objects, 'collections': [c.name for c in bpy.data.collections],
        'images': [{'name': i.name, 'path': i.filepath, 'packed': bool(i.packed_file)} for i in bpy.data.images],
        'texts': {t.name: t.as_string()[:14000] for t in bpy.data.texts},
        'materials': [{'name': m.name, 'nodes': [(n.name,n.bl_idname) for n in m.node_tree.nodes] if m.node_tree else []} for m in bpy.data.materials],
        'node_groups': [n.name for n in bpy.data.node_groups]}
args.output.write_text(json.dumps(data, indent=2)+'\n')
print('ASSET_INVENTORY', args.output, len(objects), 'objects', flush=True)
