package com.happyhealth.virtualpatient.domain;

import jakarta.persistence.ElementCollection;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import java.util.ArrayList;
import java.util.List;

@Entity
public class PatientProfile {
    @Id
    private String patientId;
    private String displayName;
    private String sex;
    private double ageYears;
    private double bmiKgM2;
    private double diabetesDurationYears;
    private Double hba1cPercent;
    private Double fastingPlasmaGlucoseMgDl;
    @ElementCollection(fetch = FetchType.EAGER)
    private List<String> diagnoses = new ArrayList<>();
    @ElementCollection(fetch = FetchType.EAGER)
    private List<String> medications = new ArrayList<>();

    protected PatientProfile() {}

    public PatientProfile(String patientId, String displayName, String sex, double ageYears,
                          double bmiKgM2, double diabetesDurationYears, Double hba1cPercent,
                          Double fastingPlasmaGlucoseMgDl, List<String> diagnoses,
                          List<String> medications) {
        this.patientId = patientId;
        this.displayName = displayName;
        this.sex = sex;
        this.ageYears = ageYears;
        this.bmiKgM2 = bmiKgM2;
        this.diabetesDurationYears = diabetesDurationYears;
        this.hba1cPercent = hba1cPercent;
        this.fastingPlasmaGlucoseMgDl = fastingPlasmaGlucoseMgDl;
        this.diagnoses = new ArrayList<>(diagnoses);
        this.medications = new ArrayList<>(medications);
    }

    public String getPatientId() { return patientId; }
    public String getDisplayName() { return displayName; }
    public String getSex() { return sex; }
    public double getAgeYears() { return ageYears; }
    public double getBmiKgM2() { return bmiKgM2; }
    public double getDiabetesDurationYears() { return diabetesDurationYears; }
    public Double getHba1cPercent() { return hba1cPercent; }
    public Double getFastingPlasmaGlucoseMgDl() { return fastingPlasmaGlucoseMgDl; }
    public List<String> getDiagnoses() { return List.copyOf(diagnoses); }
    public List<String> getMedications() { return List.copyOf(medications); }
}
