"""Song SRT Generator — processing pipeline.

All logic lives here; app.py is UI-only. Also runnable from the CLI:

    python pipeline.py <audio> <lyrics.txt>
"""

import json
import logging
import re
import shutil
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

import config

ROOT = Path(__file__).parent
JOBS_DIR = ROOT / "jobs"
MODELS_DIR = ROOT / "models"

ACCEPTED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac"}

MIN_CUE_SECONDS = 0.6
OVERLAP_GAP = 0.010  # 10 ms pulled between overlapping cues

# Lazily loaded, cached across jobs so only the first run pays model-load time.
_align_model = None


class PipelineError(Exception):
    """Error with a message safe to show in the UI. Details go to the job log."""


# ---------------------------------------------------------------------------
# Stage 0: validate

def probe_duration(audio_path: Path) -> float:
    """Return audio duration in seconds via ffprobe."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
            capture_output=True, text=True, timeout=60,
        )
    except FileNotFoundError:
        raise PipelineError(
            "ffmpeg isn't installed or isn't on PATH. Re-run the setup guide (CLAUDE.md / README)."
        )
    try:
        return float(out.stdout.strip())
    except ValueError:
        raise PipelineError("Couldn't read this audio file. Use MP3, WAV, M4A, or FLAC.")


def validate_audio(audio_path: Path) -> tuple[float, str | None]:
    """Return (duration_seconds, warning_or_None). Raises PipelineError on hard failures."""
    if audio_path.suffix.lower() not in ACCEPTED_EXTENSIONS:
        raise PipelineError("Couldn't read this audio file. Use MP3, WAV, M4A, or FLAC.")
    if not audio_path.exists():
        raise PipelineError("Couldn't read this audio file. Use MP3, WAV, M4A, or FLAC.")
    duration = probe_duration(audio_path)
    if duration > config.MAX_MINUTES_HARD * 60:
        raise PipelineError(
            f"This file is over the {config.MAX_MINUTES_HARD} minute limit for this tool."
        )
    warning = None
    if duration > config.MAX_MINUTES_WARN * 60:
        warning = (
            f"Heads up: this file is over {config.MAX_MINUTES_WARN} minutes, "
            "processing will take a while."
        )
    return duration, warning


# ---------------------------------------------------------------------------
# Stage 1: preprocess lyrics

SECTION_TAG = re.compile(r"^\[.*\]$")
REPEAT_SHORTHAND = re.compile(r"\bx\s?\d+\b", re.IGNORECASE)

REPEAT_WARNING = (
    "Possible repeat shorthand like \"x2\" detected in the lyrics. "
    "Write out every repeated chorus in full or the timing will be wrong."
)


def preprocess_lyrics(raw_text: str, strip_tags: bool = True) -> tuple[list[str], str | None]:
    """Return (lyric_lines, warning_or_None). Raises PipelineError if nothing remains."""
    lines = []
    warning = None
    for line in raw_text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = re.sub(r" {2,}", " ", line.strip())
        if not line:
            continue
        if strip_tags and SECTION_TAG.match(line):
            continue
        if REPEAT_SHORTHAND.search(line):
            warning = REPEAT_WARNING
        lines.append(line)
    if not lines:
        raise PipelineError(
            "Lyrics are empty. Paste the lyrics exactly as sung, one line per subtitle."
        )
    return lines, warning


# ---------------------------------------------------------------------------
# Stage 2: vocal isolation

def separate_vocals(audio_path: Path, job_dir: Path, log: logging.Logger) -> Path:
    """Isolate the vocal stem into job_dir/vocals.wav using the configured engine."""
    if config.SEPARATOR_ENGINE == "mlx":
        return _separate_mlx(audio_path, job_dir, log)
    return _separate_cpu(audio_path, job_dir, log)


def _find_vocals_output(job_dir: Path) -> Path:
    target = job_dir / "vocals.wav"
    if target.exists():
        return target
    candidates = [p for p in job_dir.glob("*.wav") if "vocal" in p.name.lower()]
    if not candidates:
        raise PipelineError(
            "Couldn't isolate the vocals from this song. Check the job log for details."
        )
    candidates[0].rename(target)
    return target


def _separate_mlx(audio_path: Path, job_dir: Path, log: logging.Logger) -> Path:
    """Apple Silicon path: mlx-audio-separator on the GPU."""
    from mlx_audio_separator import Separator

    separator = Separator(
        log_level=logging.INFO,
        model_file_dir=str(MODELS_DIR),
        output_dir=str(job_dir),
        output_format="WAV",
        output_single_stem="Vocals",
    )
    separator.load_model(model_filename=config.SEPARATOR_MODEL)
    separator.separate(str(audio_path), custom_output_names={"Vocals": "vocals"})
    return _find_vocals_output(job_dir)


def _separate_cpu(audio_path: Path, job_dir: Path, log: logging.Logger) -> Path:
    """Cross-platform path (Windows / Intel Mac): audio-separator on CPU.

    NOTE: untested until Windows hardware is available — see DECISIONS.md.
    """
    try:
        from audio_separator.separator import Separator
    except ImportError:
        raise PipelineError(
            "The CPU separation engine isn't installed on this machine. "
            "Re-run the installer, or set SEPARATOR_ENGINE in config.py to 'mlx' on Apple Silicon."
        )
    separator = Separator(
        log_level=logging.INFO,
        model_file_dir=str(MODELS_DIR),
        output_dir=str(job_dir),
        output_format="WAV",
        output_single_stem="Vocals",
    )
    separator.load_model(model_filename=config.SEPARATOR_MODEL)
    separator.separate(str(audio_path), custom_output_names={"Vocals": "vocals"})
    return _find_vocals_output(job_dir)


# ---------------------------------------------------------------------------
# Stage 3: forced alignment

def _load_align_model():
    global _align_model
    if _align_model is None:
        import stable_whisper

        device = config.DEVICE
        if device == "auto":
            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
        _align_model = stable_whisper.load_faster_whisper(config.MODEL_SIZE, device=device)
    return _align_model


ALIGN_FAILURE_MESSAGE = (
    "Couldn't align these lyrics to this song. Two usual causes: the lyrics "
    "don't match what is actually sung, or repeated choruses aren't written "
    "out in full. Fix the lyrics and try again."
)


def align_lyrics(vocals_path: Path, lyric_lines: list[str], log: logging.Logger):
    """Force-align lyric lines to the vocal stem. Returns a stable-ts result."""
    model = _load_align_model()
    text = "\n".join(lyric_lines)
    try:
        result = model.align(
            str(vocals_path), text, language=config.LANGUAGE, original_split=True
        )
    except MemoryError:
        raise PipelineError(
            "This machine ran out of memory. Open config.py and set MODEL_SIZE "
            "to 'small', then restart the app."
        )
    except Exception:
        log.error("Alignment raised:\n%s", traceback.format_exc())
        raise PipelineError(ALIGN_FAILURE_MESSAGE)
    if not result.segments:
        raise PipelineError(ALIGN_FAILURE_MESSAGE)
    return result


# ---------------------------------------------------------------------------
# Stage 3.5: chunk aligned lines into screen-sized cues

# A word ending in clause/sentence punctuation always ends the cue.
PUNCT_BREAK = re.compile(r"[,.;:!?…]['\"\)\]]*$")


def _split_run(run: list, max_chars: int) -> list[list]:
    """Split a punctuation-free word run into balanced pieces of at most max_chars."""
    text = " ".join(w.word.strip() for w in run)
    if len(text) <= max_chars:
        return [run]
    import math

    target = len(text) / math.ceil(len(text) / max_chars)
    pieces, cur, cur_len = [], [], 0
    for w in run:
        wlen = len(w.word.strip()) + (1 if cur else 0)
        if cur and (cur_len + wlen > max_chars or cur_len >= target):
            pieces.append(cur)
            cur, cur_len = [], 0
            wlen = len(w.word.strip())
        cur.append(w)
        cur_len += wlen
    if cur:
        pieces.append(cur)
    return pieces


def chunk_segments(segments, max_chars: int) -> list[dict]:
    """Turn aligned lyric lines into single-line cues.

    Rules (in priority order): never merge across the user's lyric lines; a comma or
    full stop always ends a cue; no cue exceeds max_chars (split at the most balanced
    word boundary); cue times come from word-level timestamps.
    """
    cues = []
    for seg in segments:
        words = [w for w in seg.words if w.word.strip()]
        if not words:
            continue
        runs, cur = [], []
        for w in words:
            cur.append(w)
            if PUNCT_BREAK.search(w.word.strip()):
                runs.append(cur)
                cur = []
        if cur:
            runs.append(cur)
        for run in runs:
            for piece in _split_run(run, max_chars):
                cues.append({
                    "start": float(piece[0].start),
                    "end": float(piece[-1].end),
                    "text": " ".join(w.word.strip() for w in piece),
                    "words": [
                        {"word": w.word.strip(), "start": float(w.start), "end": float(w.end)}
                        for w in piece
                    ],
                })
    if config.EARLY_APPEAR_SECONDS > 0:
        for cue in cues:
            cue["start"] = max(0.0, cue["start"] - config.EARLY_APPEAR_SECONDS)
    for i, cue in enumerate(cues, start=1):
        cue["index"] = i
    return cues


# ---------------------------------------------------------------------------
# Stage 4: outputs

def sanitize_cues(cues: list[dict]) -> list[dict]:
    """Clamp negatives, enforce monotonic order, fix overlaps, enforce minimum length."""
    for cue in cues:
        cue["start"] = max(0.0, cue["start"])
        cue["end"] = max(cue["start"], cue["end"])
    cues.sort(key=lambda c: c["start"])
    for i, cue in enumerate(cues):
        nxt = cues[i + 1] if i + 1 < len(cues) else None
        if nxt and cue["end"] > nxt["start"] - OVERLAP_GAP:
            cue["end"] = max(cue["start"], nxt["start"] - OVERLAP_GAP)
        if cue["end"] - cue["start"] < MIN_CUE_SECONDS:
            wanted = cue["start"] + MIN_CUE_SECONDS
            limit = nxt["start"] - OVERLAP_GAP if nxt else wanted
            cue["end"] = max(cue["end"], min(wanted, limit))
    for i, cue in enumerate(cues, start=1):
        cue["index"] = i
    return cues


def _fmt_timestamp(seconds: float) -> str:
    ms = round(seconds * 1000)
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(cues: list[dict], path: Path) -> None:
    blocks = [
        f"{c['index']}\n{_fmt_timestamp(c['start'])} --> {_fmt_timestamp(c['end'])}\n{c['text']}"
        for c in cues
    ]
    path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def export_stem(vocals_wav: Path, job_dir: Path) -> Path:
    """Convert or keep the vocal stem per config.STEM_FORMAT."""
    if config.STEM_FORMAT == "wav":
        return vocals_wav
    out = job_dir / "vocals.mp3"
    proc = subprocess.run(
        ["ffmpeg", "-y", "-i", str(vocals_wav), "-b:a", "320k", str(out)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0 or not out.exists():
        return vocals_wav  # WAV always exists; fall back rather than fail the job
    return out


# ---------------------------------------------------------------------------
# Orchestration

def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return slug[:40] or "song"


def _make_job_dir(audio_path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    job_dir = JOBS_DIR / f"{stamp}-{_slugify(audio_path.stem)}"
    job_dir.mkdir(parents=True, exist_ok=False)
    return job_dir


def _job_logger(job_dir: Path) -> logging.Logger:
    log = logging.getLogger(f"job.{job_dir.name}")
    log.setLevel(logging.INFO)
    log.handlers.clear()
    handler = logging.FileHandler(job_dir / "log.txt", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(handler)
    return log


def run_pipeline(audio_path, lyrics_text: str, strip_tags: bool = True,
                 video_format: str = None, progress_callback=None) -> dict:
    """Run the full pipeline. Returns a result dict with paths and metadata.

    video_format: "vertical" (9:16, short lines) or "horizontal" (16:9).
    progress_callback(step:int, total:int, message:str) drives UI status text.
    Raises PipelineError with a user-safe message on any failure.
    """
    def report(step, total, message):
        if progress_callback:
            progress_callback(step, total, message)

    video_format = video_format or config.FORMAT_DEFAULT
    max_chars = (config.MAX_CHARS_VERTICAL if video_format == "vertical"
                 else config.MAX_CHARS_HORIZONTAL)
    audio_path = Path(audio_path)
    duration, duration_warning = validate_audio(audio_path)
    lyric_lines, lyric_warning = preprocess_lyrics(lyrics_text, strip_tags=strip_tags)
    warnings = [w for w in (duration_warning, lyric_warning) if w]

    job_dir = _make_job_dir(audio_path)
    log = _job_logger(job_dir)
    log.info("Input: %s (%.1fs), %d lyric lines, strip_tags=%s, format=%s (max %d chars/line)",
             audio_path.name, duration, len(lyric_lines), strip_tags, video_format, max_chars)
    for w in warnings:
        log.warning(w)

    input_copy = job_dir / f"input{audio_path.suffix.lower()}"
    shutil.copy2(audio_path, input_copy)

    timings = {}
    try:
        report(1, 3, "Step 1 of 3 — isolating vocals (roughly 10–60 seconds)…")
        t0 = time.perf_counter()
        vocals_path = separate_vocals(input_copy, job_dir, log)
        timings["separate_seconds"] = round(time.perf_counter() - t0, 2)
        log.info("Vocals isolated in %.1fs -> %s", timings["separate_seconds"], vocals_path.name)

        report(2, 3, "Step 2 of 3 — aligning lyrics (first run loads the model, "
                     "roughly 30 seconds to 2 minutes)…")
        t0 = time.perf_counter()
        result = align_lyrics(vocals_path, lyric_lines, log)
        timings["align_seconds"] = round(time.perf_counter() - t0, 2)
        log.info("Aligned %d segments in %.1fs", len(result.segments), timings["align_seconds"])

        report(3, 3, "Step 3 of 3 — building SRT…")
        t0 = time.perf_counter()
        cues = chunk_segments(result.segments, max_chars)
        cues = sanitize_cues(cues)

        srt_path = job_dir / f"{audio_path.stem}.srt"
        write_srt(cues, srt_path)

        cues_json = {
            "source_file": audio_path.name,
            "video_format": video_format,
            "max_chars_per_line": max_chars,
            "early_appear_seconds": config.EARLY_APPEAR_SECONDS,
            "model_size": config.MODEL_SIZE,
            "language": config.LANGUAGE,
            "separator_engine": config.SEPARATOR_ENGINE,
            "separator_model": config.SEPARATOR_MODEL,
            "duration_seconds": round(duration, 2),
            "timings": timings,
            "cues": cues,
        }
        (job_dir / "cues.json").write_text(
            json.dumps(cues_json, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        stem_path = export_stem(vocals_path, job_dir)
        timings["outputs_seconds"] = round(time.perf_counter() - t0, 2)
        log.info("Outputs written in %.1fs. Timings: %s", timings["outputs_seconds"], timings)

        return {
            "srt_path": srt_path,
            "stem_path": stem_path,
            "cues_path": job_dir / "cues.json",
            "job_dir": job_dir,
            "cues": cues,
            "timings": timings,
            "warnings": warnings,
        }
    except PipelineError:
        raise
    except Exception:
        log.error("Unexpected failure:\n%s", traceback.format_exc())
        raise PipelineError(
            "Something went wrong while processing this song. "
            f"Check the log at {job_dir / 'log.txt'} for details."
        )


# ---------------------------------------------------------------------------
# CLI

def main(argv: list[str]) -> int:
    if len(argv) not in (2, 3) or (len(argv) == 3 and argv[2] not in ("vertical", "horizontal")):
        print("Usage: python pipeline.py <audio> <lyrics.txt> [vertical|horizontal]")
        return 2
    audio, lyrics_file = Path(argv[0]), Path(argv[1])
    video_format = argv[2] if len(argv) == 3 else None
    lyrics_text = lyrics_file.read_text(encoding="utf-8")

    def progress(step, total, message):
        print(f"[{step}/{total}] {message}")

    try:
        result = run_pipeline(audio, lyrics_text,
                              strip_tags=config.STRIP_TAGS_DEFAULT,
                              video_format=video_format,
                              progress_callback=progress)
    except PipelineError as e:
        print(f"FAILED: {e}")
        return 1
    for w in result["warnings"]:
        print(f"WARNING: {w}")
    print(f"Job folder: {result['job_dir']}")
    print(f"SRT:        {result['srt_path']}")
    print(f"Vocals:     {result['stem_path']}")
    print(f"Timings:    {result['timings']}")
    print("--- SRT ---")
    print(result["srt_path"].read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
