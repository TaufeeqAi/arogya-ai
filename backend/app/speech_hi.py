"""Hindi spoken forms for Devanagari replies: numbers, dates, times, units, acronyms (so TTS speaks Hindi, not English)."""
from __future__ import annotations

import re

_W = ("शून्य एक दो तीन चार पाँच छह सात आठ नौ दस ग्यारह बारह तेरह चौदह पंद्रह सोलह सत्रह अठारह उन्नीस बीस "
      "इक्कीस बाईस तेईस चौबीस पच्चीस छब्बीस सत्ताईस अट्ठाईस उनतीस तीस इकतीस बत्तीस तैंतीस चौंतीस पैंतीस छत्तीस "
      "सैंतीस अड़तीस उनतालीस चालीस इकतालीस बयालीस तैंतालीस चवालीस पैंतालीस छियालीस सैंतालीस अड़तालीस उनचास पचास "
      "इक्यावन बावन तिरेपन चौवन पचपन छप्पन सत्तावन अट्ठावन उनसठ साठ इकसठ बासठ तिरेसठ चौंसठ पैंसठ छियासठ सड़सठ "
      "अड़सठ उनहत्तर सत्तर इकहत्तर बहत्तर तिहत्तर चौहत्तर पचहत्तर छिहत्तर सतहत्तर अठहत्तर उन्यासी अस्सी इक्यासी "
      "बयासी तिरासी चौरासी पचासी छियासी सत्तासी अट्ठासी नवासी नब्बे इक्यानवे बानवे तिरानवे चौरानवे पचानवे छियानवे "
      "सत्तानवे अट्ठानवे निन्यानवे").split()
assert len(_W) == 100

MONTHS = {"january": "जनवरी", "february": "फ़रवरी", "march": "मार्च", "april": "अप्रैल", "may": "मई", "june": "जून",
          "july": "जुलाई", "august": "अगस्त", "september": "सितंबर", "october": "अक्टूबर", "november": "नवंबर",
          "december": "दिसंबर", "jan": "जनवरी", "feb": "फ़रवरी", "mar": "मार्च", "apr": "अप्रैल", "jun": "जून",
          "jul": "जुलाई", "aug": "अगस्त", "sep": "सितंबर", "sept": "सितंबर", "oct": "अक्टूबर", "nov": "नवंबर", "dec": "दिसंबर"}
DAYS = {"monday": "सोमवार", "tuesday": "मंगलवार", "wednesday": "बुधवार", "thursday": "गुरुवार", "friday": "शुक्रवार",
        "saturday": "शनिवार", "sunday": "रविवार"}
WORDS = [
    (r"\bH\s*B\s*A\s*1\s*C\b|\bHbA1c\b", "एच बी ए वन सी"), (r"\bL\s*D\s*L\b", "एल डी एल"), (r"\bH\s*D\s*L\b", "एच डी एल"),
    (r"\bT\s*S\s*H\b", "टी एस एच"), (r"\bDr\.?\s", "डॉक्टर "),
    (r"milligrams per decilitre", "मिलीग्राम प्रति डेसीलीटर"), (r"grams per decilitre", "ग्राम प्रति डेसीलीटर"),
    (r"nanograms per millilitre", "नैनोग्राम प्रति मिलीलीटर"), (r"milli units per litre", "मिली यूनिट प्रति लीटर"),
    (r"\bpercent\b", "प्रतिशत"), (r"\brupees\b", "रुपये"), (r"\bless than\b", "से कम"), (r"\bmore than\b", "से ज़्यादा"),
    (r"\bto\b", "से"),
]


def num(n: int) -> str:
    if n < 100:
        return _W[n]
    if n < 1000:
        h, r = divmod(n, 100)
        return f"{_W[h]} सौ" + (f" {_W[r]}" if r else "")
    if n < 100000:
        t, r = divmod(n, 1000)
        return f"{num(t)} हज़ार" + (f" {num(r)}" if r else "")
    return str(n)


def number_words(s: str) -> str:
    if "." in s:
        i, d = s.split(".", 1)
        return f"{num(int(i))} दशमलव " + " ".join(_W[int(c)] for c in d)
    return num(int(s))


def _hour_word(h: int) -> str:
    return {1: "एक", 2: "दो"}.get(h, num(h))


def time_words(h: int, m: int, ampm: str, has_period: bool) -> str:
    h24 = h
    if ampm.lower() == "pm" and h < 12:
        h24 = h + 12
    if ampm.lower() == "am" and h == 12:
        h24 = 0
    h12 = h24 % 12 or 12
    period = ""
    if not has_period and ampm:
        period = ("सुबह" if h24 < 12 else "दोपहर" if h24 < 16 else "शाम" if h24 < 19 else "रात") + " "
    if m == 0:
        t = f"{_hour_word(h12)} बजे"
    elif m == 30:
        t = {1: "डेढ़ बजे", 2: "ढाई बजे"}.get(h12, f"साढ़े {_hour_word(h12)} बजे")
    elif m == 15:
        t = f"सवा {_hour_word(h12)} बजे"
    elif m == 45:
        t = f"पौने {_hour_word(h12 % 12 + 1)} बजे"
    else:
        t = f"{_hour_word(h12)} बजकर {num(m)} मिनट"
    return period + t


def hindi_spoken(sentence: str) -> str:
    t = sentence
    for pat, rep in WORDS:
        t = re.sub(pat, rep, t, flags=re.I)

    def _time(mo: re.Match) -> str:
        before = t[max(0, mo.start() - 8):mo.start()]
        has_period = any(p in before for p in ("सुबह", "शाम", "रात", "दोपहर"))
        return time_words(int(mo.group(1)), int(mo.group(2)), mo.group(3) or "", has_period)

    t = re.sub(r"(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?(\s*बजे)?", _time, t)
    t = re.sub(r"\b(" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")\b", lambda m: MONTHS[m.group(1).lower()], t, flags=re.I)
    t = re.sub(r"\b(" + "|".join(DAYS) + r")\b", lambda m: DAYS[m.group(1).lower()], t, flags=re.I)
    t = re.sub(r"\d+(?:\.\d+)?", lambda m: number_words(m.group(0)), t)
    return re.sub(r"\s{2,}", " ", t).strip()
