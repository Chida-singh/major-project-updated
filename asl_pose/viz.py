from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile

import cv2
import numpy as np


# Minimal connection lists for drawing.
POSE_CONNECTIONS: list[tuple[int, int]] = [
    (0, 1), (1, 2), (2, 3), (3, 7),
    (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10),
    (11, 12),
    (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
    (11, 23), (12, 24), (23, 24),
    (23, 25), (25, 27), (27, 29), (27, 31),
    (24, 26), (26, 28), (28, 30), (28, 32),
    (29, 31), (30, 32),
]

HAND_CONNECTIONS: list[tuple[int, int]] = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]


def visualize_pose_sequence(
    pose_sequence: np.ndarray,
    output_path: str | Path,
    *,
    fps: float = 15.0,
    canvas_size: tuple[int, int] = (640, 480),
) -> None:
    """Render pose+hands from a (T, 543, 3) sequence onto a white canvas."""

    output_path = Path(output_path)
    w, h = canvas_size

    seq = np.asarray(pose_sequence)
    if seq.ndim != 3 or seq.shape[1] < 543 or seq.shape[2] < 2:
        raise ValueError(f"Expected shape (T, 543, 3), got {seq.shape}")

    # OpenCV's MP4 codecs are often not playable out-of-the-box on Windows.
    # Strategy:
    # - Always render frames into a temporary MJPG .avi (widely decodable)
    # - If the user asked for .mp4, transcode to H.264 using ffmpeg.
    requested_suffix = output_path.suffix.lower()
    want_mp4 = requested_suffix == ".mp4"

    tmp_dir = Path(tempfile.mkdtemp(prefix="asl_pose_viz_"))
    tmp_avi = tmp_dir / "render.avi"

    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    out = cv2.VideoWriter(str(tmp_avi), fourcc, fps, (w, h))
    if not out.isOpened():
        raise RuntimeError(
            "OpenCV VideoWriter failed to open. "
            "Try a different output path, or install a full ffmpeg build."
        )

    for frame_landmarks in seq:
        canvas = np.full((h, w, 3), 255, dtype=np.uint8)

        # Landmarks layout depends on whether face landmarks were included.
        # - Full holistic: face(468) + pose(33) + left(21) + right(21) = 543
        # - No-face: pose(33) + left(21) + right(21) = 75
        landmark_count = int(frame_landmarks.shape[0])
        if landmark_count >= 543:
            pose_start = 468
            left_start = 501
            right_start = 522
        elif landmark_count >= (33 + 21 + 21):
            pose_start = 0
            left_start = 33
            right_start = 54
        else:
            raise ValueError(f"Unsupported landmark count: {landmark_count}")

        pose_lms = frame_landmarks[pose_start : pose_start + 33]
        for (s, e) in POSE_CONNECTIONS:
            if s < len(pose_lms) and e < len(pose_lms):
                x1, y1 = int(pose_lms[s, 0] * w), int(pose_lms[s, 1] * h)
                x2, y2 = int(pose_lms[e, 0] * w), int(pose_lms[e, 1] * h)
                cv2.line(canvas, (x1, y1), (x2, y2), (100, 100, 200), 2)

        left = frame_landmarks[left_start : left_start + 21]
        for (s, e) in HAND_CONNECTIONS:
            if s < len(left) and e < len(left):
                x1, y1 = int(left[s, 0] * w), int(left[s, 1] * h)
                x2, y2 = int(left[e, 0] * w), int(left[e, 1] * h)
                cv2.line(canvas, (x1, y1), (x2, y2), (50, 180, 100), 2)

        right = frame_landmarks[right_start : right_start + 21]
        for (s, e) in HAND_CONNECTIONS:
            if s < len(right) and e < len(right):
                x1, y1 = int(right[s, 0] * w), int(right[s, 1] * h)
                x2, y2 = int(right[e, 0] * w), int(right[e, 1] * h)
                cv2.line(canvas, (x1, y1), (x2, y2), (200, 100, 50), 2)

        out.write(canvas)

    out.release()

    if not tmp_avi.exists() or tmp_avi.stat().st_size == 0:
        raise RuntimeError("Visualization render produced an empty video file")

    if not want_mp4:
        # If user requested a non-mp4 path, just move the AVI there.
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_avi.replace(output_path)
        return

    # Transcode AVI -> H.264 MP4 for maximum compatibility.
    from imageio_ffmpeg import get_ffmpeg_exe

    ffmpeg = get_ffmpeg_exe()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(tmp_avi),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output_path),
    ]

    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        # If ffmpeg fails, keep the AVI next to the requested MP4 name.
        fallback = output_path.with_suffix(".avi")
        try:
            tmp_avi.replace(fallback)
        except Exception:
            pass
        raise RuntimeError(
            f"ffmpeg transcode failed ({type(e).__name__}: {e}). "
            f"Kept AVI fallback at: {fallback}"
        )
