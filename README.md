# Song SRT Generator

Turn a song, podcast, interview, voiceover or reel (audio or video) into a timestamped SRT subtitle file. Two ways in:

- **I have the lyrics/script:** paste the exact words and they're snapped to the audio, so every subtitle matches a line exactly as written.
- **Transcribe for me:** Whisper writes a draft; you correct it and approve it, then it's timed the same way.

Everything runs on your machine; files never leave your computer.

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
2. Pick the mode at the top: **I have the lyrics/script** or **Transcribe for me**.
3. Upload the file: audio (MP3, WAV, M4A, FLAC, up to 500 MB) or video (MP4, MOV, MKV, WEBM, up to 4 GB; only its sound is used).
4. Pick the **content type**: **Song** isolates the vocals first so the music doesn't get in the way; **Speech** (podcasts, interviews, voiceovers, reels) skips that step and also keeps every subtitle on screen for 7 seconds at most.
5. Pick the **video format**: Vertical 9:16 for Reels/TikTok (short subtitle lines, max 25 characters) or Horizontal 16:9 for YouTube (up to 42 characters). Every subtitle is a single line; a comma or full stop in the text always starts a new subtitle — punctuate the way the audio breathes and the captions will follow.
6. Pick the **language**: Auto-detect, English, Hindi, Hinglish, Spanish, Portuguese, French, German, Italian, Punjabi or Urdu. Each mode remembers its last choice (lyrics mode starts on English, transcribe mode on Auto-detect). The Hindi/Urdu sentence marks (। ॥ ۔ ، ؟) end a subtitle just like a comma or full stop, and a Spanish `¿` or `¡` starts a new one.
7. Then:
   - **Lyrics/script mode:** paste the words exactly as sung or spoken (one line becomes one subtitle, write out every repeated chorus in full; **Load .txt** fills the box) and click **Generate SRT**.
   - **Transcribe mode:** click **Transcribe**. The draft appears in the box, one line per phrase, with the language Whisper detected. Play the audio, fix any wrong words, and click **Approve & generate SRT**. The approved text is timed against the same audio (a song's vocals are isolated only once). Spotted a mistake afterwards? Edit and approve again.
8. Download the SRT (and, for songs, the isolated vocal stem as a bonus).

**Transcription quality, honestly:** clear English speech comes out nearly perfect. Sung lyrics come out mostly right but with misheard words, so always read the draft against the audio. Transcribing takes roughly as long as the audio itself on Apple Silicon (the CPU does it), so a 4-minute song takes about 4 minutes; aligning the approved text then takes seconds.

**Hindi and Hinglish:** Whisper can't write Hindi in Roman letters. With **Hinglish** selected, the draft comes out in Devanagari (Hindi script); retype it in Roman letters before approving for Hinglish subtitles, or approve it as is for Hindi-script subtitles. **Auto-detect** often hears Hindi as Urdu and writes Urdu script, so pick Hindi or Hinglish for Hindi audio. In lyrics mode, Hinglish works as before: paste the Roman-script lyrics and they're aligned well.

Every job is also saved in the `jobs/` folder (the input audio, or just the sound of a video, plus vocals, the draft, the approved text, SRT, cue data and log). In the Mac app that's `~/Library/Application Support/Song SRT Generator/jobs/` (in Finder: Go → Go to Folder…). Delete old job folders whenever you like.

From the command line:

- `python pipeline.py <audio|video> <lyrics.txt> [vertical|horizontal] [auto|en|hi|hinglish|es|pt|fr|de|it|pa|ur] [song|speech]` (the options are optional, in any order)
- `python pipeline.py --transcribe <audio|video> [language] [song|speech]` prints a draft transcript

## Settings

Open `config.py` in a text editor — each setting has a one-line comment. (In the Mac app, config.py sits inside the read-only app bundle; the defaults are what you get.) The useful ones: `LANGUAGE` and `TRANSCRIBE_LANGUAGE` (the language preselected in each mode), `MAX_CUE_SECONDS_SPEECH` (longest a speech subtitle stays on screen), `MAX_UPLOAD_MB` / `MAX_VIDEO_UPLOAD_MB`, `MODEL_SIZE` (`"small"` = faster, `"medium"` = more accurate), `STEM_FORMAT` (`"wav"` or `"mp3"`), `PORT`, and `HOST` (set to `"0.0.0.0"` to let teammates on your network use it from their browser).

## If something goes wrong

| Problem | Fix |
|---|---|
| "ffmpeg isn't installed" | Re-run the installer; open a fresh terminal afterwards. |
| Ran out of memory | Set `MODEL_SIZE = "small"` in config.py and restart. |
| Port already in use | Change `PORT` in config.py. |
| First job is slow | The model loads into memory once per app start; later jobs are much faster. |
| "Couldn't align this text to the audio" | The words don't match what's sung or said, or repeated choruses aren't written out in full. Fix and retry. |
| Transcription draft is in the wrong script (Urdu, Devanagari) | See *Hindi and Hinglish* above: pick the language instead of Auto-detect, or retype the draft. |
| "This video has no sound track" / "This file is silent" | There's no audio to subtitle; check you exported the video with sound. |
| Mac app setup window shows an error | Click **Try again**. If it keeps failing, click **Show the log** and send Aman `install.log`. |
| "Port 7860 is already in use" in the Mac app | The browser version (`start.command`) is still running. Close its Terminal window and click **Try again**. |

Setup needs internet once (model downloads). After that the app works fully offline; the only network request is the update check on launch, which is skipped silently when offline (turn it off with `CHECK_FOR_UPDATES = False` in config.py).
