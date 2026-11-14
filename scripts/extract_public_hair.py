"""Freeze the author's evaluated groom as data; never run embedded scripts.

Run against the pinned official Hair Styles .blend with --disable-autoexec.
The source author is Daniel Bystedt, published CC BY-SA (version unstated).
"""
import json
from pathlib import Path
import bpy
import numpy as np

root=Path(__file__).resolve().parents[1]
output=root/'work/public_candidates'
scene=bpy.data.scenes['hairstyles main']
bpy.context.window.scene=scene
def enable(layer):
    layer.exclude=False
    layer.hide_viewport=False
    for child in layer.children:
        enable(child)
enable(bpy.context.view_layer.layer_collection)
for collection in bpy.data.collections:
    collection.hide_viewport=False
for obj in bpy.data.objects:
    obj.hide_viewport=False
    obj.hide_set(False)
bpy.context.view_layer.update()
report={}
for name in ['curly hair','cyberpunk hair','long hair main','eyes','head']:
    obj=bpy.data.objects[name]
    evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    entry={'type':evaluated.type,'matrix_world':[list(r) for r in obj.matrix_world],
           'dimensions':list(evaluated.dimensions)}
    if evaluated.type=='CURVES':
        data=evaluated.data
        entry['curves']=len(data.curves)
        entry['points']=len(data.points)
        entry['attributes']=[(a.name,a.domain,a.data_type) for a in data.attributes]
        positions=np.array([p.vector[:] for p in data.attributes['position'].data],dtype=np.float32)
        starts=np.array([c.first_point_index for c in data.curves],dtype=np.int32)
        sizes=np.array([c.points_length for c in data.curves],dtype=np.int32)
        radii=np.array([p.value for p in data.attributes['radius'].data],dtype=np.float32) if data.attributes.get('radius') else np.full(len(positions),.0005)
        np.savez_compressed(output/(name.replace(' ','_')+'_evaluated.npz'),positions=positions,starts=starts,sizes=sizes,radii=radii,matrix_world=np.array(obj.matrix_world))
    elif evaluated.type=='MESH':
        mesh=evaluated.to_mesh()
        positions=np.array([evaluated.matrix_world@v.co for v in mesh.vertices])
        entry['bounds']=[positions.min(0).tolist(),positions.max(0).tolist()]
        entry['material_slots']=[m.name for m in obj.data.materials]
        evaluated.to_mesh_clear()
    report[name]=entry
for mat in bpy.data.materials:
    if 'eye' in mat.name.lower():
        report[mat.name]={'nodes':[(n.name,n.bl_idname,getattr(n,'node_tree',None).name if getattr(n,'node_tree',None) else None) for n in mat.node_tree.nodes]}
(output/'hair_evaluation.json').write_text(json.dumps(report,indent=2)+'\n')
print('HAIR_EVALUATED',[(name,entry.get('curves')) for name,entry in report.items() if entry.get('curves')],flush=True)
