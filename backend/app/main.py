from __future__ import annotations

import asyncio
import json
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import redis.asyncio as aioredis
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select

from . import actions, agora, ingest, memory, storage
from .actions import ActionError, fmt_dt
from .agent import note_external_decision, run_turn
from .config import get_settings
from .db import AgentEvent, Appointment, Doctor, Document, Patient, Reminder, create_all, session
from .events import channel, emit
from .seed import PATIENT_ID, reset_and_seed

S = get_settings()
FILLER = {"devanagari": "जी, एक पल, मैं देख रही हूँ। ", "latin": "Ji, ek pal, main dekh rahi hoon. "}


async def reminder_loop():
    """Persistent scheduler: due reminders are emitted to the patient's devices; daily ones re-arm."""
    while True:
        try:
            now = datetime.now(timezone.utc)
            fired = []
            with session() as s:
                for r in s.scalars(select(Reminder).where(Reminder.status == "scheduled", Reminder.due_at <= now)):
                    r.status = "sent"
                    fired.append({"reminder_id": r.id, "kind": r.kind, "title": r.title, "body": r.body,
                                  "patient_id": r.patient_id, "due_at": r.due_at.isoformat()})
                    if r.recurrence == "daily":
                        s.add(Reminder(patient_id=r.patient_id, kind=r.kind, ref_id=r.ref_id, title=r.title,
                                       body=r.body, recurrence="daily", due_at=r.due_at + timedelta(days=1)))
            for f in fired:
                emit(f["patient_id"], "", "reminder", f)
        except Exception as e:
            print("reminder loop error", e)
        await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_all()
    with session() as s:
        seeded = s.get(Patient, PATIENT_ID) is not None
    if not seeded:
        reset_and_seed()
    task = asyncio.create_task(reminder_loop())
    yield
    task.cancel()


app = FastAPI(title="Aarogya API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

SESSIONS: dict[str, dict] = {}


def patient_for(session_id: str) -> str:
    # Demo: single synthetic patient. Production: derived from the authenticated identity.
    return SESSIONS.get(session_id, {}).get("patient_id", PATIENT_ID)


# ------------------------------------------------------------------ health / session
@app.get("/api/health")
def health():
    return {"ok": True, "llm": bool(S.llm_api_key), "agora": bool(S.agora_app_id and S.agora_customer_id),
            "murf": bool(S.murf_api_key or S.agora_tts_json), "public_base_url": S.public_base_url}


@app.post("/api/session")
def new_session():
    sid = uuid.uuid4().hex[:16]
    SESSIONS[sid] = {"patient_id": PATIENT_ID, "created": time.time()}
    return {"session_id": sid, "patient_id": PATIENT_ID}


class ChatIn(BaseModel):
    session_id: str
    text: str
    language_hint: str = "Hindi/Hinglish"


@app.post("/api/chat")
async def chat(body: ChatIn):
    reply = await run_turn(patient_for(body.session_id), body.session_id, body.text, "text", body.language_hint)
    return {"reply": reply}


# ------------------------------------------------------------------ voice (Agora)
class VoiceIn(BaseModel):
    session_id: str


@app.post("/api/voice/start")
async def voice_start(body: VoiceIn):
    SESSIONS.setdefault(body.session_id, {"patient_id": PATIENT_ID, "created": time.time()})
    try:
        info = await agora.start_agent(body.session_id)
    except Exception as e:
        raise HTTPException(502, str(e))
    SESSIONS[body.session_id]["agent_id"] = info["agent_id"]
    emit(patient_for(body.session_id), body.session_id, "activity",
         {"label": "Voice agent joined (Agora + Murf Falcon)", "status": "done", "detail": info["channel"], "tool": "agora"})
    return info


@app.post("/api/voice/stop")
async def voice_stop(body: VoiceIn):
    agent_id = SESSIONS.get(body.session_id, {}).pop("agent_id", None)
    if not agent_id:
        return {"ok": True}
    return await agora.stop_agent(agent_id)


def _chunk(content: str | None, finish: str | None = None, role: bool = False) -> str:
    delta = {}
    if role:
        delta["role"] = "assistant"
    if content is not None:
        delta["content"] = content
    return "data: " + json.dumps({"id": "chatcmpl-aarogya", "object": "chat.completion.chunk", "created": int(time.time()),
                                  "model": "aarogya-langgraph",
                                  "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]}) + "\n\n"


def _last_user_text(messages: list[dict]) -> str:
    for m in reversed(messages):
        if m.get("role") == "user":
            c = m.get("content")
            if isinstance(c, list):
                return " ".join(p.get("text", "") for p in c if isinstance(p, dict))
            return str(c or "")
    return ""


@app.post("/agora/llm/{session_id}/chat/completions")
async def agora_llm(session_id: str, request: Request):
    """OpenAI-compatible custom LLM endpoint called by Agora Conversational AI for each user turn."""
    auth = request.headers.get("authorization", "")
    if S.agora_llm_shared_secret and auth.replace("Bearer ", "") != S.agora_llm_shared_secret:
        raise HTTPException(401, "bad key")
    body = await request.json()
    text = _last_user_text(body.get("messages", [])).strip()
    pid = patient_for(session_id)
    if not text:
        text = "..."
    task = asyncio.create_task(run_turn(pid, session_id, text, "voice"))

    if not body.get("stream", True):
        reply = await task
        return {"id": "chatcmpl-aarogya", "object": "chat.completion", "model": "aarogya-langgraph",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": reply}, "finish_reason": "stop"}]}

    async def gen():
        yield _chunk("", role=True)
        done, _ = await asyncio.wait({task}, timeout=1.6)
        if not done:  # mask tool latency with a natural filler so the caller is never in silence
            yield _chunk(FILLER.get(S.response_script, FILLER["latin"]))
        reply = await task
        # stream sentence-ish pieces so TTS can start early
        buf = ""
        for ch in reply:
            buf += ch
            if ch in ".?!।," and len(buf) > 12:
                yield _chunk(buf); buf = ""
        if buf:
            yield _chunk(buf)
        yield _chunk(None, finish="stop")
        yield "data: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


# ------------------------------------------------------------------ live agent events (SSE)
@app.get("/api/events")
async def events(request: Request, patient_id: str = PATIENT_ID):
    r = aioredis.Redis.from_url(S.redis_url, decode_responses=True)
    ps = r.pubsub()
    await ps.subscribe(channel(patient_id))

    async def gen():
        yield "event: ready\ndata: {}\n\n"
        try:
            while True:
                if await request.is_disconnected():
                    break
                msg = await ps.get_message(ignore_subscribe_messages=True, timeout=15)
                if msg:
                    yield f"data: {msg['data']}\n\n"
                else:
                    yield ": keepalive\n\n"
        finally:
            await ps.unsubscribe()
            await r.aclose()

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ------------------------------------------------------------------ approvals (tap on card)
class DecideIn(BaseModel):
    session_id: str
    decision: str  # approve | reject


@app.post("/api/approvals/{approval_id}/decide")
def decide(approval_id: str, body: DecideIn):
    pid = patient_for(body.session_id)
    if body.decision == "reject":
        actions.reject(pid, body.session_id, approval_id)
        note_external_decision(body.session_id, "Patient rejected the proposal by tapping Cancel.")
        return {"status": "rejected"}
    try:
        res = actions.execute(pid, body.session_id, approval_id, via="tap on approval card")
        note_external_decision(body.session_id, f"Patient approved via app; result: {json.dumps(res, default=str)[:600]}")
        return {"status": "executed", "result": res}
    except ActionError as e:
        note_external_decision(body.session_id, f"Approval failed: {e.code} {e.message} {json.dumps(e.data, default=str)[:400]}")
        return JSONResponse({"status": "failed", "error": e.code, "message": e.message, **e.data}, status_code=409)


# ------------------------------------------------------------------ data for screens
@app.get("/api/patient")
def get_patient():
    with session() as s:
        p = s.get(Patient, PATIENT_ID)
        return {"id": p.id, "name": p.name, "age": p.age, "sex": p.sex, "city": p.city, "area": p.area,
                "conditions": p.conditions, "allergies": p.allergies, "preferences": p.preferences}


@app.get("/api/documents")
def list_documents():
    with session() as s:
        docs = s.scalars(select(Document).where(Document.patient_id == PATIENT_ID).order_by(Document.issued_on.desc()))
        return [{"id": d.id, "title": d.title, "doc_type": d.doc_type, "source_type": d.source_type,
                 "source_name": d.source_name, "issued_on": d.issued_on.isoformat(), "status": d.status,
                 "trust_label": d.trust_label, "sha256": d.sha256[:12]} for d in docs]


@app.get("/api/documents/{doc_id}")
def get_document(doc_id: str):
    doc, obs = memory.report_observations(PATIENT_ID, doc_id)
    if not doc:
        with session() as s:
            doc = s.get(Document, doc_id)
        if not doc or doc.patient_id != PATIENT_ID:
            raise HTTPException(404)
    return {"id": doc.id, "title": doc.title, "doc_type": doc.doc_type, "issued_on": doc.issued_on.isoformat(),
            "source_name": doc.source_name, "trust_label": doc.trust_label, "text": doc.text, "observations": obs,
            "file_url": f"/api/documents/{doc.id}/file"}


@app.get("/api/documents/{doc_id}/file")
def document_file(doc_id: str):
    with session() as s:
        d = s.get(Document, doc_id)
    if not d or d.patient_id != PATIENT_ID:
        raise HTTPException(404)
    return Response(storage.get(d.storage_key), media_type=d.mime_type,
                    headers={"Content-Disposition": f'inline; filename="{d.id}.pdf"'})


@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...), session_id: str = Form("")):
    data = await file.read()
    if len(data) > 15 * 1024 * 1024:
        raise HTTPException(413, "File too large")
    mime = file.content_type or "application/pdf"
    if not (mime == "application/pdf" or mime.startswith("image/")):
        raise HTTPException(415, "PDF or image only")
    d = ingest.create_upload(PATIENT_ID, file.filename or "document", data, mime)
    if d.status == "extracting":
        ingest.spawn(PATIENT_ID, session_id, d.id)
    return {"document_id": d.id, "status": d.status, "duplicate": d.status != "extracting"}


class ConfirmIn(BaseModel):
    session_id: str = ""


@app.post("/api/documents/{doc_id}/confirm")
def confirm_document(doc_id: str, body: ConfirmIn):
    return ingest.confirm(PATIENT_ID, body.session_id, doc_id)


@app.get("/api/comparison")
def comparison():
    return memory.compare(PATIENT_ID)


@app.get("/api/medications")
def medications():
    return actions.medications_view(PATIENT_ID)


@app.get("/api/appointments")
def appointments():
    with session() as s:
        out = []
        for a in s.scalars(select(Appointment).where(Appointment.patient_id == PATIENT_ID).order_by(Appointment.start)):
            d = s.get(Doctor, a.doctor_id)
            out.append({"id": a.id, "doctor_name": d.name, "clinic": d.clinic, "area": d.area, "start": a.start.isoformat(),
                        "label": fmt_dt(a.start), "booking_ref": a.booking_ref, "status": a.status,
                        "calendar_url": a.calendar_url})
        return out


@app.get("/api/appointments/{appt_id}.ics")
def appointment_ics(appt_id: str):
    with session() as s:
        a = s.get(Appointment, appt_id)
        if not a or a.patient_id != PATIENT_ID:
            raise HTTPException(404)
        d = s.get(Doctor, a.doctor_id)
    f = "%Y%m%dT%H%M%SZ"
    st = a.start.astimezone(timezone.utc)
    ics = "\r\n".join(["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Aarogya//EN", "BEGIN:VEVENT", f"UID:{a.id}@aarogya",
                       f"DTSTAMP:{datetime.now(timezone.utc).strftime(f)}", f"DTSTART:{st.strftime(f)}",
                       f"DTEND:{(st + timedelta(minutes=30)).strftime(f)}", f"SUMMARY:Doctor visit: {d.name}",
                       f"LOCATION:{d.clinic}\\, {d.area}", f"DESCRIPTION:Booking ref {a.booking_ref}",
                       "BEGIN:VALARM", "TRIGGER:-PT2H", "ACTION:DISPLAY", "DESCRIPTION:Doctor visit", "END:VALARM",
                       "END:VEVENT", "END:VCALENDAR"])
    return Response(ics, media_type="text/calendar", headers={"Content-Disposition": f'attachment; filename="{a.booking_ref}.ics"'})


@app.get("/api/reminders")
def reminders():
    with session() as s:
        rs = s.scalars(select(Reminder).where(Reminder.patient_id == PATIENT_ID).order_by(Reminder.due_at))
        return [{"id": r.id, "kind": r.kind, "title": r.title, "body": r.body, "due_at": r.due_at.isoformat(),
                 "label": fmt_dt(r.due_at), "status": r.status, "recurrence": r.recurrence} for r in rs]


class ReminderAction(BaseModel):
    action: str  # taken | skipped | snoozed


@app.post("/api/reminders/{rid}/action")
def reminder_action(rid: str, body: ReminderAction):
    with session() as s:
        r = s.get(Reminder, rid)
        if not r or r.patient_id != PATIENT_ID:
            raise HTTPException(404)
        r.status = body.action
        if body.action == "snoozed":
            s.add(Reminder(patient_id=r.patient_id, kind=r.kind, ref_id=r.ref_id, title=r.title, body=r.body,
                           due_at=datetime.now(timezone.utc) + timedelta(minutes=10)))
    emit(PATIENT_ID, "", "activity", {"label": f"Patient reported: {body.action}", "status": "done",
                                      "detail": r.title + " (self-reported)", "tool": "adherence"})
    return {"ok": True}


@app.get("/api/activity")
def recent_activity(limit: int = 40):
    with session() as s:
        evts = s.scalars(select(AgentEvent).where(AgentEvent.patient_id == PATIENT_ID, AgentEvent.type == "activity")
                         .order_by(AgentEvent.id.desc()).limit(limit))
        return [{"ts": e.created_at.isoformat(), **e.payload} for e in evts]


# ------------------------------------------------------------------ demo controls
@app.post("/api/demo/reset")
def demo_reset():
    reset_and_seed()
    return {"ok": True}


@app.post("/api/demo/conflict")
def demo_conflict(on: bool = True):
    actions._r.set(actions.CONFLICT_KEY, "1") if on else actions._r.delete(actions.CONFLICT_KEY)
    return {"conflict_next_booking": on}


# ------------------------------------------------------------------ serve the exported web app (PWA) on the same origin
from pathlib import Path as _P
from fastapi.responses import FileResponse as _F

_DIST = _P(__file__).resolve().parents[2] / "app" / "dist"


@app.get("/{full_path:path}", include_in_schema=False)
def spa(full_path: str):
    if full_path.startswith(("api/", "agora/")):
        raise HTTPException(404)
    f = (_DIST / full_path).resolve()
    if full_path and f.is_file() and _DIST.resolve() in f.parents:
        return _F(f)
    idx = _DIST / "index.html"
    if idx.exists():
        return _F(idx, headers={"Cache-Control": "no-cache"})
    return JSONResponse({"error": "web app not built; run: cd app && npx expo export -p web"}, status_code=404)


@app.post("/api/demo/medication-reminder-now")
def demo_reminder_now():
    with session() as s:
        s.add(Reminder(patient_id=PATIENT_ID, kind="medication", ref_id="med-metformin", title="Metformin 500 mg",
                       body="After breakfast", due_at=datetime.now(timezone.utc)))
    return {"ok": True}
