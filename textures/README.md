# Native GNM texture looks - Milestone 2

Five draft looks contain 4096x4096 skin base-color, roughness and 16-bit height maps, plus distinct 2048x2048 left/right eye base-color and 16-bit height maps. `skin_coverage.png` records the native skin UV coverage. All files use the original GNM Head 3.0 per-region UVs, with separate materials for skin and each eye.

The albedo sources are CC0 MakeHuman maps, spatially transferred onto GNM. They are 2K full-body source images; a 4K export does not increase their original facial detail. Fine pores/roughness and iris/sclera details are authored separately. This is a work in progress toward the visual reference, rather than a completed photorealism claim.

## Rebuild

Run from the project root with Python dependencies in `requirements.txt`, the GNM download and CC0 skin sources available:

```powershell
& ./scripts/fetch_gnm.ps1
& ./scripts/fetch_skin_sources.ps1
& 'E:\Apps\blender.exe' --factory-startup -b --python-exit-code 1 --python scripts/prepare_gnm_skin_transfer.py
python scripts/make_gnm_texture_looks.py
& 'E:\Apps\blender.exe' --factory-startup -b --python-exit-code 1 --python scripts/build_gnm_look.py -- --look look_01 --views front,macro,macro_left,macro_right,eye_closeup,side_left,side_right
```

The transfer uses the preserved CC0 `assets/mpfb_head.json.gz` as a source surface, fits a temporary copy to geometric landmarks and projects source UVs. The GNM target geometry and its UVs are unchanged. Visible orbital skin is sampled from front-facing source surfaces to avoid transferring inner-socket atlas colors onto the lids. `assets/gnm/skin_transfer.json` records distances and local source-seam handling.

Repeat the final command with `look_02` through `look_05`. `wrapper.materials.apply_look('look_01')` applies the exported images directly to a fresh native baseline without the source surface or transfer UVs. Seven material images are packed in each generated `work/gnm/scene_look_XX.blend`.

```powershell
python scripts/audit_gnm_textures.py
& 'E:\Apps\blender.exe' --factory-startup -b --python-exit-code 1 --python scripts/validate_gnm_materials.py
python scripts/make_gnm_material_sheet.py
```

## Evidence and remaining work

`tests/milestone2/texture_audit.json` checks hashes, dimensions, bit depth, distinct maps and source licenses, and reports native UV seam color measurements. `portability_report.json` checks each look on an independently reloaded baseline. Engineering passes do not certify photographic realism.

Static brows, lashes and tear menisci support material review. Their deformation-aware binding and lid animation belong to Milestone 3. Macro and side cameras are additional review views; the saved scene restores the locked 40 cm render camera and neutral gaze.

Current pupil metadata describes the geometric aperture centroid projected through the pinhole camera. Refraction can shift the apparent rendered pupil; these quantities are not asserted equal.

Remaining visual issues and rejected drafts are recorded in `tests/milestone2/REVIEW.md`. This checkpoint preserves the texture/material drafts; Milestone 2 remains in progress until its visual acceptance gates pass. Source authors, modifications and per-map hashes are in each look's manifest and `assets/LICENSES.md`.
