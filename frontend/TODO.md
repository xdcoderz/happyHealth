# Frontend TODO: Phases 1-3

> **Historical planning checklist:** the working responsive dashboard is now
> implemented and tested. See the root README and `docs/PHASE_STATUS.md` for the
> current status.

Owner: M1, fullstack developer.
Collaborators: M2 for Spring Boot APIs; M3 for clinical labels and demo review.
M1 also owns Python ML service coordination; see [ML TODO](../ml-service/TODO.md).
Roadmap: [Project phases](../docs/PROJECT_PHASES.md).
Status: retained for learning and traceability; implementation is tracked elsewhere.

Practical companion: [HOW_TO.md](HOW_TO.md) explains the steps, tools, sources, review handoffs, and when each phase can be marked done.

## Phase 1: Scope & Contracts

- [ ] Sketch a compact doctor dashboard: patient selection/summary, historical glucose chart, prediction result, and refresh action.
- [ ] Limit the first demo to one synthetic patient; support a patient-list response without building cohort analytics.
- [ ] Agree all required backend fields, units, loading behavior, and error responses with M2.
- [ ] Define TypeScript shapes from docs/API_CONTRACT.md rather than inventing frontend-only payloads.
- [ ] Ask M3 to review patient labels, glucose units, risk-band wording, and the two-hour horizon.
- [ ] Plan a persistent "Mock prediction" indicator and mark explanation factors as demo text.
- [ ] Define separate states for initial load, no patients, no readings, no prediction yet, fetching prediction, and request failure.
- [ ] Define how generated_at is displayed and how an old result is identified after a failed refresh.
- [ ] Agree frontend -> Spring Boot only; no browser requests to FastAPI or MQTT.
- [ ] Reserve live twin views and what-if controls for later phases.

Acceptance: the dashboard sketch and API field list are reviewed by M2/M3.

## Phase 2: Project Setup

- [ ] Initialize React 18 + TypeScript + Vite and select compatible pinned versions.
- [ ] Configure Tailwind CSS, Recharts, Axios, and Lucide React; commit the package lock.
- [ ] Use src/api/, src/components/, src/pages/, src/types/, and src/utils/ following the existing structure plan.
- [ ] Add a shared Axios client with an environment-configured backend base URL and finite timeout.
- [ ] Agree a local Vite proxy or backend CORS settings with M2; document the selected approach.
- [ ] Use frontend port 5173 by default; document alternatives if occupied.
- [ ] Define scripts for development, production build, and tests; add a compatible test runner for React Testing Library.
- [ ] Create a minimal application shell with usable headings, responsive layout, and keyboard-accessible controls.
- [ ] Add a frontend Dockerfile and Docker ignore rules; supply its Compose configuration to M2.
- [ ] Ensure browser URLs use localhost or a browser-accessible proxy, never Compose-only hostnames.
- [ ] Document setup and environment variables in frontend/README.md; keep secrets out of Vite environment variables.
- [ ] Verify the app renders and a configured backend health request works.

Acceptance: a fresh dependency install and production build succeed; app and API configuration work locally and in Compose.

## Phase 3: First End-to-End Demo

- [ ] Implement patient API functions and types for list, detail, EHR, sensor history, current prediction, and refresh.
- [ ] Fetch the canonical synthetic patient through Spring Boot; do not hardcode a separate frontend patient.
- [ ] Render demographics and selected EHR values with correct units and sensible missing-value placeholders.
- [ ] Plot historical CGM readings with Recharts; order timestamps and show mg/dL on the axis/tooltip.
- [ ] Keep missing data distinct from zero; never create trend values to fill an empty history.
- [ ] Provide a refresh action that calls Spring Boot's prediction refresh endpoint and prevents duplicate in-flight clicks.
- [ ] Display returned risk probability as a percentage, risk band, prediction horizon, and generated timestamp.
- [ ] Preserve and visibly render prediction_source=mock; treat returned factors as mock explanation text.
- [ ] Show risk text alongside color so the result is understandable without color alone.
- [ ] Add loading, empty, no-result, unavailable, and retry states.
- [ ] Prevent stale responses from replacing a newer patient selection/result.
- [ ] If retaining a previous result on failure, label it as a previous result and show refresh failure separately.
- [ ] Add React Testing Library checks for patient display, mock labelling, refresh interaction, and unavailable prediction state.
- [ ] Verify browser requests go only to Spring Boot and inspect the actual end-to-end response.
- [ ] Check desktop and narrow/mobile layouts for chart sizing, readable text, and non-overlapping controls.
- [ ] Review visible text with M3 and capture a Phase 3 screenshot plus run evidence in docs/PHASE_STATUS.md.

Planned files: package.json, lock file, Vite/TypeScript/Tailwind configuration, Dockerfile, README.md, src/ application and tests.
Dependencies: M2's API endpoints and M1's separate ML mock service.
Handoff: reproducible doctor demo with labelled mock output and clear failure states.

## Deferred

Live sensor refresh, complete digital twin timeline, computed SHAP charts, scenario simulation, export, and dashboard polish beyond the first working flow.
