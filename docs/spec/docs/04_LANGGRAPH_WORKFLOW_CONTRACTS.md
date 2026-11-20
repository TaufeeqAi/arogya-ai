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
