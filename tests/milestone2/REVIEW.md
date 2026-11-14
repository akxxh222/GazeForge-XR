# Milestone 2 visual review - in progress

Milestone 1 is committed as `5738394`. This checkpoint adds native-UV texture transfer, five PBR/eye looks and static facial detail. Milestone 2 remains in progress pending visual acceptance.

## Latest imported-asset review

**Current correction:** open `work/review/lids/IRISX_LIDS_REVIEW.blend`. This later revision fixes the EEVEE black-socket defect visible in the user's screenshot, preserves Cycles refraction, and adds a native lid-fold/margin sculpt, finer tear line/canthal detail and shorter clustered lashes. Its actual Cycles eye/front and EEVEE eye renders are beside the scene. `lid_review/report.json` records **41 PASS / 0 FAIL**, with native data equality, separate engine outputs, EEVEE iris visibility, lash-root fit and calibration/reset checks. The file has also been opened in the live Blender session with both irises visible in Material Preview. These checks establish the preview correction, not reference-level photorealism. The older public-asset revision below is retained as its parent.

The user did not accept the earlier eye/hair appearance. Open **`work/review/cyberpunk/IRISX_ASSET_REVIEW.blend`** and press **F12** for the latest separate candidate. It contains 47,251 scalp curves adapted from Daniel Bystedt's official Hair Styles demo, a modern dark melanin/Huang shader and a native-UV adaptation of his Splash Fox iris color network. The iris is round/hazel, source fox emission is removed, and a pupil-constriction shape key retains the native Basis geometry/UVs. The skin bump is reduced from the prior heavy close-up.

The front, eye and side previews are actual 256-sample Cycles renders beside the scene. `public_asset_review/report.json` records **46 PASS / 0 FAIL** after reopening, including every native component's UV/topology/Basis, pupil centroids, untouched exterior-eye geometry, source credits, packed textures, metric capture and direction/reset. Across 512 sampled strands, the maximum root distance is approximately 0.0301 mm and minimum sampled segment-center clearance is approximately 0.0296 mm. These are sampled geometry checks, not complete collision or visual certification.

See [asset provenance and reproduction](../../assets/public_candidates/README.md) from the repository root as `assets/public_candidates/README.md`. The adapted iris retains CC BY-SA 3.0; the hair source is CC BY-SA with the version unstated, a final-package issue still open. CC0 MakeHuman eye maps are downloaded alternatives but not used here. The unavailable Gumroad product was not obtained and no buyer email was submitted.

This candidate improves the eye pattern and scalp silhouette, but skin/source resolution, lid/canthus integration, lash/brow flow and full-head seams remain visible limitations. It does not yet match the Eye Piece reference. It has not replaced the five prior look scenes or submission ZIP. This historical static revision predates the Milestone 3 blink prototype. Subsequent changes are preserved in task-specific checkpoint commits. Earlier sections below describe the previous five-look revision.

## Current scalp-groom and eye-reflection follow-up

Open **`work/gnm/scene_look_01_realism.blend`** for the revised adult male portrait and press **F12** for the actual Cycles materials. The corresponding five look files use the `_realism.blend` suffix, preserving the earlier scenes. Camera framing, Material Preview and hidden rig overlays survive reopening; Rendered viewport mode reverted to Solid in this Blender build and is not relied on for startup.

The current pass adds an independently authored 64,000-strand swept-back scalp groom, tapered sides, an irregular sparse hairline, a narrow side part and 9,530 short shaved-stubble strands. Roots are area-sampled on evaluated GNM skin; native ear membership excludes ears without cutting a bare strip from the temple. The scalp object follows rigid head transforms; expression-deformation binding is still Milestone 3 work.

The fill light is raised so its broad corneal reflection moves above the pupil. The cornea retains refraction and a restrained window catchlight; reduced interior specularity and micro-bump avoid duplicate sparkling highlights. The final previews use 256 Cycles samples and denoising, with 128-sample denoised viewport previews. A rejected test with refractive caustics disabled produced dark eye interiors, so refractive/reflective caustics remain enabled.

All **15 actual 256-sample renders** regenerated successfully in **704.14 seconds**. Current reports pass **133 texture/source, 80 fresh-scene portability, 70 render/provenance and 105 saved-scene/groom checks**, zero failures. The saved-scene checks reopen all five files, preserve native head/eye UVs and topology, confirm calibration/reset, and measure 512 sampled scalp strands per file. Maximum sampled root distance is approximately 0.0351 mm; sampled interior clearance stays positive. These are engineering checks, not a visual realism score.

See [the actual before/after comparison](groom_comparison.png), [five-look sheet](contact_sheet.png), [refinement receipt](groom_refinement.json), [saved-scene checks](groom_report.json) and [render timings](render_runs.json). The older scan-detail comparison and receipts below describe earlier revisions. Broad source-color resolution, full-head seam acceptance, static lid/canthus integration and final reference-level visual acceptance remain open. That static refinement pass added no animation; its files are now checkpointed separately.

## Earlier scan-detail and iris refinement

The preceding revision added attributed 4096px scan microdetail, an original AI-authored iris plate registered to the native annulus, separate iris/sclera shading, and native Cycles hair strands for brows, lashes and subtle facial fuzz. Its fifteen 128-sample renders and **133 texture/source, 80 portability and 70 render/metadata checks** formed the baseline for the current follow-up.

`realism_comparison.png` compares the same eye/camera/gaze before and after this revision. `realism_refinement.json` records current source hashes, scope and remaining limits. The iris plate is appearance data, not a human photograph; its exact built-in generation prompt and registration are preserved in `assets/iris/`. The skin detail source is attributed in `assets/skin_detail/`; its 8-bit JPEG source and artist-selected bump amplitude are disclosed. Original source colors remain limited by the CC0 body maps.

These changes improve visible iris structure, capillaries and skin microstructure. Residual full-head side/ear/oral transitions and final reference-level visual acceptance remain open. Milestone 2 is still in progress; these changes do not claim an animated eyelid rig or measured apparent pupil centers. Changes after `bef6cbe` are preserved in task-specific checkpoint commits.

## Static refinement after the checkpoint

The initial implementation is committed as `bef6cbe`. The subsequent refinement preserves that checkpoint and its original render evidence in ignored `work/milestone2_before_static_refinement/`.

The texture generator now feathers paired native UV cut edges using dense samples of both sides of each shared 3D edge. This changes image colors only; target topology and UV coordinates remain unchanged. Per-look manifests record the method, sample count, feather width and before/after measurements. The generator also blends painted source scalp patterns toward a continuous skin tone and applies a restrained vermilion tint to reduce pale source-projection streaks. The scalp blend and source facial resolution still need visual acceptance.

Skin bump amplitude is reduced, iris fibers are less wavy, scleral variation extends closer to the iris, and upper/lower lashes have denser roots with individual curl and outward fanning. Review lighting is held constant across the five revised looks. These changes are static material/appearance work, not the Milestone 3 deformation or animation rig.

`scripts/audit_gnm_renders.py` checks the actual preview files against their current texture manifest, appearance code, shader code and render-builder hashes. It detects stale views after a partial re-render. See the current audit JSON files for the latest completed validation; a source edit or rebuild requires rerunning them.

Completed refinement review (2026-11-14): all five looks and 15 preview views were regenerated successfully. The current reports pass 117 texture checks, 80 fresh-scene portability checks and 70 render/metadata checks. At the same 426 sampled native cut-edge locations per look, the 95th-percentile RGB differences are 79.8-85.4% lower than the checkpoint. Residual maximum differences remain nonzero. `refinement_review.json` records the per-look comparison and remaining defects. The updated contact sheet and mature/deep skin macros were inspected; they still show limited source detail and an overly uniform scleral appearance. These refinements are preserved in task-specific checkpoint commits. This historical static revision predates the Milestone 3 blink prototype.

## Implemented and checked

- Five distinct 4K native-GNM skin looks, with separate 2K left/right eye maps and 16-bit height channels.
- Original target UVs and topology retained; source projection exists only in the offline authoring pipeline.
- Skin roughness/micro-bump and millimeter-scale subsurface shading; native iris/pupil/cornea geometry with refractive material; static brows, lashes and tear menisci.
- `texture_audit.json`: 133 passing file/source/map checks, zero failures. Native UV color discontinuity measurements are reported separately, with no invented visual score.
- `portability_report.json`: 80 passing checks, zero failures, applying all five looks to independently reloaded native baselines. No MakeHuman UV map is needed at application time.
- `render_audit.json`: 70 passing checks, zero failures, across 15 actual renders. Image dimensions, current texture/appearance provenance, finite labels and explicit refractive-label semantics are checked.
- `groom_report.json`: 105 passing checks, zero failures, reopening the five current packed scenes and measuring sampled hair fit, native geometry/UV preservation, camera/target calibration, reset and saved review UI.
- Actual fixed-camera front renders and macro material views. Look 01 also has left/right gaze macros, an individual-eye close-up and two side views. These are material previews, not the final required ten-frame sequence or videos.

## Corrected drafts

The first projection mapped inner-socket atlas colors onto visible lids. Orbital projection now uses front-facing source surfaces. The initial Aksel source also contains a bruised eye; it was replaced with the CC0 mature skin source for the neutral five-look set. The rejected frontal/macro images are retained in `rejected_projection_v1/`.

The first static lash fit used the transparent corneal silhouette, which placed some upper roots too high on the lid. The fit now uses the opaque eye aperture, and control points clear the skin surface. The final close-up shows continuous visible upper lashes; their flow and density still need artistic refinement before accepting static appearance.

## Remaining acceptance work

- Review and repair visible color discontinuities around UV cuts, ears, lid corners and neck. Quantitative seam differences remain nonzero; the map audit is not a seam-free certification.
- Improve natural skin detail and tone. The source facial pixels remain limited; broad scalp/temple tone transitions and stretched source detail remain visible in side views. Procedural detail does not replace the missing photographic information. Ear and oral joins also retain color differences.
- Refine upper lashes, brow flow/density, tear-film/canthus integration and iris/sclera appearance against the Eye Piece reference. Hair counts or render samples alone are not visual acceptance.
- Preserve geometric pupil labels and clearly separate any future measured apparent, refracted centers. The current scene declares this distinction; no apparent-center validation is claimed.
- Keep Milestone 2 in progress until static close-ups, full-face looks and seam reviews pass. Eyelid motion, blinking and animated hair attachments are subsequent Milestone 3 work.
