"""Select a locally available Cycles GPU without persisting preferences."""
import bpy
def configure():
    prefs=bpy.context.preferences.addons['cycles'].preferences
    for backend in ['OPTIX','CUDA','HIP','ONEAPI','METAL']:
        try:
            prefs.compute_device_type=backend
            prefs.get_devices()
            gpu=[d for d in prefs.devices if d.type==backend]
            if gpu:
                for d in prefs.devices:d.use=d in gpu
                bpy.context.scene.cycles.device='GPU'
                return backend+': '+', '.join(d.name for d in gpu)
        except (TypeError,RuntimeError): pass
    bpy.context.scene.cycles.device='CPU'
    return 'CPU'
