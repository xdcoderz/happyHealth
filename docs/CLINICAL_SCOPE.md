# Clinical Scope and Safety Boundaries

## Intended use

HappyHealth is a research proof of concept showing how static clinical context and
simulated continuous glucose monitoring can be fused into a virtual metabolic
patient. It estimates the probability of the project's defined glucose-spike event
during the following 120 minutes.

The prototype is intended for technical demonstration and research discussion with
a doctor-facing interface.

## Target definition

Model version 1 labels an event positive when, within 120 minutes after the
prediction baseline, either:

- glucose reaches at least 180 mg/dL, or
- glucose rises by at least 40 mg/dL above baseline.

This is a project research definition. It is not a universal diagnostic threshold,
prescription rule, or recommendation to change treatment.

## Explicitly excluded uses

The prototype must not be used to:

- diagnose diabetes or another condition;
- calculate or recommend insulin or medication doses;
- replace CGM device alerts or professional clinical judgment;
- recommend an intervention as proven to cause a particular outcome;
- make decisions about a real identifiable patient;
- claim validation for Indian patients or another population not studied.

## Demonstration-data policy

- The public application uses only a fictional synthetic patient.
- Open ShanghaiT2DM data is used locally for model research and evaluation.
- Raw and processed participant-level research tables are not committed to GitHub.
- The dashboard must always label the patient and sensor stream as synthetic.

## Required clinical review

Before submission, the healthcare-domain lead must review:

- the target definition and how it is displayed;
- patient fields, units, and synthetic values;
- risk-band wording;
- explanation wording;
- limitations and research-use notices;
- presentation and video statements.

Clinical review remains pending until the reviewer and date are recorded in
[`PHASE_STATUS.md`](PHASE_STATUS.md).
