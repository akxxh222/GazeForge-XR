# Native GNM asset

Google GNM Head 3.0, Apache-2.0, copyright 2026 Google LLC. See `LICENSE.Apache-2.0.txt`, `download_manifest.json` and `reference/MODEL_CARD.md` for the upstream license, pinned sources and recorded hashes.

From the project root, download the data with:

```powershell
& ./scripts/fetch_gnm.ps1
```

The model NPZ is excluded from Git and verified against Google's published checksum. Expression/identity decoder weights are also downloaded for later expression work; they are not executed by the baseline importer. Upstream reference Python files are retained unmodified as implementation documentation and are not imported by our baseline.

Build and validate in Blender:

```powershell
$env:OPTIX_CACHE_PATH = Join-Path (Get-Location) 'tests/.optix_cache'
& 'E:\Apps\blender.exe' --factory-startup -b --python-exit-code 1 --python scripts/build_gnm_baseline.py
& 'E:\Apps\blender.exe' --factory-startup -b work/gnm/scene_baseline.blend --python-exit-code 1 --python scripts/validate_gnm_baseline.py -- --render
python scripts/make_gnm_contact_sheet.py
```

Use `validate_gnm_baseline.py` without `--render` for a fast check; it writes `geometry_report.json` separately. Generated draft scene: `work/gnm/scene_baseline.blend`. Evidence: `tests/milestone1/`. This path intentionally preserves the previous prototype in root `scene.blend`.

The importer retains the original `quad_uvs` per region, using separate material assignments for skin, each eye and oral components. This is the model's native per-region layout, rather than a new unwrap or an MPFB layout. It preserves original vertex/quad identifiers for independent equality checks. All-zero identity/expression values define the initial template.

Draft skin/iris materials establish geometry and calibration only. Texture transfer, fine detail, eyelid actions and expression videos are subsequent milestone work. Native corneal geometry is present; apparent refracted pupil measurements remain separate work from the geometric pupil projection.
