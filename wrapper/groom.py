"""Original, deterministic scalp groom fitted to the unchanged GNM surface.

Native Cycles hair curves, in meters. This is a static groom, not a scalp
texture or a mesh cap. Root deformation for expressions remains M3 work.
"""
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

from .appearance import _curve, _strand_material


def _hairline(point):
    """An irregular adult hairline; lower at the sides and occiput."""
    x, y, z = point
    angle = abs(math.atan2(x, .065-y))
    anchors = [0, .45, .72, 1.05, 1.45, 1.9, 2.5, math.pi]
    heights = [.056, .060, .052, .022, -.003, -.022, -.044, -.049]
    index = min(6, max(0, int(np.searchsorted(anchors, angle))-1))
    u = (angle-anchors[index])/(anchors[index+1]-anchors[index])
    u = u*u*(3-2*u)
    boundary = heights[index]*(1-u)+heights[index+1]*u
    boundary += .00065*math.sin(360*x+35*y)+.00045*math.sin(712*x-81*y)
    return z-boundary


def add_scalp_groom(texture_id='look_01', count=64000):
    rng = np.random.default_rng(83125)
    obj = bpy.data.objects['GNM_skin']
    # Native anatomical ear membership avoids removing a whole strip of scalp
    # with an arbitrary X threshold (which leaves an implausible bare temple).
    with np.load(Path(__file__).resolve().parents[1]/'assets/gnm/gnm_head.npz', allow_pickle=False) as source:
        ear_mask = source['vertex_groups'][source['vertex_group_names'].tolist().index('ears')]
    native_ids = [item.value for item in obj.data.attributes['gnm_vertex_id'].data]
    nearest_base = KDTree(len(obj.data.vertices))
    for index, vertex in enumerate(obj.data.vertices):
        nearest_base.insert(obj.matrix_world @ vertex.co, index)
    nearest_base.balance()
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    vertices = np.array([obj.matrix_world @ v.co for v in mesh.vertices])
    triangles = np.array([t.vertices[:] for t in mesh.loop_triangles], dtype=np.int32)
    xyz = vertices[triangles]
    centers = xyz.mean(axis=1)
    candidates = np.array([_hairline(p) > -.002 for p in centers])
    xyz = xyz[candidates]
    cross = np.cross(xyz[:, 1]-xyz[:, 0], xyz[:, 2]-xyz[:, 0])
    areas = np.linalg.norm(cross, axis=1)
    probability = areas/areas.sum()
    bvh = BVHTree.FromPolygons(vertices.tolist(), triangles.tolist(), all_triangles=True)
    evaluated.to_mesh_clear()

    center = Vector((0, .065, .026))

    def project(point):
        direction = (point-center).normalized()
        origin = center+direction*.30
        p, n, face, distance = bvh.ray_cast(origin, -direction, .32)
        return p, n

    # Sample triangle area rather than UV area: root density is independent of
    # atlas stretching. The sparse edge and part are sampled, not painted black.
    roots = []
    attempts = 0
    while len(roots) < count and attempts < count*15:
        batch = min(10000, (count-len(roots))*2)
        selected = xyz[rng.choice(len(xyz), batch, p=probability)]
        a = np.sqrt(rng.random(batch))
        b = rng.random(batch)
        points = (1-a[:, None])*selected[:, 0]+a[:, None]*(1-b[:, None])*selected[:, 1]+a[:, None]*b[:, None]*selected[:, 2]
        for point in points:
            attempts += 1
            edge = _hairline(point)
            if edge < 0 or rng.random() > min(1, .12+edge/.0035):
                continue
            _, nearest_index, _ = nearest_base.find(Vector(point))
            if ear_mask[native_ids[nearest_index]] > .1:
                continue
            fitted, fitted_normal = project(Vector(point))
            # Reject hidden triangles and ear folds instead of moving their
            # roots to a different radial surface several millimeters away.
            if fitted is None or (fitted-Vector(point)).length > .0003:
                continue
            # A narrow, slightly curved right-side part on the top only.
            part = .036+.015*(point[1]-.03)
            if point[2] > .076 and point[1] < .122:
                distance = abs(point[0]-part)
                if rng.random() > min(1, .15+distance/.0007):
                    continue
            roots.append(point)
            if len(roots) == count:
                break
    if len(roots) != count:
        raise RuntimeError('Unable to populate the scalp groom')

    strands = []
    max_root_error = 0.
    min_clearance = 1.
    for root_array in roots:
        root, normal = project(Vector(root_array))
        if root is None:
            raise RuntimeError('Scalp root projection failed')
        max_root_error = max(max_root_error, (root-Vector(root_array)).length)
        top = max(0., min(1., (normal.z-.15)/.65))
        front = max(0., min(1., (.08-root.y)/.095))
        clump = .85+.15*math.sin(root.x*640+root.y*170)
        length = rng.uniform(.010, .018)*(1-top)+rng.uniform(.040, .061)*top
        length *= clump
        length *= top+(1-top)*(.25+.75*min(1, _hairline(root)/.020))
        lift = (.0014*(1-top)+(.007+.011*front)*top)*rng.uniform(.70, 1.30)*clump
        flyaway = rng.random() < .018
        if flyaway:
            lift *= rng.uniform(1.25, 1.65)
        side = -1 if root.x < .036+.015*(root.y-.03) else 1
        variation = rng.normal(0, .13)
        phase = rng.uniform(0, 2*math.pi)
        current = root.copy()
        points = [root+normal*.000035]
        for index in range(1, 12):
            t = index/11
            # Swept-back top, combed-down sides, with a soft crown turn.
            comb = Vector((side*(.68 if side < 0 else .25)+variation,
                           .92, -.85*(1-top)))
            if root.y > .11:
                comb += Vector((-.16, -.15, -.48))
            comb -= normal*comb.dot(normal)
            if comb.length < .05:
                comb = Vector((1, 0, 0)).cross(normal)
            comb.normalize()
            proposal = current+comb*(length/11)
            p, normal = project(proposal)
            if p is None:
                raise RuntimeError('Scalp strand projection failed')
            current = p
            offset = .000035+lift*math.sin(math.pi*t*.84)**.80
            # Millimeter-scale irregularity follows the groom, not white noise.
            wave = .00030*math.sin(2*math.pi*t+phase)*math.sin(math.pi*t)
            point = p+normal*offset+normal.cross(comb)*wave
            min_clearance = min(min_clearance, offset)
            points.append(point)
        strands.append(points)

    melanin, redness = {'look_01': (.94, .10), 'look_02': (.98, .10),
                        'look_03': (.85, .17), 'look_04': (.40, .58),
                        'look_05': (.92, .14)}[texture_id]
    material = _strand_material('Scalp | natural melanin fibers', melanin, redness, .43)
    material.node_tree.nodes.get('Principled Hair BSDF').inputs['Random Color'].default_value = .16
    groom = _curve('Scalp_swept_back_hair', strands, material, .000040)
    world = groom.matrix_world.copy()
    groom.parent = obj
    groom.matrix_world = world
    groom['groom_style'] = 'Short swept-back adult cut, tapered sides, sparse irregular hairline and right part'
    groom['groom_seed'] = 83125
    groom['root_surface'] = 'GNM_skin evaluated subdivision; no target UV or topology modifications'
    groom['hair_length_range_m'] = [.007, .061]
    return {'scalp_strands': len(strands), 'points_per_strand': 12,
            'max_root_fit_error_m': max_root_error, 'minimum_control_clearance_m': min_clearance,
            'native_curves': True, 'static_groom': True}
