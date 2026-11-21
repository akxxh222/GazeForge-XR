# GazeForge XR

**VITChennai_IrisX · Samsung XR Track 01**

We built a Blender face rig that generates labelled gaze images and short eye-movement sequences. Both eyes rotate about their own centres and follow one fixation target. The scene includes eyelid closure, gaze follow, eyebrow controls and five texture looks on the original GNM UVs.

## Start here

1. Open `scene.blend` in **Blender 5.2.3 LTS**. The textures are packed; no add-ons are needed.
2. Press **F12** for the Cycles render. Material Preview is useful for navigation, but its hair and cornea shading differs from the final render.
3. Play frames **1–144** to see the six-second gaze sequence and blinks.
4. Open `videos/` for the three final clips, `previews/` for the five face/eye looks, or `demo/presentation.pptx` for the project slides.

| Path | Contents |
| --- | --- |
| `scene.blend` | Editable face, eye bones, lids, materials, camera and lights |
| `wrapper/` | Gaze, expression, texture and capture controls |
| `renders/` + `metadata.json` | Ten clockwise 1024 × 1024 PNGs and their labels |
| `videos/` | Left, Right and GenerateMotion; six seconds each |
| `textures/` | Five native face/eye map sets and shared sclera height maps |
| `previews/` | One front and one eye close-up per look |
| `demo/` | Presentation and 90-second overview |
| `tests/` | Validation results and capture receipts |
| `docs/` | Rig/metadata notes and asset credits |

## Render again

Run these commands from this folder. Replace the Blender executable path if needed.

```powershell
& 'E:\Apps\blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python scripts/render_expressions.py -- --mode all --duration 6 --fps 24 --resolution 720 --samples 96 --official --official-samples 192
```

This renders every video frame from the 3D scene. New files go under `runtime/capture/`; the supplied results stay in place. To generate only the ten official images, replace `--mode all --official` with `--official-only`.

Cycles uses an available GPU and falls back to the CPU. The supplied clips are 720 × 720 at 24 fps. The official PNGs are 1024 × 1024. Rendering the full set can take a while, especially on the CPU.

## Python controls

In Blender's Python Console, add this folder to the import path:

```python
import bpy, sys
from pathlib import Path
project = Path(bpy.data.filepath).parent
sys.path.insert(0, str(project))
from wrapper import eyes, expressions, submission_looks
```

`eyes.move(h, v)` accepts values from −1 to +1. Positive `h` means image right; positive `v` means up. `eyes.reset()` returns to the centre. A manual gaze pauses the eye/target actions so rendering does not replace the requested pose.

For a manual render with open lids:

```python
with expressions.manual():
    expressions.reset()
    eyes.move(-1, 0)
    eyes.render('runtime/manual_left.png')
```

The context restores the previous timeline actions afterwards. Select a saved sequence with `expressions.use_action('left')`, `'right'` or `'generate_motion'`. Switch textures with `submission_looks.apply_look('look_02')`; IDs run from `look_01` to `look_05`.

## Calibration and labels

The camera is fixed **40 cm** in front of the eye midpoint. The target plane is **35 cm** forward with horizontal/vertical offsets up to **±5 cm**. Ten clockwise samples use `theta = 2*pi*k/10`, `h = sin(theta)`, `v = cos(theta)`, starting at the top.

World axes are X right, Y behind the subject and Z up. Distances are metres; rotations are world XYZ Euler angles in radians. Anatomical eye L appears on the right of the image. Pixel coordinates start at the top-left.

Pupil labels describe the geometric aperture centre projected by the camera. They are not apparent pupil centres measured through corneal refraction. The 3 × 4 `camera_matrix` maps a world point to homogeneous pixel coordinates; divide its first two outputs by the third. [Rig and metadata details](docs/METHODS.md).

## Check the submission

```powershell
python -m pip install -r requirements.txt
python scripts/verify_submission.py
```

The check covers file hashes, video decoding, image sizes, sequence order and metadata. Full rerender checks and the fresh-extraction smoke run are recorded in `tests/report.json`.

Build the team ZIP with `python scripts/package_submission.py`. The generated ZIP and its checksum file stay local and are excluded from Git.

## AI disclosure

We used OpenAI Codex for substantial assistance with the Blender/Python implementation, rig and material setup, debugging, rendering automation, validation, documentation and presentation preparation. We set the requirements and reviewed the scene through successive revisions, including eye alignment and appearance.

The final images and motion clips are Blender renders made with the credited public assets listed in [docs/ASSETS.md](docs/ASSETS.md). The overview video combines those renders with captions. An AI-generated iris texture was tested during prototyping, then replaced, together with its derived maps, before the final renders. That experiment remains in earlier Git commits; it is absent from the current files and submission ZIP. No generative-AI images or video clips are included in the final presentation or rendered media.

## Notes

The face uses transferred skin detail and an original strand groom. Fine eyelid detail and the closely combed temples remain approximations. The cornea uses an artistic shadow-transmission adjustment; the scene is not a measured optical model. We have not biologically validated the motion. Asset credits and licence terms are in [docs/ASSETS.md](docs/ASSETS.md).

If the viewport looks grey, switch out of Solid shading. If a manual pose disappears, use the manual context above. Keep the whole folder together when switching texture looks; the default scene's textures are also packed for direct opening.
