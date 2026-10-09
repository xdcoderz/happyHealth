package com.happyhealth.virtualpatient.api;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.time.Instant;
import java.util.List;

public final class ApiModels {
    private ApiModels() {}

    public record CgmIngestRequest(
            @NotBlank String eventId,
            @NotNull Instant observedAt,
            @DecimalMin("40.0") @DecimalMax("500.0") double glucoseMgDl,
            @NotBlank String source) {}

    public record CgmView(String eventId, Instant observedAt, double glucoseMgDl, String source) {}

    public record PatientView(
            String patientId, String displayName, String sex, double ageYears,
            double bmiKgM2, double diabetesDurationYears, Double hba1cPercent,
            Double fastingPlasmaGlucoseMgDl, List<String> diagnoses,
            List<String> medications) {}

    public record FactorView(String feature, String displayName, String direction,
                             double contribution) {}

    public record PredictionView(
            String status, Double probability, String riskBand,
            int predictionWindowMinutes, Instant predictionTime,
            String modelVersion, List<FactorView> topFactors,
            List<String> warnings) {}

    public record TwinView(
            String schemaVersion, boolean synthetic, boolean researchUseOnly,
            PatientView patient, List<CgmView> cgmReadings,
            CgmView latestCgm, long dataAgeSeconds,
            PredictionView prediction, Instant predictionUpdatedAt) {}
}
