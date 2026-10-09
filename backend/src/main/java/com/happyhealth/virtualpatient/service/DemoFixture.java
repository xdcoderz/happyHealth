package com.happyhealth.virtualpatient.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.InputStream;
import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Component;

@Component
public class DemoFixture {
    private final ObjectMapper objectMapper;
    private final Resource resource;

    public DemoFixture(ObjectMapper objectMapper,
                       @Value("${happyhealth.demo.fixture}") Resource resource) {
        this.objectMapper = objectMapper;
        this.resource = resource;
    }

    public Fixture read() {
        try (InputStream stream = resource.getInputStream()) {
            return objectMapper.readValue(stream, Fixture.class);
        } catch (IOException error) {
            throw new IllegalStateException("Cannot read the synthetic demo fixture", error);
        }
    }

    public record Fixture(String schemaVersion, Provenance provenance, Patient patient,
                          Meal currentMeal, List<RelativeCgm> cgmHistory) {}
    public record Provenance(boolean synthetic, String purpose, boolean containsRealPatientData) {}
    public record Patient(String patientId, String displayName, String sex, double ageYears,
                          double bmiKgM2, double diabetesDurationYears, Double hba1cPercent,
                          Double fastingPlasmaGlucoseMgDl, List<String> diagnoses,
                          List<String> medications) {}
    public record Meal(String description, Double minutesSincePreviousMeal,
                       double csiiBolusInsulinIu, double csiiBasalInsulinIuPerHour,
                       boolean hasRecordedCsiiBolus, boolean hasRecordedCsiiBasalSetting,
                       boolean hasRecordedSubcutaneousInsulin,
                       boolean hasRecordedNonInsulinMedication,
                       boolean hasRecordedIntravenousInsulin) {}
    public record RelativeCgm(long minutesBefore, double glucoseMgDl) {}
}
