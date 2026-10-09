# Model Card: Shanghai Logistic Baseline v1

## Purpose

This model estimates whether glucose will rise by at least **40 mg/dL within two
hours after a recorded meal**. It exists to demonstrate static EHR + dynamic CGM
fusion for the HappyHealth prototype. It is not a medical device.

## Inputs

The 43 numeric inputs combine recent CGM history, time and meal text signals,
recorded medication events, and static patient values such as age, BMI, diabetes
duration, HbA1c, and fasting glucose. The exact definitions are in
[`FEATURE_DICTIONARY.md`](../FEATURE_DICTIONARY.md) and are enforced by a schema
parity test.

## Training and evaluation

The baseline is Logistic Regression with median imputation, missingness indicators,
and standard scaling. Patients—not rows—were divided between train, validation, and
test sets to reduce information leakage.

| Split | ROC AUC | F1 |
| --- | ---: | ---: |
| Validation | 0.701 | 0.779 |
| Test | 0.757 | 0.742 |

These are technical prototype metrics, not evidence of clinical safety or benefit.

## Data and privacy

Training uses the openly shared ShanghaiT2DM research dataset under its source
terms. Raw data is excluded from Git. The repository contains only the small
derived model bundle and aggregate metrics. The public application demonstrates a
fully synthetic patient and simulated CGM events.

## Limitations and prohibited use

- Not clinically validated and not calibrated for an individual patient.
- The training population may not represent other countries or care settings.
- Meal text and medication recording can be incomplete.
- Explanatory factors are model contributions, not medical causes.
- Do not use the result for diagnosis, treatment, dosing, or emergency decisions.
