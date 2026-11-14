# Saved lid and Material Preview correction

Scene: `work/review/lids/IRISX_LIDS_REVIEW.blend`. Actual renders: `eye.png`, `front.png`, `eevee_eye.png` beside that scene. `receipt.json` records renderer, metadata, timings and image hashes for this exact saved file. `report.json` contains 41 passing saved-scene/render checks.

The EEVEE corneal output uses transparent/Fresnel glazing to show the interior; Cycles keeps the original refractive shader. Supported EEVEE strand surfaces replace Cycles-only hair scattering in Material Preview. These are renderer-specific approximations on the same geometry, not interchangeable physical optical models. The geometric pupil-label convention remains unchanged.

The native head's bounded static lid-sculpt shape key changes depth only. All 772 affected native vertices remain in the original Basis/UV/topology. New lash bundles, a fine waterline/tear film and small canthal tissue follow rigid head transforms in this static file. Deformation-aware motion is being developed separately in Milestone 3.

The file was opened and inspected in the live Blender session. Both irises and sclera were visible in Material Preview, correcting the reported black sockets. Full photographic detail, complete seams, natural expression/gaze follow and final reference-level visual acceptance remain open.

Reproduce:

```powershell
$env:OPTIX_CACHE_PATH = Join-Path (Get-Location) 'tests/.optix_cache'
& 'E:\Apps\blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python scripts/build_lid_review.py
& 'E:\Apps\blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python scripts/validate_lid_review.py
```

Source asset licensing remains in `assets/public_candidates/README.md` and embedded in the scene. Imported hair/iris licenses are retained; no commit or final-package replacement is included in this correction.
