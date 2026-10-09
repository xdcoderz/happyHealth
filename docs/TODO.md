# Documentation TODO: Phases 1-3

> **Historical planning checklist:** the contracts, scope, data dictionary,
> architecture, acceptance criteria, and submission package now exist. Use
> `PHASE_STATUS.md` and `submission/SUBMISSION_CHECKLIST.md` for current gaps.

Owners: M3 for clinical content; M1 for frontend/ML contracts and demo documentation; M2 for backend/IoT architecture and run configuration.
Roadmap: [Project phases](PROJECT_PHASES.md).
Status: retained for learning and traceability; current deliverables are tracked elsewhere.

Practical companion: [HOW_TO.md](HOW_TO.md) explains the steps, tools, sources, review handoffs, and when each phase can be marked done.

## Phase 1: Scope and Shared Contracts

- [ ] M3 creates CLINICAL_SCOPE.md covering Type 2 Diabetes, intended doctor workflow, two-hour target, and prototype limitations.
- [ ] Review the blueprint's candidate event thresholds and select one explicit label definition before training begins.
- [ ] Record supporting sources and review date for clinical definitions; separate glucose thresholds from probability risk bands.
- [ ] M3 drafts patient-field descriptions and proposed units; M1/M2 complete machine types and validation rules in DATA_DICTIONARY.md.
- [ ] M2 leads API_CONTRACT.md for patient/EHR/history/prediction routes; M1 owns the internal ML request/response section.
- [ ] Include valid JSON examples, required/null rules, error status codes, UTC timestamps, and naming conventions.
- [ ] Explicitly define prediction_source=mock, model_version=mock-v1, generated_at, and prediction_window_minutes=120.
- [ ] M2 creates ARCHITECTURE.md showing browser -> Spring Boot -> FastAPI and separate data import.
- [ ] Mark MQTT/digital twin streaming and model training as future phases, not existing capabilities.
- [ ] M1 sketches the first dashboard and M3 reviews visible clinical terms.
- [ ] Create ACCEPTANCE_CRITERIA.md using the Phase 3 demonstration checklist from PROJECT_PHASES.md.
- [ ] Record agreements and unresolved questions with an owner; all three review their responsibilities.

Acceptance: engineers have enough detail to work independently without inventing incompatible payloads.

## Phase 2: Setup and Reproducibility

- [ ] M1 leads the root README.md: project title, purpose, three roles, folder map, prerequisites, service commands, and current mock status.
- [x] M2 documents Java 21, Maven Wrapper, H2 reset behavior, backend port, ML URL, and backend startup.
- [ ] M1 documents Node/npm compatibility, frontend dependency install/build, and Python 3.11 environment setup.
- [x] M2 documents Compose services and .env.example, distinguishing host URLs from container service names.
- [ ] Record exact chosen dependency versions through manifests/lock files; link to them rather than duplicating drifting version lists.
- [ ] Write a short startup/troubleshooting section for occupied ports, missing runtimes, unavailable ML, and fixture mount paths.
- [ ] M1/M2 add service-specific README files and link them from the root README.
- [ ] Create PHASE_STATUS.md with columns: task/phase, owner, status, evidence, unresolved issue.
- [ ] Record verified startup and health-check commands with actual results; do not mark planned checks as passed.
- [ ] Update TEAM_WORKLOAD.md and stack references if implementation decisions change.

Acceptance: a teammate can start all three services using the documented commands.

## Phase 3: Demo, Review, and Evidence

- [ ] M1 creates DEMO_SCRIPT.md for a short internal Phase 3 walkthrough; the final 20-minute submission video remains Phase 8.
- [ ] Demonstrate startup, patient load, historical CGM chart, prediction refresh, mock indicator, and explanation.
- [ ] M2 documents the actual HTTP chain and the import/reset procedure.
- [ ] M1/M2 demonstrate an unknown patient and an unavailable ML service, including recovery/retry.
- [ ] M3 reviews the dashboard wording, two-hour horizon, synthetic-data notice, and mock explanation.
- [ ] Record that Phase 3 does not demonstrate trained prediction accuracy, live MQTT, or a completed digital twin.
- [ ] Add representative API examples and a dashboard screenshot to the documentation.
- [ ] Record test commands, results, environment, date, and known limitations in PHASE_STATUS.md.
- [ ] Complete the Phase 3 acceptance checklist only after observing the working multi-service demo.
- [ ] Create a follow-on issue list for Phase 4 IoT and Phase 5 ML, preserving the agreed owners.
- [ ] All three review the Phase 3 gate before declaring the milestone complete.

Planned files: CLINICAL_SCOPE.md, DATA_DICTIONARY.md, API_CONTRACT.md, ARCHITECTURE.md, ACCEPTANCE_CRITERIA.md, PHASE_STATUS.md, DEMO_SCRIPT.md, plus the root/service READMEs.
Existing reference documents: PROJECT_BLUEPRINT.md, TEAM_WORKLOAD.md, TECH_STACK_AND_FILE_STRUCTURE.md.
Dependency: evidence from the backend, frontend, ML, and data task lists.

## Checklist Maintenance

- Mark [x] only after the stated result has been verified.
- Keep blocked tasks unchecked and record the dependency/owner in PHASE_STATUS.md.
- Update contracts before changing payloads consumed by another member.
- Use PROJECT_PHASES.md as the authoritative phase numbering when older planning prose differs.
