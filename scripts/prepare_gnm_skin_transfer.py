"""Project licensed MakeHuman skin sources onto unchanged native GNM UVs.

Run inside Blender. Only the temporary source mesh is aligned/deformed. The
GNM target's vertex positions, topology and UV coordinates remain untouched.
"""
import gzip
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]


def barycentric(point, a, b, c):
    v0, v1, v2 = b-a, c-a, point-a
    d00, d01, d11 = np.dot(v0, v0), np.dot(v0, v1), np.dot(v1, v1)
    denominator = d00*d11-d01*d01
    if abs(denominator) < 1e-20:
        return np.array([1., 0., 0.])
    y = (d11*np.dot(v2, v0)-d01*np.dot(v2, v1))/denominator
    z = (d00*np.dot(v2, v1)-d01*np.dot(v2, v0))/denominator
    return np.array([1-y-z, y, z])


def main():
    with gzip.open(ROOT/'assets/mpfb_head.json.gz', 'rt') as f:
        source = json.load(f)
    a = np.array(source['vertices'], dtype=np.float64)
    with np.load(ROOT/'assets/gnm/gnm_head.npz', allow_pickle=False) as model:
        rotation = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]])
        midpoint = model['template_joint_positions'][2:4].mean(0)
        b = (model['template_vertex_positions']-midpoint) @ rotation.T
        quads = model['quads']
        uvs = model['quad_uvs']
        groups = dict(zip(model['vertex_group_names'].tolist(), model['vertex_groups']))
        target_faces = np.flatnonzero((groups['skin'][quads] > .5).all(1))
        target_quads = quads[target_faces]
        upper, lower = b[groups['upper_lip'] > .5], b[groups['lower_lip'] > .5]
        lip_weight = np.maximum(groups['upper_lip'], groups['lower_lip'])
    lip_ids = sorted({i for face, zone in zip(source['faces'], source['zones']) if zone == 'lips' for i in face})
    lips = a[lip_ids]
    target_lips = np.concatenate([upper, lower])
    controls = []
    # Keep alignment tied to geometric features; source UVs remain attached.
    for sign in (-1, 1):
        controls.append((np.array(source['eye_centers']['L' if sign > 0 else 'R']), np.array([sign*.03085, 0, 0])))
        controls.append((lips[np.argmax(sign*lips[:, 0])], target_lips[np.argmax(sign*target_lips[:, 0])]))
    for source_set, target_set in [(lips[lips[:, 2] > np.median(lips[:, 2])], upper),
                                   (lips[lips[:, 2] <= np.median(lips[:, 2])], lower)]:
        controls.append((source_set[np.argmin(source_set[:, 1])], target_set[np.argmin(target_set[:, 1])]))
    mask_a = (abs(a[:, 0]) < .015) & (a[:, 2] > -.055) & (a[:, 2] < .015)
    mask_b = (abs(b[:, 0]) < .015) & (b[:, 2] > -.055) & (b[:, 2] < .015)
    controls.append((a[mask_a][np.argmin(a[mask_a][:, 1])], b[mask_b][np.argmin(b[mask_b][:, 1])]))
    for anchor in [(0, .05, .10), (0, .17, .03), (0, .06, -.17), (-.08, .08, -.025), (.08, .08, -.025), (0, 0, -.12)]:
        controls.append((np.array(anchor), np.array(anchor)))
    control_source = np.array([c[0] for c in controls])
    control_target = np.array([c[1] for c in controls])
    sigma = .035
    kernel = np.exp(-np.square(control_source[:, None]-control_source[None]).sum(2)/(2*sigma*sigma))
    coefficients = np.linalg.solve(kernel+np.eye(len(kernel))*1e-7, control_target-control_source)
    a += np.exp(-np.square(a[:, None]-control_source[None]).sum(2)/(2*sigma*sigma)) @ coefficients

    mesh = bpy.data.meshes.new('Temporary source correspondence mesh')
    mesh.from_pydata(a.tolist(), [], source['faces'])
    mesh.update()
    uv = mesh.uv_layers.new(name='MakeHuman_source')
    for poly, coords in zip(mesh.polygons, source['uvs']):
        for loop_index, coord in zip(poly.loop_indices, coords):
            uv.data[loop_index].uv = coord
    obj = bpy.data.objects.new('Temporary source correspondence mesh', mesh)
    bpy.context.scene.collection.objects.link(obj)
    mod = obj.modifiers.new('Source correspondence smoothing', 'SUBSURF')
    mod.levels = 2
    bpy.context.view_layer.update()
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    detailed = evaluated.to_mesh()
    detailed.calc_loop_triangles()
    points = np.array([v.co[:] for v in detailed.vertices])
    triangles = np.array([t.vertices[:] for t in detailed.loop_triangles])
    tri_uvs = np.array([[detailed.uv_layers.active.data[i].uv[:] for i in t.loops] for t in detailed.loop_triangles])
    tree = BVHTree.FromPolygons(points.tolist(), triangles.tolist(), all_triangles=True)
    tri_points = points[triangles]
    normals = np.cross(tri_points[:, 1]-tri_points[:, 0], tri_points[:, 2]-tri_points[:, 0])
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-20)
    centers = tri_points.mean(1)
    front_ids = np.flatnonzero((normals[:, 1] < -.25) & (centers[:, 1] < .05) & (centers[:, 2] > -.15))
    front_tree = BVHTree.FromPolygons(points.tolist(), triangles[front_ids].tolist(), all_triangles=True)

    def nearest(point):
        # Interior socket UV islands contain mucosa. Do not project them onto
        # the visible GNM lid skin merely because they are closer in 3D.
        orbital = abs(abs(point[0])-.03085) < .023 and -.014 < point[2] < .022 and point[1] < .012
        result = (front_tree if orbital else tree).find_nearest(Vector(point))
        hit, normal, index, distance = result
        return hit, normal, int(front_ids[index]) if orbital else index, distance
    mapped = np.empty((len(target_quads), 4, 2), dtype=np.float32)
    distances = []
    seam_faces = 0
    for i, quad in enumerate(target_quads):
        center = b[quad].mean(0)
        hit, normal, center_id, distance = nearest(center)
        corner_uvs = []
        for p in b[quad]:
            hit, normal, triangle_id, distance = nearest(p)
            weights = barycentric(np.array(hit), *points[triangles[triangle_id]])
            corner_uvs.append(weights @ tri_uvs[triangle_id])
            distances.append(distance)
        corner_uvs = np.array(corner_uvs)
        if np.ptp(corner_uvs, axis=0).max() > .20:
            # A source-atlas seam cannot be interpolated across a target quad.
            # Locally extrapolate the nearest central source triangle instead.
            seam_faces += 1
            corner_uvs = np.array([barycentric(p, *points[triangles[center_id]]) @ tri_uvs[center_id] for p in b[quad]])
        mapped[i] = corner_uvs
    evaluated.to_mesh_clear()
    bpy.data.objects.remove(obj, do_unlink=True)
    output = ROOT/'assets/gnm/skin_transfer.npz'
    np.savez_compressed(output, target_face_ids=target_faces, native_uvs=uvs[target_faces],
                        source_uvs=mapped, positions=b[target_quads].astype('float32'),
                        lip_weights=lip_weight[target_quads],
                        control_source=control_source, control_target=control_target)
    report = {'method': 'Locally aligned MakeHuman source surface; nearest-triangle UV projection; native GNM UV rasterization follows',
              'source_geometry': 'assets/mpfb_head.json.gz', 'source_license': 'CC0-1.0',
              'target': 'GNM Head 3.0 skin; unchanged native per-region UVs',
              'target_faces': len(target_quads), 'source_seam_quads_locally_extrapolated': seam_faces,
              'projection_distance_m': {'median': float(np.median(distances)), 'p95': float(np.quantile(distances, .95)), 'max': float(max(distances))},
              'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
              'status': 'Correspondence prepared; texture alignment and seams require render review.'}
    (ROOT/'assets/gnm/skin_transfer.json').write_text(json.dumps(report, indent=2)+'\n')
    print('GNM_TRANSFER_READY', json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
