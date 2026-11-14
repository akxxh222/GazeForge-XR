# Gaze-follow, brow and combined-blink review

Current scene: `work/milestone3/gaze_lids/IRISX_GAZE_LIDS_RIG.blend`. The preceding committed blink-only scene remains unchanged. This new scene opens at neutral frame 1 and contains a six-second, 144-frame action at 24 fps: left/right/up/down fixation, two blinks during vertical gaze, and restrained brow raising.

## What changed

- Four independent native gaze-follow keys rotate upper/lower lid regions around the physical eye centers, with 0.65/0.35 response gains. Canthal taper restrains lateral edges. Follow attenuates with `1 - blink` so the full closed pose stays deterministic.
- Independent `Brow.Raise.L` / `Brow.Raise.R` keys add a restrained 1.5 mm maximum authored brow raise.
- A smooth, at-most 0.40 mm depth-only ocular-clearance key and matching attachment refit address shallow lash-root/cornea intersections in combined poses. Native Basis, topology and UVs remain unchanged.
- Generalized rest-triangle barycentric binding and normal transport carry lashes, brows, waterline, tear film and canthal details through eight motion keys.
- Exact native Track To constraints keep both eyes aimed at the common fixation target between timeline keys. Three editable actions retain eye, target and lid/brow motion. No frame handlers or custom Python callbacks run during playback.
- `wrapper.expressions.manual()` temporarily detaches the three actions for script poses/renders, then restores the timeline even after a caller exception. Gaze-follow and attachment drivers remain active.

The first attachment draft retained a stale subdivision snapshot and was rejected after millimetre-scale drift. Explicit mesh update tags and isolated key capture corrected it before the accepted render run. An earlier ocular-distance probe also exposed shallow contact intersections; the current depth correction is included in all evidence below.

## Evidence and limits

`report.json`: **591 PASS / 0 FAIL** with auto-execution disabled. The exact saved scene hash matches the geometric probe. Nine gaze positions (center/cardinals/corners) times five opening fractions cover 45 poses. All 1,447 lash/brow roots stay within 0.10 mm of the moving skin (acceptance threshold 0.30 mm). Lash-root signed eye-surface probes stay within the declared 30 micrometer contact tolerance; the minimum is approximately -0.0095 mm, rather than a claim of mathematically positive clearance everywhere. Full closure exposes zero eye samples on each 81x81 frontal grid at all nine gazes.

Across all 144 timeline frames, both physical eye centers stay invariant and the maximum aim-direction vector residual is 1.23e-7. Manual controls/reset, invalid brow inputs, action restoration, simple native drivers and the original 40 cm camera/35 cm target contract are checked.

Native face-area ratios in sampled deformations span approximately 0.17-1.70; closure compresses some lid faces. Lash-endpoint nearest-native-vertex proxies move up to 3.53 mm during the semantic wink. These sparse proxies are not established anatomical canthal landmarks; their movement and the tight closure shape need visual review/corrective sculpting before claiming relaxed natural blinks. Gaze-follow alone moves these proxies by only about 0.0041 mm. Quantitative face areas do not certify natural texture stretching or a self-intersection-free lid volume.

Actual 1024x1024 / 64-sample Cycles stills beside the scene: `up_open`, `down_open`, `up_half`, `down_half`, `up_closed`, and `front`. The up/down and intermediate close-ups were visually inspected. The scene was opened and its timeline played in the live Blender session, then returned to frame 1 without saving UI-only changes.

`gaze_lids_preview.mp4` is a continuously rendered six-second review clip: 144 actual 384x384 / 24-sample Cycles frames at 24 fps. It is a small motion diagnostic, not a final expression-mode video. Raw frames and pose/hash records are retained in local `work/`. `video_report.json` records **17 PASS / 0 FAIL** after all frames were decoded and compared with their raw source/hash/pose records. The render took 720.81 seconds. `decoded_strip.png` shows actual decoded left/right/up/closed/down/closed frames and was visually inspected.

## Reproduce

From the repository root in PowerShell, with the committed static and blink parent scenes present:

```powershell
& 'E:\Apps\blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python scripts/build_gaze_lid_rig.py
& 'E:\Apps\blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python scripts/probe_gaze_lid_rig.py
& 'E:\Apps\blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python scripts/validate_gaze_lid_rig.py
& 'E:\Apps\blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python scripts/render_gaze_lid_review.py -- --video
python scripts/validate_gaze_lid_video.py
```

Within Blender, add the project root to `sys.path`, then:

```python
from wrapper import eyes, lids, expressions
with expressions.manual():
    eyes.move(0, 1)
    lids.set_opening(.5)
    expressions.set_brows(.35, .2)
    eyes.render('tests/custom_gaze_lids.png')
# The prior timeline pose/actions are restored here.
```

Remaining gates: relaxed canthal/closure sculpting, continuous corneal/lid-volume and self-intersection checks, texture-stretch/skin/hair visual acceptance and five-look expression portability. The three final expression-mode videos and final packaging remain pending. This work does not complete Milestone 3 and has not been committed automatically. Existing GNM, skin, iris and hair licenses still apply; the public hair license-version issue remains open for final redistribution.
