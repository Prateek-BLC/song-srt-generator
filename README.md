# Song SRT Generator

Upload an AI-generated song plus the lyrics it was written from — get back a perfectly timestamped SRT subtitle file. It never transcribes: your known lyrics are snapped to the isolated vocal track, so every subtitle matches a lyric line exactly as written. Everything runs on your machine; files never leave your computer.

## Install — Apple Silicon Macs (M1, M2, M3, M4)

Nothing needs to be pre-installed. Not even Python.

1. Download `Song-SRT-Generator-<version>-mac.zip` from the [latest release](https://github.com/brightlifecreations-projects/song-srt-generator/releases/latest) and double-click it to unzip.
2. Drag **Song SRT Generator** into your **Applications** folder.
3. Double-click it. macOS says *"Apple could not verify 'Song SRT Generator'…"* because the app isn't from the App Store. Click **Done** (not *Move to Bin*).
4. Open **System Settings → Privacy & Security**, scroll down to the message about Song SRT Generator, click **Open Anyway**, and confirm with your password or Touch ID. You do this once per downloaded version.
5. The first launch sets everything up in a progress window: a private Python, the app's packages and the AI models (about 2.5 GB, 5–20 minutes, internet needed once). It finishes with a test run that has to pass, then the app opens.

Everything the app installs lives in `~/Library/Application Support/Song SRT Generator/` (Python, packages, models and your `jobs/` folder); the app itself stays unchanged. To uninstall, delete the app and that folder.

**Updating:** when a newer version is out, the app shows an *Update available* banner linking to the release. Download the new zip, replace the app in Applications, and repeat steps 3–4. Your models are kept, so an update takes about a minute.

**Windows (x64, untested on real hardware):** download `Song-SRT-Generator-<version>-win-lite.zip`, unzip it somewhere short like Desktop, double-click `Install.bat` (if SmartScreen appears: *More info → Run anyway*), wait for PASS, then use `Start.bat`.

Building release zips from this repo: `./make_release.sh <version>` builds the Mac app zip (the version must match the `VERSION` file); add `--windows` for the Windows zip or `--full` to bake the models into the Mac app for offline installs. Developers can still run from a checkout with `bash install.command` and `start.command`.

## Using it

1. Open **Song SRT Generator** from Applications (or Launchpad). The app opens in its own window; closing the window quits it. Use the toggle in the top-right corner for dark mode. (On Windows or a source checkout, `Start.bat` / `start.command` opens it in your browser instead.)
2. Upload the song (MP3, WAV, M4A, or FLAC).
3. Paste the lyrics exactly as sung — one line becomes one subtitle. Write out every repeated chorus in full. You can also upload a `.txt` to fill the box.
4. Pick the **video format**: Vertical 9:16 for Reels/TikTok (short subtitle lines, max 25 characters) or Horizontal 16:9 for YouTube (up to 42 characters). Every subtitle is a single line; a comma or full stop in your lyrics always starts a new subtitle — punctuate the lyrics the way the song breathes and the captions will follow.
5. Pick the **lyrics language** from the dropdown under the format: English, Hindi, Hinglish, Spanish, Portuguese, French, German, Italian, Punjabi, or Urdu. The app remembers your last choice. Pick **Hinglish** for Hindi lyrics written in Roman script ("Kabhi kabhi Aditi zindagi mein…") — it aligns them as English, which works well for romanized lyrics; pick **Hindi** for lyrics in Devanagari. The Hindi/Urdu sentence marks (। ॥ ۔ ، ؟) end a subtitle just like a comma or full stop, and a Spanish `¿` or `¡` starts a new one.
6. Click **Generate SRT**, watch the three steps run, then download the SRT (and the isolated vocal stem as a bonus).

Every job is also saved in the `jobs/` folder (input copy, vocals, SRT, cue data, log). In the Mac app that's `~/Library/Application Support/Song SRT Generator/jobs/` (in Finder: Go → Go to Folder…). Delete old job folders whenever you like.

From the command line: `python pipeline.py <audio> <lyrics.txt> [vertical|horizontal] [en|hi|hinglish|es|pt|fr|de|it|pa|ur]` (format and language are optional, in either order).

## Settings

Open `config.py` in a text editor — each setting has a one-line comment. (In the Mac app, config.py sits inside the read-only app bundle; the defaults are what you get.) The useful ones: `LANGUAGE` (the language preselected in the dropdown), `MODEL_SIZE` (`"small"` = faster, `"medium"` = more accurate), `STEM_FORMAT` (`"wav"` or `"mp3"`), `PORT`, and `HOST` (set to `"0.0.0.0"` to let teammates on your network use it from their browser).

## If something goes wrong

| Problem | Fix |
|---|---|
| "ffmpeg isn't installed" | Re-run the installer; open a fresh terminal afterwards. |
| Ran out of memory | Set `MODEL_SIZE = "small"` in config.py and restart. |
| Port already in use | Change `PORT` in config.py. |
| First job is slow | The model loads into memory once per app start; later jobs are much faster. |
| "Couldn't align these lyrics" | The lyrics don't match what's sung, or repeated choruses aren't written out in full. Fix and retry. |
| Mac app setup window shows an error | Click **Try again**. If it keeps failing, click **Show the log** and send Aman `install.log`. |
| "Port 7860 is already in use" in the Mac app | The browser version (`start.command`) is still running. Close its Terminal window and click **Try again**. |

Setup needs internet once (model downloads). After that the app works fully offline; the only network request is the update check on launch, which is skipped silently when offline (turn it off with `CHECK_FOR_UPDATES = False` in config.py).
