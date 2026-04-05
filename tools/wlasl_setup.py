from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2
from tqdm import tqdm


@dataclass(frozen=True)
class SetupConfig:
    wlasl_json: Path
    work_dir: Path
    raw_dir: Path
    raw_mp4_dir: Path
    videos_dir: Path
    limit_glosses: int | None
    max_instances_per_gloss: int | None
    include_youtube: bool
    sleep_seconds: float


def _load_wlasl_entries(wlasl_json: Path) -> list[dict]:
    with wlasl_json.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("WLASL json must be a list")
    return data


def _iter_instances(
    entries: list[dict],
    *,
    limit_glosses: int | None,
    max_instances_per_gloss: int | None,
) -> Iterable[tuple[str, dict]]:
    if limit_glosses is not None:
        entries = entries[:limit_glosses]

    for entry in entries:
        gloss = str(entry.get("gloss", "")).upper().strip()
        instances = entry.get("instances", [])
        if max_instances_per_gloss is not None:
            instances = instances[:max_instances_per_gloss]

        for inst in instances:
            yield gloss, inst


def _request_bytes(url: str, *, referer: str | None = None) -> bytes:
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
    headers = {"User-Agent": user_agent}
    if referer:
        headers["Referer"] = referer

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def _download_direct(url: str, dst: Path, *, referer: str | None = None, sleep_seconds: float = 0.0) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and dst.stat().st_size > 0:
        return

    data = _request_bytes(url, referer=referer)
    dst.write_bytes(data)
    if sleep_seconds > 0:
        time.sleep(sleep_seconds)


def _download_youtube(url: str, raw_dir: Path) -> None:
    """Download a YouTube url into raw_dir using yt-dlp (Python API)."""
    import yt_dlp

    raw_dir.mkdir(parents=True, exist_ok=True)
    ydl_opts = {
        "outtmpl": str(raw_dir / "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "retries": 3,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def _ensure_mp4(src: Path, dst: Path) -> None:
    """Convert/copy any input video to mp4 at dst."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and dst.stat().st_size > 0:
        return

    if src.suffix.lower() == ".mp4":
        shutil.copyfile(src, dst)
        return

    from imageio_ffmpeg import get_ffmpeg_exe

    ffmpeg = get_ffmpeg_exe()

    # Ensure even width/height via pad filter (same idea as WLASL bash script).
    cmd = (
        f'"{ffmpeg}" -y -loglevel error -i "{src}" '
        "-vf pad=width=ceil(iw/2)*2:height=ceil(ih/2)*2 "
        f'"{dst}"'
    )
    rv = os.system(cmd)
    if rv != 0 or not dst.exists():
        raise RuntimeError(f"ffmpeg conversion failed for {src.name}")


def _extract_segment_to_video(
    src_mp4: Path,
    dst_mp4: Path,
    *,
    frame_start_1_indexed: int | None,
    frame_end_1_indexed: int | None,
    fps: int = 25,
) -> None:
    dst_mp4.parent.mkdir(parents=True, exist_ok=True)
    if dst_mp4.exists() and dst_mp4.stat().st_size > 0:
        return

    # If frame_end is -1 (WLASL convention), copy full video.
    if frame_end_1_indexed is not None and frame_end_1_indexed <= 0:
        shutil.copyfile(src_mp4, dst_mp4)
        return

    cap = cv2.VideoCapture(str(src_mp4))
    if not cap.isOpened():
        raise RuntimeError(f"OpenCV cannot open: {src_mp4}")

    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()

    if not frames:
        raise RuntimeError(f"No frames read from: {src_mp4}")

    # JSON is indexed from 1 in WLASL docs.
    start0 = (frame_start_1_indexed - 1) if frame_start_1_indexed else 0
    end0 = (frame_end_1_indexed - 1) if frame_end_1_indexed else (len(frames) - 1)

    start0 = max(0, min(start0, len(frames) - 1))
    end0 = max(0, min(end0, len(frames) - 1))
    if end0 < start0:
        start0, end0 = end0, start0

    selected = frames[start0 : end0 + 1]
    h, w = selected[0].shape[:2]

    out = cv2.VideoWriter(str(dst_mp4), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for f in selected:
        out.write(f)
    out.release()


def run_setup(cfg: SetupConfig) -> None:
    cfg.work_dir.mkdir(parents=True, exist_ok=True)
    cfg.raw_dir.mkdir(parents=True, exist_ok=True)
    cfg.raw_mp4_dir.mkdir(parents=True, exist_ok=True)
    cfg.videos_dir.mkdir(parents=True, exist_ok=True)

    entries = _load_wlasl_entries(cfg.wlasl_json)

    jobs = list(
        _iter_instances(
            entries,
            limit_glosses=cfg.limit_glosses,
            max_instances_per_gloss=cfg.max_instances_per_gloss,
        )
    )

    # Download phase
    for _, inst in tqdm(jobs, desc="Downloading"):
        url = str(inst.get("url", ""))
        video_id = str(inst.get("video_id", "")).strip()
        if not url or not video_id:
            continue

        if ("youtube" in url) or ("youtu.be" in url):
            if not cfg.include_youtube:
                continue
            try:
                _download_youtube(url, cfg.raw_dir)
            except Exception:
                # Keep going; many URLs die over time.
                continue
        elif "aslpro" in url:
            # ASLPro sometimes needs a referer.
            try:
                _download_direct(
                    url,
                    cfg.raw_dir / f"{video_id}.swf",
                    referer="http://www.aslpro.com/cgi-bin/aslpro/aslpro.cgi",
                    sleep_seconds=cfg.sleep_seconds,
                )
            except Exception:
                continue
        else:
            try:
                _download_direct(url, cfg.raw_dir / f"{video_id}.mp4", sleep_seconds=cfg.sleep_seconds)
            except Exception:
                continue

    # Convert to mp4 phase
    raw_files = list(cfg.raw_dir.glob("*"))
    for src in tqdm(raw_files, desc="Converting"):
        stem = src.stem
        dst = cfg.raw_mp4_dir / f"{stem}.mp4"
        try:
            _ensure_mp4(src, dst)
        except Exception:
            continue

    # Preprocess/cut to per-instance videos/video_id.mp4
    for _, inst in tqdm(jobs, desc="Preprocessing"):
        url = str(inst.get("url", ""))
        video_id = str(inst.get("video_id", "")).strip()
        if not url or not video_id:
            continue

        if ("youtube" in url) or ("youtu.be" in url):
            yt_identifier = url[-11:]
            src_mp4 = cfg.raw_mp4_dir / f"{yt_identifier}.mp4"
        else:
            src_mp4 = cfg.raw_mp4_dir / f"{video_id}.mp4"

        if not src_mp4.exists():
            continue

        dst_mp4 = cfg.videos_dir / f"{video_id}.mp4"

        frame_start = inst.get("frame_start")
        frame_end = inst.get("frame_end")

        try:
            _extract_segment_to_video(
                src_mp4,
                dst_mp4,
                frame_start_1_indexed=int(frame_start) if frame_start is not None else None,
                frame_end_1_indexed=int(frame_end) if frame_end is not None else None,
                fps=int(inst.get("fps", 25) or 25),
            )
        except Exception:
            continue


def main() -> int:
    p = argparse.ArgumentParser(description="Windows-friendly WLASL download + preprocess")
    p.add_argument("--wlasl-json", default="WLASL/start_kit/WLASL_v0.3.json")
    p.add_argument("--work-dir", default="WLASL/start_kit")
    p.add_argument("--limit-glosses", type=int, default=50)
    p.add_argument("--max-instances-per-gloss", type=int, default=1)
    p.add_argument("--include-youtube", action="store_true")
    p.add_argument("--sleep-seconds", type=float, default=0.0)
    args = p.parse_args()

    work_dir = Path(args.work_dir)
    cfg = SetupConfig(
        wlasl_json=Path(args.wlasl_json),
        work_dir=work_dir,
        raw_dir=work_dir / "raw_videos",
        raw_mp4_dir=work_dir / "raw_videos_mp4",
        videos_dir=work_dir / "videos",
        limit_glosses=args.limit_glosses,
        max_instances_per_gloss=args.max_instances_per_gloss,
        include_youtube=bool(args.include_youtube),
        sleep_seconds=float(args.sleep_seconds),
    )

    run_setup(cfg)
    print(f"Done. Preprocessed videos are in: {cfg.videos_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
