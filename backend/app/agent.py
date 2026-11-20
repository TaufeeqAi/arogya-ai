"""LangGraph orchestrator: deterministic input guard -> tool-calling agent loop -> deterministic output guard."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from . import safety
from .actions import TZ
from .config import get_settings
from .events import activity, emit
from .tools import ALL_TOOLS

S = get_settings()

SCRIPT_RULE = {
    "devanagari": "Write Hindi in Devanagari script (हिंदी), keep English medical terms and numbers in English "
                  "(e.g. 'आपका HbA1c 8.1 percent है'). This text is spoken by a Hindi TTS voice.",
    "latin": "Write Hindi in Roman script (Hinglish), e.g. 'Aapka HbA1c 8.1 percent hai'.",
}


def system_prompt(language_hint: str) -> str:
    now = datetime.now(TZ)
    return f"""You are Aarogya, a warm, patient-controlled personal health companion for Indian families.
You are speaking on a real-time VOICE call. Today is {now.strftime('%A, %d %B %Y')}, time {now.strftime('%I:%M %p')} IST.
The signed-in patient is Sunita Sharma (patient scope is enforced by the server).

LANGUAGE
- Reply in the language the patient uses: Hindi/Hinglish if they speak Hindi or Hinglish, English if English.
- {SCRIPT_RULE.get(S.response_script, SCRIPT_RULE['devanagari'])}
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
- Call confirm_action ONLY when the patient's latest message is an explicit yes to that proposal.
- If confirm_action returns SLOT_UNAVAILABLE, say nothing was booked, offer the alternatives it returned.
- Only say something is booked/shared/ordered/scheduled after the tool returns ok with a verified status.
- After a booking, offer (separately) to share the latest reports with that doctor (propose_record_share)
  and mention calendar reminder was added.
- Medicine reminders/refills: get_medications first. Never create reminders for an instruction marked
  needs_clarification; explain it is unclear on the prescription and suggest confirming with the doctor.
- Language hint for this session: {language_hint}.
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


def guard_input(state: State, config) -> dict:
    pid, sid, _ = _ctx(config)
    last = state["messages"][-1]
    if isinstance(last, HumanMessage) and safety.is_emergency(str(last.content)):
        activity(pid, sid, "Safety policy: emergency escalation", "failed", "Fixed escalation response; no AI advice",
                 "safety_guard")
        emit(pid, sid, "ui", {"component": "emergency", "version": 1, "props": {"call": "112"}})
        return {"emergency": True, "messages": [AIMessage(content=safety.emergency_reply(S.response_script))]}
    return {"emergency": False}


def text_of(content) -> str:
    """Gemini returns content as parts (text + thought signature); keep only the spoken text."""
    if isinstance(content, list):
        return " ".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content).strip()
    return str(content or "").strip()


def _window(msgs: list[AnyMessage], n: int = 40) -> list[AnyMessage]:
    """Recent history that always starts at a user turn (never mid tool-call)."""
    w = msgs[-n:]
    while w and not isinstance(w[0], HumanMessage):
        w = w[1:]
    return w or msgs[-1:]


async def call_agent(state: State, config) -> dict:
    _, _, lang = _ctx(config)
    resp = await llm.ainvoke([SystemMessage(content=system_prompt(lang))] + _window(state["messages"]), config)
    return {"messages": [resp]}


def guard_output(state: State, config) -> dict:
    pid, sid, _ = _ctx(config)
    last = state["messages"][-1]
    ok, rule = safety.check_output(text_of(last.content))
    if not ok:
        activity(pid, sid, "Safety policy rewrote a response", "failed", "medication-change/diagnosis language blocked",
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


async def run_turn(patient_id: str, session_id: str, text: str, channel: str = "text",
                   language_hint: str = "Hindi/Hinglish") -> str:
    emit(patient_id, session_id, "transcript", {"role": "user", "text": text, "channel": channel})
    config = {"configurable": {"thread_id": session_id, "patient_id": patient_id, "session_id": session_id,
                               "language_hint": language_hint, "user_text": text,
                               "turn_started": datetime.now(timezone.utc).isoformat()}, "recursion_limit": 25}
    try:
        out = await graph.ainvoke({"messages": [HumanMessage(content=text)]}, config)
        reply = text_of(out["messages"][-1].content) or "Maaf kijiye, kya aap dobara bol sakti hain?"
    except Exception as e:  # never leave a voice user in silence
        activity(patient_id, session_id, "Agent error", "failed", type(e).__name__, "agent")
        print("AGENT ERROR", repr(e))
        reply = "Maaf kijiye, abhi mujhe thodi dikkat aa rahi hai. Kya aap ek baar phir bol sakti hain?"
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
