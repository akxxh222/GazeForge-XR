"""Author native gaze-follow/brow keys and bind details, preserving blink parent."""
import hashlib
import json
import math
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from wrapper import eyes,lids,surface_bindings
from wrapper.lid_anatomy import _roots
from build_gnm_blink_prototype import surface


def add_key(head,name,delta):
    key=head.shape_key_add(name=name)
    base=np.array([p.co[:] for p in head.data.vertices],np.float32)
    key.data.foreach_set('co',(base+delta).ravel())
    key.slider_min=0
    key.slider_max=1
    return key


def follow_delta(head,side,sign):
    base=np.array([p.co[:] for p in head.data.shape_keys.key_blocks['Lids | margin roll and tarsal fold'].data])
    base+=np.array([p.co[:] for p in head.data.shape_keys.key_blocks['Lids | ocular clearance'].data])-np.array([v.co[:] for v in head.data.vertices])
    center=bpy.data.objects['Eye_'+side].matrix_world.translation
    upper,lower=[_roots('Lashes_'+lid+'_'+side) for lid in ('upper','lower')]
    low=max(upper[0,0],lower[0,0])
    high=min(upper[-1,0],lower[-1,0])
    result=np.zeros_like(base)
    for i,p in enumerate(base):
        x,y,z=p
        if not low<x<high or y>.005:continue
        top=float(np.interp(x,upper[:,0],upper[:,2]))
        bottom=float(np.interp(x,lower[:,0],lower[:,2]))
        middle=(top+bottom)/2
        margin=top if z>=middle else bottom
        u=(x-low)/(high-low)
        taper=math.sin(math.pi*u)**1.2
        weight=taper*math.exp(-((z-margin)/.008)**2)
        strength=.65 if z>=middle else .35
        angle=-sign*math.atan2(.05,.35)*strength*weight
        rotated=center+Matrix.Rotation(angle,3,'X')@(Vector(p)-center)
        result[i]=rotated-Vector(p)
    return result


def clearance_field(point,profiles):
    x,y,z=point
    if y>.005:return 0.
    result=0.
    for upper,lower in profiles.values():
        low=max(upper[0,0],lower[0,0])
        high=min(upper[-1,0],lower[-1,0])
        if not low<x<high:continue
        top=float(np.interp(x,upper[:,0],upper[:,2]))
        bottom=float(np.interp(x,lower[:,0],lower[:,2]))
        u=(x-low)/(high-low)
        taper=math.sin(math.pi*u)**.35
        result=max(result,.00040*taper*max(math.exp(-((z-top)/.004)**2),math.exp(-((z-bottom)/.004)**2)))
    return result


def add_clearance(head):
    profiles={side:tuple(_roots('Lashes_'+lid+'_'+side) for lid in ('upper','lower')) for side in ('L','R')}
    delta=np.zeros((len(head.data.vertices),3),np.float32)
    for i,vertex in enumerate(head.data.vertices):delta[i,1]=-clearance_field(vertex.co,profiles)
    add_key(head,'Lids | ocular clearance',delta).value=1
    # Refit small attachments by the same smooth depth field before capturing
    # the new rest surface. Original native Basis and UVs remain unchanged.
    for obj in bpy.context.scene.objects:
        if obj.hide_render or not obj.name.startswith(('Lid_lashes_','Brow_fibers_','Lid_waterline_','Lid_tear_film_','Lid_caruncle_')):continue
        if obj.type=='CURVES':
            for curve in obj.data.curves:
                start=curve.first_point_index
                shift=clearance_field(obj.matrix_world@obj.data.attributes['position'].data[start].vector,profiles)
                for i in range(start,start+curve.points_length):obj.data.attributes['position'].data[i].vector.y-=shift
        elif obj.type=='CURVE':
            for spline in obj.data.splines:
                for point in spline.points:
                    point.co.y-=clearance_field(obj.matrix_world@Vector(point.co[:3]),profiles)
        elif obj.type=='MESH':obj.location.y-=clearance_field(obj.matrix_world.translation,profiles)
    head.data.update()
    bpy.context.view_layer.update()


def brow_delta(head,side):
    center=bpy.data.objects['Eye_'+side].matrix_world.translation
    result=np.zeros((len(head.data.vertices),3),np.float32)
    for i,vertex in enumerate(head.data.vertices):
        x,y,z=vertex.co
        if y>.005:continue
        w=math.exp(-((x-center.x)/.014)**4-((z-.022)/.008)**2)
        result[i]=(0,-.00018*w,.0015*w)
    return result


def follow_driver(key,head,side,sign):
    driver=key.driver_add('value').driver
    driver.type='SCRIPTED'
    for name,id_type,owner,path in [('z','OBJECT',bpy.data.objects['FixationTarget'],'location[2]'),
                                     ('blink','KEY',head.data.shape_keys,f'key_blocks["Blink.{side}"].value')]:
        variable=driver.variables.new()
        variable.name=name
        variable.type='SINGLE_PROP'
        variable.targets[0].id_type=id_type
        variable.targets[0].id=owner
        variable.targets[0].data_path=path
    driver.expression=f'max(0,min(1,{sign}*z/0.05))*(1-blink)'


def clamp_action(owner,name):
    action=owner.animation_data.action
    action.name=name
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for point in curve.keyframe_points:
                        point.handle_left_type='AUTO_CLAMPED'
                        point.handle_right_type='AUTO_CLAMPED'


def main():
    parent=ROOT/'work/milestone3/IRISX_BLINK_PROTOTYPE.blend'
    bpy.ops.wm.open_mainfile(filepath=str(parent),use_scripts=False)
    old=bpy.data.objects['GNM_skin']
    blink={s:np.array([p.co[:] for p in old.data.shape_keys.key_blocks['Blink.'+s].data],np.float32)
             -np.array([v.co[:] for v in old.data.vertices],np.float32) for s in ('L','R')}
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'work/review/lids/IRISX_LIDS_REVIEW.blend'),use_scripts=False)
    head=bpy.data.objects['GNM_skin']
    add_clearance(head)
    names=[]
    for side in ('L','R'):
        name='Blink.'+side
        add_key(head,name,blink[side])
        names.append(name)
    for side in ('L','R'):
        for direction,sign in [('Up',1),('Down',-1)]:
            name=f'LidFollow.{direction}.{side}'
            add_key(head,name,follow_delta(head,side,sign))
            names.append(name)
        name='Brow.Raise.'+side
        add_key(head,name,brow_delta(head,side))
        names.append(name)
    for name in names:head.data.shape_keys.key_blocks[name].value=0
    # Tag coordinate writes before the first evaluated snapshot. Without this,
    # Blender can retain a stale subdivision result while keys are authored.
    head.data.update()
    bpy.context.view_layer.update()
    rest,triangles,polygons=surface(head)
    print("REST_KEYS",[(n,head.data.shape_keys.key_blocks[n].value) for n in names],flush=True)
    poses={}
    for name in names:
        for other in names:head.data.shape_keys.key_blocks[other].value=0
        key=head.data.shape_keys.key_blocks[name]
        key.value=1
        head.data.update()
        bpy.context.view_layer.update()
        pose,_,faces=surface(head)
        if not np.array_equal(polygons,faces):raise ValueError('Native surface connectivity changed')
        poses[name]=pose
        print('CAPTURE',name,float(np.abs(pose-rest).max()),[(n,head.data.shape_keys.key_blocks[n].value) for n in names],flush=True)
        key.value=0
    bpy.context.view_layer.update()
    tree=BVHTree.FromPolygons(rest.tolist(),triangles.tolist(),all_triangles=True)
    bound=[]
    for obj in list(bpy.context.scene.objects):
        if obj.hide_render:continue
        if obj.type=='CURVES' and obj.name.startswith(('Lid_lashes_','Brow_fibers_')):
            bound.append(surface_bindings.bind_curves(obj,head,tree,triangles,rest,poses).name)
        elif obj.name.startswith(('Lid_waterline_','Lid_tear_film_','Lid_caruncle_')):
            bound.append(surface_bindings.bind_mesh(obj,head,tree,triangles,rest,poses).name)
    for side in ('L','R'):
        for direction,sign in [('Up',1),('Down',-1)]:
            follow_driver(head.data.shape_keys.key_blocks[f'LidFollow.{direction}.{side}'],head,side,sign)
    scene=bpy.context.scene
    rig=bpy.data.objects['GazeRig']
    target=bpy.data.objects['FixationTarget']
    for side in ('L','R'):
        bone=rig.pose.bones['eye.'+side]
        bone.rotation_mode='QUATERNION'
        aim=bone.constraints.new('TRACK_TO')
        aim.name='Metric fixation | exact between keyframes'
        aim.target=target
        aim.track_axis='TRACK_Y'
        aim.up_axis='UP_Z'
        aim.use_target_z=True
    # Six-second review action: scan left/right/up/down, blink in vertical poses.
    timeline=[(1,0,0,1,0),(18,-1,0,1,0),(36,1,0,1,0),(54,0,1,1,.35),
              (57,0,1,1,.35),(60,0,1,0,.35),(65,0,1,1,.35),(84,0,0,1,0),
              (102,0,-1,1,0),(105,0,-1,1,0),(108,0,-1,0,0),(114,0,-1,1,0),
              (132,0,0,1,0),(144,0,0,1,0)]
    for frame,h,v,opening,brow in timeline:
        eyes.move(h,v)
        lids.set_opening(opening)
        target.keyframe_insert(data_path='location',frame=frame)
        for side in ('L','R'):
            rig.pose.bones['eye.'+side].keyframe_insert(data_path='rotation_quaternion',frame=frame)
            keys=head.data.shape_keys.key_blocks
            keys['Blink.'+side].keyframe_insert(data_path='value',frame=frame)
            keys['Brow.Raise.'+side].value=brow
            keys['Brow.Raise.'+side].keyframe_insert(data_path='value',frame=frame)
    clamp_action(head.data.shape_keys,'IrisX | lids and brows review')
    clamp_action(rig,'IrisX | binocular gaze review')
    clamp_action(target,'IrisX | fixation review')
    scene.render.fps=24
    scene.frame_start=1
    scene.frame_end=144
    scene.frame_set(1)
    scene.camera=bpy.data.objects['RenderCamera']
    scene['milestone3_status']='Gaze-follow/brow prototype: sampled combined-gaze and collision review required.'
    scene['lid_follow_design']='Native shape-key endpoint rotations about physical eye centers, upper gain 0.65/lower 0.35, tapered at canthi; follow attenuates by 1-blink.'
    folder=ROOT/'work/milestone3/gaze_lids'
    folder.mkdir(exist_ok=True)
    path=folder/'IRISX_GAZE_LIDS_RIG.blend'
    note=bpy.data.texts.new('IRISX_GAZE_LIDS_RIG.txt')
    note.write('Original native-UV gaze-follow and brow authoring, retaining GNM Apache-2.0. Static parent and public-asset credits are inherited. Three editable actions: target, eye rotations, lids/brows. No Python handlers or custom scripted callbacks. Sampled clearance and visual acceptance remain required.\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    receipt={'scene':str(path.relative_to(ROOT)),'scene_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
             'parent_sha256':hashlib.sha256(parent.read_bytes()).hexdigest(),'shape_keys':names,'bound_objects':bound,
             'timeline':timeline,'authoring_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'status':'Authored, awaiting combined-gaze geometry/render validation.'}
    (folder/'rig.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('GAZE_LID_RIG_SAVED',json.dumps(receipt),flush=True)


if __name__=='__main__':main()
