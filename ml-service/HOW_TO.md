# How to Build the Python Service Through Phase 3

> **Implementation note (2026-10-09):** This file preserves the original learning
> plan. The deterministic mock has been replaced by the trained, versioned
> 43-feature Logistic Regression artifact served through FastAPI. Use the root
> README, model card, and `docs/PHASE_STATUS.md` as the current source of truth.

Owner: M1, including coordination. Objective: accept a backend request and return an explicit deterministic mock prediction.
M2 owns the calling Java client; M3 reviews clinical meaning.
Roadmap: [Project phases](../docs/PROJECT_PHASES.md).

## How to Use This Guide

Read [TODO.md](TODO.md) for the full checklist; this guide explains how to work through it.
M1 = fullstack + Python ML coordination. M2 = Spring Boot + MQTT + digital twin. M3 = BPharma healthcare lead.
These instructions cover Phases 1-3. The services, fixtures, and commands described below are planned; this document does not claim they already exist or have passed tests.

A folder is ready when its completion checks pass and the named reviewer has checked the handoff. The whole phase is done only when all required folders meet the gate in the project roadmap.
Record evidence and review notes in docs/PHASE_STATUS.md when that file is created. Use Pending, In progress, Ready for review, Blocked, or Done. Leave TODO boxes unchecked until the relevant check passes.
For a dependency question, send the file/revision, a concrete example, expected behavior, actual behavior, and the decision needed. Continue independent work while waiting; do not silently guess a shared field or clinical definition.

## Tools You Will Use

| Tool | Purpose now |
| --- | --- |
| Python 3.11, venv, pip | Isolated Python environment and dependencies |
| FastAPI, Uvicorn | Internal HTTP API and server |
| Pydantic | Validate request/response data |
| Pytest, HTTPX/TestClient | Endpoint tests |
| PowerShell, Git, Docker | Manual requests, version control, container startup |

Pandas, NumPy, Scikit-learn, XGBoost, SHAP, and Joblib are planned for Phase 5. The first mock demo needs no trained artifact.

## Phase 1: Agree a Small Mock Contract

1. Read the ML TODO with M2's backend contract. A mock is a deliberately fixed demonstration response used to connect services before a model exists.
2. Agree POST /ml/predict-glucose-spike input: patient ID, as-of observation time, EHR, and historical readings. Explicitly decide missing/empty-history behavior.
3. Agree output: patient_id, risk_probability, risk_band, prediction_window_minutes, generated_at, prediction_source, model_version, and top_factors.
4. Use source mock, version mock-v1, and horizon 120 minutes. Choose a fixed probability with a matching demo band; label it an integration fixture.
5. Define timestamps/units and validation rules. A reading after the request as-of time must not accidentally become a valid historical feature.
6. Give M2 one complete JSON request/response pair and one invalid example. Record FastAPI validation status behavior and M2's public error mapping.
7. Ask M3 to review the meanings of EHR fields and mock factors. Do not invent clinical thresholds to make the endpoint look complete.

### Ask for Input Before Proceeding

| When | Ask | Send | Continue after |
| --- | --- | --- | --- |
| Before defining Pydantic models | M2 | Request/response examples including empty and invalid cases | Java can supply/consume the shapes |
| Before finalizing clinical field meanings | M3 | Data dictionary and mock explanation text | Meaning and units are reviewed |
| Before changing any response field | M2 | Old/new example and why it changes | Backend mapping and frontend types are coordinated |

While waiting, set up the environment, health route, and tests that do not depend on disputed fields.

### Mark Phase 1 Done for ML When

- [ ] Complete valid/invalid contract examples exist and M2 confirms them.
- [ ] Mock provenance, fixed score/band, and timestamp rules are unambiguous.
- [ ] M3 has reviewed relevant field/factor meanings.

## Phase 2: Run a Health Endpoint

1. Check Python 3.11 is available. Create a local environment following the [Python venv documentation](https://docs.python.org/3.11/library/venv.html).
2. Add pinned compatible FastAPI, Uvicorn, Pydantic, Pytest, and HTTPX dependencies. Pick one authoritative dependency list and document how other manifests stay synchronized.
3. Create app/main.py and a FastAPI application following the [first steps tutorial](https://fastapi.tiangolo.com/tutorial/first-steps/).
4. Add GET /health returning service status and mock mode. Do not require a Joblib file to start.
5. Add a health test. FastAPI's [testing guide](https://fastapi.tiangolo.com/tutorial/testing/) explains using TestClient with HTTPX.
6. Add a Dockerfile and send M2 the port, health path, command, and environment settings. Browser access to ML is unnecessary.
7. Write ml-service/README.md with verified setup/run/test instructions.

Environment creation on Windows:

~~~powershell
Set-Location 'D:\code\happyHealth\ml-service'
py -3.11 -m venv .venv
~~~

After requirements.txt and app/main.py exist, these commands use the environment directly and do not require PowerShell activation:

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
~~~

Use 0.0.0.0 as the bind address in the container so other containers can reach it. Use a separate terminal to check http://localhost:8000/health and, if enabled, FastAPI's local /docs page.

### Ask for Validation

Ask M2 to call your health endpoint through the Java client locally and in Compose. Send a working URL/command and expected response so a network/configuration problem can be separated from an application problem.

### Mark Phase 2 Done for ML When

- [ ] Health tests and startup pass without any trained model.
- [ ] M2 confirms Java-to-ML connectivity in both agreed environments.
- [ ] Dependencies and reproducible commands are recorded.

## Phase 3: Return the Explicit Mock

1. Define Pydantic request/response models using the agreed field shapes. Read [FastAPI request bodies](https://fastapi.tiangolo.com/tutorial/body/) and [Pydantic fields](https://docs.pydantic.dev/latest/concepts/fields/) for validation syntax matching your version.
2. Put response construction in a small service function; let the route validate input and call it.
3. Echo patient_id, return the fixed score/band and mock factors, and generate a current UTC response timestamp. Preserve the historical as-of value separately if the contract includes it.
4. Set prediction_source=mock and model_version=mock-v1 explicitly on every response. Keep the score deterministic; only metadata such as generated_at should change between identical calls.
5. Test valid output, wrong/missing inputs, preserved patient ID, probability bounds, and consistent mock markers.
6. Run tests, then test an actual HTTP request using the reviewed request JSON. Do not assume passing unit tests proves the Java client works.
7. Pair with M2 for refresh, service-stop failure, restart, and retry. Inspect the response seen by the frontend and ensure mock markers survived.

After tests exist:

~~~powershell
Set-Location 'D:\code\happyHealth\ml-service'
.\.venv\Scripts\python.exe -m pytest
~~~

### Ask for Validation

M2 confirms response mapping and failure behavior. M3 confirms displayed mock factors have understandable, non-misleading wording. If validation changes a field type, update the contract with M2 before changing code.

### Mark Phase 3 Done for ML When

- [ ] Valid/invalid endpoint tests pass and the response remains explicitly mock.
- [ ] An actual Spring Boot request reaches FastAPI and returns the expected patient/result.
- [ ] Failure/restart behavior is observed in the dashboard.
- [ ] M2's integration check and M3's relevant wording review are recorded.

Update the ML TODO and shared status. Actual training waits for Phase 5; real-mode inference must never silently substitute a mock.

## Sources and How to Use Them

Official references checked for this guide on 2026-10-05.

| Source | Read for |
| --- | --- |
| [Python 3.11 venv](https://docs.python.org/3.11/library/venv.html) | Isolated environment |
| [FastAPI first steps](https://fastapi.tiangolo.com/tutorial/first-steps/) | Application and routes |
| [FastAPI request body](https://fastapi.tiangolo.com/tutorial/body/) | JSON input models |
| [Pydantic fields](https://docs.pydantic.dev/latest/concepts/fields/) | Field validation |
| [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/) | TestClient, HTTPX, Pytest |
