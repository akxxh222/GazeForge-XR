"""Static, surface-fitted brows, lashes and tear menisci for material review.

Lid animation and deformation-aware attachments are milestone 3 work.
"""
import math
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _material(name, color, roughness):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    return material


def _curve(name, strands, material, radius):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 3
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    for strand in strands:
        spline = curve.splines.new('BEZIER')
        spline.bezier_points.add(len(strand)-1)
        for index, (point, xyz) in enumerate(zip(spline.bezier_points, strand)):
            point.co = xyz
            point.handle_left_type = point.handle_right_type = 'AUTO'
            point.radius = max(.06, 1-.94*index/(len(strand)-1)) if len(strands) > 1 else 1
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    curve.materials.append(material)
    obj['appearance_stage'] = 'Milestone 2 static appearance; rebind to animated lids in milestone 3'
    return obj


def add_static_details(texture_id):
    rng = np.random.default_rng(5821)
    head = bpy.data.objects['GNM_skin']
    deps = bpy.context.evaluated_depsgraph_get()
    surface = head.evaluated_get(deps)
    brown = (.032, .016, .007) if texture_id != 'look_04' else (.11, .035, .008)
    if texture_id == 'look_02':
        brown = (.006, .004, .003)
    hair = _material('Fine brow and lash hair', brown, .60)
    wet = _material('Tear meniscus | water approximation', (.97, .94, .91), .09)
    shader = wet.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Transmission Weight'].default_value = 1
    shader.inputs['IOR'].default_value = 1.333
    stats = {}

    def skin_hit(x, z):
        hit, point, normal, face = surface.ray_cast(Vector((x, -.20, z)), Vector((0, 1, 0)))
        return point if hit else None

    for sign, side in [(1, 'L'), (-1, 'R')]:
        strands = []
        for index in range(620):
            u = rng.uniform(0, 1)
            x = sign*(.014+.046*u)
            z = .013+.007*math.sin(u*math.pi)-.004*u+rng.normal(0, .00085)
            root = skin_hit(x, z)
            if root is None:
                continue
            points = []
            hair_dx = sign*(.0005+.0025*u)*rng.uniform(.65, 1.4)
            hair_dz = (.0025-.002*u)*rng.uniform(.6, 1.3)
            for t in (0, .5, 1):
                px = x+t*hair_dx
                pz = z+t*hair_dz
                p = skin_hit(px, pz)
                if p is None:
                    p = root.copy()
                p.y -= .00010+.00020*math.sin(t*math.pi)
                points.append(p)
            strands.append(points)
        _curve('Brow_fibers_'+side, strands, hair, .000026)
        stats['brow_'+side] = len(strands)
        eye = bpy.data.objects['Eye_'+side].evaluated_get(deps)
        eye_mesh = eye.to_mesh()
        eye_mesh.calc_loop_triangles()
        points = [eye.matrix_world @ vertex.co for vertex in eye_mesh.vertices]
        opaque_faces = [triangle.vertices[:] for triangle in eye_mesh.loop_triangles if triangle.material_index != 3]
        # Fit to the visible opaque eye aperture. The transparent corneal shell
        # can project over lid skin and is not a valid lash-root silhouette.
        aperture = BVHTree.FromPolygons(points, opaque_faces, all_triangles=True)
        eye.to_mesh_clear()

        def opening(x, z):
            root = skin_hit(x, z)
            point, normal, face, distance = aperture.ray_cast(Vector((x, -.20, z)), Vector((0, 1, 0)))
            if point is None:
                return False
            return root is None or point.y < root.y-.00002

        upper, lower = [], []
        center = eye.matrix_world.translation.x
        for x in np.linspace(center-.019, center+.019, 100):
            zs = np.linspace(-.013, .014, 54)
            opened = np.array([opening(x, z) for z in zs])
            ids = np.flatnonzero(opened)
            if not len(ids) or ids[0] == 0 or ids[-1] == len(zs)-1:
                continue
            for output, a, b in [(lower, zs[ids[0]-1], zs[ids[0]]), (upper, zs[ids[-1]], zs[ids[-1]+1])]:
                for iteration in range(8):
                    mid = (a+b)/2
                    if opening(x, a) == opening(x, mid):
                        a = mid
                    else:
                        b = mid
                closed = a if not opening(x, a) else b
                root = skin_hit(x, closed)
                if root is not None:
                    root.y -= .00007
                    output.append(root)
        for upper_lid, line in [(True, upper), (False, lower)]:
            if len(line) < 8:
                continue
            label = 'upper' if upper_lid else 'lower'
            if not upper_lid:
                _curve('Tear_meniscus_'+side, [line], wet, .00012)
            strands = []
            for index, root in enumerate(line):
                if not upper_lid and index % 2:
                    continue
                u = index/(len(line)-1)
                taper = math.sin(math.pi*u)**.4
                length = rng.uniform(.0026, .0042) if upper_lid else rng.uniform(.0009, .0019)
                length *= taper
                horizontal = sign*(u-.35)*.0014
                vertical = length*(.65 if upper_lid else -.6)
                strand = []
                for t in (0, .33, .66, 1):
                    point = root+Vector((horizontal*t, -length*1.2*t, vertical*t*t))
                    skin = skin_hit(point.x, point.z)
                    if skin is not None:
                        point.y = min(point.y, skin.y-.00010-.00025*math.sin(t*math.pi))
                    strand.append(point)
                strands.append(strand)
            _curve('Lashes_'+label+'_'+side, strands, hair, .000032 if upper_lid else .000020)
            stats['lashes_'+label+'_'+side] = len(strands)
    bpy.context.scene['static_appearance_counts'] = str(stats)
    return stats
