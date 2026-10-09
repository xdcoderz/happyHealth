# How to Build the Frontend Through Phase 3

> **Implementation note (2026-10-09):** This file preserves the original learning
> plan. The responsive React doctor dashboard and its loading, failure, timeline,
> and live-prediction states are now implemented. Use the root README and
> `docs/PHASE_STATUS.md` as the current source of truth.

Owner: M1. Objective: show a synthetic patient, historical glucose chart, and clearly labelled mock prediction from Spring Boot.
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
| React 18, TypeScript, Vite | Components, API types, development/build |
| Tailwind CSS, Lucide React | Styling and familiar control icons |
| Axios | A shared HTTP client for Spring Boot |
| Recharts | Glucose history chart |
| React Testing Library, compatible Vitest + DOM test environment | Component and interaction tests |
| Browser developer tools, Git, Docker | Inspect requests/layout, track changes, run container |

Vitest is a proposed lightweight runner for the existing React Testing Library plan; record a compatible version when setting up. Match Node to the chosen Vite/Vitest versions.

## Phase 1: Draw the First Screen and Agree Its Data

1. Read the frontend TODO. Sketch one usable screen with patient summary, chart, mock risk result, explanation, and refresh action.
2. For each visible value, list its API field and unit in docs/API_CONTRACT.md. For example, the displayed percentage comes from risk_probability multiplied by 100.
3. Ask M2 for JSON examples covering patient, EHR, history, prediction, no-result, and error states. Agree the ID and timestamp formats before writing TypeScript types.
4. Ask M3 to review labels, units, and the phrase "Mock prediction". Record that a fixed demo score is not an assessed patient risk.
5. Draw loading, empty, unavailable, and retry states next to the main sketch. Decide what happens if refresh fails while an earlier result is visible.
6. Identify the smallest Phase 3 screen. Leave live twin updates and what-if interactions for later phases.

### Ask for Input Before Proceeding

| When | Ask | Send | Continue after |
| --- | --- | --- | --- |
| Before implementing API types | M2 | Required field list and example screen | Response shapes and status codes are agreed |
| Before finalizing patient labels | M3 | Screen sketch with units and mock wording | Clinical wording is reviewed |
| When a needed field is missing | M2, with M3 for clinical meaning | Exact UI use and proposed field | Contract is updated or UI scope is reduced |

While waiting, build the static layout and state components with clearly labelled development fixtures.

### Mark Phase 1 Done for Frontend When

- [ ] Screen/state sketch exists and maps to agreed API examples.
- [ ] M2 confirms the data contract; M3 reviews wording.
- [ ] No unresolved field decision blocks integration.

## Phase 2: Set Up the App and API Connection

1. Check node --version and npm --version. Select compatible Vite and Node versions using the [Vite guide](https://vite.dev/guide/); record the choice.
2. Generate a React/TypeScript starter in a temporary directory, then copy its application/configuration files here while preserving TODO.md and HOW_TO.md. Avoid generator options that clear this nonempty folder.
3. Set React/react-dom to compatible React 18 versions and align their TypeScript definitions. Do not assume a current starter still uses React 18. Use the [React TypeScript guide](https://react.dev/learn/typescript).
4. Add Axios, Recharts, Lucide React, and Tailwind. The existing structure proposes Tailwind/PostCSS config files; use the [Tailwind v3 Vite recipe](https://v3.tailwindcss.com/docs/guides/vite) if selecting v3. If selecting another major, explicitly update the setup instructions rather than mixing recipes.
5. Create src/api/client.ts with a single backend base URL and timeout; Axios supports a reusable [client instance](https://axios-http.com/docs/instance). Never place private credentials in browser configuration.
6. Agree either a Vite proxy or backend CORS with M2. The browser must use a browser-reachable address; Docker service names such as backend are for containers, not the user's browser.
7. Add a minimal app shell and configure test/build scripts, including the DOM environment needed for React Testing Library.
8. Supply the frontend Dockerfile/run settings to M2. Record installation/startup steps and commit the package lock.

After package.json and the lock file exist:

~~~powershell
Set-Location 'D:\code\happyHealth\frontend'
npm ci
npm run build
npm run dev
~~~

Use npm install for the first dependency setup that creates/updates the lock file. Use npm ci for repeatable installs after that. Configure the test script before using npm run test -- --run.

### Ask for Validation

Send M2 the frontend origin (normally http://localhost:5173), backend base URL, and any browser error. Ask M2 to confirm the proxy/CORS path works from the browser, not just from a terminal.

### Mark Phase 2 Done for Frontend When

- [ ] Repeatable install/build passes, app renders, and test setup runs.
- [ ] A real browser request reaches backend health successfully.
- [ ] M2 has checked Compose routing; startup/configuration instructions are recorded.

## Phase 3: Replace Screen Fixtures with Backend Data

1. Add typed API functions for patient list/detail, EHR, history, current prediction, and refresh. Keep the base URL in the shared client.
2. Load P001 through Spring Boot. Remove screen-level hardcoded patient values from the integrated demo.
3. Render EHR values and a Recharts glucose-history chart. Label mg/dL and time; preserve missing readings as missing. Refer to [Recharts TypeScript support](https://recharts.github.io/guide/typescript/).
4. Add refresh. While it runs, disable repeated clicks; show the returned mock score, band, horizon, timestamp, and mock factors.
5. Show the returned prediction_source clearly. Historical readings remain historical even if a new response timestamp is generated.
6. Implement error/empty/no-result states and retry. If showing an earlier result after failure, label it as previous. Ignore/cancel stale responses after patient changes.
7. Write user-visible behavior tests: correct patient shown, mock label present, refresh requests data, unavailable service gives a clear error. Use the [Testing Library introduction](https://testing-library.com/docs/react-testing-library/intro/) and [Vitest setup guide](https://vitest.dev/guide/).
8. Check the browser Network panel: product requests go to Spring Boot, never directly to FastAPI or MQTT. Test a narrow viewport and keyboard navigation.
9. With M2, stop/restart ML and check failure/recovery. Show M3 the rendered dashboard, not just a list of strings.

### Ask for Validation

Ask M2 when a status/field differs from the approved contract; send the actual response and expected example. Ask M3 to review clinical labels, units, historical-data wording, and mock explanation before marking the screen complete.

### Mark Phase 3 Done for Frontend When

- [ ] Patient and chart values match the reviewed data received through Spring Boot.
- [ ] Refresh traverses all three services; mock identity is visible.
- [ ] Interaction tests, production build, failure/retry, and layout checks pass.
- [ ] M2 confirms the integration and M3 records the wording review.

Record evidence, mark matching TODO boxes, and contribute the screenshot/demo steps to docs/. M1's separate ml-service tasks must also pass before the full team gate closes.

## Sources and How to Use Them

Official references checked for this guide on 2026-10-05; match examples to chosen versions.

| Source | Read for |
| --- | --- |
| [React with TypeScript](https://react.dev/learn/typescript) | Typed props and components |
| [Vite](https://vite.dev/guide/) | Runtime requirements and starter setup |
| [Tailwind v3 + Vite](https://v3.tailwindcss.com/docs/guides/vite) | Version-specific styling configuration |
| [Axios instance](https://axios-http.com/docs/instance) | Shared backend client |
| [Recharts TypeScript](https://recharts.github.io/guide/typescript/) | Typed charts |
| [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/) and [Vitest](https://vitest.dev/guide/) | Behavior tests and runner setup |
