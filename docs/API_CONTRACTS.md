# API Contracts

This repo is organized as a pipeline. These contracts are the “interfaces” between stages.

## 1) Whisper output (speech → English + timestamps)

**Goal:** produce word-level timing so the overlay can stay synchronized.

Recommended JSON (example):

```json
{
  "source": "whisper-large-v3",
  "language": "en",
  "text": "...full text...",
  "segments": [
    {
      "start": 12.34,
      "end": 18.90,
      "text": "...segment text...",
      "words": [
        {"w": "hello", "start": 12.34, "end": 12.80},
        {"w": "world", "start": 12.80, "end": 13.20}
      ]
    }
  ]
}
```

Notes:
- Times are in seconds.
- If word-level timestamps are unavailable, fall back to segment-level timings.

## 2) GPT‑4o translation output (English → ASL gloss order + NMM)

**Schema (required):**

```json
{
  "glosses": [
    {"w": "HELP", "nmm": ["TOPIC_RAISED_BROWS"], "duration_ms": 600, "confidence": 0.9}
  ],
  "sentence_nmm": ["YESNO_Q"],
  "oov": ["somemissingword"]
}
```

Rules:
- `w` MUST be uppercase.
- `duration_ms` SHOULD be present for synchronization.
- `nmm` tags are optional per gloss but recommended.
- `oov` lists tokens that could not be mapped to dataset vocabulary.

## 3) Pose sequence format (gloss → landmarks)

The pose database stores MediaPipe Holistic landmarks.

- Per gloss file: `pose_database/<GLOSS>.npy` (large; not committed)
- Shape: `(N, 30, 543, 3)`
  - `N` = number of signer instances
  - `30` = fixed frames per gloss (current default)
  - `543` = landmarks
  - `3` = xyz

Canonical lookup output (mean over signers): shape `(30, 543, 3)`.

## 4) Browser transport format (pose → overlay)

For a browser overlay, you will likely transport:

- A list of frames with 2D or 3D points
- A frame rate (fps) or explicit per-frame timestamps

Recommended JSON (debug-friendly; not the most compact):

```json
{
  "fps": 30,
  "frames": [
    [[0.0, 0.0, 0.0], [0.1, 0.0, 0.0], "...543 points..."],
    "..."
  ]
}
```

Compact/binary formats (msgpack, flat arrays) can be introduced later.
