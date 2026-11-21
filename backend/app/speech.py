"""Make agent replies safe to speak: symbols/units spelled out, no markdown, sentence-level chunks that never
split a number ("8.1" must never become "8." + "1")."""
from __future__ import annotations

import re

UNITS = [
    (r"mg\s*/\s*dl", " milligrams per decilitre"),
    (r"g\s*/\s*dl", " grams per decilitre"),
    (r"ng\s*/\s*ml", " nanograms per millilitre"),
    (r"miu\s*/\s*l", " milli units per litre"),
    (r"mmol\s*/\s*l", " millimoles per litre"),
]


def speakable(text: str) -> str:
    t = text
    t = re.sub(r"<\s*=?\s*(?=\d)", " less than ", t)
    t = re.sub(r">\s*=?\s*(?=\d)", " more than ", t)
    t = re.sub(r"[*_#`>|]+", " ", t)                         # markdown
    t = re.sub(r"^\s*[-•]\s+", "", t, flags=re.M)            # bullets
    t = re.sub(r"\bHbA1c\b", "H B A 1 C", t, flags=re.I)
    t = re.sub(r"\bLDL\b", "L D L", t)
    t = re.sub(r"\bHDL\b", "H D L", t)
    t = re.sub(r"\bFBS\b", "fasting blood sugar", t)
    t = re.sub(r"\bTSH\b", "T S H", t)
    for pat, rep in UNITS:
        t = re.sub(r"(?<=\d)\s*" + pat, rep, t, flags=re.I)
        t = re.sub(r"\b" + pat + r"\b", rep.strip(), t, flags=re.I)
    t = re.sub(r"(\d)\s*%", r"\1 percent", t)
    t = re.sub(r"₹\s*(\d[\d,]*)", r"\1 rupees", t)
    t = re.sub(r"(\d(?:\.\d+)?)\s*[-–]\s*(\d)", r"\1 to \2", t)  # ranges 4.0 - 5.6
    t = re.sub(r"(?<=\d),(?=\d{3}\b)", "", t)                   # 1,200 -> 1200
    t = re.sub(r"\s*\n+\s*", " ", t)
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip()


ABBREV = ("dr.", "mr.", "mrs.", "ms.", "st.", "vs.", "e.g.", "i.e.", "no.", "approx.", "ref.")


def sentences(text: str) -> list[str]:
    """Split only at sentence ends followed by whitespace (decimals/times stay intact; 'Dr.' never splits)."""
    parts = [p.strip() for p in re.split(r"(?<=[.!?।])\s+", text) if p.strip()]
    out: list[str] = []
    for p in parts:
        if out and out[-1].lower().endswith(ABBREV):
            out[-1] = out[-1] + " " + p
        else:
            out.append(p)
    return out
