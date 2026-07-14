"""Song SRT Generator — Gradio UI. All processing lives in pipeline.py."""

import os

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

import queue
import threading
from pathlib import Path

import gradio as gr

import config
from pipeline import PipelineError, run_pipeline

APP_TITLE = "Song SRT Generator"
PRIVACY_NOTE = "Everything runs on this machine. Files never leave your computer."

LYRICS_PLACEHOLDER = (
    "Paste lyrics exactly as they are sung. Write out every repeated chorus in full. "
    "One line here becomes one subtitle."
)


def load_lyrics_file(file_path):
    """Fill the lyrics textbox from an uploaded .txt. The textbox stays the source of truth."""
    if not file_path:
        return gr.update()
    try:
        return Path(file_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return gr.update()


def generate(audio_path, lyrics_text, strip_tags):
    """Generator handler: streams status updates while the pipeline runs in a thread."""
    busy = gr.update(interactive=False)
    idle = gr.update(interactive=True)

    def fail(message):
        return f"⚠️ {message}", None, None, idle

    if not audio_path:
        yield fail("Upload a song file first.")
        return
    if not (lyrics_text or "").strip():
        yield fail("Lyrics are empty. Paste the lyrics exactly as sung, one line per subtitle.")
        return

    yield "Starting…", None, None, busy

    events = queue.Queue()
    result_box = {}

    def progress_callback(step, total, message):
        events.put(("status", f"**{message}**"))

    def worker():
        try:
            result_box["result"] = run_pipeline(
                audio_path, lyrics_text, strip_tags=strip_tags,
                progress_callback=progress_callback,
            )
        except PipelineError as e:
            result_box["error"] = str(e)
        except Exception:
            result_box["error"] = (
                "Something went wrong while processing this song. "
                "Check the newest folder in jobs/ for the log."
            )
        finally:
            events.put(("done", None))

    threading.Thread(target=worker, daemon=True).start()

    while True:
        kind, payload = events.get()
        if kind == "done":
            break
        yield payload, None, None, busy

    if "error" in result_box:
        yield fail(result_box["error"])
        return

    result = result_box["result"]
    lines = ["✅ **Done.** Your SRT is ready below."]
    for warning in result["warnings"]:
        lines.append(f"⚠️ {warning}")
    lines.append(
        f"\nVocal isolation {result['timings']['separate_seconds']:.0f}s · "
        f"alignment {result['timings']['align_seconds']:.0f}s · "
        f"{len(result['cues'])} subtitles. "
        f"Also saved in `jobs/{result['job_dir'].name}/`."
    )
    yield "\n\n".join(lines), str(result["srt_path"]), str(result["stem_path"]), idle


with gr.Blocks(title=APP_TITLE, analytics_enabled=False) as demo:
    gr.Markdown(
        f"# {APP_TITLE}\n"
        "Upload an AI-generated song and paste its lyrics — get a perfectly timed SRT. "
        "No transcription, no guessing: your lyrics are snapped to the vocal track.\n\n"
        f"<small>{PRIVACY_NOTE}</small>"
    )
    with gr.Row():
        with gr.Column():
            audio_in = gr.Audio(label="Song file (MP3 or WAV)", type="filepath")
            lyrics_file = gr.File(label="Lyrics file (.txt, optional)", file_types=[".txt"])
            lyrics_box = gr.Textbox(
                label="Lyrics (exactly as sung)", lines=16,
                placeholder=LYRICS_PLACEHOLDER,
            )
            strip_tags_box = gr.Checkbox(
                label="Strip [section] tags like [Chorus]", value=config.STRIP_TAGS_DEFAULT,
            )
            generate_btn = gr.Button("Generate SRT", variant="primary")
        with gr.Column():
            status_md = gr.Markdown("Upload a song, paste the lyrics, then hit **Generate SRT**.")
            srt_out = gr.File(label="Subtitles (.srt)")
            vocals_out = gr.File(label="Isolated vocals")

    lyrics_file.upload(load_lyrics_file, inputs=lyrics_file, outputs=lyrics_box)
    generate_btn.click(
        generate,
        inputs=[audio_in, lyrics_box, strip_tags_box],
        outputs=[status_md, srt_out, vocals_out, generate_btn],
    )


if __name__ == "__main__":
    demo.queue(default_concurrency_limit=1)
    try:
        demo.launch(
            server_name=config.HOST,
            server_port=config.PORT,
            inbrowser=not os.environ.get("SRT_NO_BROWSER"),
            enable_monitoring=False,
        )
    except OSError as e:
        raise SystemExit(
            f"Couldn't start on port {config.PORT} ({e}). Something else is probably "
            "using it — change the PORT constant in config.py and run again."
        )
