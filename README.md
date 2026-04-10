# ASL Overlay for Streaming Media

BE Final Year Project — DSCE Bengaluru (VTU)

## What this does

Takes any lecture video, transcribes speech with **Whisper**, converts English → **ASL gloss order** using **GPT‑4o** (plus NMM annotations), looks up pre-extracted **pose sequences** for each gloss, and renders a synchronized **skeleton signer overlay** in the browser.

**Scope constraints**

- Skeleton overlay only (no MimicMotion / diffusion; no SignAvatars).
- GPU available: RTX 5060 Ti 16GB (optional; most of this runs fine on CPU).
- Budget target: ~$20 GPT‑4o API.
- Deadline: < 2 months.

## Repo layout (modular)

- `asl_pose/` — MediaPipe Holistic extraction + pose DB helpers + offline visualizer.
- `tools/` — CLI utilities (extract, build DB, visualize) + Windows-friendly WLASL setup.
- `pose_database/` — generated per-gloss pose arrays (large; normally not committed).
- `WLASL/` — external dataset repo + videos (large; not committed).
- `models/` — cached MediaPipe task models (large; not committed).
- `docs/` — project docs: roadmap, missing assets, API contracts.
- `server/` — FastAPI app that serves the local website.
- `web/` — static website UI (served by `server/`).
- `extension/` — legacy Chrome extension popup (not used).

## Setup + run (teammates)

See `docs/SETUP_AND_RUN.md` for Python 3.11 venv setup, dataset folder placement, and the exact commands to run the pipeline.

Each folder has (or should have) its own README for teammates using other IDEs.

## Pipeline stages (end-to-end)

### Stage 0 — Environment (Windows)

MediaPipe and PyTorch are typically most reliable on **Python 3.10 / 3.11** on Windows.

Notes for this workspace:

- A `.venv` exists, but it was configured on Python 3.14 during earlier experiments.
- **Do not** base the final combined system on Python 3.14.
- How2Sign `.pkl` files are Torch-serialized and often reference `cuda:0`, and will fail to load without a PyTorch-compatible Python.

### Stage 1 — Data

- WLASL (dxli94/WLASL) — used to build the initial per-gloss pose DB.
- ASL Citizen (planned) — additional coverage.
- How2Sign (planned; access required) — later integration.

### Stage 2 — Pose extraction + pose database (MediaPipe Holistic)

**Goal:** build `pose_database/<GLOSS>.npy` where each file stores multiple signer instances.

Current implementation status:

- Pose extraction works end-to-end using MediaPipe Holistic Tasks API.
- DB format: per gloss file `pose_database/<GLOSS>.npy` with shape `(num_signers, 30, 543, 3)`.
- `asl_pose/db.py` lookup returns the mean over signers for a gloss → shape `(30, 543, 3)`.

### Stage 3 — Whisper transcription

**Goal:** transcribe the lecture audio and get word-level timestamps.

Status:

- Not yet implemented in this repo.
- Required for caption sync and for gloss duration estimation.

### Stage 4 — GPT‑4o translation layer (English → ASL gloss order + NMM)

**Goal:** for each sentence (or chunk), produce a JSON object:

```json
{
	"glosses": [
		{ "w": "HELP", "nmm": ["TOPIC_RAISED_BROWS"], "duration_ms": 600, "confidence": 0.9 }
	],
	"sentence_nmm": ["YESNO_Q"],
	"oov": ["somemissingword"]
}
```

Status:

- Prompt + API wiring not yet implemented in this repo.
- Design requirement: pass the `pose_database/index.json` vocabulary to GPT‑4o to reduce OOV.

### Stage 5 — Pose assembly (gloss list → full sequence)

**Goal:** lookup each gloss pose, concatenate, and **interpolate transitions**.

Status:

- Concatenation exists: `tools/pose_pipeline.py sentence` produces a full pose array (hard cuts).
- Missing: transition blending (3–5 frames), variable timing based on `duration_ms`, and a real fallback for OOV (currently zero-fill).

### Stage 6 — NMM conditioning (novel contribution)

**Goal:** apply NMM as explicit landmark offsets on the face region before rendering.

Landmark layout (543 total):

- 0–467: Face (468 points)
	- Brow area: 0–10
	- Eye corners: 33, 133, 362, 263
	- Mouth anchors: 61, 291, 13, 14
- 468–500: Body pose (33 points)
	- Shoulders: 472–473
	- Wrists: 476–477
- 501–521: Left hand (21 points)
- 522–542: Right hand (21 points)

Status:

- Not yet implemented.
- This will be the core “IP” / contribution: deterministic facial landmark conditioning from GPT NMM tags.

### Stage 7 — Browser renderer overlay (Canvas / Three.js)

**Goal:** draw a stick figure signer in the corner of the lecture video, synchronized to captions.

Status:

- Offline MP4 renderer exists (`asl_pose/viz.py`) using OpenCV.
- Missing: browser overlay renderer + transport format + video-time synchronization loop.

## Current state (quick inventory)

**Built / working now**

- Pose DB lookup: `asl_pose/db.py`.
- Sentence concatenation CLI: `tools/pose_pipeline.py sentence` (hard cuts).
- Fixed-length resampling to 30 frames: `asl_pose/normalize.py`.
- Offline visualization to MP4: `asl_pose/viz.py`.
- `pose_database/` exists locally with `index.json` and `.npy` gloss files.

**Known gaps (next engineering steps)**

- Whisper transcription + timestamps.
- GPT‑4o translation prompt + API call (JSON contract above).
- Transition interpolation + duration-aware sequencing.
- NMM conditioning implementation (brow/mouth offsets).
- Browser overlay renderer + sync.

## Roadmap (41 tasks)

The full checklist lives in `docs/ROADMAP.md` and is numbered `01_...` → `41_...`.

## Quick commands (pose DB pipeline)

### Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Single-video extraction test

```powershell
python tools\pose_pipeline.py single --video path\to\test.mp4 --out out.npy
```

### WLASL dry-run setup + DB build

```powershell
python tools\wlasl_setup.py --include-youtube --limit-glosses 50 --max-instances-per-gloss 1
python tools\pose_pipeline.py build-db --limit-glosses 50
```

### Lookup + offline visualization

```powershell
python tools\pose_pipeline.py lookup --gloss HELP --out help.npy
python tools\pose_pipeline.py viz --npy help.npy --out help.mp4
```

## Required-but-not-in-repo assets

See `docs/MISSING_ASSETS.md` for a precise checklist of keys, datasets, and model files that should NOT be committed.


Set-Location "d:/DSCE/Major Project/April 5th"; .\.venv\Scripts\python.exe tools\wlasl_setup.py --include-youtube --limit-glosses 2000 --max-instances-per-gloss 5; .\.venv\Scripts\python.exe tools\pose_pipeline.py build-db --limit-glosses 2000 --limit-instances-per-gloss 5 --target-frames 60 --output-dir pose_database_2000x5_f60