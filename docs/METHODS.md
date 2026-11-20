# Rig and dataset notes

## Eye motion

We use the original GNM face and its per-region UV layout. The two eyeballs have separate fixed pivots. A shared target is placed at `(0.05*h, -0.35, 0.05*v)` relative to the eye midpoint. Each eye aims at that target, so the angles differ slightly for near fixation. Matching their Euler angles would remove this convergence.

The eye mesh's local +Y axis is its optical axis. World X points right in the image, world −Y points forward from the face, and Z points up. The camera stays at 40 cm. Camera, lighting and exposure remain constant during a capture.

## Lids and surface details

Blink and brow controls are saved in the scene. Geometry Nodes deform the lids and keep the lashes and moist margins attached to the evaluated head surface. Clearance nodes keep those details outside the eye shells. The inner-corner fold is smaller at open rest and unfolds near full closure to cover the canthus.

The three action bundles are Left, Right and GenerateMotion. Each has 144 frames at 24 fps. All frames in the videos are rendered from the scene; there is no image interpolation. A separate short fixation/hold action remains available in the scene for editing.

## Texture looks

We transferred five CC0 MakeHuman skin sources to the native GNM UVs and added registered detail from the Lee Perry-Smith scan. The source colour map is 4096 × 4096; its height source is 6000 × 6000, 16-bit. Closed eyes, brows, markers, lips and nostrils from the scan are masked out during transfer. We use local frequency bands rather than importing the source scan's geometry or broad lighting.

The exported skin height maps are shader inputs with an authored amplitude. They are not calibrated metric displacement. The eye maps come from the public MakeHuman eye texture. The 64,000-strand scalp groom uses our original root sampling and trajectories.

`wrapper/submission_looks.py` swaps the face, iris and sclera image channels. `wrapper/native_textures.py` can assign the exported materials to a separately loaded GNM head after checking its UV hashes. The application does not change mesh geometry or transforms.

## Metadata

The ten samples run clockwise from the top. Record `k` uses:

```python
theta = 2 * pi * k / 10
h = sin(theta)
v = cos(theta)
```

Each record includes the input, target, eye rotations, geometric pupil centres in 3D and 2D, and the camera projection. Rotations are radians; world positions are metres; 2D positions are continuous pixels from the image's top-left edge.

For a world point `[X, Y, Z, 1]`, multiply by the 3 × 4 camera matrix to obtain `[a, b, c]`. The pixel is `[a/c, b/c]`. These pinhole labels track the geometric pupil aperture. Refraction can shift its apparent centre in a rendered image, so image measurements are checked separately.

## Validation

We check native UV/geometry preservation, target bounds, fixed eye pivots, common-target aiming, texture hashes, full blink coverage and detail clearance. Video checks decode every frame, compare it with the rendered source and measure direction changes in the image. The final archive is extracted and the documented workflow is exercised again.

The reports describe the poses and frames actually checked. They do not give a photorealism score or guarantee continuous-pose collision freedom beyond the sampled cases.
