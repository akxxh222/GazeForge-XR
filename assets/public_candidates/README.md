# Public asset adaptation review

The current local review is `work/review/cyberpunk/IRISX_ASSET_REVIEW.blend`. Press **F12** for the actual Cycles result. Its front, eye close-up and side renders are next to the scene. This file is separate from the older `groom_draft.blend` and five-look scenes.

The selected scalp curves come from **Daniel Bystedt's Hair Styles** on [Blender's official demo page](https://www.blender.org/download/demo-files/). Evaluated source curves are frozen, metrically aligned and root-fitted to GNM, trimmed to a short adult cut, collision corrected, tapered and shaded with a new dark melanin/Huang material. The source is marked **CC BY-SA**, with no version in the published or embedded notice. This is a local fit/review candidate; resolve that version before including its derivatives in the final redistribution bundle.

The iris color network comes from **Daniel Bystedt's Splash Fox / Blender 2.90 splash**, published and embedded as **CC BY-SA 3.0**. Its fox eye mesh is not imported. The adapted network uses the original GNM UVs, round masks, a restrained hazel palette, a native-UV limbal gradient and a modern opaque iris material beneath the native cornea. Fox emission is removed. The adapted iris material retains [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). An authored pupil-constriction shape key preserves the original Basis mesh and UVs.

Two [CC0 MakeHuman eye maps](https://opengameart.org/content/makehuman-system-assets-eyes) are downloaded fallbacks, not used in the selected preview. Amin Missaoui's Just An Eye currently cannot be obtained from its free checkout: the live product says it is not for sale. No buyer email was submitted. BlendSwap downloads also remain unacquired because they require login. Preview pictures or downloaded HTML are not described as usable Blender assets.

`manifest.json` records actual source file sizes, SHA-256 hashes, licenses and modifications. `SOURCE_NOTICES.txt` preserves the relevant embedded source credits. Binary downloads and intermediate experiments remain under ignored `work/public_candidates/`. The scene embeds its own attribution text. No imported asset is relicensed as MIT or CC0.

Reproduce from the project root in PowerShell, after building the existing look 01 scene:

```powershell
python scripts/fetch_public_candidates.py --only hair_nodes-female_hair_styles.blend bystedt_fox_eyes.blend
$env:OPTIX_CACHE_PATH = Join-Path (Get-Location) 'tests/.optix_cache'
& 'E:\Apps\blender.exe' --background --factory-startup --disable-autoexec work/public_candidates/hair_nodes-female_hair_styles.blend --python-exit-code 1 --python scripts/extract_public_hair.py
& 'E:\Apps\blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python scripts/fit_public_groom.py -- --style cyberpunk
& 'E:\Apps\blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python scripts/build_public_asset_review.py -- --style cyberpunk --samples 256
& 'E:\Apps\blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python scripts/validate_public_asset_review.py
```

Downloaded Blender files are loaded as data with auto-execution disabled. No embedded source scripts or add-ons are executed or installed. The reviewer pipeline imports the iris network and fits the groom to the native GNM model; it does not replace GNM with a foreign head or unwrap.

The saved review's geometric checks and actual renders are recorded in `tests/milestone2/public_asset_review/`. A passing geometry report is not a photorealism score. Full-head seams, eyelid/canthus detail, brow/lash flow and reference-level visual acceptance remain open. This review does not complete Milestone 2 or begin Milestone 3, and does not update the final submission ZIP.
