# Milestone 4: completed expression and capture checkpoint

Completed **2026-11-15** for **VITChennai_IrisX**. Commit history is recorded in [the checkpoint ledger](../../docs/CHECKPOINTS.md). Historical JSON receipts retain their capture-time commit status. This accepts modular controls, continuous rendered expression sequences and the calibrated dataset. **Milestone 2 reference-level appearance and Milestone 5 final submission remain open.**

## Delivered media

| Input | Actual video | Frames / fps | Duration | Resolution |
|---|---|---|---|---|
| Left | [left.mp4](../../work/milestone4/capture/left/left.mp4) | 144 / 24 | 6 seconds | 720x720 |
| Right | [right.mp4](../../work/milestone4/capture/right/right.mp4) | 144 / 24 | 6 seconds | 720x720 |
| Generate Motion | [generate_motion.mp4](../../work/milestone4/capture/generate_motion/generate_motion.mp4) | 144 / 24 | 6 seconds | 720x720 |

Each frame evaluates and renders the 3D scene with Cycles at 64 samples. A held pose is rendered again on every frame. No intermediate motion is synthesized from stills. Six seconds preserves the accepted timeline's blink timing and meets the fifteen-second maximum.

The ten official [clockwise PNGs](../../work/milestone4/capture/clockwise/renders/) and [metadata.json](../../work/milestone4/capture/clockwise/metadata.json) use 1024x1024 output and 128 samples. They start at top and advance clockwise with `theta=2*pi*k/10`, `h=sin(theta)`, `v=cos(theta)`. Lids stay open, brows neutral and pupil constriction 0.7. Camera distance is 40 cm, fixation plane 35 cm forward, and target-plane motion is bounded by +/-5 cm. Camera, lighting and appearance stay fixed.

Source scene: `work/milestone3/final/IRISX_MILESTONE3.blend`, SHA-256 `fb808fedf7595e2d80fe2baaf7a5346172cc827d521b83e25be0f64d2ea497e8`. It remains unchanged and retains all three editable native action bundles. [Capture API and exact commands](../../docs/EXPRESSION_CAPTURE.md).

## Validation

- `controls.json`: **961 PASS / 0 FAIL**. Invalid numeric/mode/look inputs are rejected before scene/output mutation; all 432 default timeline poses, deterministic fractional evaluation, binocular aim, fixed centers, camera/lighting stability and five native look applications pass. Five applications are engineering evidence, not five newly accepted photoreal looks.
- `report.json`: **5419 PASS / 0 FAIL**. Every raw PNG checksum, all 432 decoded video frames, frame-to-pose ordering, dimensions, fps, duration, neutral return, blinks, geometric and actual pixel directions, held-pose stability, world Euler/quaternion agreement, rigid pupil motion, camera projection and all ten official samples pass.
- `fresh_environment_report.json`: the **same 5419 checks pass** in an isolated environment freshly installed from `requirements.txt`. `dependencies.json` records both tested environments and report hashes. This is a dependency compatibility check; clean extracted final-bundle execution remains Milestone 5.
- `metadata_export.json`: exact requested controls are retained within [-1,1], while separate `evaluated_input` values preserve Blender float32 rounding. The updated background CLI reuses all ten PNGs and reproduces identical finalized metadata/receipts. Original observed coordinates, rotations and projections are unchanged.
- `resume.json`: the original renderer stopped after eight scan frames. Exact-configuration resume verified and reused all eight PNGs, then completed the scan and official dataset. The cause of interruption is not inferred. The original incomplete auto-audit reported missing outputs; the completed audit supersedes it.
- `visual_review.json`: all 432 decoded frames were inspected on twelve time-ordered sheets, plus selected raw/full-face images and all ten official views. Bounded expression/capture review passes. It is not real-time playback observation or photorealism approval.

Maximum decoded/source compression MAE is **2.352 / 255**. Left, Right and Generate Motion have respectively **68, 66 and 119** changing adjacent decoded-frame pairs; intentional gaze holds remain stable. These numerical bounds support continuity review, rather than establishing realism by themselves.

The pupil labels are geometric aperture centroids and pinhole projections, not apparent refracted centroids. A separately recorded dark-component measurement from actual pixels confirms left/right/up/down direction and neutral return. Highlights and occlusion can bias it; it is not optical ground truth or a replacement for the geometric labels. Native anatomical L appears on image right.

## Review evidence and scope

[Left](left_decoded.png), [Right](right_decoded.png), [scan/blinks](generate_motion_decoded.png), [clockwise eyes](clockwise_eyes.png), [clockwise full faces](temporal/clockwise_faces.png). `temporal/index.json` binds the twelve all-frame sheets to their MP4/receipt hashes. Crops preserve aspect ratio and do not add detail.

Open-eye gaze changes retain readable colored irises. Bilateral blinks close and reopen without a visible exposed-globe flash at the delivered resolution. Camera, head, hair and lighting remain fixed. The scan includes an upward brow rise, blinks during upward/downward gaze and a neutral return. Full-resolution geometry/contact evidence belongs to the exact-source Milestone 3 audit; these video/image checks do not constitute a continuous collision certificate.

Source skin-color detail remains broad/soft in close views, and fine iris/lash/canthus integration still falls short of the Eye Piece reference. Five-look visual/UV export acceptance, full-head seam review and the source hair's unstated CC BY-SA version remain final-delivery work. The current local render checkpoint does not resolve those gates or certify a final ZIP.

`acceptance.json` binds the accepted reports, dependency/resume/visual evidence and deliverable manifest. `deliverables.json` lists the three MP4s, four frame-to-pose receipts, geometric metadata and ten official PNGs by size/hash. Raw animation PNGs and virtual-environment/cache data remain local reproducible files under ignored `work/`.

The initial two-frame neutral-endpoint CLI/encode smoke and its resume remain under `work/milestone4/smoke/`. That sparse diagnostic is not a deliverable: the earlier audit correctly rejected its absent motion, direction and blink evidence.
