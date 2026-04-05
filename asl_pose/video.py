from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

import os
import urllib.request

from .landmarks import extract_landmarks_from_results


@dataclass(frozen=True)
class VideoProcessConfig:
    model_complexity: int = 1
    min_detection_confidence: float = 0.5
    min_tracking_confidence: float = 0.5
    include_face: bool = True
    include_pose: bool = True
    include_hands: bool = True
    frame_step: int = 1  # >1 = skip frames


_HOLISTIC_TASK_URL = (
    "https://storage.googleapis.com/mediapipe-models/holistic_landmarker/"
    "holistic_landmarker/float16/latest/holistic_landmarker.task"
)


def _ensure_holistic_task_model(model_path: Path) -> Path:
    model_path.parent.mkdir(parents=True, exist_ok=True)
    if model_path.exists() and model_path.stat().st_size > 0:
        return model_path

    tmp_path = model_path.with_suffix(model_path.suffix + ".tmp")
    with urllib.request.urlopen(_HOLISTIC_TASK_URL) as resp:
        tmp_path.write_bytes(resp.read())
    tmp_path.replace(model_path)
    return model_path


def _workspace_root() -> Path:
    # asl_pose/ is at workspace root in this project layout.
    return Path(__file__).resolve().parents[1]


def process_video(
    video_path: str | Path,
    *,
    start_frame: Optional[int] = None,
    end_frame: Optional[int] = None,
    config: VideoProcessConfig | None = None,
) -> np.ndarray | None:
    """Extract a pose sequence from a video.

    - `start_frame`/`end_frame` are interpreted the same way as many dataset
      metadata fields: boundaries are applied while reading sequential frames.
    - Returns `None` if no frames were extracted.

    Output shape (default): (T, 543, 3)
    """

    if config is None:
        config = VideoProcessConfig()

    video_path = Path(video_path)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None

    frames: list[np.ndarray] = []
    frame_idx = 0

    import mediapipe as mp  # local import so import errors show clearly

    # Legacy Solutions API (mp.solutions) may not be present in newer wheels.
    if hasattr(mp, "solutions"):
        mp_holistic = mp.solutions.holistic

        with mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=config.model_complexity,
            min_detection_confidence=config.min_detection_confidence,
            min_tracking_confidence=config.min_tracking_confidence,
        ) as holistic:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if start_frame is not None and frame_idx < start_frame:
                    frame_idx += 1
                    continue
                if end_frame is not None and frame_idx > end_frame:
                    break

                if config.frame_step > 1 and (frame_idx % config.frame_step != 0):
                    frame_idx += 1
                    continue

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = holistic.process(rgb)

                lm = extract_landmarks_from_results(
                    results,
                    include_face=config.include_face,
                    include_pose=config.include_pose,
                    include_hands=config.include_hands,
                )
                frames.append(lm)

                frame_idx += 1
    else:
        # Tasks API (HolisticLandmarker) backend.
        import importlib

        mp_tasks = importlib.import_module("mediapipe.tasks.python")
        vision = mp_tasks.vision
        BaseOptions = mp_tasks.BaseOptions

        model_path_str = os.environ.get("ASL_POSE_HOLISTIC_TASK", "").strip()
        if model_path_str:
            model_path = Path(model_path_str)
        else:
            model_path = _workspace_root() / "models" / "holistic_landmarker.task"
        model_path = _ensure_holistic_task_model(model_path)

        options = vision.HolisticLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            min_face_detection_confidence=config.min_detection_confidence,
            min_face_landmarks_confidence=config.min_tracking_confidence,
            min_pose_detection_confidence=config.min_detection_confidence,
            min_pose_landmarks_confidence=config.min_tracking_confidence,
            min_hand_landmarks_confidence=config.min_tracking_confidence,
        )

        landmarker = vision.HolisticLandmarker.create_from_options(options)
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            if not fps or fps <= 1e-6:
                fps = 30.0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if start_frame is not None and frame_idx < start_frame:
                    frame_idx += 1
                    continue
                if end_frame is not None and frame_idx > end_frame:
                    break

                if config.frame_step > 1 and (frame_idx % config.frame_step != 0):
                    frame_idx += 1
                    continue

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                ts_ms = int(1000.0 * (frame_idx / fps))

                results = landmarker.detect_for_video(mp_image, ts_ms)

                lm = extract_landmarks_from_results(
                    results,
                    include_face=config.include_face,
                    include_pose=config.include_pose,
                    include_hands=config.include_hands,
                )
                frames.append(lm)

                frame_idx += 1
        finally:
            landmarker.close()

    cap.release()

    if not frames:
        return None

    return np.stack(frames, axis=0).astype(np.float32)
