"""Export native canthus reference projections for frame-43 visual diagnosis."""
import json
from pathlib import Path
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wrapper import expressions

bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/milestone3/final/IRISX_MILESTONE3.blend'), use_scripts=False)
scene = bpy.context.scene
head = bpy.data.objects['GNM_skin']
landmarks = json.loads(scene['canthus_landmarks'])
corners = {s: [head.matrix_world @ head.data.vertices[i].co for i in landmarks[s]['head_vertex_indices']]
           for s in ('L', 'R')}
# Only project fixed native corner references; this is not a fresh measurement
# of the deformed visible eyelid silhouette or refracted pupil center.
for obj in scene.objects:
    if obj.name not in {'GazeRig', 'FixationTarget', 'Eye_L', 'Eye_R', 'RenderCamera'}:
        obj.hide_viewport = True
    else:
        for mod in obj.modifiers:
            mod.show_viewport = False
scene.render.resolution_x = scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
expressions.use_action('generate_motion')
result = {'scope': 'Native Basis canthus reference projections at 720 square; not measured visible aperture boundaries.', 'frames': {}}
for frame in (1, 43):
    scene.frame_set(frame)
    row = {}
    for side in ('L', 'R'):
        points = [world_to_camera_view(scene, scene.camera, p) for p in corners[side]]
        row[side] = sorted([[float(p.x*720), float((1-p.y)*720)] for p in points])
    result['frames'][str(frame)] = row
output = ROOT/'work/diagnostics/frame43_canthus_references.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print('FRAME43_REFERENCES', json.dumps(result), flush=True)
