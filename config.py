"""App configuration. Plain constants, edit in a text editor and restart the app."""

# Whisper model size for lyric alignment: "small" is ~3x faster, "medium" is more accurate.
MODEL_SIZE = "medium"

# Lyrics/vocal language (ISO code). V1 is English only.
LANGUAGE = "en"

# Bind address. "127.0.0.1" = this machine only. "0.0.0.0" = teammates on your LAN can open it.
HOST = "127.0.0.1"

# Port the app runs on. Change if something else already uses it.
PORT = 7860

# Compute device for alignment: "auto" picks CUDA if available, else CPU.
DEVICE = "auto"

# Warn the user above this many minutes of audio.
MAX_MINUTES_WARN = 10

# Refuse to process audio above this many minutes.
MAX_MINUTES_HARD = 20

# Default state of the "Strip [section] tags" checkbox in the UI.
STRIP_TAGS_DEFAULT = True

# Format of the downloadable isolated vocal stem: "wav" (exact) or "mp3" (small, 320 kbps).
STEM_FORMAT = "wav"

# Vocal separation engine: "mlx" (Apple Silicon GPU, fast) or "cpu" (cross-platform audio-separator).
# The installer sets this per machine; don't change it unless you know why.
SEPARATOR_ENGINE = "mlx"

# Separation model. Decided by benchmark at Milestone 2 (see DECISIONS.md).
SEPARATOR_MODEL = "htdemucs.yaml"
