# Song SRT Generator

Upload an AI-generated song plus the lyrics it was written from — get back a perfectly timestamped SRT subtitle file. It never transcribes: your known lyrics are snapped to the isolated vocal track, so every subtitle matches a lyric line exactly as written. Everything runs on your machine; files never leave your computer.

## Setup (once)

1. Install **Python 3.11** (or 3.10) from https://www.python.org/downloads/ if you don't have it. On Windows, tick "Add to PATH".
2. **Mac:** double-click `install.command` (or run `bash install.command` in Terminal).
   **Windows:** double-click `install.bat`.
3. The installer checks your system, installs ffmpeg if needed, sets up dependencies for your machine, downloads the models (~2 GB, needs internet this once), and verifies everything with a test run. Wait for **PASS**.

## Using it

1. **Mac:** run `start.sh` — **Windows:** run `start.bat` (or `python app.py`). Your browser opens automatically.
2. Upload the song (MP3, WAV, M4A, or FLAC).
3. Paste the lyrics exactly as sung — one line becomes one subtitle. Write out every repeated chorus in full. You can also upload a `.txt` to fill the box.
4. Pick the **video format**: Vertical 9:16 for Reels/TikTok (short subtitle lines, max 25 characters) or Horizontal 16:9 for YouTube (up to 42 characters). Every subtitle is a single line; a comma or full stop in your lyrics always starts a new subtitle — punctuate the lyrics the way the song breathes and the captions will follow.
5. Click **Generate SRT**, watch the three steps run, then download the SRT (and the isolated vocal stem as a bonus).

Every job is also saved in the `jobs/` folder (input copy, vocals, SRT, cue data, log). Delete old job folders whenever you like.

## Settings

Open `config.py` in a text editor — each setting has a one-line comment. The useful ones: `MODEL_SIZE` (`"small"` = faster, `"medium"` = more accurate), `STEM_FORMAT` (`"wav"` or `"mp3"`), `PORT`, and `HOST` (set to `"0.0.0.0"` to let teammates on your network use it from their browser).

## If something goes wrong

| Problem | Fix |
|---|---|
| "ffmpeg isn't installed" | Re-run the installer; open a fresh terminal afterwards. |
| Ran out of memory | Set `MODEL_SIZE = "small"` in config.py and restart. |
| Port already in use | Change `PORT` in config.py. |
| First job is slow | The model loads into memory once per app start; later jobs are much faster. |
| "Couldn't align these lyrics" | The lyrics don't match what's sung, or repeated choruses aren't written out in full. Fix and retry. |

Setup needs internet once (model downloads). After that the app works fully offline.
