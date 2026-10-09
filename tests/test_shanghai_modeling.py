from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from scripts.build_shanghai_features import (
    FORBIDDEN_MODEL_INPUT_PATTERNS,
    MODEL_FEATURE_COLUMNS,
    TARGET_COLUMN,
    build_feature_table,
)
from scripts.train_shanghai_baseline import train_and_evaluate


class ShanghaiFeatureTest(unittest.TestCase):
    def test_features_use_only_meal_time_and_earlier_readings(self) -> None:
        timestamps = pd.date_range("2022-01-01 06:00", periods=11, freq="15min")
        glucose = [100.0 + index for index in range(9)] + [400.0, 450.0]
        readings = pd.DataFrame(
            {
                "patient_id": "1",
                "recording_id": "1_1_20220101",
                "split": "train",
                "timestamp": timestamps,
                "glucose_mg_dl": glucose,
                "csii_bolus_insulin_iu": [pd.NA] * 8 + [2.0, pd.NA, pd.NA],
                "csii_basal_insulin_iu_per_hour": [pd.NA] * 11,
                "csii_basal_insulin_raw": [pd.NA] * 11,
                "insulin_subcutaneous_raw": [pd.NA] * 11,
                "non_insulin_hypoglycemic_agents_raw": [pd.NA] * 11,
                "insulin_intravenous_raw": [pd.NA] * 11,
            }
        )
        meals = pd.DataFrame(
            {
                "source_dataset": ["ShanghaiT2DM"],
                "cohort": ["type_2_diabetes"],
                "patient_id": ["1"],
                "recording_id": ["1_1_20220101"],
                "split": ["train"],
                "meal_id": ["1_1_20220101_meal_001"],
                "timestamp": [timestamps[8]],
                "dietary_intake_raw": ["Rice 100 g\nVegetable 150 g"],
                "source_file": ["1_1_20220101.xlsx"],
                "source_sheet": ["CGM data"],
                "source_row": [10],
                "eligible_for_initial_model": [True],
                "baseline_glucose_mg_dl": [108.0],
                "minutes_since_previous_meal": [180.0],
                TARGET_COLUMN: [True],
            }
        )
        clinical = pd.DataFrame(
            {
                "patient_id": ["1"],
                "recording_id": ["1_1_20220101"],
                "split": ["train"],
                "sex_code": [1],
                "age_years": [55],
                "bmi_kg_m2": [26.0],
                "diabetes_duration_years": [8],
                "hba1c_percent": [7.2],
                "fasting_plasma_glucose_mg_dl": [130],
            }
        )

        result = build_feature_table(readings, meals, clinical)

        self.assertEqual(len(result), 1)
        row = result.iloc[0]
        self.assertEqual(row["glucose_lag_60_min_mg_dl"], 104.0)
        self.assertEqual(row["glucose_change_prev_60_min_mg_dl"], 4.0)
        self.assertEqual(row["glucose_mean_prev_120_min_mg_dl"], 104.0)
        self.assertEqual(row["glucose_max_prev_120_min_mg_dl"], 108.0)
        self.assertEqual(row["reported_food_weight_g"], 250.0)
        self.assertEqual(row["meal_contains_rice"], 1)
        self.assertEqual(row["meal_contains_vegetable"], 1)
        self.assertEqual(row["has_recorded_csii_bolus_at_meal"], 1)
        self.assertEqual(row["sex_female"], 1)
        self.assertEqual(row[TARGET_COLUMN], 1)
        self.assertFalse(
            any(
                pattern in feature
                for feature in MODEL_FEATURE_COLUMNS
                for pattern in FORBIDDEN_MODEL_INPUT_PATTERNS
            )
        )


class ShanghaiBaselineTest(unittest.TestCase):
    def test_training_writes_reproducible_baseline_outputs(self) -> None:
        rows = []
        sequence = 0
        for split in ("train", "validation", "test"):
            for label in (0, 1, 0, 1):
                sequence += 1
                row = {feature: float((sequence % 3) + label) for feature in MODEL_FEATURE_COLUMNS}
                row.update(
                    {
                        "patient_id": f"P{sequence:03d}",
                        "recording_id": f"R{sequence:03d}",
                        "meal_id": f"M{sequence:03d}",
                        "split": split,
                        TARGET_COLUMN: label,
                    }
                )
                row["baseline_glucose_mg_dl"] = 100.0 + 50.0 * label
                rows.append(row)
        features = pd.DataFrame(rows)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            metadata = train_and_evaluate(
                features,
                root / "outputs",
                root / "models" / "baseline.joblib",
            )

            self.assertIn("validation", metadata["metrics"]["logistic_regression"])
            self.assertTrue(metadata["checks"]["future_outcomes_excluded_from_inputs"])
            self.assertTrue((root / "outputs" / "baseline_metrics.json").is_file())
            self.assertTrue((root / "outputs" / "baseline_predictions.csv").is_file())
            self.assertTrue((root / "outputs" / "baseline_coefficients.csv").is_file())
            self.assertTrue((root / "models" / "baseline.joblib").is_file())


if __name__ == "__main__":
    unittest.main()
