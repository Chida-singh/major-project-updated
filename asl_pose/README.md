# `asl_pose/`

Core Python package for the MediaPipe-based pose pipeline.

## What’s inside

- `video.py` — Extracts MediaPipe Holistic landmarks from a video into arrays.
- `landmarks.py` — Converts MediaPipe results into a fixed `(T, 543, 3)` format.
- `normalize.py` — Resampling utilities (e.g., to a fixed frame count).
- `db.py` — Pose database build + lookup (per-gloss `.npy` files).
- `viz.py` — Offline renderer that draws the skeleton to an `.mp4`.

## Data shapes

- Pose sequence: `(T, 543, 3)` where `T` is frames.
- Database item: typically `(N, T, 543, 3)` for `N` signer instances.

## Entry points

Most usage goes through the CLI in `tools/pose_pipeline.py`.
