from __future__ import annotations

from pathlib import Path

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

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (w, h))

    seq = np.asarray(pose_sequence)
    if seq.ndim != 3 or seq.shape[1] < 543 or seq.shape[2] < 2:
        raise ValueError(f"Expected shape (T, 543, 3), got {seq.shape}")

    for frame_landmarks in seq:
        canvas = np.full((h, w, 3), 255, dtype=np.uint8)

        # Pose is 33 points starting at index 468
        pose_lms = frame_landmarks[468:501]
        for (s, e) in POSE_CONNECTIONS:
            if s < len(pose_lms) and e < len(pose_lms):
                x1, y1 = int(pose_lms[s, 0] * w), int(pose_lms[s, 1] * h)
                x2, y2 = int(pose_lms[e, 0] * w), int(pose_lms[e, 1] * h)
                cv2.line(canvas, (x1, y1), (x2, y2), (100, 100, 200), 2)

        # Left hand is 21 points starting at index 501
        left = frame_landmarks[501:522]
        for (s, e) in HAND_CONNECTIONS:
            if s < len(left) and e < len(left):
                x1, y1 = int(left[s, 0] * w), int(left[s, 1] * h)
                x2, y2 = int(left[e, 0] * w), int(left[e, 1] * h)
                cv2.line(canvas, (x1, y1), (x2, y2), (50, 180, 100), 2)

        # Right hand is 21 points starting at index 522
        right = frame_landmarks[522:543]
        for (s, e) in HAND_CONNECTIONS:
            if s < len(right) and e < len(right):
                x1, y1 = int(right[s, 0] * w), int(right[s, 1] * h)
                x2, y2 = int(right[e, 0] * w), int(right[e, 1] * h)
                cv2.line(canvas, (x1, y1), (x2, y2), (200, 100, 50), 2)

        out.write(canvas)

    out.release()
