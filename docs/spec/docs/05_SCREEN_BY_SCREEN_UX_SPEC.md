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
