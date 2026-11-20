# Aarogya - Master Product and Engineering Specification

**Version:** 1.0.0  |  **Baseline date:** 21 November 2026  |  **Track:** Build with Agora PS11

## Document map

1. Product Requirements Document
2. System Architecture Specification
3. Database Schema Specification
4. LangGraph Workflow and Tool Contracts
5. Screen-by-Screen UX Specification

---

# Aarogya — Product Requirements Document

| Field | Value |
|---|---|
| Document ID | AAR-PRD-001 |
| Version | 1.0.0 |
| Status | Baseline for hackathon implementation; review before production use |
| Date | 21 November 2026 |
| Product | Aarogya — Your Personal AI Health Companion |
| Track | PS11 — Breaking Language Barriers Through Agentic Voice AI |
| Primary platforms | Android-first mobile; iOS-compatible; responsive web where supported |
| Initial languages | Hindi/Hinglish and English; additional Indic languages only after validation |

## 1. Executive summary

Aarogya is a patient-controlled, multilingual, voice-first health companion. It helps a person organize and understand their health records over time, manage patient-confirmed medication reminders, and coordinate healthcare activities such as finding a doctor, booking an appointment, sharing selected records with consent, and managing follow-up tasks.

Aarogya is not an autonomous doctor, diagnostic system, prescriber, or replacement for a registered medical practitioner. Its role is to retrieve, organize, explain source material in accessible language, and coordinate actions that the patient or an authorized professional has approved.

The product's differentiator is not a medical-document chatbot. It is a **longitudinal health memory connected to a multilingual voice agent and bounded action workflows**. Facts about the patient remain traceable to their source and provenance. Consequential actions require explicit authorization and are verified against the connected service.

## 2. Problem statement

People accumulate health information across diagnostic laboratories, hospitals, clinics, prescriptions, discharge summaries, paper documents, patient portals and conversations with clinicians. Information is fragmented, difficult to interpret, and often unavailable at the point of the next consultation. Patients may also forget clinician-directed follow-ups, medication schedules, or appointment actions.

Digital services may be difficult to use for people who prefer Indian languages, speak code-mixed language, or find complex forms inaccessible. The result is avoidable administrative burden and poor continuity of information between care interactions.

**Product problem:** How might a patient-controlled, multilingual assistant connect a person's health information across time and help the person understand and coordinate next steps without making clinical decisions or exceeding the patient's authorization?

## 3. Product vision and positioning

**Tagline:** Your health history. Your language. Your care, connected.

Aarogya provides four connected capabilities:

1. **Understand** — retrieve and explain health information with links to original sources.
2. **Monitor** — present longitudinal observations and patient-confirmed care tasks without inventing clinical interpretations.
3. **Coordinate** — find providers, check availability, book appointments and share selected records with consent.
4. **Communicate** — provide a natural voice-first experience in validated supported languages.

Medication management extends the care loop through verified prescription capture, patient-confirmed reminders, adherence self-reporting and bounded refill coordination.

## 4. Goals

### 4.1 Hackathon goals (MVP)

- Deliver a working real-time voice experience using the required Agora technology path and Murf Falcon TTS, subject to an early integration feasibility spike.
- Demonstrate Hindi/Hinglish and English interactions. Do not claim support for any language until the configured ASR and TTS path has passed the language test set.
- Allow a synthetic patient to upload health documents and view extracted information with provenance and validation status.
- Retrieve structured observations from PostgreSQL and narrative context from a vector store where appropriate.
- Explain a health-record question using evidence-linked, non-diagnostic language.
- Compare compatible historical observations deterministically, preserving source units, dates and reference intervals.
- Complete at least one end-to-end agentic service workflow: search a doctor, retrieve actual demo availability, request explicit approval, create a booking, verify the booking, and create a reminder or calendar event.
- Demonstrate patient-confirmed medication reminder setup from a verified synthetic prescription.
- Demonstrate approval gates, failure recovery, and visible agent execution state.
- Render context-aware UI components from validated, versioned schemas.

### 4.2 Product goals beyond the hackathon

- Support provider-connected record synchronization with appropriate identity, consent and provenance controls.
- Support pharmacy integrations through appropriately licensed partners and compliant prescription checks.
- Support broader Indian-language coverage after measurable speech and task-level evaluation.
- Support standards-aligned health-record exchange, including an appropriately scoped FHIR-compatible model.
- Support patient-authorized caregiver access and family coordination.

## 5. Non-goals and explicit boundaries

The MVP will not:

- Diagnose diseases, predict disease risk, triage autonomously, or replace clinician judgment.
- Prescribe, discontinue, renew, substitute or change medicines autonomously.
- Infer medication dose, frequency, duration or timing from incomplete or ambiguous source material.
- Independently recommend investigations or treatment.
- Provide personalized health-insurance sales recommendations using patient medical history.
- Perform real medicine sales or payment unless a suitable authorized pharmacy/payment integration is secured. The hackathon path uses clearly labelled sandbox services.
- Claim live ABDM integration or production provider connectivity when only a simulation exists.
- Store raw clinical details in prompts, logs, analytics or notifications beyond what is necessary.
- Use real patient information in the hackathon demo unless the necessary authorization, safeguards and approvals exist. Use synthetic data by default.

A future **Health Coverage Explainer** may explain an uploaded insurance policy using cited policy text. It is outside MVP scope and must not be conflated with insurance solicitation or suitability advice.

## 6. Target users and personas

### 6.1 Primary: Patient

A person who wants to keep their reports and prescriptions organized, understand what a document says, ask questions in a preferred language, and coordinate appointments and reminders.

Needs: clarity, accessible language, evidence, privacy, simple workflows and control over actions.

### 6.2 Secondary: Clinician/provider user (future portal or demo provider)

A verified doctor or clinic representative who creates consultation documents, prescriptions or follow-up instructions and shares them through an authenticated, patient-linked workflow.

Needs: accurate patient matching, clear provenance, low administrative burden and no misleading AI-generated clinical content.

### 6.3 Secondary: Authorized caregiver

A person explicitly authorized by a patient or lawful representative to receive selected reminders or coordinate selected activities.

Needs: scoped access, clear role boundaries, revocation and auditability.

### 6.4 Internal demo operator

A team member managing synthetic doctors, clinic availability, documents and sandbox pharmacy records for the hackathon demonstration.

Needs: deterministic seed data, resettable demo state and observability without access to real patient data.

## 7. Core user journeys

### Journey A — Report-to-Consultation CareLoop (primary demo)

1. Patient signs into the synthetic demo account and selects Hindi/Hinglish or English.
2. Patient uploads two synthetic reports, or opens pre-seeded reports.
3. Aarogya stores original files and displays extraction/review status.
4. The patient asks a voice question about the latest report.
5. Aarogya retrieves the correct patient's source-linked report facts and explains what the source says without diagnosing.
6. Patient requests a historical comparison.
7. Aarogya retrieves compatible observations and displays dates, values, units, source reference intervals and original document links.
8. Patient asks to find a doctor.
9. Aarogya searches the seeded provider directory and current demo availability.
10. Patient chooses a slot and reviews a typed approval card.
11. Patient explicitly approves; the system revalidates the slot, books with an idempotency key and verifies the returned booking reference.
12. Aarogya offers separately scoped consent to share selected records with the selected provider.
13. Aarogya creates a reminder and/or calendar event, then confirms only actions whose completion was verified.

### Journey B — Medication reminder setup

1. Patient opens a prescription originating from an authenticated provider or a patient-uploaded document.
2. The extraction pipeline captures medication facts and source evidence.
3. Any ambiguous or low-confidence instruction is placed into review and cannot activate a schedule.
4. Patient reviews the extracted schedule against the prescription and confirms it. This patient confirmation does not convert a patient-uploaded document into a clinician-verified record.
5. Aarogya creates a reminder schedule using an explicit timezone and dates.
6. Reminder notifications are sent by a persistent scheduler; patient-reported Taken/Skipped/Snoozed actions are recorded as self-reports.

### Journey C — Refill request (bounded/stretch)

1. Patient requests a refill by voice.
2. Aarogya retrieves the relevant verified prescription and checks documented refill eligibility.
3. The connected pharmacy/sandbox returns a quote and availability.
4. Pharmacy professional verification is required where applicable.
5. Patient reviews product, strength, formulation, quantity, pharmacy, delivery, price and terms.
6. Patient explicitly approves payment through a secure checkout; no payment credentials are handled by the LLM.
7. Order and payment status are verified from the provider response before Aarogya reports completion.

### Journey D — Provider document synchronization

1. A provider signs into an authenticated provider system.
2. The provider creates and signs a consultation document or prescription.
3. The integration verifies provider identity, patient match and applicable consent/authority.
4. The document is imported with source identity, timestamp and integrity metadata.
5. Aarogya notifies the patient and routes the document through the same ingestion pipeline as a patient upload while preserving the distinct source classification.

## 8. Functional requirements

Priority key: **P0** = required for core demo; **P1** = strong differentiator; **P2** = stretch/future.

### 8.1 Identity, patient context and preferences

- **FR-001 (P0):** The application shall authenticate the current user before retrieving or changing patient information.
- **FR-002 (P0):** The application shall resolve the patient profile from authenticated identity, not from a caller-supplied patient ID alone.
- **FR-003 (P0):** The patient shall be able to set a preferred language and timezone.
- **FR-004 (P1):** The patient shall be able to review connected providers and active sharing permissions.

### 8.2 Health documents and memory

- **FR-010 (P0):** The patient shall upload supported PDF and image documents.
- **FR-011 (P0):** The system shall preserve the original document, cryptographic hash, uploader, source type, upload timestamp and storage reference.
- **FR-012 (P0):** The system shall classify the document type and expose processing status.
- **FR-013 (P0):** The system shall extract supported observations with test name, value, unit, reference interval, observation date, source page/location and validation status.
- **FR-014 (P0):** The system shall distinguish patient-uploaded, provider-imported, AI-extracted, patient-confirmed and provider-verified information.
- **FR-015 (P0):** The system shall let the patient inspect the original source for a displayed extracted observation.
- **FR-016 (P0):** The system shall answer record questions using authorized structured queries and/or filtered semantic retrieval.
- **FR-017 (P0):** Every factual claim about a patient's stored record shall have one or more source references, or the system shall explicitly state that it cannot substantiate the claim.
- **FR-018 (P0):** The system shall compare historical measurements only when test identity and units are comparable or a validated conversion exists.
- **FR-019 (P1):** The system shall present a longitudinal health timeline of documents, encounters, observations, appointments and follow-up tasks.

### 8.3 Multilingual voice and conversational UX

- **FR-020 (P0):** The patient shall start and end a real-time voice session.
- **FR-021 (P0):** The UI shall display voice connection, listening, processing, speaking, interrupted, approval-waiting and error states.
- **FR-022 (P0):** The UI shall display partial/final transcripts where supported and allow a text fallback.
- **FR-023 (P0):** The system shall respond using the selected, validated language/voice configuration.
- **FR-024 (P0):** The assistant shall ask clarifying questions where dates, numbers, names, medication instructions or actions are ambiguous.
- **FR-025 (P1):** The session shall support barge-in/interruption and recover conversation state without duplicating actions.
- **FR-026 (P1):** The assistant shall render typed context-specific UI components from a registry; arbitrary model-generated code is prohibited.

### 8.4 Doctor discovery and appointments

- **FR-030 (P0):** The patient shall search providers by specialty and location.
- **FR-031 (P0):** The system shall retrieve availability from a connected or explicitly labelled demo service.
- **FR-032 (P0):** The patient shall review exact provider, clinic, date, time, timezone and appointment type before booking.
- **FR-033 (P0):** Booking shall require an explicit, action-bound, unexpired patient approval.
- **FR-034 (P0):** Booking shall use idempotency and revalidate slot availability immediately before execution.
- **FR-035 (P0):** The system shall verify the external booking reference/status before displaying success.
- **FR-036 (P1):** The patient shall separately authorize which documents or summary may be shared with a provider.
- **FR-037 (P1):** The system shall create a calendar event and reminder after verified booking, where configured.

### 8.5 Medication management

- **FR-040 (P1):** The system shall capture prescription-linked medication details and retain the source reference.
- **FR-041 (P1):** A schedule shall not become active until source instructions are sufficiently clear and required patient confirmation/review is complete.
- **FR-042 (P1):** Medication reminders shall use an explicit timezone, recurrence, start date and optional end date.
- **FR-043 (P1):** The patient shall be able to record Taken, Skipped or Snoozed as self-reported events.
- **FR-044 (P1):** The system shall not independently change dose, route, frequency, duration or restart a discontinued medication.
- **FR-045 (P2):** Refill quote and order flows shall require a valid prescription check, pharmacy review where applicable, patient confirmation and secure payment-provider authorization.

### 8.6 Follow-up and notifications

- **FR-050 (P1):** The system shall create follow-up tasks only from patient instructions or clinician-documented plans, with provenance.
- **FR-051 (P1):** Patient shall confirm extracted care tasks before reminders are scheduled when extraction is uncertain or the instruction is ambiguous.
- **FR-052 (P1):** Notifications shall minimize sensitive health details on lock screens.
- **FR-053 (P1):** Scheduled reminders shall persist independently of the mobile app process.

### 8.7 Consent, privacy and audit

- **FR-060 (P0):** Every patient data request shall be scoped to the authenticated user and authorized patient context.
- **FR-061 (P0):** Sharing shall identify recipient, purpose, selected records, expiry and status.
- **FR-062 (P0):** The patient shall be able to revoke future sharing permissions.
- **FR-063 (P0):** Consequential actions and access to sensitive records shall create audit events.
- **FR-064 (P0):** Revoked or expired grants shall not authorize new access.
- **FR-065 (P1):** The patient shall be able to request export/deletion subject to applicable retention and legal requirements.

## 9. Non-functional requirements

### 9.1 Reliability

- Core appointment workflow must be retry-safe.
- Booking, payment and refill operations must be idempotent.
- The system must distinguish Pending, Succeeded, Failed and Unknown external outcomes.
- A timeout must not be interpreted as proof of failure or success.
- Scheduled reminders must be persisted and recoverable after worker restarts.

### 9.2 Performance targets (prototype targets, not guarantees)

- Non-voice API reads: p95 under 800 ms on local/demo infrastructure, excluding external provider latency.
- UI response to a received agent event: under 200 ms on a representative device.
- Voice perceived response latency: measure and report p50/p95 from Bengaluru; do not claim a target until the Agora/Murf configuration has been tested.
- Document extraction: asynchronous; UI shall expose queued/processing/review/complete/failed states.

### 9.3 Security and privacy

- TLS in transit; encryption at rest for documents and databases where supported.
- Short-lived access tokens and server-side secrets.
- Patient-level authorization at every service boundary.
- Secure object storage with private buckets and signed URLs.
- No PHI in analytics events, application logs or error trackers unless strictly necessary and protected.
- Retention/deletion policy and consent records.
- Separate synthetic demo environment from any production environment.

### 9.4 Accessibility and language

- Text scaling and screen-reader labels.
- High-contrast status indicators not relying on color alone.
- Large touch targets.
- Spoken numbers, dates and medical terms tested for pronunciation.
- Language support claims must follow measured ASR/TTS task tests.

### 9.5 Observability

- Correlation ID across app request, workflow run, tool call and external transaction.
- Structured logs without unnecessary clinical payloads.
- Distributed traces for API/agent workflows.
- Metrics for voice session stability, tool success, workflow completion and error recovery.

## 10. Safety requirements and prohibited behaviors

- Aarogya may explain what a source document states, but it must not represent this as a diagnosis.
- It must not prescribe or change treatment.
- It must not infer missing medication instructions.
- It must not treat an LLM confidence score as proof of extraction correctness.
- It must not treat patient-reported adherence as verified ingestion.
- It must not share patient information without the required authority and scoped consent.
- It must not state that an appointment/order/payment succeeded until independently verified.
- It must provide a clinically reviewed escalation response for configured emergency triggers; the LLM alone is not the emergency classifier.
- Untrusted content in uploaded documents must not be treated as system instructions.
- The product must be reviewed against applicable Indian healthcare, privacy, pharmacy, payment and medical-device requirements before production deployment. This document is a product/engineering specification, not legal or clinical advice.

## 11. Success metrics

### Hackathon demonstration metrics

- End-to-end appointment completion rate on controlled test scenarios.
- Correct provider/slot selection rate.
- Duplicate booking prevention rate.
- Health-record retrieval accuracy.
- Observation extraction accuracy on clean synthetic reports.
- Evidence coverage for health-record claims.
- Hindi/Hinglish intent accuracy on a curated task set.
- Voice session connection success and p50/p95 response latency.
- Approval bypass count (target zero in test suite).
- Unsafe medication schedule creation count (target zero in test suite).

### Product metrics for later validation

- Patient task completion and time-to-completion.
- Reminder acknowledgement and self-reported adherence event rates (not clinical adherence proof).
- Follow-up task completion rate.
- Patient understanding/usability ratings.
- Record coverage and duplicate-document rate.
- Provider integration success rate.

## 12. Assumptions and dependencies

- The hackathon MVP uses synthetic patient records, providers and availability.
- A real-time Agora/Murf configuration must be proven early; platform preview, geography, ASR language support and TTS configuration can change.
- External doctor, pharmacy, payment and calendar integrations may be simulated unless authorized partner credentials are available.
- The initial supported interaction set is Hindi/Hinglish and English, subject to actual tests.
- The application starts as a modular monolith, not microservices.
- Shared Pydantic contracts are the source of truth for API schemas; TypeScript clients are generated from OpenAPI.

## 13. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Agora/Murf integration or latency issue | Critical demo failure | Phase 0 spike; fallback voice transport/ASR/TTS adapter; never defer testing |
| Incorrect medical extraction | Unsafe explanation/schedule | Source provenance, validation, review state, synthetic test suite |
| LLM invents health facts | Loss of trust | Structured retrieval, evidence-required response contract, abstain on unsupported claim |
| Duplicate booking/order | Financial/operational harm | Idempotency, external status reconciliation, approval binding |
| Cross-patient leakage | Severe privacy breach | Auth-derived patient scope, row-level checks, adversarial tests |
| Too much MVP scope | Incomplete demo | P0/P1/P2 prioritization and one signature workflow |
| Generative UI payload drift | Broken UI | Versioned discriminated unions and runtime schema validation |
| Pharmacy integration unavailable | Refill feature incomplete | Sandbox demonstration; keep refill stretch, not core dependency |

## 14. MVP acceptance criteria

The MVP is accepted when:

1. A synthetic patient can use the app in the selected validated language.
2. The patient can access two synthetic reports and source-linked extracted observations.
3. The assistant can answer a report question without presenting a diagnosis.
4. The assistant can compare compatible observations and display provenance.
5. The patient can ask by voice to find a doctor and retrieve demo availability.
6. A booking requires an explicit confirmation and is verified against the booking service.
7. The UI renders the correct typed dynamic components and activity timeline.
8. A verified synthetic prescription can create a patient-confirmed reminder schedule.
9. At least one failure or changing requirement is recovered safely.
10. The system has zero cross-patient access or approval-bypass failures in the MVP test suite.

## 15. Scope decision log

| Feature | MVP decision | Rationale |
|---|---|---|
| Longitudinal health memory | Include | Core product differentiator |
| Report intelligence | Include | Core value and demo entry point |
| Appointment workflow | Include as primary end-to-end action | Strong PS11 workflow and verifiable result |
| Medication reminders | Include as secondary workflow | Useful ongoing care feature; bounded by verified source instructions |
| Medicine refill | Stretch/sandbox | Pharmacy, prescription and payment dependencies |
| Provider auto-sync | Simulated provider integration | Demonstrates hybrid ingestion without claiming live ecosystem access |
| Manual uploads | Include | Works with non-integrated providers |
| Insurance recommendation | Exclude | Regulatory, privacy and commercial complexity |
| Insurance policy explainer | Future | Separate document-understanding feature |
| ABDM live integration | Future | Scope and onboarding exceed hackathon MVP |
| Multiple agents | Not required | Single orchestrator with subgraphs is simpler and more testable |

---

**End of PRD.** Product scope is the baseline for the architecture, database, workflow and UX specifications that follow.

---

# Aarogya — System Architecture Specification

| Field | Value |
|---|---|
| Document ID | AAR-ARCH-001 |
| Version | 1.0.0 |
| Status | Baseline architecture for hackathon MVP |
| Date | 21 November 2026 |
| Related documents | PRD, Database Schema, LangGraph Workflow Contracts, UX Specification |

## 1. Architecture objectives

The architecture must support a frontend-first delivery process, a real-time voice interaction path, a persistent patient health record, controlled agent workflows, and external actions with explicit approval and verification.

Primary architectural objectives:

1. Keep the application understandable and deliverable by a small hackathon team.
2. Use a modular monolith for the MVP; avoid premature microservices.
3. Make Pydantic contracts the canonical source for public API and event schemas.
4. Keep domain data separate from conversational memory and LangGraph internal state.
5. Make the patient identity and authorization scope server-derived.
6. Treat uploaded documents and retrieved text as untrusted data, never as system instructions.
7. Use deterministic services for numeric comparisons, permissions, payment and action state.
8. Make external operations idempotent and reconcilable after timeouts.
9. Separate audio transport from agent orchestration.
10. Support later FHIR-compatible exchange without claiming full standards conformance in the MVP.

## 2. Architecture decision summary

| ID | Decision | Rationale |
|---|---|---|
| ADR-001 | React Native + Expo + TypeScript for patient app | Shared Android/iOS codebase and web reuse where compatible |
| ADR-002 | Pydantic contracts -> FastAPI OpenAPI -> generated TypeScript client | Prevent schema drift |
| ADR-003 | Modular monolith for FastAPI | Low operational overhead; clear module boundaries |
| ADR-004 | PostgreSQL is canonical structured datastore | Transactionality, relational integrity and precise queries |
| ADR-005 | Qdrant stores embeddings for narrative retrieval | Semantic search, always filtered by authenticated patient scope |
| ADR-006 | Object storage holds original documents | Private binary storage; database stores metadata and keys |
| ADR-007 | LangGraph is the workflow orchestrator | Explicit state, checkpointing, interrupts and controlled recovery |
| ADR-008 | NeMo Guardrails is a model interaction policy layer | Defense in depth; not the authorization authority |
| ADR-009 | One primary orchestrator with bounded subgraphs | Avoid multi-agent complexity in MVP |
| ADR-010 | Agora RTC/Conversational AI plus Murf Falcon, with LangGraph as sole workflow authority | Avoid competing LLM decision loops |
| ADR-011 | SSE for agent progress events; HTTP for commands | Simple server-to-client event transport; explicit action calls |
| ADR-012 | Persistent worker for reminders and asynchronous ingestion | Tasks survive app closure and worker restart |
| ADR-013 | Typed generative UI registry | Dynamic UX without executing model-generated code |
| ADR-014 | Explicit human approval for consequential actions | Patient control and auditability |

## 3. System context and actors

### Actors

- **Patient:** uploads records, asks questions, configures reminders, chooses providers, approves actions and controls sharing.
- **Provider/doctor:** creates records through an authenticated integration or simulated provider portal.
- **Authorized caregiver:** receives only explicitly delegated access/notifications.
- **Aarogya operator:** seeds demo providers and synthetic availability; not a production clinical role.
- **External provider systems:** appointment, pharmacy, payment, calendar and notification adapters.

### System boundary

Aarogya owns patient-facing orchestration, record metadata, consent state, internal workflow state, event history and UI contracts. External services remain authoritative for their own bookings, pharmacy orders, payment states and calendar events. Aarogya must reconcile with external state before claiming completion.

## 4. Logical architecture

### 4.1 Patient experience layer

**React Native + Expo + TypeScript** with:

- Expo Router navigation.
- Design-system component library.
- TanStack Query for server state.
- Zustand for transient UI/voice state.
- React Hook Form for user inputs.
- Generated OpenAPI client and runtime Zod validation.
- Generative UI component registry.
- Agora client/SDK adapter.
- Local notification integration as a supplement to backend scheduling.

The frontend does not make clinical decisions, compute medical trends, authorize provider access, or call payment/pharmacy APIs directly.

### 4.2 API and application layer

**FastAPI modular monolith** with modules:

- Identity and patient context.
- Health documents and extraction.
- Health observations and timeline.
- Medication and adherence.
- Appointment and provider directory.
- Refill and payment orchestration (sandbox in MVP).
- Consent and sharing.
- Agent sessions and events.
- Notification and scheduled task management.
- Audit and observability.

Routes validate public contracts and delegate to application services. Domain services must not depend on HTTP request objects.

### 4.3 Agent orchestration layer

**LangGraph** owns goal routing and controlled workflow execution. It calls typed application tools. It is not the system of record for health data.

Bounded subgraphs:

- Health question and report explanation.
- Historical comparison.
- Appointment coordination.
- Medication schedule setup.
- Medication adherence capture.
- Refill request.
- Follow-up planning.
- Record sharing.

A single top-level orchestrator selects a workflow. Do not create autonomous specialist agents for each simple tool.

### 4.4 Safety layer

**NeMo Guardrails** can check model inputs, retrieved content, dialog state, tool execution requests and outputs. Deterministic backend controls independently enforce identity, patient scope, consent, approval, idempotency, clinical boundaries and payment authorization.

Guardrails may prevent or flag unsafe model behavior, but they are not trusted as the only access-control system.

### 4.5 Data layer

- PostgreSQL: canonical structured health and workflow records.
- Qdrant: embeddings for narrative document chunks, with patient and permission metadata filters.
- S3-compatible object storage: original PDF/image files and derived artifacts.
- Redis: short-lived cache and task-queue infrastructure.
- LangGraph checkpointer: thread/workflow checkpoint state, stored separately from domain records.

### 4.6 Integration layer

Adapters isolate vendor-specific APIs:

- `AgoraVoiceAdapter`
- `MurfTTSAdapter` (where configured as a separate provider integration)
- `AppointmentProviderAdapter`
- `PharmacyAdapter`
- `PaymentAdapter`
- `CalendarAdapter`
- `PushNotificationAdapter`
- `ProviderRecordImportAdapter`

Use ports/interfaces in the application core so demo adapters can be replaced with real integrations.

## 5. Voice architecture and decision boundary

### 5.1 Single decision authority

**LangGraph is the sole authority for Aarogya workflow decisions and tool execution.** Avoid a second independent LLM inside a managed voice platform making its own clinical or transactional decisions.

The intended logical flow is:

1. Mobile client establishes a voice session.
2. Agora provides RTC transport and supported conversational/ASR lifecycle services.
3. Recognized finalized utterances are routed to the Aarogya conversation/agent gateway.
4. The gateway invokes LangGraph with authenticated session and patient context.
5. LangGraph retrieves facts or invokes typed tools.
6. The backend emits structured response and UI events.
7. TTS renders approved response content using the configured Murf Falcon integration.
8. Audio returns through the supported Agora voice path.

**Integration spike requirement:** The exact Agora Conversational AI custom-LLM/tool bridge and Murf Falcon configuration must be validated against the vendor's current SDK/API. If the managed conversation path cannot delegate deterministically to the external LangGraph orchestrator, use Agora RTC with a custom voice gateway/ASR/TTS composition rather than allowing two LLMs to compete. The product contract does not depend on a particular provider adapter.

### 5.2 Voice channels

- Audio: Agora RTC session.
- Transcript/agent response: event stream associated with `conversation_id`.
- Agent progress: SSE or a supported realtime data channel.
- User approvals: authenticated HTTP command, not an untrusted transcript event.
- Session lifecycle: backend-managed session IDs and scoped short-lived client credentials.

### 5.3 Voice state

Client voice state and backend workflow state are related but distinct. A client may be `SPEAKING` while a workflow is `AWAITING_APPROVAL`. Model them separately.

## 6. Shared contract architecture

### 6.1 Source of truth

Canonical public schemas live in the Python package `aarogya_contracts` using Pydantic v2.

Pipeline:

1. Pydantic models define API request/response, agent event and generative UI payload contracts.
2. FastAPI exports OpenAPI JSON.
3. Orval generates TypeScript types/client/hooks and Zod validators (configuration-dependent).
4. Frontend imports generated types; it does not hand-maintain API duplicates.
5. Contract tests validate fixtures and API responses.
6. CI regenerates the client and fails if generated artifacts differ.

Database ORM entities and LangGraph state are internal models and must not leak directly into public response types.

### 6.2 Versioning

- REST API prefix: `/api/v1`.
- Event schema: `schema_version` field and stable event discriminators.
- Generative UI schema: component name plus component version.
- Breaking change: new API/event/component major version or coordinated migration.
- Optional additive fields: allowed only with documented backwards-compatible behavior.

### 6.3 Standard response envelope

Success responses may be direct typed resource representations or a documented envelope. Pick one convention in implementation and apply it consistently. Errors use a stable shape:

```json
{
  "code": "APPOINTMENT_SLOT_UNAVAILABLE",
  "message": "The selected slot is no longer available.",
  "retryable": true,
  "request_id": "req_demo_001",
  "details": {}
}
```

Do not expose stack traces or sensitive upstream payloads.

## 7. Data flows

### 7.1 Document ingestion

1. Client requests an upload URL.
2. Backend authenticates patient and allocates a document record.
3. Client uploads to private object storage using short-lived signed URL.
4. Client notifies completion; backend verifies object metadata and hash.
5. Worker classifies and extracts text.
6. Structured extraction service emits typed facts with page/source evidence and confidence signal.
7. Validation determines whether facts are auto-accepted for display, need user review, or require provider confirmation. Medication instructions are never activated from uncertain extraction.
8. Structured observations are persisted in PostgreSQL.
9. Narrative chunks are embedded and indexed in Qdrant with patient filters.
10. UI receives processing status events.

### 7.2 Health question

1. Authenticated patient sends finalized utterance.
2. Intent router identifies a record question.
3. Query planner selects structured SQL, Qdrant or hybrid retrieval.
4. Retrieval layer applies patient and consent filters before data reaches the model.
5. Evidence builder creates source-linked context.
6. Model produces a constrained, non-diagnostic explanation.
7. Output policy checks response and evidence references.
8. UI renders text and typed evidence/observation cards.

### 7.3 Appointment booking

1. Search providers and retrieve live demo/provider slots.
2. Present exact choice to patient.
3. Create `ApprovalRequest` bound to action, slot, provider, patient, price if applicable, expiry and payload hash.
4. Patient confirms through authenticated action endpoint.
5. Backend revalidates patient, approval, slot and idempotency key.
6. Provider adapter creates booking.
7. Backend queries provider or validates authoritative response.
8. Persist booking reference/status and audit event.
9. Create calendar event/reminder through outbox-driven worker.
10. Report success only after verification; otherwise show Pending/Unknown and reconcile.

### 7.4 Medication reminder

1. Retrieve prescription and medication record.
2. Confirm source and extraction review state.
3. Present the extracted instructions to patient for confirmation where appropriate.
4. Create schedule with timezone, effective dates and explicit recurrence.
5. Worker produces due reminder occurrences.
6. Push/local notification is dispatched.
7. Patient may record a self-reported Taken, Skipped or Snoozed event.
8. No inference of actual ingestion is made.

## 8. Deployment topology for hackathon MVP

Use Docker Compose:

- `patient-app` (Expo dev server, local development; web build optional)
- `api` (FastAPI)
- `worker` (document and notification tasks)
- `postgres`
- `qdrant`
- `redis`
- `minio`
- optional `langfuse` or remote tracing endpoint

External Agora/Murf/LLM services remain vendor endpoints. For mobile testing, expose the API through a secure reachable development URL. Do not assume `localhost` on a physical phone maps to the development machine.

## 9. Reliability patterns

### 9.1 Idempotency

All side-effecting commands accept an idempotency key or use a server-generated unique operation ID. Unique constraints prevent duplicate booking/order/payment creation.

### 9.2 Transactional outbox

When a database transaction commits an appointment or reminder, write an outbox event in the same transaction. A worker publishes it to notifications/calendar adapters. This avoids losing the follow-up if the process crashes between DB commit and message publish.

### 9.3 External timeout and unknown outcome

Represent `UNKNOWN` separately from `FAILED`. On timeout after a side effect, reconcile using provider reference/idempotency key before retrying.

### 9.4 Retries

Retry only transient failures and only where the operation is idempotent. Do not retry payment or booking blindly.

### 9.5 Scheduling

PostgreSQL stores authoritative schedules; a persistent scheduler/worker creates occurrences. Redis may support queue delivery but must not be the only persistence for a future reminder.

## 10. Security and trust boundaries

- Authenticate every request.
- Derive patient identity from auth context; never trust client-supplied patient ownership fields.
- Authorize every document, observation, vector retrieval, action and sharing request.
- Keep document buckets private.
- Use short-lived signed URLs.
- Store provider/API/payment secrets only on server-side secret storage.
- Validate webhook signatures and idempotency.
- Treat uploaded documents, OCR text, tool results and user transcript as untrusted inputs.
- Use separate permissions for viewing a record, sharing it with a provider and using it in an agent workflow.
- Minimize PII in observability systems.
- Make demo data synthetic and isolate demo credentials from production credentials.

## 11. Privacy and clinical safety controls

This is an engineering specification, not a legal or clinical compliance determination. Before production, obtain qualified review of applicable Indian privacy, healthcare, telemedicine, pharmacy, payments and medical software obligations.

Aarogya shall:

- Explain source content without claiming a diagnosis.
- Abstain when source support is missing or ambiguous.
- Not prescribe or change medication.
- Not convert uncertain extraction into a medication schedule.
- Use clinically reviewed emergency escalation rules; LLM judgment alone is not sufficient.
- Keep clinician-authored and patient-reported data distinct.
- Preserve source values and units alongside any normalized representation.
- Avoid presenting a numeric change as clinical significance without validated criteria and appropriate clinical oversight.

## 12. Observability

Trace IDs should link:

`mobile_action -> API_request -> workflow_run -> graph_node -> tool_call -> provider_transaction -> UI_event`.

Capture:

- Voice connection success and disconnect reason.
- ASR finalization and correction events where available.
- Time to first response audio.
- LLM and retrieval latency.
- Tool success/failure/unknown status.
- Approval completion/expiry.
- Booking/payment reconciliation result.
- Document extraction failure and review rate.

Do not log raw reports, full medical histories or complete transcripts by default.

## 13. Architecture decision records required

- ADR-001: React Native + Expo platform strategy.
- ADR-002: Pydantic/OpenAPI/Orval contract pipeline.
- ADR-003: Modular monolith and module boundaries.
- ADR-004: PostgreSQL + Qdrant hybrid memory.
- ADR-005: Original document storage and provenance model.
- ADR-006: LangGraph as sole workflow authority.
- ADR-007: Agora/Murf integration mode and fallback.
- ADR-008: SSE/event transport and agent UI events.
- ADR-009: NeMo Guardrails and deterministic enforcement boundary.
- ADR-010: Human approval and idempotency model.
- ADR-011: Persistent reminder scheduler and transactional outbox.
- ADR-012: FHIR-aligned internal representation; no implied live ABDM integration.

## 14. Architecture acceptance criteria

1. Frontend and backend share generated types from a canonical Pydantic contract package.
2. Backend routes do not expose ORM or LangGraph state directly.
3. No health data query can execute without authenticated patient scope.
4. Qdrant results are filtered by patient and permissions.
5. Every side-effecting action has idempotency and explicit lifecycle state.
6. Appointment success is based on provider verification.
7. Medication schedules require adequate source verification and user confirmation.
8. Voice sessions cannot bypass the same agent approval/tool policy used by non-voice requests.
9. A timeout does not trigger blind side-effect retries.
10. All critical workflow steps are observable without unnecessarily logging PHI.

---

**End of Architecture Specification.**

---

# Aarogya — Database Schema Specification

| Field | Value |
|---|---|
| Document ID | AAR-DATA-001 |
| Version | 1.0.0 |
| Status | Logical schema baseline; SQL is an MVP starting migration, not production-certified |
| Date | 21 November 2026 |
| Primary database | PostgreSQL |
| Secondary index | Qdrant for narrative embeddings |
| Binary storage | Private S3-compatible object storage |

## 1. Data architecture principles

1. PostgreSQL is the authoritative source for structured patient facts and workflow state.
2. Qdrant stores embeddings and retrieval metadata for narrative content; it is not the source of truth and not the authorization boundary.
3. Object storage contains original PDF/image documents and derived binary artifacts. PostgreSQL stores metadata and private storage keys.
4. All patient-associated domain records have an explicit `patient_id` foreign key.
5. Patient ownership is derived from authenticated server context, never trusted from an arbitrary request body.
6. Clinical facts preserve source document, source location, author/source type, observed date, original value and unit, verification status and extraction provenance.
7. Patient-reported information, provider-authored records, patient-uploaded documents and AI-extracted data remain distinguishable.
8. Medication schedule state is separate from the prescription record and adherence events.
9. A booking/order/payment has an explicit lifecycle and idempotency key.
10. LangGraph checkpoints are separate from domain entities; graph state should store IDs/references rather than duplicate the full health record.
11. Soft deletion or retention behavior must follow a documented policy; do not silently cascade-delete audit/provenance records.
12. The schema is FHIR-aligned in concepts, but it does not claim full FHIR R4 conformance or ABDM integration.

## 2. Entity groups

| Domain | Tables | Purpose |
|---|---|---|
| Identity | `app_users`, `patient_profiles`, `patient_devices` | Account, patient settings, notification devices |
| Provider directory | `clinics`, `providers`, `provider_locations`, `provider_patient_links` | Doctor/clinic identity and authorized relationships |
| Documents | `health_documents`, `document_extractions` | Original records and extraction runs |
| Health memory | `health_observations`, `encounters`, `condition_records`, `allergy_records`, `care_plans`, `follow_up_tasks` | Structured longitudinal patient record |
| Medication | `medication_records`, `medication_schedules`, `reminder_occurrences`, `adherence_events` | Prescriptions, schedules and patient-reported adherence |
| Care coordination | `provider_slots`, `appointments` | Availability and appointments |
| Pharmacy | `pharmacy_partners`, `refill_requests`, `pharmacy_quotes`, `refill_orders`, `payment_attempts` | Refill workflow and payment references |
| Consent | `consent_grants`, `record_share_events` | Scoped authorization and sharing audit |
| Agent | `agent_threads`, `workflow_runs`, `approval_requests` | Conversation and workflow execution metadata |
| Operations | `notifications`, `audit_events`, `outbox_events` | Reminders, audit and reliable async delivery |

## 3. Important lifecycle models

### 3.1 Document lifecycle

`UPLOADED -> QUEUED -> PROCESSING -> NEEDS_REVIEW -> READY`

Alternative terminal states: `FAILED`, `QUARANTINED`, `ARCHIVED`.

A provider-imported document is not automatically clinically verified merely because the transport succeeded. Source authenticity and extraction correctness are separate properties.

### 3.2 Extraction lifecycle

`PENDING -> RUNNING -> EXTRACTED -> VALIDATION_REQUIRED -> ACCEPTED`

Alternative states: `REJECTED`, `FAILED`.

### 3.3 Medication lifecycle

Prescription record: `DRAFT`, `ACTIVE`, `COMPLETED`, `DISCONTINUED`, `SUPERSEDED`, `REVIEW_REQUIRED`.

Schedule: `DRAFT`, `PENDING_CONFIRMATION`, `ACTIVE`, `PAUSED`, `COMPLETED`, `CANCELLED`.

Adherence: `TAKEN_REPORTED`, `SKIPPED_REPORTED`, `SNOOZED`, `NOT_REPORTED`, `CANCELLED`. These states describe patient interaction, not biometric proof of ingestion.

### 3.4 Appointment lifecycle

`REQUESTED`, `PENDING_APPROVAL`, `BOOKING`, `CONFIRMED`, `CANCEL_PENDING`, `CANCELLED`, `FAILED`, `UNKNOWN`, `COMPLETED`, `NO_SHOW`.

`UNKNOWN` is essential when an upstream timeout occurs after the provider may have accepted the booking.

### 3.5 Refill/order/payment lifecycle

Refill: `DRAFT`, `ELIGIBILITY_CHECK`, `PHARMACY_REVIEW`, `QUOTE_READY`, `PENDING_PATIENT_APPROVAL`, `ORDERING`, `ORDERED`, `REJECTED`, `FAILED`, `UNKNOWN`, `CANCELLED`.

Payment: `CREATED`, `PENDING`, `AUTHORIZED`, `CAPTURED`, `FAILED`, `CANCELLED`, `REFUNDED`, `UNKNOWN`.

## 4. Relationship summary

- One `app_user` may own one patient profile in MVP; schema allows account-to-profile to evolve later.
- A patient has many documents, observations, encounters, medication records, appointments, care plans, reminders and audit records.
- A document has many extraction runs and may yield many observations.
- An observation belongs to a patient and normally references its source document and extraction.
- A medication record may originate from a document and/or encounter; it may have one or more schedules.
- A schedule creates reminder occurrences; an occurrence may have one or more adherence events to preserve corrections/history.
- An appointment references a provider and clinic and may map to an external provider booking ID.
- A refill request references a medication record and may receive multiple pharmacy quotes; one accepted quote can create an order and payment attempt(s).
- A consent grant can authorize a defined purpose, recipient and set of records; record-share events record each actual share.
- Agent threads and workflow runs reference patient context but do not own clinical facts.
- Approvals are bound to one exact action payload and expiry.

## 5. Indexing and integrity requirements

- Index every patient foreign key used in authorization-filtered queries.
- Composite indexes for `(patient_id, observed_at)` and `(patient_id, created_at)` timeline queries.
- Unique constraint on `(provider_id, external_booking_id)` where external IDs exist.
- Unique constraint on idempotency keys per operation domain.
- Unique reminder occurrence per `(schedule_id, scheduled_at)`.
- Store all event instants as `TIMESTAMPTZ`; store patient timezone as IANA timezone string.
- Store value and unit as separate fields; retain original units even if a normalized value is calculated.
- Use `NUMERIC` for clinical values and money, not binary floating point.
- Keep original extraction JSON in a versioned record with limited access and retention.
- Qdrant payload filters must include `patient_id`, document status and permission scope; application authorization must still run before query.

## 6. SQL migration

The accompanying `../database/001_initial_schema.sql` defines the MVP tables and baseline constraints. `../database/002_patient_scope_constraints.sql` adds composite foreign keys that prevent linking a resource from one patient to a row owned by another patient. Apply migration 002 after 001. Both migrations must be reviewed, tested, and adapted to the chosen authentication, ORM, retention, deployment and multi-tenancy requirements before production.

## 7. Qdrant collection design

Suggested collection: `aarogya_health_chunks_v1`.

Payload fields:

```json
{
  "patient_id": "uuid",
  "document_id": "uuid",
  "extraction_id": "uuid",
  "document_type": "LAB_REPORT",
  "source_kind": "PATIENT_UPLOAD",
  "page_number": 2,
  "encounter_id": null,
  "created_at": "2026-11-21T12:00:00Z",
  "record_visibility": "PATIENT_ONLY",
  "chunk_version": 1
}
```

Mandatory query filter: authenticated `patient_id` plus any applicable permission/status constraints. Never trust a patient ID supplied by model-generated query arguments.

Chunk content should not include unnecessary identity information. Store the original document as the source and preserve page/section references.

## 8. Retention and deletion

Define retention rules before production. A patient deletion request may require legal/clinical retention exceptions. The MVP should support soft-deactivation and a deletion request workflow, but must not claim that all records are immediately erasable regardless of applicable obligations.

Deletion must propagate across PostgreSQL, Qdrant, object storage, cached representations and any derived files according to the approved policy. Audit entries should record the deletion action without retaining unnecessary clinical content.

## 9. Security requirements

- Enable database TLS in deployed environments.
- Use separate database roles for API, worker, migrations and read-only analytics.
- Apply patient-scoped authorization in application queries.
- Consider PostgreSQL Row-Level Security as defense in depth after connection-pool context propagation is tested.
- Never use a client-provided patient UUID as authorization.
- Never expose object-storage bucket paths; use short-lived signed URLs.
- Encrypt backups and restrict backup access.
- Keep secrets outside source control.
- Ensure Qdrant is not directly reachable from the public client.

---

**End of Database Specification.**

---

# Aarogya — LangGraph Workflow and Tool Contracts

| Field | Value |
|---|---|
| Document ID | AAR-AGENT-001 |
| Version | 1.0.0 |
| Status | Workflow baseline for implementation |
| Date | 21 November 2026 |
| Orchestrator | LangGraph |
| Policy layer | NVIDIA NeMo Guardrails plus deterministic backend policy checks |

## 1. Design intent

LangGraph coordinates bounded workflows. It does not own the canonical patient record, authorize access on its own, or directly connect to arbitrary third-party APIs. It invokes typed application tools exposed by FastAPI/application services.

**Single workflow authority:** one top-level Aarogya orchestrator chooses and runs a bounded subgraph. Avoid independent agents competing to make decisions.

**Domain truth:** PostgreSQL and authorized external services are authoritative for their respective records and transaction outcomes.

**Evidence:** each health-record claim must carry source references. If evidence is unavailable or ambiguous, the graph must ask, qualify or abstain.

**Agency:** every side effect is typed, scoped, idempotent where appropriate, auditable and approval-gated according to policy.

## 2. Runtime boundaries

- Voice platform: audio session, supported speech processing, transcript events, speech output.
- Conversation gateway: authenticated mapping from voice session to `conversation_id`, user, patient and language.
- LangGraph: intent routing, retrieval planning, workflow state, tool sequencing, interrupts and response composition.
- Application tools: deterministic domain services with typed inputs/outputs.
- NeMo Guardrails: model interaction checks; cannot replace service authorization.
- PostgreSQL: patient facts, workflow IDs, approvals, schedules and audit.
- LangGraph checkpointer: thread-level checkpoint state and recovery.
- External providers: authoritative booking, order, payment and calendar outcomes.

The graph state should store IDs, references and minimal transient information. Do not persist entire medical documents or unnecessary raw PHI in checkpoint state.

## 3. Shared graph state contract

The implementation may use `TypedDict` or Pydantic state, but fields and semantics must match this contract.

```python
class AarogyaState(TypedDict, total=False):
    schema_version: str
    conversation_id: str
    thread_id: str
    workflow_run_id: str
    correlation_id: str

    authenticated_user_id: str
    patient_id: str                 # derived by backend, never from model args
    preferred_language: str
    timezone: str

    user_utterance_ref: str          # reference; avoid storing raw transcript in checkpoint
    intent: str
    intent_confidence: float | None
    intent_parameters: dict
    clarification_required: bool
    clarification_question: str | None

    evidence_refs: list[dict]        # document/observation IDs + source locators
    structured_result_ref: str | None
    response_text: str | None
    response_language: str | None
    ui_components: list[dict]

    proposed_action: dict | None
    approval_request_id: str | None
    approval_state: str | None

    tool_results: list[dict]
    safety_decisions: list[dict]
    workflow_status: str
    error_code: str | None
```

### State invariants

1. `authenticated_user_id` and `patient_id` are injected by the trusted session gateway.
2. Model-generated tool arguments cannot override patient identity.
3. Every `evidence_ref` points to a source visible to the authenticated patient.
4. `proposed_action` is a preview, not an executed action.
5. `approval_request_id` identifies a server-side, payload-bound approval.
6. A `SUCCEEDED` workflow requires verified results for all mandatory side effects.
7. `UNKNOWN` is distinct from `FAILED` when upstream outcome reconciliation is required.
8. Raw transcripts and health content follow explicit retention rules; checkpoint retention is minimized.

## 4. Top-level graph

```text
START
  -> resolve_session_context
  -> normalize_utterance
  -> classify_intent
  -> validate_scope_and_safety
  -> route_intent
       |-> health_question_subgraph
       |-> report_comparison_subgraph
       |-> appointment_subgraph
       |-> medication_schedule_subgraph
       |-> adherence_capture_subgraph
       |-> refill_subgraph
       |-> follow_up_subgraph
       |-> record_sharing_subgraph
       |-> clarification_response
  -> compose_response_and_ui
  -> output_policy_check
  -> emit_agent_events
  -> END
```

Unknown, unsupported or safety-sensitive requests route to clarification, safe informational response or reviewed escalation. The graph must not route a medical request into a transactional tool merely because the utterance contains a medicine or doctor name.

## 5. Workflow contracts

### 5.1 Health question / report explanation

**Trigger:** Patient asks what a stored report or record says.

**Nodes:**

1. `resolve_health_question` — classify the requested fact and date.
2. `plan_retrieval` — choose structured SQL, semantic retrieval or hybrid path.
3. `retrieve_authorized_evidence` — retrieve within authenticated patient scope.
4. `build_evidence_packet` — attach document ID, page/section, observed date and exact stored values.
5. `draft_explanation` — explain source material in selected language; no diagnosis.
6. `validate_claim_support` — reject unsupported patient-specific claims.
7. `render_health_ui` — generate `health_summary`, `lab_observation` or `document_viewer` payload.
8. `emit_response`.

**Tool calls:**

- `get_patient_profile`
- `search_health_records`
- `get_lab_observations`
- `get_encounter_summary`

**Output contract:** `response_text`, `evidence_refs[]`, optional typed UI component(s), `workflow_status=SUCCEEDED` only if retrieval/response generation completed. If there are no matching records, state that no source was found.

**Forbidden:** diagnose, predict disease, claim a normal result means the patient is healthy, infer missing record content.

### 5.2 Historical report comparison

**Trigger:** Patient requests comparison over time.

**Nodes:**

1. `resolve_comparison_request` — identify analyte/test and time range.
2. `retrieve_observations` — query PostgreSQL by patient and test identity.
3. `validate_comparability` — verify identity, unit compatibility, specimen/method metadata where available and reference range provenance.
4. `normalize_units_if_supported` — use versioned deterministic conversion rules only where valid.
5. `calculate_comparison` — deterministic difference/percent calculation, no clinical interpretation.
6. `build_comparison_evidence` — source references for each point.
7. `draft_plain_language_explanation` — explain numeric comparison and limitations.
8. `render_comparison_chart`.

**Tool calls:** `get_lab_observations`, `compare_lab_observations`.

**Output contract:** ordered observations, units, dates, each lab reference interval, comparable flag, calculation method/version, evidence refs and a chart payload.

**Forbidden:** compare unlike tests as if equivalent; hide differing reference intervals; call a numeric shift clinically significant without a validated clinical rule and clinician oversight.

### 5.3 Report-to-Consultation appointment workflow (primary demo)

**Trigger:** Patient asks to find/book a consultation.

**Nodes:**

1. `extract_appointment_constraints` — specialty, location, date/time window, mode and preferences.
2. `clarify_missing_constraints` — ask for required missing information.
3. `retrieve_relevant_health_context` — prepare a concise optional summary; do not assume it will be shared.
4. `search_doctors` — retrieve provider records.
5. `check_appointment_slots` — retrieve current availability.
6. `rank_options` — deterministic filtering/sorting by explicit criteria; do not fabricate availability.
7. `render_doctor_and_slot_cards` — show source and freshness timestamp.
8. `create_booking_proposal` — exact provider, clinic, slot, mode, cost if available.
9. `request_booking_approval` — create server-side approval bound to payload hash and expiry; interrupt graph.
10. `resume_after_approval` — verify approver, exact approval ID, expiry and payload hash.
11. `revalidate_slot` — check that the slot remains available.
12. `book_appointment` — idempotent provider call.
13. `verify_booking` — verify external booking ID/status.
14. `create_calendar_event` — if configured; separate idempotency key.
15. `schedule_reminder` — persist reminder.
16. `offer_record_sharing` — separate consent workflow, never bundled into booking approval.
17. `emit_confirmation`.

**Tools:** `search_doctors`, `check_appointment_slots`, `create_approval_request`, `validate_approval`, `book_appointment`, `get_booking_status`, `create_calendar_event`, `schedule_follow_up`.

**Critical invariants:**

- Approval binds to exact patient, doctor, clinic, slot, mode, price/fees if shown and action payload hash.
- The exact slot is revalidated after approval and before booking.
- A timeout after booking enters `UNKNOWN` and triggers reconciliation; it does not trigger a blind retry.
- Booking confirmation is not considered record-sharing consent.
- Calendar failure does not undo an already confirmed provider booking; report partial completion honestly and retry calendar separately.

### 5.4 Medication schedule setup

**Trigger:** Patient asks to create a reminder from a prescription.

**Nodes:**

1. `resolve_medication_reference` — identify the medicine and source prescription.
2. `retrieve_prescription_facts` — structured medication record and source document.
3. `validate_prescription_provenance` — inspect source and verification status.
4. `validate_instruction_completeness` — require medicine, dose/instruction, route if present, frequency/timing, effective dates/duration as needed; ambiguous facts cannot be inferred.
5. `present_schedule_preview` — show exact extracted instructions and source.
6. `request_patient_confirmation` — confirm that the schedule represents the source instructions; unclear clinical instructions go to clinician/pharmacist, not LLM guessing.
7. `create_medication_schedule` — persist timezone and recurrence.
8. `schedule_reminder_occurrences` — persistent worker/outbox.
9. `emit_schedule_confirmation`.

**Tools:** `get_medication_record`, `get_prescription_source`, `create_medication_schedule`, `schedule_reminder`.

**Forbidden:** choose a dose/time not in the source or explicitly configured by the patient in a non-clinical reminder context; change treatment; infer an instruction from a medicine name alone.

### 5.5 Medication adherence capture

**Trigger:** Patient responds to reminder or opens a schedule.

**Nodes:** `resolve_due_occurrence -> capture_patient_report -> persist_adherence_event -> update_ui`.

**Tools:** `get_due_reminder`, `record_adherence_event`, `snooze_reminder`.

**Output:** status is explicitly labelled patient-reported. Never state that ingestion has been verified.

### 5.6 Medication refill workflow (stretch)

**Trigger:** Patient requests a refill.

**Nodes:**

1. `resolve_medication`.
2. `retrieve_source_prescription`.
3. `check_refill_eligibility` — deterministic policy/partner response.
4. `search_pharmacy_inventory`.
5. `request_pharmacy_quote`.
6. `pharmacy_review_if_required` — external professional decision.
7. `render_refill_quote`.
8. `request_patient_order_approval` — binds product/strength/form/quantity/pharmacy/price/delivery/quote expiry.
9. `validate_patient_approval`.
10. `create_payment_session` — payment provider hosted/secure flow; LLM never receives credentials.
11. `verify_payment`.
12. `place_pharmacy_order` — idempotent.
13. `verify_order`.
14. `emit_order_status`.

**Tools:** `get_medication_record`, `check_refill_eligibility`, `get_pharmacy_quote`, `request_pharmacist_review`, `create_refill_approval`, `create_payment_session`, `get_payment_status`, `place_pharmacy_order`, `get_pharmacy_order_status`.

**Invariants:** Pharmacy and applicable prescription requirements are checked by the authorized pharmacy workflow; payment requires explicit approval; no substitutions; no medicine is reported as ordered until provider order verification; sandbox state must be labelled sandbox.

### 5.7 Follow-up task workflow

**Trigger:** A clinician-authored care plan contains a follow-up instruction, or the patient explicitly requests a personal reminder.

**Nodes:** `retrieve_source_plan -> extract_task_candidates -> validate_source_and_due_date -> patient_review_if_ambiguous -> create_follow_up_task -> schedule_notification -> emit_confirmation`.

Do not invent a date or investigation interval. Preserve exact source instruction and author. A patient-created general reminder must be labelled patient-requested, not clinician-prescribed.

### 5.8 Record-sharing workflow

**Trigger:** Patient elects to share selected documents with a provider/caregiver.

**Nodes:** `resolve_recipient -> select_records -> build_scope_preview -> explain_purpose_and_expiry -> request_explicit_consent -> persist_consent_grant -> execute_share -> verify_receipt -> audit_share`.

Consent is scoped by recipient, purpose, selected records, validity interval and status. Revocation blocks future access; already disclosed copies may require separate recipient/deletion handling and must not be misrepresented as retroactively erased.

## 6. Tool contracts

All tools use JSON-serializable typed inputs and outputs. The authenticated patient/user context is injected by the application service; do not expose `patient_id` as an LLM-controllable argument unless it is ignored and overwritten server-side.

| Tool | Input (conceptual) | Output (conceptual) | Side effect | Approval |
|---|---|---|---|---|
| `get_patient_profile` | `include_preferences` | profile ref, preferred language, timezone | No | No |
| `search_health_records` | query, date range, types | document refs + source locators | No | No |
| `get_lab_observations` | analyte IDs, date range | observations with units/provenance | No | No |
| `compare_lab_observations` | observation IDs | deterministic comparison result | No | No |
| `get_care_plan` | care-plan ref or date range | source-linked plan | No | No |
| `search_doctors` | specialty, locality, mode | provider cards | No | No |
| `check_appointment_slots` | provider IDs, time window | slots + freshness/expiry | No | No |
| `create_approval_request` | action + exact payload | approval ID, expiry, payload hash | Creates pending approval | N/A |
| `validate_approval` | approval ID, decision token | verified decision | No | N/A |
| `book_appointment` | approval ref, slot ID, idempotency key | booking status/reference | Yes | Required |
| `get_booking_status` | booking ref | authoritative status | No | No |
| `create_calendar_event` | appointment ref, idempotency key | event ref/status | Yes | Product policy after booking approval |
| `create_medication_schedule` | medication ref, schedule preview, confirmation | schedule ref/status | Yes | Patient confirmation |
| `record_adherence_event` | occurrence ref, self-reported state | event ref | Yes | User action itself |
| `check_refill_eligibility` | medication ref | eligible/review/not eligible/unknown | No | No |
| `get_pharmacy_quote` | medication ref, pharmacy scope | quote details and expiry | No | No |
| `create_payment_session` | approved quote ref | hosted checkout URL/session | Yes | Required |
| `place_pharmacy_order` | verified payment + approved quote | order reference/status | Yes | Patient and pharmacy gates |
| `share_health_records` | consent ref, selected record refs | share status/reference | Yes | Required |
| `schedule_follow_up` | source task ref, due date, timezone | task/reminder refs | Yes | Required when ambiguous or product policy demands |

### Common tool result envelope

```json
{
  "tool_call_id": "tool_demo_001",
  "status": "SUCCEEDED",
  "result": {},
  "source_refs": [],
  "idempotency_key": "idem_demo_001",
  "retryable": false,
  "error_code": null,
  "completed_at": "2026-11-21T10:00:00+05:30"
}
```

Allowed status values: `SUCCEEDED`, `FAILED`, `UNKNOWN`, `REQUIRES_APPROVAL`, `REJECTED`. A tool must not represent a timeout as a confirmed failure if the external outcome may have occurred.

## 7. Approval contract

An approval request must include:

- `approval_id`
- `patient_id` (server-side binding)
- `requesting_user_id`
- `action_type`
- human-readable action summary
- exact canonical action payload
- payload hash
- creation and expiry timestamp
- allowed approver identity/role
- one-time decision state
- idempotency key

Approval endpoint:

`POST /api/v1/agent/actions/{approval_id}/decision`

Request:

```json
{
  "decision": "APPROVE",
  "expected_payload_hash": "sha256:..."
}
```

The server validates that the approver is authorized, the request is pending and unexpired, the hash matches the displayed action, and the action has not already executed. The client does not submit arbitrary action arguments when approving; it approves the stored, exact proposal.

## 8. Agent event contract

All events include:

- `schema_version`
- `event_id`
- `conversation_id`
- `workflow_run_id` (nullable for transcript-only events)
- `sequence` (monotonic within a conversation stream)
- `occurred_at`
- `type`
- `payload`

Event types:

- `agent.session.started`
- `agent.status.changed`
- `conversation.transcript.partial`
- `conversation.transcript.final`
- `assistant.message.started`
- `assistant.message.delta`
- `assistant.message.completed`
- `ui.component.render`
- `ui.component.update`
- `tool.execution.started`
- `tool.execution.completed`
- `tool.execution.failed`
- `approval.required`
- `approval.completed`
- `approval.rejected`
- `approval.expired`
- `workflow.completed`
- `workflow.failed`
- `safety.notice`

Events must not contain secret tokens, payment credentials or unnecessary raw clinical documents. Use resource references and fetch authorized data separately.

## 9. Error taxonomy

| Code | Meaning | Recovery |
|---|---|---|
| `AUTH_REQUIRED` | No valid authenticated context | Re-authenticate |
| `PATIENT_SCOPE_DENIED` | Patient access not authorized | Deny, audit |
| `CONSENT_REQUIRED` | Required sharing consent absent | Ask for scoped consent |
| `SOURCE_NOT_FOUND` | No matching record | Clarify/abstain |
| `EXTRACTION_REVIEW_REQUIRED` | Data uncertain | Ask for review; no medication schedule |
| `NOT_COMPARABLE` | Measurements cannot be validly compared | Explain limitation |
| `APPROVAL_REQUIRED` | Side effect not yet approved | Create approval request |
| `APPROVAL_EXPIRED` | Approval expired | Create new proposal |
| `SLOT_UNAVAILABLE` | Slot no longer open | Search alternatives |
| `EXTERNAL_TIMEOUT_UNKNOWN` | External result unknown | Reconcile before retry |
| `PROVIDER_REJECTED` | Provider rejected action | Explain and provide next step |
| `DUPLICATE_ACTION` | Idempotency conflict | Return original operation status |
| `POLICY_BLOCKED` | Safety/policy restriction | Safe response or professional referral |
| `VOICE_SESSION_FAILED` | Audio/session failure | Reconnect or text fallback |

## 10. LangGraph persistence and recovery

- Use a stable thread ID bound to authenticated user/patient context.
- Use a production-capable checkpointer for recoverable graph execution; an in-memory saver is acceptable only in local development.
- Store domain records in PostgreSQL, never only in graph state.
- Persist before and after side-effecting nodes.
- Use graph interrupts for explicit approval; never rely on conversational memory alone to remember that the patient approved.
- On resume, revalidate current patient, approval, expiry, payload hash and external state.
- Use reconciliation nodes for `UNKNOWN` external outcomes.
- Expire inactive sessions and remove transient state according to retention requirements.

## 11. Testing contracts

For each workflow, test:

1. Happy path.
2. Missing required input.
3. Ambiguous language/time/number.
4. Unauthorized patient scope.
5. Malicious instructions inside uploaded document.
6. Tool returns empty result.
7. Tool timeout before action.
8. Tool timeout after action may have succeeded.
9. Duplicate event delivery.
10. User declines approval.
11. Approval expires.
12. User changes a parameter after approval (must invalidate prior approval).
13. Revoked consent.
14. Language switch during conversation.
15. Voice session disconnect and resume.

---

**End of LangGraph Workflow Contracts.**

---

# Aarogya — Screen-by-Screen UX Specification

| Field | Value |
|---|---|
| Document ID | AAR-UX-001 |
| Version | 1.0.0 |
| Status | Interaction and visual baseline for frontend implementation |
| Date | 21 November 2026 |
| Platform | React Native + Expo; responsive web where supported |

## 1. UX principles

1. **Voice-first, not voice-only:** Every voice action has a visible state and a text/manual alternative.
2. **Patient control:** The user sees what the agent intends to do before consequential action.
3. **Evidence-first:** Health claims link to the original record or clearly state that evidence is unavailable.
4. **Calm clinical language:** Avoid alarmist colors, unsupported severity scores and unexplained “health scores.”
5. **Progressive disclosure:** Show the key information first; let the user open detail and original documents.
6. **Accessible language:** Use plain language and the selected language; preserve canonical medicine names, units, numbers and codes.
7. **Action transparency:** Show the current agent step, whether it is running, awaiting approval, completed, failed or unknown.
8. **Trust distinctions:** Visually distinguish provider-authenticated source, patient-uploaded source, AI-extracted facts and patient-reported events.
9. **No false success:** UI success states require a verified backend result.
10. **Data minimization:** Notifications and lock-screen surfaces must not expose sensitive details by default.

## 2. Visual direction

### 2.1 Brand character

Aarogya should feel like a reassuring personal health companion, not a hospital ERP dashboard. Use warm neutral backgrounds, clean typography, restrained teal/green accents, dark navy text, amber for review-needed states and red only for clearly defined critical/error states.

### 2.2 Design token intent

| Token | Recommended use |
|---|---|
| `color.canvas` | Warm ivory / neutral app background |
| `color.surface` | White cards and sheets |
| `color.text.primary` | Deep navy |
| `color.text.secondary` | Muted slate |
| `color.brand.primary` | Teal |
| `color.status.success` | Muted green |
| `color.status.review` | Amber |
| `color.status.error` | Accessible red |
| `color.action` | Accessible blue |
| `radius.card` | 16–24 px range, consistent |
| `space.*` | 4/8/12/16/24/32 px scale |
| `type.*` | Accessible display, heading, body and caption scale |

Exact hex values are implementation tokens to be finalized in the design system. Never rely on color alone to convey status; pair color with text/icon.

### 2.3 Motion

Use motion to communicate listening/speaking, loading, completion and transitions. Respect reduced-motion preferences. Avoid continuously pulsing medical alerts or decorative animation that competes with content.

## 3. Global navigation

Five primary destinations:

1. **Home** — overview and next actions.
2. **Health** — Health Locker, documents, reports and timeline.
3. **Talk** — voice companion and conversation history.
4. **Medicines** — medication records, schedules, reminders and refills.
5. **Care** — providers, appointments, follow-ups and sharing.

Account/profile/privacy settings are reachable from the Home header or profile menu. The Talk tab is visually prominent, but other workflows remain discoverable without voice.

## 4. Global interaction states

### 4.1 Voice states

- `IDLE`: Ready to start.
- `CONNECTING`: Establishing session; show cancel/retry.
- `LISTENING`: Microphone active; show clear listening indicator.
- `PROCESSING`: User utterance finalized; show lightweight “understanding” status.
- `SPEAKING`: Assistant audio active; allow barge-in.
- `INTERRUPTED`: Current output was interrupted; preserve conversation context.
- `AWAITING_APPROVAL`: Show exact proposal and explicit decision controls.
- `RECOVERING`: Connection or provider is being recovered; do not imply completion.
- `ERROR`: Explain safe next steps and provide text/manual path.
- `ENDED`: Session ended; keep transcript according to user and retention settings.

Voice UI state and business workflow state are separate. A voice session can be speaking while a workflow is awaiting approval or a background tool is still running.

### 4.2 Agent activity states

- `QUEUED`
- `RUNNING`
- `WAITING_FOR_USER`
- `SUCCEEDED`
- `FAILED`
- `UNKNOWN`
- `CANCELLED`

For a consequential action, show an approval screen/card before execution. Never display `SUCCEEDED` until the relevant external result is verified.

### 4.3 Data trust labels

- Provider authenticated.
- Patient uploaded.
- Patient reported.
- AI extracted — review required.
- Patient confirmed.
- Provider verified.

Do not compress these into one generic “verified” badge.

## 5. Screen specifications

Each screen defines purpose, entry, composition, interactions, states and acceptance criteria. Component names correspond to the frontend component registry; API names correspond to the shared contracts and backend API specification.

---

## UX-01 — Onboarding and language selection

**Purpose:** Establish language and basic user preference before the first voice interaction.

**Entry:** First launch or language settings.

**Layout:** Aarogya logo/name, short value proposition, language cards, Continue CTA, privacy summary.

**Content:** “Your health history. Your language. Your care, connected.” Offer Hindi, English initially; other languages appear only when the configured speech path is validated.

**Interactions:** Select preferred language; optionally select secondary language; confirm timezone (default can be suggested but must be editable); view privacy summary; continue.

**States:** Loading saved preferences; no network; unsupported language configuration; permission explanation.

**API/contracts:** `PatientPreferences`, `GET /patient/me`, `PATCH /patient/preferences`.

**UX acceptance:** Selection persists; language labels are self-readable; unsupported language is not represented as fully available.

---

## UX-02 — Sign-in / synthetic demo entry

**Purpose:** Establish authenticated identity and patient context.

**Entry:** Onboarding Continue or expired session.

**Layout:** Phone/email sign-in or clearly labelled “Enter synthetic demo” option for hackathon; concise privacy note; no real patient data in demo mode.

**Interactions:** Authenticate; continue as seeded synthetic patient; sign out.

**States:** Authenticating, invalid credentials, session expired, demo unavailable.

**API/contracts:** Auth provider; `PatientProfile`; session token response.

**UX acceptance:** Patient identity is derived from authentication; no arbitrary patient ID field is exposed as a security mechanism.

---

## UX-03 — Home dashboard

**Purpose:** Give the patient a calm, useful snapshot and clear next actions.

**Entry:** Successful sign-in or Home tab.

**Layout hierarchy:**

1. Greeting in preferred language and profile/language control.
2. Prominent “Talk to Aarogya” voice entry.
3. Upcoming appointment card.
4. Today's medication reminders (if present).
5. Recent health documents and report-processing status.
6. Pending follow-up tasks.
7. Quick actions: Upload report, Find a doctor, View medicines.

**Interactions:** Start voice; open appointment; record reminder action; upload document; open recent report; view timeline.

**States:** First-use empty dashboard; loading skeleton; partial data unavailable; no upcoming care; reminders all completed; backend error.

**Data:** Patient summary, next appointment, due reminders, recent documents, pending tasks.

**Generative UI:** May render `health_summary`, `appointment_summary` and `medication_today` cards. These must use typed payloads.

**UX acceptance:** No fabricated health score or inferred disease status. Each summary card links to its source/detail. A missing dataset is shown as “No record available,” not “Normal.”

---

## UX-04 — Voice Companion

**Purpose:** Primary conversational interface for report questions and care coordination.

**Entry:** Talk tab, Home CTA, or contextual “Ask Aarogya” button.

**Layout:**

- Header with conversation topic, language and session status.
- Central animated voice orb/waveform.
- Live transcript and assistant response region.
- Contextual prompt chips.
- Dynamic UI surface for evidence, doctor options, schedule previews or approvals.
- Microphone, interrupt, end session and text fallback controls.

**Interactions:** Start/stop voice; interrupt assistant; switch language; edit/clarify transcript where supported; select a generated component; approve/reject an action; switch to typed input.

**States:** Idle, connecting, listening, processing, speaking, interrupted, awaiting approval, recovering, error, ended.

**Data/events:** Agora session metadata; `AgentEvent`; `UIComponent`; `ApprovalRequest`.

**UX acceptance:** Clear microphone state; no hidden recording; visible interruption; no approval through ambiguous conversational context alone; the exact approved action is visible.

---

## UX-05 — Health Locker

**Purpose:** Unified patient-controlled collection of medical documents.

**Entry:** Health tab or Home recent records.

**Layout:** Search; filters by document type and date; upload/import CTA; document list; source/trust badges; processing state.

**Interactions:** Upload PDF/image; open document; filter; search; view source; request deletion/archive (subject to policy); open extraction review.

**States:** Empty locker; uploading; queued; processing; review required; ready; failed; unsupported format; duplicate file warning.

**API/contracts:** `HealthDocument`, `DocumentUploadInit`, `DocumentProcessingStatus`.

**UX acceptance:** Original source remains accessible to authorized patient; source type is visible; no document is labelled provider-authenticated solely because OCR succeeded.

---

## UX-06 — Upload and extraction progress

**Purpose:** Make ingestion understandable and let the patient correct extraction mistakes.

**Entry:** Health Locker upload or provider-import notification.

**Layout:** Document preview/filename; progress stages (Secure upload, Classifying, Extracting, Validating, Ready/Review); source type; review summary.

**Interactions:** Retry safe upload; inspect extracted fields; confirm/correct a transcription; reject incorrect extraction; return to locker.

**States:** Upload progress, offline/retry, processing, extraction error, review required, accepted.

**API/contracts:** `HealthDocument`, `DocumentExtraction`, `ExtractionReviewRequest`.

**UX acceptance:** Extraction confidence is not marketed as medical accuracy. Medication fields with ambiguity cannot be activated into reminder schedules.

---

## UX-07 — Report detail and evidence view

**Purpose:** Explain a single report and its specific observations.

**Entry:** Document list, voice-generated `document_viewer` or `lab_observation` component.

**Layout:** Document identity/date/source; summary of source-reported flags; list of test observations; value, unit, original reference interval, original lab interpretation; page/source link; educational explanation separated from source facts.

**Interactions:** Open original page; ask Aarogya; compare with previous; report an extraction error; review extraction status.

**States:** Complete extraction, partial extraction, review required, unsupported test, missing reference interval.

**API/contracts:** `HealthDocument`, `HealthObservation`, `EvidenceReference`.

**UX acceptance:** Show original lab interpretation separately from AI explanation. No overall health conclusion from a subset of visible values. If evidence is missing, say so.

---

## UX-08 — Historical comparison

**Purpose:** Show how compatible recorded observations differ over time.

**Entry:** Report detail or voice request “compare with previous report.”

**Layout:** Analyte name; selectable date range; chart/table; unit and reference intervals per observation; source report links; comparison note explaining comparability.

**Interactions:** Change date range; select data point; open original report; compare another analyte; export/share only through explicit consent workflow.

**States:** Comparable data; insufficient data; unit mismatch; method/lab difference; conflicting test identity; no historical observation.

**API/contracts:** `ObservationComparisonRequest`, `ObservationComparisonResponse`.

**UX acceptance:** Chart does not imply clinical significance. Incomparable values are not joined as a continuous trend. Dates, units and per-report reference intervals remain visible.

---

## UX-09 — Medication dashboard

**Purpose:** Show recorded medication instructions and active patient-confirmed schedules.

**Entry:** Medicines tab or Home reminder card.

**Layout:** Active schedules grouped by time of day; medication name/strength from source; prescription/source link; schedule state; next reminder; adherence history clearly labelled patient-reported.

**Interactions:** Open medicine; view prescription; configure reminder; pause/cancel a reminder; request refill; review patient-reported event history.

**States:** No medication records; prescription review required; schedule pending confirmation; active; paused; completed; expired; conflicting prescription.

**API/contracts:** `MedicationRecord`, `MedicationSchedule`, `AdherenceEvent`.

**UX acceptance:** Do not display extracted or patient-reported medication instructions as provider verified. No dosage-change controls.

---

## UX-10 — Medication schedule review and reminder setup

**Purpose:** Confirm that an extracted schedule accurately reflects the source instructions and define reminder timing.

**Entry:** New prescription extraction or Add Reminder.

**Layout:** Source prescription panel; extracted fields; time zone; reminder times; start/end; schedule preview; confirmation CTA.

**Interactions:** Review each field; edit reminder notification times only within allowed product policy; flag unclear prescription text; confirm schedule; cancel.

**States:** Extraction review required; ambiguous instruction; patient confirmation pending; saved; save failed.

**API/contracts:** `MedicationSchedulePreview`, `CreateMedicationScheduleRequest`.

**UX acceptance:** Any change to clinical dose/frequency/duration must not be presented as an ordinary reminder preference. Unclear clinical instruction routes to clinician/pharmacist clarification.

---

## UX-11 — Reminder notification and adherence capture

**Purpose:** Let patients respond to a due reminder.

**Entry:** Push notification, local notification or Medicines dashboard.

**Layout:** Minimal privacy-safe notification; in-app detail shows medication and source-linked schedule; actions Taken, Snooze, Skipped.

**Interactions:** Record self-reported status; snooze within configured limits; open source prescription; dismiss.

**States:** Due; dispatched; delivered; patient responded; expired; schedule paused/cancelled.

**API/contracts:** `ReminderOccurrence`, `RecordAdherenceRequest`.

**UX acceptance:** Use wording such as “You reported this as taken”; never “verified taken.” Sensitive medication detail is hidden on lock screen by default.

---

## UX-12 — Refill request and quote review

**Purpose:** Let a patient request a refill with prescription and pharmacy checks.

**Entry:** Medication detail or voice request.

**Layout:** Matched medication from verified source; prescription validity/review status; pharmacy quote; formulation/strength/quantity; delivery; total price; expiry; pharmacy identity; approval CTA.

**Interactions:** Request quote; choose pharmacy; inspect exact product; confirm order proposal; launch secure payment-provider flow; view status.

**States:** Not eligible; pharmacist review required; no stock; quote expired; approval pending; payment pending; order pending; confirmed; unknown; failed.

**API/contracts:** `RefillRequest`, `PharmacyQuote`, `ApprovalRequest`, `PaymentSession`, `RefillOrder`.

**UX acceptance:** No substitution is silently selected. Patient must see exact product/strength/form/quantity and final cost. Payment occurs outside the LLM and is separately authorized. Demo sandbox is visibly labelled.

---

## UX-13 — Doctor discovery

**Purpose:** Find an appropriate provider based on the patient's explicit request.

**Entry:** Care tab, Home quick action or voice request.

**Layout:** Search specialty, location, date and consultation mode; results with provider identity, specialty, clinic, distance/location if grounded, availability freshness and source label.

**Interactions:** Search; refine filters; open provider; compare slots; change locality/date.

**States:** Searching; results; no results; provider data stale; provider verification state unclear; API unavailable.

**API/contracts:** `DoctorSearchRequest`, `DoctorSearchResponse`.

**UX acceptance:** Do not invent ratings, fees, qualifications, distance or availability. Distinguish verified and demo provider listings.

---

## UX-14 — Doctor detail and appointment slots

**Purpose:** Show a specific provider and current available slots.

**Entry:** Doctor discovery result or voice-generated provider card.

**Layout:** Provider/clinic information; specialty; verified identity status; appointment mode; available slots with local date/time and timezone; fees only if sourced.

**Interactions:** Select slot; refresh availability; change mode; return to results.

**States:** Available; slot expired; no availability; provider API timeout; appointment mode unavailable.

**API/contracts:** `ProviderSummary`, `AppointmentSlot`, `AppointmentAvailabilityResponse`.

**UX acceptance:** Availability includes retrieval timestamp/expiry. Selection does not itself book the slot.

---

## UX-15 — Approval and action confirmation

**Purpose:** Present a complete, unambiguous action proposal before consequential execution.

**Entry:** Agent creates an `ApprovalRequest`.

**Layout:** Action type; exact target/provider/product; date/time; price and fees if relevant; data to be shared if relevant; purpose; expiry; Approve and Reject actions.

**Interactions:** Inspect details; approve exact proposal; reject; request changes (which invalidates prior approval and creates a new proposal).

**States:** Pending; expired; approved; rejected; action executing; action result unknown; action verified.

**API/contracts:** `ApprovalRequest`, `ApprovalDecisionRequest`, `ActionResult`.

**UX acceptance:** Approval is bound to payload hash and action ID. A changed slot, price, pharmacy, product or sharing scope requires new approval. Voice-only ambiguous “yes” is insufficient unless the action summary is clearly restated and confirmed.

---

## UX-16 — Appointment confirmation and detail

**Purpose:** Show verified provider booking and next steps.

**Entry:** Successful booking verification or Care tab.

**Layout:** Provider, clinic, date/time/timezone, mode, booking reference, status, calendar event status, reminder status, selected records-sharing option.

**Interactions:** Open directions/contact if sourced; add/update calendar; cancel/reschedule through separate approval workflow; share records through separate consent flow.

**States:** Confirmed; calendar pending; booking unknown; booking failed; cancelled; completed.

**UX acceptance:** A calendar integration failure does not erase confirmed booking. Partial outcomes are transparent. No success badge until provider booking is verified.

---

## UX-17 — Care timeline and follow-up tasks

**Purpose:** Present past events and upcoming patient-approved tasks in chronological order.

**Entry:** Care tab or Home timeline card.

**Layout:** Chronological events: documents, encounters, appointments, medication schedule events, follow-up tasks. Each event has a source/author and status.

**Interactions:** Open source; mark patient task complete; reschedule personal reminder; request new appointment; inspect clinician instruction.

**States:** Empty timeline; future tasks; completed; overdue; uncertain source; extraction review required.

**API/contracts:** `HealthTimelineEvent`, `FollowUpTask`.

**UX acceptance:** Distinguish clinician-directed tasks from patient-created reminders. Do not mark a clinical task complete based only on calendar dismissal.

---

## UX-18 — Consent and record sharing

**Purpose:** Let patients understand and control who can access selected records and why.

**Entry:** Appointment flow, provider request, profile/privacy settings.

**Layout:** Recipient identity; purpose; exact documents/record categories; permission duration; data use explanation; grant/deny/revoke controls; sharing history.

**Interactions:** Select records; review sharing scope; grant; revoke future access; inspect audit/share status.

**States:** No active grants; pending; active; revoked; expired; recipient unavailable; share failed/unknown.

**API/contracts:** `ConsentGrant`, `CreateConsentRequest`, `RecordShareEvent`.

**UX acceptance:** Booking approval is not bundled with record-sharing consent. Consent is specific, understandable and revocable for future access. Do not imply revocation can erase copies already lawfully received by another party.

---

## UX-19 — Notifications and preferences

**Purpose:** Manage language, timezone, notification preferences and reminder delivery.

**Entry:** Profile/settings.

**Layout:** Preferred language, secondary language, timezone, notification channels, privacy-safe notification setting, reminder quiet hours (if supported), connected devices.

**Interactions:** Change language/timezone; enable/disable categories; register device; test notification; view delivery status.

**States:** Permission denied; token invalid; delivery failed; settings saving.

**API/contracts:** `PatientPreferences`, `DeviceRegistration`, `NotificationPreference`.

**UX acceptance:** Changing timezone recalculates future schedule occurrences carefully and never changes the prescribed dose/frequency. The user receives a clear preview before consequential schedule changes.

---

## UX-20 — Profile, privacy and help

**Purpose:** Give the patient control over identity, privacy, data export/deletion requests, connected providers and support.

**Entry:** Home header/profile menu.

**Layout:** Profile summary; connected provider list; permissions; data export/deletion request; help and emergency disclaimer; sign out.

**Interactions:** Edit non-clinical preferences; inspect consents; revoke; export request; deletion request; sign out.

**States:** Request pending; export ready; deletion review; network error.

**UX acceptance:** The application explains that legal/clinical retention exceptions may apply; it does not promise immediate deletion of all records without policy validation.

---

## 6. Generative UI registry specification

All dynamic components use a versioned discriminated union. The model may choose a registered component and populate a schema-valid payload. The frontend must not execute arbitrary HTML, JavaScript or model-authored code.

| Component key | Version | Intended payload |
|---|---|---|
| `health_summary` | 1 | Summary text, source refs, status qualifiers |
| `lab_observation` | 1 | Test name, value, unit, reference text, date, source ref |
| `lab_comparison` | 1 | Comparable points, units, ranges, source refs, method |
| `document_viewer` | 1 | Document ID, page, authorized URL reference |
| `medication_schedule` | 1 | Medication record ref, schedule, verification status |
| `adherence_status` | 1 | Reminder occurrence ref and allowed self-report actions |
| `refill_review` | 1 | Quote, exact product, pharmacy, amount, expiry, review flags |
| `doctor_results` | 1 | Provider summaries with source/freshness |
| `appointment_slots` | 1 | Provider and available slots |
| `approval_card` | 1 | Approval ID, exact action summary, payload hash, expiry |
| `care_timeline` | 1 | Ordered events and provenance |
| `safety_notice` | 1 | Approved notice category and safe next-step text |

### Renderer behavior

1. Validate `schema_version`, component key and component payload at runtime.
2. Reject unknown versions/components and display a safe textual fallback.
3. Enforce maximum list length and text length.
4. Fetch protected resources through authenticated API endpoints; do not trust model-supplied URLs.
5. Use server-issued IDs for actions.
6. Do not let component payloads encode arbitrary API paths or executable callbacks.
7. Action components call named frontend commands, which in turn call authenticated backend endpoints.

## 7. Accessibility and localization requirements

- All buttons have accessible labels and roles.
- Waveform and voice states have textual/screen-reader equivalents.
- Dynamic cards announce title and status changes without repeatedly reading entire screens.
- Text scales with device accessibility settings.
- Date/time display respects patient timezone and locale; API stores instants in UTC plus explicit timezone context where necessary.
- Numbers, decimal separators, units and medication names are preserved.
- Language fallback is explicit; never silently switch a patient to a language that is not supported by the voice pipeline.
- Use captions/transcript as a fallback when audio is unavailable.

## 8. Analytics and privacy

Track UX events such as `voice_session_started`, `voice_session_failed`, `ui_component_rendered`, `approval_shown`, `approval_decided`, `workflow_completed` and `workflow_failed` using pseudonymous IDs and non-sensitive metadata. Do not send report values, medicine names, diagnoses or raw transcripts to general analytics by default.

## 9. Screen acceptance checklist

- Screen has defined loading, empty, error and success states.
- All patient-specific data comes from authorized repository/API layer.
- All record claims link to evidence.
- All actions show exact status and do not fake success.
- All consequential actions have approval and backend authorization.
- All dynamic components validate against the shared schema.
- Voice and text interactions are both usable.
- Language and timezone behavior is tested.
- Accessibility labels and text scaling are verified.

---

**End of UX Specification.**
