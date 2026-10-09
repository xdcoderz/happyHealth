# Engineering Status

The challenge's “Phase 1” is the complete prototype submission. The stages below
are internal engineering checkpoints only.

| Internal stage | Status | Evidence or next gate |
| --- | --- | --- |
| Scope and contracts | Ready for review | API, data, architecture, acceptance, and safety documents exist; clinical review pending |
| Project setup | Complete | Five-service Docker Compose definition and local run paths are documented |
| Synthetic end-to-end demo | Complete | Canonical fictional patient drives a live API and dashboard prediction |
| Simulated stream and digital twin | Complete | MQTT publisher, ordered/idempotent ingestion, H2 state, and backend tests exist |
| ML development | Ready for review | Reproducible Logistic Regression baseline; clinical target review pending |
| Live prediction integration | Complete | FastAPI loads the versioned 43-feature artifact; Spring Boot returns model results or an explicit unavailable state |
| Dashboard | Complete | Responsive doctor view, timeline, risk, model factors, loading, and failure states are implemented |
| Submission package | In progress | Licence, architecture, and presentation files are ready; team details, clinical review, video, and clean-computer Docker check remain |

## Review record

| Review | Owner | Date | Status | Notes |
| --- | --- | --- | --- | --- |
| Clinical target and wording | Healthcare-domain lead | — | Pending | Record reviewer name and corrections |
| API and feature availability | Fullstack + backend owners | 2026-10-09 | Verified | Automated Python, Java, and React tests plus a local live integration check |
| Submission compliance | Team leader | — | Pending | Confirm team details, public access, folder name, and links |
