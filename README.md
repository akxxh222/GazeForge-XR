# GazeForge XR - VITChennai_IrisX

Milestone 1 establishes the native GNM Head 3.0 baseline, preserving its UVs and connecting bone-driven eyes to the calibrated Python controller. This checkpoint contains the baseline source, asset/license manifests, five-direction draft renders and validation evidence. This checkpoint also adds the Milestone 2 texture/material drafts described below. Eyelid, expression-video and submission work is planned in [MILESTONES.md](MILESTONES.md).

## Reproduce the baseline

Prerequisites: Blender 5.2.3 LTS; Python 3.10+ with the packages in `requirements.txt` for the optional contact sheet. The importer and controller run inside Blender using its bundled NumPy. PowerShell downloads the official model with TLS verification and checks Google's published SHA-256.

```powershell
& ./scripts/fetch_gnm.ps1
$env:OPTIX_CACHE_PATH = Join-Path (Get-Location) 'tests/.optix_cache'
& 'E:\Apps\blender.exe' --factory-startup -b --python-exit-code 1 --python scripts/build_gnm_baseline.py
& 'E:\Apps\blender.exe' --factory-startup -b work/gnm/scene_baseline.blend --python-exit-code 1 --python scripts/validate_gnm_baseline.py -- --render
python scripts/make_gnm_contact_sheet.py
```

Replace the Blender executable path on other machines. The downloaded model and generated `.blend` are excluded from Git and are reproducible through these commands. The generated scene is `work/gnm/scene_baseline.blend`. [Asset details](assets/gnm/README.md) document the native per-region UV layout and retained topology IDs.

## Baseline contract and evidence

The camera is locked 0.40 m ahead of the eye midpoint. The common fixation target is 0.35 m ahead with +/-0.05 m horizontal/vertical bounds. `wrapper.eyes.move(h,v)`, `reset()` and `render()` provide deterministic binocular control. Each eye rotates rigidly around its native joint; original pupil coordinates supply geometric projections.

`tests/milestone1/report.json` records 82 passing checks, zero failures and actual Cycles GPU render timings. The neutral and native-UV checker images are 1024x1024; four directional previews are 512x512 diagnostics. These are baseline evidence, not the final ten submission renders. See [the evidence notes](tests/milestone1/README.md) and [contact sheet](tests/milestone1/contact_sheet.png).

## Scope, provenance and licenses

Milestone 2 remains in progress. Static brows, lashes and layered eye/skin materials are implemented; visual seam/detail refinement, dynamic eyelids, expression videos and apparent refracted pupil validation remain pending.

The calibrated gaze/projection controller and render-device selector were developed for the earlier local MPFB prototype on 2026-11-07 and reused here. The original project commit `0adb2a2` was removed from active history at the user's request and retained in a local recovery bundle; this checkpoint does not imply that reused code was first written now. Legacy prototype assets, decks, videos, ZIPs and unrelated source files are excluded from this commit.

Original project code uses the [MIT license](LICENSE). The Google GNM model and retained upstream reference files use Apache-2.0; see [asset provenance](assets/LICENSES.md) and the [full third-party license](assets/gnm/LICENSE.Apache-2.0.txt).

## Milestone 2 texture and material checkpoint

Five draft looks in `textures/look_01` through `look_05` provide 4K native-GNM skin maps and separate 2K left/right eye maps. The offline authoring pipeline transfers licensed CC0 sources using a temporary MakeHuman surface; the target GNM topology and original UVs remain unchanged. `wrapper.materials.apply_look()` applies the resulting maps directly to a fresh baseline. `wrapper/appearance.py` adds static brows, lashes and tear menisci.

Build the baseline first, then follow [the texture reproduction commands](textures/README.md). Python post-processing additionally requires SciPy from `requirements.txt`. Rebuildable downloaded source maps, caches and packed `.blend` scenes remain outside Git; exported maps, source manifests and review images are included.

Evidence: 117 texture checks, 80 fresh-scene portability checks and 70 render/metadata checks pass. Fifteen rendered preview views and a [five-look contact sheet](tests/milestone2/contact_sheet.png) are retained. These checks establish technical behavior; photographic realism and visible seam quality still need acceptance. See [the review ledger](tests/milestone2/REVIEW.md) for remaining defects and rejected drafts. This is a work-in-progress checkpoint, not completion of Milestone 2.

The calibrated front camera remains fixed at 40 cm. Macro and side cameras serve material review only. Pupil labels describe geometric pinhole projections; corneal refraction can shift the apparent visible pupil.
