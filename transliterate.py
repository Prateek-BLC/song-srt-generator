"""Offline script conversion for transcribe mode's "Lyrics script" option (DECISIONS.md V3.8).

- to_hinglish(): Devanagari (or stray Urdu script) → casual Roman Hindi the way people
  type it: "kabhi kabhi zindagi mein", not IAST "kabhī kabhī". aksharamukha's
  RomanColloquial does the letters; this module adds what it lacks for Hindi:
  schwa deletion ("apna", not "apana"), nasals as n ("hain", not "haim"), ड़/ढ़ as
  d/dh, and a short list of common Hinglish spellings. Words already in Latin
  letters (English in the lyrics) are left exactly as they are.
- to_devanagari(): converts any Urdu-script words to Devanagari. Urdu omits short
  vowels, so this is rough; callers warn the user when it happens.
"""

import re
import unicodedata
import warnings

with warnings.catch_warnings():  # aksharamukha 2.3 has `is` literal comparisons
    warnings.simplefilter("ignore", SyntaxWarning)
    from aksharamukha import transliterate as _ak

DEVANAGARI = re.compile(r"[ऀ-ॿ]")
URDU = re.compile(r"[؀-ۿݐ-ݿ]")

VIRAMA, NUKTA = "्", "़"
ANUSVARA, CHANDRABINDU = "ं", "ँ"
CONSONANTS = {chr(c) for c in range(0x915, 0x93A)} | {chr(c) for c in range(0x958, 0x960)}
MATRAS = {chr(c) for c in range(0x93E, 0x94D)} | {"ॢ", "ॣ"}
INDEPENDENT_VOWELS = {chr(c) for c in range(0x904, 0x915)} | {"ॠ", "ॡ"}
LABIALS = {"प", "फ", "ब", "भ", "म"}
# Hinglish writes these flaps as plain d / dh ("bada", "padhna").
NUKTA_FOLD = {"ड़": "ड", "ढ़": "ढ", "ड़": "ड", "ढ़": "ढ"}

# Common words whose everyday Roman spelling differs from the rule-based output.
HINGLISH_SPELLINGS = {
    "men": "mein", "mem": "mein", "maim": "main", "haim": "hain", "hun": "hoon",
    "ham": "hum", "kyon": "kyun", "kyom": "kyun", "nahim": "nahin", "vo": "wo",
    "vah": "woh", "yah": "yeh", "jindagi": "zindagi", "jindgi": "zindagi",
    "tumhen": "tumhe", "mujhen": "mujhe", "unhen": "unhe", "hamen": "humein",
    "vahan": "wahan", "vaha": "waha", "vale": "wale", "vala": "wala", "vali": "wali",
}
AA = "\u093e"  # ा


def _units(word: str) -> list[dict]:
    """Split a Devanagari word into aksharas: consonant + vowel sign ("a" = inherent,
    None = virama), independent vowels, and nasal marks attached to the unit before."""
    for k, v in NUKTA_FOLD.items():
        word = word.replace(k, v)
    units, i = [], 0
    while i < len(word):
        ch = word[i]
        if ch in CONSONANTS:
            cons, i = ch, i + 1
            if i < len(word) and word[i] == NUKTA:
                cons, i = cons + NUKTA, i + 1
            vowel = "a"
            if i < len(word) and word[i] == VIRAMA:
                vowel, i = None, i + 1
            elif i < len(word) and word[i] in MATRAS:
                vowel, i = word[i], i + 1
            units.append({"c": cons, "v": vowel, "nasal": False, "raw": None})
        elif ch in INDEPENDENT_VOWELS:
            units.append({"c": None, "v": ch, "nasal": False, "raw": None})
            i += 1
        elif ch in (ANUSVARA, CHANDRABINDU) and units:
            units[-1]["nasal"] = True
            i += 1
        else:
            units.append({"c": None, "v": None, "nasal": False, "raw": ch})
            i += 1
    return units


def _delete_schwas(units: list[dict]) -> None:
    """Hindi drops the inherent "a" word-finally and in V-C-a-C-V (kamala → kamla)."""
    cons = [u["c"] is not None for u in units]
    has_vowel = [u["v"] is not None or u["c"] is None and u["raw"] is None for u in units]
    last = len(units) - 1
    if (last > 0 and cons[last] and units[last]["v"] == "a" and not units[last]["nasal"]
            and units[last - 1]["v"] is not None):
        units[last]["v"] = None
        has_vowel[last] = False
    for i in range(last - 1, 0, -1):
        u = units[i]
        # Not after a nasal: that would stack three consonants (zin-da-gi, not zindgi).
        if (cons[i] and u["v"] == "a" and not u["nasal"] and has_vowel[i - 1]
                and not units[i - 1]["nasal"] and cons[i + 1] and has_vowel[i + 1]):
            u["v"] = None
            has_vowel[i] = False


def _rebuild(units: list[dict]) -> str:
    out = []
    for i, u in enumerate(units):
        if u["raw"] is not None:
            out.append(u["raw"])
            continue
        if u["c"] is not None:
            out.append(u["c"] + ("" if u["v"] == "a" else VIRAMA if u["v"] is None else u["v"]))
        else:
            out.append(u["v"])
        if u["nasal"]:
            nxt = units[i + 1]["c"] if i + 1 < len(units) else None
            out.append(("म" if nxt in LABIALS else "न") + VIRAMA)
    return "".join(out)


def _urdu_word_to_devanagari(word: str) -> str:
    text = _ak.process("Urdu", "Devanagari", word, pre_options=["UrduShortNotShown"])
    return re.sub(r"य(?=$|[^ऀ-ॿ])", "ी", text)  # word-final ی is usually ī


def _hinglish_word(word: str) -> str:
    units = _units(word)
    _delete_schwas(units)
    roman = _ak.process("Devanagari", "RomanColloquial", _rebuild(units))
    core = re.match(r"^(\W*)(.*?)(\W*)$", roman)
    pre, body, post = core.groups()
    if body.lower() in HINGLISH_SPELLINGS:
        return pre + HINGLISH_SPELLINGS[body.lower()] + post
    letters = [u for u in units if u["raw"] is None]
    vowels = [u["v"] for u in letters if u["v"] is not None]
    # Long aa is written double where it's the whole syllable's vowel: aaj, baat, aansu.
    if letters and letters[0]["c"] is None and letters[0]["v"] == "आ" and body[:1].lower() == "a":
        body = body[0] + "a" + body[1:]
    elif vowels == [AA] and letters[-1]["v"] is None and body.count("a") == 1:
        body = body.replace("a", "aa")
    return pre + body + post


def _convert_tokens(line: str, fn) -> str:
    return " ".join(fn(tok) for tok in line.split())


def to_devanagari(text: str) -> str:
    """Convert Urdu-script words to (rough) Devanagari; everything else is unchanged."""
    def fix(tok):
        return _urdu_word_to_devanagari(tok) if URDU.search(tok) else tok
    return "\n".join(_convert_tokens(line, fix) for line in text.split("\n"))


def _plain_roman(token: str) -> str:
    """Hinglish is typed in plain ASCII: drop accents (ể → e) and anything that isn't
    Latin, like the stray kana or CJK Whisper sometimes hallucinates on songs."""
    token = token.replace("’", "'").replace("‘", "'")
    token = "".join(ch for ch in unicodedata.normalize("NFKD", token)
                    if not unicodedata.combining(ch))
    return "".join(ch for ch in token if ch.isascii())


def to_hinglish(text: str) -> str:
    """Devanagari/Urdu → casual Roman Hindi, line by line. Latin-letter words pass through."""
    def fix(tok):
        if URDU.search(tok):
            tok = _urdu_word_to_devanagari(tok)
        return _plain_roman(_hinglish_word(tok) if DEVANAGARI.search(tok) else tok)
    lines = []
    for line in text.split("\n"):
        line = re.sub(r"\s+", " ", _convert_tokens(line, fix)).strip().replace(" .", ".")
        lines.append(line[:1].upper() + line[1:])
    return "\n".join(line for line in lines if line)


def has_urdu(text: str) -> bool:
    return bool(URDU.search(text))
