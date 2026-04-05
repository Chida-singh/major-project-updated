from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import numpy as np
from tqdm import tqdm

from .normalize import resample_pose_sequence
from .video import VideoProcessConfig, process_video


def build_pose_database(
    *,
    wlasl_json: str | Path = Path("WLASL/start_kit/WLASL_v0.3.json"),
    videos_dir: str | Path = Path("WLASL/start_kit/videos"),
    output_dir: str | Path = Path("pose_database"),
    target_frames: int = 30,
    min_frames: int = 5,
    limit_glosses: Optional[int] = 50,
    limit_instances_per_gloss: Optional[int] = None,
    use_frame_bounds: bool = False,
    config: VideoProcessConfig | None = None,
) -> list[str]:
    """Process WLASL videos into per-gloss `.npy` files.

    Returns: list of glosses that were successfully saved.

    File format per gloss: (N, target_frames, L, 3)
    - N = number of usable instances/signers
    - L = landmark count (543 by default)
    """

    if config is None:
        config = VideoProcessConfig()

    wlasl_json = Path(wlasl_json)
    videos_dir = Path(videos_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with wlasl_json.open("r", encoding="utf-8") as f:
        wlasl_data = json.load(f)

    if limit_glosses is not None:
        wlasl_data = wlasl_data[:limit_glosses]

    saved: list[str] = []

    for entry in tqdm(wlasl_data, desc="Glosses"):
        gloss = str(entry.get("gloss", "")).upper().strip()
        if not gloss:
            continue

        instances = entry.get("instances", [])
        if limit_instances_per_gloss is not None:
            instances = instances[:limit_instances_per_gloss]

        sequences: list[np.ndarray] = []

        for inst in instances:
            video_id = str(inst.get("video_id", "")).strip()
            if not video_id:
                continue

            video_path = videos_dir / f"{video_id}.mp4"
            if not video_path.exists():
                continue

            start_frame = None
            end_frame = None
            if use_frame_bounds:
                # WLASL json uses 1-indexed frame bounds: frame_start/frame_end.
                frame_start_1 = inst.get("frame_start", inst.get("start_frame"))
                frame_end_1 = inst.get("frame_end", inst.get("end_frame"))

                if frame_start_1 is not None:
                    start_frame = int(frame_start_1) - 1

                if frame_end_1 is not None:
                    end_val = int(frame_end_1)
                    end_frame = None if end_val == -1 else (end_val - 1)

            seq = process_video(video_path, start_frame=start_frame, end_frame=end_frame, config=config)
            if seq is None or seq.shape[0] < min_frames:
                continue

            seq = resample_pose_sequence(seq, target_frames)
            sequences.append(seq)

        if sequences:
            arr = np.stack(sequences, axis=0).astype(np.float32)
            np.save(output_dir / f"{gloss}.npy", arr)
            saved.append(gloss)

    with (output_dir / "index.json").open("w", encoding="utf-8") as f:
        json.dump(saved, f, indent=2)

    return saved


def load_pose_index(output_dir: str | Path = Path("pose_database")) -> set[str]:
    output_dir = Path(output_dir)
    index_path = output_dir / "index.json"
    if not index_path.exists():
        return set()

    with index_path.open("r", encoding="utf-8") as f:
        items = json.load(f)
    return {str(x).upper().strip() for x in items}


def get_pose_for_gloss(
    gloss: str,
    *,
    output_dir: str | Path = Path("pose_database"),
    available_glosses: set[str] | None = None,
) -> np.ndarray | None:
    """Return a canonical pose sequence for a gloss (mean over instances).

    Output shape: (target_frames, L, 3)
    """

    output_dir = Path(output_dir)

    g = gloss.upper().strip()
    if not g:
        return None

    if available_glosses is None:
        available_glosses = load_pose_index(output_dir)

    if g not in available_glosses:
        return None

    npy_path = output_dir / f"{g}.npy"
    if not npy_path.exists():
        return None

    all_instances = np.load(npy_path)
    if all_instances.ndim != 4:
        return None

    return np.mean(all_instances, axis=0).astype(np.float32)
