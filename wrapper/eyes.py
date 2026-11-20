"""Deterministic binocular control. Execute inside Blender's Python runtime.

World: X=image right, Y=behind subject, Z=up. Face forward is -Y.
Eye mesh local +Y is its optical axis. World Euler rotations use XYZ radians.
"""
import math
import numbers
from pathlib import Path
import bpy
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(__file__).resolve().parents[1]
_input=(0.,0.)

def _scene():
    scene=bpy.context.scene
    if 'GazeRig' not in bpy.data.objects: raise RuntimeError('Load GazeForge scene.blend first')
    return scene,bpy.data.objects['GazeRig']

def midpoint():
    _,rig=_scene()
    return sum((rig.matrix_world @ rig.data.bones['eye.'+s].head_local for s in ['L','R']),Vector())/2

def move(h:float,v:float)->None:
    global _input
    for name,x in [('h',h),('v',v)]:
        if isinstance(x,bool) or not isinstance(x,numbers.Real): raise TypeError(name+' must be a real number')
        if not math.isfinite(x) or not -1<=x<=1: raise ValueError(name+' must be finite and in [-1,1]')
    scene,rig=_scene()
    # Manual gaze takes ownership of the eye controllers. A render evaluates
    # animation again, which otherwise replaces the requested target with the
    # saved timeline pose. use_action() reattaches the selected timeline bundle;
    # expressions.manual() also restores its captured actions on context exit.
    for owner in (rig,bpy.data.objects['FixationTarget']):
        if owner.animation_data and owner.animation_data.action:
            owner.animation_data.action=None
    # The target occupies a square +/- 5 cm in the frontal plane at 35 cm.
    # Circular samples lie on a 5 cm radius circle in that plane.
    target=midpoint()+Vector((float(h)*.05,-.35,float(v)*.05))
    bpy.data.objects['FixationTarget'].location=target
    for side in ['L','R']:
        bone=rig.data.bones['eye.'+side]
        center=rig.matrix_world @ bone.head_local
        direction=(target-center).normalized()
        # +Y tracking, +Z up fixes the otherwise free optical-axis roll.
        world=direction.to_track_quat('Y','Z').to_matrix().to_4x4()
        world.translation=center
        rig.pose.bones[bone.name].matrix=rig.matrix_world.inverted() @ world
    _input=(float(h),float(v))
    bpy.context.view_layer.update()

def reset()->None: move(0.,0.)

def camera_matrix():
    """3x4 world-to-pixel projective matrix, continuous edge-origin pixels."""
    scene,_=_scene(); cam=scene.camera
    w=scene.render.resolution_x*scene.render.resolution_percentage/100
    h=scene.render.resolution_y*scene.render.resolution_percentage/100
    proj=cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=int(w),y=int(h),scale_x=scene.render.pixel_aspect_x,scale_y=scene.render.pixel_aspect_y)
    clip=proj @ cam.matrix_world.inverted()
    rows=[(clip[0]+clip[3])*(w/2),(-clip[1]+clip[3])*(h/2),clip[3]]
    return [[float(x) for x in row] for row in rows]

def state(frame=0,theta=0.):
    scene,_=_scene(); result={'frame':frame,'theta':float(theta),'input':{'h':_input[0],'v':_input[1]},'camera_matrix':camera_matrix(),'camera_matrix_convention':'3x4: [u*w,v*w,w]=P@[X,Y,Z,1]; u right, v down; continuous edge-origin pixels','eye_rotation_convention':'world XYZ Euler radians, mesh local +Y optical axis','fixation_world_m':list(bpy.data.objects['FixationTarget'].location)}
    w=scene.render.resolution_x*scene.render.resolution_percentage/100
    h=scene.render.resolution_y*scene.render.resolution_percentage/100
    for side in ['L','R']:
        eye=bpy.data.objects['Eye_'+side]
        local_point=eye.get('pupil_center_local',(0.,float(eye['pupil_radius_m']),0.))
        point=eye.matrix_world @ Vector(local_point)
        p=world_to_camera_view(scene,scene.camera,point)
        result['eye_rotation_'+side]=list(eye.matrix_world.to_euler('XYZ'))
        result['eye_quaternion_wxyz_'+side]=list(eye.matrix_world.to_quaternion())
        result['pupil_center_3D_'+side]=list(point)
        result['pupil_center_2D_'+side]=[p.x*w,(1-p.y)*h]
        result['eye_center_3D_'+side]=list(eye.matrix_world.translation)
    return result

def render(output_path:str|None=None):
    scene,_=_scene()
    path=Path(output_path) if output_path is not None else ROOT/'tests'/'preview.png'
    if not path.is_absolute(): path=ROOT/path
    path.parent.mkdir(parents=True,exist_ok=True)
    scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True)
    return state()
