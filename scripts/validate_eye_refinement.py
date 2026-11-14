"""Audit the separate eye candidate at selected poses; no realism score."""
import hashlib
import json
from pathlib import Path
import sys
import time

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
from wrapper import eyes, lids, expressions
from validate_lid_review import digest
from validate_milestone3_final import evaluated_surface, detail_clearance
from probe_milestone3_surface import surface_metrics, closure_visibility
from probe_gaze_lid_rig import attachment_metrics


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    folder = ROOT/'work/review/eye_refinement'
    output = ROOT/'tests/eye_refinement'
    output.mkdir(parents=True, exist_ok=True)
    source = ROOT/'work/milestone3/final/IRISX_MILESTONE3.blend'
    candidate = folder/'IRISX_EYE_REFINEMENT.blend'
    bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
    bpy.context.view_layer.update()
    native = {o.name: digest(o.data) for o in bpy.context.scene.objects if o.get('gnm_component')}
    calibration = {n: np.array(bpy.data.objects[n].matrix_world, dtype=float).copy() for n in ['RenderCamera', 'Key', 'Fill', 'Rim']}
    light_data = {n: (bpy.data.objects[n].data.type, float(bpy.data.objects[n].data.energy),
                     tuple(bpy.data.objects[n].data.color), float(bpy.data.objects[n].data.size)) for n in ['Key', 'Fill', 'Rim']}
    reference_closed = {}
    gazes = [(0,0), (-1,0), (1,0), (0,1), (0,-1)]
    with expressions.manual():
        for h,v in gazes:
            expressions.reset(); eyes.move(h,v); lids.set_opening(0)
            reference_closed[(h,v)] = evaluated_surface(bpy.data.objects['GNM_skin'])[0]
    bpy.ops.wm.open_mainfile(filepath=str(candidate), use_scripts=False)
    bpy.context.view_layer.update()
    scene = bpy.context.scene
    report = {'status': 'RUNNING', 'source_sha256': sha(source), 'candidate_sha256': sha(candidate),
              'validator_sha256': sha(Path(__file__)), 'checks': [], 'poses': [],
              'scope': 'Native data, fixed calibration, selected five gazes x three lid openings plus frame43; evaluated lid intersections, point clearances, roots and closure. Not full continuous-pose certification or visual acceptance.'}
    started = time.perf_counter()
    def check(name, value):
        report['checks'].append({'test': name, 'passed': bool(value)})
        if not value:
            print('FAILED', name, flush=True)
    def save():
        report['passed'] = sum(c['passed'] for c in report['checks'])
        report['failed'] = sum(not c['passed'] for c in report['checks'])
        report['runtime_s'] = time.perf_counter()-started
        (output/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    for name, expected in native.items():
        check(name+' original Basis/UV/topology', digest(bpy.data.objects[name].data) == expected)
    report['calibration_matrix_max_abs_difference'] = {}
    for name, expected in calibration.items():
        delta = float(np.max(np.abs(np.array(bpy.data.objects[name].matrix_world)-expected)))
        report['calibration_matrix_max_abs_difference'][name] = delta
        check(name+' matrix retained within 1e-6 round-trip tolerance', delta<1e-6)
    for name, expected in light_data.items():
        data = bpy.data.objects[name].data
        check(name+' light type/energy/color/size unchanged', (data.type, float(data.energy), tuple(data.color), float(data.size)) == expected)
    check('camera 40cm from midpoint', abs((bpy.data.objects['RenderCamera'].location-eyes.midpoint()).length-.4)<1e-6)
    check('packed CC0 iris on both eyes', all(bpy.data.objects['Eye_'+s].data.materials[1].get('license') == 'CC0-1.0'
          and all(n.image.packed_file for n in bpy.data.objects['Eye_'+s].data.materials[1].node_tree.nodes if n.type=='TEX_IMAGE') for s in ('L','R')))
    centers = {s: bpy.data.objects['Eye_'+s].matrix_world.translation.copy() for s in ('L','R')}
    def inspect(label, closure=False):
        geometry = surface_metrics()
        roots = attachment_metrics()
        details = detail_clearance()
        check(label+' no lid self crossings', geometry['surface_nonadjacent_crossing_pairs'] == 0)
        check(label+' skin points clear outer eyes', all(r['inside_beyond_30um']==0 for r in geometry['outer_shell'].values()))
        check(label+' bound roots fit skin', roots['max_root_distance_m'] < .0003)
        check(label+' details clear eyes', all(r['inside_beyond_30um']==0 for r in details.values()))
        target = bpy.data.objects['FixationTarget'].location
        check(label+' fixed pivots and shared aim', all((bpy.data.objects['Eye_'+s].matrix_world.translation-centers[s]).length<1e-7 and
              ((bpy.data.objects['Eye_'+s].matrix_world.to_3x3()@Vector((0,1,0))).normalized() -
               (target-centers[s]).normalized()).length<1e-5 for s in ('L','R')))
        row = {'pose': label, 'geometry': geometry, 'attachments': roots, 'details': details}
        if closure:
            row['closure'] = {s: closure_visibility(s) for s in ('L','R')}
            check(label+' both eyes fully occluded on sampled grid', all(r['visible_eye_rays']==0 for r in row['closure'].values()))
        report['poses'].append(row)
        save()
        print('EYE_CANDIDATE_POSE', label, report['passed'], report['failed'], flush=True)
    expressions.use_action('generate_motion')
    scene.frame_set(43)
    inspect('timeline frame43')
    with expressions.manual():
        for h,v in gazes:
            for opening in (1,.5,0):
                expressions.reset(); eyes.move(h,v); lids.set_opening(opening)
                label = f'gaze {h},{v}, opening {opening}'
                inspect(label, opening==0)
                if opening==0:
                    current = evaluated_surface(bpy.data.objects['GNM_skin'])[0]
                    delta = float(np.max(np.abs(current-reference_closed[(h,v)])))
                    check(label+' original closed head surface retained', delta<1e-7)
    check('three original action bundles retained and additional review action present', set(json.loads(scene['expression_actions'])) == {'left','right','generate_motion','natural_review'})
    receipt = json.loads((folder/'render_receipt.json').read_text(encoding='utf-8'))
    check('receipt identifies candidate and refiner', receipt['scene_sha256']==sha(candidate) and receipt['refiner_sha256']==sha(ROOT/'wrapper/eye_refinement.py'))
    for record in receipt['renders']:
        check(record['file']+' actual image hash', sha(folder/record['file'])==record['sha256'])
    report['status'] = 'PASS' if all(c['passed'] for c in report['checks']) else 'FAIL'
    save()
    print('EYE_REFINEMENT_AUDIT', report['status'], report['passed'], report['failed'], flush=True)
    if report['failed']:
        raise RuntimeError('Candidate needs correction; see report')


if __name__ == '__main__':
    main()
