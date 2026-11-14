# Eye refinement candidate evidence

2026-11-15, VITChennai_IrisX. Separate scene:
`work/review/eye_refinement/IRISX_EYE_REFINEMENT.blend`.

The selected geometry audit passes **111 checks, zero failures**. It reopens
the saved candidate and verifies native Basis/UV/topology equality, camera and
light calibration, packed CC0 iris source, fixed pivots/shared aim, original
action retention, and actual image receipts. Five cardinal/neutral gazes at
open/half/closed plus the original timeline frame 43 are checked for lid
triangle self-crossings, skin/eye point clearance, attachment fit and detailed
lash/canthal clearance. Sampled closure has no exposed eyes; the evaluated
closed head surface agrees with the original at all five tested gazes.

`report.json` contains the exact candidate SHA and fresh pose measurements.
These discrete samples do not certify every intermediate pose, every possible
control input, or reference-level photographic realism.

The first local audit compared unevaluated cached light matrices exactly and
reported two failures. After explicitly updating the dependency graph before
recording either scene's calibration, all four matrix differences are exactly
zero; light energies/colors/types/sizes also agree. The final audit reruns all
selected pose checks. The first report remains in the ignored review folder
as `first_audit_exact_matrix.json`; no scene adjustment was needed for this.

`media.json` passes **493 checks, zero failures**, including per-frame shared-target aim, fixed eye centers and bounds, and records the complete decoded-video/source-order audit. The
four-second review uses 96 independently rendered Cycles frames at 24 fps,
512 square and 32 samples. It is a close-up diagnostic with the extra
`natural_review` action, not an official dataset replacement. `all_frames.png`
shows every decoded frame in time order; `comparison.png` compares actual
1024-square/128-sample original-action neutral/frame-43 renders before/after.

The source MP4, PNG stills and receipt are in `work/review/eye_refinement/`.
Raw motion frames remain local render cache. The scene's original three
actions, 35 cm target plane, 40 cm RenderCamera and native eye pivots remain.

The user-reported visible alignment concern requires visual review. The new
iris and lid appearance are a candidate, not a declaration that M2 is complete.
Broad skin detail, brow/canthus polish, the five final looks and inherited hair
license-version resolution remain open. See
[implementation and reproduction notes](../../docs/EYE_REFINEMENT_REVIEW.md).

`visual_review.json` records the actual image/frame inspection and remaining defects. `manifest.json` binds the candidate, four stills, clip and evidence by SHA256. The original M3 scene hash is unchanged. Commit history is recorded in `docs/CHECKPOINTS.md`; JSON receipts retain creation-time status.
