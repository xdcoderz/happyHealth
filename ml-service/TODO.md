# Python ML Service TODO: Phases 1-3

> **Historical planning checklist:** the mock service has been replaced by the
> trained, versioned 43-feature model API. See the model card, root README, and
> `docs/PHASE_STATUS.md` for the current status.

Owner: M1, fullstack developer and ML service coordinator.
Collaborators: M2 for Spring Boot client integration; M3 for clinical target/field review.
M2 consumes this service but does not own its coordination.
Roadmap: [Project phases](../docs/PROJECT_PHASES.md).
Status: retained for learning and traceability; implementation is tracked elsewhere.

Practical companion: [HOW_TO.md](HOW_TO.md) explains the steps, tools, sources, review handoffs, and when each phase can be marked done.

## Phase 1: Scope & Contracts

- [ ] Define GET /health and POST /ml/predict-glucose-spike with M2 in docs/API_CONTRACT.md.
- [ ] Agree a request carrying patient_id, observation/as-of time, selected EHR fields, and historical sensor readings.
- [ ] Explicitly define units, timestamps, required fields, nullability, minimum history, and whether empty history is accepted for the mock.
- [ ] Reject future observations relative to the agreed as-of time, or document the agreed validation behavior.
- [ ] Agree response fields: patient_id, risk_probability, risk_band, prediction_window_minutes, generated_at, prediction_source, model_version, and top_factors.
- [ ] Use prediction_source=mock, model_version=mock-v1, and prediction_window_minutes=120 for Phase 3.
- [ ] Set a deterministic fixture probability and matching demo risk band; this is not a trained or calibrated probability.
- [ ] Agree top_factors as a simple list of labelled mock factor strings initially; defer a computed SHAP schema until needed.
- [ ] Specify 422 behavior for invalid FastAPI requests and how M2 maps internal errors to public API errors.
- [ ] Let M3 review event definition and terminology; do not ask M3 to implement statistical evaluation or Python code.
- [ ] Record that no standalone explanation endpoint or model artifact is required for Phase 3.

Acceptance: M2 can implement the WebClient using a complete valid request, response, and error example.

## Phase 2: Project Setup

- [ ] Initialize the service for Python 3.11 with a reproducible virtual environment and pinned dependencies.
- [ ] Add FastAPI, Uvicorn, Pydantic, Pytest, and compatible HTTP test tooling.
- [ ] Use app/main.py, app/api/, app/schemas/, app/services/, and tests/ as the minimal layout.
- [ ] Keep pyproject.toml and requirements/dependency files consistent; document the authoritative install command.
- [ ] Add GET /health with service status and explicit mock mode; startup must not depend on a missing trained model.
- [ ] Configure host/port and environment settings; use port 8000 by default.
- [ ] Add a Dockerfile and ignore virtual environments, caches, and future large training outputs.
- [ ] Supply ML service configuration to M2 for root Docker Compose.
- [ ] Keep the service internal to Spring Boot in the product flow; the browser does not need ML CORS access.
- [ ] Add a health test and verify local/container startup.
- [ ] Write ml-service/README.md with prerequisites, install, run, test, and sample health commands.

Acceptance: GET /health succeeds and M2's backend can reach it using the configured URL.

## Phase 3: Deterministic Mock Inference

- [ ] Implement Pydantic request/response schemas matching the approved contract.
- [ ] Implement POST /ml/predict-glucose-spike as an explicit deterministic mock service.
- [ ] Echo the request patient ID and return a current UTC generated_at timestamp.
- [ ] Return the agreed fixed probability and matching band without pretending to run a model.
- [ ] Include the 120-minute horizon, prediction_source=mock, model_version=mock-v1, and mock factors on every successful response.
- [ ] Validate numeric types, field presence, patient IDs, units, and timestamps to the extent defined in the Phase 1 contract.
- [ ] Keep response construction separate from the route so actual inference can replace it in Phase 6.
- [ ] Do not silently fall back to a mock when a real mode is later selected; mode must remain explicit.
- [ ] Write Pytest checks for valid response, preserved patient identity, deterministic score, mock provenance, and malformed request.
- [ ] Exchange the canonical request/response example with M2 and verify the real HTTP round trip.
- [ ] Exercise service-stop/restart with M2 so unavailable ML is visible in the frontend.
- [ ] Document mock limitations and evidence in docs/PHASE_STATUS.md.

Planned files: dependency manifests, Dockerfile, README.md, app/main.py, API/schema/service modules, tests/.
Dependencies: docs/API_CONTRACT.md and data/sample/ fixture.
Handoff: stable mock endpoint and validation examples for M2; truthful display fields for frontend/.

## Deferred to Phase 5 and Later

Pandas/NumPy feature processing, Scikit-learn baseline, XGBoost training, patient/time splits, evaluation, SHAP computation, Joblib artifacts, and real inference.
Do not spend Phase 3 installing or training a model that the integration demo does not yet need.
