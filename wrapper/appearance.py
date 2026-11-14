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


def _strand_material(name, melanin, redness, roughness=.4):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    shader = nodes.new('ShaderNodeBsdfHairPrincipled')
    shader.parametrization = 'MELANIN'
    shader.inputs['Melanin'].default_value = melanin
    shader.inputs['Melanin Redness'].default_value = redness
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Radial Roughness'].default_value = .32
    shader.inputs['Random Color'].default_value = .12
    shader.inputs['Random Roughness'].default_value = .10
    random = nodes.new('ShaderNodeHairInfo')
    links.new(random.outputs['Random'], shader.inputs['Random'])
    links.new(shader.outputs[0], output.inputs['Surface'])
    material['strand_shader'] = True
    return material


def _curve(name, strands, material, radius):
    if material.get('strand_shader'):
        # Native Cycles hair primitives provide strand tangents and scattering.
        # A beveled legacy curve would instead be a tubular surface mesh.
        curve = bpy.data.hair_curves.new(name)
        curve.add_curves([len(strand) for strand in strands])
        positions = np.concatenate([np.array(strand, dtype=np.float32) for strand in strands])
        curve.attributes['position'].data.foreach_set('vector', positions.ravel())
        radii = np.concatenate([radius*np.maximum(.035, 1-.965*np.linspace(0, 1, len(strand)))**.75
                                for strand in strands]).astype(np.float32)
        attribute = curve.attributes.new('radius', 'FLOAT', 'POINT')
        attribute.data.foreach_set('value', radii)
        curve.materials.append(material)
        obj = bpy.data.objects.new(name, curve)
        bpy.context.scene.collection.objects.link(obj)
        obj['appearance_stage'] = 'Milestone 2 native hair strands; deformation binding is milestone 3 work'
        obj['strand_count'] = len(strands)
        return obj
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
    melanin, redness = {'look_01':(.82, .16), 'look_02':(.92, .12), 'look_03':(.60, .20),
                        'look_04':(.15, .70), 'look_05':(.62, .22)}[texture_id]
    hair = _strand_material('Brow fibers | melanin strand shading', melanin, redness, .42)
    lashes = _strand_material('Lash fibers | melanin strand shading', .55 if texture_id == 'look_04' else .9,
                              .5 if texture_id == 'look_04' else .12, .38)
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
            count = 118 if upper_lid else 58
            for index in range(count):
                u = (index+.25+rng.uniform(0, .5))/count
                sample = u*(len(line)-1)
                start = min(int(sample), len(line)-2)
                root = line[start].lerp(line[start+1], sample-start)
                taper = math.sin(math.pi*u)**.4
                length = rng.uniform(.0040, .0058) if upper_lid else rng.uniform(.0014, .0026)
                length *= taper
                # The samples run in world-X order on both lids. Fan outward
                # from each aperture's midpoint rather than reversing one eye.
                horizontal = (u-.5)*.0038+rng.normal(0, .00018)
                curl = rng.uniform(.75, 1.05)
                strand = []
                for t in (0, .33, .66, 1):
                    vertical = length*(.12*t+curl*.8*t*t) if upper_lid else -length*(.35*t+.25*t*t)
                    point = root+Vector((horizontal*t, -length*(t-.24*t*t), vertical))
                    skin = skin_hit(point.x, point.z)
                    if skin is not None:
                        point.y = min(point.y, skin.y-.00010-.00025*math.sin(t*math.pi))
                    strand.append(point)
                strands.append(strand)
            _curve('Lashes_'+label+'_'+side, strands, lashes, .000029 if upper_lid else .000019)
            stats['lashes_'+label+'_'+side] = len(strands)
    fuzz = _strand_material('Vellus fibers | soft strand scattering', .62 if texture_id == 'look_02' else .20,
                            .18, .48)
    strands = []
    for index in range(11000):
        x, z = rng.uniform(-.078, .078), rng.uniform(-.135, .080)
        if (abs(abs(x)-.031) < .020 and -.014 < z < .013) or (abs(x) < .028 and -.085 < z < -.058):
            continue
        if (abs(x) < .020 and -.055 < z < -.019) or (.011 < abs(x) < .063 and .009 < z < .029):
            continue
        hit, root, normal, face = surface.ray_cast(Vector((x, -.20, z)), Vector((0, 1, 0)))
        if not hit or root.y > .035:
            continue
        direction = Vector((.3*np.sign(x)+rng.normal(0, .2), 0, -1))
        direction -= normal*direction.dot(normal)
        if direction.length < .1:
            continue
        direction.normalize()
        length = rng.uniform(.00020, .00055)
        strand = [root+normal*.000012+direction*(length*t)+normal*(.000045*math.sin(math.pi*t))
                  for t in (0, .5, 1)]
        strands.append(strand)
    _curve('Vellus_facial_fibers', strands, fuzz, .000005)
    stats['vellus'] = len(strands)
    # Sparse, short shaved stubble grounds the adult male portrait without a
    # painted beard mask. Keep the vermilion, nose and eyelids clear.
    stubble = _strand_material('Shaved stubble | melanin strands', .88 if texture_id != 'look_04' else .40,
                               .15 if texture_id != 'look_04' else .58, .55)
    strands = []
    for index in range(26000):
        x, z = rng.uniform(-.074, .074), rng.uniform(-.140, -.043)
        cheek_line = -.097+.049*min(1, abs(x)/.064)**.65
        moustache = .009 < abs(x) < .026 and -.064 < z < -.052
        if not moustache and z > cheek_line:
            continue
        if abs(x) < .026 and -.092 < z < -.063:
            continue
        hit, root, normal, face = surface.ray_cast(Vector((x, -.20, z)), Vector((0, 1, 0)))
        if not hit or root.y > .040 or normal.y > -.15:
            continue
        if rng.random() > (.65 if moustache else .82):
            continue
        tangent = Vector((.15*np.sign(x), 0, -1))
        tangent -= normal*tangent.dot(normal)
        tangent.normalize()
        length = rng.uniform(.00028, .00085)
        strand = [root+normal*.000018,
                  root+normal*(length*.35)+tangent*(length*.50),
                  root+normal*(length*.62)+tangent*(length*.78)]
        strands.append(strand)
    _curve('Facial_shaved_stubble', strands, stubble, .000026)
    stats['shaved_stubble'] = len(strands)
    bpy.context.scene['static_appearance_counts'] = str(stats)
    return stats
