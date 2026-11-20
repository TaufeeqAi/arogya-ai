# Shared Contract Package

## Canonical source

`python/aarogya_contracts/` contains Pydantic v2 starter models for public API, event and generative UI contracts. Extend these models as endpoints are implemented. The package intentionally excludes SQLAlchemy ORM models and LangGraph internal checkpoint state.

## Generate JSON Schemas

From the pack root:

```bash
python -m pip install -e 'contracts/python[dev]'
python scripts/export_contract_schemas.py
```

The generated schemas are written to `contracts/events/`.

## Intended API client generation flow

1. Import the contract package into the FastAPI application.
2. Define endpoint request/response models using these shared Pydantic classes.
3. Export `app.openapi()` to a versioned `openapi/aarogya-v1.json` artifact.
4. Run Orval using that OpenAPI file to generate TypeScript API types and client hooks.
5. Validate inbound dynamic UI payloads at runtime with generated Zod schemas (or a schema validator generated from the same OpenAPI/JSON Schema source).
6. Commit generated files or generate them in CI, but never hand-edit generated files.
7. CI re-generates and fails on an uncommitted diff.

The starter pack does not include a live FastAPI `app` or a complete OpenAPI document yet. That is created in Phase 4. Until then, frontend uses typed mock repositories and these initial contract models/fixtures.

## Required compatibility rules

- REST version prefix: `/api/v1`.
- Agent event schema: `schema_version` is required.
- Generative UI: component key and `version` are required.
- Timestamps are timezone-aware ISO 8601.
- Money uses decimal-safe amount plus ISO currency code.
- Every patient health fact carries provenance/evidence.
- Client must not supply trusted patient identity in a model-generated tool call.
- Public DTOs must not expose ORM entities or private storage keys.
