"""Render five 1024px directions plus a repeated reset from the portable scene."""
import hashlib
import json
from pathlib import Path
import sys
import time

import bpy

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from wrapper import sequences,expressions,eyes


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    folder=ROOT/'runtime/directions';folder.mkdir(parents=True,exist_ok=True)
    scene,provenance=sequences._prepare('look_01',1024,128,ROOT/'scene.blend')
    result={'scene_sha256':sha(ROOT/'scene.blend'),'provenance':provenance,
            'builder_sha256':sha(Path(__file__)),'renders':[]}
    with expressions.manual():
        for name,h,v in [('reset',0,0),('left',-1,0),('right',1,0),('up',0,1),('down',0,-1),('reset_repeat',0,0)]:
            expressions.reset();eyes.move(h,v)
            before=expressions.state();path=folder/(name+'.png');scene.render.filepath=str(path)
            started=time.perf_counter();bpy.ops.render.render(write_still=True)
            result['renders'].append({'direction':name,'requested_input':{'h':h,'v':v},'pose':before,
                                       'file':path.name,'sha256':sha(path),'seconds':time.perf_counter()-started,
                                       'pose_after_render':expressions.state()})
            (folder/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    result['status']='COMPLETE'
    (folder/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('FIVE_DIRECTIONS_RENDERED',flush=True)


if __name__=='__main__':main()
