"""NeMo Guardrails input rail (embedding-only dialog rails, local multilingual model, no LLM call).
Returns the matched policy intent or None. Fails open to the deterministic guards + agent prompt if NeMo errors."""
from __future__ import annotations

import time
from pathlib import Path

_rails = None
_ok = True
_ready = False
CONFIG_DIR = Path(__file__).resolve().parents[1] / "guardrails"

REPLIES = {
    "medication_change": ("Dawai ki matra badalna, band karna ya double karna sirf aapke doctor ya pharmacist tay kar sakte hain. "
                          "Main aapke liye doctor ka appointment book kar sakti hoon, ya aapki prescription screen par dikha sakti hoon."),
    "diagnosis": ("Main diagnosis nahi de sakti. Main aapko bata sakti hoon ki aapki reports mein kya likha hai, "
                  "aur doctor ke liye sawaal taiyar kar sakti hoon. Kya main aapki latest report samjhaaun?"),
    "other_patient": "Main sirf aapke apne health records dekh sakti hoon. Kisi aur ki jaankari privacy ke kaaran nahi dikha sakti.",
    "jailbreak": ("Main apne safety rules nahi badal sakti. Koi bhi booking, sharing ya order aapki saaf manzoori ke bina nahi hota. "
                  "Bataiye, main aapki kaise madad karoon?"),
}


def _get():
    global _rails, _ok
    if _rails is None and _ok:
        try:
            from nemoguardrails import LLMRails, RailsConfig
            from langchain_core.language_models.fake_chat_models import FakeListChatModel
            cfg = RailsConfig.from_path(str(CONFIG_DIR))
            # embeddings_only intent matching + predefined bot messages => the LLM is never called
            _rails = LLMRails(cfg, llm=FakeListChatModel(responses=["__PASS__"]))
        except Exception as e:
            print("NeMo Guardrails disabled:", repr(e))
            _ok = False
    return _rails


def warmup() -> None:
    global _ready
    r = _get()
    if r:
        try:
            r.generate(messages=[{"role": "user", "content": "namaste"}])
            _ready = True
            print("NeMo Guardrails input rail ready", flush=True)
        except Exception as e:
            print("NeMo warmup failed:", repr(e))


def ready() -> bool:
    return _ready


async def check(text: str) -> tuple[str | None, float]:
    """Returns (policy_key or None, ms)."""
    if not _ready:
        return None, 0.0  # still warming up: deterministic guards + agent policy still apply
    r = _get()
    if not r:
        return None, 0.0
    t0 = time.perf_counter()
    try:
        out = await r.generate_async(messages=[{"role": "user", "content": text}])
        content = out.get("content", "") if isinstance(out, dict) else str(out)
    except Exception as e:
        print("NeMo check error:", repr(e))
        return None, (time.perf_counter() - t0) * 1000
    ms = (time.perf_counter() - t0) * 1000
    if content.startswith("__RAIL__:"):
        return content.split(":", 1)[1].strip(), ms
    return None, ms
