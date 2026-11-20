"""Agora Conversational AI session management. Agora handles RTC audio, ASR, turn-taking and Murf TTS;
our /agora/llm endpoint is the custom LLM, so LangGraph stays the single decision authority."""
from __future__ import annotations

import base64
import json
import time
import uuid

import httpx

from .access_token2 import build_rtc_rtm_token
from .config import get_settings

S = get_settings()

GREETING = {
    "devanagari": "नमस्ते सुनीता जी, मैं आरोग्य हूँ। आज मैं आपकी कैसे मदद कर सकती हूँ?",
    "latin": "Namaste Sunita ji, main Aarogya hoon. Aaj main aapki kaise madad kar sakti hoon?",
}


def token(channel: str, uid: int) -> str:
    if not S.agora_app_certificate:
        return ""  # project in testing mode (no certificate)
    return build_rtc_rtm_token(S.agora_app_id, S.agora_app_certificate, channel, uid)


def _auth_header() -> dict:
    raw = f"{S.agora_customer_id}:{S.agora_customer_secret}".encode()
    return {"Authorization": "Basic " + base64.b64encode(raw).decode(), "Content-Type": "application/json"}


def tts_block() -> dict:
    if S.agora_tts_json.strip():
        return json.loads(S.agora_tts_json)
    return {"vendor": "murf", "params": {"api_key": S.murf_api_key, "voice_id": S.murf_voice_id,
                                         "model": S.murf_model, "locale": S.murf_locale, "style": "Conversational"}}


def join_body(channel: str, session_id: str) -> dict:
    return {
        "name": f"aarogya-{session_id}-{int(time.time())}",
        "properties": {
            "channel": channel,
            "token": token(channel, S.agora_agent_uid),
            "agent_rtc_uid": str(S.agora_agent_uid),
            "remote_rtc_uids": [str(S.agora_user_uid)],
            "idle_timeout": 300,
            "advanced_features": {"enable_aivad": True},
            "asr": json.loads(S.agora_asr_json),
            "llm": {
                "url": f"{S.public_base_url.rstrip('/')}/agora/llm/{session_id}/chat/completions",
                "api_key": S.agora_llm_shared_secret,
                "system_messages": [{"role": "system", "content": "Aarogya health companion"}],
                "greeting_message": GREETING.get(S.response_script, GREETING["latin"]),
                "failure_message": "Maaf kijiye, ek pal rukiye.",
                "max_history": 10,
                "params": {"model": "aarogya-langgraph"},
            },
            "tts": tts_block(),
        },
    }


async def start_agent(session_id: str) -> dict:
    channel = f"aarogya-{uuid.uuid4().hex[:8]}"
    body = join_body(channel, session_id)
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(f"{S.agora_api_base}/{S.agora_app_id}/join", headers=_auth_header(), json=body)
    if r.status_code >= 300:
        safe = json.loads(json.dumps(body))
        safe["properties"]["tts"]["params"] = {k: ("***" if "key" in k else v) for k, v in safe["properties"]["tts"].get("params", {}).items()}
        raise RuntimeError(f"Agora join failed {r.status_code}: {r.text} | body={json.dumps(safe)[:1500]}")
    data = r.json()
    return {"app_id": S.agora_app_id, "channel": channel, "uid": S.agora_user_uid,
            "token": token(channel, S.agora_user_uid) or None, "agent_id": data.get("agent_id"),
            "agent_uid": S.agora_agent_uid, "status": data.get("status")}


async def stop_agent(agent_id: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(f"{S.agora_api_base}/{S.agora_app_id}/agents/{agent_id}/leave", headers=_auth_header())
    return {"status": r.status_code, "body": r.text[:300]}
