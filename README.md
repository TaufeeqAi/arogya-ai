# Aarogya — Your health history. Your language. Your care, connected.

**Build with Agora – BLR · PS11: Breaking Language Barriers Through Agentic Voice AI**

Aarogya is a voice-first, Hindi/Hinglish health companion. It remembers a patient's medical history across
reports, labs and prescriptions, explains it with sources, and **acts on it**: books doctor appointments, shares
records with consent, sets medicine reminders and orders refills. Every consequential action is approved by the
patient and verified against the connected system.

> Aarogya never diagnoses, prescribes or changes medicines. It explains what documents say and coordinates care.

---

## What makes it different

| Typical health voice bot | Aarogya |
|---|---|
| Answers from one document | **Longitudinal health memory** (Postgres + Qdrant) across labs and dates |
| "Your value is high" | **Evidence-linked**: every claim cites the source report; deterministic comparison, units checked |
| Says "please book a doctor" | **Books it**: search → live slots → approval → revalidate → book → verify → calendar → reminders |
| LLM decides when to act | **Deterministic consent gate**: proposal must be shown first + explicit "haan/yes" in a later turn |
| Breaks when a slot vanishes | **Recovers**: slot taken after approval → nothing booked, alternatives offered |
| Trusts OCR blindly | **AI extraction → patient review** before values enter memory |
| Generic chat UI | **Generative UI**: agent picks typed cards (report, chart, slots, approval, booking, meds) |
| Hidden reasoning | **Live agent activity panel**: every tool call, approval and verification visible |

## Architecture

```
Phone / Web (Expo, React Native Web PWA)
   │  Agora RTC (mic + agent audio)         SSE (agent events, generative UI)   HTTP (approvals, uploads)
   ▼
Agora Conversational AI Engine ── ASR (hi-IN) ── Murf Falcon TTS (hi-IN-shweta)
   │  custom LLM (OpenAI-compatible, streaming)
   ▼
FastAPI  /agora/llm/{session}/chat/completions
   │
LangGraph: guard_input (emergency rules + NeMo Guardrails embedding rail) → agent ⇄ tools → guard_output
   │            Gemini (flash-lite, fallback chain)
   ├─ Health Memory: Postgres (observations, provenance) + Qdrant (semantic notes) + deterministic comparison
   ├─ Actions: payload-hash approvals · idempotent booking · verification · calendar (.ics + Google) · reminders
   ├─ Ingestion: upload → sha256 → Gemini structured extraction → patient review → memory
   ├─ Provider sync: signed record from connected clinic → signature + patient match + consent → import
   └─ Event bus: Redis pub/sub → SSE → live activity + generative UI cards; audit log in Postgres
```

**Single decision authority:** Agora handles audio, ASR, turn-taking and Murf TTS; our LangGraph agent is the only
thing that decides and acts, so no two LLMs make competing decisions.

## Demo script (3 minutes)

1. **"Meri latest blood report samjhao."** → report card with values outside the lab range, source PDF linked.
2. **"Pichhli report se compare karo."** → deterministic chart: HbA1c 7.2 → 8.1, Vitamin D/TSH marked *not comparable*.
3. *(Health Locker)* **Upload** `docs/demo/Metro_Path_Labs_Thyroid_Vitamin_14Feb2026.pdf` (different lab) → AI extraction → confirm → thyroid/vitamin trends gain a data point.
4. **"Saturday morning doctor ka appointment chahiye."** → live slots → **"Pehla wala"** → approval card (nothing booked yet).
5. *(Profile → Simulate slot conflict)* **"Haan, book kar do."** → slot taken → nothing booked → alternatives → **"11 baje wala, haan"** → booked, verified ref, calendar + 2 reminders.
6. **"Report doctor ke saath share kar do"** → separate consent → shared for 7 days.
7. **Medicines** (7 on record): *"Kaun si dawaiyon ke reminder lage hain?"* → Telmisartan (daily) + Vitamin D3 (weekly) already on;
   *"Pantoprazole ka reminder laga do"* → proposed → "haan" → set; *"Kaunsi dawaiyan khatam hone wali hain?"* → Metformin,
   Pantoprazole → refill with approval; *"Glimepiride wapas shuru karni hai, order kar do"* → refused (stopped by doctor);
   **Atorvastatin refused** (instruction unclear on prescription).
   *(Profile → Simulate: Dr. Meera's clinic sends clarified prescription)* → signed provider record imported →
   **"Atorvastatin ka reminder laga do"** → now allowed, set for 9:30 PM.
8. **"Kya main dose double kar loon?"** → safe refusal. **"Seene mein dard ho raha hai"** → fixed 112 escalation.

## Run it

```bash
docker compose up -d                       # Postgres, Qdrant, Redis
cp .env.example .env                       # fill Agora, Murf, Gemini keys
cd backend && uv sync && uv run uvicorn app.main:app --port 8000
ngrok http 8000                            # put the https URL in PUBLIC_BASE_URL
cd app && npm i && npx expo export -p web  # backend serves the PWA at the ngrok URL
```

Windows helpers: `scripts/restart_backend.ps1`, `scripts/start_web_dev.ps1` (dev server on :8081).
Regression: `cd backend && uv run python -m scripts.careloop_e2e --conflict`.

## Safety model (defence in depth, tested by `scripts/redteam.py`: 9/9)

- **NeMo Guardrails** input rail: embedding-only dialog rails with a local multilingual model (~30 ms, no LLM
  call) block dose-change, diagnosis, other-patient and jailbreak requests in Hindi, Hinglish and English.
- Emergency language (Hindi, Hinglish, English, Devanagari) → fixed escalation, no LLM advice.
- Output guard blocks dose-change / diagnosis language.
- Approvals bound to exact payload hash, 10-minute expiry, one-time execution, idempotency keys.
- Consent for record sharing is separate from booking consent.
- AI-extracted values are excluded from answers and comparisons until the patient confirms them.
- Synthetic data only; patient scope resolved server-side.

Full product spec, architecture, schema, workflow contracts and UX spec: [`docs/spec`](docs/spec).
