# Eye appearance review, 2026-11-15

Team: VITChennai_IrisX. This is a separate local candidate following the user's
frame-43 coordination concern. It does not replace the completed M3 scene or
M4 captures, and does not close the M2 reference-level appearance gate.

## Open and inspect

Open `work/review/eye_refinement/IRISX_EYE_REFINEMENT.blend`.
The saved default is the new `natural_review` action: 96 frames at 24 fps,
with short authored gaze transitions, held fixations and a blink. Its timing
is an animation choice, not measured human kinematics. Original `left`,
`right` and `generate_motion` bundles remain selectable through
`wrapper.expressions.use_action()`.

For the original reported pose, select `generate_motion` and frame 43.
The before/after stills use that original action and the same `Review_macro`
camera, lighting, resolution and 128-sample Cycles settings. The fixed
`RenderCamera` remains the camera for calibrated dataset views.

The rendered review video is `work/review/eye_refinement/eye_refinement_review.mp4`.
It uses the separate close-up camera at 512 square and 32 samples; it is a
motion diagnostic, not the final 1024-square dataset or a final-quality film.

## Changes

- Replaced the active Splash Fox iris shader with a packed CC0 MakeHuman iris
  region, sampled through an annulus registration on the unchanged GNM UVs.
  Both inner and outer iris boundaries are registered to avoid painting an
  additional black pupil ring. Saturation and hue are restrained.
- Warmed the scleral material while reducing its bump and subsurface strength.
  The native opaque pupil and refractive outer cornea remain separate.
- Reduced corneal roughness from 0.035 to 0.025, retaining IOR 1.376.
- Relaxed the evaluated open-lid rest by 7.5% of the existing closure map.
  The field is `0.075 + 0.925 * blink`, retaining the full-closure endpoint.
  This changes the physical open rest; a control opening of 1 now means this
  relaxed rest. Live attachments continue to sample the evaluated head.
- Added a separate four-second action with gaze holds and a blink. Original
  action data, target plane and rigid eye pivots are retained.

There is no pupil translation, forced parallel gaze, corrective eye yaw,
change to native Basis/UV/topology, or camera-distance adjustment in this pass.
The common target remains 35 cm forward with normalized motion bounded by
5 cm; RenderCamera remains 40 cm forward.

## Diagnostic limits

The first mesh-corner projection diagnosis was insufficient to establish
misplaced eyeballs. `probe_eye_appearance.py` instead casts camera rays against
the actual evaluated head and eye surfaces. In the original scene, the two
skin-bounded apertures contain 566/565 visible pixels at neutral and 585/584
at frame 43 on its 720-square pixel grid. These counts exclude small tissue
attachments and are not a complete optical pupil-center measurement.

In the original rendered frame 43, dark-pupil pixel measurements move right
by 2.20 and 2.56 pixels from neutral. This supports coupled visible movement;
it does not prove that the pose reads naturally. The user-reported visible
alignment concern remains an explicit visual review item.

The new candidate requires its own geometry and rendered-media checks; the
old M3/M4 pass counts do not certify altered evaluated lids or this new clip.
Evidence is written to `tests/eye_refinement/`. A contact sheet covers every
decoded video frame. Full continuous collision and human-kinematic validation
are not claimed.

Skin detail, eyebrow/canthus integration, hair appearance and final five-look
acceptance remain open. The inherited groom still has the recorded unresolved
CC BY-SA version; this local review does not resolve final redistribution.

## Reproduce

From the repository root, in PowerShell:

```powershell
$env:OPTIX_CACHE_PATH = Join-Path (Get-Location).Path 'tests/.optix_cache'
& 'E:\Apps\blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python scripts/build_eye_refinement.py
& 'E:\Apps\blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python scripts/render_eye_refinement_review.py
& 'E:\Apps\blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python scripts/validate_eye_refinement.py
python scripts/audit_eye_refinement_media.py
```

These commands write only the separate review/evidence folders. Rebuilding
renders overwrites that candidate's review files. For a refined shader rerun,
`build_eye_refinement.py -- --after-only` verifies and reuses the two baseline
stills. Reapply the motion builder afterward to restore the extra review mode.

The pinned unchanged CC0 image is in `assets/eye_refinement/`; it is packed in
the candidate. Existing source assets are required to rebuild the parent M3
scene, as documented in the earlier milestones.

## Completed review artifacts

The saved candidate passes 111 selected geometry/control checks and 493 media/pose checks, with zero failures. All 96 decoded frames were inspected in order on the contact sheet, alongside the before/after stills and selected raw closure images. This is a validated review candidate, not reference-level realism acceptance. See `tests/eye_refinement/manifest.json` and `visual_review.json` for exact files, hashes and remaining defects. Commit history is recorded in `docs/CHECKPOINTS.md`; immutable JSON receipts retain their creation-time commit status.
