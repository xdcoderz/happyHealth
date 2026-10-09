# How to Build the Backend Through Phase 3

> **Implementation note (2026-10-09):** This file preserves the original learning
> plan. The Spring Boot digital twin, MQTT ingestion, H2 state, FastAPI integration,
> and automated tests are now implemented. Use the root README, API contract, and
> `docs/PHASE_STATUS.md` as the current source of truth.

Owner: M2. Objective: serve one synthetic patient and connect the dashboard to the Python mock prediction service.
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
| Java 21, Spring Boot 3, Maven Wrapper | Build and run the main API |
| Spring Web, Validation, Data JPA, H2 | HTTP routes, input checks, patient storage |
| WebClient, Actuator | Call FastAPI; expose backend health |
| JUnit 5, Mockito, MockMvc | Check backend behavior and failures |
| PowerShell, Git, Docker Compose | Try requests, track changes, run services together |

Mosquitto, Spring Integration MQTT, and Python Paho belong to Phase 4. You still own them; they do not block the Phase 3 mock demo.

## Phase 1: Agree What Goes In and Out

1. Read the blueprint and this folder's TODO. Write down the routes required for the first demo: patient list/detail, EHR, sensor history, current prediction, and prediction refresh.
2. In docs/API_CONTRACT.md, give every route one successful JSON example and its error behavior. A contract is simply the agreement about the fields two programs exchange.
3. Use one patient ID, such as P001, everywhere. Agree UTC timestamps and glucose units with M1/M3. Write missing values as the agreed null/absence representation, not zero.
4. With M1, draw the request journey: browser -> backend -> ML -> backend -> browser. Agree the ML request and response before implementing the client.
5. Keep patient observation time separate from prediction generation time. The fixture is historical; generating a response today must not make its readings appear live.
6. Decide the no-prediction-yet response, error envelope, timeouts, and how an old result is displayed after failed refresh.
7. Record the future sensor-event shape in the architecture notes. Do not implement MQTT yet.

### Ask for Input Before Proceeding

| When | Ask | Send | Continue after |
| --- | --- | --- | --- |
| Before finalizing fields or units | M3 | Data dictionary with examples and unclear meanings highlighted | Field meanings and proposed values are reviewed |
| Before implementing MlServiceClient | M1 | Exact request/response JSON, status codes, and timeout proposal | M1 confirms FastAPI will accept/return those shapes |
| Before choosing public response names | M1 | Patient and prediction examples | Frontend types and backend DTOs agree |

While waiting, prepare package directories, route outlines, and test cases that do not depend on the disputed fields.

### Mark Phase 1 Done for Backend When

- [ ] Every initial route has request/response/error examples.
- [ ] M1 has confirmed the API and ML shapes; M3 has reviewed units and field meanings.
- [ ] No unresolved contract question blocks coding; review notes are recorded.

## Phase 2: Start a Small Working Service

1. Check Java with java -version. Create a Maven/Java project using Spring Initializr with Java 21 and an explicitly chosen Spring Boot 3 release. Do not accept a different major version just because it is the default. If Boot 3 is not offered, agree a supported version path with M1 and record it before generating. See the [official REST guide](https://spring.io/guides/gs/rest-service/).
2. Generate into a temporary location, then bring project files into this folder without overwriting TODO.md or HOW_TO.md. Keep the package root com.happyhealth and the Maven Wrapper.
3. Add Web, Validation, Data JPA, H2, Actuator, and compatible WebClient dependencies. With Boot 3's Spring MVC application, use WebClient as the outgoing HTTP client; this does not require redesigning all controllers as reactive.
4. Add application configuration: backend port 8080, H2 connection/reset policy, and an environment-configured ML URL. Learn repository/entity basics from the [JPA guide](https://spring.io/guides/gs/accessing-data-jpa/).
5. Create the ML client and give it finite connection/response timeouts. Follow the [WebClient reference](https://docs.spring.io/spring-framework/reference/web/webflux-webclient.html) for your selected Spring version.
6. Expose Actuator health and verify it. Check ML health through the Java client as a separate connectivity check; a successful PowerShell request alone does not prove Java-to-ML connectivity.
7. Add a Dockerfile. Collect M1's frontend and ML container settings, then assemble root Docker Compose configuration using the [Compose quickstart](https://docs.docker.com/compose/gettingstarted/).
8. Write backend/README.md with install, run, test, and configuration instructions. Add a focused health/context test.

Run these only after the Maven project and health endpoint exist, from a backend PowerShell terminal:

~~~powershell
Set-Location 'D:\code\happyHealth\backend'
.\mvnw.cmd test
.\mvnw.cmd spring-boot:run
~~~

Use another terminal while the server runs:

~~~powershell
Invoke-RestMethod -Uri 'http://localhost:8080/actuator/health'
~~~

For local processes, the ML URL can be http://localhost:8000. Inside Compose, use the actual ML service name, for example http://ml-service:8000. Inside a container, localhost means that same container.

### Ask for Validation

Ask M1 for the ML startup command, port, health path, and an observed health response before testing connectivity. Share your backend URL and proxy/CORS settings so M1 can test browser access.
If a request fails, send the URL, status, and relevant error text; do not send environment secrets.

### Mark Phase 2 Done for Backend When

- [ ] Build/tests pass, backend health succeeds, and H2 initializes.
- [ ] The backend's ML health call works locally and in Compose.
- [ ] M1 can reach the backend from the frontend environment.
- [ ] Run/configuration instructions and observed results are recorded.

## Phase 3: Connect One Patient to One Mock Prediction

1. Import the canonical data/sample/demo_patient_001.json fixture. Give patient/readings stable keys so importing twice does not duplicate them.
2. Build in this order: entities/repositories -> services -> DTOs -> controllers. DTOs are the public JSON shapes; avoid exposing database entities directly.
3. Implement patient, EHR, and ordered sensor-history routes. Compare their output with the fixture before connecting the UI.
4. Implement refresh: find patient, collect EHR/history, construct the agreed ML request, call FastAPI, check the returned patient ID/score, and store the latest result.
5. Return prediction_source=mock, model_version=mock-v1, generated_at, and the 120-minute horizon unchanged. Implement current-result lookup and its no-result state.
6. Add tests for valid patient, unknown patient, correct prediction mapping, and ML failure. Agree public error codes with M1; do not leak stack traces.
7. With M1, run the real HTTP chain. Temporarily stop ML, attempt refresh, restart ML, and retry. Confirm failure is visible and no new score is fabricated.
8. Give M3 sample patient output and the dashboard to review. Record test results and review notes.

After the routes exist, these are simple manual checks:

~~~powershell
Invoke-RestMethod -Uri 'http://localhost:8080/api/patients/P001'
Invoke-RestMethod -Method Post -Uri 'http://localhost:8080/api/predictions/P001/refresh'
~~~

### Ask for Validation

Ask M1 to confirm the ML response matches the contract before completing refresh mapping, and then to demonstrate frontend integration. Ask M3 to review any changed field meaning or unit before changing fixture/API interpretation.

### Mark Phase 3 Done for Backend When

- [ ] Seeding is repeatable; patient/history output matches the reviewed fixture.
- [ ] Automated behavior tests and the actual FastAPI round trip pass.
- [ ] M1 confirms dashboard refresh and unavailable-service handling.
- [ ] M3's relevant field review and the integration evidence are recorded.

Then mark the corresponding TODO items and hand the API examples/run instructions to M1. Whole Phase 3 still requires the shared demonstration checklist.

## Sources and How to Use Them

Official references checked for this guide on 2026-10-05. Follow docs matching pinned dependency versions; a newer guide is not permission to change the agreed stack.

| Source | Read for |
| --- | --- |
| [Spring REST guide](https://spring.io/guides/gs/rest-service/) | Initializr, controller, and Maven workflow |
| [Spring Data JPA guide](https://spring.io/guides/gs/accessing-data-jpa/) | Entities and repositories |
| [Spring validation](https://docs.spring.io/spring-boot/reference/io/validation.html) | Input constraints |
| [WebClient](https://docs.spring.io/spring-framework/reference/web/webflux-webclient.html) | Outgoing HTTP requests |
| [Docker Compose](https://docs.docker.com/compose/gettingstarted/) | Multi-service local startup |
