#!/usr/bin/env python3
"""Prepare the open ShanghaiT2DM workbooks for reproducible modelling.

The script never changes the downloaded source workbooks. It creates local,
derived CSV files and a JSON quality report under data/processed/.
"""

from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


DATASET_NAME = "ShanghaiT2DM"
COHORT = "type_2_diabetes"
MODEL_HORIZON_MINUTES = 120
GLUCOSE_THRESHOLD_MG_DL = 180.0
RISE_THRESHOLD_MG_DL = 40.0
MINIMUM_MEAL_GAP_MINUTES = 120

REQUIRED_READING_COLUMNS = {
    "Date",
    "CGM (mg / dl)",
    "CBG (mg / dl)",
    "Blood Ketone (mmol / L)",
    "Dietary intake",
    "Insulin dose - s.c.",
    "Non-insulin hypoglycemic agents",
    "CSII - bolus insulin (Novolin R, IU)",
    "CSII - basal insulin (Novolin R, IU / H)",
    "Insulin dose - i.v.",
}

RECORDING_PATTERN = re.compile(
    r"^(?P<patient_id>\d+)_(?P<visit_number>\d+)_(?P<start_date>\d{8})$"
)

CLINICAL_COLUMN_MAP = {
    "Patient Number": "recording_id",
    "Gender (Female=1, Male=2)": "sex_code",
    "Age (years)": "age_years",
    "Height (m)": "height_m",
    "Weight (kg)": "weight_kg",
    "BMI (kg/m2)": "bmi_kg_m2",
    "Smoking History (pack year)": "smoking_pack_years",
    "Alcohol Drinking History (drinker/non-drinker)": "alcohol_history",
    "Type of Diabetes": "diabetes_type",
    "Duration of diabetes (years)": "diabetes_duration_years",
    "Acute Diabetic Complications": "acute_diabetic_complications",
    "Diabetic Macrovascular Complications": "macrovascular_complications",
    "Diabetic Microvascular Complications": "microvascular_complications",
    "Comorbidities": "comorbidities",
    "Hypoglycemic Agents": "hypoglycemic_agents",
    "Other Agents": "other_agents",
    "Fasting Plasma Glucose (mg/dl)": "fasting_plasma_glucose_mg_dl",
    "2-hour Postprandial Plasma Glucose (mg/dl)": (
        "postprandial_2h_plasma_glucose_mg_dl"
    ),
    "Fasting C-peptide (nmol/L)": "fasting_c_peptide_nmol_l",
    "2-hour Postprandial C-peptide (nmol/L)": (
        "postprandial_2h_c_peptide_nmol_l"
    ),
    "Fasting Insulin (pmol/L)": "fasting_insulin_pmol_l",
    "2-hour Postprandial insulin (pmol/L)": "postprandial_2h_insulin_pmol_l",
    "HbA1c (%)": "hba1c_percent",
    "Glycated Albumin (%)": "glycated_albumin_percent",
    "Total Cholesterol (mmol/L)": "total_cholesterol_mmol_l",
    "Triglyceride (mmol/L)": "triglyceride_mmol_l",
    "High-Density Lipoprotein Cholesterol (mmol/L)": "hdl_cholesterol_mmol_l",
    "Low-Density Lipoprotein Cholesterol (mmol/L)": "ldl_cholesterol_mmol_l",
    "Creatinine (umol/L)": "creatinine_umol_l",
    "Estimated Glomerular Filtration Rate (ml/min/1.73m2)": "egfr_ml_min_1_73m2",
    "Uric Acid (mmol/L)": "uric_acid_mmol_l",
    "Blood Urea Nitrogen (mmol/L)": "blood_urea_nitrogen_mmol_l",
    "Hypoglycemia (yes/no)": "hypoglycemia_yes_no",
}

READING_OUTPUT_COLUMNS = [
    "source_dataset",
    "cohort",
    "patient_id",
    "recording_id",
    "visit_number",
    "recording_start_date",
    "split",
    "source_file",
    "source_sheet",
    "source_row",
    "timestamp",
    "glucose_mg_dl",
    "cbg_mg_dl",
    "blood_ketone_mmol_l",
    "dietary_intake_raw",
    "insulin_subcutaneous_raw",
    "non_insulin_hypoglycemic_agents_raw",
    "csii_bolus_insulin_iu",
    "csii_basal_insulin_iu_per_hour",
    "csii_basal_insulin_raw",
    "insulin_intravenous_raw",
]


class PipelineValidationError(ValueError):
    """Raised when the source data violates a safety-critical pipeline rule."""


@dataclass(frozen=True)
class PipelineResult:
    """Paths and row counts produced by one pipeline run."""

    output_dir: Path
    readings: int
    clinical_records: int
    meal_events: int
    eligible_meal_events: int
    rejected_rows: int
    participants: int


def normalise_header(value: object) -> str:
    """Trim a column heading and collapse repeated whitespace."""

    return " ".join(str(value).strip().split())


def generic_column_name(value: object) -> str:
    """Create a readable snake_case fallback for an unexpected heading."""

    text = normalise_header(value).lower()
    text = text.replace("%", " percent ")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "unnamed_column"


def clean_text(series: pd.Series) -> pd.Series:
    """Keep source text while representing empty cells as missing."""

    def clean(value: object) -> object:
        if pd.isna(value):
            return pd.NA
        text = str(value).strip()
        return text if text else pd.NA

    return series.map(clean).astype("string")


def parse_recording_id(recording_id: str) -> dict[str, Any]:
    """Parse patient, visit, and nominal start date from a file stem."""

    match = RECORDING_PATTERN.fullmatch(recording_id)
    if not match:
        raise PipelineValidationError(
            f"Recording name does not match patient_visit_YYYYMMDD: {recording_id}"
        )
    values = match.groupdict()
    return {
        "patient_id": values["patient_id"],
        "visit_number": int(values["visit_number"]),
        "recording_start_date": pd.to_datetime(
            values["start_date"], format="%Y%m%d"
        ),
    }


def find_reading_sheet(path: Path) -> tuple[str, pd.DataFrame]:
    """Find the one worksheet containing the required Date and CGM fields.

    Sheet names vary considerably and some workbooks contain pump schedules.
    Selecting by schema is therefore safer than selecting by sheet position.
    """

    candidates: list[tuple[str, pd.DataFrame]] = []
    with pd.ExcelFile(path) as workbook:
        sheet_names = workbook.sheet_names.copy()
        for sheet_name in sheet_names:
            frame = workbook.parse(sheet_name=sheet_name)
            frame.columns = [normalise_header(column) for column in frame.columns]
            if {"Date", "CGM (mg / dl)"}.issubset(frame.columns):
                candidates.append((sheet_name, frame))

    if len(candidates) != 1:
        raise PipelineValidationError(
            f"Expected exactly one Date/CGM sheet in {path.name}; "
            f"found {len(candidates)}. Sheets: {sheet_names}"
        )

    sheet_name, frame = candidates[0]
    missing = sorted(REQUIRED_READING_COLUMNS.difference(frame.columns))
    if missing:
        raise PipelineValidationError(
            f"Required fields missing from {path.name}/{sheet_name}: {missing}"
        )
    return sheet_name, frame


def rejection_reason(frame: pd.DataFrame) -> pd.Series:
    """Describe why a source row cannot become a glucose observation."""

    bad_time = frame["timestamp"].isna()
    bad_glucose = frame["glucose_mg_dl"].isna()
    reason = pd.Series("", index=frame.index, dtype="string")
    reason.loc[bad_time & bad_glucose] = "missing_timestamp_and_glucose"
    reason.loc[bad_time & ~bad_glucose] = "missing_or_invalid_timestamp"
    reason.loc[~bad_time & bad_glucose] = "missing_or_invalid_glucose"
    return reason


def prepare_recordings(
    source_files: list[Path],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Read and standardise every recording workbook."""

    valid_frames: list[pd.DataFrame] = []
    rejected_frames: list[pd.DataFrame] = []
    sheet_names: Counter[str] = Counter()
    extension_counts: Counter[str] = Counter()
    total_source_rows = 0

    for path in source_files:
        metadata = parse_recording_id(path.stem)
        sheet_name, raw = find_reading_sheet(path)
        sheet_names[sheet_name] += 1
        extension_counts[path.suffix.lower()] += 1
        total_source_rows += len(raw)

        frame = pd.DataFrame(index=raw.index)
        frame["source_dataset"] = DATASET_NAME
        frame["cohort"] = COHORT
        frame["patient_id"] = metadata["patient_id"]
        frame["recording_id"] = path.stem
        frame["visit_number"] = metadata["visit_number"]
        frame["recording_start_date"] = metadata["recording_start_date"]
        frame["source_file"] = path.name
        frame["source_sheet"] = sheet_name
        frame["source_row"] = raw.index.to_series().astype(int) + 2
        frame["timestamp"] = pd.to_datetime(raw["Date"], errors="coerce")
        frame["glucose_mg_dl"] = pd.to_numeric(
            raw["CGM (mg / dl)"], errors="coerce"
        )
        frame["cbg_mg_dl"] = pd.to_numeric(raw["CBG (mg / dl)"], errors="coerce")
        frame["blood_ketone_mmol_l"] = pd.to_numeric(
            raw["Blood Ketone (mmol / L)"], errors="coerce"
        )
        frame["dietary_intake_raw"] = clean_text(raw["Dietary intake"])
        frame["insulin_subcutaneous_raw"] = clean_text(
            raw["Insulin dose - s.c."]
        )
        frame["non_insulin_hypoglycemic_agents_raw"] = clean_text(
            raw["Non-insulin hypoglycemic agents"]
        )
        frame["csii_bolus_insulin_iu"] = pd.to_numeric(
            raw["CSII - bolus insulin (Novolin R, IU)"], errors="coerce"
        )
        frame["csii_basal_insulin_iu_per_hour"] = pd.to_numeric(
            raw["CSII - basal insulin (Novolin R, IU / H)"], errors="coerce"
        )
        frame["csii_basal_insulin_raw"] = clean_text(
            raw["CSII - basal insulin (Novolin R, IU / H)"]
        )
        frame["insulin_intravenous_raw"] = clean_text(raw["Insulin dose - i.v."])

        invalid = frame["timestamp"].isna() | frame["glucose_mg_dl"].isna()
        if invalid.any():
            rejected = frame.loc[invalid].copy()
            rejected["rejection_reason"] = rejection_reason(rejected)
            rejected_frames.append(rejected)
        valid_frames.append(frame.loc[~invalid].copy())

    readings = pd.concat(valid_frames, ignore_index=True)
    readings = readings.sort_values(
        ["patient_id", "recording_id", "timestamp", "source_row"]
    ).reset_index(drop=True)

    duplicate_count = int(
        readings.duplicated(["recording_id", "timestamp"], keep=False).sum()
    )
    if duplicate_count:
        raise PipelineValidationError(
            f"Found {duplicate_count} valid rows with duplicate recording timestamps"
        )

    if rejected_frames:
        rejected_rows = pd.concat(rejected_frames, ignore_index=True)
    else:
        rejected_rows = pd.DataFrame(
            columns=[column for column in READING_OUTPUT_COLUMNS if column != "split"]
            + ["rejection_reason"]
        )

    diagnostics = {
        "recording_files": len(source_files),
        "file_extensions": dict(sorted(extension_counts.items())),
        "distinct_reading_sheet_names": len(sheet_names),
        "source_rows": total_source_rows,
        "valid_reading_rows": len(readings),
        "rejected_rows": len(rejected_rows),
        "duplicate_valid_recording_timestamps": duplicate_count,
    }
    return readings, rejected_rows, diagnostics


def create_patient_splits(
    patient_ids: list[str], seed: int
) -> pd.DataFrame:
    """Create deterministic 70/15/15 patient-level splits."""

    unique_ids = sorted(set(patient_ids))
    if len(unique_ids) < 3:
        raise PipelineValidationError(
            "At least three patients are required for train/validation/test splits"
        )

    shuffled = unique_ids.copy()
    random.Random(seed).shuffle(shuffled)

    train_count = max(1, int(len(shuffled) * 0.70))
    validation_count = max(1, int(len(shuffled) * 0.15))
    if train_count + validation_count >= len(shuffled):
        train_count = len(shuffled) - 2
        validation_count = 1

    assignments: dict[str, str] = {}
    for patient_id in shuffled[:train_count]:
        assignments[patient_id] = "train"
    for patient_id in shuffled[
        train_count : train_count + validation_count
    ]:
        assignments[patient_id] = "validation"
    for patient_id in shuffled[train_count + validation_count :]:
        assignments[patient_id] = "test"

    result = pd.DataFrame(
        {
            "source_dataset": DATASET_NAME,
            "patient_id": unique_ids,
            "split": [assignments[patient_id] for patient_id in unique_ids],
            "split_seed": seed,
        }
    )
    if result["patient_id"].duplicated().any():
        raise PipelineValidationError("A patient was assigned to more than one split")
    return result


def add_split(frame: pd.DataFrame, splits: pd.DataFrame) -> pd.DataFrame:
    """Attach a split and fail if any participant is unassigned."""

    result = frame.merge(
        splits[["patient_id", "split"]], on="patient_id", how="left", validate="m:1"
    )
    if result["split"].isna().any():
        missing = sorted(result.loc[result["split"].isna(), "patient_id"].unique())
        raise PipelineValidationError(f"Missing split assignment for patients: {missing}")
    return result


def prepare_clinical_records(
    summary_path: Path,
    recording_ids: set[str],
    splits: pd.DataFrame,
) -> pd.DataFrame:
    """Standardise the recording-level clinical summary."""

    frame = pd.read_excel(summary_path)
    frame.columns = [normalise_header(column) for column in frame.columns]
    if "Patient Number" not in frame.columns:
        raise PipelineValidationError("Clinical summary has no Patient Number column")

    rename_map = {
        column: CLINICAL_COLUMN_MAP.get(column, generic_column_name(column))
        for column in frame.columns
    }
    frame = frame.rename(columns=rename_map)
    frame["recording_id"] = frame["recording_id"].astype("string").str.strip()

    summary_ids = set(frame["recording_id"].dropna().astype(str))
    if summary_ids != recording_ids:
        missing_summary = sorted(recording_ids - summary_ids)
        missing_file = sorted(summary_ids - recording_ids)
        raise PipelineValidationError(
            "Recording/clinical-summary mismatch. "
            f"Missing summary rows: {missing_summary}; missing files: {missing_file}"
        )
    if frame["recording_id"].duplicated().any():
        raise PipelineValidationError("Clinical summary contains duplicate recording IDs")

    parsed = frame["recording_id"].map(parse_recording_id)
    frame.insert(0, "source_dataset", DATASET_NAME)
    frame.insert(1, "cohort", COHORT)
    frame.insert(2, "patient_id", parsed.map(lambda value: value["patient_id"]))
    frame.insert(4, "visit_number", parsed.map(lambda value: value["visit_number"]))
    frame.insert(
        5,
        "recording_start_date",
        parsed.map(lambda value: value["recording_start_date"]),
    )
    frame.insert(6, "source_summary_row", range(2, len(frame) + 2))
    frame = add_split(frame, splits)

    leading = [
        "source_dataset",
        "cohort",
        "patient_id",
        "recording_id",
        "visit_number",
        "recording_start_date",
        "split",
        "source_summary_row",
    ]
    trailing = [column for column in frame.columns if column not in leading]
    return frame[leading + trailing].sort_values("recording_id").reset_index(drop=True)


def is_meal_text_available(series: pd.Series) -> pd.Series:
    """Mark meal descriptions that contain more than a missing-data message."""

    normalised = series.astype("string").str.strip().str.lower()
    placeholder = normalised.str.fullmatch(
        r"(?:data\s+)?not\s+available|n/?a|none|unknown", na=True
    )
    return series.notna() & ~placeholder


def build_meal_events(
    readings: pd.DataFrame,
    horizon_minutes: int,
    glucose_threshold_mg_dl: float,
    rise_threshold_mg_dl: float,
    minimum_meal_gap_minutes: int,
) -> pd.DataFrame:
    """Create meal rows with exact and within-horizon future outcomes.

    Future outcome columns are labels for later modelling. They must never be
    included among the model's input features.
    """

    meals = readings.loc[readings["dietary_intake_raw"].notna()].copy()
    meals = meals.sort_values(["recording_id", "timestamp"]).reset_index(drop=True)
    meals["meal_sequence"] = meals.groupby("recording_id").cumcount() + 1
    meals["meal_id"] = meals.apply(
        lambda row: f"{row['recording_id']}_meal_{int(row['meal_sequence']):03d}",
        axis=1,
    )
    meals["meal_text_available"] = is_meal_text_available(
        meals["dietary_intake_raw"]
    )
    meals["minutes_since_previous_meal"] = (
        meals.groupby("recording_id")["timestamp"]
        .diff()
        .dt.total_seconds()
        .div(60)
    )
    meals["minutes_until_next_meal"] = (
        meals.groupby("recording_id")["timestamp"]
        .shift(-1)
        .sub(meals["timestamp"])
        .dt.total_seconds()
        .div(60)
    )
    meals["isolated_meal_120_min"] = (
        meals["minutes_since_previous_meal"].isna()
        | (
            meals["minutes_since_previous_meal"]
            >= minimum_meal_gap_minutes
        )
    ) & (
        meals["minutes_until_next_meal"].isna()
        | (meals["minutes_until_next_meal"] >= minimum_meal_gap_minutes)
    )

    meals["baseline_glucose_mg_dl"] = meals["glucose_mg_dl"]
    meals["target_timestamp"] = meals["timestamp"] + pd.to_timedelta(
        horizon_minutes, unit="m"
    )

    lookup = readings.set_index(["recording_id", "timestamp"])["glucose_mg_dl"]
    target_index = pd.MultiIndex.from_arrays(
        [meals["recording_id"], meals["target_timestamp"]], names=lookup.index.names
    )
    meals["glucose_at_120_min_mg_dl"] = lookup.reindex(target_index).to_numpy()
    meals["glucose_change_at_120_min_mg_dl"] = (
        meals["glucose_at_120_min_mg_dl"] - meals["baseline_glucose_mg_dl"]
    )

    max_future: dict[int, float] = {}
    for recording_id, group in readings.groupby("recording_id", sort=False):
        group = group.sort_values("timestamp").reset_index(drop=True)
        timestamps = group["timestamp"]
        glucose = group["glucose_mg_dl"]
        meal_indexes = meals.index[meals["recording_id"] == recording_id]
        for meal_index in meal_indexes:
            meal_time = meals.at[meal_index, "timestamp"]
            target_time = meals.at[meal_index, "target_timestamp"]
            start = int(timestamps.searchsorted(meal_time, side="right"))
            end = int(timestamps.searchsorted(target_time, side="right"))
            future_values = glucose.iloc[start:end]
            if not future_values.empty:
                max_future[meal_index] = float(future_values.max())

    meals["max_glucose_next_120_min_mg_dl"] = pd.Series(max_future)
    meals["max_rise_next_120_min_mg_dl"] = (
        meals["max_glucose_next_120_min_mg_dl"]
        - meals["baseline_glucose_mg_dl"]
    )

    outcome_available = meals["max_glucose_next_120_min_mg_dl"].notna()
    high_glucose = pd.Series(pd.NA, index=meals.index, dtype="boolean")
    high_glucose.loc[outcome_available] = (
        meals.loc[outcome_available, "max_glucose_next_120_min_mg_dl"]
        >= glucose_threshold_mg_dl
    )
    sharp_rise = pd.Series(pd.NA, index=meals.index, dtype="boolean")
    sharp_rise.loc[outcome_available] = (
        meals.loc[outcome_available, "max_rise_next_120_min_mg_dl"]
        >= rise_threshold_mg_dl
    )
    meals["reaches_180_mg_dl_within_120_min"] = high_glucose
    meals["rises_40_mg_dl_within_120_min"] = sharp_rise
    meals["spike_within_120_min"] = high_glucose | sharp_rise
    meals["eligible_for_initial_model"] = (
        meals["meal_text_available"]
        & meals["isolated_meal_120_min"]
        & meals["glucose_at_120_min_mg_dl"].notna()
        & outcome_available
    )

    columns = [
        "source_dataset",
        "cohort",
        "patient_id",
        "recording_id",
        "split",
        "meal_id",
        "meal_sequence",
        "timestamp",
        "target_timestamp",
        "dietary_intake_raw",
        "meal_text_available",
        "minutes_since_previous_meal",
        "minutes_until_next_meal",
        "isolated_meal_120_min",
        "baseline_glucose_mg_dl",
        "glucose_at_120_min_mg_dl",
        "glucose_change_at_120_min_mg_dl",
        "max_glucose_next_120_min_mg_dl",
        "max_rise_next_120_min_mg_dl",
        "reaches_180_mg_dl_within_120_min",
        "rises_40_mg_dl_within_120_min",
        "spike_within_120_min",
        "eligible_for_initial_model",
        "source_file",
        "source_sheet",
        "source_row",
    ]
    return meals[columns]


def interval_counts(readings: pd.DataFrame) -> dict[str, int]:
    """Count time gaps between consecutive readings within a recording."""

    minutes = (
        readings.groupby("recording_id")["timestamp"]
        .diff()
        .dt.total_seconds()
        .div(60)
        .dropna()
        .round(3)
    )
    counts = Counter(float(value) for value in minutes)
    return {f"{value:g}": count for value, count in sorted(counts.items())}


def bool_count(series: pd.Series) -> int:
    """Count true values while tolerating nullable booleans."""

    return int(series.fillna(False).astype(bool).sum())


def build_quality_report(
    readings: pd.DataFrame,
    clinical: pd.DataFrame,
    meals: pd.DataFrame,
    rejected: pd.DataFrame,
    splits: pd.DataFrame,
    recording_diagnostics: dict[str, Any],
    horizon_minutes: int,
    glucose_threshold_mg_dl: float,
    rise_threshold_mg_dl: float,
    minimum_meal_gap_minutes: int,
    seed: int,
) -> dict[str, Any]:
    """Create a machine-readable record of what the pipeline accepted."""

    event_columns = [
        "cbg_mg_dl",
        "blood_ketone_mmol_l",
        "dietary_intake_raw",
        "insulin_subcutaneous_raw",
        "non_insulin_hypoglycemic_agents_raw",
        "csii_bolus_insulin_iu",
        "csii_basal_insulin_raw",
        "insulin_intravenous_raw",
    ]
    eligible = meals["eligible_for_initial_model"]
    split_details: dict[str, Any] = {}
    for split_name in ["train", "validation", "test"]:
        split_meals = meals[meals["split"] == split_name]
        split_eligible = split_meals["eligible_for_initial_model"]
        split_details[split_name] = {
            "patients": int((splits["split"] == split_name).sum()),
            "glucose_rows": int((readings["split"] == split_name).sum()),
            "meal_events": len(split_meals),
            "eligible_meal_events": bool_count(split_eligible),
            "eligible_positive_spikes": bool_count(
                split_meals.loc[split_eligible, "spike_within_120_min"]
            ),
        }

    rejected_with_events = 0
    if not rejected.empty:
        rejected_with_events = int(rejected[event_columns].notna().any(axis=1).sum())

    return {
        "dataset": DATASET_NAME,
        "cohort": COHORT,
        "pipeline_version": 1,
        "source_is_modified": False,
        "recordings": recording_diagnostics,
        "participants": {
            "unique_patients": int(readings["patient_id"].nunique()),
            "clinical_recording_rows": len(clinical),
        },
        "glucose": {
            "rows": len(readings),
            "minimum_mg_dl": float(readings["glucose_mg_dl"].min()),
            "maximum_mg_dl": float(readings["glucose_mg_dl"].max()),
            "first_timestamp": readings["timestamp"].min().isoformat(),
            "last_timestamp": readings["timestamp"].max().isoformat(),
            "interval_minutes_counts": interval_counts(readings),
        },
        "events": {
            column: int(readings[column].notna().sum()) for column in event_columns
        },
        "meals": {
            "all_recorded_meal_rows": len(meals),
            "meal_text_available": bool_count(meals["meal_text_available"]),
            "exact_120_minute_target_available": int(
                meals["glucose_at_120_min_mg_dl"].notna().sum()
            ),
            "isolated_for_120_minutes": bool_count(
                meals["isolated_meal_120_min"]
            ),
            "eligible_for_initial_model": bool_count(eligible),
            "eligible_patients": int(meals.loc[eligible, "patient_id"].nunique()),
            "eligible_positive_spikes": bool_count(
                meals.loc[eligible, "spike_within_120_min"]
            ),
        },
        "target_definition": {
            "horizon_minutes": horizon_minutes,
            "spike_if_max_glucose_at_least_mg_dl": glucose_threshold_mg_dl,
            "or_max_rise_at_least_mg_dl": rise_threshold_mg_dl,
            "minimum_gap_from_other_meals_minutes": minimum_meal_gap_minutes,
            "exact_120_minute_glucose_is_also_retained_for_regression": True,
        },
        "splits": {
            "method": "deterministic patient-level 70/15/15 split",
            "seed": seed,
            "details": split_details,
        },
        "rejected": {
            "rows": len(rejected),
            "rows_that_contained_another_event_value": rejected_with_events,
        },
        "checks": {
            "recording_ids_match_clinical_summary": True,
            "duplicate_valid_recording_timestamps": 0,
            "every_patient_has_exactly_one_split": True,
            "future_target_columns_are_labels_not_features": True,
        },
    }


def atomic_write_csv(frame: pd.DataFrame, path: Path) -> None:
    """Write a CSV completely before replacing an older generated copy."""

    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False, date_format="%Y-%m-%dT%H:%M:%S")
    temporary.replace(path)


def atomic_write_json(value: dict[str, Any], path: Path) -> None:
    """Write JSON completely before replacing an older generated copy."""

    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def prepare_dataset(
    input_root: Path,
    output_dir: Path,
    *,
    seed: int = 42,
    horizon_minutes: int = MODEL_HORIZON_MINUTES,
    glucose_threshold_mg_dl: float = GLUCOSE_THRESHOLD_MG_DL,
    rise_threshold_mg_dl: float = RISE_THRESHOLD_MG_DL,
    minimum_meal_gap_minutes: int = MINIMUM_MEAL_GAP_MINUTES,
) -> PipelineResult:
    """Run the complete preparation pipeline and write derived outputs."""

    expected_definition = (
        MODEL_HORIZON_MINUTES,
        GLUCOSE_THRESHOLD_MG_DL,
        RISE_THRESHOLD_MG_DL,
        MINIMUM_MEAL_GAP_MINUTES,
    )
    supplied_definition = (
        horizon_minutes,
        glucose_threshold_mg_dl,
        rise_threshold_mg_dl,
        minimum_meal_gap_minutes,
    )
    if supplied_definition != expected_definition:
        raise PipelineValidationError(
            "Version 1 has a fixed, documented target: 120-minute horizon, "
            "180 mg/dL glucose threshold, 40 mg/dL rise threshold, and "
            "120-minute meal-isolation gap. Change the schema and documentation "
            "before changing those values."
        )

    recordings_dir = input_root / "Shanghai_T2DM"
    summary_path = input_root / "ShanghaiT2DM_Summary.xlsx"
    if not recordings_dir.is_dir():
        raise FileNotFoundError(f"Missing recording directory: {recordings_dir}")
    if not summary_path.is_file():
        raise FileNotFoundError(f"Missing clinical summary: {summary_path}")

    source_files = sorted(
        path
        for path in recordings_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".xls", ".xlsx"}
    )
    if not source_files:
        raise PipelineValidationError(f"No .xls/.xlsx files found in {recordings_dir}")

    readings, rejected, recording_diagnostics = prepare_recordings(source_files)
    splits = create_patient_splits(readings["patient_id"].astype(str).tolist(), seed)
    readings = add_split(readings, splits)
    readings = readings[READING_OUTPUT_COLUMNS]

    clinical = prepare_clinical_records(
        summary_path,
        set(readings["recording_id"].astype(str)),
        splits,
    )
    meals = build_meal_events(
        readings,
        horizon_minutes,
        glucose_threshold_mg_dl,
        rise_threshold_mg_dl,
        minimum_meal_gap_minutes,
    )
    report = build_quality_report(
        readings,
        clinical,
        meals,
        rejected,
        splits,
        recording_diagnostics,
        horizon_minutes,
        glucose_threshold_mg_dl,
        rise_threshold_mg_dl,
        minimum_meal_gap_minutes,
        seed,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_csv(readings, output_dir / "glucose_readings.csv")
    atomic_write_csv(clinical, output_dir / "clinical_records.csv")
    atomic_write_csv(meals, output_dir / "meal_events.csv")
    atomic_write_csv(splits, output_dir / "patient_splits.csv")
    atomic_write_csv(rejected, output_dir / "rejected_rows.csv")
    atomic_write_json(report, output_dir / "quality_report.json")

    return PipelineResult(
        output_dir=output_dir,
        readings=len(readings),
        clinical_records=len(clinical),
        meal_events=len(meals),
        eligible_meal_events=bool_count(meals["eligible_for_initial_model"]),
        rejected_rows=len(rejected),
        participants=int(readings["patient_id"].nunique()),
    )


def build_parser() -> argparse.ArgumentParser:
    """Define documented command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Prepare ShanghaiT2DM workbooks without changing the raw files."
    )
    parser.add_argument(
        "--input-root",
        type=Path,
        default=Path("data/external/datasets/shanghai-v5"),
        help="Folder containing Shanghai_T2DM and ShanghaiT2DM_Summary.xlsx",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed/shanghai-t2dm"),
        help="Local folder for generated CSV files and quality_report.json",
    )
    parser.add_argument("--seed", type=int, default=42, help="Patient split seed")
    return parser


def main() -> int:
    """Run from the command line and print a beginner-readable summary."""

    args = build_parser().parse_args()
    result = prepare_dataset(
        args.input_root.resolve(),
        args.output_dir.resolve(),
        seed=args.seed,
    )
    print("ShanghaiT2DM preparation complete")
    print(f"  Participants: {result.participants}")
    print(f"  Valid glucose rows: {result.readings}")
    print(f"  Clinical recording rows: {result.clinical_records}")
    print(f"  Recorded meal rows: {result.meal_events}")
    print(f"  Initially eligible meal rows: {result.eligible_meal_events}")
    print(f"  Rejected source rows: {result.rejected_rows}")
    print(f"  Output: {result.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
