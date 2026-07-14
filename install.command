#!/bin/bash
# Song SRT Generator — one-time installer for macOS.
# Double-click this file (or run: bash install.command). Safe to re-run.
set -e
cd "$(dirname "$0")"

echo "=== Song SRT Generator installer (macOS) ==="

# 1. Find Python 3.10 or 3.11
PY=""
for candidate in python3.11 python3.10; do
  if command -v "$candidate" >/dev/null 2>&1; then PY="$candidate"; break; fi
done
if [ -z "$PY" ]; then
  echo ""
  echo "Python 3.10 or 3.11 is required and wasn't found."
  echo "Install it from https://www.python.org/downloads/ (choose 3.11), then run this again."
  exit 1
fi
echo "OK  Using $($PY --version)"

# 2. ffmpeg
if ! command -v ffmpeg >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    echo "Installing ffmpeg with Homebrew..."
    brew install ffmpeg
  else
    echo ""
    echo "ffmpeg is required and wasn't found, and Homebrew isn't installed."
    echo "Either install Homebrew (https://brew.sh) and run this again,"
    echo "or download a static ffmpeg build from https://evermeet.cx/ffmpeg/,"
    echo "unzip it, and move the ffmpeg and ffprobe files into /usr/local/bin/."
    exit 1
  fi
fi
echo "OK  $(ffmpeg -version | head -1)"

# 3. Virtual environment + dependencies (platform-aware)
if [ ! -d .venv ]; then
  echo "Creating virtual environment..."
  "$PY" -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip -q

ARCH="$(uname -m)"
if [ "$ARCH" = "arm64" ]; then
  echo "Apple Silicon detected — installing the MLX (GPU) separation engine..."
  pip install -q -r requirements.txt
else
  echo "Intel Mac detected — installing the CPU separation engine..."
  pip install -q stable-ts faster-whisper fastapi "uvicorn[standard]" python-multipart "audio-separator[cpu]"
  # Tell the app to use the cross-platform engine
  /usr/bin/sed -i '' 's/^SEPARATOR_ENGINE = .*/SEPARATOR_ENGINE = "cpu"/' config.py
fi
echo "OK  Dependencies installed"

# 4. Download models and verify end to end
echo ""
echo "Downloading models and verifying (first time only, needs internet)..."
GRADIO_ANALYTICS_ENABLED=False python warmup.py

echo ""
echo "=== Install complete. Start the app anytime with start.sh (or: python app.py) ==="
