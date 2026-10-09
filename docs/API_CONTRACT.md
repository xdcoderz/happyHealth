# Prototype API Contract

## Service boundary

```text
React browser → Spring Boot → FastAPI model service
                         ↘ H2 digital-twin state
Synthetic CGM publisher → Spring Boot or MQTT subscriber
```

The browser calls Spring Boot only. FastAPI and MQTT remain internal services.

All timestamps are ISO 8601 UTC. Glucose uses mg/dL.

## Spring Boot endpoints

### `GET /api/patients/{patientId}/twin`

Returns the synthetic patient profile, recent CGM readings, freshness information,
and the most recent prediction. An unknown patient returns HTTP 404.

### `POST /api/patients/{patientId}/cgm`

Accepts one simulated CGM event:

```json
{
  "eventId": "demo-event-010",
  "observedAt": "2026-10-09T10:15:00Z",
  "glucoseMgDl": 148.0,
  "source": "synthetic-cgm-simulator"
}
```

The path patient ID is authoritative. A repeated `eventId` is idempotent and does
not create another reading. An older observation may be retained in history but
must not replace a newer current state.

### `POST /api/predictions/{patientId}/refresh`

Builds a request from the synthetic EHR, current meal context, and recent CGM
history, then calls FastAPI. It returns the updated twin view. If FastAPI is
unavailable, the response contains an explicit unavailable prediction rather than a
mock probability.

### `GET /actuator/health`

Returns Spring Boot health information.

## FastAPI endpoints

### `GET /health`

Reports service health, model-loaded state, model version, and research-use status.

### `POST /ml/predict-glucose-spike`

Input structure:

```json
{
  "patient": {
    "patientId": "DEMO-001",
    "sex": "female",
    "ageYears": 52,
    "bmiKgM2": 27.4,
    "diabetesDurationYears": 7.0,
    "hba1cPercent": 7.6,
    "fastingPlasmaGlucoseMgDl": 136.0
  },
  "predictionTime": "2026-10-09T10:15:00Z",
  "meal": {
    "description": "Brown rice 120 g, mixed vegetables 150 g, grilled chicken 60 g",
    "minutesSincePreviousMeal": 240.0,
    "csiiBolusInsulinIu": 0.0,
    "csiiBasalInsulinIuPerHour": 0.0,
    "hasRecordedCsiiBolus": false,
    "hasRecordedCsiiBasalSetting": false,
    "hasRecordedSubcutaneousInsulin": false,
    "hasRecordedNonInsulinMedication": true,
    "hasRecordedIntravenousInsulin": false
  },
  "cgmReadings": [
    {"observedAt": "2026-10-09T08:15:00Z", "glucoseMgDl": 112.0},
    {"observedAt": "2026-10-09T10:15:00Z", "glucoseMgDl": 142.0}
  ]
}
```

Successful response:

```json
{
  "status": "available",
  "probability": 0.71,
  "riskBand": "high",
  "predictionWindowMinutes": 120,
  "predictionTime": "2026-10-09T10:15:00Z",
  "modelVersion": "shanghai-logistic-v1",
  "topFactors": [
    {
      "feature": "baseline_glucose_mg_dl",
      "displayName": "Current glucose",
      "direction": "higher",
      "contribution": 0.42
    }
  ],
  "warnings": [
    "Research prototype using a synthetic demonstration patient."
  ]
}
```

Validation errors return HTTP 422. Insufficient history returns HTTP 200 with
`status: insufficient_data`, a null probability, and specific warnings.

## Compatibility rule

The model bundle, feature builder, backend request, and documentation share schema
version `1.0`. A service must fail visibly when it cannot support the received
schema instead of guessing how to transform it.
