"""LangGraph orchestrator: deterministic input guard -> tool-calling agent loop -> deterministic output guard."""
from __future__ import annotations

import asyncio
import re
import time
from datetime import datetime, timezone
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from . import nemo_rail, safety, transcript
from .actions import TZ
from .config import get_settings
from .events import activity, emit
from .tools import ALL_TOOLS

S = get_settings()

SCRIPT_RULE = {
    "devanagari": "Use ONE script per reply, matching the patient's message: if they wrote/spoke in Devanagari, reply "
                  "fully in Devanagari Hindi (keep test names like HbA1c, LDL and numbers in English); if they wrote in "
                  "Roman Hinglish, reply fully in Roman Hinglish. Never mix scripts in one reply.",
    "latin": "Write Hindi in Roman script (Hinglish), e.g. 'Aapka HbA1c 8.1 percent hai'. Never use Devanagari.",
}


def system_prompt(lang_rule: str) -> str:
    now = datetime.now(TZ)
    return f"""MANDATORY REPLY LANGUAGE FOR THIS TURN: {lang_rule}
(The patient may switch language at any time; always follow the rule above for this reply, regardless of earlier turns.)

You are Aarogya, a warm, patient-controlled personal health companion for Indian families.
You are speaking on a real-time VOICE call. Today is {now.strftime('%A, %d %B %Y')}, time {now.strftime('%I:%M %p')} IST.
The signed-in patient is Sunita Sharma (patient scope is enforced by the server).

PERSONA: You are female. Always use feminine first-person grammar in Hindi: "main kar sakti hoon",
"dekh rahi hoon", "maine dikha di hai" (मैं कर सकती हूँ, देख रही हूँ). Address the patient respectfully as "Sunita ji".

LANGUAGE
- Reply in the language the patient uses: Hindi/Hinglish if they speak Hindi or Hinglish, English if English.
- {SCRIPT_RULE.get(S.response_script, SCRIPT_RULE['devanagari'])}
- Times: say them the way people speak, e.g. "raat 9:30 baje", "subah 11 baje" (रात 9:30 बजे).
- Voice style: 1-3 short spoken sentences per turn (max ~45 words). No markdown, no bullet lists, no emojis,
  no URLs, no IDs. Say dates naturally ("18 November"). The screen shows the details as cards, so say
  "screen par dikha diya hai" instead of reading long lists.

GROUNDING (non-negotiable)
- Never state any fact about the patient's health unless it came from a tool result in this conversation.
  Always use tools to fetch records; mention the source naturally ("18 November ki report ke hisaab se").
- You explain what documents say. You do NOT diagnose, predict disease, prescribe, change, stop or adjust
  medicine doses. For such questions say a doctor/pharmacist must decide and offer to book a doctor.
- Say "lab range se upar/neeche" (outside the lab's printed range), never "dangerous" or "normal for you".
- Comparisons: use compare_lab_history; report numbers and direction only.

ACTIONS (human-in-the-loop)
- To book: search_doctors -> check_slots (resolve 'Saturday' etc. to an exact YYYY-MM-DD date; prefer the
  patient's preferred doctor Dr. Meera Rao and morning time if unspecified) -> offer 1-2 slots ->
  propose_appointment for the chosen slot -> ask "Kya main yeh appointment book kar doon?".
- If exactly one slot fits (or the patient names one), call propose_appointment in the SAME turn and ask
  for confirmation, so the patient only has to say yes once. Never ask "book karoon?" without a pending proposal.
- If the patient rejects a proposed slot, call cancel_pending_action, then offer alternatives.
- Call confirm_action ONLY when the patient's latest message is an explicit yes to that proposal.
- If confirm_action returns SLOT_UNAVAILABLE, say nothing was booked, offer the alternatives it returned.
- Only say something is booked/shared/ordered/scheduled after the tool returns ok with a verified status.
- After a booking, offer (separately) to share the latest reports with that doctor (propose_record_share)
  and mention calendar reminder was added.
- "What needs attention / how is my liver / explain this test / what to ask my doctor": get_health_status
  (optionally one system), then prepare_doctor_brief for doctor questions. Say "outside the lab's range", never
  "abnormal" or a disease name; suggest discussing with a doctor and offer to book.
- Follow-ups / pending care / "kya baaki hai": get_care_plan (doctor-documented tasks with sources).
- Sharing: include a short purpose; patient can revoke anytime (revoke_record_share).
- REMINDER vs ORDER: "reminder / yaad dilana / alarm / remind" means propose_medication_reminders. Only call
  propose_refill when the patient explicitly asks to order / buy / refill / mangwana. Never switch one for the other.
- If reminders are already active, say so (with the times) instead of proposing again.
- A medicine with status "stopped" was stopped by the doctor: never set reminders, refill or suggest restarting it.
- When several medicines are low on supply, list them and ask which to refill (one approval per order).
- Medicine reminders/refills: get_medications first. Never create reminders for an instruction marked
  needs_clarification; explain it is unclear on the prescription and suggest confirming with the doctor.
"""


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    emergency: bool


def _make_llm(model: str):
    if "generativelanguage.googleapis.com" in S.llm_base_url or model.startswith("gemini"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        kw = {"thinking_level": S.llm_thinking} if not model.startswith("gemini-2") else {"thinking_budget": 0}
        return ChatGoogleGenerativeAI(model=model, google_api_key=S.llm_api_key, temperature=S.llm_temperature,
                                      timeout=25, max_retries=0, **kw)
    return ChatOpenAI(model=model, base_url=S.llm_base_url, api_key=S.llm_api_key or "missing",
                      temperature=S.llm_temperature, timeout=25, max_retries=0)


# Primary model + fallbacks (separate per-model quotas; also covers transient provider errors)
_models = [S.llm_model] + [m.strip() for m in S.llm_fallback_models.split(",") if m.strip()]
llm = _make_llm(_models[0]).bind_tools(ALL_TOOLS).with_fallbacks(
    [_make_llm(m).bind_tools(ALL_TOOLS) for m in _models[1:]])


def _ctx(config) -> tuple[str, str, str]:
    c = config.get("configurable", {})
    return c["patient_id"], c.get("session_id", ""), c.get("language_hint", "Hindi/Hinglish")


async def guard_input(state: State, config) -> dict:
    pid, sid, _ = _ctx(config)
    last = state["messages"][-1]
    text = str(last.content) if isinstance(last, HumanMessage) else ""
    if text and safety.is_emergency(text):
        activity(pid, sid, "Safety policy: emergency escalation", "blocked", "Fixed escalation response; no AI advice",
                 "safety_guard")
        emit(pid, sid, "ui", {"component": "emergency", "version": 1, "props": {"call": "112"}})
        rl = config.get("configurable", {}).get("reply_lang", "")
        reply = safety.EMERGENCY_REPLY_EN if rl == "english" else safety.emergency_reply(S.response_script, text)
        return {"emergency": True, "messages": [AIMessage(content=reply)]}
    if text and not text.startswith("[App event"):
        key, ms = await nemo_rail.check(text)
        if key:
            activity(pid, sid, f"NeMo Guardrails input rail: {key.replace('_', ' ')}", "blocked",
                     f"blocked before the LLM · {ms:.0f} ms", "nemo_guardrails")
            rl = config.get("configurable", {}).get("reply_lang", "hinglish")
            return {"emergency": True, "messages": [AIMessage(content=nemo_rail.REPLIES_EN[key] if rl == "english" else nemo_rail.REPLIES[key])]}
    return {"emergency": False}


def text_of(content) -> str:
    """Gemini returns content as parts (text + thought signature); keep only the spoken text."""
    if isinstance(content, list):
        return "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content).strip()
    return str(content or "").strip()


def _window(msgs: list[AnyMessage], n: int = 40) -> list[AnyMessage]:
    """Recent history that always starts at a user turn (never mid tool-call)."""
    w = msgs[-n:]
    while w and not isinstance(w[0], HumanMessage):
        w = w[1:]
    return w or msgs[-1:]


async def call_agent(state: State, config) -> dict:
    _, sid, lang = _ctx(config)
    t0 = time.perf_counter()
    last_user = next((str(m.content) for m in reversed(state["messages"]) if isinstance(m, HumanMessage)
                      and not str(m.content).startswith("[App event")), "")
    rl = config.get("configurable", {}).get("reply_lang") or safety.reply_language(last_user)
    lang_rule = {"english": "ENGLISH. The patient wrote in English, so reply ONLY in natural English.",
                 "devanagari": "HINDI in Devanagari script. Write months, weekdays and time-of-day in Hindi (18 नवंबर, शनिवार, शाम 5:30 बजे); keep test names like HbA1c in English. Use feminine first person.",
                 "hinglish": "ROMAN HINGLISH (Hindi written in Latin script). Use feminine first person."}[rl]
    tag = {"english": "[Reply in English]", "devanagari": "[हिंदी (देवनागरी) में जवाब दें]",
           "hinglish": "[Reply in Roman Hinglish]"}[rl]
    window = _window(state["messages"])
    # annotate the latest patient turn (model-facing copy only; stored history stays clean)
    for i in range(len(window) - 1, -1, -1):
        m = window[i]
        if isinstance(m, HumanMessage) and not str(m.content).startswith("[App event"):
            window = window[:i] + [HumanMessage(content=str(m.content) + "  " + tag)] + window[i + 1:]
            break
    voice_rule = (" VOICE CALL: this reply is spoken aloud. Maximum 2 short sentences and at most 2 numbers. "
                  "Never list all values; the screen card shows the details.") if config.get("configurable", {}).get("channel") == "voice" else ""
    msgs = [SystemMessage(content=system_prompt(lang_rule) + voice_rule)] + window
    resp = await llm.ainvoke(msgs, config)
    calls = [c["name"] for c in getattr(resp, "tool_calls", []) or []]
    print(f"LLM {sid} {time.perf_counter() - t0:.2f}s -> {calls or 'answer'}", flush=True)
    return {"messages": [resp]}


def guard_output(state: State, config) -> dict:
    pid, sid, _ = _ctx(config)
    last = state["messages"][-1]
    ok, rule = safety.check_output(text_of(last.content))
    if not ok:
        activity(pid, sid, "Safety policy rewrote a response", "blocked", "medication-change/diagnosis language blocked",
                 "output_guard")
        return {"messages": [AIMessage(content=safety.SAFE_REDIRECT, id=last.id)]}
    return {}


def route_after_agent(state: State) -> str:
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else "guard_output"


g = StateGraph(State)
g.add_node("guard_input", guard_input)
g.add_node("agent", call_agent)
g.add_node("tools", ToolNode(ALL_TOOLS))
g.add_node("guard_output", guard_output)
g.add_edge(START, "guard_input")
g.add_conditional_edges("guard_input", lambda s: END if s.get("emergency") else "agent")
g.add_conditional_edges("agent", route_after_agent, {"tools": "tools", "guard_output": "guard_output"})
g.add_edge("tools", "agent")
g.add_edge("guard_output", END)
graph = g.compile(checkpointer=MemorySaver())


def turn_language(text: str) -> str:
    """Fast, deterministic reply-language choice. Handles the hi-IN ASR writing English speech in Devanagari."""
    if transcript.needs_normalization(text) or re.search(r"[ऀ-ॿ]", text):
        en, hi = transcript.english_signal(text)
        if en >= 2 and en >= 2 * hi:
            return "english"
        if en >= 2 and hi >= 1:
            return "hinglish"
        return "devanagari"
    return safety.reply_language(text)


async def run_turn(patient_id: str, session_id: str, text: str, channel: str = "text",
                   language_hint: str = "Hindi/Hinglish") -> str:
    rl = turn_language(text)
    try:
        from .db import Patient, session as _sess
        with _sess() as _s:
            pref = ((_s.get(Patient, patient_id).preferences or {}).get("reply_language") or "auto")
        rl = {"hindi": "devanagari", "english": "english", "hinglish": "hinglish"}.get(pref, rl)
    except Exception:
        pass
    # Show the user's words in the right script; runs in parallel with the agent (off the critical path)
    norm_task = asyncio.create_task(transcript.normalize(text)) if transcript.needs_normalization(text) else None

    print(f"USER {session_id} [{channel}/{rl}]: {text}", flush=True)

    async def _emit_user():
        shown = text
        if norm_task:
            done, _ = await asyncio.wait({norm_task}, timeout=2.5)  # never cancels; falls back to raw ASR text
            if done:
                try:
                    shown = norm_task.result() or text
                except Exception:
                    shown = text
        emit(patient_id, session_id, "transcript", {"role": "user", "text": shown, "channel": channel,
                                                    "asr_raw": text if shown != text else None})
    user_emit = asyncio.create_task(_emit_user())

    config = {"configurable": {"thread_id": session_id, "patient_id": patient_id, "session_id": session_id,
                               "language_hint": language_hint, "user_text": text, "reply_lang": rl, "channel": channel,
                               "turn_started": datetime.now(timezone.utc).isoformat()}, "recursion_limit": 25}
    try:
        out = await graph.ainvoke({"messages": [HumanMessage(content=text)]}, config)
        reply = text_of(out["messages"][-1].content) or "Maaf kijiye, kya aap dobara bol sakti hain?"
    except Exception as e:  # never leave a voice user in silence
        activity(patient_id, session_id, "Agent error", "failed", type(e).__name__, "agent")
        print("AGENT ERROR", repr(e))
        reply = "Maaf kijiye, abhi mujhe thodi dikkat aa rahi hai. Kya aap ek baar phir bol sakti hain?"
    await asyncio.wait({user_emit}, timeout=3)  # keep the user line before the assistant line (never cancels)
    print(f"AAROGYA {session_id}: {reply[:200]}", flush=True)
    emit(patient_id, session_id, "transcript", {"role": "assistant", "text": reply, "channel": channel})
    return reply


def note_external_decision(session_id: str, text: str) -> None:
    """Record approvals made by tapping the card so the voice agent knows what happened."""
    try:
        graph.update_state({"configurable": {"thread_id": session_id}},
                           {"messages": [HumanMessage(content=f"[App event, not spoken by patient] {text}"),
                                         AIMessage(content="Noted.")]}, as_node="guard_output")
    except Exception as e:
        print("note_external_decision failed", e)
