"""Manual pose control for the native gaze/lid/brow rig, with timeline restore."""
from contextlib import contextmanager
import math
import numbers
import json
import bpy
from . import eyes,lids


def _fraction(name,value):
    if isinstance(value,bool) or not isinstance(value,numbers.Real):raise TypeError(name+' must be real')
    if not math.isfinite(value) or not 0<=value<=1:raise ValueError(name+' must be finite in [0,1]')
    return float(value)


def set_brows(left=0.,right=None):
    if right is None:right=left
    left,right=_fraction('left brow',left),_fraction('right brow',right)
    keys=bpy.data.objects['GNM_skin'].data.shape_keys.key_blocks
    keys['Brow.Raise.L'].value=left
    keys['Brow.Raise.R'].value=right
    bpy.context.view_layer.update()


def reset():
    eyes.reset()
    lids.reset()
    set_brows(0,0)
    set_pupil_constriction(.7)


def set_pupil_constriction(value=.7):
    value=_fraction('pupil constriction',value)
    keys=[bpy.data.objects['Eye_'+s].data.shape_keys.key_blocks['Pupil | daylight constriction'] for s in ('L','R')]
    for key in keys:key.value=value
    bpy.context.view_layer.update()


def use_action(mode='generate_motion'):
    """Select an authored bundle without a playback callback or GUI state."""
    scene=bpy.context.scene
    library=json.loads(scene['expression_actions'])
    if mode not in library:raise ValueError('mode must be left, right or generate_motion')
    owners=[bpy.data.objects['GNM_skin'].data.shape_keys,bpy.data.objects['GazeRig'],bpy.data.objects['FixationTarget']]
    actions=[bpy.data.actions[name] for name in library[mode]]
    for owner,action in zip(owners,actions):owner.animation_data_create().action=action
    scene.frame_start=1
    scene.frame_end=144
    scene.render.fps=24
    scene.frame_set(1)


def state():
    result=eyes.state()
    delta=bpy.data.objects['FixationTarget'].location-eyes.midpoint()
    result['input']={'h':float(delta.x/.05),'v':float(delta.z/.05)}
    result.update(lids.state())
    keys=bpy.data.objects['GNM_skin'].data.shape_keys.key_blocks
    result['brow_raise']={s:float(keys['Brow.Raise.'+s].value) for s in ('L','R')}
    result['pupil_constriction']={s:float(bpy.data.objects['Eye_'+s].data.shape_keys.key_blocks['Pupil | daylight constriction'].value) for s in ('L','R')}
    result['lid_follow']={f'{direction}_{side}':float(keys[f'LidFollow.{direction}.{side}'].value)
                          for side in ('L','R') for direction in ('Up','Down')}
    return result


@contextmanager
def manual():
    """Temporarily detach this rig's actions, keeping gaze/attachment drivers.

    Use around manual poses and renders. Actions and the timeline pose are
    restored even if a caller raises, avoiding hidden render-time overrides.
    """
    scene=bpy.context.scene
    frame,subframe=scene.frame_current,scene.frame_subframe
    owners=[bpy.data.objects['GNM_skin'].data.shape_keys,bpy.data.objects['GazeRig'],bpy.data.objects['FixationTarget']]
    actions=[owner.animation_data.action if owner.animation_data else None for owner in owners]
    try:
        for owner in owners:
            if owner.animation_data:owner.animation_data.action=None
        yield
    finally:
        for owner,action in zip(owners,actions):
            if action is not None:owner.animation_data_create().action=action
        scene.frame_set(frame,subframe=subframe)
