from __future__ import annotations

import numpy as np


def resample_pose_sequence(pose_sequence: np.ndarray, target_frames: int) -> np.ndarray:
    """Resample a pose sequence to a fixed frame length using linear interpolation.

    Input shape: (T, L, 3)
    Output shape: (target_frames, L, 3)
    """

    seq = np.asarray(pose_sequence, dtype=np.float32)

    if seq.ndim != 3:
        raise ValueError(f"Expected shape (T, L, 3), got {seq.shape}")

    t = seq.shape[0]
    if t == 0:
        raise ValueError("Cannot resample an empty sequence")

    if target_frames <= 0:
        raise ValueError("target_frames must be > 0")

    if t == target_frames:
        return seq

    if t == 1:
        return np.repeat(seq, target_frames, axis=0)

    idx = np.linspace(0, t - 1, target_frames)
    idx0 = np.floor(idx).astype(int)
    idx1 = np.clip(idx0 + 1, 0, t - 1)
    alpha = (idx - idx0).astype(np.float32).reshape(-1, 1, 1)

    out = (1.0 - alpha) * seq[idx0] + alpha * seq[idx1]
    return out.astype(np.float32)
