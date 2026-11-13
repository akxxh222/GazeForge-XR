# Milestone 1 baseline evidence

The report and actual Cycles renders validate the imported native GNM template, rather than the older MPFB prototype. Reproduction commands are in `assets/gnm/README.md`.

- `report.json`: native UV/topology/rest-coordinate equality, all-face coverage, metric camera/target, fitted scleral pivot centers, rigid eye rotation, five input directions, projection agreement and deterministic reset. Includes measured render timings and device.
- `geometry_report.json`: the optional geometry-only run.
- `direction_metadata.json`: actual transforms and geometric pupil labels for the five diagnostic poses.
- `reset.png`: 1024x1024 neutral draft. Other four poses are 512x512 diagnostic previews, not the final ten required 1024x1024 submission frames.
- `native_uv_checker.png`: 1024x1024 diagnostic material rendered through the preserved native UVs.
- `contact_sheet.png`: actual pose renders with enlarged eye crops for review.

Visual review: the face is oriented correctly and all five pupil directions are visible in the draft renders. The frontal checker exposes the native UV layout without an obvious discontinuity across the central face. This does not certify texture seams around the full head, realistic skin, dynamic eyelid clearance, refraction-aware labels or final visual quality. Those checks belong to subsequent milestones.
