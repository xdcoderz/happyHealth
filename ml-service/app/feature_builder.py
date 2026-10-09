"""Create live model inputs with the same definitions used for training."""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from app.schemas import PredictionRequest


GLUCOSE_LAGS_MINUTES = (15, 30, 60, 120)

MEAL_KEYWORDS = {
    "rice": ("rice",),
    "noodle": ("noodle", "vermicelli"),
    "bread": ("bread", "bun", "toast"),
    "fruit": (
        "apple",
        "banana",
        "grape",
        "orange",
        "peach",
        "pear",
        "pomelo",
        "watermelon",
    ),
    "vegetable": (
        "vegetable",
        "spinach",
        "cabbage",
        "lettuce",
        "cucumber",
        "tomato",
        "broccoli",
        "cauliflower",
    ),
    "animal_protein": (
        "beef",
        "chicken",
        "duck",
        "egg",
        "fish",
        "lamb",
        "mutton",
        "pork",
        "shrimp",
    ),
    "dairy": ("milk", "yogurt", "yoghurt"),
    "root_or_corn": ("potato", "sweet potato", "yam", "corn", "lotus root"),
}

MODEL_FEATURE_COLUMNS = [
    "baseline_glucose_mg_dl",
    "glucose_lag_15_min_mg_dl",
    "glucose_lag_30_min_mg_dl",
    "glucose_lag_60_min_mg_dl",
    "glucose_lag_120_min_mg_dl",
    "glucose_change_prev_15_min_mg_dl",
    "glucose_change_prev_30_min_mg_dl",
    "glucose_change_prev_60_min_mg_dl",
    "glucose_change_prev_120_min_mg_dl",
    "glucose_mean_prev_120_min_mg_dl",
    "glucose_std_prev_120_min_mg_dl",
    "glucose_min_prev_120_min_mg_dl",
    "glucose_max_prev_120_min_mg_dl",
    "glucose_range_prev_120_min_mg_dl",
    "glucose_observations_prev_120_min",
    "meal_hour_sin",
    "meal_hour_cos",
    "meal_is_weekend",
    "minutes_since_previous_meal",
    "reported_food_weight_g",
    "food_items_with_reported_weight",
    "meal_text_length_characters",
    "meal_contains_rice",
    "meal_contains_noodle",
    "meal_contains_bread",
    "meal_contains_fruit",
    "meal_contains_vegetable",
    "meal_contains_animal_protein",
    "meal_contains_dairy",
    "meal_contains_root_or_corn",
    "csii_bolus_insulin_iu_at_meal",
    "csii_basal_insulin_iu_per_hour_at_meal",
    "has_recorded_csii_bolus_at_meal",
    "has_recorded_csii_basal_setting_at_meal",
    "has_recorded_subcutaneous_insulin_at_meal",
    "has_recorded_non_insulin_medication_at_meal",
    "has_recorded_intravenous_insulin_at_meal",
    "sex_female",
    "age_years",
    "bmi_kg_m2",
    "diabetes_duration_years",
    "hba1c_percent",
    "fasting_plasma_glucose_mg_dl",
]


class InsufficientHistoryError(ValueError):
    """Raised when a live request cannot form a defensible baseline."""


def utc(value: datetime) -> datetime:
    return value.astimezone(timezone.utc)


def meal_text_features(text: str) -> dict[str, float]:
    lowered = text.lower()
    weights = [
        float(value)
        for value in re.findall(r"(?<![a-z])([0-9]+(?:\.[0-9]+)?)\s*g\b", lowered)
    ]
    result: dict[str, float] = {
        "reported_food_weight_g": sum(weights) if weights else math.nan,
        "food_items_with_reported_weight": float(len(weights)),
        "meal_text_length_characters": float(len(text)),
    }
    for group, keywords in MEAL_KEYWORDS.items():
        result[f"meal_contains_{group}"] = float(
            any(re.search(rf"\b{re.escape(keyword)}\b", lowered) for keyword in keywords)
        )
    return result


def build_features(request: PredictionRequest) -> tuple[pd.DataFrame, list[str]]:
    """Return one ordered feature row and non-fatal data warnings."""

    prediction_time = utc(request.predictionTime)
    readings: dict[datetime, float] = {}
    for reading in request.cgmReadings:
        observed_at = utc(reading.observedAt)
        if observed_at > prediction_time:
            continue
        readings[observed_at] = float(reading.glucoseMgDl)

    if prediction_time not in readings:
        raise InsufficientHistoryError(
            "No CGM reading exists at the requested prediction time."
        )

    history_start = prediction_time - pd.Timedelta(minutes=120)
    history = sorted(
        (timestamp, value)
        for timestamp, value in readings.items()
        if history_start <= timestamp <= prediction_time
    )
    if len(history) < 5:
        raise InsufficientHistoryError(
            "At least five CGM readings during the previous 120 minutes are required."
        )

    baseline = readings[prediction_time]
    row: dict[str, Any] = {"baseline_glucose_mg_dl": baseline}
    warnings: list[str] = []
    for minutes in GLUCOSE_LAGS_MINUTES:
        target = prediction_time - pd.Timedelta(minutes=minutes)
        lag = readings.get(target, math.nan)
        row[f"glucose_lag_{minutes}_min_mg_dl"] = lag
        row[f"glucose_change_prev_{minutes}_min_mg_dl"] = (
            baseline - lag if not math.isnan(lag) else math.nan
        )
        if math.isnan(lag):
            warnings.append(f"Exact {minutes}-minute CGM lag was unavailable and imputed.")

    values = pd.Series([value for _, value in history], dtype="float64")
    row["glucose_mean_prev_120_min_mg_dl"] = float(values.mean())
    row["glucose_std_prev_120_min_mg_dl"] = float(values.std(ddof=1))
    row["glucose_min_prev_120_min_mg_dl"] = float(values.min())
    row["glucose_max_prev_120_min_mg_dl"] = float(values.max())
    row["glucose_range_prev_120_min_mg_dl"] = float(values.max() - values.min())
    row["glucose_observations_prev_120_min"] = float(len(values))

    hour = prediction_time.hour + prediction_time.minute / 60.0
    angle = 2.0 * math.pi * hour / 24.0
    row["meal_hour_sin"] = math.sin(angle)
    row["meal_hour_cos"] = math.cos(angle)
    row["meal_is_weekend"] = float(prediction_time.weekday() >= 5)
    row["minutes_since_previous_meal"] = (
        request.meal.minutesSincePreviousMeal
        if request.meal.minutesSincePreviousMeal is not None
        else math.nan
    )
    row.update(meal_text_features(request.meal.description))

    row["csii_bolus_insulin_iu_at_meal"] = request.meal.csiiBolusInsulinIu
    row["csii_basal_insulin_iu_per_hour_at_meal"] = (
        request.meal.csiiBasalInsulinIuPerHour
    )
    row["has_recorded_csii_bolus_at_meal"] = float(
        request.meal.hasRecordedCsiiBolus
    )
    row["has_recorded_csii_basal_setting_at_meal"] = float(
        request.meal.hasRecordedCsiiBasalSetting
    )
    row["has_recorded_subcutaneous_insulin_at_meal"] = float(
        request.meal.hasRecordedSubcutaneousInsulin
    )
    row["has_recorded_non_insulin_medication_at_meal"] = float(
        request.meal.hasRecordedNonInsulinMedication
    )
    row["has_recorded_intravenous_insulin_at_meal"] = float(
        request.meal.hasRecordedIntravenousInsulin
    )

    row["sex_female"] = float(request.patient.sex == "female")
    row["age_years"] = request.patient.ageYears
    row["bmi_kg_m2"] = request.patient.bmiKgM2
    row["diabetes_duration_years"] = request.patient.diabetesDurationYears
    row["hba1c_percent"] = (
        request.patient.hba1cPercent
        if request.patient.hba1cPercent is not None
        else math.nan
    )
    row["fasting_plasma_glucose_mg_dl"] = (
        request.patient.fastingPlasmaGlucoseMgDl
        if request.patient.fastingPlasmaGlucoseMgDl is not None
        else math.nan
    )

    frame = pd.DataFrame([row], columns=MODEL_FEATURE_COLUMNS, dtype="float64")
    return frame, warnings
