# `tools/`

Command-line scripts for running the pipeline end-to-end.

## Key scripts

- `pose_pipeline.py`
  - `single` — extract landmarks from one video
  - `build-db` — build pose DB from WLASL videos
  - `lookup` — fetch canonical pose for one gloss
  - `sentence` — stitch multiple glosses into one sequence
  - `viz` — render a sequence to `.mp4`

- `wlasl_setup.py`
  - Windows-friendly helper to download/prepare a WLASL subset into the expected layout.

## Typical flow

1. Prepare WLASL (download subset) with `wlasl_setup.py`.
2. Build DB with `pose_pipeline.py build-db`.
3. Lookup + render with `pose_pipeline.py lookup` and `pose_pipeline.py viz`.
