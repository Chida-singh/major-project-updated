# Project Context (ASL Overlay for Streaming Media)

## One-line goal

Turn lecture videos into a browser overlay that shows a synchronized ASL signer skeleton.

## Pipeline

1. Whisper: audio → text + word timestamps
2. GPT‑4o: English → ASL gloss order + NMM annotations (JSON-only)
3. Pose lookup: gloss → canonical pose sequence (MediaPipe landmark space)
4. Pose assembly: timing + transitions + OOV fallback
5. NMM conditioning: deterministic face landmark offsets (core contribution)
6. Browser overlay: Canvas renderer synced to video time

## What already works in this repo

- MediaPipe Holistic extraction (Tasks API) → `(T, 543, 3)`
- Pose DB builder + lookup (`pose_database/`, `asl_pose/db.py`)
- Sentence concatenation CLI (`tools/pose_pipeline.py sentence`)
- Offline MP4 visualization (`asl_pose/viz.py`)

## What was imported from other work

- `extension/` — legacy Chrome extension popup (not used).

## Frontend choice (important)

We are building a **website UI**, not an extension popup.

- Backend: `server/` (FastAPI)
- Frontend: `web/` (static HTML/JS)

## Where to track work

- The master checklist is `docs/ROADMAP.md` (tasks are numbered `01_...` → `41_...`).

## How to get running

Use `docs/SETUP_AND_RUN.md` (Python 3.11 venv + dataset placement + run commands).
