# Original iris appearance plate

`iris_stroma_master.png` is an original AI-authored appearance texture created with the built-in image generation tool on 2026-11-14. The exact prompt is in `PROMPT.md`; source hash, dimensions and measured image-space pupil/limbus radii are in `manifest.json`. The provided source file makes the downstream authoring steps deterministic without another generation call.

`scripts/make_gnm_texture_looks.py` registers the source annulus to the unchanged GNM pupil/iris UV radii, varies its color per look and applies distinct deterministic L/R rotations. New scleral capillaries are authored separately. Catchlights and refraction are produced by Blender materials and scene lighting.

This is appearance data, not a photograph, measured human anatomy or biometric ground truth. Any project-held rights in the original plate and its original eye-texture derivatives are dedicated under CC0 1.0 Universal. This does not alter the Google GNM model's Apache-2.0 terms or the attributed skin scan's CC BY terms.
