# Aarogya Specification Pack

**Version:** 1.0.0  
**Date:** 21 November 2026  
**Track:** Build with Agora — PS11, Breaking Language Barriers Through Agentic Voice AI  
**Status:** Implementation baseline for hackathon MVP; not a production compliance certification.

## Product summary

Aarogya is a patient-controlled, multilingual, voice-first health companion. The MVP focuses on longitudinal health memory, source-linked report understanding, a report-to-consultation appointment workflow, patient-confirmed medication reminders, and consent-aware follow-up coordination.

The assistant is not a diagnostic system or autonomous prescriber. Real patient data is out of scope for the hackathon demo by default; use synthetic patient records and clearly labelled provider/pharmacy/payment sandboxes.

## Contents

| Path | Purpose |
|---|---|
| `docs/01_PRODUCT_REQUIREMENTS.md` | Product scope, personas, functional/non-functional requirements, acceptance criteria and exclusions |
| `docs/02_SYSTEM_ARCHITECTURE.md` | System architecture, boundaries, data flows, integration topology, reliability and security decisions |
| `docs/03_DATABASE_SCHEMA.md` | Logical data model, relationships, lifecycle rules, indexes and security requirements |
| `database/001_initial_schema.sql` | PostgreSQL MVP base schema |
| `database/002_patient_scope_constraints.sql` | Composite foreign keys that harden cross-patient relationship integrity |
| `docs/04_LANGGRAPH_WORKFLOW_CONTRACTS.md` | Graph state, workflow nodes, tools, approval, event and recovery contracts |
| `docs/05_SCREEN_BY_SCREEN_UX_SPEC.md` | Screen purposes, layout, interactions, states, data contracts and acceptance criteria |
| `contracts/python/aarogya_contracts/` | Pydantic v2 starter models for public API/event/UI contracts |
| `contracts/events/` | Exported JSON Schemas for key contracts |
| `scripts/export_contract_schemas.py` | Regenerates JSON Schemas from Pydantic models |

## Recommended implementation order

1. Phase 0: contracts and voice feasibility spike.
2. Phase 1: frontend design system and app shell.
3. Phase 2: simulated voice experience and Generative UI.
4. Phase 3: all key patient workflows against mock repositories.
5. Phase 4: backend identity, database and storage.
6. Phase 5: document ingestion and health memory.
7. Phase 6: LangGraph and NeMo safety integration.
8. Phase 7: appointment, medication and pharmacy workflows.
9. Phase 8: real Agora/Murf integration.
10. Phase 9: red-team, evaluation and demo hardening.

## Shared contract workflow

Pydantic models are the canonical contract definitions. The intended generation pipeline is:

`Pydantic -> FastAPI OpenAPI -> Orval -> TypeScript API client + Zod validation`.

The current pack includes starter Pydantic contracts and JSON Schema exports. It does not include a completed FastAPI application or generated OpenAPI client because those are implementation deliverables. Once the FastAPI app exists, export its OpenAPI specification and generate the frontend client. Do not hand-maintain duplicate TypeScript API interfaces.

To export the included JSON Schemas:

```bash
cd aarogya_spec_pack
python -m pip install -e 'contracts/python[dev]'
python scripts/export_contract_schemas.py
```

## SQL schema use

`database/001_initial_schema.sql` is the starting migration for a local/synthetic MVP environment. Apply `database/002_patient_scope_constraints.sql` immediately afterward to add composite patient-scope foreign keys. Migration 001 requires PostgreSQL with permission to enable `pgcrypto`. Review both migrations and add project-specific migrations before use. They are not a production-ready healthcare database certification.

## Key architecture rules

- PostgreSQL is the source of truth for structured records and workflow state.
- Qdrant stores searchable narrative chunks but never authorizes access.
- Original documents stay in private object storage.
- LangGraph state stores minimal references, not entire patient histories.
- LangGraph is the single workflow decision authority.
- NeMo Guardrails supplements, but does not replace, backend authorization.
- Consequential actions require server-side, payload-bound approval.
- Appointments, refills and payments are idempotent and must be verified against the external system.
- Medication reminders use source-linked, sufficiently verified instructions; adherence is explicitly patient-reported.
- Generative UI selects from a fixed component registry and never executes model-generated code.
- Voice, API and agent progress channels have separate responsibilities.

## Scope decisions

### Included in the MVP

- Synthetic patient health locker and uploads.
- Structured report extraction with provenance/review state.
- Health history retrieval and historical comparison.
- Hindi/Hinglish and English voice prototype after actual ASR/TTS validation.
- Report-to-Consultation appointment workflow.
- Patient-confirmed medication reminder setup where feasible.
- Consent and record-sharing UI.
- Mock provider import to demonstrate hybrid ingestion.
- Schema-driven Generative UI.

### Stretch or future

- Pharmacy refill and sandbox payment.
- Kannada and broader Indic language support.
- Caregiver access.
- Real provider/laboratory integration.
- Full ABDM onboarding/exchange.
- Insurance policy explainer.

### Excluded from v1

- Personalized insurance sales/recommendation using medical history.
- Autonomous diagnosis, prescribing, dosage changes or treatment recommendations.
- Unverified real-world pharmacy sales.

## Open implementation decisions / risks

1. Validate the exact Agora Conversational AI custom LLM/tool integration path with LangGraph as the sole workflow authority. Avoid dual independent LLM decision loops.
2. Validate Murf Falcon voice/language compatibility in the chosen Agora configuration.
3. Measure end-to-end voice latency from Bengaluru.
4. Pick the final Expo native audio integration and confirm iOS/Android/web support boundaries.
5. Select persistent worker/scheduler implementation after testing recurrence and retry behavior.
6. Confirm applicable legal/clinical review before any real patient/provider/pharmacy deployment.

## Artifact status and limitations

This is a specification and starter-contract pack. It is not an implemented product, not clinical validation, not legal advice, and not a claim of live integration with Agora, Murf, ABDM, any hospital, pharmacy, payment processor or calendar provider. Integration credentials and current vendor capabilities must be verified during Phase 0.
