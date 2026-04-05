# Legacy: Browser Extension (not used)

This folder contains an older Chrome extension popup that extracts YouTube transcripts.

We are **not** using the extension UI anymore.

## Replacement: website

Use the website instead:

- Backend: `server/`
- Frontend: `web/`

Run:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn server.main:app --reload
```

Open:

- http://127.0.0.1:8000/
