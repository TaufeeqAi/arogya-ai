-- Aarogya additional patient-scope integrity constraints
-- Apply after 001_initial_schema.sql in a migration transaction.
-- These composite keys prevent cross-patient relationships even if application
-- code accidentally pairs a resource ID with another patient's ID.

BEGIN;

-- Parent composite keys.
ALTER TABLE health_documents ADD CONSTRAINT uq_health_documents_id_patient UNIQUE (id, patient_id);
ALTER TABLE document_extractions ADD CONSTRAINT uq_document_extractions_id_patient UNIQUE (id, patient_id);
ALTER TABLE encounters ADD CONSTRAINT uq_encounters_id_patient UNIQUE (id, patient_id);
ALTER TABLE care_plans ADD CONSTRAINT uq_care_plans_id_patient UNIQUE (id, patient_id);
ALTER TABLE medication_records ADD CONSTRAINT uq_medication_records_id_patient UNIQUE (id, patient_id);
ALTER TABLE medication_schedules ADD CONSTRAINT uq_medication_schedules_id_patient UNIQUE (id, patient_id);
ALTER TABLE reminder_occurrences ADD CONSTRAINT uq_reminder_occurrences_id_patient UNIQUE (id, patient_id);
ALTER TABLE health_observations ADD CONSTRAINT uq_health_observations_id_patient UNIQUE (id, patient_id);
ALTER TABLE refill_requests ADD CONSTRAINT uq_refill_requests_id_patient UNIQUE (id, patient_id);
ALTER TABLE consent_grants ADD CONSTRAINT uq_consent_grants_id_patient UNIQUE (id, patient_id);
ALTER TABLE agent_threads ADD CONSTRAINT uq_agent_threads_id_patient UNIQUE (id, patient_id);
ALTER TABLE workflow_runs ADD CONSTRAINT uq_workflow_runs_id_patient UNIQUE (id, patient_id);

-- Documents/extractions/observations.
ALTER TABLE document_extractions
    ADD CONSTRAINT fk_extractions_document_patient
    FOREIGN KEY (document_id, patient_id)
    REFERENCES health_documents(id, patient_id);

ALTER TABLE health_observations
    ADD CONSTRAINT fk_observations_document_patient
    FOREIGN KEY (document_id, patient_id)
    REFERENCES health_documents(id, patient_id);

ALTER TABLE health_observations
    ADD CONSTRAINT fk_observations_extraction_patient
    FOREIGN KEY (extraction_id, patient_id)
    REFERENCES document_extractions(id, patient_id);

-- Encounters, conditions, allergies and care plans.
ALTER TABLE encounters
    ADD CONSTRAINT fk_encounters_document_patient
    FOREIGN KEY (source_document_id, patient_id)
    REFERENCES health_documents(id, patient_id);

ALTER TABLE condition_records
    ADD CONSTRAINT fk_conditions_encounter_patient
    FOREIGN KEY (encounter_id, patient_id)
    REFERENCES encounters(id, patient_id);

ALTER TABLE condition_records
    ADD CONSTRAINT fk_conditions_document_patient
    FOREIGN KEY (source_document_id, patient_id)
    REFERENCES health_documents(id, patient_id);

ALTER TABLE allergy_records
    ADD CONSTRAINT fk_allergies_document_patient
    FOREIGN KEY (source_document_id, patient_id)
    REFERENCES health_documents(id, patient_id);

ALTER TABLE care_plans
    ADD CONSTRAINT fk_care_plans_encounter_patient
    FOREIGN KEY (encounter_id, patient_id)
    REFERENCES encounters(id, patient_id);

ALTER TABLE care_plans
    ADD CONSTRAINT fk_care_plans_document_patient
    FOREIGN KEY (source_document_id, patient_id)
    REFERENCES health_documents(id, patient_id);

ALTER TABLE follow_up_tasks
    ADD CONSTRAINT fk_followups_care_plan_patient
    FOREIGN KEY (care_plan_id, patient_id)
    REFERENCES care_plans(id, patient_id);

ALTER TABLE follow_up_tasks
    ADD CONSTRAINT fk_followups_document_patient
    FOREIGN KEY (source_document_id, patient_id)
    REFERENCES health_documents(id, patient_id);

-- Medication records and schedules.
ALTER TABLE medication_records
    ADD CONSTRAINT fk_medication_document_patient
    FOREIGN KEY (source_document_id, patient_id)
    REFERENCES health_documents(id, patient_id);

ALTER TABLE medication_records
    ADD CONSTRAINT fk_medication_encounter_patient
    FOREIGN KEY (encounter_id, patient_id)
    REFERENCES encounters(id, patient_id);

ALTER TABLE medication_schedules
    ADD CONSTRAINT fk_schedules_medication_patient
    FOREIGN KEY (medication_record_id, patient_id)
    REFERENCES medication_records(id, patient_id);

ALTER TABLE medication_schedules
    ADD CONSTRAINT fk_schedules_instruction_document_patient
    FOREIGN KEY (instruction_source_document_id, patient_id)
    REFERENCES health_documents(id, patient_id);

ALTER TABLE reminder_occurrences
    ADD CONSTRAINT fk_occurrences_schedule_patient
    FOREIGN KEY (medication_schedule_id, patient_id)
    REFERENCES medication_schedules(id, patient_id);

ALTER TABLE adherence_events
    ADD CONSTRAINT fk_adherence_schedule_patient
    FOREIGN KEY (medication_schedule_id, patient_id)
    REFERENCES medication_schedules(id, patient_id);

ALTER TABLE adherence_events
    ADD CONSTRAINT fk_adherence_occurrence_patient
    FOREIGN KEY (reminder_occurrence_id, patient_id)
    REFERENCES reminder_occurrences(id, patient_id);

-- Refill and payment records.
ALTER TABLE refill_requests
    ADD CONSTRAINT fk_refill_medication_patient
    FOREIGN KEY (medication_record_id, patient_id)
    REFERENCES medication_records(id, patient_id);

ALTER TABLE refill_requests
    ADD CONSTRAINT fk_refill_prescription_document_patient
    FOREIGN KEY (prescription_document_id, patient_id)
    REFERENCES health_documents(id, patient_id);

ALTER TABLE pharmacy_quotes ADD COLUMN patient_id UUID;
UPDATE pharmacy_quotes q
SET patient_id = r.patient_id
FROM refill_requests r
WHERE r.id = q.refill_request_id;
ALTER TABLE pharmacy_quotes ALTER COLUMN patient_id SET NOT NULL;
ALTER TABLE pharmacy_quotes
    ADD CONSTRAINT fk_pharmacy_quote_request_patient
    FOREIGN KEY (refill_request_id, patient_id)
    REFERENCES refill_requests(id, patient_id);
ALTER TABLE pharmacy_quotes
    ADD CONSTRAINT uq_pharmacy_quotes_id_patient UNIQUE (id, patient_id);

ALTER TABLE refill_orders ADD COLUMN patient_id UUID;
UPDATE refill_orders o
SET patient_id = r.patient_id
FROM refill_requests r
WHERE r.id = o.refill_request_id;
ALTER TABLE refill_orders ALTER COLUMN patient_id SET NOT NULL;
ALTER TABLE refill_orders
    ADD CONSTRAINT fk_refill_order_request_patient
    FOREIGN KEY (refill_request_id, patient_id)
    REFERENCES refill_requests(id, patient_id);
ALTER TABLE refill_orders
    ADD CONSTRAINT fk_refill_order_quote_patient
    FOREIGN KEY (pharmacy_quote_id, patient_id)
    REFERENCES pharmacy_quotes(id, patient_id);
ALTER TABLE refill_orders
    ADD CONSTRAINT uq_refill_orders_id_patient UNIQUE (id, patient_id);

ALTER TABLE payment_attempts
    ADD CONSTRAINT fk_payment_order_patient
    FOREIGN KEY (refill_order_id, patient_id)
    REFERENCES refill_orders(id, patient_id);

-- Consent and sharing.
ALTER TABLE record_share_events
    ADD CONSTRAINT fk_share_consent_patient
    FOREIGN KEY (consent_grant_id, patient_id)
    REFERENCES consent_grants(id, patient_id);

ALTER TABLE record_share_events
    ADD CONSTRAINT fk_share_document_patient
    FOREIGN KEY (document_id, patient_id)
    REFERENCES health_documents(id, patient_id);

ALTER TABLE record_share_events
    ADD CONSTRAINT fk_share_observation_patient
    FOREIGN KEY (observation_id, patient_id)
    REFERENCES health_observations(id, patient_id);

-- Agent workflow scope.
ALTER TABLE workflow_runs
    ADD CONSTRAINT fk_workflow_thread_patient
    FOREIGN KEY (agent_thread_id, patient_id)
    REFERENCES agent_threads(id, patient_id);

ALTER TABLE approval_requests
    ADD CONSTRAINT fk_approval_workflow_patient
    FOREIGN KEY (workflow_run_id, patient_id)
    REFERENCES workflow_runs(id, patient_id);

COMMIT;
