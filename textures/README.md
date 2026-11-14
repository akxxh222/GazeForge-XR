# Native GNM texture looks - Milestone 2

Five draft looks contain 4096x4096 skin base-color, roughness and 16-bit height maps, plus distinct 2048x2048 left/right eye base-color and 16-bit height maps. `skin_coverage.png` records the native skin UV coverage. All files use the original GNM Head 3.0 per-region UVs, with separate materials for skin and each eye.

The albedo sources are CC0 MakeHuman maps, spatially transferred onto GNM. They are 2K full-body source images; a 4K export does not increase their original facial detail. Fine pores/roughness and iris/sclera details are authored separately. This is a work in progress toward the visual reference, rather than a completed photorealism claim.

## Rebuild

Run from the project root with Python dependencies in `requirements.txt`, the GNM download and CC0 skin sources available:

```powershell
& ./scripts/fetch_gnm.ps1
& ./scripts/fetch_skin_sources.ps1
& 'E:\Apps\blender.exe' --factory-startup -b --python-exit-code 1 --python scripts/build_gnm_baseline.py
& 'E:\Apps\blender.exe' --factory-startup -b --python-exit-code 1 --python scripts/prepare_gnm_skin_transfer.py
python scripts/make_gnm_texture_looks.py
& 'E:\Apps\blender.exe' --factory-startup -b --python-exit-code 1 --python scripts/build_gnm_look.py -- --look look_01 --views front,macro,macro_left,macro_right,eye_closeup,side_left,side_right
```

The transfer uses the preserved CC0 `assets/mpfb_head.json.gz` as a source surface, fits a temporary copy to geometric landmarks and projects source UVs. The GNM target geometry and its UVs are unchanged. Visible orbital skin is sampled from front-facing source surfaces to avoid transferring inner-socket atlas colors onto the lids. `assets/gnm/skin_transfer.json` records distances and local source-seam handling.

The map generator also feathers color across paired native UV cut edges through `scripts/gnm_texture_seams.py`. Each look's manifest records dense edge sample counts and before/after measurements. Painted scalp patterns are blended toward continuous skin, and the lip tint is restrained. These are authored corrections to the transferred images; they do not add photographic source detail or change the native UV layout.

Repeat the final command with `look_02` through `look_05`, or run `python scripts/render_gnm_looks.py --blender 'E:\Apps\blender.exe'` to rebuild the entire current preview set sequentially. `wrapper.materials.apply_look('look_01')` applies the exported images directly to a fresh native baseline without the source surface or transfer UVs. Seven material images are packed in each generated `work/gnm/scene_look_XX_realism.blend`. The earlier `scene_look_XX.blend` scenes are preserved.

```powershell
python scripts/audit_gnm_textures.py
& 'E:\Apps\blender.exe' --factory-startup -b --python-exit-code 1 --python scripts/validate_gnm_materials.py
python scripts/audit_gnm_renders.py
& 'E:\Apps\blender.exe' --factory-startup -b --python-exit-code 1 --python scripts/validate_gnm_groom.py
python scripts/make_gnm_material_sheet.py
```

## Evidence and remaining work

`tests/milestone2/texture_audit.json` checks hashes, dimensions, bit depth, distinct maps and source licenses, and reports native UV seam color measurements. `portability_report.json` checks each look on an independently reloaded baseline. Engineering passes do not certify photographic realism.

Static brows, lashes and tear menisci support material review. Their deformation-aware binding and lid animation belong to Milestone 3. Macro and side cameras are additional review views; the saved scene restores the locked 40 cm render camera and neutral gaze.

Current pupil metadata describes the geometric aperture centroid projected through the pinhole camera. Refraction can shift the apparent rendered pupil; these quantities are not asserted equal.

Remaining visual issues and rejected drafts are recorded in `tests/milestone2/REVIEW.md`. This checkpoint preserves the texture/material drafts; Milestone 2 remains in progress until its visual acceptance gates pass. Source authors, modifications and per-map hashes are in each look's manifest and `assets/LICENSES.md`.


## Scan-detail and iris refinement

The current authoring pipeline combines the CC0 diffuse sources with attributed 4K skin-detail bands from the Lee Perry-Smith scan. The scan is registered in frontal target-world coordinates and fades smoothly toward the scalp, neck and sides. Its detail is baked into native-UV color, roughness and 16-bit height maps; no source mesh replaces or deforms GNM. `assets/skin_detail/README.md` documents the CC BY attribution and the 8-bit source limitation.

The original iris plate in `assets/iris/` is AI-authored appearance data. Its pupil/limbus are measured in source pixels and registered to the native GNM annulus, with deterministic L/R rotations and five color treatments. `PROMPT.md` and the manifest preserve origin and registration. It is not a photograph or biometric ground truth.

Brows, lashes and subtle facial fuzz use native hair curves and strand scattering; iris and sclera use separate materials under the refractive shell. The current refinement adds an original 64,000-strand short swept-back scalp groom and sparse shaved stubble. Roots are sampled by surface area, anatomical ear membership excludes ear hairs, and the sides/irregular hairline taper naturally. Hair is independently authored code, with no additional downloaded asset or license. Rigid scalp parenting follows the head object; expression-deformation binding remains Milestone 3 work.

The default review quality is 256 Cycles samples, with 128-sample denoised viewport previews. The fill light is raised so its large reflection moves above the pupil, and the native cornea retains refraction and a restrained window catchlight. Both refractive and reflective caustics remain enabled: switching refraction caustics off incorrectly darkens the eye interior in this layered scene. The saved UI uses Material Preview, camera framing and hidden overlays; press **F12** for the actual Cycles result. In this Blender build, the saved Rendered viewport reopened as Solid during validation; Material Preview persisted and is used for startup. Strand pigment/roughness variation uses Blender's [Principled Hair BSDF](https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/hair_principled.html).

The provided source files make the downstream build deterministic without another image-generation call. Preserve both CC0 diffuse-source credits and the scan's CC BY attribution with skin-map derivatives.
