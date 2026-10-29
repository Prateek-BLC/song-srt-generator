# Song SRT Generator

Upload an AI-generated song plus the lyrics it was written from — get back a perfectly timestamped SRT subtitle file. It never transcribes: your known lyrics are snapped to the isolated vocal track, so every subtitle matches a lyric line exactly as written. Everything runs on your machine; files never leave your computer.

## Setup (once) — Apple Silicon Macs

Nothing needs to be pre-installed. Not even Python.

1. Unzip the release zip.
2. Open Terminal, type `bash ` (with a space), drag `Install.command` into the window, press Enter. Wait for **PASS** (first time 5–20 min — it sets up a private Python, ffmpeg, and the AI models, all *inside this folder*; your Mac is otherwise untouched). Terminal is used because macOS Gatekeeper blocks double-clicked unsigned scripts ("Apple could not verify…"); the blocked-dialog escape hatch is System Settings → Privacy & Security → "Open Anyway".
3. Done. To uninstall, delete the folder. (`Start.command` double-clicks cleanly — the installer removes the quarantine flags.)

Building a release zip from this repo: `./make_release.sh <version>` (add `--full` to bake the models in for offline installs).

## Using it

1. Double-click `Start.command` (browser opens automatically). Use the toggle in the top-right corner for dark mode.
2. Upload the song (MP3, WAV, M4A, or FLAC).
3. Paste the lyrics exactly as sung — one line becomes one subtitle. Write out every repeated chorus in full. You can also upload a `.txt` to fill the box.
4. Pick the **video format**: Vertical 9:16 for Reels/TikTok (short subtitle lines, max 25 characters) or Horizontal 16:9 for YouTube (up to 42 characters). Every subtitle is a single line; a comma or full stop in your lyrics always starts a new subtitle — punctuate the lyrics the way the song breathes and the captions will follow.
5. Pick the **lyrics language** from the dropdown under the format: English, Hindi, Hinglish, Spanish, Portuguese, French, German, Italian, Punjabi, or Urdu. The app remembers your last choice. Pick **Hinglish** for Hindi lyrics written in Roman script ("Kabhi kabhi Aditi zindagi mein…") — it aligns them as English, which works well for romanized lyrics; pick **Hindi** for lyrics in Devanagari. The Hindi/Urdu sentence marks (। ॥ ۔ ، ؟) end a subtitle just like a comma or full stop, and a Spanish `¿` or `¡` starts a new one.
6. Click **Generate SRT**, watch the three steps run, then download the SRT (and the isolated vocal stem as a bonus).

Every job is also saved in the `jobs/` folder (input copy, vocals, SRT, cue data, log). Delete old job folders whenever you like.

From the command line: `python pipeline.py <audio> <lyrics.txt> [vertical|horizontal] [en|hi|hinglish|es|pt|fr|de|it|pa|ur]` (format and language are optional, in either order).

## Settings

Open `config.py` in a text editor — each setting has a one-line comment. The useful ones: `LANGUAGE` (the language preselected in the dropdown), `MODEL_SIZE` (`"small"` = faster, `"medium"` = more accurate), `STEM_FORMAT` (`"wav"` or `"mp3"`), `PORT`, and `HOST` (set to `"0.0.0.0"` to let teammates on your network use it from their browser).

## If something goes wrong

| Problem | Fix |
|---|---|
| "ffmpeg isn't installed" | Re-run the installer; open a fresh terminal afterwards. |
| Ran out of memory | Set `MODEL_SIZE = "small"` in config.py and restart. |
| Port already in use | Change `PORT` in config.py. |
| First job is slow | The model loads into memory once per app start; later jobs are much faster. |
| "Couldn't align these lyrics" | The lyrics don't match what's sung, or repeated choruses aren't written out in full. Fix and retry. |

Setup needs internet once (model downloads). After that the app works fully offline.
