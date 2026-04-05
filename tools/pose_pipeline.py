from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from asl_pose.db import build_pose_database, get_pose_for_gloss, load_pose_index
from asl_pose.normalize import resample_pose_sequence
from asl_pose.video import VideoProcessConfig, process_video
from asl_pose.viz import visualize_pose_sequence


def _cmd_single(args: argparse.Namespace) -> int:
    cfg = VideoProcessConfig(
        model_complexity=args.model_complexity,
        min_detection_confidence=args.min_detection_confidence,
        min_tracking_confidence=args.min_tracking_confidence,
        include_face=not args.no_face,
        include_pose=True,
        include_hands=True,
        frame_step=args.frame_step,
        use_gpu=bool(getattr(args, "gpu", False)),
    )

    seq = process_video(args.video, start_frame=args.start_frame, end_frame=args.end_frame, config=cfg)
    if seq is None:
        raise SystemExit("No frames extracted (bad path or unreadable video)")

    if args.target_frames:
        seq = resample_pose_sequence(seq, args.target_frames)

    print(f"Sequence shape: {seq.shape}")
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        np.save(out, seq.astype(np.float32))
        print(f"Saved: {out}")

    return 0


def _cmd_build_db(args: argparse.Namespace) -> int:
    cfg = VideoProcessConfig(
        model_complexity=args.model_complexity,
        min_detection_confidence=args.min_detection_confidence,
        min_tracking_confidence=args.min_tracking_confidence,
        include_face=not args.no_face,
        include_pose=True,
        include_hands=True,
        frame_step=args.frame_step,
        use_gpu=bool(args.gpu),
    )

    saved = build_pose_database(
        wlasl_json=args.wlasl_json,
        videos_dir=args.videos_dir,
        output_dir=args.output_dir,
        target_frames=args.target_frames,
        min_frames=args.min_frames,
        limit_glosses=args.limit_glosses,
        limit_instances_per_gloss=args.limit_instances_per_gloss,
        use_frame_bounds=args.use_frame_bounds,
        config=cfg,
    )

    print(f"Saved {len(saved)} glosses to {args.output_dir}")
    return 0


def _cmd_lookup(args: argparse.Namespace) -> int:
    available = load_pose_index(args.output_dir)
    pose = get_pose_for_gloss(args.gloss, output_dir=args.output_dir, available_glosses=available)
    if pose is None:
        raise SystemExit(f"Gloss not found in index: {args.gloss}")

    print(f"Canonical pose shape: {pose.shape}")

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        np.save(out, pose.astype(np.float32))
        print(f"Saved: {out}")

    return 0


def _cmd_sentence(args: argparse.Namespace) -> int:
    available = load_pose_index(args.output_dir)

    glosses = [g.upper().strip() for g in args.glosses]
    sequences = []
    missing = []

    for g in glosses:
        pose = get_pose_for_gloss(g, output_dir=args.output_dir, available_glosses=available)
        if pose is None:
            missing.append(g)
            pose = np.zeros((args.target_frames, 543, 3), dtype=np.float32)
        sequences.append(pose)

    full = np.concatenate(sequences, axis=0)
    print(f"Full sequence shape: {full.shape}")

    if missing:
        print("Missing glosses:")
        print(json.dumps(missing, indent=2))

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        np.save(out, full.astype(np.float32))
        print(f"Saved: {out}")

    return 0


def _cmd_viz(args: argparse.Namespace) -> int:
    pose = np.load(args.npy)

    # Accept either (T, 543, 3) OR (543, 3) (single frame)
    if pose.ndim == 2:
        pose = pose[None, ...]

    visualize_pose_sequence(pose, args.out, fps=args.fps)
    print(f"Saved: {args.out}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="MediaPipe Holistic pose extraction pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_single = sub.add_parser("single", help="Extract pose sequence from a single video")
    p_single.add_argument("--video", required=True)
    p_single.add_argument("--out", default=None)
    p_single.add_argument("--start-frame", type=int, default=None)
    p_single.add_argument("--end-frame", type=int, default=None)
    p_single.add_argument("--target-frames", type=int, default=None)
    p_single.add_argument("--model-complexity", type=int, default=1)
    p_single.add_argument("--min-detection-confidence", type=float, default=0.5)
    p_single.add_argument("--min-tracking-confidence", type=float, default=0.5)
    p_single.add_argument("--frame-step", type=int, default=1)
    p_single.add_argument("--no-face", action="store_true")
    p_single.add_argument("--gpu", action="store_true", help="Use MediaPipe Tasks GPU delegate when available")
    p_single.set_defaults(func=_cmd_single)

    p_db = sub.add_parser("build-db", help="Build per-gloss .npy database from WLASL")
    p_db.add_argument("--wlasl-json", default="WLASL/start_kit/WLASL_v0.3.json")
    p_db.add_argument("--videos-dir", default="WLASL/start_kit/videos")
    p_db.add_argument("--output-dir", default="pose_database")
    p_db.add_argument("--target-frames", type=int, default=30)
    p_db.add_argument("--min-frames", type=int, default=5)
    p_db.add_argument("--limit-glosses", type=int, default=50)
    p_db.add_argument("--limit-instances-per-gloss", type=int, default=None)
    p_db.add_argument("--model-complexity", type=int, default=1)
    p_db.add_argument("--min-detection-confidence", type=float, default=0.5)
    p_db.add_argument("--min-tracking-confidence", type=float, default=0.5)
    p_db.add_argument("--frame-step", type=int, default=1)
    p_db.add_argument("--no-face", action="store_true")
    p_db.add_argument("--gpu", action="store_true")
    p_db.add_argument(
        "--use-frame-bounds",
        action="store_true",
        help="Apply WLASL frame_start/frame_end bounds on videos (use only for raw/untrimmed videos)",
    )
    p_db.set_defaults(func=_cmd_build_db)

    p_lookup = sub.add_parser("lookup", help="Load + average instances for a gloss")
    p_lookup.add_argument("--output-dir", default="pose_database")
    p_lookup.add_argument("--gloss", required=True)
    p_lookup.add_argument("--out", default=None)
    p_lookup.set_defaults(func=_cmd_lookup)

    p_sentence = sub.add_parser("sentence", help="Concatenate multiple glosses")
    p_sentence.add_argument("--output-dir", default="pose_database")
    p_sentence.add_argument("--target-frames", type=int, default=30)
    p_sentence.add_argument("--out", default=None)
    p_sentence.add_argument("glosses", nargs="+")
    p_sentence.set_defaults(func=_cmd_sentence)

    p_viz = sub.add_parser("viz", help="Render a .npy pose sequence to mp4")
    p_viz.add_argument("--npy", required=True)
    p_viz.add_argument("--out", required=True)
    p_viz.add_argument("--fps", type=float, default=15.0)
    p_viz.set_defaults(func=_cmd_viz)

    args = p.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
