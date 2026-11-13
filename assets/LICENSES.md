# Asset provenance: Milestone 1

## Google GNM Head 3.0

The new native-UV baseline derives from Google GNM, copyright 2026 Google LLC, licensed under **Apache-2.0**, not CC0. Sources:

- https://github.com/google/GNM at revision `f84cdbdc86a34f55627526f137495f864e687679`.
- https://huggingface.co/google/gnm-v3 at revision `c01e90d298d82301f9fd18f54806be751775cb7c`.

The model host explicitly licenses the weights under Apache-2.0. The full license is retained in `gnm/LICENSE.Apache-2.0.txt`. Unmodified upstream reference source, the model card, a UV diagnostic image retain their upstream licensing. `gnm/download_manifest.json` records sources, sizes and SHA-256 hashes. The model NPZ matches the published checksum `61d78bbfb4ad8e0b38495804a4caef3214d3df00f8c3f68761e63b41ce3747eb`.

Project modifications in `work/gnm/scene_baseline.blend`: native geometry separated into six components, rigid axis/origin conversion, calibrated eye-bone control, draft materials, camera/lights and subdivision. Original vertex/quad IDs and per-region UV coordinates are retained. `gnm/native_manifest.json` records topology/UV hashes. These model derivatives remain subject to Apache-2.0.

No Chris Jones / Universal Human models, textures, shaders or rig files are included. That work is reference material only.
