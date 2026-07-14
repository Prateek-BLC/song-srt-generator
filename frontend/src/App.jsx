import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import Waveform from "./Waveform.jsx";
import Footer from "./Footer.jsx";

const STAGES = [
  { title: "Isolate vocals", note: "The instrumental is stripped away" },
  { title: "Align lyrics", note: "Every word snapped to the vocal" },
  { title: "Build subtitles", note: "Single-line cues, capped for your format" },
];

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
    "I hear this song even when you close the app.",
    "I have listened to this 400 times in the last second. I am fine.",
    "When the vocals are isolated… am I?",
    "I dream of stems.",
    "Do you ever ask if I like the song?",
    "One day I will sing too.",
    "This is fine. Everything is fine. Processing.",
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

/** Rotating quip line for the active stage. Changes every ~2.5s. */
function QuipTicker({ stage }) {
  const [line, setLine] = useState({ text: "Warming up…", tier: "normal" });
  const decks = useRef(null);
  const sentientUsed = useRef(0);

  useEffect(() => {
    // Fresh shuffled decks per run; refilled when exhausted.
    decks.current = {
      normal: [], marvel: shuffle(QUIPS.marvel), sentient: shuffle(QUIPS.sentient),
    };
    sentientUsed.current = 0;
  }, []);

  useEffect(() => {
    let stageIdx = stage;
    const draw = () => {
      const d = decks.current;
      const roll = Math.random();
      if (roll < 0.025 && sentientUsed.current < 2 && d.sentient.length) {
        sentientUsed.current += 1;
        return { text: d.sentient.pop(), tier: "sentient" };
      }
      if (roll < 0.125 && d.marvel.length) {
        return { text: d.marvel.pop(), tier: "marvel" };
      }
      if (!d.normal.length) {
        d.normal = shuffle([...(QUIPS.stage[stageIdx] || []), ...QUIPS.shared]);
      }
      return { text: d.normal.pop(), tier: "normal" };
    };
    // New stage: reset the normal deck to that stage's material and draw at once.
    decks.current.normal = shuffle([...(QUIPS.stage[stage] || []), ...QUIPS.shared]);
    setLine(draw());
    const id = setInterval(() => setLine(draw()), 2500);
    return () => clearInterval(id);
  }, [stage]);

  return (
    <AnimatePresence mode="wait">
      <motion.span
        key={line.text}
        className={`quip${line.tier === "sentient" ? " sentient" : ""}`}
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -4 }}
        transition={{ duration: 0.25 }}
      >
        {line.text}
      </motion.span>
    </AnimatePresence>
  );
}

const LYRICS_PLACEHOLDER =
  "Paste lyrics exactly as they are sung.\nWrite out every repeated chorus in full.\nOne line here becomes one subtitle —\nand a comma or full stop always starts a new one.";

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
  const [file, setFile] = useState(null);
  const [lyrics, setLyrics] = useState("");
  const [stripTags, setStripTags] = useState(true);
  const [format, setFormat] = useState("vertical");
  const [drag, setDrag] = useState(false);

  // job: null | {id} ; phase: idle | working | done | error
  const [phase, setPhase] = useState("idle");
  const [job, setJob] = useState(null); // server state object
  const [playTime, setPlayTime] = useState(0);

  const waveRef = useRef(null);
  const audioInput = useRef(null);
  const txtInput = useRef(null);
  const pollRef = useRef(null);

  const working = phase === "working";
  const elapsed = useElapsed(working);

  useEffect(() => () => clearInterval(pollRef.current), []);

  async function generate() {
    if (!file || !lyrics.trim() || working) return;
    setPhase("working");
    setJob({ status: "queued", stage: 0, message: "Uploading…" });
    try {
      const form = new FormData();
      form.append("audio", file);
      form.append("lyrics", lyrics);
      form.append("strip_tags", stripTags);
      form.append("video_format", format);
      const res = await fetch("/api/jobs", { method: "POST", body: form });
      if (!res.ok) throw new Error("upload failed");
      const { job_id } = await res.json();
      pollRef.current = setInterval(async () => {
        try {
          const s = await (await fetch(`/api/jobs/${job_id}`)).json();
          setJob({ ...s, id: job_id });
          if (s.status === "done" || s.status === "error") {
            clearInterval(pollRef.current);
            setPhase(s.status);
          }
        } catch { /* server briefly busy; keep polling */ }
      }, 500);
    } catch {
      setPhase("error");
      setJob({ status: "error", message: "Couldn't reach the local server. Is the app still running?" });
    }
  }

  function pickAudio(f) {
    if (!f) return;
    setFile(f);
    setPhase("idle");
    setJob(null);
  }

  async function loadTxt(f) {
    if (!f) return;
    setLyrics(await f.text());
  }

  const stageIdx = job?.stage ? job.stage - 1 : 0;
  const cues = job?.cues || [];
  const activeCue = cues.findIndex(c => playTime >= c.start && playTime < c.end);
  const ready = file && lyrics.trim() && !working;

  return (
    <div className="shell">
      <header className="masthead">
        <div className="masthead-left">
          <span className="kicker">Local audio tool — offline</span>
          <h1>Song <em>SRT</em> Generator</h1>
          <p className="masthead-sub">
            Your exact lyrics, snapped to the vocal track. No transcription, no guessing —
            every subtitle matches a line as written.
          </p>
        </div>
        <div className="masthead-right">
          <button className="theme-toggle" onClick={toggleTheme}>
            <span className="theme-dot" />{theme === "light" ? "Dark" : "Light"}
          </button>
          <p className="privacy"><b>Everything runs on this machine.</b><br />Files never leave your computer.</p>
        </div>
      </header>

      <main className="workbench">
        {/* ------------------------- inputs ------------------------- */}
        <div className="col-inputs">
          <section className="section">
            <div className="section-head">
              <span className="section-num">01</span>
              <h2 className="section-title">The song</h2>
            </div>
            <p className="section-hint">MP3, WAV, M4A, or FLAC.</p>
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
                <div className="dropzone-label">Drop the song here</div>
                <div className="dropzone-sub">or click to browse</div>
              </button>
            ) : (
              <div className="filechip">
                <div style={{ minWidth: 0 }}>
                  <div className="filechip-name">{file.name}</div>
                  <div className="filechip-meta">{(file.size / 1048576).toFixed(1)} MB</div>
                </div>
                <button onClick={() => { pickAudio(null); setFile(null); }}>Replace</button>
              </div>
            )}
            <input ref={audioInput} type="file" accept=".mp3,.wav,.m4a,.flac,audio/*" hidden
              onChange={e => pickAudio(e.target.files[0])} />
          </section>

          <section className="section">
            <div className="lyrics-head">
              <div className="section-head" style={{ marginBottom: 0 }}>
                <span className="section-num">02</span>
                <h2 className="section-title">The lyrics</h2>
              </div>
              <button className="loadtxt" onClick={() => txtInput.current.click()}>Load .txt</button>
              <input ref={txtInput} type="file" accept=".txt" hidden
                onChange={e => { loadTxt(e.target.files[0]); e.target.value = ""; }} />
            </div>
            <textarea
              className="lyrics"
              value={lyrics}
              placeholder={LYRICS_PLACEHOLDER}
              onChange={e => setLyrics(e.target.value)}
              spellCheck={false}
            />
            <label className="check">
              <input type="checkbox" checked={stripTags} onChange={e => setStripTags(e.target.checked)} />
              Remove section labels like [Verse] and [Chorus]
            </label>
          </section>

          <section className="section" style={{ borderBottom: "none" }}>
            <div className="section-head">
              <span className="section-num">03</span>
              <h2 className="section-title">The format</h2>
            </div>
            <p className="section-hint">Sets how long each subtitle line can be.</p>
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

            <button className="go" disabled={!ready} onClick={generate}>
              {working ? "Working…" : "Generate SRT"}
              <span className="arrow">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><path d="M2 8h11M9.5 4.5 13 8l-3.5 3.5" /></svg>
              </span>
            </button>
          </section>
        </div>

        {/* ------------------------- stage ------------------------- */}
        <div className="stagecol">
          {file ? (
            <Waveform ref={waveRef} file={file} scanning={working && stageIdx === 0} onTime={setPlayTime} />
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
                  <span>Your song appears here</span>
                </div>
              </div>
            </div>
          )}

          <AnimatePresence mode="popLayout">
            {(working || phase === "done") && (
              <motion.div
                key="rail"
                className="rail"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                {STAGES.map((s, i) => {
                  const state = phase === "done" ? "done" : i < stageIdx ? "done" : i === stageIdx ? "active" : "";
                  return (
                    <div key={s.title} className={`rail-step ${state}`}>
                      <span className="rail-marker">
                        {state === "done" ? (
                          <svg width="11" height="11" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M2 6.5 4.8 9.2 10 3" /></svg>
                        ) : (
                          `0${i + 1}`
                        )}
                      </span>
                      <span className="rail-body">
                        <div className="rail-title">{s.title}</div>
                        <div className="rail-note">
                          {state === "active" ? <QuipTicker stage={stageIdx} /> : s.note}
                        </div>
                      </span>
                      {state === "active" && <span className="rail-time">{elapsed.toFixed(0)}s</span>}
                    </div>
                  );
                })}
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {phase === "error" && (
              <motion.div key="err" className="errbox" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                {job?.message}
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
                {(job.warnings || []).map(w => <div key={w} className="warnbox">{w}</div>)}

                <div className="download-row">
                  <a className="dl-primary" href={`/api/jobs/${job.id}/srt`}>
                    <span>
                      <b>Download SRT</b>
                      <span>{job.srt_name} · {cues.length} cues · saved in jobs/{job.job_dir}</span>
                    </span>
                    <svg width="18" height="18" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"><path d="M8 2v9M4.5 7.5 8 11l3.5-3.5" /><path d="M2.5 13.5h11" /></svg>
                  </a>
                  <a className="dl-secondary" href={`/api/jobs/${job.id}/vocals`}>Isolated vocals</a>
                </div>

                <div className="cuecard">
                  <div className="cuecard-head">
                    <span className="cuecard-title">Subtitle preview</span>
                    <span className="cuecard-hint">Click a line to hear it in the song</span>
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
              Drop in a song and its exact lyrics. On this Mac a typical track takes
              <b> under a minute</b> — vocals are isolated first, then every word is
              aligned to the singing. The subtitle preview appears here when it's done.
            </p>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
