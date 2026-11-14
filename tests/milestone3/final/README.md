# Milestone 3 articulation checkpoint

Team: **VITChennai_IrisX**. Scene: `work/milestone3/final/IRISX_MILESTONE3.blend`.

Acceptance is recorded in `report.json`, `video_report.json` and the visual review below. Only reports whose scene hash matches `work/milestone3/final/rig.json` apply to this checkpoint. Earlier blink and gaze-lid prototypes are preserved separately.

## Open and control

Open the scene in Blender 5.2.3 LTS. The default timeline spans frames **1–144 at 24 fps**. Space plays a left/right/up/down scan, a restrained brow raise and blinks during upward/downward gaze. Frame 1 is neutral. The saved scene uses the calibrated camera; the render evidence also uses separate macro review cameras.

The `GNM_skin` shape keys `Blink.L` and `Blink.R` are normalized closure controls: 0 is open, 1 is closed. The post-subdivision Geometry Nodes modifier reads these values; their key coordinates deliberately equal Basis. `Brow.Raise.L/R` and gaze-follow keys remain separate. Leave the native eyelid modifier and detail-binding modifiers enabled.

From Blender's Python console, after adding the repository root to `sys.path`:

```python
from wrapper import expressions, eyes, lids

expressions.use_action('left')              # also 'right', 'generate_motion'
# Play the selected 144-frame action bundle.

with expressions.manual():
    eyes.move(0.6, 0.8)                     # normalized target-plane input
    lids.set_opening(0.5, 0.7)              # independent L/R openings
    expressions.set_brows(0.2, 0.4)
    expressions.set_pupil_constriction(0.7)
    eyes.render('work/manual_pose.png')
    expressions.reset()                    # neutral gaze, open lids, brows 0, pupils .7
```

The manual context temporarily detaches the three authored actions and restores their timeline/subframe pose on exit, including caller exceptions. Gaze/lid-follow/detail drivers stay active. Playback does not require running a downloaded script or registering a Python handler. Identity is the calibrated native checkpoint identity; arbitrary identity deformation is not exposed.

## What changed

The contracted semantic wink is replaced by an independently authored continuous, piecewise lid map after subdivision. It compresses the opening toward a curved closing seam while expanding the covering upper/lower lid tissue into the opening. The exterior transition tapers away from the margin and preserves a positive vertical derivative. Applying the map after subdivision avoids spline overshoot at the thin closing seam.

Two closed, watertight collision proxies use the original GNM `eye_exteriors` surfaces and share the native eye transforms. A smooth depth-ordering field follows their actual anterior surfaces. It preserves depth ordering rather than projecting different tissue layers onto the same coordinates. The nominal anterior allowance is 80 micrometers; measured clearances are in the report.

Lash/brow roots, tear film and wet margins sample the evaluated head through Geometry Nodes with stored barycentric coordinates. The small canthal tissues follow a native canthal surface anchor by translation; allowing its rapidly changing tangent frame to rotate them produced a rejected floating-bead artifact. Their rest geometry conforms to the curved native eye shell. A second shared depth-ordering field keeps complete bound detail points outside the live ocular shells, including diagonal gazes where fixed rest clearance proved insufficient. Outer joins carry barycentrically transferred native skin UVs; the nasal tissue uses a restrained mucosal material. Original head/eye Basis coordinates, UVs and topology are unchanged.

The opaque wet margin and canthal tissues are part of the rendered anatomy. The closure audit explicitly includes these meshes; the native skin alone can retain tiny canthal slits. This is not represented as a watertight welded native head mesh. Tissue-to-skin embedding and lid contact are intentional.

All three input modes have editable saved action bundles for the shape keys, eye rig and fixation target. Original materials, fixed eye pivots, common 35 cm target plane and 40 cm camera remain in place.

## Reproduce

The committed static lid review and blink prototype are the parents. Fetch the verified GNM NPZ if absent, then run from the repository root:

```powershell
& 'E:\Apps\blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python scripts/build_gaze_lid_rig.py
& 'E:\Apps\blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python scripts/build_milestone3_final.py
& 'E:\Apps\blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python scripts/validate_milestone3_final.py
$env:OPTIX_CACHE_PATH = Join-Path (Get-Location) 'tests/.optix_cache'
& 'E:\Apps\blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python scripts/render_milestone3_final.py -- --video
python scripts/validate_milestone3_video.py
```

`rig.json` records scene, source, builder and control-module hashes. The render receipt records individual still/frame hashes, pose state and runtime. The video contains **144 independently rendered 384×384 Cycles frames, 24 samples, 24 fps, six seconds**. The stills are **1024×1024 at 64 samples**; three additional native-UV checker poses use 32 samples. No interpolated stills or held-image animation substitutes are used.

## Acceptance scope and remaining project work

The geometry audit checks a nine-gaze/five-opening grid, raised-brow combinations, all 432 integer frames across the three saved actions, and quarter-frame samples through blink transitions. It measures the evaluated skin against the closed native outer eye surfaces, nonadjacent lid-triangle crossings, complete lash/canthal/wet-margin point clearance, attachment fit, native data equality, canthal movement, binocular aim, resets and invalid inputs. Exact skin/eye triangle crossing checks are also applied to the manual pose grid. Visible changed-face area distributions accompany native-UV checker renders; compression of hidden/contact tissue is reported separately from visible skin.

These are discrete geometric and visual acceptance checks. They do not certify every continuous real-valued pose, solve arbitrary eyelid soft-body contact, or guarantee photographic realism. The 30-micrometer contact threshold is stated in the report; it is not silently rounded away.

Milestone 2's reference-level skin/hair/eye material acceptance is a separate open gate. Milestone 4 still needs the general sequence wrapper, three final expression videos and official dataset renders/metadata. Milestone 5 still needs final five-look visual approval, portability/package validation and resolution of the hair source's unspecified CC BY-SA version before redistribution. Existing asset notices remain applicable; see `assets/LICENSES.md`.

## Completed acceptance (2026-11-14)

**1313 scene/control/motion checks and 21 video checks pass, zero failures.** All 45 gaze/opening poses, 432 integer action frames and 105 quarter-frame blink samples pass their stated gates. Minimum measured skin clearance: 0.1921 mm; complete detail-point clearance: 0.0529 mm; maximum attachment-root distance: 0.1468 mm; maximum evaluated canthal movement: 0.0780 mm. The video rendered in 821.62 seconds, and every frame decodes at 24 fps.

The closed-lid quads can change their rendering diagonals without changing native face connectivity. The audit now compares evaluated polygon-loop connectivity rather than equating a triangle-list change with a topology change. Completed head collision measurements from the identical scene were reused for that test correction; the final report records the cache hash and scope, while controls/details/canthi/connectivity and every action/subframe are freshly checked. The normal reproduction command above recomputes the full grid without that optional cache.

[Pose review](pose_sheet.png), [native-UV deformation](uv_sheet.png), [decoded directions](decoded_strip.png), [blink transitions](blink_strip.png) and `visual_review.json` record the inspected evidence. Open/partial/closed poses remain fitted, the curved closure covers the iris, and the checker remains continuous. A narrow contact band compresses strongly at closure; its minima and the full area distributions remain visible in `report.json`. Source skin/groom detail and simplified mucosal appearance remain Milestone 2 work, and no reference-level photorealism approval is claimed.

Milestone 3 articulation is complete. New completion files are uncommitted; the parent checkpoints remain preserved.
