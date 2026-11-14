# CC0 iris review source

`green_eye.png` is the unchanged MakeHuman system eye asset, downloaded from
https://opengameart.org/sites/default/files/green_eye.png and attributed by
https://opengameart.org/content/makehuman-system-assets-eyes as CC0.

SHA256: `b9864ac4f4fa484b24e18f6aba030d70dbc8820cbbacfbe63a974c76772c2009`.
The earlier download evidence is in `assets/public_candidates/manifest.json`.

Only an iris region is sampled in the new candidate. The Blender shader maps
its annulus onto the original GNM UVs and reduces saturation. The native pupil,
cornea, eye geometry, UV layout and physical pivots are retained. The source is
an authored asset; it is not presented as photographic eye ground truth.

This replaces the active Splash Fox iris color material in this candidate.
Inherited attribution remains in the source scene; the separate fitted hair
asset's unresolved CC BY-SA version still prevents final bundle acceptance.
