"""Render ten actual 1024px previews after fresh scene loads for five looks."""
import hashlib
import json
from pathlib import Path
import sys
import time

import bpy
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from wrapper import expressions, submission_looks
from scripts.render_device import configure


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def signature():
    result={}
    for obj in bpy.context.scene.objects:
        if obj.get('gnm_component'):
            data=obj.data
            h=hashlib.sha256(np.array([list(v.co) for v in data.vertices],np.float32).tobytes())
            h.update(np.array([list(u.uv) for u in data.uv_layers.active.data],np.float32).tobytes())
            h.update(json.dumps([list(p.vertices) for p in data.polygons]).encode())
            result[obj.name]=h.hexdigest()
    return result


def main():
    folder=ROOT/'previews';folder.mkdir(exist_ok=True)
    receipt={'schema':'IrisX five-look render 1','scene_sha256':sha(ROOT/'scene.blend'),
             'renderer_sha256':sha(Path(__file__)),'looks':[],'checks':[],
             'visual_status':'Final texture previews; appearance limits are documented in README.md'}
    for index in range(1,6):
        name=f'look_{index:02d}'
        bpy.ops.wm.open_mainfile(filepath=str(ROOT/'scene.blend'),use_scripts=False)
        before=signature();appearance=submission_looks.apply_look(name)
        receipt['checks'].append({'test':name+' native Basis/UV/topology unchanged after fresh application','passed':signature()==before})
        scene=bpy.context.scene;device=configure()
        scene.render.engine='CYCLES';scene.cycles.samples=128;scene.cycles.use_denoising=True
        scene.cycles.seed=0;scene.cycles.use_animated_seed=False
        scene.render.use_persistent_data=True
        scene.render.resolution_x=scene.render.resolution_y=1024;scene.render.resolution_percentage=100
        scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
        expressions.use_action('generate_motion');scene.frame_set(1)
        row={'id':name,'appearance':appearance,'device':device,'renders':[]}
        for label,camera in [('front','RenderCamera'),('eyes','Review_macro')]:
            scene.camera=bpy.data.objects[camera]
            path=folder/f'{name}_{label}.png';scene.render.filepath=str(path)
            started=time.perf_counter();bpy.ops.render.render(write_still=True)
            row['renders'].append({'file':path.name,'sha256':sha(path),'camera':camera,
                                   'seconds':time.perf_counter()-started,'state':expressions.state()})
        receipt['looks'].append(row)
        receipt['status']='COMPLETE' if index==5 else 'RUNNING'
        (folder/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
        print('SUBMISSION_LOOK_RENDERED',name,flush=True)
    if not all(c['passed'] for c in receipt['checks']):raise RuntimeError('Native UV portability changed')


if __name__=='__main__':main()
