-- Aarogya MVP initial PostgreSQL schema
-- Version: 1.0.0 | Date: 2026-11-21
-- Synthetic demo baseline. Review migrations, tenancy, retention, and regulatory
-- requirements before using with real patient data.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- -----------------------------------------------------------------------------
-- Identity and patient context
-- -----------------------------------------------------------------------------
CREATE TABLE app_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE,
    phone_e164 TEXT UNIQUE,
    display_name TEXT NOT NULL,
    account_status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK (account_status IN ('ACTIVE','LOCKED','DEACTIVATED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (email IS NOT NULL OR phone_e164 IS NOT NULL)
);

CREATE TABLE patient_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES app_users(id),
    preferred_language TEXT NOT NULL DEFAULT 'hi',
    secondary_language TEXT,
    timezone TEXT NOT NULL DEFAULT 'Asia/Kolkata',
    date_of_birth DATE,
    sex_at_birth TEXT CHECK (sex_at_birth IS NULL OR sex_at_birth IN ('FEMALE','MALE','INTERSEX','UNKNOWN','NOT_RECORDED')),
    profile_status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK (profile_status IN ('ACTIVE','INACTIVE','DELETION_REQUESTED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE patient_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_profiles(id),
    platform TEXT NOT NULL CHECK (platform IN ('IOS','ANDROID','WEB')),
    push_token TEXT NOT NULL,
    token_hash TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_seen_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (platform, token_hash)
);

CREATE INDEX ix_patient_devices_patient ON patient_devices(patient_id, is_active);

-- -----------------------------------------------------------------------------
-- Provider directory and provider-patient linkage
-- -----------------------------------------------------------------------------
CREATE TABLE clinics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    display_name TEXT NOT NULL,
    address_line TEXT,
    locality TEXT,
    city TEXT,
    state TEXT,
    postal_code TEXT,
    country_code CHAR(2) NOT NULL DEFAULT 'IN',
    phone_public TEXT,
    source_kind TEXT NOT NULL DEFAULT 'DEMO'
        CHECK (source_kind IN ('DEMO','PARTNER_API','PROVIDER_PORTAL')),
    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE','INACTIVE')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    app_user_id UUID REFERENCES app_users(id),
    display_name TEXT NOT NULL,
    specialty TEXT NOT NULL,
    registration_reference TEXT,
    verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED'
        CHECK (verification_status IN ('UNVERIFIED','PENDING','VERIFIED','REJECTED')),
    source_kind TEXT NOT NULL DEFAULT 'DEMO'
        CHECK (source_kind IN ('DEMO','PARTNER_API','PROVIDER_PORTAL')),
    external_provider_id TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE','INACTIVE')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source_kind, external_provider_id)
);

CREATE TABLE provider_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID NOT NULL REFERENCES providers(id),
    clinic_id UUID NOT NULL REFERENCES clinics(id),
    consultation_modes TEXT[] NOT NULL DEFAULT ARRAY['IN_PERSON'],
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (provider_id, clinic_id)
);

CREATE TABLE provider_patient_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_profiles(id),
    provider_id UUID NOT NULL REFERENCES providers(id),
    link_status TEXT NOT NULL CHECK (link_status IN ('PENDING','ACTIVE','REVOKED','EXPIRED')),
    verification_method TEXT NOT NULL,
    verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (patient_id, provider_id)
);

CREATE INDEX ix_providers_specialty ON providers(specialty, status);
CREATE INDEX ix_provider_locations_clinic ON provider_locations(clinic_id, is_active);

-- -----------------------------------------------------------------------------
-- Health documents and extraction provenance
-- -----------------------------------------------------------------------------
CREATE TABLE health_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_profiles(id),
    uploaded_by_user_id UUID REFERENCES app_users(id),
    source_kind TEXT NOT NULL CHECK (source_kind IN ('PATIENT_UPLOAD','PROVIDER_IMPORT','LAB_IMPORT','OTHER')),
    source_provider_id UUID REFERENCES providers(id),
    source_organization TEXT,
    document_type TEXT NOT NULL CHECK (document_type IN (
        'LAB_REPORT','PRESCRIPTION','CONSULTATION_NOTE','DISCHARGE_SUMMARY',
        'RADIOLOGY_REPORT','MEDICAL_CERTIFICATE','INSURANCE_POLICY','OTHER','UNKNOWN'
    )),
    original_filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    byte_size BIGINT NOT NULL CHECK (byte_size >= 0),
    page_count INTEGER CHECK (page_count IS NULL OR page_count > 0),
    storage_key TEXT NOT NULL UNIQUE,
    sha256_hex CHAR(64) NOT NULL,
    document_status TEXT NOT NULL DEFAULT 'UPLOADED'
        CHECK (document_status IN ('UPLOADED','QUEUED','PROCESSING','NEEDS_REVIEW','READY','FAILED','QUARANTINED','ARCHIVED')),
    source_verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED'
        CHECK (source_verification_status IN ('UNVERIFIED','PATIENT_ATTESTED','PROVIDER_AUTHENTICATED','INDEPENDENTLY_VERIFIED')),
    record_visibility TEXT NOT NULL DEFAULT 'PATIENT_ONLY'
        CHECK (record_visibility IN ('PATIENT_ONLY','SHARED_BY_CONSENT','RESTRICTED')),
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    archived_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_health_documents_patient_time ON health_documents(patient_id, received_at DESC);
CREATE INDEX ix_health_documents_patient_type ON health_documents(patient_id, document_type, document_status);
CREATE INDEX ix_health_documents_sha ON health_documents(patient_id, sha256_hex);

CREATE TABLE document_extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_profiles(id),
    document_id UUID NOT NULL REFERENCES health_documents(id),
    extractor_name TEXT NOT NULL,
    extractor_version TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    extraction_status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (extraction_status IN ('PENDING','RUNNING','EXTRACTED','VALIDATION_REQUIRED','ACCEPTED','REJECTED','FAILED')),
    extracted_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    raw_text_storage_key TEXT,
    error_code TEXT,
    review_required BOOLEAN NOT NULL DEFAULT FALSE,
    reviewed_by_user_id UUID REFERENCES app_users(id),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX ix_extractions_document ON document_extractions(document_id, created_at DESC);
CREATE INDEX ix_extractions_patient ON document_extractions(patient_id, extraction_status);

-- -----------------------------------------------------------------------------
-- Structured longitudinal health memory
-- -----------------------------------------------------------------------------
CREATE TABLE health_observations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_profiles(id),
    document_id UUID NOT NULL REFERENCES health_documents(id),
    extraction_id UUID REFERENCES document_extractions(id),
    test_code_system TEXT,
    test_code TEXT,
    test_name_original TEXT NOT NULL,
    test_name_normalized TEXT,
    value_numeric NUMERIC(18,6),
    value_text TEXT,
    unit_original TEXT,
    unit_normalized TEXT,
    reference_low NUMERIC(18,6),
    reference_high NUMERIC(18,6),
    reference_text TEXT,
    laboratory_interpretation TEXT,
    observed_at TIMESTAMPTZ,
    laboratory_name TEXT,
    page_number INTEGER CHECK (page_number IS NULL OR page_number > 0),
    source_locator TEXT,
    source_excerpt TEXT,
    extraction_confidence NUMERIC(5,4) CHECK (extraction_confidence IS NULL OR (extraction_confidence >= 0 AND extraction_confidence <= 1)),
    verification_status TEXT NOT NULL DEFAULT 'EXTRACTION_PENDING'
        CHECK (verification_status IN ('EXTRACTION_PENDING','REVIEW_REQUIRED','PATIENT_CONFIRMED','PROVIDER_VERIFIED','SOURCE_ONLY','REJECTED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (value_numeric IS NOT NULL OR value_text IS NOT NULL),
    CHECK (reference_low IS NULL OR reference_high IS NULL OR reference_low <= reference_high)
);

CREATE INDEX ix_observations_patient_date ON health_observations(patient_id, observed_at DESC);
CREATE INDEX ix_observations_patient_test ON health_observations(patient_id, test_name_normalized, observed_at DESC);
CREATE INDEX ix_observations_document ON health_observations(document_id, page_number);

CREATE TABLE encounters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_profiles(id),
    provider_id UUID REFERENCES providers(id),
    clinic_id UUID REFERENCES clinics(id),
    appointment_id UUID,
    encounter_type TEXT NOT NULL CHECK (encounter_type IN ('CONSULTATION','FOLLOW_UP','EMERGENCY','DIAGNOSTIC','OTHER')),
    occurred_at TIMESTAMPTZ NOT NULL,
    source_document_id UUID REFERENCES health_documents(id),
    assessment_text TEXT,
    note_text TEXT,
    source_kind TEXT NOT NULL CHECK (source_kind IN ('PROVIDER_AUTHORED','PATIENT_REPORTED','PATIENT_UPLOADED','SYSTEM_DERIVED')),
    verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED'
        CHECK (verification_status IN ('UNVERIFIED','PATIENT_CONFIRMED','PROVIDER_VERIFIED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_encounters_patient_date ON encounters(patient_id, occurred_at DESC);

CREATE TABLE condition_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_profiles(id),
    encounter_id UUID REFERENCES encounters(id),
    source_document_id UUID REFERENCES health_documents(id),
    code_system TEXT,
    code TEXT,
    display_text TEXT NOT NULL,
    clinical_status TEXT NOT NULL DEFAULT 'UNKNOWN'
        CHECK (clinical_status IN ('ACTIVE','RESOLVED','INACTIVE','UNKNOWN')),
    source_kind TEXT NOT NULL CHECK (source_kind IN ('PROVIDER_AUTHORED','PATIENT_REPORTED','PATIENT_UPLOADED','SYSTEM_DERIVED')),
    verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED'
        CHECK (verification_status IN ('UNVERIFIED','PATIENT_CONFIRMED','PROVIDER_VERIFIED')),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_conditions_patient ON condition_records(patient_id, clinical_status);

CREATE TABLE allergy_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_profiles(id),
    substance TEXT NOT NULL,
    reaction TEXT,
    severity TEXT,
    source_document_id UUID REFERENCES health_documents(id),
    source_kind TEXT NOT NULL CHECK (source_kind IN ('PROVIDER_AUTHORED','PATIENT_REPORTED','PATIENT_UPLOADED')),
    verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED'
        CHECK (verification_status IN ('UNVERIFIED','PATIENT_CONFIRMED','PROVIDER_VERIFIED')),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_allergies_patient ON allergy_records(patient_id);

CREATE TABLE care_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_profiles(id),
    encounter_id UUID REFERENCES encounters(id),
    source_document_id UUID REFERENCES health_documents(id),
    authored_by_provider_id UUID REFERENCES providers(id),
    title TEXT NOT NULL,
    instruction_text TEXT NOT NULL,
    effective_from DATE,
    effective_until DATE,
    source_kind TEXT NOT NULL CHECK (source_kind IN ('PROVIDER_AUTHORED','PATIENT_REPORTED','PATIENT_UPLOADED')),
    verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED'
        CHECK (verification_status IN ('UNVERIFIED','PATIENT_CONFIRMED','PROVIDER_VERIFIED')),
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','COMPLETED','SUPERSEDED','CANCELLED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_care_plans_patient ON care_plans(patient_id, status, created_at DESC);

CREATE TABLE follow_up_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_profiles(id),
    care_plan_id UUID REFERENCES care_plans(id),
    source_document_id UUID REFERENCES health_documents(id),
    task_type TEXT NOT NULL CHECK (task_type IN ('APPOINTMENT','INVESTIGATION','MEDICATION_REVIEW','GENERAL_FOLLOW_UP','OTHER')),
    title TEXT NOT NULL,
    instructions TEXT,
    due_at TIMESTAMPTZ,
    timezone TEXT NOT NULL DEFAULT 'Asia/Kolkata',
    source_kind TEXT NOT NULL CHECK (source_kind IN ('PROVIDER_AUTHORED','PATIENT_REQUESTED','PATIENT_CONFIRMED')),
    status TEXT NOT NULL DEFAULT 'PENDING_CONFIRMATION'
        CHECK (status IN ('PENDING_CONFIRMATION','SCHEDULED','COMPLETED','DISMISSED','CANCELLED')),
    patient_confirmed_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_followups_patient_due ON follow_up_tasks(patient_id, due_at) WHERE status IN ('PENDING_CONFIRMATION','SCHEDULED');

-- -----------------------------------------------------------------------------
-- Medication records, schedules and patient-reported adherence
-- -----------------------------------------------------------------------------
CREATE TABLE medication_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_profiles(id),
    source_document_id UUID REFERENCES health_documents(id),
    encounter_id UUID REFERENCES encounters(id),
    prescribing_provider_id UUID REFERENCES providers(id),
    medication_name_original TEXT NOT NULL,
    generic_name TEXT,
    brand_name TEXT,
    strength TEXT,
    dosage_form TEXT,
    route TEXT,
    dosage_instruction TEXT,
    frequency_instruction TEXT,
    duration_instruction TEXT,
    additional_instruction TEXT,
    prescribed_at TIMESTAMPTZ,
    start_date DATE,
    end_date DATE,
    source_kind TEXT NOT NULL CHECK (source_kind IN ('PROVIDER_AUTHORED','PATIENT_UPLOAD','PATIENT_REPORTED')),
    verification_status TEXT NOT NULL DEFAULT 'REVIEW_REQUIRED'
        CHECK (verification_status IN ('REVIEW_REQUIRED','PATIENT_CONFIRMED','PROVIDER_VERIFIED','REJECTED')),
    status TEXT NOT NULL DEFAULT 'REVIEW_REQUIRED'
        CHECK (status IN ('DRAFT','ACTIVE','COMPLETED','DISCONTINUED','SUPERSEDED','REVIEW_REQUIRED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date)
);

CREATE INDEX ix_medications_patient_status ON medication_records(patient_id, status, prescribed_at DESC);

CREATE TABLE medication_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_profiles(id),
    medication_record_id UUID NOT NULL REFERENCES medication_records(id),
    timezone TEXT NOT NULL,
    times_of_day TIME[] NOT NULL,
    days_of_week SMALLINT[] NOT NULL DEFAULT ARRAY[0,1,2,3,4,5,6],
    start_date DATE NOT NULL,
    end_date DATE,
    reminder_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    instruction_source_document_id UUID REFERENCES health_documents(id),
    patient_confirmed_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'PENDING_CONFIRMATION'
        CHECK (status IN ('DRAFT','PENDING_CONFIRMATION','ACTIVE','PAUSED','COMPLETED','CANCELLED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (cardinality(times_of_day) > 0),
    CHECK (cardinality(days_of_week) > 0),
    CHECK (end_date IS NULL OR end_date >= start_date),
    CHECK (0 <= ALL(days_of_week) AND 6 >= ALL(days_of_week))
);

CREATE INDEX ix_medication_schedules_due ON medication_schedules(status, reminder_enabled, start_date, end_date);
CREATE INDEX ix_medication_schedules_patient ON medication_schedules(patient_id, status);

CREATE TABLE reminder_occurrences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_profiles(id),
    medication_schedule_id UUID NOT NULL REFERENCES medication_schedules(id),
    scheduled_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'SCHEDULED'
        CHECK (status IN ('SCHEDULED','DISPATCHED','DELIVERED','FAILED','CANCELLED','EXPIRED')),
    dispatched_at TIMESTAMPTZ,
    delivery_reference TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (medication_schedule_id, scheduled_at)
);

CREATE INDEX ix_reminder_occurrences_patient_due ON reminder_occurrences(patient_id, scheduled_at DESC);
CREATE INDEX ix_reminder_occurrences_pending ON reminder_occurrences(scheduled_at) WHERE status = 'SCHEDULED';

CREATE TABLE adherence_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_profiles(id),
    reminder_occurrence_id UUID REFERENCES reminder_occurrences(id),
    medication_schedule_id UUID NOT NULL REFERENCES medication_schedules(id),
    reported_status TEXT NOT NULL CHECK (reported_status IN ('TAKEN_REPORTED','SKIPPED_REPORTED','SNOOZED')),
    reported_by_user_id UUID NOT NULL REFERENCES app_users(id),
    reported_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    source TEXT NOT NULL DEFAULT 'PATIENT_APP' CHECK (source IN ('PATIENT_APP','VOICE_AGENT','AUTHORIZED_CAREGIVER')),
    note TEXT
);

CREATE INDEX ix_adherence_patient_time ON adherence_events(patient_id, reported_at DESC);

-- -----------------------------------------------------------------------------
-- Provider availability and appointments
-- -----------------------------------------------------------------------------
CREATE TABLE provider_slots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID NOT NULL REFERENCES providers(id),
    clinic_id UUID NOT NULL REFERENCES clinics(id),
    external_slot_id TEXT,
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    timezone TEXT NOT NULL,
    consultation_mode TEXT NOT NULL CHECK (consultation_mode IN ('IN_PERSON','VIDEO','PHONE')),
    availability_status TEXT NOT NULL DEFAULT 'AVAILABLE'
        CHECK (availability_status IN ('AVAILABLE','HELD','BOOKED','UNAVAILABLE','EXPIRED')),
    source_kind TEXT NOT NULL CHECK (source_kind IN ('DEMO','PARTNER_API')),
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ,
    UNIQUE (provider_id, external_slot_id),
    CHECK (ends_at > starts_at)
);

CREATE INDEX ix_provider_slots_search ON provider_slots(provider_id, starts_at, availability_status);
CREATE INDEX ix_provider_slots_clinic ON provider_slots(clinic_id, starts_at, availability_status);

CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_profiles(id),
    provider_id UUID NOT NULL REFERENCES providers(id),
    clinic_id UUID NOT NULL REFERENCES clinics(id),
    provider_slot_id UUID REFERENCES provider_slots(id),
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    timezone TEXT NOT NULL,
    consultation_mode TEXT NOT NULL CHECK (consultation_mode IN ('IN_PERSON','VIDEO','PHONE')),
    status TEXT NOT NULL DEFAULT 'REQUESTED'
        CHECK (status IN ('REQUESTED','PENDING_APPROVAL','BOOKING','CONFIRMED','CANCEL_PENDING','CANCELLED','FAILED','UNKNOWN','COMPLETED','NO_SHOW')),
    external_booking_id TEXT,
    source_kind TEXT NOT NULL CHECK (source_kind IN ('DEMO','PARTNER_API')),
    idempotency_key TEXT NOT NULL UNIQUE,
    created_by_user_id UUID NOT NULL REFERENCES app_users(id),
    confirmed_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    result_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (provider_id, external_booking_id),
    CHECK (ends_at > starts_at)
);

CREATE INDEX ix_appointments_patient_time ON appointments(patient_id, starts_at DESC);
CREATE INDEX ix_appointments_provider_time ON appointments(provider_id, starts_at);
CREATE INDEX ix_appointments_status ON appointments(status, updated_at);

-- Add encounter -> appointment FK after appointments exists.
ALTER TABLE encounters
    ADD CONSTRAINT fk_encounters_appointment
    FOREIGN KEY (appointment_id) REFERENCES appointments(id);

-- -----------------------------------------------------------------------------
-- Pharmacy, refill and payment records (sandbox or authorized partner only)
-- -----------------------------------------------------------------------------
CREATE TABLE pharmacy_partners (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    display_name TEXT NOT NULL,
    integration_kind TEXT NOT NULL CHECK (integration_kind IN ('SANDBOX','PARTNER_API')),
    authorization_status TEXT NOT NULL DEFAULT 'UNVERIFIED'
        CHECK (authorization_status IN ('UNVERIFIED','PENDING_REVIEW','VERIFIED','SUSPENDED')),
    licence_reference TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','INACTIVE')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE refill_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_profiles(id),
    medication_record_id UUID NOT NULL REFERENCES medication_records(id),
    prescription_document_id UUID REFERENCES health_documents(id),
    pharmacy_partner_id UUID REFERENCES pharmacy_partners(id),
    requested_quantity TEXT,
    request_status TEXT NOT NULL DEFAULT 'DRAFT'
        CHECK (request_status IN ('DRAFT','ELIGIBILITY_CHECK','PHARMACY_REVIEW','QUOTE_READY','PENDING_PATIENT_APPROVAL','ORDERING','ORDERED','REJECTED','FAILED','UNKNOWN','CANCELLED')),
    eligibility_status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (eligibility_status IN ('PENDING','ELIGIBLE','NOT_ELIGIBLE','PHARMACIST_REVIEW_REQUIRED','UNKNOWN')),
    idempotency_key TEXT NOT NULL UNIQUE,
    created_by_user_id UUID NOT NULL REFERENCES app_users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_refill_patient_status ON refill_requests(patient_id, request_status, created_at DESC);

CREATE TABLE pharmacy_quotes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    refill_request_id UUID NOT NULL REFERENCES refill_requests(id),
    pharmacy_partner_id UUID NOT NULL REFERENCES pharmacy_partners(id),
    product_description TEXT NOT NULL,
    strength TEXT,
    formulation TEXT,
    quantity TEXT NOT NULL,
    amount NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
    currency CHAR(3) NOT NULL DEFAULT 'INR',
    delivery_fee NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (delivery_fee >= 0),
    quote_status TEXT NOT NULL CHECK (quote_status IN ('AVAILABLE','UNAVAILABLE','EXPIRED','REVIEW_REQUIRED')),
    external_quote_id TEXT,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE refill_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    refill_request_id UUID NOT NULL UNIQUE REFERENCES refill_requests(id),
    pharmacy_quote_id UUID NOT NULL REFERENCES pharmacy_quotes(id),
    pharmacy_partner_id UUID NOT NULL REFERENCES pharmacy_partners(id),
    external_order_id TEXT,
    order_status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (order_status IN ('PENDING','PHARMACY_REVIEW','CONFIRMED','DISPATCHED','DELIVERED','REJECTED','CANCELLED','FAILED','UNKNOWN')),
    idempotency_key TEXT NOT NULL UNIQUE,
    ordered_at TIMESTAMPTZ,
    verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (pharmacy_partner_id, external_order_id)
);

CREATE TABLE payment_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_profiles(id),
    refill_order_id UUID NOT NULL REFERENCES refill_orders(id),
    payment_provider TEXT NOT NULL,
    external_payment_id TEXT,
    amount NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
    currency CHAR(3) NOT NULL DEFAULT 'INR',
    payment_status TEXT NOT NULL DEFAULT 'CREATED'
        CHECK (payment_status IN ('CREATED','PENDING','AUTHORIZED','CAPTURED','FAILED','CANCELLED','REFUNDED','UNKNOWN')),
    idempotency_key TEXT NOT NULL UNIQUE,
    approved_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (payment_provider, external_payment_id)
);

-- -----------------------------------------------------------------------------
-- Consent and record sharing
-- -----------------------------------------------------------------------------
CREATE TABLE consent_grants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_profiles(id),
    granted_by_user_id UUID NOT NULL REFERENCES app_users(id),
    recipient_provider_id UUID REFERENCES providers(id),
    recipient_user_id UUID REFERENCES app_users(id),
    purpose TEXT NOT NULL,
    scope JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','REVOKED','EXPIRED')),
    valid_from TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (recipient_provider_id IS NOT NULL OR recipient_user_id IS NOT NULL),
    CHECK (expires_at IS NULL OR expires_at > valid_from)
);

CREATE INDEX ix_consents_patient_status ON consent_grants(patient_id, status, expires_at);

CREATE TABLE record_share_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_profiles(id),
    consent_grant_id UUID NOT NULL REFERENCES consent_grants(id),
    document_id UUID REFERENCES health_documents(id),
    observation_id UUID REFERENCES health_observations(id),
    recipient_provider_id UUID REFERENCES providers(id),
    recipient_user_id UUID REFERENCES app_users(id),
    share_purpose TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('REQUESTED','SHARED','FAILED','REVOKED')),
    external_share_reference TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_record_shares_patient_time ON record_share_events(patient_id, created_at DESC);

-- -----------------------------------------------------------------------------
-- Agent threads, workflow runs and approvals
-- -----------------------------------------------------------------------------
CREATE TABLE agent_threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_profiles(id),
    owner_user_id UUID NOT NULL REFERENCES app_users(id),
    graph_thread_id TEXT NOT NULL UNIQUE,
    preferred_language TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','ENDED','ARCHIVED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_agent_threads_patient ON agent_threads(patient_id, last_activity_at DESC);

CREATE TABLE workflow_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_profiles(id),
    agent_thread_id UUID REFERENCES agent_threads(id),
    workflow_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING','RUNNING','AWAITING_APPROVAL','SUCCEEDED','FAILED','CANCELLED','UNKNOWN')),
    current_node TEXT,
    checkpoint_reference TEXT,
    correlation_id UUID NOT NULL DEFAULT gen_random_uuid(),
    idempotency_key TEXT,
    input_reference JSONB NOT NULL DEFAULT '{}'::jsonb,
    result_reference JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (workflow_type, idempotency_key)
);

CREATE INDEX ix_workflow_runs_patient_time ON workflow_runs(patient_id, created_at DESC);
CREATE INDEX ix_workflow_runs_status ON workflow_runs(status, created_at);

CREATE TABLE approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_profiles(id),
    workflow_run_id UUID REFERENCES workflow_runs(id),
    action_type TEXT NOT NULL,
    action_payload JSONB NOT NULL,
    action_payload_sha256 CHAR(64) NOT NULL,
    approval_token_hash CHAR(64) NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING','APPROVED','REJECTED','EXPIRED','CANCELLED')),
    requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    decided_by_user_id UUID REFERENCES app_users(id),
    decided_at TIMESTAMPTZ,
    decision_note TEXT,
    CHECK (expires_at > requested_at)
);

CREATE INDEX ix_approvals_patient_status ON approval_requests(patient_id, status, expires_at);

-- -----------------------------------------------------------------------------
-- Notifications, audit and transactional outbox
-- -----------------------------------------------------------------------------
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_profiles(id),
    notification_type TEXT NOT NULL,
    title TEXT NOT NULL,
    body_safe TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    scheduled_at TIMESTAMPTZ,
    dispatched_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING','DISPATCHED','DELIVERED','READ','FAILED','CANCELLED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_notifications_patient_time ON notifications(patient_id, created_at DESC);
CREATE INDEX ix_notifications_pending ON notifications(scheduled_at) WHERE status = 'PENDING';

CREATE TABLE audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patient_profiles(id),
    actor_user_id UUID REFERENCES app_users(id),
    actor_type TEXT NOT NULL CHECK (actor_type IN ('PATIENT','PROVIDER','CAREGIVER','SYSTEM','WORKER','ADMIN')),
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    outcome TEXT NOT NULL CHECK (outcome IN ('SUCCESS','DENIED','FAILED','UNKNOWN')),
    correlation_id UUID,
    request_id TEXT,
    metadata_safe JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_audit_patient_time ON audit_events(patient_id, created_at DESC);
CREATE INDEX ix_audit_correlation ON audit_events(correlation_id);

CREATE TABLE outbox_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type TEXT NOT NULL,
    aggregate_id UUID NOT NULL,
    event_type TEXT NOT NULL,
    event_payload JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING','PROCESSING','PUBLISHED','FAILED')),
    attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    available_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at TIMESTAMPTZ,
    last_error_code TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_outbox_pending ON outbox_events(available_at, created_at) WHERE status IN ('PENDING','FAILED');

-- -----------------------------------------------------------------------------
-- Recommended implementation notes (not executable policies)
-- -----------------------------------------------------------------------------
-- 1. Derive patient_id from authenticated server-side identity for all requests.
-- 2. Add PostgreSQL Row-Level Security only after setting a trusted transaction-local
--    patient/user context and testing connection-pool reset behavior.
-- 3. Qdrant payload filters must include authenticated patient scope, but the API
--    must still authorize before querying Qdrant.
-- 4. Never store payment card numbers, CVV, UPI PINs or other payment credentials.
-- 5. Do not log raw clinical payloads in audit_events.metadata_safe.
-- 6. Add production retention/deletion jobs and backup encryption policies separately.
