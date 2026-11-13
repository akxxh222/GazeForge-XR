# Asset provenance: Milestones 1 and 2

## Google GNM Head 3.0

The new native-UV baseline derives from Google GNM, copyright 2026 Google LLC, licensed under **Apache-2.0**, not CC0. Sources:

- https://github.com/google/GNM at revision `f84cdbdc86a34f55627526f137495f864e687679`.
- https://huggingface.co/google/gnm-v3 at revision `c01e90d298d82301f9fd18f54806be751775cb7c`.

The model host explicitly licenses the weights under Apache-2.0. The full license is retained in `gnm/LICENSE.Apache-2.0.txt`. Unmodified upstream reference source, the model card, a UV diagnostic image retain their upstream licensing. `gnm/download_manifest.json` records sources, sizes and SHA-256 hashes. The model NPZ matches the published checksum `61d78bbfb4ad8e0b38495804a4caef3214d3df00f8c3f68761e63b41ce3747eb`.

Project modifications in `work/gnm/scene_baseline.blend`: native geometry separated into six components, rigid axis/origin conversion, calibrated eye-bone control, draft materials, camera/lights and subdivision. Original vertex/quad IDs and per-region UV coordinates are retained. `gnm/native_manifest.json` records topology/UV hashes. These model derivatives remain subject to Apache-2.0.

No Chris Jones / Universal Human models, textures, shaders or rig files are included. That work is reference material only.

## CC0 source surface for texture authoring

`mpfb_head.json.gz` is a head-and-shoulders extraction of the user's pre-existing MPFB 2.0.18 human, exported for the earlier project prototype on 2026-11-07. It derives from MakeHuman/MPFB core base geometry. The source contained no third-party clothes, skins or hair. Core base assets use CC0 1.0 Universal; the MPFB add-on's GPL source is not included or required here. Source evidence recorded with the prototype:

- https://static.makehumancommunity.org/mpfb/faq/use_in_closed_source.html
- https://creativecommons.org/publicdomain/zero/1.0/

Milestone 2 reuses this geometry only as a temporary correspondence surface in `scripts/prepare_gnm_skin_transfer.py`. The final target geometry and UVs remain native GNM. The legacy prototype scene, generated skin image, demo and submission outputs are excluded.

## MakeHuman skin sources

MakeHuman Community [Skins 02](https://static.makehumancommunity.org/assets/assetpacks/skins02.html) is the official curated CC0 pack downloaded on 2026-11-14. Archive SHA-256: `1613f1ef3afca53094511d26620ed7cf1d2dedc29ed3d384d60bdebe250698ae`, locally recorded rather than an independently advertised upstream checksum. The embedded catalog lists author/source and CC0 license per material. `source_skins/manifest.json` preserves this catalog and per-file hashes; `selection.json` identifies the five selected sources and the rejected bruised-eye candidate.

Raw 2048x2048 body-UV sources are reproducible local authoring inputs in ignored `work/source_skins/`. They are not directly compatible with GNM. Exporting a 4K map does not increase the source facial detail.

## Milestone 2 generated texture drafts

`textures/look_01` through `look_05` contain native-GNM UV exports derived from CC0 sources by OnlyTheGhosts, Mindfront and MargaretToigo. Each look's manifest identifies its source file, author, license and SHA-256. The transfer adds continuous procedural pore/roughness fields and minor color modulation. Iris fibers, crypts, scleral variation and vein maps are authored for this project. Original procedural texture additions are dedicated under CC0 1.0 Universal; authoring/application code uses the project's MIT license.

Retain the GNM Apache license and notices with the native model and its scene derivatives, and the CC0 source provenance with exported skin maps. No Chris Jones / Universal Human asset files are used. These are draft exports under visual review, not accepted photorealistic assets.
