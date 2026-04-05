# Repo Workflow

## How tasks are named

We track all work as numbered tasks:

- `01_<name>` … `41_<name>`

These map to the end-to-end pipeline stages.

## Where things live

- `asl_pose/` — extraction, normalization helpers, DB access, offline viz
- `tools/` — CLI + dataset setup helpers
- `pose_database/` — generated DB (large `.npy` ignored; keep `index.json`)
- `models/` — cached MediaPipe task model (ignored)
- `WLASL/` — dataset clone/videos (ignored)
- `extension/` — browser extension shell (to be upgraded into the overlay)

## Contribution rules

- Do not commit datasets, large videos, large arrays, or API keys.
- Keep changes scoped to the task number you are working on.
- Update `docs/ROADMAP.md` checkbox status when a task is finished.
