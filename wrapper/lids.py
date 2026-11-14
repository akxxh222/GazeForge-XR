"""Deterministic opening control for the native GNM blink prototype.

The saved action controls values when the timeline evaluates. For manual
render overrides, detach that action in an unsaved working copy first.
"""
import math
import numbers
import bpy


def set_opening(left=1.0,right=None):
    if right is None:right=left
    for name,value in [('left',left),('right',right)]:
        if isinstance(value,bool) or not isinstance(value,numbers.Real):raise TypeError(name+' must be a real opening fraction')
        if not math.isfinite(value) or not 0<=value<=1:raise ValueError(name+' must be finite and in [0,1]')
    keys=bpy.data.objects['GNM_skin'].data.shape_keys.key_blocks
    keys['Blink.L'].value=1-float(left)
    keys['Blink.R'].value=1-float(right)
    bpy.context.view_layer.update()


def reset():set_opening(1,1)


def state():
    keys=bpy.data.objects['GNM_skin'].data.shape_keys.key_blocks
    return {'opening_L':1-float(keys['Blink.L'].value),'opening_R':1-float(keys['Blink.R'].value)}
