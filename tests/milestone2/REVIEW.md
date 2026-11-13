# Milestone 2 visual review - in progress

Milestone 1 is committed as `5738394`. This checkpoint adds native-UV texture transfer, five PBR/eye looks and static facial detail. Milestone 2 remains in progress pending visual acceptance.

## Implemented and checked

- Five distinct 4K native-GNM skin looks, with separate 2K left/right eye maps and 16-bit height channels.
- Original target UVs and topology retained; source projection exists only in the offline authoring pipeline.
- Skin roughness/micro-bump and millimeter-scale subsurface shading; native iris/pupil/cornea geometry with refractive material; static brows, lashes and tear menisci.
- `texture_audit.json`: 117 passing file/source/map checks, zero failures. Native UV color discontinuity measurements are reported separately, with no invented visual score.
- `portability_report.json`: 80 passing checks, zero failures, applying all five looks to independently reloaded native baselines. No MakeHuman UV map is needed at application time.
- `render_audit.json`: 70 passing checks, zero failures, across 15 actual renders. Image dimensions, current texture/appearance provenance, finite labels and explicit refractive-label semantics are checked.
- Actual fixed-camera front renders and macro material views. Look 01 also has left/right gaze macros, an individual-eye close-up and two side views. These are material previews, not the final required ten-frame sequence or videos.

## Corrected drafts

The first projection mapped inner-socket atlas colors onto visible lids. Orbital projection now uses front-facing source surfaces. The initial Aksel source also contains a bruised eye; it was replaced with the CC0 mature skin source for the neutral five-look set. The rejected frontal/macro images are retained in `rejected_projection_v1/`.

The first static lash fit used the transparent corneal silhouette, which placed some upper roots too high on the lid. The fit now uses the opaque eye aperture, and control points clear the skin surface. The final close-up shows continuous visible upper lashes; their flow and density still need artistic refinement before accepting static appearance.

## Remaining acceptance work

- Review and repair visible color discontinuities around UV cuts, ears, lid corners and neck. Quantitative seam differences remain nonzero; the map audit is not a seam-free certification.
- Improve natural skin detail and tone. The source facial pixels are limited and some source scalp/hair patterns look stretched in side views. Procedural detail does not replace that missing photographic information.
- Refine upper lashes, brow flow/density, tear-film/canthus integration and iris/sclera appearance against the Eye Piece reference. Hair counts or render samples alone are not visual acceptance.
- Preserve geometric pupil labels and clearly separate any future measured apparent, refracted centers. The current scene declares this distinction; no apparent-center validation is claimed.
- Keep Milestone 2 in progress until static close-ups, full-face looks and seam reviews pass. Eyelid motion, blinking and animated hair attachments are subsequent Milestone 3 work.
