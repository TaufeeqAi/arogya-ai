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
