from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from scripts.prepare_shanghai_t2dm import (
    PipelineValidationError,
    prepare_dataset,
)


SOURCE_COLUMNS = [
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
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def example_recording() -> pd.DataFrame:
    timestamps = pd.date_range("2022-01-01 08:00", periods=9, freq="15min")
    frame = pd.DataFrame(index=range(10), columns=SOURCE_COLUMNS)
    frame.loc[:8, "Date"] = timestamps
    frame.loc[:8, "CGM (mg / dl)"] = [100, 115, 135, 160, 190, 180, 165, 150, 140]
    frame.loc[0, "Dietary intake"] = "rice 100 g and vegetables 100 g"
    # A row with no valid observation but with another source event must be audited.
    frame.loc[9, "CSII - basal insulin (Novolin R, IU / H)"] = 0.5
    return frame


def write_source(input_root: Path, *, omit_required_column: bool = False) -> list[Path]:
    recordings = input_root / "Shanghai_T2DM"
    recordings.mkdir(parents=True)
    paths: list[Path] = []
    ids = ["1_1_20220101", "2_1_20220101", "3_1_20220101"]
    for recording_id in ids:
        frame = example_recording()
        if omit_required_column:
            frame = frame.drop(columns=["Dietary intake"])
        path = recordings / f"{recording_id}.xlsx"
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            pd.DataFrame({"note": ["not the measurement sheet"]}).to_excel(
                writer, sheet_name="Notes", index=False
            )
            frame.to_excel(writer, sheet_name="CGM data", index=False)
        paths.append(path)

    pd.DataFrame(
        {
            "Patient Number": ids,
            "Gender (Female=1, Male=2)": [1, 2, 1],
            "Age (years)": [45, 52, 61],
            "HbA1c (%)": [7.1, 8.0, 6.9],
        }
    ).to_excel(input_root / "ShanghaiT2DM_Summary.xlsx", index=False)
    return paths


class ShanghaiPipelineTest(unittest.TestCase):
    def test_pipeline_preserves_sources_and_creates_patient_safe_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_root = root / "source"
            output_dir = root / "processed"
            paths = write_source(input_root)
            before = {path.name: sha256(path) for path in paths}

            result = prepare_dataset(input_root, output_dir)

            self.assertEqual(result.participants, 3)
            self.assertEqual(result.readings, 27)
            self.assertEqual(result.rejected_rows, 3)
            self.assertEqual(before, {path.name: sha256(path) for path in paths})

            meals = pd.read_csv(output_dir / "meal_events.csv")
            self.assertEqual(len(meals), 3)
            self.assertTrue(meals["eligible_for_initial_model"].all())
            self.assertTrue(meals["spike_within_120_min"].all())
            self.assertTrue((meals["glucose_at_120_min_mg_dl"] == 140).all())

            splits = pd.read_csv(output_dir / "patient_splits.csv")
            self.assertEqual(set(splits["split"]), {"train", "validation", "test"})
            self.assertEqual(splits["patient_id"].nunique(), 3)

            report = json.loads((output_dir / "quality_report.json").read_text())
            self.assertFalse(report["source_is_modified"])
            self.assertEqual(report["rejected"]["rows_that_contained_another_event_value"], 3)

    def test_missing_required_source_column_fails_loudly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_root = root / "source"
            write_source(input_root, omit_required_column=True)

            with self.assertRaisesRegex(PipelineValidationError, "Required fields missing"):
                prepare_dataset(input_root, root / "processed")


if __name__ == "__main__":
    unittest.main()
