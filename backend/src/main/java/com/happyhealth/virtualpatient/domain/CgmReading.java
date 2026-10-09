package com.happyhealth.virtualpatient.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.Table;
import java.time.Instant;

@Entity
@Table(indexes = @Index(name = "idx_cgm_patient_time", columnList = "patientId,observedAt"))
public class CgmReading {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(nullable = false, unique = true, length = 100)
    private String eventId;
    @Column(nullable = false, length = 64)
    private String patientId;
    @Column(nullable = false)
    private Instant observedAt;
    @Column(nullable = false)
    private double glucoseMgDl;
    @Column(nullable = false, length = 100)
    private String source;

    protected CgmReading() {}

    public CgmReading(String eventId, String patientId, Instant observedAt,
                      double glucoseMgDl, String source) {
        this.eventId = eventId;
        this.patientId = patientId;
        this.observedAt = observedAt;
        this.glucoseMgDl = glucoseMgDl;
        this.source = source;
    }

    public String getEventId() { return eventId; }
    public String getPatientId() { return patientId; }
    public Instant getObservedAt() { return observedAt; }
    public double getGlucoseMgDl() { return glucoseMgDl; }
    public String getSource() { return source; }
}
