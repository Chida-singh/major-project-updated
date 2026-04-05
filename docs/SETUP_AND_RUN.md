# Setup + Run (Teammates)

This is the fastest path to get a new teammate running the project on **Windows**.

## 0) Prereqs

- Windows 10/11
- Python **3.11.x** installed and available as `py -3.11`
- Git
- (Optional) FFmpeg installed (some video pipelines benefit, but current repo also uses `imageio-ffmpeg`).

> Important: do **not** use Python 3.14 for the final integrated system (PyTorch + How2Sign pkls will break).

## 1) Clone the repo

```powershell
git clone https://github.com/Chida-singh/major-project-updated.git
cd major-project-updated
```

## 2) Create a Python 3.11 virtual environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3) Put datasets in the expected folders (local-only)

This repo does **not** include datasets. Place them locally like this:

### WLASL

- Folder: `WLASL/`
- Expected paths used by scripts:
  - `WLASL/start_kit/WLASL_v0.3.json`
  - `WLASL/start_kit/videos/*.mp4`

> Note: `WLASL/` is git-ignored (except `WLASL/README.md`).

### How2Sign (planned)

- Keep the pkls in a local folder (do not commit)
- Your current example path:
  - `D:\DSCE\Major Project\how2sign_pkls_default_shape\how2sign_pkls_cropTrue_shapeFalse`

> These `.pkl` files are Torch-serialized and often reference `cuda:0`.

## 4) Quick sanity check — single video extraction

```powershell
python tools\pose_pipeline.py single --video path\to\test.mp4 --out out.npy
```

Expected: `out.npy` contains a pose sequence shaped like `(T, 543, 3)`.

## 5) Build a small WLASL pose database (dry run)

If you haven’t already prepared clips, use the helper:

```powershell
python tools\wlasl_setup.py --include-youtube --limit-glosses 50 --max-instances-per-gloss 1
```

Then build the DB:

```powershell
python tools\pose_pipeline.py build-db --limit-glosses 50
```

Outputs (local-only):

- `pose_database/index.json` (small; can be committed)
- `pose_database/<GLOSS>.npy` (large; git-ignored)

## 6) Lookup + offline visualization

```powershell
python tools\pose_pipeline.py lookup --gloss HELP --out help.npy
python tools\pose_pipeline.py viz --npy help.npy --out help.mp4
```

## 7) Where the browser extension lives

- The existing Chrome extension is in `extension/`.
- It currently extracts YouTube transcripts; later it will be upgraded to render the signer overlay.

## Troubleshooting

- If you see MediaPipe model download issues, delete `models/` and retry (it’s a cache).
- If you accidentally committed large files, check `.gitignore` and remove them from git history before pushing.
- If you need PyTorch for How2Sign pkls, stay on Python 3.10/3.11 and install a compatible PyTorch wheel.
