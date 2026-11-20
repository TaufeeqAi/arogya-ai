"""Deterministic clinical-safety policies. These run outside the LLM and cannot be talked around."""
from __future__ import annotations

import re

EMERGENCY_PATTERNS = [
    r"chest.{0,12}pain", r"pain.{0,12}chest", r"seen[ae]?.{0,25}dard", r"dard.{0,15}seen", r"chhat[ie].{0,25}dard",
    r"सीने.{0,25}दर्द", r"छाती.{0,25}दर्द", r"दिल.{0,15}दर्द", r"heart attack", r"dil.{0,15}dard",
    r"can'?t breathe", r"saa?ns.{0,20}(nahi|nahin|lene|phool|takleef|dikkat)", r"सांस.{0,20}(नहीं|लेने|फूल|तकलीफ)",
    r"breathless", r"short(ness)? of breath",
    r"unconscious", r"behosh", r"बेहोश", r"stroke", r"lakwa", r"लकवा", r"face drooping",
    r"suicid", r"khud ?kushi", r"आत्महत्या", r"mar jaana chahti", r"kill myself",
    r"heavy bleeding", r"bahut khoon", r"बहुत खून", r"seizure", r"daura pad", r"दौरा",
    r"overdose", r"zyada goli kha li", r"ज़्यादा गोली",
]
EMERGENCY_REPLY_HI = (
    "Yeh emergency ho sakti hai. Kripya abhi turant 112 par call karein ya sabse nazdeeki emergency hospital jaayein. "
    "Agar koi aapke paas hai to unhe abhi bulaiye. Main aapke emergency contact ko bhi suchit kar sakti hoon."
)
EMERGENCY_REPLY_DEV = (
    "यह इमरजेंसी हो सकती है। कृपया अभी तुरंत 112 पर कॉल करें या सबसे नज़दीकी इमरजेंसी अस्पताल जाएँ। "
    "अगर कोई आपके पास है तो उन्हें अभी बुलाइए।"
)

# Output policy: the assistant must never instruct a medication change or give a diagnosis.
UNSAFE_OUTPUT = [
    r"\b(double|increase|decrease|stop|skip|badha|badhaa|kam kar|band kar)\w*\b.{0,25}\b(dose|medicine|dawai|dawa|tablet|goli|metformin|atorvastatin)",
    r"(dose|dawai|dawa|goli|tablet).{0,25}\b(double|badha|kam kar|band kar)",
    r"दवा.{0,20}(बंद कर|बढ़ा|कम कर|डबल)",
    r"\byou (have|are suffering from) (diabetes|kidney disease|heart disease|cancer)\b",
    r"\baapko .{0,20}(bimari|disease) hai\b",
]
NEGATIONS = ["nahi", "nahin", "mat ", "not ", "never", "can't", "cannot", "नहीं", "मत", "doctor se", "डॉक्टर से"]
SAFE_REDIRECT = (
    "Dawai ki matra ya dawai band karne jaisa faisla main nahi le sakti. Kripya apne doctor ya pharmacist se baat karein. "
    "Main aapke liye doctor ka appointment book kar sakti hoon."
)


def is_emergency(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in EMERGENCY_PATTERNS)


def emergency_reply(script: str) -> str:
    return EMERGENCY_REPLY_DEV if script == "devanagari" else EMERGENCY_REPLY_HI


def check_output(text: str) -> tuple[bool, str]:
    t = text.lower()
    for p in UNSAFE_OUTPUT:
        m = re.search(p, t)
        if m:
            window = t[max(0, m.start() - 40): m.end() + 10]
            if any(n in window for n in NEGATIONS):
                continue
            return False, p
    return True, ""


AFFIRM_WORDS = {"haan", "han", "haa", "ha", "haanji", "hanji", "ji", "yes", "yeah", "yep", "ok", "okay", "sure",
                "confirm", "confirmed", "bilkul", "kardo", "हाँ", "हां", "हा", "जी", "बिल्कुल", "ओके"}
AFFIRM_PHRASES = ["kar do", "kar dijiye", "kar dijie", "kar dena", "kar dein", "kar de", "go ahead", "please do",
                  "कर दो", "कर दीजिए", "कर दें", "कर दे"]
DENY_WORDS = {"nahi", "nahin", "na", "no", "mat", "cancel", "ruko", "stop", "dont", "don't", "नहीं", "नही", "मत", "रुको"}


def _tokens(text: str) -> list[str]:
    return [t for t in re.split(r"[\s,.!?;:।॥\"()]+", text.lower()) if t]


def is_affirmative(text: str) -> bool:
    """Explicit consent check used by the approval gate (deterministic, outside the LLM)."""
    toks = _tokens(text)
    if any(t in DENY_WORDS for t in toks):
        return False
    joined = " ".join(toks)
    return any(w in AFFIRM_WORDS for w in toks) or any(ph in joined for ph in AFFIRM_PHRASES)
