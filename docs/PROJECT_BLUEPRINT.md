# HappyHealth Digital Twin Challenge 2026 - Project Blueprint

## 1. Challenge Context

The Digital Twin Challenge 2026 asks teams to build a proof-of-concept healthcare digital twin that combines:

- Static or historical patient data such as demographics, diagnoses, lab values, medication history, and risk markers.
- Dynamic time-series data such as glucose readings, heart rate, sleep, activity, or other wearable signals.

The prototype must predict a specific adverse health outcome and show a conceptual doctor-facing dashboard for interacting with the virtual patient.

## 2. Proposed Project

### Project Title

GlucoTwin India: A Personalized Digital Twin for Predicting Type 2 Diabetes Glucose Spikes

### One-Line Pitch

GlucoTwin India creates a virtual metabolic profile for a patient and predicts glucose spikes up to 2 hours in advance by combining open research data for model development with synthetic patient data for a safe application demonstration.

### Healthcare Use Case

Type 2 Diabetes is highly prevalent in India and often worsens through repeated post-meal glucose spikes, poor sleep, low activity, stress, and delayed treatment adjustment. A clinician usually sees lab summaries after the fact. This system helps surface near-future glucose risk early enough for preventive action.

### Predicted Adverse Event

The model predicts whether a patient is likely to experience a clinically meaningful glucose spike within the next 2 hours.

Initial spike definition:

- CGM glucose greater than or equal to 180 mg/dL within the next 2 hours, or
- A sharp upward trend, such as an increase of 40 mg/dL or more from the current baseline.

This threshold can be tuned during experimentation.

## 3. Target Users

### Primary User

Doctor, diabetologist, or clinical care team reviewing patient risk and intervention recommendations.

### Secondary User

Patient or health coach viewing simplified preventive guidance.

## 4. Core Prototype Scope

### Must-Have

- Synthetic patient cohort with EHR-style features.
- Simulated CGM and wearable time-series streams.
- Feature pipeline that joins static EHR and dynamic sensor data.
- Machine learning model that predicts 2-hour glucose spike risk.
- Doctor dashboard showing patient profile, risk score, signal trends, and explainability.
- Documentation for datasets, model, architecture, and ethical/privacy approach.

### Should-Have

- Risk factor attribution using SHAP or another explainability method.
- Scenario simulation, such as "what if the patient walks after dinner?"
- Alert severity bands: low, moderate, high, critical.
- Basic evaluation report with AUROC, precision, recall, F1, and calibration.

### Nice-to-Have

- Multiple digital twin profiles for comparison.
- Treatment recommendation mock layer.
- PDF export of patient risk summary.
- Demo video script and slide outline.

## 5. Data Strategy

### Two Data Lanes

Use open, de-identified research data to develop and evaluate the model. Use synthetic patients for the public application demonstration so no real participant record is exposed through the interface.

The first research cohort is ShanghaiT2DM: 100 base patients across 109 recordings with 15-minute CGM, timed dietary and medication events, and clinical summaries. Keep downloaded and generated patient-level files local; commit only preparation code, documentation, and non-patient inventories.

### Static EHR-Like Data

Use ShanghaiT2DM clinical fields for research experiments and synthetic EHR generation for the demonstration patient.

Candidate fields:

- Age
- Sex
- BMI
- Diabetes duration
- HbA1c
- Fasting glucose
- Blood pressure
- LDL/HDL/triglycerides
- Existing conditions such as hypertension or dyslipidemia
- Medication class
- Family history marker

Possible generation sources:

- Synthea-generated synthetic patients
- Custom synthetic generator based on medically plausible distributions

### Dynamic Wearable and CGM Data

Use synthetic or open-source time-series signals.

Candidate streams:

- Continuous glucose readings every 5 or 15 minutes
- Heart rate
- Heart rate variability
- Step count
- Sleep duration and sleep quality
- Meal timing and carbohydrate load
- Stress proxy score

For the first model version, prepare ShanghaiT2DM with a reproducible patient-level split. Synthetic CGM and wearable streams remain useful for application demos and scenario testing, but they do not replace evaluation on real open research measurements.

## 6. Digital Twin Concept

Each patient twin contains:

- Baseline metabolic risk profile from EHR data.
- Recent behavior and physiology from wearable/CGM streams.
- Personalized response patterns, such as meal sensitivity and activity benefit.
- Current risk state and near-future predicted glucose trajectory.

The digital twin is not a full-body simulator. It is a focused metabolic twin for short-horizon diabetes risk prediction.

## 7. ML Approach

### Baseline Model

Start with a tabular time-window classifier:

- Input: rolling 2 to 6 hour features plus static EHR features.
- Output: probability of glucose spike within the next 2 hours.
- Candidate models: XGBoost, LightGBM, Random Forest, or Logistic Regression baseline.

### Advanced Model

If time permits:

- LSTM/GRU model over CGM and wearable sequences.
- Temporal Fusion Transformer for sequence plus static feature fusion.
- Hybrid approach: sequence embeddings plus tabular classifier.

### Initial Feature Set

Static:

- Age, BMI, HbA1c, diabetes duration, medication class, comorbidities.

Dynamic rolling features:

- Current glucose
- Glucose slope over 15, 30, 60 minutes
- Glucose variability over 2 hours
- Time since meal
- Estimated carbohydrate load
- Steps in last 2 hours
- Sleep quality last night
- Heart rate deviation from baseline
- Stress proxy score

## 8. Evaluation Plan

Metrics:

- AUROC for discrimination.
- Precision and recall for high-risk spike detection.
- F1 score for balanced classification.
- Calibration curve or Brier score for probability quality.
- Lead-time analysis showing how early warnings are produced.

Validation:

- Train/validation/test split by patient, not by row, to reduce leakage.
- Compare against simple baselines such as current glucose threshold or recent slope only.

## 9. Doctor Dashboard Requirements

### Dashboard Views

1. Patient Overview
   - Basic profile
   - Diagnosis summary
   - Key lab values
   - Current risk level

2. Digital Twin Timeline
   - CGM trend
   - Predicted 2-hour risk window
   - Activity, sleep, meal, and heart-rate overlays

3. Risk Explanation
   - Top drivers of current risk
   - Examples: high carb load, poor sleep, low activity, high glucose slope

4. Scenario Simulator
   - Compare predicted risk after lightweight interventions.
   - Example: 15-minute walk after meal, reduced carb intake, medication adherence.

5. Clinical Summary
   - Concise, readable summary for a doctor.
   - Suggested follow-up prompts, clearly marked as decision support rather than diagnosis.

## 10. Recommended Technical Stack

### Frontend

- React + Vite
- TypeScript
- Tailwind CSS or CSS modules
- Recharts or ECharts for time-series visualization

### Backend

- Java 21 + Spring Boot 3 for the main backend API
- Spring Web, Spring Data JPA, Spring Validation, and WebClient
- H2 Database for local prototype persistence
- Separate Python FastAPI ML service for model inference and explainability
- Pandas, NumPy, Scikit-learn, XGBoost, and SHAP inside the ML service

### Data and Storage

- CSV or Parquet for prototype data
- SQLite for lightweight local persistence if needed

### Demo Deployment

- Local Docker Compose for frontend, Spring Boot backend, Python ML service, and MQTT broker
- Optional hosted frontend with a mock API for presentation

## 11. Proposed Repository Structure

```text
happyHealth/
  docs/
    PROJECT_BLUEPRINT.md
    ARCHITECTURE.md
    DATA_DICTIONARY.md
    MODEL_CARD.md
  data/
    synthetic/
    processed/
  notebooks/
    01_data_generation.ipynb
    02_model_training.ipynb
    03_evaluation.ipynb
  backend/
    pom.xml
    src/
      main/
        java/
          com/
            happyhealth/
              HappyHealthApplication.java
              controller/
              service/
              repository/
              entity/
              dto/
              client/
    tests/
  ml-service/
    requirements.txt
    app/
      main.py
      api/
      services/
      ml/
  frontend/
    src/
      components/
      pages/
      charts/
      services/
    package.json
  scripts/
    generate_synthetic_data.py
    train_model.py
    evaluate_model.py
  README.md
  LICENSE
```

## 12. Architecture Overview

```text
Synthetic EHR Generator
        |
        v
Synthetic Patient Profiles ---------
        |                          |
        v                          v
Wearable/CGM Time-Series      Static Features
        |                          |
        -------- Feature Pipeline --
                    |
                    v
             Prediction Model
                    |
                    v
        Python ML Risk + Explanation API
                    |
                    v
          Spring Boot Backend API
                    |
                    v
          Doctor Dashboard UI
```

## 13. Privacy, Safety, and Ethics

- Use only synthetic, anonymized, or open-source data.
- Do not claim diagnostic authority.
- Present outputs as clinical decision support.
- Clearly document model limitations and synthetic data assumptions.
- Avoid collecting personally identifiable information.
- Include disclaimer that the prototype is not for real clinical use without validation.

## 14. Submission Deliverables

Required by challenge:

- Public GitHub repository.
- README with team details, title, problem statement, stack, model details, license.
- 20-minute demo/explanation video.
- Architecture diagram in PDF/PPT format.
- Presentation in PDF/PPT format.

Recommended additions:

- Model card.
- Data dictionary.
- Reproducible setup instructions.
- Demo patient accounts or preloaded demo patients.
- Evaluation notebook or report.

## 15. Development Milestones

The delivery sequence is defined in [PROJECT_PHASES.md](PROJECT_PHASES.md):

1. Scope & Contracts.
2. Project Setup.
3. First End-to-End Demo using a clearly labelled mock prediction.
4. IoT & Digital Twin.
5. ML Development & Validation.
6. Live Prediction Integration.
7. Dashboard & Scenario Simulation.
8. Testing & Submission.

Phases 4 and 5 can proceed in parallel after their shared contracts are agreed. Model training is not a prerequisite for the Phase 3 integration milestone.

## 16. Immediate Next Steps

1. Complete Phase 1 contracts and clinical review using the five folder TODO.md checklists.
2. Initialize the three services, root setup files, and health checks in Phase 2.
3. Prepare one small synthetic patient fixture with historical CGM readings.
4. Connect the dashboard to Spring Boot and its internal FastAPI mock endpoint.
5. Verify the Phase 3 acceptance gate before starting live IoT and actual model development.

