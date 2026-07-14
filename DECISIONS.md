# DECISIONS.md — Song SRT Generator V1

Source of truth for build decisions. Where this file and the build brief conflict, this file wins.
Recorded 2026-07-15 from Aman's answers.

## Section 2 answers

1. **Primary machine:** Aman's Mac — Apple M4 Pro, 48 GB RAM, macOS (Darwin 25.5). Build and test here. ffmpeg 8.1 and Python 3.10.5 already installed.
2. **Typical input files:** WAV and MP3 both expected (sample provided is 48 kHz stereo WAV). Accept mp3/wav/m4a/flac per brief.
3. **Lyric section tags:** Strip lines that are only a bracketed tag like `[Chorus]` (default on, checkbox in UI).
4. **Repeated choruses:** On-screen warning only when "x2"-style shorthand is detected. Never refuse to run.
5. **Whisper model:** `medium` via the **faster-whisper** backend of stable-ts. Checked Aman's machine: existing Whisper install is openai-whisper on Python 3.9 with vanilla `.pt` models (incl. large-v3) — different format, not reusable by faster-whisper, and large-v3 would be slower with no alignment-accuracy benefit. App downloads its own CT2 `medium` model once.
6. **Language:** English only for V1 (`LANGUAGE = "en"` in config).
7. **Vocal stem format:** WAV default (Aman: "WAV or MP3 or MPEG all fine" → keeping brief default WAV; switchable via `STEM_FORMAT` in config).
8. **Job retention:** Keep everything in `jobs/`, manual cleanup.
9. **Network:** localhost only (127.0.0.1:7860). LAN opt-in later via `HOST` constant.
10. **Length limits:** Warn > 10 min, refuse > 20 min (brief defaults confirmed).
11. **Sample:** `sample/clip.wav` (17 s, from Aman's "Hook Try.wav") + `sample/lyrics.txt` (2 lines, spoken vocal).
12. **Brief changes:** See stack changes below. Repo root is this folder (`Song to srt Generator/`), not a nested `song-srt-tool/`.

## Stack changes vs the brief (approved by Aman)

- **Aligner:** stable-ts `align()` kept (its forced-alignment API is still best-fit), but running on the **faster-whisper backend** (`load_faster_whisper`) for 2–4× speed. Note: stable-ts repo was archived May 2026 — versions are pinned; acceptable for a local offline tool.
- **Vocal separation:** platform-abstracted `separate_vocals()` interface instead of hard-coded Demucs.
  - **Apple Silicon (build target):** `mlx-audio-separator` (MLX / Apple GPU). Model choice (RoFormer vs htdemucs) decided by benchmark at Milestone 2 on the sample clip.
  - **Windows / Intel (future):** `audio-separator` package, same RoFormer model family → same output quality, CPU speed. Code path written defensively but **untested until Windows hardware is available**.
- **Compute:** CPU-only for alignment in V1 (no CUDA setup, no MPS for torch). Separation uses MLX GPU on Apple Silicon.

## Product/distribution decisions

- **V1 target: Mac only.** Windows support is a stated future requirement — keep the separator abstraction and installer platform-detection ready for it, but do not test on Windows now.
- **Eventually shipped as an installable zip:** unzip → run one installer script → it checks system (Python 3.10/3.11, ffmpeg), detects platform, installs the right dependency set into a venv, downloads models, runs `warmup.py` to PASS, creates start script. User prerequisite: Python installed (fully-bundled standalone app deferred to V2+).
- **Settings live in `config.py` only.** No settings panel in the app UI — UI stays upload → paste → generate.

## Hard rules (unchanged from brief)

No Docker, no databases, no React/JS frameworks, no Electron, no cloud calls at runtime, no paid APIs, no accounts, no telemetry. Python + Gradio only. App must run without any coding agent present.
