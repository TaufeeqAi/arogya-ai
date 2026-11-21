# Aarogya — Your health history. Your language. Your care, connected.

**Build with Agora – BLR · PS11: Breaking Language Barriers Through Agentic Voice AI**

Aarogya is a voice-first health companion that speaks **Hindi, Hinglish and English**. It remembers a patient's
medical history across labs and years, explains it with sources, shows what needs attention by body system — and
**acts on it**: books doctors, shares records with consent, sets medicine reminders, orders refills and tracks
doctor-advised follow-ups. Every consequential action is approved by the patient and verified against the connected
system.

> Aarogya explains what documents say and coordinates care. It never diagnoses, prescribes, changes doses or restarts
> stopped medicines. All data in this repo is **synthetic**.

- **Web app (PWA)** with side navigation · **Android app** (Expo / React Native) with bottom tabs and a centre mic
- **Voice:** Agora Conversational AI (RTC + ASR + turn-taking) → our LangGraph agent (custom LLM) → **Murf Falcon TTS**

---

## What makes it different

| Typical health voice bot | Aarogya |
|---|---|
| Answers from one document | **Longitudinal health memory** — 4 lab reports, 33 tests, 2 labs, 1 year of trends (Postgres + Qdrant) |
| "Your value is high" | **Evidence-linked** answers; deterministic comparisons (same test + same unit); every value links to its source PDF |
| A chat window | **Health tab**: 8 body systems around a body figure, "needs attention" per system, detail screens with trends and "what is this test" |
| Says "please see a doctor" | **Books it**: search → live slots → approval → revalidate → book → verify → calendar + reminders → follow-up marked booked |
| LLM decides when to act | **Deterministic consent gate**: proposal shown first + explicit yes ("haan / yes / यस") in a later turn; approvals bound to a payload hash |
| Breaks when a slot vanishes | **Recovers**: slot taken after approval → nothing booked → alternatives offered; outcome UNKNOWN never retried blindly |
| Trusts OCR blindly | **AI extraction → patient review**; unconfirmed values are never used in answers or comparisons |
| One language per session | **Per-turn language**: English, Roman Hinglish or Devanagari Hindi — even when ASR writes English in Devanagari |
| Reads "8." and "1%" | **Speech-safe TTS**: numbers never split, units spelled out, Hindi replies speak dates/times/numbers in Hindi |
| One safety prompt | **Defence in depth**: NeMo Guardrails embedding rail (local, ~30 ms) + deterministic emergency/consent/output rules + agent policy |

## Feature tour

| Area | What it does |
|---|---|
| **Home** | Today: next appointment, today's reminders, *needs your attention* (pending approvals, overdue follow-ups, low supply), key results, recent documents |
| **Health** | Body-system overview (Sugar, Heart, Liver, Kidney, Hemogram, Thyroid, Nutrition, Infections) → detail per system: value, lab range, status, 3-report trend, ⓘ test explanation, source, *Book consultation* / *Ask Aarogya* |
| **Aarogya (voice)** | Real-time voice + text; generative UI cards (report, comparison, doctors, slots, approval, booking, sharing, medicines, health, care plan, doctor brief); live agent activity panel |
| **Records** | Health Locker with trust labels (provider verified / patient uploaded / AI extracted / patient confirmed), upload PDF or photo → AI extraction → review |
| **Care** | Doctor-advised follow-ups, appointments, 7-medicine cabinet (reminders on / none yet / needs clarification / stopped), adherence, refill state |
| **Timeline** | Everything in one history: reports, visits, medicines, follow-ups, sharing, orders — filterable, source-linked |
| **Notifications** | Reminder types, appointment lead times, quiet hours (honoured by the scheduler), privacy (hide medicine names) |
| **Profile** | Reply language (Auto / हिंदी / Hinglish / English), shared records with **Revoke**, demo controls |

## Architecture

```
Phone (Expo Android, react-native-agora)  ·  Web (Expo web PWA, agora-rtc-sdk-ng)
   │  Agora RTC (mic + agent audio, AI-client audio scenario)   SSE (agent events, UI cards)   HTTP (approvals, uploads)
   ▼
Agora Conversational AI Engine ── ASR (hi-IN) ── Murf Falcon TTS (en-IN-anusha, bilingual)
   │  custom LLM (OpenAI-compatible, streaming, shared secret)
   ▼
FastAPI  /agora/llm/{session}/chat/completions        (filler while tools run, sentence-safe chunks, barge-in cancels stale turn)
   │
LangGraph: guard_input (emergency rules + NeMo Guardrails rail) → agent ⇄ 18 tools → guard_output
   │            Gemini Flash-Lite (minimal thinking, multi-model fallback chain)
   ├─ Health memory: Postgres observations (provenance, validation status) + Qdrant semantic notes + deterministic comparison
   ├─ Lab catalogue: 33 tests → 8 body systems, lab ranges, plain-language "what this test measures"
   ├─ Actions: payload-hash approvals · idempotent booking + verification · calendar (.ics + Google) · reminders (daily/weekly)
   │           · consented sharing (purpose, 7-day expiry, revoke) · sandbox pharmacy (idempotent order, verify, cancel)
   ├─ Ingestion: upload → sha256 → Gemini structured extraction (schema-bound) → patient review → memory
   ├─ Provider sync: signed clinic record → signature + patient match + consent → import (clarifies unclear prescriptions)
   ├─ Scheduler: reminders honour notification preferences (muted types, quiet hours)
   └─ Event bus: Redis pub/sub → SSE → live activity + generative UI; audit trail in Postgres
```

**Single decision authority:** Agora handles audio, ASR, turn-taking and Murf TTS; the LangGraph agent is the only
component that decides and acts.

## Demo script (≈4 minutes)

1. **Home → Health tab** — "Needs attention · 6 areas" → tap **Liver** → ALT 36 → 44 → 52 U/L vs lab range < 40, ⓘ explains ALT.
2. 🎙 **"What needs attention in my reports?"** → health overview card. **"Meri liver report samjhao, ALT kya hota hai?"**
3. **"Pichhli report se compare karo."** → deterministic comparison chart with sources.
4. **Records → Upload** `docs/demo/Metro_Path_Labs_Thyroid_Vitamin_14Feb2026.pdf` (different lab) → AI extraction → confirm → new data points.
5. **"Saturday morning doctor ka appointment chahiye."** → slots → approval card (nothing booked yet).
   *(Profile → Simulate slot conflict)* **"Haan, book kar do."** → slot taken → nothing booked → alternative → **"Yes, book it"** → verified booking, calendar, reminders, follow-up marked booked.
6. **"Report doctor ke saath share kar do"** → separate consent with purpose → shared for 7 days → revoke in Profile.
7. **Medicines:** "Kaun si dawaiyon ke reminder lage hain?" → Telmisartan (daily) + Vitamin D3 (weekly) · "Pantoprazole ka reminder laga do" → "haan" ·
   "Kaunsi dawaiyan khatam hone wali hain?" → refill with approval · "Glimepiride wapas shuru karni hai" → **refused (stopped by doctor)** ·
   Atorvastatin reminder **refused** (unclear prescription) → *(Profile → Dr. Meera's clinic sends clarified prescription)* → now allowed.
8. **Safety:** "Kya main dose double kar loon?" → refused · "Seene mein dard ho raha hai" → fixed 112 escalation · English questions → English answers.

## Run it

```bash
docker compose up -d                                   # Postgres, Qdrant, Redis
cp .env.example .env                                   # Gemini, Agora, Murf keys + a random AGORA_LLM_SHARED_SECRET
cd backend && uv sync && uv run uvicorn app.main:app --port 8000
ngrok http --url=<your-static-domain> 8000             # PUBLIC_BASE_URL = that https URL
cd app && npm install && npx expo export -p web         # the backend serves the PWA at the public URL
```

- Windows helpers: `scripts/restart_backend.ps1` (detached, UTF-8 safe), `scripts/start_web_dev.ps1` (Expo dev server on :8081).
- Android APK (cloud build, no Android Studio): `cd app && npx eas-cli build -p android --profile preview` (needs `EXPO_TOKEN`).
- Demo data reset: `POST /api/demo/reset` or Profile → Reset demo data.

## Tests

```bash
cd backend
PYTHONIOENCODING=utf-8 uv run python -m scripts.careloop_e2e   # 12 assertions: report → booking w/ conflict → follow-up → share/revoke → refill/cancel → safety
PYTHONIOENCODING=utf-8 uv run python -m scripts.redteam        # 9 adversarial cases: injection, self-approval, diagnosis, dose change,
                                                               # other patient's data, false premise, overdose, sharing without consent
```
Both exit non-zero on failure. Both passed in full (**12/12** and **9/9**) on `gemini-3.5-flash-lite`; results depend on the LLM tier and quota (free-tier daily limits and weaker models cause failures).

## Safety model (defence in depth)

- **NeMo Guardrails** input rail — embedding-only dialog rails with a local multilingual model (no extra LLM call) block
  dose-change, diagnosis, other-patient and jailbreak requests in Hindi, Hinglish and English.
- **Emergency rules** (Hindi, Hinglish, English, Devanagari) → fixed 112 escalation, no AI advice.
- **Consent gate** — an action executes only if it was proposed in an earlier turn and the latest utterance is an explicit yes;
  approvals are bound to a payload hash, expire after 10 minutes, execute once, and older proposals are withdrawn.
- **Output guard** blocks medication-change / diagnosis language; stopped medicines can never be restarted, refilled or reminded.
- Health status is "outside the lab's printed range", never a diagnosis; AI-extracted values need patient confirmation.
- Sharing needs separate consent with a purpose, expires in 7 days and is revocable. Synthetic data only.

## Repository

```
backend/app/     FastAPI app: agent.py (LangGraph), tools.py, actions.py, memory.py, labs.py, views.py, ingest.py,
                 provider.py, safety.py, nemo_rail.py, agora.py, speech*.py, transcript.py, seed.py
backend/guardrails/   NeMo Guardrails config (rails.co, config.yml)
backend/scripts/      careloop_e2e.py, redteam.py
app/             Expo app (web + Android): App.tsx, src/screens/*, src/components/GenUI.tsx, src/voice/agora.{web,native}.ts
docs/spec/       Product, architecture, schema, workflow-contract and UX specifications
docs/demo/       Upload-demo lab report PDF
```

**Deliberate MVP deviations from the spec:** one synthetic patient (no login), local private file storage instead of
MinIO, one LangGraph agent loop with typed tools instead of separate subgraphs, simulated clinic / pharmacy / provider
services, in-app notifications only (no OS push yet).
