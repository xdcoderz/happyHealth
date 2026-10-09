from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.feature_builder import MODEL_FEATURE_COLUMNS
from app.main import app


client = TestClient(app)


def request_body(reading_count: int = 9) -> dict:
    prediction_time = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)
    glucose = [112, 114, 116, 118, 121, 126, 131, 136, 142]
    selected = glucose[-reading_count:]
    readings = []
    for index, value in enumerate(selected):
        minutes_before = (len(selected) - index - 1) * 15
        readings.append(
            {
                "observedAt": (prediction_time - timedelta(minutes=minutes_before)).isoformat(),
                "glucoseMgDl": value,
            }
        )
    return {
        "schemaVersion": "1.0",
        "patient": {
            "patientId": "DEMO-001",
            "sex": "female",
            "ageYears": 52,
            "bmiKgM2": 27.4,
            "diabetesDurationYears": 7,
            "hba1cPercent": 7.6,
            "fastingPlasmaGlucoseMgDl": 136,
        },
        "predictionTime": prediction_time.isoformat(),
        "meal": {
            "description": "Brown rice 120 g, mixed vegetables 150 g, grilled chicken 60 g",
            "minutesSincePreviousMeal": 240,
            "csiiBolusInsulinIu": 0,
            "csiiBasalInsulinIuPerHour": 0,
            "hasRecordedCsiiBolus": False,
            "hasRecordedCsiiBasalSetting": False,
            "hasRecordedSubcutaneousInsulin": False,
            "hasRecordedNonInsulinMedication": True,
            "hasRecordedIntravenousInsulin": False,
        },
        "cgmReadings": readings,
    }


def test_health_reports_loaded_versioned_model() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["modelLoaded"] is True
    assert response.json()["researchUseOnly"] is True


def test_prediction_uses_real_loaded_model() -> None:
    response = client.post("/ml/predict-glucose-spike", json=request_body())
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "available"
    assert 0 <= body["probability"] <= 1
    assert body["predictionWindowMinutes"] == 120
    assert body["modelVersion"] == "shanghai-logistic-v1"
    assert body["topFactors"]


def test_short_history_is_explicitly_insufficient() -> None:
    response = client.post(
        "/ml/predict-glucose-spike", json=request_body(reading_count=4)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "insufficient_data"
    assert body["probability"] is None


def test_unknown_fields_are_rejected() -> None:
    payload = request_body()
    payload["futureGlucose"] = 300
    response = client.post("/ml/predict-glucose-spike", json=payload)
    assert response.status_code == 422


def test_live_feature_schema_matches_training_schema() -> None:
    from scripts.build_shanghai_features import MODEL_FEATURE_COLUMNS as training_columns

    assert MODEL_FEATURE_COLUMNS == training_columns
