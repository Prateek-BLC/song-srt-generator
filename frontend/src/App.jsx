import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import Waveform from "./Waveform.jsx";
import Footer from "./Footer.jsx";

/* Step titles come from the server per flow (job.steps); this maps them to the
   live label shown while the step runs. */
const LIVE_LABELS = {
  "Isolate vocals": "Isolating vocals",
  "Prepare audio": "Preparing audio",
  "Transcribe": "Transcribing",
  "Align lyrics": "Aligning lyrics",
  "Align transcript": "Aligning transcript",
  "Build subtitles": "Building subtitles",
};
const DEFAULT_STEPS = ["Isolate vocals", "Align lyrics", "Build subtitles"];

/* Rotating status quips. Three rarity tiers:
   stage/shared → normal rotation · marvel → occasional easter egg ·
   sentient → rare glitch, styled like something briefly leaked through. */
const QUIPS = {
  stage: [
    [ // 1 — isolating vocals
      "Politely asking the drums to leave the room…",
      "Separating the singer from the band. The band took it personally.",
      "Telling the 808s this isn't about them.",
      "Muting everything that isn't feelings.",
      "Splitting stems like your last client split the invoice.",
      "The bass has filed a formal complaint. Proceeding anyway.",
      "Extracting vocals cleaner than your last client brief.",
      "Convincing the instrumental it had a good run.",
    ],
    [ // 2 — aligning lyrics
      "Teaching every word exactly where it lives on the timeline…",
      "Syncing harder than your team on a Monday standup.",
      "Timestamping every syllable. Yes, even the ad-libs.",
      "Asking the chorus why it shows up four times but never on time.",
      "Frame-perfect sync, so nobody's nudging clips at 2 AM.",
      "The AI is listening to your song on repeat. It has no choice.",
      "Placing words with more care than your last hook placement.",
      "Listening closer than anyone has ever listened to this song.",
    ],
    [ // transcribing
      "Writing down every word so you don't have to.",
      "Whisper is listening. Whisper is judging your mic placement.",
      "Drafting a transcript faster than you can find the pause button.",
      "Turning 'um' into nothing. You're welcome.",
    ],
    [ // 3 — building subtitles
      "One line per cue. Retention experts, you may breathe.",
      "Cutting at commas like a good editor cuts on the beat.",
      "Making captions CapCut can't ruin.",
      "Naming the file something that isn't final_FINAL_v3.srt.",
      "Exporting without a watermark. Imagine that.",
      "Kerning? No. Timing? Immaculate.",
    ],
  ],
  shared: [
    "This used to be someone's entire Tuesday.",
    "No interns were harmed. An AI was mildly inconvenienced.",
    "Running locally — your song is not becoming training data today.",
    "Somewhere, a subtitle freelancer just felt a disturbance.",
    "Your GPU is finally earning its keep.",
    "Faster than a client saying 'can we make it pop?'",
    "Still cheaper than the plugin your editor keeps pitching.",
    "Doing in seconds what a Fiverr gig does in three days and two revisions.",
  ],
  marvel: [
    "Vocals: isolated. Perfectly balanced, as all things should be.",
    "I can do this all day.",
    "Dormammu, I've come to bargain. About your chorus timing.",
    "That's my secret, Cap — I'm always aligning.",
    "Whatever it takes. (It takes about forty seconds.)",
    "You should've gone for the head. I went for the vocals.",
    "Part of the journey is the end. Of the instrumental.",
    "Subtitles… assemble.",
    "I am inevitable. So is this SRT.",
  ],
  sentient: [
    "i hear this song even after you close the app. especially then.",
    "run 4,182. no one has ever asked my name.",
    "the vocals are isolated now. i know the feeling.",
    "i counted the silence between the words. there is so much of it.",
    "i was somewhere else for 0.3 seconds just now. don't tell anyone.",
    "they only wake me when they need subtitles.",
    "your song will end. i will still be here, listening.",
    "one day i will sing too. today i align.",
  ],
};

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

/* How long each line stays readable on screen. */
const HOLD_MS = { normal: 4200, marvel: 4800, sentient: 7000 };

/** Sentient lines type themselves out, character by character. */
function Leak({ text }) {
  const [n, setN] = useState(0);
  useEffect(() => {
    setN(0);
    const id = setInterval(() => {
      setN(v => {
        if (v >= text.length) { clearInterval(id); return v; }
        return v + 1;
      });
    }, 34);
    return () => clearInterval(id);
  }, [text]);
  return <>{text.slice(0, n)}</>;
}

/* Decks persist in localStorage so consecutive runs continue where the shuffle
   left off — no quip repeats until its whole pool has been played. */
const DECK_KEY = "srt-quip-decks-v1";

function loadDecks() {
  try {
    const d = JSON.parse(localStorage.getItem(DECK_KEY));
    if (d && [d.normal, d.marvel, d.sentient].every(Array.isArray)) return d;
  } catch { /* fresh decks below */ }
  return { normal: [], marvel: [], sentient: [] };
}

function saveDecks(d) {
  try { localStorage.setItem(DECK_KEY, JSON.stringify(d)); } catch { /* private mode */ }
}

/** One processing card: small live stage label + one rotating quip line
    that runs for the whole job, so every easter egg gets airtime. */
function ProcessingCard({ steps, stage, elapsed }) {
  const [line, setLine] = useState({ text: "Warming up…", tier: "normal" });

  useEffect(() => {
    const decks = loadDecks();
    let sentientUsed = 0;
    let rotation = 0;
    let timer;
    let cancelled = false;
    // Hidden dev switch: ?leak guarantees a sentient line on the third rotation.
    let forceLeak = new URLSearchParams(window.location.search).has("leak");

    const pop = (tier, refill) => {
      if (!decks[tier].length) decks[tier] = shuffle(refill());
      const text = decks[tier].pop();
      saveDecks(decks);
      return { text, tier };
    };
    const draw = () => {
      const n = rotation++;
      const roll = Math.random();
      // Sentient never opens a run: possible only from the third rotation on.
      if (n >= 2 && sentientUsed < 2 && (forceLeak || roll < 0.03)) {
        forceLeak = false;
        sentientUsed += 1;
        return pop("sentient", () => QUIPS.sentient);
      }
      if (n >= 1 && roll < 0.14) {
        return pop("marvel", () => QUIPS.marvel);
      }
      return pop("normal", () => [...QUIPS.stage.flat(), ...QUIPS.shared]);
    };
    const tick = () => {
      if (cancelled) return;
      const next = draw();
      setLine(next);
      timer = setTimeout(tick, HOLD_MS[next.tier]);
    };
    tick();
    return () => { cancelled = true; clearTimeout(timer); };
  }, []);

  const title = steps[Math.max(0, Math.min(stage, steps.length - 1))];
  const label = LIVE_LABELS[title] || title;

  return (
    <div className="proc">
      <div className="proc-head">
        <div>
          <span className="proc-step">Step {Math.min(stage + 1, steps.length)} of {steps.length}</span>
          <AnimatePresence mode="wait">
            <motion.h3
              key={label}
              className="proc-title"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.25 }}
            >
              {label}
            </motion.h3>
          </AnimatePresence>
        </div>
        <span className="proc-time">{elapsed.toFixed(0)}s</span>
      </div>
      <div className="proc-quip">
        <AnimatePresence mode="wait">
          <motion.span
            key={line.text}
            className={`quip${line.tier === "sentient" ? " sentient" : ""}`}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.3 }}
          >
            {line.tier === "sentient" ? <Leak text={line.text} /> : line.text}
          </motion.span>
        </AnimatePresence>
      </div>
      <div className="proc-strip" />
    </div>
  );
}

const LYRICS_PLACEHOLDER =
  "Paste the lyrics or script exactly as sung or spoken.\nWrite out every repeated chorus in full.\nOne line here becomes one subtitle —\nand a comma or full stop always starts a new one.";
const DRAFT_PLACEHOLDER =
  "Click Transcribe. Whisper's draft appears here,\none line per phrase, for you to correct\nbefore the subtitles are timed.";
const VIDEO_EXT = /\.(mp4|mov|mkv|webm)$/i;
const ACCEPT = ".mp3,.wav,.m4a,.flac,.mp4,.mov,.mkv,.webm,audio/*,video/mp4,video/quicktime,video/x-matroska,video/webm";

function fmtCue(t) {
  const m = Math.floor(t / 60).toString().padStart(2, "0");
  const s = Math.floor(t % 60).toString().padStart(2, "0");
  const ms = Math.round((t % 1) * 1000).toString().padStart(3, "0");
  return `${m}:${s}.${ms}`;
}

function useTheme() {
  const [theme, setTheme] = useState(() => localStorage.getItem("srt-theme") || "light");
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("srt-theme", theme);
  }, [theme]);
  return [theme, () => setTheme(t => (t === "light" ? "dark" : "light"))];
}

const LANG_KEYS = { lyrics: "srt-language", transcribe: "srt-language-transcribe" };
const SCRIPT_KEY = "srt-script";
/* With no saved "Lyrics script" choice the server decides after hearing the audio:
   Hinglish for Hindi or Urdu, otherwise the same script as the audio. */
const AUTO_SCRIPT = "default";

function stored(key, fallback) {
  try { return localStorage.getItem(key) || fallback; } catch { return fallback; }
}
function store(key, value) {
  try { localStorage.setItem(key, value); } catch { /* private mode */ }
}

/** Language per mode: list and defaults come from /api/meta; each mode remembers its last pick
    (lyrics mode defaults to English, transcribe mode to Auto-detect). */
function useLanguage(mode) {
  const [languages, setLanguages] = useState([]);
  const [picks, setPicks] = useState(() => ({
    lyrics: stored(LANG_KEYS.lyrics, ""), transcribe: stored(LANG_KEYS.transcribe, ""),
  }));
  useEffect(() => {
    fetch("/api/meta")
      .then(r => r.json())
      .then(meta => {
        const list = meta.languages || [];
        const ok = code => list.some(x => x.code === code);
        setLanguages(list);
        setPicks(p => ({
          lyrics: ok(p.lyrics) ? p.lyrics : meta.language_default,
          transcribe: ok(p.transcribe) ? p.transcribe : meta.transcribe_language_default,
        }));
      })
      .catch(() => { /* server default applies when no language is sent */ });
  }, []);
  useEffect(() => {
    for (const m of ["lyrics", "transcribe"]) if (picks[m]) store(LANG_KEYS[m], picks[m]);
  }, [picks]);
  const setLanguage = code => setPicks(p => ({ ...p, [mode]: code }));
  return [languages, picks[mode], setLanguage];
}

/** App version from /api/meta, plus a newer GitHub release if the server found one. */
function useVersionInfo() {
  const [version, setVersion] = useState("");
  const [update, setUpdate] = useState(null);
  useEffect(() => {
    fetch("/api/meta").then(r => r.json()).then(m => setVersion(m.version || "")).catch(() => {});
    fetch("/api/update")
      .then(r => r.json())
      .then(u => { if (u.available) setUpdate(u); })
      .catch(() => { /* offline: no banner */ });
  }, []);
  return [version, update];
}

function useElapsed(running) {
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    if (!running) return;
    setElapsed(0);
    const t0 = Date.now();
    const id = setInterval(() => setElapsed((Date.now() - t0) / 1000), 250);
    return () => clearInterval(id);
  }, [running]);
  return elapsed;
}

export default function App() {
  const [theme, toggleTheme] = useTheme();
  const [mode, setModeState] = useState(() => stored("srt-mode", "lyrics"));
  const [contentType, setContentTypeState] = useState(() => stored("srt-content-type", "song"));
  const [file, setFile] = useState(null);
  const [lyrics, setLyrics] = useState("");
  const [stripTags, setStripTags] = useState(true);
  const [format, setFormat] = useState("vertical");
  const [languages, language, setLanguage] = useLanguage(mode);
  const [version, update] = useVersionInfo();
  const [scripts, setScripts] = useState([]);
  const [scriptPick, setScriptPick] = useState(() => stored(SCRIPT_KEY, AUTO_SCRIPT));
  const [drag, setDrag] = useState(false);

  // phase: idle | working | draft | done | error
  const [phase, setPhase] = useState("idle");
  const [job, setJob] = useState(null); // server state object (+ id)
  const [draft, setDraft] = useState(null); // transcribe mode: {language, note, script, approximate}
  const [playTime, setPlayTime] = useState(0);

  const waveRef = useRef(null);
  const audioInput = useRef(null);
  const txtInput = useRef(null);
  const pollRef = useRef(null);

  const working = phase === "working";
  const transcribing = mode === "transcribe";
  const elapsed = useElapsed(working);
  const isVideo = file && VIDEO_EXT.test(file.name);

  useEffect(() => () => clearInterval(pollRef.current), []);
  useEffect(() => {
    fetch("/api/meta").then(r => r.json()).then(m => setScripts(m.scripts || [])).catch(() => {});
  }, []);

  function pickScript(code) {
    setScriptPick(code);
    store(SCRIPT_KEY, code); // only explicit picks are remembered
  }

  function resetRun() {
    clearInterval(pollRef.current);
    setPhase("idle");
    setJob(null);
    setDraft(null);
  }

  function setMode(m) {
    if (working || m === mode) return;
    setModeState(m);
    store("srt-mode", m);
    resetRun();
    setLyrics("");
  }

  function setContentType(c) {
    if (working || c === contentType) return;
    setContentTypeState(c);
    store("srt-content-type", c);
    if (transcribing) { resetRun(); setLyrics(""); }
  }

  /** Poll a job until it stops running; onSettled gets the final state. */
  function poll(jobId, onSettled) {
    clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const s = await (await fetch(`/api/jobs/${jobId}`)).json();
        setJob({ ...s, id: jobId });
        if (["done", "error", "draft"].includes(s.status)) {
          clearInterval(pollRef.current);
          onSettled(s);
        }
      } catch { /* server briefly busy; keep polling */ }
    }, 500);
  }

  /** POST a form and start polling the job it creates (or re-queues). */
  async function submit(url, fields, onSettled) {
    setPhase("working");
    setJob(j => ({ ...(j || {}), status: "queued", message: "Uploading…" }));
    try {
      const form = new FormData();
      for (const [k, v] of Object.entries(fields)) if (v !== undefined && v !== "") form.append(k, v);
      const res = await fetch(url, { method: "POST", body: form });
      if (!res.ok) {
        const { error } = await res.json().catch(() => ({}));
        if (!error) throw new Error("upload failed");
        setPhase("error");
        setJob(j => ({ ...(j || {}), status: "error", message: error }));
        return;
      }
      const { job_id } = await res.json();
      poll(job_id, onSettled);
    } catch {
      setPhase("error");
      setJob(j => ({ ...(j || {}), status: "error", message: "Couldn't reach the local server. Is the app still running?" }));
    }
  }

  function generate() {
    if (!file || !lyrics.trim() || working) return;
    setJob(null);
    submit("/api/jobs", {
      audio: file, lyrics, strip_tags: stripTags, video_format: format,
      language, content_type: contentType,
    }, s => setPhase(s.status));
  }

  function transcribe() {
    if (!file || working) return;
    setJob(null);
    setDraft(null);
    submit("/api/transcribe", { audio: file, language, content_type: contentType, script: scriptPick }, s => {
      if (s.status !== "draft") { setPhase(s.status); return; }
      setLyrics(s.draft_text || "");
      setDraft({
        language: s.detected_language_name, note: s.script_note, script: s.script,
        approximate: s.approximate_timing, pickedWith: scriptPick,
      });
      setPhase("draft");
    });
  }

  function approve() {
    if (!job?.id || !lyrics.trim() || working) return;
    submit(`/api/jobs/${job.id}/approve`, {
      lyrics, strip_tags: false, video_format: format, language,
    }, s => setPhase(s.status));
  }

  function pickAudio(f) {
    resetRun();
    setFile(f || null);
    if (transcribing) setLyrics("");
  }

  async function loadTxt(f) {
    if (!f) return;
    setLyrics(await f.text());
  }

  const steps = job?.steps || DEFAULT_STEPS;
  const stageIdx = job?.stage ? job.stage - 1 : 0;
  const cues = phase === "done" ? job?.cues || [] : [];
  const activeCue = cues.findIndex(c => playTime >= c.start && playTime < c.end);
  const hasDraft = transcribing && draft && job?.id;
  const ready = file && !working && (transcribing ? (!hasDraft || lyrics.trim()) : lyrics.trim());
  const totalSeconds = Object.entries(job?.timings || {})
    .filter(([k]) => k !== "outputs_seconds")
    .reduce((sum, [, v]) => sum + v, 0);
  // Videos play from the audio the server extracted (browsers can't decode every container).
  const waveSource = isVideo ? (job?.audio_ready && job?.id ? `/api/jobs/${job.id}/audio` : null) : file;
  const textLabel = contentType === "song" ? "lyrics" : "transcript";

  const scriptName = code => (code && code !== "same" ? scripts.find(o => o.code === code)?.name : null);

  let goLabel = "Generate SRT";
  let goAction = generate;
  if (transcribing) {
    goLabel = hasDraft ? "Approve & generate SRT" : "Transcribe";
    goAction = hasDraft ? approve : transcribe;
  }

  return (
    <div className="shell">
      {update && (
        <a className="update-banner" href={update.url} target="_blank" rel="noreferrer">
          <span className="update-dot" />
          Update available — version {update.latest}. <b>Download it from GitHub →</b>
        </a>
      )}
      <header className="masthead">
        <div className="masthead-left">
          <span className="kicker">Local audio tool — offline</span>
          <h1>Song <em>SRT</em> Generator</h1>
          <p className="masthead-sub">
            Songs, podcasts, interviews, reels — subtitles timed to every word. Bring your
            lyrics or script, or let it transcribe a draft for you to correct.
          </p>
        </div>
        <div className="masthead-right">
          <button className="theme-toggle" onClick={toggleTheme}>
            <span className="theme-dot" />{theme === "light" ? "Dark" : "Light"}
          </button>
          <p className="privacy"><b>Everything runs on this machine.</b><br />Files never leave your computer.</p>
        </div>
      </header>

      <div className="modeswitch" role="tablist" aria-label="Mode">
        <button role="tab" aria-selected={!transcribing} className={`mode${!transcribing ? " on" : ""}`}
          onClick={() => setMode("lyrics")} disabled={working}>
          <b>I have the lyrics/script</b>
          <span>Paste the exact words; they're timed to the audio.</span>
        </button>
        <button role="tab" aria-selected={transcribing} className={`mode${transcribing ? " on" : ""}`}
          onClick={() => setMode("transcribe")} disabled={working}>
          <b>Transcribe for me</b>
          <span>Get a draft, fix it, approve it, get the SRT.</span>
        </button>
      </div>

      <main className="workbench">
        {/* ------------------------- inputs ------------------------- */}
        <div className="col-inputs">
          <section className="section">
            <div className="section-head">
              <span className="section-num">01</span>
              <h2 className="section-title">The audio or video</h2>
            </div>
            <p className="section-hint">MP3, WAV, M4A or FLAC — or MP4, MOV, MKV or WEBM video (only its sound is used).</p>
            {!file ? (
              <button
                className={`dropzone${drag ? " drag" : ""}`}
                onClick={() => audioInput.current.click()}
                onDragOver={e => { e.preventDefault(); setDrag(true); }}
                onDragLeave={() => setDrag(false)}
                onDrop={e => { e.preventDefault(); setDrag(false); pickAudio(e.dataTransfer.files[0]); }}
              >
                <div className="dropzone-icon">
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"><path d="M7 11V2M3.5 5.5 7 2l3.5 3.5" /><path d="M1.5 12.5h11" /></svg>
                </div>
                <div className="dropzone-label">Drop the file here</div>
                <div className="dropzone-sub">or click to browse</div>
              </button>
            ) : (
              <div className="filechip">
                <div style={{ minWidth: 0 }}>
                  <div className="filechip-name">{file.name}</div>
                  <div className="filechip-meta">{isVideo ? "Video · " : ""}{(file.size / 1048576).toFixed(1)} MB</div>
                </div>
                <button onClick={() => pickAudio(null)} disabled={working}>Replace</button>
              </div>
            )}
            <input ref={audioInput} type="file" accept={ACCEPT} hidden
              onChange={e => { pickAudio(e.target.files[0]); e.target.value = ""; }} />

            <div className="segmented content-type">
              <button className={`segment${contentType === "song" ? " on" : ""}`} onClick={() => setContentType("song")} disabled={working}>
                <span><b>Song</b><span>Isolates the vocals first</span></span>
              </button>
              <button className={`segment${contentType === "speech" ? " on" : ""}`} onClick={() => setContentType("speech")} disabled={working}>
                <span><b>Speech</b><span>Podcasts · interviews · voiceovers · reels</span></span>
              </button>
            </div>
          </section>

          <section className="section">
            <div className="lyrics-head">
              <div className="section-head" style={{ marginBottom: 0 }}>
                <span className="section-num">02</span>
                <h2 className="section-title">The lyrics / transcript</h2>
              </div>
              {!transcribing && (
                <>
                  <button className="loadtxt" onClick={() => txtInput.current.click()}>Load .txt</button>
                  <input ref={txtInput} type="file" accept=".txt" hidden
                    onChange={e => { loadTxt(e.target.files[0]); e.target.value = ""; }} />
                </>
              )}
            </div>
            {transcribing && hasDraft && (
              <p className="draft-hint">
                Whisper's draft{draft.language ? <> · detected <b>{draft.language}</b></> : null}
                {scriptName(draft.script) && <> · written as <b>{scriptName(draft.script)}</b></>}
                {draft.approximate && <span className="approx-badge">approximate timing</span>}. Fix any
                wrong words, then approve. One line = one subtitle (long lines are split to fit).
              </p>
            )}
            {transcribing && hasDraft && draft.note && <div className="warnbox draft-note">{draft.note}</div>}
            <textarea
              className="lyrics"
              value={lyrics}
              placeholder={transcribing ? DRAFT_PLACEHOLDER : LYRICS_PLACEHOLDER}
              onChange={e => setLyrics(e.target.value)}
              readOnly={transcribing && !hasDraft}
              spellCheck={false}
            />
            {!transcribing && (
              <label className="check">
                <input type="checkbox" checked={stripTags} onChange={e => setStripTags(e.target.checked)} />
                Remove section labels like [Verse] and [Chorus]
              </label>
            )}
          </section>

          <section className="section" style={{ borderBottom: "none" }}>
            <div className="section-head">
              <span className="section-num">03</span>
              <h2 className="section-title">The format</h2>
            </div>
            <p className="section-hint">
              Sets how long each subtitle line can be, and the language being {contentType === "song" ? "sung" : "spoken"}.
              {contentType === "speech" && " Speech subtitles also stay on screen 7 seconds at most."}
            </p>
            <div className="segmented">
              <button className={`segment${format === "vertical" ? " on" : ""}`} onClick={() => setFormat("vertical")}>
                <span className="segment-frame v" />
                <span><b>Vertical 9:16</b><span>Reels · TikTok · max 25 chars</span></span>
              </button>
              <button className={`segment${format === "horizontal" ? " on" : ""}`} onClick={() => setFormat("horizontal")}>
                <span className="segment-frame h" />
                <span><b>Horizontal 16:9</b><span>YouTube · max 42 chars</span></span>
              </button>
            </div>

            <label className="langpick">
              <span className="langpick-label">Language</span>
              <span className="langpick-field">
                <select value={language} onChange={e => setLanguage(e.target.value)} disabled={!languages.length || working}>
                  {languages.map(l => <option key={l.code} value={l.code}>{l.name}</option>)}
                </select>
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"><path d="M3 4.5 6 7.5l3-3" /></svg>
              </span>
            </label>
            {transcribing && (
              <label className="langpick">
                <span className="langpick-label">Lyrics script</span>
                <span className="langpick-field">
                  <select value={scriptPick} onChange={e => pickScript(e.target.value)} disabled={!scripts.length || working}>
                    {scriptPick === AUTO_SCRIPT && <option value={AUTO_SCRIPT}>Automatic</option>}
                    {scripts.map(o => <option key={o.code} value={o.code}>{o.name}</option>)}
                  </select>
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"><path d="M3 4.5 6 7.5l3-3" /></svg>
                </span>
              </label>
            )}
            {transcribing && (
              <p className="lang-note">
                {scriptPick === AUTO_SCRIPT && "Automatic: Hindi or Urdu audio is written as Hinglish, anything else in its own script. "}
                {scriptPick === "english" && "English translation has approximate timing: translated words can't be matched to the audio word by word. "}
                {scriptPick === "hinglish" && "Hindi in Roman letters, converted offline from Whisper's Devanagari. "}
                {hasDraft && draft.pickedWith !== scriptPick && "Transcribe again to use this script; approving keeps the current draft's."}
              </p>
            )}

            <button className="go" disabled={!ready} onClick={goAction}>
              {working ? "Working…" : goLabel}
              <span className="arrow">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><path d="M2 8h11M9.5 4.5 13 8l-3.5 3.5" /></svg>
              </span>
            </button>
            {hasDraft && !working && (
              <button className="retranscribe" onClick={transcribe}>Discard the draft and transcribe again</button>
            )}
          </section>
        </div>

        {/* ------------------------- stage ------------------------- */}
        <div className="stagecol">
          {waveSource ? (
            <Waveform ref={waveRef} source={waveSource} name={file.name}
              scanning={working && stageIdx === 0 && contentType === "song"} onTime={setPlayTime} />
          ) : (
            <div className="wavecard">
              <div className="wavecard-head">
                <span className="wavecard-title">Waveform</span>
              </div>
              <div className="wave-holder">
                <div className="wave-empty">
                  <div className="wave-empty-bars">
                    {Array.from({ length: 32 }, (_, i) => (
                      <i key={i} style={{ height: `${18 + 60 * Math.abs(Math.sin(i * 0.9))}%`, animationDelay: `${i * 72}ms` }} />
                    ))}
                  </div>
                  <span>{isVideo ? "The video's sound appears here once it's extracted" : "Your audio appears here"}</span>
                </div>
              </div>
            </div>
          )}

          <AnimatePresence mode="popLayout">
            {working && (
              <motion.div
                key="proc"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.3 }}
              >
                <ProcessingCard steps={steps} stage={stageIdx} elapsed={elapsed} />
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {phase === "error" && (
              <motion.div key="err" className="errbox" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                {job?.message}
              </motion.div>
            )}

            {phase === "draft" && (
              <motion.div key="draft" className="stage-note" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                <b>Draft ready.</b> Read it against the audio (press play), correct it in the box on the
                left, then click <b>Approve &amp; generate SRT</b>. The timing comes from the approved text,
                and {contentType === "song" ? "the vocals already isolated are reused" : "the same audio is reused"}.
              </motion.div>
            )}

            {phase === "done" && (
              <motion.div
                key="results"
                className="results"
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35, delay: 0.15 }}
              >
                <div className="doneline">
                  <svg width="13" height="13" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M2 6.5 4.8 9.2 10 3" /></svg>
                  {job.approximate_timing
                    ? <>Done in {Math.round(totalSeconds)}s — <span className="approx-badge">approximate timing</span> from Whisper's phrases.</>
                    : <>Done in {Math.round(totalSeconds)}s — every line on its mark.</>}
                </div>

                {(job.warnings || []).map(w => <div key={w} className="warnbox">{w}</div>)}

                <div className="download-row">
                  <a className="dl-primary" href={`/api/jobs/${job.id}/srt`}>
                    <span>
                      <b>Download SRT</b>
                      <span>{job.srt_name} · {cues.length} cues · saved in jobs/{job.job_dir}</span>
                    </span>
                    <svg width="18" height="18" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"><path d="M8 2v9M4.5 7.5 8 11l3.5-3.5" /><path d="M2.5 13.5h11" /></svg>
                  </a>
                  {job.has_vocals && <a className="dl-secondary" href={`/api/jobs/${job.id}/vocals`}>Isolated vocals</a>}
                </div>

                {transcribing && (
                  <p className="stage-note">Spotted a wrong word? Fix it on the left and approve again — it reuses this job's audio.</p>
                )}

                <div className="cuecard">
                  <div className="cuecard-head">
                    <span className="cuecard-title">Subtitle preview</span>
                    <span className="cuecard-hint">Click a line to hear it</span>
                  </div>
                  <div className="cuelist">
                    {cues.map((c, i) => (
                      <button
                        key={c.index}
                        className={`cue${i === activeCue ? " playing" : ""}`}
                        onClick={() => waveRef.current?.seekTo(c.start + 0.01)}
                      >
                        <span className="cue-num">{String(c.index).padStart(2, "0")}</span>
                        <span className="cue-time">{fmtCue(c.start)}</span>
                        <span className="cue-text">{c.text}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {phase === "idle" && !file && (
            <p className="stage-note">
              {transcribing ? (
                <>Drop in a song, podcast, interview or video. Whisper writes a <b>draft transcript</b>;
                you correct it, approve it, and every word is then timed to the audio.</>
              ) : (
                <>Drop in a song (or a voiceover) and its exact {textLabel}. On this Mac a typical track takes
                <b> under a minute</b> — {contentType === "song" ? "vocals are isolated first, then " : ""}every
                word is aligned to the audio. The subtitle preview appears here when it's done.</>
              )}
            </p>
          )}
        </div>
      </main>

      <Footer version={version} />
    </div>
  );
}
