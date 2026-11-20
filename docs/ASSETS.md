# Asset credits

The project code is under the MIT licence in `LICENSE`. Imported assets retain their own licences.

| Asset | Credit and licence | Use |
| --- | --- | --- |
| GNM Head 3.0 | Google GNM, Apache-2.0 | Native face/eye meshes, topology and per-region UVs |
| Five skin sources | OnlyTheGhosts, Mindfront and Margaret Toigo, CC0 | Base skin colours transferred from MakeHuman UVs |
| MakeHuman green eye | MakeHuman system asset, CC0 | Registered iris/sclera colour and sclera detail |
| Infinite 3D Head Scan | Lee Perry-Smith / Infinite-Realities, CC BY 3.0 | Local skin colour and height detail |
| Scalp groom | Original project curves, CC0 dedication | 64,000 native hair strands |

Skin source IDs are `onlytheghosts_old_eurasian_male`, `mindfront_skin_male_african_middleage`, `toigo_light_skin_male_freckles`, `toigo_light_skin_male_ginger` and `toigo_light_skin_male_bronze`. Their original files are full-body 2048px maps; a 4K export does not add source facial detail by itself.

The scan's convenient-format distribution credits Morgan McGuire and Guedis Cardenas; the Unity distribution was prepared by Keijiro Takahashi. We registered local detail onto GNM, masked closed features/markers, removed broad colour illumination, normalised the height bands and feathered colour across UV cuts. The resulting skin maps combine CC0 sources with CC BY 3.0 scan detail, so they are not described as entirely CC0.

Sources and retained notices:

- [Google GNM](https://github.com/google/gnm) — `assets/gnm/LICENSE.Apache-2.0.txt` and `native_manifest.json`.
- [MakeHuman skin asset packs](https://static.makehumancommunity.org/assets/assetpacks.html) — source records in `assets/source_skins/manifest.json`.
- [MakeHuman eye texture](https://opengameart.org/content/makehuman-system-assets-eyes) — original `green_eye.png`, SHA-256 `b9864ac4f4fa484b24e18f6aba030d70dbc8820cbbacfbe63a974c76772c2009`.
- [InfiniteScan](https://github.com/keijiro/InfiniteScan/tree/150b6c46ebb6a011b93ed2e0fee9b612df78281b) — 4096px colour source; licence retained in `assets/skin_detail/License.txt`.
- [FaceWorks LPSHead](https://github.com/NVIDIAGameWorks/FaceWorks/tree/1624b67e26b984d393f053fbf2761e5c6207b44e/samples/media/LPSHead) — the separately credited 6000px scan height texture. No FaceWorks code or other demo heads are included.

All preview images and videos in this submission are Blender renders of the supplied scene. The scene contains no imported commercial reference character or demo groom.
