# Validation results

- Overall result: **PASS**.
- Scope: controller, anatomy, textures and capture checks.

| Check | Passed | Failed |
| --- | ---: | ---: |
| Scene and controller | 1,388 | 0 |
| Anatomy | 51 | 0 |
| Native material application | 55 | 0 |
| Capture and metadata | 5,419 | 0 |
| Texture looks | 112 | 0 |
| Gaze directions | 27 | 0 |

## Deliverables checked

- Three motion clips: 432 rendered frames in total.
- Ten official PNGs with matching ordered metadata.
- Five native texture looks.
- Nine presentation slides: structure and layout checks passed; exported previews reviewed.
- Overview video: all 2,160 frames decoded; duration 90 seconds.

## Extracted ZIP check

- The ZIP was extracted into a new folder.
- All three capture modes and the ten-image export completed from that folder.
- Reduced settings: three one-second clips at 4 fps and 128px, plus ten 1024px images; one sample per render.
- Geometric labels matched the final capture.
- This was a portability check, not a second full-quality render.

## Evidence and limits

| File | Contents |
| --- | --- |
| `report.json` | Settings, check scope and source hashes |
| `fresh_extraction.json` | Extracted-folder run results |
| `presentation.json` | Presentation checks |
| `overview.json` | Overview video checks |
| `../README.md` | Appearance and motion limitations |

- Passing checks confirms the recorded technical behaviour.
- Motion has not been biologically validated; no photorealism score is claimed.
