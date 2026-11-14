"""Measure evaluated skin/eye occlusion and inspect current optical materials."""
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wrapper import expressions


def tree(obj, graph):
    evaluated = obj.evaluated_get(graph)
    mesh = evaluated.to_mesh()
    result = BVHTree.FromPolygons([evaluated.matrix_world @ v.co for v in mesh.vertices],
                                 [list(p.vertices) for p in mesh.polygons])
    evaluated.to_mesh_clear()
    return result


def main():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/milestone3/final/IRISX_MILESTONE3.blend'), use_scripts=False)
    scene = bpy.context.scene
    expressions.use_action('generate_motion')
    scene.camera = bpy.data.objects['RenderCamera']
    folder = ROOT/'work/review/eye_refinement'
    folder.mkdir(parents=True, exist_ok=True)
    materials = {}
    for owner in ['Eye_L', 'Eye_R', 'GNM_skin', 'Lid_caruncle_L_native', 'Mucosal_rim_L']:
        obj = bpy.data.objects[owner]
        for material in obj.data.materials:
            if material.name in materials:
                continue
            materials[material.name] = [
                {'name': n.name, 'type': n.type,
                 'inputs': {i.name: list(i.default_value) if hasattr(i.default_value, '__len__') else i.default_value
                            for i in n.inputs if hasattr(i, 'default_value') and not i.is_linked
                            and isinstance(i.default_value, (int, float, str, bool)) or
                            hasattr(i, 'default_value') and not i.is_linked and hasattr(i.default_value, '__len__')},
                 'links': [f'{l.from_node.name}.{l.from_socket.name} -> {l.to_node.name}.{l.to_socket.name}'
                           for output in n.outputs for l in output.links]}
                for n in material.node_tree.nodes if n.type in {'BSDF_PRINCIPLED', 'BSDF_GLASS', 'BSDF_TRANSPARENT',
                                                               'OUTPUT_MATERIAL', 'BUMP', 'TEX_IMAGE'}]
    result = {'scope': 'Actual evaluated head/eye nearest-surface occlusion at pixel centers; attachments excluded from aperture mask.',
              'materials': materials, 'frames': {}}
    width = 720
    camera = scene.camera
    inv = (camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(), x=width, y=width) @ camera.matrix_world.inverted()).inverted()
    origin = camera.matrix_world.translation
    for frame in (1, 43):
        scene.frame_set(frame)
        graph = bpy.context.evaluated_depsgraph_get()
        head = tree(bpy.data.objects['GNM_skin'], graph)
        row = {}
        for side, bounds in [('R', (260, 335, 334, 388)), ('L', (389, 335, 463, 388))]:
            eye = tree(bpy.data.objects['Eye_'+side], graph)
            pixels = []
            for y in range(bounds[1], bounds[3]):
                for x in range(bounds[0], bounds[2]):
                    near = inv @ Vector((2*(x+.5)/width-1, 1-2*(y+.5)/width, -1, 1))
                    direction = (Vector(near[:3])/near.w-origin).normalized()
                    eh = eye.ray_cast(origin, direction)
                    if eh[0] is None:
                        continue
                    hh = head.ray_cast(origin, direction)
                    if hh[0] is None or eh[3] < hh[3]:
                        pixels.append([x, y])
            xs, ys = zip(*pixels)
            row[side] = {'visible_pixel_count': len(pixels), 'bounds_xyxy': [min(xs), min(ys), max(xs), max(ys)],
                         'centroid': [sum(xs)/len(xs), sum(ys)/len(ys)], 'pixels': pixels}
            print('APERTURE', frame, side, len(pixels), row[side]['bounds_xyxy'], flush=True)
        result['frames'][str(frame)] = row
    (folder/'aperture_probe.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print('EYE_APPEARANCE_PROBE_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
