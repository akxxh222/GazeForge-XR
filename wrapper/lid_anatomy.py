"""Static eyelid anatomy refinement on native GNM geometry and UVs.

Original lid-profile sculpt, waterline, caruncle and clustered fine lashes.
This does not implement the later deformation-aware blink/gaze-follow rig.
"""
import math
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from .appearance import _curve,_material,_strand_material


def _roots(name):
    obj=bpy.data.objects[name]
    data=obj.data
    points=np.empty(len(data.points)*3,np.float32)
    data.attributes['position'].data.foreach_get('vector',points)
    points=points.reshape(-1,3)
    indices=np.array([c.first_point_index for c in data.curves])
    return np.array([obj.matrix_world@Vector(p) for p in points[indices]])


def refine():
    head=bpy.data.objects['GNM_skin']
    source={side:{lid:_roots('Lashes_'+lid+'_'+side) for lid in ('upper','lower')} for side in ('L','R')}
    if head.data.shape_keys is None:head.shape_key_add(name='Basis')
    sculpt=head.shape_key_add(name='Lids | margin roll and tarsal fold')
    changed=[]
    for i,v in enumerate(head.data.vertices):
        x,y,z=v.co
        if y>.015 or not -.022<z<.022:continue
        delta=0
        for side in ('L','R'):
            upper,lower=source[side]['upper'],source[side]['lower']
            low=max(upper[0,0],lower[0,0])
            high=min(upper[-1,0],lower[-1,0])
            if not low<x<high:continue
            u=(x-low)/(high-low)
            taper=math.sin(math.pi*u)**.65
            top=float(np.interp(x,upper[:,0],upper[:,2]))
            bottom=float(np.interp(x,lower[:,0],lower[:,2]))
            d=z-top
            if d>-.0003:
                fold=.0033+.0020*math.sin(math.pi*u)
                delta+=taper*(-.00028*math.exp(-(d/.00075)**2)
                    -.00028*math.exp(-((d-.0014)/.0015)**2)
                    -.00065*math.exp(-((d-(fold-.0012))/.0011)**2)
                    +.00045*math.exp(-((d-fold)/.00085)**2))
            d=bottom-z
            if d>-.0003:
                delta+=taper*(-.00018*math.exp(-(d/.00060)**2)
                    -.00016*math.exp(-((d-.0017)/.0015)**2)
                    +.00010*math.exp(-((d-.0048)/.0016)**2))
        sculpt.data[i].co.y+=delta
        if abs(delta)>1e-6:changed.append(i)
    sculpt.value=1
    sculpt.slider_min=0
    sculpt.slider_max=1
    bpy.context.view_layer.update()
    head['lid_anatomy']='Native-Basis-preserving shape key: subtle margin roll, upper tarsal hood/crease and lower lid contour. Static only.'

    # Fit the waterline and new lash roots to the deformed skin, rather than
    # leaving attachments at their previous positions after the sculpt.
    surface=head.evaluated_get(bpy.context.evaluated_depsgraph_get())
    def hit(x,z):
        ok,p,n,f=surface.ray_cast(Vector((x,-.20,z)),Vector((0,1,0)))
        return p if ok else None
    wet=_material('Tear film | thin moist waterline',(.70,.62,.56),.085)
    bs=wet.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Transmission Weight'].default_value=.90
    bs.inputs['IOR'].default_value=1.333
    tissue=_material('Lid mucosa | restrained pink tissue',(.45,.235,.18),.30)
    bs=tissue.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Subsurface Weight'].default_value=.20
    bs.inputs['Subsurface Scale'].default_value=.00045
    bs.inputs['Specular IOR Level'].default_value=.28
    lashmat=_strand_material('Lash bundles | natural dark fibers',.94,.12,.46)
    rng=np.random.default_rng(582117)
    stats={'sculpted_native_vertices':len(changed),'max_sculpt_offset_m':max(abs(sculpt.data[i].co.y-head.data.vertices[i].co.y) for i in changed)}
    for side in ('L','R'):
        for lid in ('upper','lower'):
            old=bpy.data.objects['Lashes_'+lid+'_'+side]
            old.hide_render=True
            old.hide_set(True)
        old=bpy.data.objects.get('Tear_meniscus_'+side)
        if old:
            old.hide_render=True
            old.hide_set(True)
        lines={}
        for lid in ('upper','lower'):
            line=source[side][lid].copy()
            sign=1 if lid=='upper' else -1
            for i,p in enumerate(line):
                # Step just onto lid skin to get a stable front-surface root.
                q=hit(float(p[0]),float(p[2]+sign*.00015))
                if q is not None and abs(q.y-p[1])<.002:
                    line[i]=q+Vector((0,-.00005,0))
            lines[lid]=line
            if lid=='lower':
                lineobj=_curve('Lid_waterline_'+side,[[Vector(p)+Vector((0,.00002,0)) for p in line]],tissue,.000035)
                lineobj['anatomy']='Thin pigmented mucosal margin on the native lower lid'
                tear=_curve('Lid_tear_film_'+side,[[Vector(p)+Vector((0,-.000030,.000030)) for p in line]],wet,.000035)
                tear['anatomy']='Fine tear-film meniscus; no opaque white strip'
            strands=[]
            clusters=24 if lid=='upper' else 14
            for c in range(clusters):
                center=(c+rng.uniform(.15,.85))/clusters
                count=int(rng.integers(3,5)) if lid=='upper' else int(rng.integers(1,3))
                length=rng.uniform(.0032,.0049) if lid=='upper' else rng.uniform(.0011,.0020)
                length*=.45+.55*math.sin(math.pi*center)**.55
                fan=(center-.5)*.0038+rng.normal(0,.00028)
                curl=rng.uniform(.26,.50)
                for child in range(count):
                    u=float(np.clip(center+rng.normal(0,.0045),.006,.994))
                    tindex=u*(len(line)-1)
                    a=min(int(tindex),len(line)-2)
                    root=Vector(line[a]*(1-(tindex-a))+line[a+1]*(tindex-a))
                    strand=[]
                    for t in np.linspace(0,1,10):
                        childspread=(u-center)*.016*math.sin(math.pi*t)
                        dz=length*(.06*t+curl*t*t) if lid=='upper' else -length*(.25*t+.32*t*t)
                        strand.append(root+Vector((fan*t+childspread,-length*(.95*t-.26*t*t),dz)))
                    strands.append(strand)
            lashes=_curve('Lid_lashes_'+lid+'_'+side,strands,lashmat,.000027 if lid=='upper' else .000016)
            lashes['anatomy']='Irregular small lash bundles, fine tapered fibers, short curl and varied lengths; static attachments'
            stats['lashes_'+lid+'_'+side]=len(strands)
        # Lacrimal caruncle sits at the nasal canthus, within the lid opening.
        upper,lower=lines['upper'],lines['lower']
        x=min(upper[:,0].max(),lower[:,0].max())-.0014 if side=='R' else max(upper[:,0].min(),lower[:,0].min())+.0014
        top=np.array([x,np.interp(x,upper[:,0],upper[:,1]),np.interp(x,upper[:,0],upper[:,2])])
        bottom=np.array([x,np.interp(x,lower[:,0],lower[:,1]),np.interp(x,lower[:,0],lower[:,2])])
        center=(top+bottom)/2
        center[1]-=.00050
        height=max(.00020,min(.00062,abs(top[2]-bottom[2])*.27))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=center)
        caruncle=bpy.context.object
        caruncle.name='Lid_caruncle_'+side
        caruncle.scale=(.00085,.00032,height)
        caruncle.data.materials.append(tissue)
        for p in caruncle.data.polygons:p.use_smooth=True
        caruncle['anatomy']='Small moist lacrimal caruncle at nasal canthus'
        for name in ['Lid_waterline_'+side,'Lid_tear_film_'+side,'Lid_lashes_upper_'+side,'Lid_lashes_lower_'+side,'Lid_caruncle_'+side]:
            obj=bpy.data.objects[name]
            world=obj.matrix_world.copy()
            obj.parent=head
            obj.matrix_world=world
    bpy.context.view_layer.update()
    return stats
