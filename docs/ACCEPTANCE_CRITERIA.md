# Prototype Acceptance Criteria

The prototype is ready for the challenge demonstration only when every required
item below is evidenced.

## Data and safety

- [ ] The visible patient is labelled synthetic and contains no real participant row.
- [ ] Static clinical fields and dynamic CGM readings both reach the prediction request.
- [ ] Units and timestamps match the data dictionary.
- [ ] Raw and processed research participant files remain excluded from Git.
- [ ] Dataset and code licences are documented.
- [ ] The healthcare-domain lead records clinical wording review.

## Model service

- [ ] FastAPI reports a loaded, versioned model.
- [ ] Live feature calculation matches the training feature schema.
- [ ] Missing history produces `insufficient_data`, not an invented score.
- [ ] Future outcome fields are absent from inference inputs.
- [ ] The response includes a 120-minute window and research-use warning.

## Digital twin and simulated stream

- [ ] The canonical synthetic patient loads exactly once.
- [ ] A new CGM event updates the correct patient.
- [ ] Duplicate event IDs do not create duplicate readings.
- [ ] Out-of-order readings do not replace the newest state.
- [ ] Model unavailability remains visible through Spring Boot and React.

## Dashboard

- [ ] The doctor view shows static clinical context and recent CGM history.
- [ ] It shows prediction status, probability when available, model version, and timestamp.
- [ ] It distinguishes synthetic data and research output from clinical advice.
- [ ] Loading, unknown-patient, insufficient-data, stale-data, and service-error states are readable.
- [ ] The browser communicates only with Spring Boot.

## Reproducibility and submission

- [ ] One documented command starts the complete prototype from a fresh checkout.
- [ ] Automated Python, Java, and frontend checks pass.
- [ ] The end-to-end CGM-to-dashboard journey is demonstrated.
- [ ] The public README contains every challenge-required item.
- [ ] The repository includes a licence, architecture PDF/PPT, and presentation PDF/PPT.
- [ ] The minimum 20-minute video link is accessible without requesting permission.
- [ ] The final public repository/folder uses the required team and college name.
