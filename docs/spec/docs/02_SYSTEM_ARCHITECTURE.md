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
