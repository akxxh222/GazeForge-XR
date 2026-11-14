# Checkpoint commits - 2026-11-14 and 2026-11-15

These are truthful local progress checkpoints after `bef6cbe`, grouped by implementation task. The earlier checkpoints do not complete Milestone 2; the final rig checkpoint completes Milestone 3 articulation.

| Commit | Task | Included files/evidence |
|---|---|---|
| `d2420a0` | Complete M4 expression capture and calibrated dataset | Modular wrapper/CLI, three videos, ten PNGs/labels, verified resume and 961/5419-check evidence |
| `9db0bca` | Eye appearance and fixation review | CC0 iris, relaxed lids, separate candidate/clip, frame-43 diagnostics and 111/493-check evidence |
| `4fa58fb` | Native-UV skin, layered eyes and static groom | Texture/seam/scan and groom code, source assets/notices, five-look maps, actual review renders and audits |
| `318da03` | Public iris and scalp-groom adaptation | Acquisition/fitting/inspection scripts, source manifests/credits, authored asset-review scene, selected renders and 46-check report |
| `41a90f8` | Material Preview and eyelid correction | EEVEE/Cycles surfaces, native lid anatomy and attachments, authored corrected scene, three renders and 41-check report |
| `b353ece` | Complete native lid/expression articulation | Gaze-follow foundation, relaxed lids, evaluated-surface bindings, three action bundles, authored scenes, 1313 rig and 21 final video checks |
| `a45d2e9` | Native blink rig and rendered preview | Pinned semantic weights/reference, decoder, controls/binding/timeline, authored scene and pose renders, MP4/receipts, 58 scene and 8 video checks |

The following documentation checkpoint consolidates current status, licenses, the Human Progress reference and these commit boundaries. Historical reports retain their original scene revisions and limits.

Selected authored scenes and final review receipts are explicitly versioned under `work/` despite the general cache exclusion. Downloaded source `.blend` files, old source/scene experiments, `.blend1` backups, OptiX caches, raw animation frames and unrelated legacy MPFB submission/deck/demo/packaging files remain local. The five older material/groom scenes can be regenerated from the committed code/maps; their review renders are tracked.

No remote is configured and no push is performed. Final reference-level realism, submission validation and hair license-version resolution remain open. Milestone 4 supplies the validated expression videos below. The later Milestone 3 articulation completion is documented below with discrete geometry/visual limits, rather than an unqualified continuous-collision certificate.

## Completed articulation checkpoint

`work/milestone3/final/IRISX_MILESTONE3.blend` completes the articulation checkpoint with relaxed native lids, evaluated-surface details, native ocular clearance and three saved action bundles. See [the final evidence](../tests/milestone3/final/README.md). This work is committed in `b353ece`; raw animation frames and intermediate caches remain local. Milestone 2 static reference-level appearance and the final submission remain open.

## Milestone 4 completion

Completed 2026-11-15: three six-second/720px actual expression videos, ten 1024px clockwise PNGs and geometric labels. The modular wrapper, verified interruption/resume, 961 control checks, 5419 capture checks in two Python environments and bounded visual review are recorded in [the M4 evidence](../tests/milestone4/README.md). Implementation, selected renders and evidence are committed in `d2420a0`; legacy MPFB/deck/packaging files remain outside this work. Milestone 2 reference-level appearance, the hair license-version question and final submission remain open.

## Eye appearance follow-up

The 2026-11-15 candidate in `work/review/eye_refinement/` preserves the M3/M4 checkpoints and calibration. It introduces a packed CC0 iris, subtle relaxed lid rest and a separate authored fixation/hold demo. [Review notes](EYE_REFINEMENT_REVIEW.md) distinguish geometric coupling from the user's still-open visible alignment concern. This visual refinement checkpoint is committed in `9db0bca`. It does not establish final-submission or reference-level realism acceptance.

## Commit scope and retained local files

The `d2420a0` commit contains only M4 source, capture documentation, dependencies, selected validated media and evidence. The `9db0bca` commit contains only eye appearance/motion source, CC0 iris provenance, the separate candidate, diagnostics, selected media and evidence. This documentation checkpoint records both completed commit boundaries. Immutable JSON receipts retain the commit status observed when the evidence was created; this ledger records current history.

Raw animation frames, intermediate `tests/milestone4/progress.json`, logs, caches, the isolated dependency environment and unrelated legacy MPFB submission/deck/demo/packaging files remain local. No remote push is performed. Milestone 2 visual acceptance, the inherited hair license-version question and Milestone 5 remain open.
