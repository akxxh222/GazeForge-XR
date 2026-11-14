# Attributed scan detail source

`Infinite-Level_02_Disp_NoSmoothUV-4096.jpg` comes from **Infinite, 3D Head Scan by Lee Perry-Smith / Infinite-Realities**, based on work at triplegangers.com. The upstream distribution licenses it under [Creative Commons Attribution 3.0 Unported](https://creativecommons.org/licenses/by/3.0/). Retain this attribution and `LeePerrySmith_License.txt` with derivatives.

Downloaded from the [three.js example asset distribution](https://github.com/mrdoob/three.js/tree/9b4a2ac29c63ccb43fd51c5661f2f873ac2c39b8/examples/models/gltf/LeePerrySmith), pinned at commit `9b4a2ac29c63ccb43fd51c5661f2f873ac2c39b8`. `manifest.json` records exact URLs, sizes and SHA-256 values. The upstream license statement is preserved verbatim; the target GNM model retains its separate Apache-2.0 license.

Project modifications: `scripts/gnm_scan_detail.py` extracts high-frequency bands from this 4096px grayscale map, registers frontal landmarks in target world X/Z coordinates and smoothly fades the detail outside the face. The detail is baked into unchanged native GNM UV skin color, roughness and 16-bit height maps. Those scan-derived skin maps carry this CC BY attribution alongside their CC0 diffuse-source credits. The source scan mesh is not included in the target scene.

The source is an 8-bit JPEG. Exporting the combined height channel at 16-bit retains authored/interpolated precision but does not turn the source into a 16-bit scan. Heights have artist-selected amplitude and are appearance data, not measured human surface displacement or anatomical ground truth.
