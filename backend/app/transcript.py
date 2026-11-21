"""Speech-transcript normalization for code-switched Hindi/English.
The hi-IN ASR writes English speech in Devanagari ("कैन यू स्पीक इंग्लिश"). We detect transliterated English and
rewrite the utterance into English (Latin) or Roman Hinglish before language detection and the agent."""
from __future__ import annotations

import re
import time

from .config import get_settings

S = get_settings()

# English function/common words as the hi-IN ASR transliterates them
DEV_EN = {
    "कैन", "यू", "आई", "आई'म", "आईएम", "माय", "मी", "द", "दी", "इज़", "इज", "आर", "एंड", "इन", "ऑफ", "टू", "विद", "फॉर",
    "इट", "इट्स", "डू", "डज़", "डज", "व्हाट", "वॉट", "व्हेन", "व्हाई", "हाउ", "व्हिच", "प्लीज़", "प्लीज", "एक्सप्लेन", "टेल",
    "शो", "स्पीक", "इंग्लिश", "नाउ", "बिकॉज़", "बिकॉज", "ऑलसो", "आल्सो", "लाइक", "ओनली", "दैट", "दिस", "यस", "ओके",
    "थैंक", "थैंक्स", "कंपेयर", "प्रीवियस", "वांट", "नीड", "अबाउट", "हैव", "हैज़", "विल", "कुड", "शुड", "गेट", "गिव",
    "नॉट", "योर", "यॉर", "वी", "इफ", "सो", "बट", "ऑर", "ऑन", "फ्रॉम", "एवरीथिंग", "व्हाटएवर", "हियर", "हेल्प", "लास्ट",
    "लेटेस्ट", "सेट", "बुक", "शेयर", "रिपीट", "हियरिंग", "सी", "द्याट", "एनी", "सम", "टॉक", "हाय", "हेलो", "हैलो",
}
DEV_HI = {
    "है", "हैं", "मैं", "मेरी", "मेरा", "मेरे", "मुझे", "क्या", "आप", "आपकी", "आपका", "का", "की", "के", "में", "को", "से",
    "और", "नहीं", "हूँ", "हूं", "हो", "कर", "करो", "दो", "बताओ", "समझाओ", "था", "थी", "भी", "तो", "यह", "वह", "ये", "वो",
    "कैसे", "कब", "कितना", "लिए", "साथ", "पर", "रहा", "रही", "सकती", "सकते", "सकता", "चाहिए", "वाला", "वाली", "हाँ",
    "जी", "अभी", "आज", "कल", "तुम", "मेरी", "दीजिए", "करना", "लगा", "दिखाओ", "पिछली",
}


def _tokens(text: str) -> list[str]:
    return [t for t in re.split(r"[\s,.!?;:।॥\"()\-–—]+", text) if t]


_LATIN_HI = {"haan", "han", "nahi", "nahin", "kar", "karo", "do", "hai", "hain", "mera", "meri", "mujhe", "kya", "wala",
             "wali", "ji", "aur", "ka", "ki", "ke", "ko", "se", "mein", "bhi", "batao", "dikhao", "samjhao", "chahiye"}


def english_signal(text: str) -> tuple[int, int]:
    """(english, hindi) word counts. English may arrive in Devanagari (transliterated) or Latin script."""
    toks = _tokens(text)
    latin = [t.lower() for t in toks if re.fullmatch(r"[A-Za-z']+", t)]
    en = sum(t in DEV_EN for t in toks) + sum(t not in _LATIN_HI for t in latin)
    hi = sum(t in DEV_HI for t in toks) + sum(t in _LATIN_HI for t in latin)
    return en, hi


def needs_normalization(text: str) -> bool:
    if not re.search(r"[ऀ-ॿ]", text):
        return False
    en, _ = english_signal(text)
    return en >= 1


PROMPT = """You fix speech-recognition transcripts. The recognizer wrote the speaker's words in Devanagari even when
the speaker spoke English. Rewrite the transcript:
- English words that were spoken in English -> write them in normal English spelling (Latin script).
- If the whole utterance is English -> output plain English.
- If the speaker mixed Hindi and English -> output Roman Hinglish (Hindi words in Latin script, English words in English).
- If it is pure Hindi -> output it unchanged in Devanagari.
Do not translate, answer or add anything. Output only the rewritten transcript.

Transcript: """


async def normalize(text: str) -> str:
    """Returns the normalized utterance (or the original on failure)."""
    if not needs_normalization(text):
        return text
    from google import genai
    from google.genai import types
    t0 = time.perf_counter()
    try:
        client = genai.Client(api_key=S.llm_api_key)
        for model in ("gemini-3.1-flash-lite", "gemini-flash-lite-latest", S.llm_model):
            try:
                r = await client.aio.models.generate_content(
                    model=model, contents=PROMPT + text,
                    config=types.GenerateContentConfig(temperature=0, max_output_tokens=200,
                                                       thinking_config=types.ThinkingConfig(thinking_level="minimal")))
                out = (r.text or "").strip().strip('"')
                if out:
                    print(f"NORMALIZE {time.perf_counter() - t0:.2f}s {model}: {out[:80]}", flush=True)
                    return out
            except Exception as e:
                print("normalize model failed", model, repr(e)[:120], flush=True)
    except Exception as e:
        print("normalize failed", repr(e)[:160], flush=True)
    return text
