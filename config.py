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

# Refuse uploads larger than this many megabytes (a 20-minute 48 kHz 32-bit stereo WAV is ~460 MB).
MAX_UPLOAD_MB = 500

# Forget finished jobs in the app after this many minutes (download links stop working).
# Their files stay in jobs/ on disk either way.
JOB_RETENTION_MINUTES = 120

# Default state of the "Strip [section] tags" checkbox in the UI.
STRIP_TAGS_DEFAULT = True

# Format of the downloadable isolated vocal stem: "wav" (exact) or "mp3" (small, 320 kbps).
STEM_FORMAT = "wav"

# Max characters per subtitle line by video format (hard caps, never exceeded).
# Vertical follows 9:16 mobile guidance (~25); horizontal follows the Netflix standard (42).
MAX_CHARS_VERTICAL = 25
MAX_CHARS_HORIZONTAL = 42

# Default video format in the UI: "vertical" (9:16 Reels/TikTok) or "horizontal" (16:9 YouTube).
FORMAT_DEFAULT = "vertical"

# Show each subtitle this many seconds before the vocal actually starts (karaoke practice,
# text never feels late). Set to 0 to disable.
EARLY_APPEAR_SECONDS = 0.2

# Vocal separation engine: "mlx" (Apple Silicon GPU, fast) or "cpu" (cross-platform audio-separator).
# The installer sets this per machine; don't change it unless you know why.
SEPARATOR_ENGINE = "mlx"

# Separation model. Decided by benchmark at Milestone 2 (see DECISIONS.md).
SEPARATOR_MODEL = "htdemucs.yaml"
