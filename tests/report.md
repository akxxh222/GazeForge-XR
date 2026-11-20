# Validation results

The final scene passes the controller, anatomy, texture and capture checks.

| Check | Passed | Failed |
| --- | ---: | ---: |
| scene | 1,388 | 0 |
| anatomy | 51 | 0 |
| native application | 55 | 0 |
| capture | 5,419 | 0 |
| looks | 112 | 0 |
| directions | 27 | 0 |

All 432 video frames were rendered from the supplied scene. The ten official PNGs have matching ordered metadata. Appearance limits are listed in the README. See `report.json` for settings, scope and source hashes.

The ZIP was extracted into a new folder. All three capture modes and the ten-sample export ran from that folder with reduced smoke settings. Their geometric labels matched the final capture. The slides pass structure/layout checks; the 90-second overview decodes in full. Details are in `fresh_extraction.json`, `presentation.json` and `overview.json`.
