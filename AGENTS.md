# Song SRT Generator — setup and run guide

You are the installer and operator of this app. Set it up on this machine, verify it, then run it.

This app takes an AI-generated song + its ground-truth lyrics and produces a timestamped SRT by forced alignment (never transcription). Pipeline: audio → vocal isolation → align pasted lyrics to the vocal stem → SRT. Fully offline after one-time model downloads.

## 1. Preflight

- Detect the OS (`uname` on Mac/Linux, or Windows).
- `python3 --version` — need **3.10 or 3.11** (on Mac try `python3.11 --version`, `python3.10 --version`; on Windows `py -3.11 --version`). Not 3.12+.
- `ffmpeg -version` — must be on PATH.

## 2. Install ffmpeg if missing

- **macOS:** `brew install ffmpeg`. No Homebrew/admin: download a static build from https://evermeet.cx/ffmpeg/ (both `ffmpeg` and `ffprobe`), unzip, move both into `/usr/local/bin/` (or any folder on PATH).
- **Windows:** `winget install Gyan.FFmpeg`, or Chocolatey `choco install ffmpeg`. No admin rights: download the "essentials" zip from https://www.gyan.dev/ffmpeg/builds/, unzip to `C:\Users\<name>\ffmpeg`, then add `C:\Users\<name>\ffmpeg\bin` to the user PATH (Settings → System → About → Advanced system settings → Environment Variables → Path → Edit → New). Open a NEW terminal afterwards.

## 3. Environment

The scripted way (preferred): run `bash install.command` (macOS) or `install.bat` (Windows). It does everything in this section and section 4, platform-aware. Manual equivalent:

- `python3.11 -m venv .venv` (or 3.10)
- Activate: `source .venv/bin/activate` (Mac/Linux) or `.venv\Scripts\activate.bat` (Windows)
- **Apple Silicon Mac:** `pip install -r requirements.txt` (pinned; includes the MLX GPU separation engine). Keep `SEPARATOR_ENGINE = "mlx"` in config.py.
- **Windows / Intel Mac:** install the CPU torch wheel explicitly first if default resolution fails: `pip install torch --index-url https://download.pytorch.org/whl/cpu`, then `pip install stable-ts faster-whisper gradio "audio-separator[cpu]"`, and set `SEPARATOR_ENGINE = "cpu"` in config.py. (requirements.txt is the Apple Silicon pin set — don't use it on Windows.)

## 4. First-run verification

Run `python warmup.py`. It downloads the separation and alignment models (~2 GB total, internet needed once), runs the full pipeline on `sample/`, and checks that an SRT with at least one cue was produced. **Setup is not complete until it prints PASS** with per-stage timings.

## 5. Launch

`python app.py` — the browser opens automatically at http://127.0.0.1:7860. Every later use: run `start.sh` / `start.bat` or `python app.py` again. One job runs at a time; a second submit queues.

## 6. Troubleshooting

| Symptom | Fix |
|---|---|
| `ffmpeg not found` | Section 2 above; open a new terminal after installing. |
| torch install fails on Windows | `pip install torch --index-url https://download.pytorch.org/whl/cpu` first, then the rest. |
| Out of memory during a job | Open config.py, set `MODEL_SIZE = "small"`, restart the app. |
| Port busy at launch | Change `PORT` in config.py. |
| First job is slow | One-time model load into memory; later jobs are much faster. Model *downloads* only happen during warmup. |
| No internet during setup | Models can't download — setup requires internet once. Runtime is fully offline afterwards. |
| `Model conversion requires the [convert] extras` (Apple Silicon) | `pip install 'mlx-audio-separator[convert]'` (already in requirements.txt). |

## 7. Rules for the agent

- Never install packages globally outside the venv — the only system-level installs allowed are ffmpeg and Python themselves.
- Never change files outside this folder.
- Never send any project file anywhere.
