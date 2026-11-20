"""Install portable material templates on an independently loaded native GNM."""
import hashlib
import json
from pathlib import Path

import bpy
import numpy as np
from . import submission_looks

ROOT=Path(__file__).resolve().parents[1]


def apply_to_native_head(texture_id='look_01'):
    """Assign native material regions; never replace mesh, UVs or transforms."""
    if texture_id not in tuple(f'look_{i:02d}' for i in range(1,6)):
        raise ValueError('texture_id must be look_01 through look_05')
    template=json.loads((ROOT/'native_materials.json').read_text(encoding='utf-8'))
    scene_file=ROOT/'scene.blend'
    if hashlib.sha256(scene_file.read_bytes()).hexdigest()!=template['scene_sha256']:
        raise ValueError('Material template scene checksum mismatch')
    for name,slots in template['materials'].items():
        obj=bpy.data.objects.get(name)
        if obj is None or obj.type!='MESH' or not obj.get('gnm_component'):
            raise ValueError('Load the original native GNM components first: '+name)
        if not obj.data.uv_layers.get('GNM_native_per_region'):
            raise ValueError('Original native UV layer required: '+name)
        values=np.array([list(v.uv) for v in obj.data.uv_layers['GNM_native_per_region'].data],np.float32)
        if hashlib.sha256(values.tobytes()).hexdigest()!=template['native_uv_sha256'][name]:
            raise ValueError('Native UV layout differs from the exported maps: '+name)
        if len(obj.data.materials)<=max(map(int,slots)):
            raise ValueError('Original native material regions required: '+name)
    names=sorted({material for slots in template['materials'].values() for material in slots.values()})
    with bpy.data.libraries.load(str(scene_file),link=False) as (available,loaded):
        if not set(names)<=set(available.materials):raise ValueError('Missing named template materials')
        # Blender replaces data_to entries with IDs when leaving this block.
        # Keep the source-name list separate from that mutable request list.
        loaded.materials=list(names)
    materials=dict(zip(names,loaded.materials))
    for name,slots in template['materials'].items():
        for slot,material in slots.items():
            bpy.data.objects[name].data.materials[int(slot)]=materials[material]
    bpy.context.scene['portable_look_schema']=submission_looks.SCHEMA
    return submission_looks.apply_look(texture_id)
