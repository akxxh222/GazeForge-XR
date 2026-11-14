# Native expression capture

Team: **VITChennai_IrisX**. Source scene: `work/milestone3/final/IRISX_MILESTONE3.blend`.

Milestone 4 uses the completed native GNM articulation scene. Milestone 2 reference-level appearance remains a separate open gate. The current production run uses `look_01`, retaining the packed skin, attributed iris and fitted groom. Local renders do not resolve the groom's outstanding redistribution license-version question.

## Render commands

Run from the repository root in PowerShell, with Blender 5.2.3 LTS:

Capture runs inside Blender's Python. The decoded-video/image audit runs in normal CPython with `python -m pip install -r requirements.txt` (NumPy, Pillow, SciPy and OpenCV); `bpy` is supplied by Blender and is not installed into that post-processing environment.

```powershell
& 'E:\Apps\blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 `
  --python scripts/render_expressions.py -- `
  --mode all --official --output work/milestone4/capture
```

This runs **Left**, **Right** and **Generate Motion** as `left`, `right` and `generate_motion`. Each clip is six seconds, 144 actual 720×720 Cycles renders at 24 fps and 64 samples. Six seconds retains the authored and audited blink timing. The earlier ten-second plan was provisional; the evaluation permits clips up to fifteen seconds. Every frame evaluates the 3D scene, including frames during a held pose. No motion is synthesized between rendered pictures.

The same command supports `--mode left`, `--mode right` or `--mode generate_motion` individually. `--official-only` captures just the ten clockwise images. `--texture-id look_02` through `look_05` select the other draft native looks. Resolution, samples, duration and fps are configurable. Very sparse diagnostic sampling can miss brief expressions; a custom clip must pass the decoded motion checks before it is treated as a deliverable.

The locked `RenderCamera` remains 40 cm from the eye midpoint. The common fixation plane is 35 cm forward, with normalized h/v mapped to ±5 cm. Viewer-space Left is negative h; native anatomical eye L appears on the image right. Camera transform, lens, lighting, color management and render settings are checked before every frame.

## Resume and output

If interrupted, repeat the exact command with `--resume`. Resume requires identical source scene/code hashes and capture configuration. Each cached frame must match its recorded pose and image checksum; missing or mismatched frames are rendered again. A different configuration requires a separate output directory. Existing captures are not silently overwritten by an ordinary run.

```text
work/milestone4/capture/
  left/
    frames/frame_0001.png ... frame_0144.png
    left.mp4
    capture.json
  right/
    frames/...
    right.mp4
    capture.json
  generate_motion/
    frames/...
    generate_motion.mp4
    capture.json
  clockwise/
    renders/frame_00.png ... frame_09.png
    metadata.json
    capture.json
```

Each checkpoint records `RUNNING` until all its frames and output media are complete. Atomic JSON writes preserve the previous valid checkpoint during a write. Raw frames remain local reproducible render data. The completed run spans `work/milestone4/production.log` and `production_resume.log`: the first renderer stopped after eight scan frames, and verified resume reused those frames. `tests/milestone4/resume.json` records this observed recovery without inferring the interruption cause.

The official ten PNGs are always **1024×1024**, open-eyed with neutral brows and pupil constriction 0.7, under constant lighting at 128 samples by default. Sampling uses `theta=2*pi*k/10`, `h=sin(theta)`, `v=cos(theta)`, k=0..9, starting at the top and advancing clockwise. This output is separate from the legacy root `renders/` and `metadata.json`; final packaging is Milestone 5.

## Python entry points

Inside Blender, with the repository root on `sys.path`:

```python
from wrapper.sequences import render_expression, render_clockwise
from wrapper.metadata import export_clockwise_metadata

render_expression('left', texture_id='look_01', duration_s=6, fps=24,
                  output_dir='E:/captures/IrisX', resolution=720, samples=64)
receipt = render_clockwise(texture_id='look_01', output_dir='E:/captures/IrisX', samples=128)
export_clockwise_metadata(receipt)
```

These capture functions load a clean source scene, so use them in a background process or a Blender session without unsaved work. Manual controls remain `eyes.move(h,v)`, `eyes.reset()`, `eyes.render(path)`, `lids.set_opening(left,right)` and the brow/pupil controls in `expressions`. Use `expressions.manual()` around manual captures to prevent timeline actions from overriding controls.

`look_01` preserves the packed hero unchanged. The other look IDs swap verified native skin/sclera image channels while keeping the improved optical layers, canthal skin material sharing and attributed iris network. Their iris palette varies independently. These variants are draft appearances, not five newly accepted photoreal looks or five completed baked iris exports.

## Metadata and validation

Frame manifests include source timeline frame/subframe, output timestamp, actual h/v, lid openings, brow raise, pupil constriction, world eye rotations/quaternions, eye/pupil positions, 2D pupil projections, camera matrix, render runtime and PNG checksum. Camera matrices map world meters to continuous edge-origin pixels (u right, v down).

The pupil labels are **geometric aperture centroids and pinhole projections**. They are not measured apparent centers through the refractive cornea. World quaternions and positions are exported in addition to XYZ Euler radians. No apparent-centroid accuracy is inferred from finite geometric projections.

The clockwise CLI finalizes `metadata.json` through `export_clockwise_metadata()`. `input` preserves the requested sine/cosine controls within [-1,1]; `evaluated_input` separately retains the normalized target recovered from Blender's float32 coordinates, including rounding epsilon. Raw capture receipts preserve evaluated observations. The finalizer verifies the ten source PNG hashes and target agreement, and records its own code hash. Call it explicitly after the lower-level `render_clockwise()` Python capture function as shown above.

The audit separately measures a bounded dark-pupil component in actual rendered pixels. Its search window is seeded by the geometric projection; the centroid itself comes from the PNG. This supports image-space direction/neutral-return checks for the current dark-pupil appearance. Highlight and occlusion bias prevent treating that centroid as optical ground truth. It is not substituted for the required geometric metadata.

```powershell
& 'E:\Apps\blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 `
  --python scripts/validate_sequence_controls.py
python scripts/validate_expression_capture.py
```

The control audit exercises invalid-input rejection before mutation, all 432 default action poses, deterministic fractional evaluation, physical eye centers/aim and the five native look applications. The capture audit checks every PNG hash, decodes all three MP4s, compares decoded frames to their sources in order, checks durations and changing pixels, tests held-pose stability and verifies the official 3D-to-2D projections and angular order. It writes reports and eye/full-face contact sheets in `tests/milestone4/`.

`python scripts/validate_expression_capture.py --partial` reviews completed captures while a batch is running. Missing deliverables produce **PARTIAL**, never PASS. Final acceptance also needs visual inspection for flicker, eye/lid contact and natural expression; numerical temporal bounds do not replace that review. Milestone 3's exact-scene geometry audit remains the articulation evidence, and the Milestone 2 realism gate remains open.

## Completed checkpoint

Completed 2026-11-15: all three videos decode as 144 frames at 24 fps, six seconds and 720x720; all ten official PNGs are 1024x1024. The control audit passes 961 checks. The full capture audit passes 5419 checks in both existing and fresh isolated CPython environments. See [the evidence and visual limits](../tests/milestone4/README.md). Commit history is recorded in `docs/CHECKPOINTS.md`. For a new reproduction, choose an unused output directory; historical byte/source hashes identify the original capture environment, and the clean final extracted submission run remains Milestone 5.
