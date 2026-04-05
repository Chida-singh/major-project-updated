# Browser Extension (current)

This folder contains the existing Chrome extension that can extract YouTube transcripts.

## What it does now

- Runs on `youtube.com/watch` pages.
- Extracts transcript text (DOM-based + API fallback).
- Shows transcript in the popup and can download a `transcript.json`.

## How this fits the final pipeline

This extension is the **frontend shell** we will extend in Stage 7:

- Replace “transcript-only” usage with a Canvas overlay that draws the signer.
- Call the backend `FastAPI /translate/realtime` endpoint to fetch pose frames.
- Sync poses to the video `currentTime`.

See `docs/ROADMAP.md` tasks `29_...` → `34_...` for the planned changes.
