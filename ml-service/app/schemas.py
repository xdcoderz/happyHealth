"""Validated HTTP schemas for the model service."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PatientInput(StrictModel):
    patientId: str = Field(min_length=1, max_length=64)
    sex: Literal["female", "male"]
    ageYears: float = Field(ge=18, le=120)
    bmiKgM2: float = Field(gt=10, lt=80)
    diabetesDurationYears: float = Field(ge=0, le=100)
    hba1cPercent: float | None = Field(default=None, gt=0, lt=25)
    fastingPlasmaGlucoseMgDl: float | None = Field(default=None, ge=20, le=700)


class MealInput(StrictModel):
    description: str = Field(min_length=1, max_length=2_000)
    minutesSincePreviousMeal: float | None = Field(default=None, ge=0, le=2_880)
    csiiBolusInsulinIu: float = Field(default=0.0, ge=0, le=100)
    csiiBasalInsulinIuPerHour: float = Field(default=0.0, ge=0, le=20)
    hasRecordedCsiiBolus: bool = False
    hasRecordedCsiiBasalSetting: bool = False
    hasRecordedSubcutaneousInsulin: bool = False
    hasRecordedNonInsulinMedication: bool = False
    hasRecordedIntravenousInsulin: bool = False


class CgmReadingInput(StrictModel):
    observedAt: datetime
    glucoseMgDl: float = Field(ge=40, le=500)

    @field_validator("observedAt")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("observedAt must include a timezone")
        return value


class PredictionRequest(StrictModel):
    schemaVersion: Literal["1.0"] = "1.0"
    patient: PatientInput
    predictionTime: datetime
    meal: MealInput
    cgmReadings: list[CgmReadingInput] = Field(min_length=1, max_length=1_000)

    @field_validator("predictionTime")
    @classmethod
    def require_prediction_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("predictionTime must include a timezone")
        return value


class Factor(StrictModel):
    feature: str
    displayName: str
    direction: Literal["higher", "lower"]
    contribution: float


class PredictionResponse(StrictModel):
    status: Literal["available", "insufficient_data", "unavailable"]
    probability: float | None = Field(default=None, ge=0, le=1)
    riskBand: Literal["low", "moderate", "high"] | None = None
    predictionWindowMinutes: int = 120
    predictionTime: datetime
    modelVersion: str
    topFactors: list[Factor] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class HealthResponse(StrictModel):
    status: Literal["ok", "degraded"]
    modelLoaded: bool
    modelVersion: str
    researchUseOnly: bool = True
