#!/usr/bin/env python3
"""Train and evaluate the first ShanghaiT2DM spike-classification baseline."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from scripts.build_shanghai_features import (
    FORBIDDEN_MODEL_INPUT_PATTERNS,
    MODEL_FEATURE_COLUMNS,
    TARGET_COLUMN,
)
from scripts.prepare_shanghai_t2dm import (
    PipelineValidationError,
    atomic_write_csv,
    atomic_write_json,
)


RANDOM_SEED = 42
DECISION_THRESHOLD = 0.5


def validate_feature_table(frame: pd.DataFrame) -> None:
    """Check split integrity, target values, and the explicit no-leakage contract."""

    required = {
        "patient_id",
        "recording_id",
        "meal_id",
        "split",
        TARGET_COLUMN,
        *MODEL_FEATURE_COLUMNS,
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise PipelineValidationError(f"Feature table is missing columns: {missing}")
    unsafe = [
        feature
        for feature in MODEL_FEATURE_COLUMNS
        if any(pattern in feature for pattern in FORBIDDEN_MODEL_INPUT_PATTERNS)
    ]
    if unsafe:
        raise PipelineValidationError(f"Future fields reached model inputs: {unsafe}")
    if frame["meal_id"].duplicated().any():
        raise PipelineValidationError("Feature table contains duplicate meal IDs")
    if frame.groupby("patient_id")["split"].nunique().max() != 1:
        raise PipelineValidationError("A patient appears in more than one split")
    expected_splits = {"train", "validation", "test"}
    found_splits = set(frame["split"].dropna().astype(str))
    if found_splits != expected_splits:
        raise PipelineValidationError(
            f"Expected splits {sorted(expected_splits)}; found {sorted(found_splits)}"
        )
    if frame[TARGET_COLUMN].isna().any():
        raise PipelineValidationError("Feature table contains a missing target")
    if not set(frame[TARGET_COLUMN].astype(int).unique()).issubset({0, 1}):
        raise PipelineValidationError("Target must contain only 0 and 1")
    if frame[MODEL_FEATURE_COLUMNS].select_dtypes(exclude="number").columns.tolist():
        columns = frame[MODEL_FEATURE_COLUMNS].select_dtypes(
            exclude="number"
        ).columns.tolist()
        raise PipelineValidationError(f"Non-numeric model inputs found: {columns}")
    for split_name in expected_splits:
        labels = frame.loc[frame["split"] == split_name, TARGET_COLUMN].nunique()
        if labels != 2:
            raise PipelineValidationError(
                f"Split {split_name} does not contain both target classes"
            )


def build_logistic_pipeline() -> Pipeline:
    """Create a train-only imputation, scaling, and Logistic Regression pipeline."""

    return Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median",
                    add_indicator=True,
                    keep_empty_features=True,
                ),
            ),
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2_000,
                    random_state=RANDOM_SEED,
                ),
            ),
        ]
    )


def positive_probabilities(model: Any, inputs: pd.DataFrame) -> pd.Series:
    """Return class-1 probabilities from a fitted sklearn classifier."""

    probabilities = model.predict_proba(inputs)
    classes = list(model.classes_)
    if 1 not in classes:
        return pd.Series(0.0, index=inputs.index)
    return pd.Series(probabilities[:, classes.index(1)], index=inputs.index)


def classification_metrics(
    truth: pd.Series,
    probability: pd.Series,
    threshold: float = DECISION_THRESHOLD,
) -> dict[str, Any]:
    """Calculate understandable binary-classification metrics and error counts."""

    truth = truth.astype(int)
    prediction = (probability >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(truth, prediction, labels=[0, 1]).ravel()
    return {
        "rows": len(truth),
        "positive_labels": int(truth.sum()),
        "positive_label_rate": float(truth.mean()),
        "predicted_positive_rate": float(prediction.mean()),
        "decision_threshold": threshold,
        "accuracy": float(accuracy_score(truth, prediction)),
        "balanced_accuracy": float(balanced_accuracy_score(truth, prediction)),
        "precision": float(precision_score(truth, prediction, zero_division=0)),
        "recall": float(recall_score(truth, prediction, zero_division=0)),
        "f1": float(f1_score(truth, prediction, zero_division=0)),
        "roc_auc": float(roc_auc_score(truth, probability)),
        "average_precision": float(average_precision_score(truth, probability)),
        "brier_score": float(brier_score_loss(truth, probability)),
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp),
        },
    }


def coefficient_table(model: Pipeline) -> pd.DataFrame:
    """Return standardized Logistic Regression coefficients for interpretation."""

    imputer = model.named_steps["imputer"]
    classifier = model.named_steps["classifier"]
    names = imputer.get_feature_names_out(MODEL_FEATURE_COLUMNS)
    coefficients = classifier.coef_[0]
    if len(names) != len(coefficients):
        raise PipelineValidationError("Coefficient names do not match fitted coefficients")
    frame = pd.DataFrame(
        {
            "model_input_after_imputation": names,
            "standardized_coefficient": coefficients,
        }
    )
    frame["absolute_coefficient"] = frame["standardized_coefficient"].abs()
    frame["association_direction"] = frame["standardized_coefficient"].map(
        lambda value: "higher predicted spike probability" if value > 0 else (
            "lower predicted spike probability" if value < 0 else "no linear association"
        )
    )
    return frame.sort_values("absolute_coefficient", ascending=False).reset_index(drop=True)


def atomic_joblib_dump(model: Pipeline, path: Path) -> None:
    """Write a model completely before replacing an older generated copy."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    joblib.dump(model, temporary)
    temporary.replace(path)


def train_and_evaluate(
    features: pd.DataFrame,
    output_dir: Path,
    model_path: Path,
) -> dict[str, Any]:
    """Fit on training patients and evaluate untouched validation/test patients."""

    validate_feature_table(features)
    train = features.loc[features["split"] == "train"].copy()
    logistic = build_logistic_pipeline()
    logistic.fit(train[MODEL_FEATURE_COLUMNS], train[TARGET_COLUMN].astype(int))

    majority = DummyClassifier(strategy="most_frequent", random_state=RANDOM_SEED)
    majority.fit(train[MODEL_FEATURE_COLUMNS], train[TARGET_COLUMN].astype(int))

    metrics: dict[str, dict[str, Any]] = {
        "logistic_regression": {},
        "majority_class": {},
    }
    prediction_frames: list[pd.DataFrame] = []
    for split_name in ("train", "validation", "test"):
        split = features.loc[features["split"] == split_name].copy()
        inputs = split[MODEL_FEATURE_COLUMNS]
        truth = split[TARGET_COLUMN].astype(int)
        logistic_probability = positive_probabilities(logistic, inputs)
        majority_probability = positive_probabilities(majority, inputs)
        metrics["logistic_regression"][split_name] = classification_metrics(
            truth, logistic_probability
        )
        metrics["majority_class"][split_name] = classification_metrics(
            truth, majority_probability
        )
        if split_name != "train":
            prediction_frames.append(
                pd.DataFrame(
                    {
                        "patient_id": split["patient_id"],
                        "recording_id": split["recording_id"],
                        "meal_id": split["meal_id"],
                        "split": split_name,
                        "actual_spike_within_120_min": truth,
                        "predicted_spike_probability": logistic_probability,
                        "predicted_spike_at_0_5_threshold": (
                            logistic_probability >= DECISION_THRESHOLD
                        ).astype(int),
                    }
                )
            )

    coefficients = coefficient_table(logistic)
    predictions = pd.concat(prediction_frames, ignore_index=True)
    metadata = {
        "dataset": "ShanghaiT2DM",
        "model": "LogisticRegression",
        "model_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "research_use_only": True,
        "random_seed": RANDOM_SEED,
        "decision_threshold": DECISION_THRESHOLD,
        "target": TARGET_COLUMN,
        "feature_count_before_missing_indicators": len(MODEL_FEATURE_COLUMNS),
        "features": MODEL_FEATURE_COLUMNS,
        "preprocessing": {
            "missing_values": "median learned from training patients only",
            "missing_indicators": True,
            "scaling": "mean and standard deviation learned from training patients only",
        },
        "split_policy": "fit on train; inspect validation; test is an untouched patient group",
        "sklearn_version": sklearn.__version__,
        "metrics": metrics,
        "model_intercept": float(logistic.named_steps["classifier"].intercept_[0]),
        "checks": {
            "one_split_per_patient": True,
            "future_outcomes_excluded_from_inputs": True,
            "preprocessing_fit_only_on_training_rows": True,
            "patient_and_recording_ids_excluded_from_inputs": True,
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(metadata, output_dir / "baseline_metrics.json")
    atomic_write_csv(predictions, output_dir / "baseline_predictions.csv")
    atomic_write_csv(coefficients, output_dir / "baseline_coefficients.csv")
    atomic_joblib_dump(logistic, model_path)
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Train the first patient-split ShanghaiT2DM Logistic Regression model."
    )
    parser.add_argument(
        "--features",
        type=Path,
        default=Path("data/processed/shanghai-t2dm/modeling/model_features.csv"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed/shanghai-t2dm/modeling"),
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=Path("models/shanghai-t2dm/logistic_regression.joblib"),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    features = pd.read_csv(
        args.features.resolve(),
        dtype={"patient_id": "string", "recording_id": "string"},
        parse_dates=["timestamp"],
    )
    metadata = train_and_evaluate(
        features,
        args.output_dir.resolve(),
        args.model_path.resolve(),
    )
    validation = metadata["metrics"]["logistic_regression"]["validation"]
    test = metadata["metrics"]["logistic_regression"]["test"]
    print("ShanghaiT2DM Logistic Regression baseline complete")
    print(f"  Validation ROC AUC: {validation['roc_auc']:.3f}")
    print(f"  Validation F1: {validation['f1']:.3f}")
    print(f"  Test ROC AUC: {test['roc_auc']:.3f}")
    print(f"  Test F1: {test['f1']:.3f}")
    print(f"  Metrics: {args.output_dir.resolve() / 'baseline_metrics.json'}")
    print(f"  Model: {args.model_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
