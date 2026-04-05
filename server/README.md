# Website backend (`server/`)

This folder contains the FastAPI app that serves a local website.

## Run

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn server.main:app --reload
```

Then open:

- http://127.0.0.1:8000/

## Endpoints (current)

- `GET /` — website UI
- `POST /api/transcript/youtube` — server-side transcript fetch via `youtube_transcript_api`
- `POST /api/pose/lookup` — demo: lookup pose frames for a gloss (requires local `pose_database/`)
