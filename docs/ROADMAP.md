# Roadmap (41 tasks)

Status markers:
- [x] DONE
- [ ] TODO

## Data collection (Week 1–2)

- [ ] 01_apply_how2sign_access — Apply for How2Sign access at how2sign.github.io (do today)
- [ ] 02_download_wlasl_repo — Download WLASL dataset and clone the repo
- [ ] 03_download_asl_citizen_dataset — Download ASL Citizen dataset
- [ ] 04_setup_python310_311_venv — Set up Python 3.10 or 3.11 venv (do NOT use 3.14; How2Sign pkls use PyTorch cuda:0 serialization)
- [ ] 05_install_mediapipe_opencv_whisper_fastapi — Install MediaPipe, OpenCV, Whisper, FastAPI in the same venv

## Pose database (Week 2–3)

- [ ] 06_test_mediapipe_single_video_543 — Test MediaPipe on a single video; verify `(543, 3)` per frame
- [ ] 07_extract_wlasl_overnight — Run MediaPipe extraction across WLASL (overnight)
- [ ] 08_normalize_center_and_scale — Normalize landmarks to canonical body center and scale (mean-over-signers exists, but spatial normalization not yet)
- [x] 09_resample_to_fixed_30_frames — Normalize all sequences to fixed 30 frames
- [ ] 10_visual_verify_15_20_signs — Visually verify 15–20 signs using the visualizer script
- [x] 11_save_index_and_gloss_npys — Save `index.json` and per-gloss `.npy` files
- [ ] 12_add_how2sign_pkls — Add How2Sign pkl data once access arrives and PyTorch env is fixed

## GPT‑4o translation layer (Week 3–4)

- [ ] 13_set_openai_api_key — Get OpenAI API key and set `OPENAI_API_KEY` in env
- [ ] 14_design_system_prompt_json_only — Design system prompt (JSON only, glosses uppercase, include NMM + OOV fields)
- [ ] 15_inject_index_json_vocab — Pass `index.json` gloss list into the prompt to minimize OOV hits
- [ ] 16_eval_50_100_sentences — Test on 50–100 sentences and measure gloss accuracy manually
- [ ] 17_add_whisper_large_v3 — Add Whisper large-v3 for speech-to-text with word-level timestamps
- [ ] 18_map_word_timestamps_to_durations — Map Whisper word timestamps to GPT‑4o gloss durations for sync

## Pose pipeline — connect and fix (Week 4)

- [x] 19_pose_lookup_from_gloss_list — Pose lookup from gloss list (verify `pose_pipeline.py sentence` runs cleanly)
- [ ] 20_oov_fallback_fingerspelling — Replace zero-fill for missing glosses with fingerspelling fallback
- [ ] 21_transition_interpolation_3_5_frames — Add transition interpolation between signs (3–5 blended frames)
- [ ] 22_variable_timing_duration_ms — Add variable timing (use `duration_ms` from GPT‑4o instead of fixed 30 frames)

## NMM conditioning — core IP (Week 4–5)

- [ ] 23_map_nmm_to_face_indices — Map NMM JSON fields to face landmark indices (brow 0–10; mouth 61, 291, 13, 14)
- [ ] 24_brow_raise_and_furrow_offsets — Implement brow raise and furrow as landmark offsets on the face array
- [ ] 25_mouth_morpheme_overlays — Implement mouth morpheme overlays: `mm`, `oo`, `th`
- [ ] 26_verify_face_only_effect — Verify NMM modifications do not affect hand/body landmarks
- [ ] 27_document_nmm_method_precisely — Document the method precisely (patent claim)

## Browser renderer and frontend (Week 5–6)

- [x] 28_offline_opencv_mp4_renderer — Offline OpenCV MP4 renderer exists for export
- [ ] 29_browser_canvas2d_skeleton_renderer — Build browser Canvas 2D skeleton renderer (body, hands, face)
- [ ] 30_define_pose_transport_json_frames — Define transport format for pose sequence to browser (JSON frames array)
- [ ] 31_requestanimationframe_sync_loop — Implement `requestAnimationFrame` loop (video current time → pose frame index)
- [ ] 32_fastapi_translate_realtime_endpoint — Build FastAPI `/translate/realtime` endpoint returning pose JSON
- [ ] 33_extension_canvas_overlay_integration — Connect extension UI to Canvas overlay (replace SMPL‑X call in `content.js` with pose JSON fetch + draw)
- [ ] 34_overlay_controls — Add overlay controls (position, size, handedness toggle)
- [ ] 35_end_to_end_demo_lecture — Run full pipeline on a real lecture video and record the demo

## Evaluation and submission (Week 7–8)

- [ ] 36_bleu4_gloss_eval — Run BLEU-4 on gloss output against reference translations
- [ ] 37_whisper_wer_eval — Measure Whisper WER on test lecture audio
- [ ] 38_deaf_hoh_user_eval — Get 5–10 Deaf/HoH users to evaluate signing quality
- [ ] 39_publish_nmm_subset_hf — Publish NMM-annotated dataset subset on HuggingFace
- [ ] 40_file_provisional_patent_india — File provisional patent at Indian Patent Office
- [ ] 41_write_final_report — Write report with NMM conditioning as primary contribution
