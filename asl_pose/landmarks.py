from __future__ import annotations

import numpy as np

LANDMARKS_FACE = 468
LANDMARKS_POSE = 33
LANDMARKS_HAND = 21
TOTAL_LANDMARKS = LANDMARKS_FACE + LANDMARKS_POSE + 2 * LANDMARKS_HAND  # 543


def _landmark_list_to_array(landmarks, expected: int) -> np.ndarray:
    if landmarks is None:
        return np.zeros((expected, 3), dtype=np.float32)

    # Legacy Solutions API provides an object with `.landmark`.
    # Tasks API provides a plain list of landmark objects.
    lm_list = getattr(landmarks, "landmark", landmarks)

    pts = np.array([[lm.x, lm.y, lm.z] for lm in lm_list], dtype=np.float32).reshape(-1, 3)
    if pts.shape != (expected, 3):
        # Defensive: MediaPipe should always return expected counts.
        out = np.zeros((expected, 3), dtype=np.float32)
        n = min(expected, pts.shape[0])
        out[:n] = pts[:n]
        return out
    return pts


def extract_landmarks_from_results(
    results,
    *,
    include_face: bool = True,
    include_pose: bool = True,
    include_hands: bool = True,
) -> np.ndarray:
    """Convert a MediaPipe Holistic `results` object into a stacked landmark array.

    Returns shape:
    - Full (default): (543, 3) = face(468) + pose(33) + left(21) + right(21)
    - If disabling parts, the returned shape changes accordingly.

    Values are MediaPipe-normalized coordinates (x,y in [0,1] typically), z in a
    model-dependent scale.
    """

    parts: list[np.ndarray] = []

    if include_face:
        parts.append(_landmark_list_to_array(getattr(results, "face_landmarks", None), LANDMARKS_FACE))
    if include_pose:
        parts.append(_landmark_list_to_array(getattr(results, "pose_landmarks", None), LANDMARKS_POSE))
    if include_hands:
        parts.append(_landmark_list_to_array(getattr(results, "left_hand_landmarks", None), LANDMARKS_HAND))
        parts.append(_landmark_list_to_array(getattr(results, "right_hand_landmarks", None), LANDMARKS_HAND))

    if not parts:
        return np.zeros((0, 3), dtype=np.float32)

    return np.concatenate(parts, axis=0)
