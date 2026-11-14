"""Measure eye surface visible through head along frontal rays, for blink tuning."""
from pathlib import Path
import json
import sys
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from wrapper import eyes


def eye_tree(side):
    eye=bpy.data.objects['Eye_'+side]
    obj=eye.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=obj.to_mesh()
    tree=BVHTree.FromPolygons([obj.matrix_world@v.co for v in mesh.vertices],[list(p.vertices) for p in mesh.polygons])
    obj.to_mesh_clear()
    return tree


def visible_grid(side,columns=61,rows=61):
    head=BVHTree.FromObject(bpy.data.objects['GNM_skin'],bpy.context.evaluated_depsgraph_get())
    eye=eye_tree(side)
    center=bpy.data.objects['Eye_'+side].matrix_world.translation
    visible=[]
    for x in np.linspace(center.x-.016,center.x+.016,columns):
        for z in np.linspace(center.z-.012,center.z+.012,rows):
            start=Vector((x,-.2,z))
            eh=eye.ray_cast(start,Vector((0,1,0)))
            hh=head.ray_cast(start,Vector((0,1,0)))
            if eh[0] is not None and (hh[0] is None or eh[3]+1e-6<hh[3]):visible.append([float(x),float(z)])
    return {'visible_eye_rays':len(visible),'grid':[columns,rows],'visible_xz_m':visible}


def main():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/milestone3/IRISX_BLINK_PROTOTYPE.blend'),use_scripts=False)
    eyes.reset()
    keys=bpy.data.objects['GNM_skin'].data.shape_keys
    keys.animation_data.action=None
    result=[]
    for scale in [0,.5,1,1.06,1.12,1.18,1.24]:
        for side in ('L','R'):
            keys.key_blocks['Blink.'+side].slider_max=1.5
            keys.key_blocks['Blink.'+side].value=scale
        bpy.context.view_layer.update()
        row={'scale':scale,**{s:visible_grid(s) for s in ('L','R')}}
        result.append(row)
        print('CLOSURE_PROBE',scale,{s:row[s]['visible_eye_rays'] for s in ('L','R')},flush=True)
    (ROOT/'work/milestone3/closure_probe.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
