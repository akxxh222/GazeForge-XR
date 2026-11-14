"""Rebuild all five current static material/groom review scenes sequentially."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--blender', required=True)
    parser.add_argument('--samples', type=int, default=256)
    args = parser.parse_args()
    cache = ROOT/'tests/.optix_cache'
    cache.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, 'OPTIX_CACHE_PATH': str(cache)}
    runs = []
    started = time.perf_counter()
    for i in range(1, 6):
        look = f'look_{i:02d}'
        views = ['front', 'macro', 'macro_left', 'macro_right', 'eye_closeup', 'side_left', 'side_right'] if i == 1 else ['front', 'macro']
        log = ROOT/'work'/f'{look}_realism.log'
        step_started = time.perf_counter()
        with log.open('w', encoding='utf-8') as output:
            completed = subprocess.run([args.blender, '--factory-startup', '--background',
                                        '--python-exit-code', '1', '--python', 'scripts/build_gnm_look.py',
                                        '--', '--look', look, '--views', ','.join(views),
                                        '--samples', str(args.samples)],
                                       cwd=ROOT, env=env, stdout=output, stderr=subprocess.STDOUT)
        run = {'look': look, 'render_exit_code': completed.returncode,
               'render_seconds': round(time.perf_counter()-step_started, 2),
               'views': views, 'samples': args.samples,
               'scene': f'work/gnm/scene_{look}_realism.blend'}
        runs.append(run)
        receipt = {'stage': 'Milestone 2 scalp groom and controlled corneal highlights',
                   'total_seconds': round(time.perf_counter()-started, 2), 'runs': runs,
                   'complete': len(runs) == 5 and all(r['render_exit_code'] == 0 for r in runs)}
        (ROOT/'tests/milestone2/render_runs.json').write_text(json.dumps(receipt, indent=2)+'\n')
        print(json.dumps(run), flush=True)
        if completed.returncode:
            raise RuntimeError('Render failed; inspect '+str(log))


if __name__ == '__main__':
    main()
