# Prototype Data Dictionary

## Purpose

This document defines the shared fields used by the synthetic patient fixture,
Spring Boot digital twin, Python model service, and React dashboard. The model's
research features are described separately in
[`FEATURE_DICTIONARY.md`](FEATURE_DICTIONARY.md).

## Patient fields

| Field | Type | Required | Unit | Meaning |
| --- | --- | --- | --- | --- |
| `patientId` | string | Yes | None | Stable fictional identifier; `DEMO-001` in the first prototype |
| `displayName` | string | Yes | None | Non-identifying synthetic display label |
| `sex` | enum | Yes | None | `female` or `male`, matching the source model's available coding |
| `ageYears` | number | Yes | years | Synthetic age at the current demonstration time |
| `bmiKgM2` | number | Yes | kg/m² | Body mass index |
| `diabetesDurationYears` | number | Yes | years | Synthetic time since Type 2 diabetes diagnosis |
| `hba1cPercent` | number or null | No | percent | Synthetic HbA1c laboratory value |
| `fastingPlasmaGlucoseMgDl` | number or null | No | mg/dL | Synthetic fasting laboratory glucose |
| `diagnoses` | string array | Yes | None | Synthetic historical diagnoses shown to the doctor |
| `medications` | string array | Yes | None | Synthetic medication names shown to the doctor |

## CGM event fields

| Field | Type | Required | Unit | Meaning |
| --- | --- | --- | --- | --- |
| `eventId` | string | Yes | None | Unique event identifier used for duplicate protection |
| `patientId` | string | Yes | None | Fictional patient receiving the observation |
| `observedAt` | timestamp | Yes | ISO 8601 UTC | Simulated observation time |
| `glucoseMgDl` | number | Yes | mg/dL | Simulated continuous-glucose-monitor value |
| `source` | string | Yes | None | `synthetic-cgm-simulator` for the public demo |

CGM means continuous glucose monitoring. The prototype accepts values from 40 to
500 mg/dL as a software validation boundary. This boundary is not presented as a
diagnostic or treatment range.

## Meal-context fields

| Field | Type | Required | Unit | Meaning |
| --- | --- | --- | --- | --- |
| `description` | string | Yes | None | Fictional meal description used for transparent keyword features |
| `minutesSincePreviousMeal` | number or null | No | minutes | Time since the previous recorded meal |
| `csiiBolusInsulinIu` | number | Yes | IU | Numeric pump bolus recorded at prediction time; zero when no event is recorded |
| `csiiBasalInsulinIuPerHour` | number | Yes | IU/hour | Numeric pump basal setting recorded at prediction time |
| `hasRecorded...` | boolean | Yes | None | States whether each medication event was recorded at prediction time |

CSII means continuous subcutaneous insulin infusion. A false event flag means no
event was recorded in the prototype input. It does not prove non-adherence.

## Prediction fields

| Field | Type | Meaning |
| --- | --- | --- |
| `status` | enum | `available`, `insufficient_data`, or `unavailable` |
| `probability` | number or null | Model probability between 0 and 1 |
| `riskBand` | enum or null | Demonstration display band derived from probability, not a clinical category |
| `predictionWindowMinutes` | integer | Fixed at 120 for model version 1 |
| `predictionTime` | timestamp | Time of the baseline CGM observation used by the model |
| `modelVersion` | string | Exact model bundle identifier |
| `topFactors` | array | Largest linear contributions for this prediction; associations, not causes |
| `warnings` | string array | Missing-data, staleness, or research-use messages |

## Missing data policy

- Missing optional clinical values remain null through the backend.
- The fitted model pipeline imputes missing numeric features using medians learned
  from training patients only.
- The API never replaces an unavailable model result with a fabricated probability.
- A prediction requires a current baseline and adequate recent CGM history.
