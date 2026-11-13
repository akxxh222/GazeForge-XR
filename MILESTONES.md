# GazeForge XR: five milestones toward photorealistic eye animation

Plan date: 2026-11-14. Confirmed team name and submission identifier: `VITChennai_IrisX`.

## Decision and present status

Continue from the existing working files. Reuse the calibrated binocular controller, camera/projection mathematics, deterministic inputs, background execution and packaging approach after checking them against the new head. Rebuild the visual assets, native UV pipeline, eyelid/expression rig and continuously rendered animation.

The existing MPFB scene is a **legacy engineering prototype**. Its 43 passing checks demonstrate that prototype's geometry and automation. They do not demonstrate photorealism, GNM/FLAME texture compatibility or completion of the new evaluation. Existing ZIP, images, slides and demo remain legacy outputs until replaced and revalidated.

The requested Git restart removes the single local root commit `0adb2a2` from active history while retaining working files and a recovery bundle in ignored `backup/`. The new history starts with the validated milestone 1 baseline checkpoint. Keep the original creation/provenance of reused code explicit.

| Milestone | Main outcome | Status |
|---|---|---|
| 1 | Verified requirements, native GNM/FLAME head/UVs and calibrated foundation | Complete: baseline validated |
| 2 | Photorealistic skin and layered eyes, with 5-10 portable texture looks | Planned |
| 3 | Natural eyelid, gaze and eyebrow articulation saved on the Blender timeline | Planned |
| 4 | Modular controls and three continuously rendered expression videos | Planned |
| 5 | Visual review, texture/image export and reproducible final submission | Planned |

Complete stages in order. Record actual evidence, remaining defects and the resulting commit hash under each stage. A written plan or an automated test count does not complete a visual milestone.

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

The user also supplied [Human Progress, post 76](https://blenderartists.org/t/human-progress/1143224/76). The adjacent artist explanation in post 74 informs milestone 3's independently authored lid rig. Keep the GNM/FLAME native-UV requirement and calibrated capture contract. The published Universal Human asset license does not cover the editable asset redistribution required by this plan, so those commercial assets are excluded.

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

The engineering baseline is validated. Photoreal textures, eyelid motion, full-head texture-seam review and refraction-aware image labels remain subsequent work. Commit: this milestone 1 checkpoint, `feat: establish native-UV head and calibrated gaze baseline`. Its identifier is recorded by Git. Reproduction: [GNM asset instructions](assets/gnm/README.md).

## Milestone 2: photorealistic texture looks and layered eye materials

**Goal:** achieve a convincing static eye close-up and compatible full-face texture looks before rendering long animations.

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

Completion evidence / commit: pending.

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
