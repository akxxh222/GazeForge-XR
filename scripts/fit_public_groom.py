"""Fit frozen Daniel Bystedt demo grooms to GNM for local asset review.

Source credit: Daniel Bystedt, Blender Hair Styles demo, CC BY-SA (the
published source notice does not specify a version). Imported data is not
MIT/CC0. Target GNM geometry/UVs remain untouched.
"""
import argparse
import json
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from render_device import configure
from wrapper import eyes
from wrapper.appearance import _strand_material

parser=argparse.ArgumentParser()
parser.add_argument('--style',choices=['cyberpunk','curly'],default='cyberpunk')
parser.add_argument('--render-fit', action='store_true')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/gnm/scene_look_01_realism.blend'),use_scripts=False)
scene=bpy.context.scene
configure()
scene.cycles.samples=128
head=bpy.data.objects['GNM_skin']
old=bpy.data.objects.get('Scalp_swept_back_hair')
old.hide_render=True
old.hide_set(True)
deps=bpy.context.evaluated_depsgraph_get()
bvh=BVHTree.FromObject(head,deps)
center=Vector((0,.065,.026))

with np.load(ROOT/'assets/gnm/gnm_head.npz',allow_pickle=False) as source:
    ear_mask=source['vertex_groups'][source['vertex_group_names'].tolist().index('ears')]
native_ids=[a.value for a in head.data.attributes['gnm_vertex_id'].data]
nearest=KDTree(len(head.data.vertices))
for i,v in enumerate(head.data.vertices):
    nearest.insert(v.co,i)
nearest.balance()

def scalp(point):
    direction=(point-center).normalized()
    return bvh.ray_cast(center+direction*.30,-direction,.32)

data=np.load(ROOT/'work/public_candidates'/(args.style+'_hair_evaluated.npz'))
source_points=(data['positions']-np.array([0,-1.3379756212,15.301123619]))*.1
strands=[]
rng=np.random.default_rng(4157)
for start,size in zip(data['starts'],data['sizes']):
    line=source_points[start:start+size]
    root,normal,face,distance=scalp(Vector(line[0]))
    if root is None:
        continue
    _,index,_=nearest.find(root)
    if ear_mask[native_ids[index]]>.1:
        continue
    distances=np.r_[0,np.linalg.norm(np.diff(line,axis=0),axis=1).cumsum()]
    if distances[-1]<.0003:
        continue
    # Short adult cut: retain the authored trajectory up to a length limit,
    # rather than scaling long locks into identical parallel arcs.
    max_length=.070 if root.z>.060 else .025 if root.z>.015 else .012
    if root.y<.015:
        max_length=min(max_length,.047)
    length=min(distances[-1],max_length*rng.uniform(.82,1.10))
    samples=np.linspace(0,length,16)
    line=np.column_stack([np.interp(samples,distances,line[:,a]) for a in range(3)])
    offset=np.array(root)-line[0]
    for child in range(2 if args.style=='curly' else 1):
        points=line+offset
        points[0]=root+normal*.00003
        if child:
            points+=rng.normal(0,.00012,(1,3))*np.linspace(0,1,16)[:,None]
        for i in range(1,len(points)):
            point=Vector(points[i])
            close,n,face,distance=bvh.find_nearest(point)
            signed=(point-close).dot(n)
            if signed<.00008:
                points[i]=point+n*(.00008-signed)
        strands.append(points)

curve=bpy.data.hair_curves.new('Bystedt adapted '+args.style)
curve.add_curves([16]*len(strands))
curve.attributes['position'].data.foreach_set('vector',np.concatenate(strands).astype(np.float32).ravel())
radii=np.tile(.000043*np.maximum(.035,1-.965*np.linspace(0,1,16))**.65,len(strands)).astype(np.float32)
curve.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',radii)
hair=bpy.data.objects.new('Public_groom_'+args.style,curve)
scene.collection.objects.link(hair)
hair.parent=head
material=_strand_material('Public groom | modern Cycles melanin',.92,.16,.39)
shader=material.node_tree.nodes.get('Principled Hair BSDF')
shader.model='CHIANG'
shader.inputs['Coat'].default_value=.05
shader.inputs['Radial Roughness'].default_value=.44
curve.materials.append(material)
hair['source_credit']='Daniel Bystedt / Blender Hair Styles demo / CC BY-SA'
hair['source_url']='https://www.blender.org/download/demo-files/'
hair['modifications']='Frozen evaluated curves, metric alignment, radial root refit to GNM, short-cut trimming, added fine child strands for curly style, collision correction, tapered radius and replacement Cycles melanin shader.'
hair['native_target_uvs_unchanged']=True
hair['strand_count']=len(strands)
eyes.reset()
scene.camera=bpy.data.objects['RenderCamera']
folder=ROOT/'work/public_candidates'/args.style
folder.mkdir(exist_ok=True)
print('PUBLIC_HAIR_READY',args.style,len(strands),flush=True)
if args.render_fit:
    eyes.render(folder/'front.png')
    side=bpy.data.objects['Review_side_left']
    scene.camera=side
    eyes.render(folder/'side.png')
scene.camera=bpy.data.objects['RenderCamera']
scene['public_asset_review']='Local source-adaptation test; final visual/optics acceptance pending.'
bpy.ops.wm.save_as_mainfile(filepath=str(folder/'candidate.blend'))
(folder/'source.json').write_text(json.dumps({'author':'Daniel Bystedt','license':'CC BY-SA (source does not state version)',
    'source':'https://download.blender.org/demo/geometry-nodes/hair_nodes-female_hair_styles.blend',
    'source_sha256':'1ad6202095c1793678fee7d69a7e9f8b5fdb6e5c293d300eb1062d2d437e8d48',
    'modifications':hair['modifications'],'strand_count':len(strands)},indent=2)+'\n')
print('PUBLIC_HAIR_REVIEW_SAVED',folder,flush=True)
