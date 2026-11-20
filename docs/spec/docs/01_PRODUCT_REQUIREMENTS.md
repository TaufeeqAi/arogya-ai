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
