# Backend TODO: Phases 1-3

> **Historical planning checklist:** the working backend now goes beyond these
> Phase 1–3 mock requirements. See the root README and `docs/PHASE_STATUS.md` for
> verified implementation status. Unchecked boxes below are not the current
> challenge-readiness checklist.

Owner: M2, Java/Spring Boot + IoT + digital twin developer.
Collaborators: M1 for ML contracts and frontend integration; M3 for healthcare field review.
Roadmap: [Project phases](../docs/PROJECT_PHASES.md).
Status: retained for learning and traceability; implementation is tracked elsewhere.

Practical companion: [HOW_TO.md](HOW_TO.md) explains the steps, tools, sources, review handoffs, and when each phase can be marked done.

## Phase 1: Scope & Contracts

- [ ] Agree the patient identifier with data/ and M1; use a stable synthetic ID such as P001 across records and requests.
- [ ] Define the minimum Patient, EhrProfile, and SensorReading fields with M3: names, types, required/nullable rules, units, and UTC ISO-8601 timestamps.
- [ ] Document the following initial API shapes in docs/API_CONTRACT.md with request, successful response, and failure examples.
- [ ] GET /api/patients: list patient summaries with a documented empty-list result.
- [ ] GET /api/patients/{patientId}: one patient profile; unknown IDs return 404.
- [ ] GET /api/patients/{patientId}/ehr: agreed synthetic EHR fields.
- [ ] GET /api/patients/{patientId}/sensors: historical CGM readings ordered by observation time.
- [ ] POST /api/predictions/{patientId}/refresh: call the internal ML service and return/store the mock prediction.
- [ ] GET /api/predictions/{patientId}/current: return the last result, or a documented no-result state before first refresh.
- [ ] Agree one error envelope, for example code, message, and timestamp; do not return Java stack traces.
- [ ] Agree prediction fields with M1: patient_id, risk_probability, risk_band, prediction_window_minutes, generated_at, prediction_source, model_version, and top_factors.
- [ ] Require prediction_source=mock and model_version=mock-v1 in Phase 3; preserve these through the backend.
- [ ] Agree risk-band boundaries as demo configuration, separate from the clinical event definition.
- [ ] Specify the future MQTT event contract: event_id, patient_id, timestamp, signal, value, unit. Record this only; implementation belongs to Phase 4.
- [ ] Define Phase 3 as a static patient snapshot with historical readings, not a live personalized digital twin.

Acceptance: M1 can implement frontend and FastAPI against the examples; M3 has reviewed field meanings.

## Phase 2: Project Setup

- [x] Create a Maven project in backend/ using Java 21 and a compatible pinned Spring Boot 3 release; include Maven Wrapper.
- [x] Add Spring Web, Validation, Data JPA, H2, Actuator, and the dependencies needed for WebClient.
- [x] Use the existing planned package root com.happyhealth with controller/, dto/, entity/, repository/, service/, client/, and config/.
- [x] Create HappyHealthApplication and environment-driven application configuration.
- [x] Configure port 8080 by default and the ML base URL separately from browser URLs.
- [x] Configure H2 for a reproducible local demo; document whether data resets on restart.
- [x] Add an MlServiceClient using a configured WebClient with finite connection/read timeouts.
- [x] Expose GET /actuator/health; distinguish backend health from dependency connectivity.
- [ ] Verify ML connectivity through a documented internal probe/test against GET /health. Do not claim an overall ready state solely because the Java process started.
- [x] Configure local CORS for the frontend origin, or agree a Vite proxy with M1.
- [x] Add a backend Dockerfile and appropriate ignore rules.
- [x] Lead root docker-compose.yml and .env.example for backend, frontend, and ML, using service-name URLs inside containers.
- [x] Keep MQTT optional and absent from mandatory Phase 2 startup.
- [x] Add a context/health test and document native and Compose startup commands in backend/README.md.
- [x] Coordinate root Git ignore rules for target/, IDE files, H2 runtime files, and local environment files.

Acceptance: Java builds, health is available, H2 starts, and backend reaches FastAPI both locally and in Compose.

## Phase 3: First End-to-End Demo

- [ ] Consume the canonical data/sample/ fixture agreed with data/; seed it once using a repeatable import.
- [ ] Make repeated startup/import idempotent for the fixed patient ID; do not duplicate readings.
- [ ] Implement entities, repositories, DTO mapping, and patient/EHR/sensor endpoints.
- [ ] Keep JSON DTOs separate from persistence entities so API field names remain stable.
- [ ] Return timestamps and glucose units consistently; order chart readings chronologically.
- [ ] Implement the refresh endpoint: load patient + history, construct the ML request, invoke FastAPI, validate/map the response, and store the latest result.
- [ ] Check ML response patient ID matches the requested patient and probability lies between 0 and 1.
- [ ] Retain generated_at, prediction_source, model_version, and the 120-minute horizon in the frontend-facing response.
- [ ] Implement current prediction lookup without inventing a score when no result exists.
- [ ] Map unknown patients to 404, malformed requests to 400, and ML timeout/unavailability to the documented service error.
- [ ] Use a separate clearly indicated previous result if retained after refresh failure; never imply an old score was freshly generated.
- [ ] Add focused JUnit 5/Mockito/MockMvc tests for valid patient retrieval, unknown patient, refresh mapping, and ML failure.
- [ ] Verify the real backend-to-FastAPI HTTP call outside mocked unit tests.
- [ ] Rehearse with M1: patient load, history chart, refresh prediction, stop ML, visible error, restore ML, retry.
- [ ] Record commands, test results, and known limitations in docs/PHASE_STATUS.md.

Planned files: pom.xml, Maven Wrapper, Dockerfile, README.md, src/main/resources/application.yml, Java source and tests.
Dependencies: data/sample/ fixture; M1's FastAPI endpoint and JSON contract.
Handoff: working APIs, sample responses, error behavior, and exact run commands for M1.

## Not Due Before Phase 4

MQTT broker operation, publisher scripts, ingestion, rolling twin updates, real model orchestration, and scenario endpoints.
M2 remains the owner of all MQTT and digital twin implementation when that phase begins.
