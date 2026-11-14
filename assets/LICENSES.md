# Asset provenance

`mpfb_head.json.gz` is a head-and-shoulders extraction of the user's pre-existing MPFB human in `Untitled.blend`. It derives from MakeHuman/MPFB core base geometry. No third-party clothes, skins or hair were present in the source.

License: CC0 1.0 Universal. Official evidence, checked 2026-11-07:

- https://static.makehumancommunity.org/mpfb/faq/use_in_closed_source.html
- https://creativecommons.org/publicdomain/zero/1.0/

The official MPFB FAQ states: "All core assets (the base mesh, targets, skins…) are shared under CC0."

`skin_texture.png`, the eye geometry, procedural materials, hair fibers, brows and outfit appearance were generated for this project and are dedicated under CC0. MPFB 2.0.18's GPL-licensed add-on source is neither copied into the submission nor required to reproduce it.

The organizer PDF is a local reference and is not redistributed. The source backup and user-profile files are not included in the submission archive.

## Google GNM Head 3.0

The new native-UV baseline derives from Google GNM, copyright 2026 Google LLC, licensed under **Apache-2.0**, not CC0. Sources:

- https://github.com/google/GNM at revision `f84cdbdc86a34f55627526f137495f864e687679`.
- https://huggingface.co/google/gnm-v3 at revision `c01e90d298d82301f9fd18f54806be751775cb7c`.

The model host explicitly licenses the weights under Apache-2.0. The full license is retained in `gnm/LICENSE.Apache-2.0.txt`. Unmodified upstream reference source, the model card, a UV diagnostic image and semantic expression/identity weights retain their upstream licensing. `gnm/download_manifest.json` records sources, sizes and SHA-256 hashes. The model NPZ matches the published checksum `61d78bbfb4ad8e0b38495804a4caef3214d3df00f8c3f68761e63b41ce3747eb`.

Project modifications in `work/gnm/scene_baseline.blend`: native geometry separated into six components, rigid axis/origin conversion, calibrated eye-bone control, draft materials, camera/lights and subdivision. Original vertex/quad IDs and per-region UV coordinates are retained. `gnm/native_manifest.json` records topology/UV hashes. These model derivatives remain subject to Apache-2.0; the earlier CC0 description applies to the legacy MPFB prototype assets only.

No Chris Jones / Universal Human models, textures, shaders or rig files are included. That work is reference material only; see `docs/HUMAN_PROGRESS_REFERENCE.md`.

## Native blink derivatives for milestone 3

`work/gnm/blink_shapes.npz` derives left/right eyelid motion from the official GNM expression decoder and expression basis, retaining Apache-2.0 and the Google notices above. `prepare_gnm_blink_shapes.py` reads the pinned model as data using an allowlisted Dense/ReLU forward pass, zero latent and semantic wink classes 13/14; it isolates the corresponding 100 eye-region coefficients and changes axes. The authored scene uses additional endpoint gains 1.16 (L) and 1.21 (R), plus deformation-bound local lash/waterline geometry. Source hashes and modifications are recorded in the adjacent JSON receipt and `work/milestone3/prototype.json`. These native model derivatives are not reclassified as MIT or CC0. Existing iris, hair and skin attributions still apply to the composed scene.

## Relaxed native eyelid rig

The later `work/milestone3/final/IRISX_MILESTONE3.blend` replaces the contracted semantic-wink geometry with an independently authored post-subdivision lid map, using native GNM silhouette/canthal measurements. Its closed collision helpers are extracted from the native `eye_exteriors` mask. Original native Basis/UVs/topology are retained; live detail bindings, conforming canthal tissue and wet margins are project modifications. Outer canthal joins receive barycentrically transferred native skin UVs. These native model derivatives retain Apache-2.0 and Google notices. The original Python authoring/control code remains MIT; this does not relicense the composed model or inherited skin/iris/hair assets. `work/milestone3/final/rig.json` records source, scene, builder and control-module hashes, and `tests/milestone3/final/` records the applicable acceptance evidence. Earlier semantic-wink files remain historical parents rather than the final closure deformation.

## Skin sources for milestone 2

MakeHuman Community [Skins 02](https://static.makehumancommunity.org/assets/assetpacks/skins02.html) is an official curated CC0 pack. Downloaded 2026-11-14 from its official mirror; archive SHA-256 `1613f1ef3afca53094511d26620ed7cf1d2dedc29ed3d384d60bdebe250698ae` (locally recorded). The embedded catalog independently lists author/source and CC0 license per material. `source_skins/manifest.json` preserves this metadata and per-file hashes. Authors include Mindfront, MargaretToigo, jartur69, ken1138, OnlyTheGhosts and RehmanPolanski.

Raw maps are local source data in ignored `work/source_skins/`, not final GNM texture deliverables. Each source image is a 2048x2048 MakeHuman body UV map; mapping compatibility and sufficient facial detail are not established by the download. The first five candidates are listed in `source_skins/selection.json`. Any accepted head-map derivatives must be baked to unchanged native GNM UVs, visually reviewed and documented with their specific source.

## Milestone 2 generated texture drafts

`textures/look_01` through `look_05` contain native-GNM UV exports derived from CC0 sources by OnlyTheGhosts, Mindfront and MargaretToigo. Each look manifest identifies its source file, author, license and SHA-256. The former Aksel candidate was excluded from the neutral set because it contains a bruised eye.

The source CC0 head geometry supplies a temporary correspondence surface. Target GNM geometry/UVs remain unchanged. The transfer adds continuous procedural pore/roughness fields; iris fibers, crypts, scleral variation and vein maps are authored for this project. No Chris Jones asset files are used. Retain the GNM Apache license/notices with the native model and its scene derivatives, and the CC0 source provenance with exported skin maps. Original authoring/application code uses the project's MIT license.

These exports are draft assets under visual review, not a claim that downloaded MakeHuman maps were natively compatible or that higher export resolution added source facial detail.


## Scan-backed skin detail and original iris plate

The revised skin maps additionally derive high-frequency appearance detail from **Infinite, 3D Head Scan by Lee Perry-Smith / Infinite-Realities**, licensed under CC BY 3.0 Unported. The original license statement, pinned three.js host revision, source file and checksums are in `assets/skin_detail/`. Retain that attribution with the derived skin base-color, roughness and height maps, alongside their CC0 primary diffuse-source credits. The target GNM model continues to use Apache-2.0. These mixed-source skin derivatives are not described as entirely CC0.

`assets/iris/iris_stroma_master.png` is an original AI-authored appearance plate generated with the built-in image generation tool. `assets/iris/PROMPT.md` preserves the exact prompt; its manifest preserves the source hash and annulus registration. The plate is not a photograph or measured human anatomy. Original project-held rights in the iris plate and eye-map additions are dedicated under CC0 1.0 Universal. Final preview images are actual Blender Cycles renders using these textures, not generated render substitutes.

The scan's 4096px source is an 8-bit JPEG. The pipeline removes coarse shape and projects high-frequency bands with artist-selected amplitude into 16-bit output maps. The export precision does not imply 16-bit source measurements or calibrated scan displacement.

## Public eye and scalp-groom review candidates

The separate `work/review/cyberpunk/IRISX_ASSET_REVIEW.blend` imports an adapted iris color network from Daniel Bystedt's **Splash Fox / Blender 2.90 splash**, licensed **CC BY-SA 3.0**, and scalp curves from his official **Hair Styles** demo, marked **CC BY-SA** with no version specified. These are sourced from [Blender's official demo files](https://www.blender.org/download/demo-files/). Adapted iris materials retain [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/), with author, source and modifications embedded in the scene. Hair derivatives are a local fitting review; resolve the unstated version before final redistribution. Neither source becomes MIT or CC0.

`assets/public_candidates/manifest.json` records source binaries, actual SHA-256/size, licenses, modifications and availability. `SOURCE_NOTICES.txt` preserves embedded credits. Two CC0 MakeHuman eye texture fallbacks are downloaded from the [MakeHuman eye collection](https://opengameart.org/content/makehuman-system-assets-eyes), but are not used in the selected preview. Just An Eye and BlendSwap Blender files were not obtained; their public product previews or HTML are not imported assets. The scene retains the separate GNM Apache-2.0 and mixed-source skin licenses described above.
