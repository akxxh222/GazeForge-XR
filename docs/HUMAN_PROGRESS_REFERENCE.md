# Human Progress reference review

Reviewed 2026-11-14 for `VITChennai_IrisX`.

## Source and scope

The [user-linked post 76](https://blenderartists.org/t/human-progress/1143224/76) is a viewer's appreciative reply. The relevant technical explanation is Chris Jones's **post 74**, readable on [thread page 4](https://blenderartists.org/t/human-progress/1143224?page=4). This review inspected the text; the embedded animated GIFs were not successfully displayed by the web reader. It does not claim frame-by-frame inspection of those GIFs.

Jones describes eye tracking with low-influence rotation constraints on eyelid bones to produce subtle follow. His blink setup blends a sequence of intermediate shapes through a single control, using a bone action and Action Constraint in that 2019 implementation. Gaze and blink have separate controls. These are useful anatomical/rigging ideas; historical editor limitations and curve workarounds are not assumed to apply to the installed Blender version.

## Application to our requirements

The supplied evaluation deck calls for coordinated gaze/lids, smooth closure, native GNM/FLAME UVs, timeline animation and modular Python controls. Use the reference techniques through an independently authored rig on the verified target head:

| Proposed project work | Requirement and review gate |
|---|---|
| Separate gaze and lid-opening controls, combined by the sequence wrapper | Deterministic Python access and editable timeline actions |
| Restrained upper/lower lid follow driven by gaze | Review all five directions and combined blink poses; tune per target anatomy |
| Several sculpted closure poses with a smooth interpolation path | Inspect intermediate frames for corneal penetration, corner detachment and UV stretching |
| Fine skin detail, tear-line highlights and separately controlled eye material layers | Review static close-ups before long video renders |

Keep the native head UVs unchanged. The reference's presentation does not alter our fixed camera, metric calibration, official ten-frame sampling or required metadata. No milestone is completed by this review.

## Asset reuse decision

The creator's [Head Textures](https://cjones.gumroad.com/l/bnxkc) and [Eye Textures](https://cjones.gumroad.com/l/omlxn) are designed around Universal Human assets; direct GNM/FLAME UV compatibility is not established by their product descriptions. The [Skin Shader](https://cjones.gumroad.com/l/nkrsw) describes fine procedural detail, tension-driven changes and a tear-line material, which are useful reference goals.

The published [Universal Human license](https://sites.google.com/view/universalhuman/license-agreement) restricts sharing assets in original or modified form and requires protection against extraction for its software-distribution exception. Our deliverables include editable `.blend` data and separate texture files. Under those published terms, exclude these commercial models, rigs, textures and shaders from the submission. Baking them onto another UV layout does not remove that restriction. Any different permission would need to explicitly cover the required deliverables.

The forum's downloadable rig examples were not downloaded; public attachment access alone does not establish suitable redistribution rights. No third-party asset from this reference was imported or bundled. Use independently authored or appropriately licensed materials with verified native UV compatibility, and record provenance in `assets/LICENSES.md` when actual assets are added.
