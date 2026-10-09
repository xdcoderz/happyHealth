#!/usr/bin/env python3
"""Build a leakage-safe, meal-level feature table for ShanghaiT2DM.

Every model input is calculated from information available at or before the
recorded meal time. Future glucose is retained only as the prediction label.
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.prepare_shanghai_t2dm import (
    PipelineValidationError,
    atomic_write_csv,
    atomic_write_json,
)


GLUCOSE_LAGS_MINUTES = (15, 30, 60, 120)

CLINICAL_SOURCE_COLUMNS = [
    "age_years",
    "bmi_kg_m2",
    "diabetes_duration_years",
    "hba1c_percent",
    "fasting_plasma_glucose_mg_dl",
]

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

IDENTIFIER_COLUMNS = [
    "source_dataset",
    "cohort",
    "patient_id",
    "recording_id",
    "split",
    "meal_id",
    "timestamp",
    "dietary_intake_raw",
    "source_file",
    "source_sheet",
    "source_row",
]

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

TARGET_COLUMN = "spike_within_120_min"

FORBIDDEN_MODEL_INPUT_PATTERNS = (
    "target_timestamp",
    "glucose_at_120",
    "glucose_change_at_120",
    "max_glucose_next",
    "max_rise_next",
    "reaches_180",
    "rises_40",
    "spike_within",
    "minutes_until_next_meal",
)


def parse_boolean(series: pd.Series, name: str) -> pd.Series:
    """Convert CSV booleans without treating the text 'False' as true."""

    normalised = series.astype("string").str.strip().str.lower()
    mapping = {"true": True, "false": False, "1": True, "0": False}
    result = normalised.map(mapping)
    invalid = series.notna() & result.isna()
    if invalid.any():
        values = sorted(series.loc[invalid].astype(str).unique())
        raise PipelineValidationError(f"Invalid boolean values in {name}: {values}")
    return result.astype("boolean")


def read_processed_tables(input_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Read the three prepared tables required for feature engineering."""

    required = {
        "readings": input_dir / "glucose_readings.csv",
        "meals": input_dir / "meal_events.csv",
        "clinical": input_dir / "clinical_records.csv",
    }
    missing = [str(path) for path in required.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing prepared input files: {missing}")

    dtype = {"patient_id": "string", "recording_id": "string"}
    readings = pd.read_csv(
        required["readings"],
        dtype=dtype,
        parse_dates=["timestamp"],
        low_memory=False,
    )
    meals = pd.read_csv(required["meals"], dtype=dtype, parse_dates=["timestamp"])
    clinical = pd.read_csv(required["clinical"], dtype=dtype)
    return readings, meals, clinical


def exact_glucose_lag(series: pd.Series, timestamp: pd.Timestamp, minutes: int) -> Any:
    """Return glucose at an exact earlier timestamp, or missing when no reading exists."""

    target = timestamp - pd.Timedelta(minutes=minutes)
    try:
        value = series.loc[target]
    except KeyError:
        return pd.NA
    if isinstance(value, pd.Series):
        raise PipelineValidationError("Duplicate timestamps reached feature generation")
    return float(value)


def meal_text_features(text: str) -> dict[str, Any]:
    """Extract transparent text flags and explicitly reported gram quantities."""

    lowered = text.lower()
    weights = [
        float(value)
        for value in re.findall(r"(?<![a-z])([0-9]+(?:\.[0-9]+)?)\s*g\b", lowered)
    ]
    result: dict[str, Any] = {
        "reported_food_weight_g": sum(weights) if weights else pd.NA,
        "food_items_with_reported_weight": len(weights),
        "meal_text_length_characters": len(text),
    }
    for group, keywords in MEAL_KEYWORDS.items():
        result[f"meal_contains_{group}"] = int(
            any(re.search(rf"\b{re.escape(keyword)}\b", lowered) for keyword in keywords)
        )
    return result


def validate_model_feature_names() -> None:
    """Fail if a future-outcome field is ever added to the input feature list."""

    unsafe = [
        feature
        for feature in MODEL_FEATURE_COLUMNS
        if any(pattern in feature for pattern in FORBIDDEN_MODEL_INPUT_PATTERNS)
    ]
    if unsafe:
        raise PipelineValidationError(f"Future information found in model features: {unsafe}")


def build_feature_table(
    readings: pd.DataFrame,
    meals: pd.DataFrame,
    clinical: pd.DataFrame,
) -> pd.DataFrame:
    """Create one numeric, leakage-safe feature row per eligible meal."""

    validate_model_feature_names()
    required_reading_columns = {
        "patient_id",
        "recording_id",
        "split",
        "timestamp",
        "glucose_mg_dl",
        "csii_bolus_insulin_iu",
        "csii_basal_insulin_iu_per_hour",
        "csii_basal_insulin_raw",
        "insulin_subcutaneous_raw",
        "non_insulin_hypoglycemic_agents_raw",
        "insulin_intravenous_raw",
    }
    required_meal_columns = set(IDENTIFIER_COLUMNS) | {
        "eligible_for_initial_model",
        "baseline_glucose_mg_dl",
        "minutes_since_previous_meal",
        TARGET_COLUMN,
    }
    required_clinical_columns = {
        "patient_id",
        "recording_id",
        "split",
        "sex_code",
        *CLINICAL_SOURCE_COLUMNS,
    }
    for label, frame, required in [
        ("readings", readings, required_reading_columns),
        ("meals", meals, required_meal_columns),
        ("clinical", clinical, required_clinical_columns),
    ]:
        missing = sorted(required.difference(frame.columns))
        if missing:
            raise PipelineValidationError(f"Missing {label} columns: {missing}")

    readings = readings.copy()
    meals = meals.copy()
    clinical = clinical.copy()
    for frame in (readings, meals, clinical):
        frame["patient_id"] = frame["patient_id"].astype("string")
        frame["recording_id"] = frame["recording_id"].astype("string")
    readings["timestamp"] = pd.to_datetime(readings["timestamp"], errors="coerce")
    meals["timestamp"] = pd.to_datetime(meals["timestamp"], errors="coerce")
    if readings["timestamp"].isna().any() or meals["timestamp"].isna().any():
        raise PipelineValidationError("A prepared table contains an invalid timestamp")
    if readings.duplicated(["recording_id", "timestamp"]).any():
        raise PipelineValidationError("Prepared readings contain duplicate timestamps")
    if clinical["recording_id"].duplicated().any():
        raise PipelineValidationError("Clinical table contains duplicate recording IDs")

    meals["eligible_for_initial_model"] = parse_boolean(
        meals["eligible_for_initial_model"], "eligible_for_initial_model"
    )
    meals[TARGET_COLUMN] = parse_boolean(meals[TARGET_COLUMN], TARGET_COLUMN)
    eligible = meals.loc[meals["eligible_for_initial_model"].fillna(False)].copy()
    if eligible.empty:
        raise PipelineValidationError("No eligible meal rows were found")
    if eligible[TARGET_COLUMN].isna().any():
        raise PipelineValidationError("An eligible meal is missing its prediction label")
    if eligible["meal_id"].duplicated().any():
        raise PipelineValidationError("Eligible meal IDs are not unique")

    reading_groups: dict[str, pd.DataFrame] = {}
    for recording_id, group in readings.groupby("recording_id", sort=False):
        reading_groups[str(recording_id)] = group.sort_values("timestamp").set_index(
            "timestamp", drop=False
        )
    clinical_lookup = clinical.set_index("recording_id", drop=False)

    rows: list[dict[str, Any]] = []
    for meal in eligible.itertuples(index=False):
        recording_id = str(meal.recording_id)
        if recording_id not in reading_groups or recording_id not in clinical_lookup.index:
            raise PipelineValidationError(
                f"Meal {meal.meal_id} has no reading or clinical recording"
            )
        group = reading_groups[recording_id]
        timestamp = pd.Timestamp(meal.timestamp)
        if timestamp not in group.index:
            raise PipelineValidationError(f"Meal {meal.meal_id} has no baseline reading")
        current = group.loc[timestamp]
        if isinstance(current, pd.DataFrame):
            raise PipelineValidationError("Duplicate meal-time readings reached the pipeline")
        baseline = float(current["glucose_mg_dl"])
        if not math.isclose(
            baseline, float(meal.baseline_glucose_mg_dl), rel_tol=0.0, abs_tol=1e-9
        ):
            raise PipelineValidationError(f"Baseline mismatch for meal {meal.meal_id}")

        clinical_row = clinical_lookup.loc[recording_id]
        if str(current["patient_id"]) != str(meal.patient_id) or str(
            clinical_row["patient_id"]
        ) != str(meal.patient_id):
            raise PipelineValidationError(f"Patient mismatch for meal {meal.meal_id}")
        if current["split"] != meal.split or clinical_row["split"] != meal.split:
            raise PipelineValidationError(f"Split mismatch for meal {meal.meal_id}")

        row = {column: getattr(meal, column) for column in IDENTIFIER_COLUMNS}
        row["baseline_glucose_mg_dl"] = baseline
        glucose_series = group["glucose_mg_dl"]
        for minutes in GLUCOSE_LAGS_MINUTES:
            lag = exact_glucose_lag(glucose_series, timestamp, minutes)
            row[f"glucose_lag_{minutes}_min_mg_dl"] = lag
            row[f"glucose_change_prev_{minutes}_min_mg_dl"] = (
                baseline - lag if not pd.isna(lag) else pd.NA
            )

        history = group.loc[
            (group["timestamp"] >= timestamp - pd.Timedelta(minutes=120))
            & (group["timestamp"] <= timestamp),
            "glucose_mg_dl",
        ].astype(float)
        if history.empty:
            raise PipelineValidationError(f"No glucose history for meal {meal.meal_id}")
        row["glucose_mean_prev_120_min_mg_dl"] = float(history.mean())
        row["glucose_std_prev_120_min_mg_dl"] = (
            float(history.std(ddof=1)) if len(history) > 1 else pd.NA
        )
        row["glucose_min_prev_120_min_mg_dl"] = float(history.min())
        row["glucose_max_prev_120_min_mg_dl"] = float(history.max())
        row["glucose_range_prev_120_min_mg_dl"] = float(
            history.max() - history.min()
        )
        row["glucose_observations_prev_120_min"] = len(history)

        hour = timestamp.hour + timestamp.minute / 60.0
        angle = 2.0 * math.pi * hour / 24.0
        row["meal_hour_sin"] = math.sin(angle)
        row["meal_hour_cos"] = math.cos(angle)
        row["meal_is_weekend"] = int(timestamp.dayofweek >= 5)
        row["minutes_since_previous_meal"] = pd.to_numeric(
            pd.Series([meal.minutes_since_previous_meal]), errors="coerce"
        ).iloc[0]
        row.update(meal_text_features(str(meal.dietary_intake_raw)))

        bolus_at_meal = pd.to_numeric(
            pd.Series([current["csii_bolus_insulin_iu"]]), errors="coerce"
        ).iloc[0]
        basal_at_meal = pd.to_numeric(
            pd.Series([current["csii_basal_insulin_iu_per_hour"]]), errors="coerce"
        ).iloc[0]
        row["csii_bolus_insulin_iu_at_meal"] = (
            0.0 if pd.isna(bolus_at_meal) else float(bolus_at_meal)
        )
        row["csii_basal_insulin_iu_per_hour_at_meal"] = (
            0.0 if pd.isna(basal_at_meal) else float(basal_at_meal)
        )
        row["has_recorded_csii_bolus_at_meal"] = int(pd.notna(bolus_at_meal))
        row["has_recorded_csii_basal_setting_at_meal"] = int(
            pd.notna(current["csii_basal_insulin_raw"])
        )
        row["has_recorded_subcutaneous_insulin_at_meal"] = int(
            pd.notna(current["insulin_subcutaneous_raw"])
        )
        row["has_recorded_non_insulin_medication_at_meal"] = int(
            pd.notna(current["non_insulin_hypoglycemic_agents_raw"])
        )
        row["has_recorded_intravenous_insulin_at_meal"] = int(
            pd.notna(current["insulin_intravenous_raw"])
        )

        sex_code = pd.to_numeric(pd.Series([clinical_row["sex_code"]]), errors="coerce").iloc[0]
        row["sex_female"] = pd.NA if pd.isna(sex_code) else int(sex_code == 1)
        for column in CLINICAL_SOURCE_COLUMNS:
            row[column] = pd.to_numeric(
                pd.Series([clinical_row[column]]), errors="coerce"
            ).iloc[0]
        row[TARGET_COLUMN] = int(bool(meal.spike_within_120_min))
        rows.append(row)

    result = pd.DataFrame(rows)
    result = result[IDENTIFIER_COLUMNS + MODEL_FEATURE_COLUMNS + [TARGET_COLUMN]]
    result = result.sort_values(["patient_id", "timestamp", "meal_id"]).reset_index(
        drop=True
    )
    for column in MODEL_FEATURE_COLUMNS + [TARGET_COLUMN]:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    if result[MODEL_FEATURE_COLUMNS].select_dtypes(exclude="number").columns.tolist():
        non_numeric = result[MODEL_FEATURE_COLUMNS].select_dtypes(
            exclude="number"
        ).columns.tolist()
        raise PipelineValidationError(f"Non-numeric model features found: {non_numeric}")
    if result.groupby("patient_id")["split"].nunique().max() != 1:
        raise PipelineValidationError("A patient appears in more than one split")
    return result


def build_feature_report(features: pd.DataFrame) -> dict[str, Any]:
    """Summarise feature coverage, labels, and leakage protections."""

    split_details: dict[str, Any] = {}
    for split_name in ("train", "validation", "test"):
        frame = features.loc[features["split"] == split_name]
        split_details[split_name] = {
            "rows": len(frame),
            "patients": int(frame["patient_id"].nunique()),
            "positive_spikes": int(frame[TARGET_COLUMN].sum()),
            "positive_rate": float(frame[TARGET_COLUMN].mean()),
        }
    return {
        "dataset": "ShanghaiT2DM",
        "feature_table_version": 1,
        "row_definition": "one initially eligible recorded meal",
        "rows": len(features),
        "patients": int(features["patient_id"].nunique()),
        "model_feature_count": len(MODEL_FEATURE_COLUMNS),
        "target": TARGET_COLUMN,
        "target_positive_spikes": int(features[TARGET_COLUMN].sum()),
        "target_positive_rate": float(features[TARGET_COLUMN].mean()),
        "splits": split_details,
        "feature_missingness": {
            column: {
                "missing_rows": int(features[column].isna().sum()),
                "missing_rate": float(features[column].isna().mean()),
            }
            for column in MODEL_FEATURE_COLUMNS
        },
        "checks": {
            "one_split_per_patient": True,
            "only_eligible_meals_included": True,
            "future_glucose_columns_excluded_from_model_inputs": True,
            "minutes_until_next_meal_excluded_from_model_inputs": True,
            "patient_and_recording_ids_excluded_from_model_inputs": True,
        },
    }


def generate_features(input_dir: Path, output_dir: Path) -> pd.DataFrame:
    """Read prepared files, build the feature table, and write local outputs."""

    readings, meals, clinical = read_processed_tables(input_dir)
    features = build_feature_table(readings, meals, clinical)
    report = build_feature_report(features)
    output_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_csv(features, output_dir / "model_features.csv")
    atomic_write_json(report, output_dir / "feature_report.json")
    return features


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create leakage-safe meal features from prepared ShanghaiT2DM tables."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/processed/shanghai-t2dm"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed/shanghai-t2dm/modeling"),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    features = generate_features(args.input_dir.resolve(), args.output_dir.resolve())
    print("ShanghaiT2DM feature generation complete")
    print(f"  Eligible meal rows: {len(features)}")
    print(f"  Patients: {features['patient_id'].nunique()}")
    print(f"  Model input features: {len(MODEL_FEATURE_COLUMNS)}")
    print(f"  Positive spike labels: {int(features[TARGET_COLUMN].sum())}")
    print(f"  Output: {args.output_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
