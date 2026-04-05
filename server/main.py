from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi

from asl_pose.db import get_pose_for_gloss


REPO_ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = REPO_ROOT / "web"


app = FastAPI(title="ASL Overlay Website")

app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


class YouTubeTranscriptRequest(BaseModel):
    url: str


class PoseLookupRequest(BaseModel):
    gloss: str


_YT_ID_RE = re.compile(r"(?:v=|/)([0-9A-Za-z_-]{11}).*")


def _extract_youtube_id(url_or_id: str) -> str:
    match = _YT_ID_RE.search(url_or_id)
    if match:
        return match.group(1)
    if len(url_or_id) == 11:
        return url_or_id
    raise ValueError("Invalid YouTube URL or video ID")


@app.get("/")
def index() -> FileResponse:
    index_file = WEB_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=500, detail="web/index.html not found")
    return FileResponse(str(index_file))


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ok": True}


@app.post("/api/transcript/youtube")
def transcript_youtube(req: YouTubeTranscriptRequest) -> dict[str, Any]:
    try:
        video_id = _extract_youtube_id(req.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    try:
        segments = YouTubeTranscriptApi.get_transcript(video_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Transcript fetch failed: {e}") from e

    text = " ".join(seg.get("text", "") for seg in segments).strip()
    return {
        "video_id": video_id,
        "segments": segments,
        "text": text,
    }


@app.post("/api/pose/lookup")
def pose_lookup(req: PoseLookupRequest) -> dict[str, Any]:
    gloss = req.gloss.strip().upper()
    if not gloss:
        raise HTTPException(status_code=400, detail="Missing gloss")

    try:
        pose = get_pose_for_gloss(gloss)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pose lookup failed: {e}") from e

    if pose is None:
        raise HTTPException(status_code=404, detail=f"Gloss not found: {gloss}")

    # pose: (T, 543, 3). Send x,y only for the website demo.
    xy = pose[:, :, :2].tolist()
    return {"gloss": gloss, "frames_xy": xy}
