"""CLI for native expression modes and the official calibrated capture."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wrapper.sequences import MODES, LOOKS, DEFAULT_SCENE, render_expression, render_clockwise
from wrapper.metadata import export_clockwise_metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=(*MODES, 'all'), default='all')
    parser.add_argument('--texture-id', choices=LOOKS, default='look_01')
    parser.add_argument('--duration', type=float, default=6)
    parser.add_argument('--fps', type=int, default=24)
    parser.add_argument('--resolution', type=int, default=720)
    parser.add_argument('--samples', type=int, default=64)
    parser.add_argument('--output', type=Path, default=ROOT / 'work/milestone4/capture')
    parser.add_argument('--scene', type=Path, default=DEFAULT_SCENE)
    parser.add_argument('--official', action='store_true')
    parser.add_argument('--official-only', action='store_true')
    parser.add_argument('--official-samples', type=int, default=128)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    if not args.official_only:
        for mode in MODES if args.mode == 'all' else (args.mode,):
            receipt = render_expression(mode, args.texture_id, args.duration, args.fps, args.output,
                                        args.resolution, args.samples, args.resume, args.scene)
            print('IRISX_EXPRESSION_COMPLETE', receipt, flush=True)
    if args.official or args.official_only:
        receipt = render_clockwise(args.texture_id, args.output, args.official_samples, args.resume, args.scene)
        export_clockwise_metadata(receipt)
        print('IRISX_CLOCKWISE_COMPLETE', receipt, flush=True)


if __name__ == '__main__':
    main()
