# Native GNM blink prototype

Scene: `work/milestone3/IRISX_BLINK_PROTOTYPE.blend`. Blender 5.2.3 LTS, neutral frame 1; play frames 1-72 at 24 fps for two bilateral blinks. Frames 21 and 51 are closed, frames 27 and 57 reopen. Select `GNM_skin` and use Object Data > Shape Keys for `Blink.L` / `Blink.R`.

The original GNM Basis, topology and UVs remain unchanged. Deterministic semantic wink deltas come from the pinned official expression decoder (Apache-2.0), isolated to the corresponding native eye region. Explicit endpoint gains 1.16 L / 1.21 R correct the residual opening in the mean wink. Skin geometry deforms; the eyeballs retain rigid physical pivots. Lashes and brows use per-strand barycentric roots and normal transport; waterlines/tear film/canthi use driven shape keys. The blink timeline uses clamped Bezier handles.

`blink_report.json`: **58 PASS / 0 FAIL**, freshly reopened with script auto-execution disabled. This verifies native data, the saved editable timeline, independent normalized controls, invalid-input rejection without partial mutation, fixed eye centers and deterministic reset. At openings 1/.75/.5/.25/0, all 207 lash roots remain within 0.035 mm of the moving head. An 81x81 frontal ray grid per eye finds zero visible eye rays at full neutral closure. This is sampled visibility evidence, not a continuous intersection proof.

Actual Cycles diagnostic renders in `work/milestone3/`: `open.png`, `half.png`, `closed.png` and `closed_front.png`, at 1024x1024 / 64 samples. `prototype.json` records the exact saved scene and image hashes. The initial wink had a visible gap and was rejected before this checkpoint. A full blink pose was also checked on Blender's live timeline; the file was reloaded at neutral afterward.

`render_blink_preview.py` renders 36 changing 3D frames at 512x512 / 32 samples and encodes `work/milestone3/blink_preview.mp4` (1.5 seconds at 24 fps). It retains source PNGs and a frame/pose/hash manifest. This small close-up diagnostic is separate from the three final expression-mode videos.

The completed preview rendered in 237.54 seconds. `blink_video_report.json` records **8 PASS / 0 FAIL** after OpenCV decoded every frame: duration/dimensions, current-scene and raw-frame hashes, encoded frame ordering, changing pixels and reopening are verified. `blink_decoded_strip.png` shows decoded frames 18/20/21 (open, nearly closed, closed). The decoded strip was visually inspected; it still shows the source skin/brow limitations, so it is not a reference-level realism approval.

## Reproduce

From the repository root in PowerShell:

```powershell
python scripts/prepare_gnm_blink_shapes.py
& 'E:\Apps\blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python scripts/build_gnm_blink_prototype.py
& 'E:\Apps\blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python scripts/validate_gnm_blink.py
& 'E:\Apps\blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python scripts/render_blink_preview.py
python scripts/validate_blink_video.py
```

The first command needs CPython NumPy/h5py; authoring/rendering uses Blender's Python. It assumes the static lid review parent already exists. `probe_blink_closure.py` is a tuning diagnostic, not an acceptance report.

For manual script control, detach the saved blink action in an unsaved working copy before calling `lids.set_opening(left, right)`. Otherwise later frame evaluation deliberately restores the keyed timeline pose. `lids.reset()` restores open keys; `eyes.reset()` restores eye fixation separately. No user preferences or downloaded scripts are executed.

## Remaining work

- Vertical gaze follow and combined-gaze blink review, including corneal clearance and self intersections between sampled poses.
- Canthal stability and texture stretching under expression; independent brow-expression controls.
- Reference-level skin, hair and eye integration. The wider Milestone 2 visual gate remains open.
- Final expression modes, five-look motion portability and delivery packaging. The prototype is checkpointed in Git; this does not complete the milestone.

The scene inherits the public iris/hair and mixed-source skin licenses; see `assets/LICENSES.md`. Hair's unstated CC BY-SA version remains an open final-redistribution item.
