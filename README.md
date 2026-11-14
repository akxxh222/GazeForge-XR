# GazeForge XR - VITChennai_IrisX

Native GNM Head 3.0 project for Samsung XR Track 01. Milestone 1 is complete. Milestone 2 visual refinement and the Milestone 3 blink prototype are in progress; the three final expression videos and final submission remain pending. See [the five-stage plan](MILESTONES.md) and [checkpoint history](docs/CHECKPOINTS.md).

## Open the current work

- Animated scene: `work/milestone3/IRISX_BLINK_PROTOTYPE.blend`. Play frames 1-72 at 24 fps for two blinks. Independent `Blink.L` / `Blink.R` shape keys, lashes, brows and waterlines follow the native head deformation. [Blink preview](work/milestone3/blink_preview.mp4) and [motion evidence](tests/milestone3/README.md).
- Corrected static scene: `work/review/lids/IRISX_LIDS_REVIEW.blend`. Material Preview shows the iris/sclera through an EEVEE corneal surface; F12 uses physical Cycles refraction. [Static correction evidence](tests/milestone2/lid_review/README.md).
- Public asset parent: `work/review/cyberpunk/IRISX_ASSET_REVIEW.blend`. [Source/adaptation notes](assets/public_candidates/README.md).
- Five native-UV looks: [texture instructions](textures/README.md), [contact sheet](tests/milestone2/contact_sheet.png), and [visual defect ledger](tests/milestone2/REVIEW.md).

The three authored review scenes, selected pose images, receipts and short blink MP4 are versioned explicitly. Other `work/` downloads, caches, older experiments, raw animation frames and Blender backups remain local/rebuildable. The root MPFB scene, old deck/demo/ZIP and legacy packaging scripts are preserved locally and are outside these native-GNM checkpoints.

## Reproduce the calibrated baseline

Use Blender 5.2.3 LTS and the Python dependencies in `requirements.txt`. Replace the executable path on another computer.

```powershell
& ./scripts/fetch_gnm.ps1
$env:OPTIX_CACHE_PATH = Join-Path (Get-Location) 'tests/.optix_cache'
& 'E:\Apps\blender.exe' --factory-startup -b --disable-autoexec --python-exit-code 1 --python scripts/build_gnm_baseline.py
& 'E:\Apps\blender.exe' --factory-startup -b work/gnm/scene_baseline.blend --disable-autoexec --python-exit-code 1 --python scripts/validate_gnm_baseline.py -- --render
python scripts/make_gnm_contact_sheet.py
```

The main model NPZ is downloaded and verified against Google's published checksum, and remains excluded from Git. Native geometry, per-region UVs and original vertex/quad identifiers are preserved. [Asset details](assets/gnm/README.md) and [baseline evidence](tests/milestone1/README.md).

The fixed camera is 0.40 m ahead of the eye midpoint. The common fixation target is 0.35 m ahead with +/-0.05 m horizontal/vertical bounds. `wrapper.eyes.move(h,v)`, `reset()` and `render()` control rigid binocular rotations about the native physical eye centers. Macro/side cameras serve review only. Labels are geometric pinhole projections; refraction can shift visible apparent pupil centers.

## Verification and remaining gates

Latest applicable reports: 82 baseline checks, 133 texture/source checks, 80 material portability checks, 70 render/provenance checks, 105 five-look groom checks, 46 public-asset checks, 41 preview/lid checks, 58 blink-scene checks and 8 decoded-video checks. These reports apply to their documented scene revisions and do not constitute a photorealism score.

The blink diagnostic contains 36 changing Cycles frames at 512x512, encoded at 24 fps for 1.5 seconds. It is separate from the final three expression-mode videos. Gaze-follow, combined-gaze corneal clearance/self intersections, texture stretching and final reference-level skin/eye/hair acceptance remain open. Reproduction commands and the manual-versus-timeline control behavior are documented in the relevant evidence notes.

## Provenance and licensing

Original project code uses [MIT](LICENSE). GNM native model/semantic derivatives retain Apache-2.0. Skin sources combine CC0 diffuse maps and attributed Lee Perry-Smith CC BY 3.0 scan detail. The adapted Splash Fox iris shader retains CC BY-SA 3.0. The Hair Styles source states CC BY-SA without a version; its derivatives remain local review material pending resolution before final redistribution. See [the asset license ledger](assets/LICENSES.md).

The calibrated controller/render-device selector were reused from the earlier local MPFB prototype; the removed original commit remains in its local recovery bundle. No Chris Jones / Universal Human asset files are imported. [Human Progress](docs/HUMAN_PROGRESS_REFERENCE.md) informs the independently authored rig only. The final ZIP has not been rebuilt or certified against the new evaluation requirements.
