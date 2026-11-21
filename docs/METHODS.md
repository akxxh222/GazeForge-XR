# Rig and dataset notes

## Eye motion

- Base mesh: original GNM face with its per-region UV layout.
- Each eyeball rotates around its own fixed pivot.
- Shared target: `(0.05*h, -0.35, 0.05*v)`, relative to the eye midpoint.
- Both eyes aim at that point. Their rotation angles differ because of near-target convergence.
- Eye mesh optical axis: local +Y.
- World axes: X image right, −Y forward from the face, Z up.
- Camera distance: 40 cm. Camera, lighting and exposure stay fixed during capture.

## Lids and surface details

- Blink and brow controls are saved in the scene.
- Geometry Nodes deform the lids and attach the lashes and moist margins to the deformed head surface.
- Clearance nodes keep those details outside the eye shells.
- The inner-corner fold expands near full closure to cover the eye corner.
- Actions: Left, Right and GenerateMotion; 144 frames each at 24 fps.
- Every video frame is rendered from the scene, without image interpolation.
- A separate short fixation/hold action is available for editing.

## Texture looks

- Five CC0 MakeHuman skin sources were transferred to native GNM UVs.
- Added skin detail comes from the Lee Perry-Smith scan.
- Scan sources: 4096 × 4096 colour map; 6000 × 6000, 16-bit height map.
- Closed eyes, brows, markers, lips and nostrils are masked out during transfer.
- Only local texture detail is transferred; scan geometry and broad lighting are excluded.
- Skin height maps use an authored strength, rather than calibrated metric displacement.
- Eye maps come from the public MakeHuman eye texture.
- Scalp hair: 64,000 strands with original root sampling and paths.

| Module | Role |
| --- | --- |
| `wrapper/submission_looks.py` | Switches face, iris and sclera image channels |
| `wrapper/native_textures.py` | Checks UV hashes and assigns exported materials to a separately loaded GNM head |

- Material assignment preserves mesh geometry and transforms.

## Metadata

The ten samples run clockwise from the top. Record `k` uses:

```python
theta = 2 * pi * k / 10
h = sin(theta)
v = cos(theta)
```

| Field | Meaning |
| --- | --- |
| Input and target | Normalised control values and world target position |
| Eye rotations | World XYZ Euler angles, in radians |
| 3D pupil centres | Geometric aperture centres, in metres |
| 2D pupil centres | Continuous pixel coordinates from the top-left image edge |
| Camera matrix | 3 × 4 world-to-image projection matrix |

- Projection: `camera_matrix * [X, Y, Z, 1] = [a, b, c]`.
- Pixel position: `[a/c, b/c]`.
- Labels describe the geometric pupil aperture.
- Refraction may shift its apparent centre; rendered image measurements are checked separately.

## Validation

- Scene checks: native UVs and geometry, target bounds, fixed eye pivots and shared-target aiming.
- Surface checks: texture hashes, full blink coverage and detail clearance.
- Video checks: full decoding, comparison with source renders and image direction measurements.
- Portability check: archive extraction and a reduced rendering run from the extracted folder.
- Results apply to the sampled poses and frames.
- No photorealism score or collision guarantee for every possible pose is claimed.
