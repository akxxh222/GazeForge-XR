# Checkpoint commits - 2026-11-14

These are truthful local progress checkpoints after `bef6cbe`, grouped by implementation task. The earlier checkpoints do not complete Milestone 2; the final rig checkpoint completes Milestone 3 articulation.

| Commit | Task | Included files/evidence |
|---|---|---|
| `4fa58fb` | Native-UV skin, layered eyes and static groom | Texture/seam/scan and groom code, source assets/notices, five-look maps, actual review renders and audits |
| `318da03` | Public iris and scalp-groom adaptation | Acquisition/fitting/inspection scripts, source manifests/credits, authored asset-review scene, selected renders and 46-check report |
| `41a90f8` | Material Preview and eyelid correction | EEVEE/Cycles surfaces, native lid anatomy and attachments, authored corrected scene, three renders and 41-check report |
| `b353ece` | Complete native lid/expression articulation | Gaze-follow foundation, relaxed lids, evaluated-surface bindings, three action bundles, authored scenes, 1313 rig and 21 final video checks |
| `a45d2e9` | Native blink rig and rendered preview | Pinned semantic weights/reference, decoder, controls/binding/timeline, authored scene and pose renders, MP4/receipts, 58 scene and 8 video checks |

The following documentation checkpoint consolidates current status, licenses, the Human Progress reference and these commit boundaries. Historical reports retain their original scene revisions and limits.

Selected authored scenes and final review receipts are explicitly versioned under `work/` despite the general cache exclusion. Downloaded source `.blend` files, old source/scene experiments, `.blend1` backups, OptiX caches, raw animation frames and unrelated legacy MPFB submission/deck/demo/packaging files remain local. The five older material/groom scenes can be regenerated from the committed code/maps; their review renders are tracked.

No remote is configured and no push is performed. Final reference-level realism, the final expression videos, submission validation and hair license-version resolution remain open. The later Milestone 3 articulation completion is documented below with discrete geometry/visual limits, rather than an unqualified continuous-collision certificate.

## Completed articulation checkpoint

`work/milestone3/final/IRISX_MILESTONE3.blend` completes the articulation checkpoint with relaxed native lids, evaluated-surface details, native ocular clearance and three saved action bundles. See [the final evidence](../tests/milestone3/final/README.md). This work is committed in `b353ece`; raw animation frames and intermediate caches remain local. Milestone 2 static reference-level appearance and the final submission remain open.
