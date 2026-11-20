"""Check packed data, five native map applications and deterministic controls."""
import hashlib
import json
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from wrapper import expressions,eyes,submission_looks


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def signature():
    result={}
    for obj in bpy.context.scene.objects:
        if not obj.get('gnm_component'):continue
        mesh=obj.data
        result[obj.name]={
            'basis':hashlib.sha256(np.array([list(v.co) for v in mesh.vertices],np.float32).tobytes()).hexdigest(),
            'uv':hashlib.sha256(np.array([list(v.uv) for v in mesh.uv_layers.active.data],np.float32).tobytes()).hexdigest(),
            'polygons':hashlib.sha256(json.dumps([list(p.vertices) for p in mesh.polygons]).encode()).hexdigest()}
    return result


def main():
    checks=[]
    def check(name,value):
        checks.append({'test':name,'passed':bool(value)})
        if not value:print('FAIL',name,flush=True)
    reference=json.loads((ROOT/'scene_build.json').read_text())
    for index in range(1,6):
        name=f'look_{index:02d}'
        bpy.ops.wm.open_mainfile(filepath=str(ROOT/'scene.blend'),use_scripts=False)
        check(name+' fresh native Basis/UV/topology',signature()==reference['native_before'])
        check(name+' every file image packed',all(i.packed_file for i in bpy.data.images if i.source=='FILE'))
        submission_looks.apply_look(name)
        check(name+' original native geometry after map application',signature()==reference['native_before'])
        materials=[bpy.data.objects['GNM_skin'].data.materials[0]]
        materials += [bpy.data.objects['Eye_'+s].data.materials[i] for s in ('L','R') for i in (0,1)]
        tagged=[]
        manifest=json.loads((ROOT/'textures'/name/'manifest.json').read_text())
        for material in materials:
            for node in material.node_tree.nodes:
                filename=node.get('portable_file')
                if filename:
                    tagged.append(filename)
                    check(name+' packed channel '+filename,node.image.packed_file is not None)
                    check(name+' exact exported channel '+filename,
                          sha(Path(node.image.filepath))==manifest['files'][filename]['sha256'])
        check(name+' seven explicit native skin and eye channels',sorted(tagged)==sorted([
            'skin_basecolor.png','skin_roughness.png','skin_height.png',
            'eye_L_sclera_basecolor.png','eye_L_iris_basecolor.png','eye_R_sclera_basecolor.png','eye_R_iris_basecolor.png']))
        if index!=1:continue
        scene=bpy.context.scene
        scene.camera=bpy.data.objects['RenderCamera']
        check('40 cm fixed render camera',abs((scene.camera.matrix_world.translation-eyes.midpoint()).length-.4)<1e-6)
        library=json.loads(scene['expression_actions'])
        check('all three action bundles saved',all(mode in library for mode in ('left','right','generate_motion')))
        centers={s:bpy.data.objects['Eye_'+s].matrix_world.translation.copy() for s in ('L','R')}
        for mode in ('left','right','generate_motion'):
            expressions.use_action(mode)
            for frame in range(1,145):
                scene.frame_set(frame)
                target=bpy.data.objects['FixationTarget'].location
                delta=target-eyes.midpoint()
                check(f'{mode}/{frame} calibrated target bounds',abs(delta.y+.35)<1e-6 and abs(delta.x)<=.050001 and abs(delta.z)<=.050001)
                for side in ('L','R'):
                    obj=bpy.data.objects['Eye_'+side]
                    axis=(obj.matrix_world.to_3x3()@Vector((0,1,0))).normalized()
                    desired=(target-obj.matrix_world.translation).normalized()
                    check(f'{mode}/{frame} fixed physical pivot and common aim {side}',
                          (obj.matrix_world.translation-centers[side]).length<1e-7 and (axis-desired).length<1e-5)
    failed=sum(not c['passed'] for c in checks)
    report={'status':'PASS' if not failed else 'FAIL','passed':len(checks)-failed,'failed':failed,
            'checks':checks,'scene_sha256':sha(ROOT/'scene.blend'),'validator_sha256':sha(Path(__file__)),
            'scope':'Fresh packed-scene loads, five exported look applications on unchanged native GNM, and all 432 integer-frame physical aim/pivot checks. Visual acceptance remains separate.'}
    folder=ROOT/'runtime/audit';folder.mkdir(parents=True,exist_ok=True)
    (folder/'scene.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('PORTABLE_SCENE_AUDIT',report['status'],report['passed'],failed,flush=True)
    if failed:raise SystemExit(1)


if __name__=='__main__':main()
