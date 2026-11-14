# GazeForge XR: five milestones toward photorealistic eye animation

Plan date: 2026-11-14. Confirmed team name and submission identifier: `VITChennai_IrisX`.

## Decision and present status

Continue from the existing working files. Reuse the calibrated binocular controller, camera/projection mathematics, deterministic inputs, background execution and packaging approach after checking them against the new head. Rebuild the visual assets, native UV pipeline, eyelid/expression rig and continuously rendered animation.

The existing MPFB scene is a **legacy engineering prototype**. Its 43 passing checks demonstrate that prototype's geometry and automation. They do not demonstrate photorealism, GNM/FLAME texture compatibility or completion of the new evaluation. Existing ZIP, images, slides and demo remain legacy outputs until replaced and revalidated.

The requested Git restart removes the single local root commit `0adb2a2` from active history while retaining working files and a recovery bundle in ignored `backup/`. The new history begins with the validated milestone 1 checkpoint `5738394`. Keep the original creation/provenance of reused code explicit.

| Milestone | Main outcome | Status |
|---|---|---|
| 1 | Verified requirements, native GNM/FLAME head/UVs and calibrated foundation | Complete: committed `5738394` |
| 2 | Photorealistic skin and layered eyes, with 5-10 portable texture looks | In progress: five native-UV looks; visual refinement pending |
| 3 | Natural eyelid, gaze and eyebrow articulation saved on the Blender timeline | Complete: articulation checkpoint committed `b353ece` |
| 4 | Modular controls and three continuously rendered expression videos | Planned |
| 5 | Visual review, texture/image export and reproducible final submission | Planned |

The current user instruction authorizes completing Milestone 3 articulation alongside the remaining Milestone 2 static appearance work. Its rig acceptance is separate from reference-level photorealism; both gates remain required before final delivery. Record actual evidence, remaining defects and the resulting commit hash under each stage. A written plan or an automated test count does not complete a visual milestone.

## Requirements and reference evidence

### Primary evaluation deck

Source: user-supplied `Evaluation_for_SyntheticEyes.pptx`, two slides, read on 2026-11-14.

Source SHA-256: `6b7e4e1600789543706275ca3b9074068a815898ed6ad742373d5a9657c2da37`.

The deck specifies **texture photorealism 60 points, kinematic accuracy 20 points, and code/UV portability 20 points**. It calls for:

- High-frequency skin and iris detail, natural colors and a seam-free realistic face.
- GNM or FLAME UV maps only, with textures directly applicable to the target head. The appendix explicitly refers to wrapping textures onto a GNM head.
- A collection of 5-10 UV texture variants covering face and eyes, and 5-10 rendered images with different textures.
- Coordinated eye rotation and realistic eyelid closure, natural expressions and eyebrow/iris animation where appropriate.
- A modular Python wrapper accepting **Left**, **Right** and **Generate Motion**, rendering frames and creating videos.
- Three actual runtime-rendered videos, one for each input, **each at most 15 seconds**.
- A `.blend` scene with expression animation present on Blender's timeline.

Plan for five complete texture looks first, expanding toward ten only after the first five pass review. Multiple PBR channels of one look do not count as multiple texture variants. Confirm whether the evaluator expects a combined face/eye atlas or separate native eye-material images when the target template is acquired.

### Earlier Track 01 constraints retained for compatibility

The supplied screenshots and earlier organizer material also require two spherical eyeballs rotating about their physical centers, left/right eye bones, deterministic `eyes.move(h,v)`, `eyes.reset()` and `eyes.render()`, a target 0.35 m forward of the eye midpoint, a locked camera 0.40 m forward, constant lighting and 1024x1024 PNGs. Retain the documented +/-0.05 m target-plane bounds.

Preserve the ten official samples `theta=2*pi*k/10`, `h=sin(theta)`, `v=cos(theta)`, starting at top and moving clockwise. Export true world eye rotations, actual 3D pupil positions, their camera projections and the camera matrix. Keep `scene.blend`, `wrapper/eyes.py`, `renders/`, `metadata.json` and `README.md` at the submission ZIP root.

The older 20/20/40/20 scoring and the new 60/20/20 rubric are different evaluation schemes. Use the attached deck as the current visual/UV target and preserve compatible older constraints. Do not combine the weights into an invented score.

The attached deck says **October 28, 2026**, while the earlier general material says **November 18, 2026**. The attached date is already past on the plan date. The actual deadline and the controlling rubric need organizer confirmation; neither is silently rewritten here. This plan uses dependency gates rather than an invented schedule.

### Video reference and scope of evidence

Primary visual reference: Chris Jones, [Eye Piece](https://www.youtube.com/watch?v=TAZIvyAJfeM), including the user-linked 00:46 section. The authorized vidIQ full-video analysis completed in this chat using 25 credits. Its reported observations include:

- 00:00-00:03: eyelid opening/blink, lid folds and eyelashes.
- 00:04-00:13: gaze changes, detailed iris, wet corneal highlights and scleral variation.
- 00:14-00:22: surrounding skin detail, wrinkles and brow hairs during a pullback.
- 00:23-00:37: topology, control and shaded anatomical views.
- 00:38-00:46: detailed eye anatomy/wireframe views around the linked timestamp.

These are the analysis service's reported observations. They do not establish the creator's exact shader nodes, layer count, numerical optical settings or modeling method. The report's final detailed interval ends at 00:46; it is not a verified shot-by-shot transcript of any later interval. Do not invent additional timestamp observations.

Use the reference for material depth, eye/eyelid interaction, fine skin/hair detail and continuous expression quality. Build an original reproducible scene. The reference's camera pullbacks and changing presentation views do not replace the required fixed calibrated camera in submitted dataset renders.

The new deck also links [a second reference](https://youtu.be/gh6WbaYzwFc). It has not been analyzed in this chat. Record that gap rather than claiming it was watched; additional paid video analysis requires separate authorization.

### Human Progress rigging reference

The user also supplied [Human Progress, post 76](https://blenderartists.org/t/human-progress/1143224/76). The adjacent artist explanation in post 74 informs milestone 3's independently authored lid rig. See [the reference review](docs/HUMAN_PROGRESS_REFERENCE.md) for source scope, the implementation choices and asset exclusions. Keep the GNM/FLAME native-UV requirement and calibrated capture contract. The published Universal Human asset license does not cover the editable asset redistribution required by this plan, so those commercial assets are excluded.

## Milestone 1: native model, UV contract and calibrated foundation

**Goal:** establish a suitable native head and a trustworthy technical base for the visual rebuild.

Work:

- Preserve the prototype, original human asset, previous reports and old Git history as recoverable local backups.
- Acquire/identify the actual GNM target head and its native UV template. FLAME is an alternative allowed by the deck, with GNM compatibility addressed explicitly. Update 2026-11-14: official GNM Head 3.0 acquired and imported; the earlier MPFB derivative remains a separate legacy prototype.
- Verify the selected asset's source, license, redistribution conditions, topology, UV layer, eye materials and texture conventions. Save model/UV identifiers and hashes. Resolve asset access before claiming portability.
- Implement an import/configuration layer for model scale, eye centers and eye bones. Reuse sound gaze mathematics without retaining MPFB-only mesh/UV assumptions.
- Establish separate rigid spherical globes and bone pivots, with optical layers sharing the same eye transform. Calibrate units, camera, common fixation point and input directions against the new head.
- Measure a short Cycles/GPU render benchmark before selecting final quality settings and video frame counts.

Evidence and acceptance gate:

- The actual target head loads headlessly. A native UV checker renders without altered UVs or stretched eyes/face regions.
- Source/license and UV/topology manifests exist. Applying an MPFB texture to an unchanged GNM/FLAME UV layout is not presented as a completed transfer.
- Sphere/pivot, 0.35/0.40 m calibration, convergence, deterministic reset and five-direction checks pass on the new asset.
- Save a neutral draft, diagnostic eye crops, the measured benchmark and a baseline test report. Mark visual quality as draft.

Suggested coherent commit: `feat: establish native-UV head and calibrated gaze baseline`.

Completion evidence (2026-11-14): official Apache-2.0 GNM Head 3.0 downloaded and checked against Google's published SHA-256. Pinned model/source revisions and licenses are in `assets/gnm/download_manifest.json`; native topology and UV hashes are in `assets/gnm/native_manifest.json`. The importer preserves 17,821 vertices and 17,662 quads across six components, with original per-region UVs and IDs.

`work/gnm/scene_baseline.blend` loads headlessly and retains the calibrated wrapper. `tests/milestone1/report.json` records **82 PASS / 0 FAIL** and actual GPU render timings; `tests/milestone1/contact_sheet.png` and `native_uv_checker.png` provide draft visual evidence. The final benchmark run measured approximately 12.46 seconds for the 1024x1024 neutral draft and 3.75-4.52 seconds for each 512x512 directional preview, at 32 Cycles samples on the RTX 3050. The local legacy `scene.blend` and old submission outputs are preserved.

The engineering baseline is validated. Photoreal textures, eyelid motion, full-head texture-seam review and refraction-aware image labels remain subsequent work. Commit: `57383941c815ed0c58ad58253ac350fab62954f3` - `feat: establish native-UV head and calibrated gaze baseline`. Reproduction: [GNM asset instructions](assets/gnm/README.md).

## Milestone 2: photorealistic texture looks and layered eye materials

**Goal:** achieve a convincing static eye close-up and compatible full-face texture looks before rendering long animations.

Current preview/lid correction (2026-11-14): **`work/review/lids/IRISX_LIDS_REVIEW.blend`** is the current static review. The earlier public-asset file showed black eye sockets in EEVEE Material Preview even though its Cycles render showed the iris. A separate transparent/specular EEVEE corneal output now preserves visible iris/sclera, while Cycles retains its original physical refraction. Supported EEVEE strand surfaces also avoid relying on Cycles-only hair scattering. The native head gains a bounded lid-margin/tarsal-fold shape key (772 vertices; maximum depth offset 0.5624 mm), finer waterlines, small canthal tissue and shorter irregular lash bundles. Native Basis geometry, UVs and topology remain unchanged.

Three actual 128-sample previews (Cycles eye/front and EEVEE eye) completed. `tests/milestone2/lid_review/report.json` records **41 PASS / 0 FAIL**, including EEVEE iris-color probes, native data equality, separate engine outputs, all replacement lash roots (maximum surface distance 0.0347 mm), camera/target calibration and deterministic gaze reset. The corrected file was opened in the live Blender session, where both irises were visible. This fixes the reported preview defect; broad source detail, seams and reference-level visual acceptance remain open. It does not complete Milestone 2, and the changes are preserved in task-specific checkpoint commits.

Latest user-requested asset replacement review (2026-11-14): the previous hair/eye appearance was not accepted. Downloaded Daniel Bystedt's official Hair Styles file and Splash Fox eye shader. Fitted 47,251 authored scalp curves to GNM, retained their clumping/flow, trimmed to a short adult cut and installed a dark Huang/melanin material with restrained scattering. Adapted the iris color network to native GNM UVs, round masks and a hazel palette without fox emission. Added a radial pupil-constriction shape key while retaining the original Basis vertices and UVs, and reduced excessive skin bump. The selected candidate is **`work/review/cyberpunk/IRISX_ASSET_REVIEW.blend`**, with three actual 256-sample Cycles review images beside it. Reopened checks pass **46 / 46**, including native geometry/UVs, pupil centroids, camera/target calibration, direction/reset and sampled groom fit.

The imported iris is CC BY-SA 3.0; the hair source says CC BY-SA without a version. Source hashes, notices, the license-version gap and reproduction steps are in [the public-asset review](assets/public_candidates/README.md). Hair derivatives remain a local review candidate until that version is resolved for final redistribution. Two additional CC0 MakeHuman eye maps are downloaded fallbacks and are not used in the chosen render. Just An Eye is currently unavailable for sale/download; no buyer email was submitted. This is one separate static candidate, not five accepted looks or a completed submission. Prior five-look pass counts below describe the preceding scene revision. Reference-level realism, lid/canthus and brow/lash detail, seams and visual acceptance remain open. This historical static revision predates the Milestone 3 blink prototype. This asset review is now preserved in its own checkpoint commit.

Started 2026-11-14: the official MakeHuman Skins 02 CC0 pack has been downloaded, ZIP-integrity checked and inspected. Its embedded per-material author/license catalog and file hashes are preserved in `assets/source_skins/manifest.json`. Five source candidates are in `assets/source_skins/selection.json`. The 2048x2048 full-body source maps need transfer onto GNM UVs and do not supply additional facial detail merely by exporting them at 4K. The transfer and material draft implementation is recorded below; seam repair and fine-detail refinement remain pending.

Implementation update: five 4096x4096 native-UV skin looks are now exported in `textures/look_01` through `look_05`, with roughness/16-bit height maps and separate 2048x2048 left/right iris-sclera maps. The source surface is temporarily aligned and projected; the target GNM geometry and UVs are unchanged. `wrapper/materials.py` applies each look directly, while `wrapper/appearance.py` supplies static brows, lashes and tear menisci. The first bruised-eye source and inner-socket projection draft were rejected and corrected.

Engineering evidence: **133 texture/source checks and 80 fresh-scene portability checks pass, with zero failures**. Another 70 checks validate 15 actual render files and their texture/appearance metadata. Rendered scenes are saved as `work/gnm/scene_look_XX.blend`; actual material review images are under `tests/milestone2/look_XX/`, with a five-look comparison in `tests/milestone2/contact_sheet.png`. See [texture reproduction instructions](textures/README.md) and [the visual defect/review ledger](tests/milestone2/REVIEW.md).

Status remains **in progress**. Source facial resolution, seam/color continuity, natural skin detail and fine-hair/eye integration still need visual acceptance. The engineering pass counts do not establish reference-level photorealism. This checkpoint records the Milestone 2 implementation and review evidence without declaring the stage complete.

Checkpoint commit: `bef6cbe` - `feat: add milestone 2 native-UV texture and eye material drafts`. Subsequent static refinement adds dense paired-edge color correction, source scalp-pattern blending, restrained lip color, reduced bump amplitude and revised iris/lash detail. The original checkpoint evidence is retained locally. The static visual gate remains open; committing the engineering draft did not complete it. The current instruction separately authorizes finishing the articulation checkpoint, while final visual delivery still requires Milestone 2 acceptance.

Earlier skin/eye refinement: attributed 4K scan-detail bands and an original annulus-registered AI iris plate complement the five CC0 diffuse sources. Brows, lashes and facial fuzz use native hair strands. Its 15 actual 128-sample previews passed 133 texture/source, 80 portability and 70 render/metadata checks. `tests/milestone2/realism_comparison.png` shows that revision before/after, and `realism_refinement.json` records its limits and source provenance.

Current user-review follow-up: the eye's broad fill-light reflection is moved above the pupil, interior highlights/micro-bump are reduced, and denoised preview sampling is enabled. An original 64,000-strand swept-back scalp groom and 9,530 short stubble strands give the static adult portrait a complete hairstyle. Native anatomical ear exclusion and tapered sides replace a rejected bare-temple draft. All five new packed scenes are saved separately as `work/gnm/scene_look_XX_realism.blend`, with camera framing, Material Preview and hidden overlays; F12 provides the actual Cycles result.

All 15 actual 256-sample review renders regenerated in 704.14 seconds. Current validation passes **133 texture/source + 80 portability + 70 render/provenance + 105 reopened-scene/groom checks**, zero failures. The new groom checks measure sampled scalp clearance and confirm unchanged native geometry/UVs, camera/target calibration and reset. See `tests/milestone2/groom_comparison.png`, `groom_refinement.json`, `groom_report.json` and the updated `REVIEW.md`. This static Milestone 2 work is preserved in a task-specific checkpoint commit. Final reference-level visual/seam acceptance is open. This historical static revision predates the Milestone 3 blink prototype.

Refinement validation (2026-11-14): all five revised looks and 15 preview renders regenerated, with 117 texture / 80 portability / 70 render-metadata checks passing. The sampled cut-edge color metric improves by 79.8-85.4% versus the checkpoint, while nonzero residual differences and visible source-detail/eye-surface limitations remain. See `tests/milestone2/refinement_review.json` and the updated contact sheet. These refinements are preserved in task-specific checkpoint commits. The static visual gate is still open; no Milestone 3 animation implementation is claimed.

Work:

- Author or source licensed high-detail skin maps for the selected native UV layout. Transfer/bake across models only through an explicit validated UV workflow.
- Produce five distinct texture looks covering face and eyes, with room to expand to ten. Keep diffuse/base color, normal/displacement, roughness and optional masks organized per look.
- Starting quality targets are 4096x4096 facial color maps and 2048x2048 distinct left/right iris maps, with suitable higher-precision height data. These are project choices, not resolutions quoted from the deck; adjust only with recorded quality/memory evidence.
- Build iris depth, radial detail, pupil aperture and limbal transition, natural scleral shading/veins and a reflective transparent corneal surface. Keep the spherical globe/pivot contract intact while adding anatomical optical layers.
- Add restrained skin color variation, pores, wrinkles, tear-line/corner detail and fine hairs. Avoid baking lighting into diffuse maps.
- Set balanced, constant lighting for the calibrated views, with readable iris detail and controlled highlights.

Evidence and acceptance gate:

- Render neutral, left and right macro views plus a full-face view. Inspect iris depth, wet highlights, color, skin detail and eye/socket integration against the reference cues.
- Review seams at UV borders, lids, canthi, ears and neck, including views that expose those borders.
- Export per-look maps and a manifest. Apply them directly to a fresh target head with its original UVs and save the result as portability evidence.
- Record optical-label semantics: a refractive cornea may shift the apparent pupil image. Preserve required geometric projections and distinguish any separately measured apparent centers. Do not claim a pinhole projection automatically equals a refracted visible centroid.
- Save visible defects and resolve them before declaring the stage complete. Increasing render samples alone is not visual evidence of completion.

Suggested coherent commit: `feat: add native-UV photoreal skin and layered eye materials`.

Completion evidence / commit: pending.

## Milestone 3: natural eyelids and expression rig

**Goal:** make the surrounding anatomy respond naturally to eye motion and blinking.

Development started after the preview/lid correction. `scripts/prepare_gnm_blink_shapes.py` reads the pinned official GNM semantic decoder as data through allowlisted Dense/ReLU operations, using zero latent and wink classes 13/14. It isolates the corresponding 100 native eye-region components and exports deterministic left/right deltas in `work/gnm/blink_shapes.npz`, with source/artifact hashes. These GNM derivatives retain Apache-2.0. `wrapper/lids.py` provides normalized left/right opening controls and reset. `scripts/build_gnm_blink_prototype.py` is the working authoring path for native shape keys, barycentric lash/brow/waterline attachments and an editable 72-frame blink action. This paragraph describes the initial prototype; the completed articulation checkpoint below supersedes its motion limits. The wider Milestone 2 reference-level appearance gate remains open for final delivery.

Work:

- Rig upper/lower lids with continuous open/partial/closed controls and appropriate gaze following. Use actual geometry, bones and/or shape keys while preserving the head's native UVs.
- Apply the Human Progress reference through independent controls and intermediate closure poses. Tune lid follow on the selected head; verify the current Blender animation workflow instead of copying historical editor workarounds.
- Keep lids wrapping around the corneal/globe surface without clipping, detached corners or stretched texture seams.
- Add plausible blink timing, eyelashes and restrained eyebrow expression. Expose iris/pupil controls if used, with fixed defaults for calibrated dataset captures.
- Expose supported identity/expression parameters modularly. Recalibrate eyes and labels when identity deformation changes eye centers.
- Save left, right and generated-expression actions/keyframes on the Blender timeline. A background script must reproduce the same actions without GUI selection state.
- Reset eyes, lids, brows and any pupil controls deterministically.

Evidence and acceptance gate:

- Review fully open, partly closed and closed lid poses, plus left/right/up/down gaze and a short blink preview.
- Inspect intermediate closure frames at combined gaze extremes, not only the endpoint poses. Save evidence of corneal clearance, stable canthi and continuous skin detail.
- Check eye-center invariance, synchronous binocular intent, convergence, reset and eye/lid intersections over the animated range.
- Inspect native textures during deformation for eyelid/corner stretching and seams.
- Confirm timeline actions are present after reopening the `.blend`, and that the same input yields the same transforms.

Suggested coherent commit: `feat: rig natural eyelid and eye-expression motion`.

Completion evidence: the final checkpoint below is accepted. Commit: `b353ece` - `feat: complete native eyelid and expression articulation rig`.

Blink checkpoint (2026-11-14): **`work/milestone3/IRISX_BLINK_PROTOTYPE.blend`** saves two editable bilateral blinks at 24 fps with independent opening controls. The initial semantic wink left a visible gap; explicit endpoint gains of 1.16 (L) / 1.21 (R) close it in the neutral frontal review. Four actual 64-sample Cycles images show open, half, closed and closed full-face views. The reopened prototype passes **58 checks**, including unchanged native Basis/UVs/topology, timeline interpolation/reset, fixed eye centers, simple drivers with autoexec disabled, and all 207 lash roots within 0.035 mm of the moving head at five sampled openings. A frontal 81x81 ray grid per eye reports zero visible eye samples at full closure; this is sampled visibility evidence, not continuous collision certification. Pose changes were inspected on Blender's live timeline. [The motion evidence ledger](tests/milestone3/README.md) records commands and remaining defects. Gaze following, combined-gaze intermediate clearance, self-intersection and texture-stretch review remain open. This prototype is preserved in a task-specific checkpoint commit and does not complete Milestone 3.

Gaze-follow/brow follow-up (2026-11-14): `work/milestone3/gaze_lids/IRISX_GAZE_LIDS_RIG.blend` adds separate vertical lid-follow and brow keys, a bounded ocular-depth correction, generalized detail attachments and exact common-target aim between timeline keys. Three editable actions span 144 frames at 24 fps. The reopened audit passes **591 checks**, including 45 combined gaze/opening poses, 1,447 attachment roots within 0.10 mm, sampled closure at nine gazes and eye-center/aim preservation through all timeline frames. Six actual 1024px Cycles stills and a continuous six-second diagnostic provide review evidence; all 144 video frames decode at 24 fps with **17 video checks passing**. See [the current motion review](tests/milestone3/gaze_lids/README.md) for contact tolerances, face-area changes and remaining semantic-wink corner deformation. Continuous lid-volume/self-intersection and final visual/texture-stretch acceptance remain open. This historical intermediate checkpoint is included in `b353ece`; the final checkpoint below resolves its remaining articulation gates.

Completed articulation checkpoint (2026-11-14): **`work/milestone3/final/IRISX_MILESTONE3.blend`**. The final rig replaces the contracted semantic wink with post-subdivision relaxed lid mapping, depth-ordered native ocular clearance and live evaluated-surface detail binding. Independent lids/brows, pupil control/reset and three saved action bundles work without Python playback handlers. Original native Basis/UVs/topology and fixed eye centers are retained.

The reopened audit records **1313 PASS / 0 FAIL**: a nine-gaze/five-opening grid, exact skin/outer-eye triangle tests, complete lash/wet-margin/canthal point probes, all **432 integer action frames plus 105 blink subframes**, native face-connectivity/UV checks, controls and reset. Measured skin clearance is at least **0.1921 mm**, detail-point clearance **0.0529 mm**, attachment-root distance at most **0.1468 mm**, and evaluated canthal movement at most **0.0780 mm**. The same immutable scene's completed head-triangle measurements were reused when correcting an audit assertion that confused changed quad diagonals with changed polygon topology; fresh native polygon-connectivity checks pass. The report records this provenance.

Seven actual 1024px Cycles stills, three native-UV checker poses and a continuous six-second/144-frame diagnostic were reviewed. All **21 decoded-video checks pass**, including every raw-frame checksum/order, four gaze directions, two closures and neutral return. [Final evidence, controls and reproduction](tests/milestone3/final/README.md). These are bounded articulation and visual checks, not a continuous soft-body certificate or a photorealism score. Milestone 3 articulation is complete; Milestone 2 appearance, the three final expression videos and final packaging remain open. Completion files are committed in `b353ece`.

## Milestone 4: modular controls and continuous rendered sequences

**Goal:** implement the evaluator's three inputs and render actual changing 3D poses throughout each clip.

Work:

- Retain `eyes.move(h,v)`, `eyes.reset()` and `eyes.render()` for compatibility.
- Add an explicit eyelid-opening control and a sequence entry point supporting `left`, `right` and `generate_motion`, corresponding to the deck's Left, Right and Generate Motion inputs.
- Use a controlled center-to-left expression, mirrored right expression and a natural generated scan/upward glance with coordinated lids/brows. Include realistic settles/blinks where appropriate without changing the calibrated camera or lighting.
- A proposed sequence API is `render_expression(mode, texture_id, duration_s=10, fps=24, output_dir=...)`. Final naming is an implementation choice, and its exact CLI must be documented and executed.
- Render the scene for each animation frame. Save raw frames, actions, timestamps and generation settings, then encode three MP4s. Use continuous 3D motion as the evidence for smoothness.
- Generate the ten original clockwise PNG samples under fixed settings, with visible pupils and the exact required ordering. Blinking in expression clips must not invalidate open-eye directional diagnostics.
- Export world rotations, 3D pupil centers, geometric 2D projections, camera data and optional visibility/apparent-center annotations. Adapt pixel checks to the new eye optics and highlights rather than assuming the prototype's black-pixel threshold remains valid.

Evidence and acceptance gate:

- Execute each of the three modes from the documented background command, with invalid inputs rejected clearly.
- Decode and inspect `left.mp4`, `right.mp4` and `generate_motion.mp4`. Each has changing rendered poses, correct direction, stable appearance and a measured duration greater than zero and no more than 15 seconds. The initial target is 10 seconds at 24 fps per clip.
- Save a frame-to-pose manifest and inspect temporal continuity, lid motion, flicker and intersections.
- Ten 1024x1024 official PNGs and finite, correctly ordered metadata pass the updated calibration/label checks. Report geometric and image-space evidence separately when corneal refraction makes them differ.

Suggested coherent commit: `feat: render expression modes and continuous gaze videos`.

Completion evidence / commit: pending.

## Milestone 5: final visual audit, portability and submission

**Goal:** deliver a visually convincing, portable and reproducible package meeting both the new evaluation and compatible Track 01 paths.

Work:

- Render 5-10 high-resolution images demonstrating distinct validated texture looks. Export the corresponding face/eye UV maps for direct target-model application.
- Review close-up and full-face renders for photographic color/detail, seams, flat irises, excessive scleral whiteness, eye/socket integration and hair/lid quality.
- Review all three clips for natural expressions, continuous motion, temporal stability and corneal/lid contact. Preserve the reference comparison and a defect-resolution record.
- Run fresh-model texture application tests and all required mathematical, control, render and metadata checks. Record actual runtimes and failures. Do not convert automated pass counts into a photorealism score or guaranteed jury marks.
- Pack images/materials into the scene as needed and also ship the portable UV texture files separately. Include model/texture provenance, licenses, dependencies and exact commands.
- Produce a labeled contact sheet and, if useful, an additional 1-2 minute explanatory demo. That overview is additional to the three required videos of at most 15 seconds each.
- Extract the final ZIP into a clean directory, open the packaged scene, execute all three modes and regenerate the official sequence. Verify dimensions, durations, metadata, UV compatibility and archive paths.

Expected final layout (supporting filenames may change before this stage):

```text
VITChennai_IrisX.zip
  scene.blend
  wrapper/eyes.py
  renders/frame_00.png ... frame_09.png
  metadata.json
  README.md
  textures/look_01/ ... look_05/ [up to look_10/]
  texture_preview_renders/
  videos/left.mp4
  videos/right.mp4
  videos/generate_motion.mp4
  scripts/
  tests/
  assets/LICENSES.md
```

Acceptance gate: every required file is present, all three short videos decode and meet the duration limit, 5-10 distinct texture looks/images pass visual and native-UV review, the timeline rig is usable, engineering checks pass, and the clean extracted run succeeds. List any unmet requirements explicitly instead of declaring them complete.

Suggested coherent commit: `release: package validated photoreal synthetic-eye submission`.

Completion evidence / commit: pending.

## Commit and evidence discipline

- Start the new history with real milestone 1 work, including this plan and provenance of reused prototype code. Do not re-add the entire legacy output set as another undifferentiated initial submission.
- Commit coherent changes as they are completed. The five milestone messages are checkpoints, not a requirement to hide useful smaller implementation/fix commits.
- Use current dates and truthful messages. Do not reconstruct or backdate a development history for work already completed.
- Keep source, small review evidence and asset/license manifests together. Keep reproducible caches, local backups and obsolete bulk renders outside active commits where appropriate. Choose how to version large authored `.blend`/texture assets before adding them.
- Update each milestone's status and evidence only after its acceptance gate passes. Preserve rejected visual drafts in local backups when useful.
- The old commit is removed from active local history only. The recovery bundle intentionally retains it. No remote is configured and no force push is needed.

## Open items before implementation

- Acquired/verified: official GNM Head 3.0 with original face/eye per-region UVs. Continue using that verified asset rather than the MPFB prototype for the new work.
- Use separate native face/left-eye/right-eye material maps for the first five looks; retain the original per-region UVs. Confirm any additional organizer-specific map-layout expectations before final delivery.
- Confirm the controlling rubric and deadline with the organizer.
- Add member details when supplied. Use the confirmed team name `VITChennai_IrisX` for the deck and submission ZIP.
- Review the second video if needed; no further vidIQ credit spending is authorized by this plan.

These items do not prevent writing the plan or retaining the useful calibrated code. Asset/UV compatibility must be resolved before claiming milestone 1 complete.
