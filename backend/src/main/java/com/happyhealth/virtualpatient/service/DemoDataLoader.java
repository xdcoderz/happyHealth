package com.happyhealth.virtualpatient.service;

import com.happyhealth.virtualpatient.domain.CgmReading;
import com.happyhealth.virtualpatient.domain.PatientProfile;
import com.happyhealth.virtualpatient.repository.CgmReadingRepository;
import com.happyhealth.virtualpatient.repository.PatientRepository;
import java.time.Instant;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@Component
public class DemoDataLoader implements ApplicationRunner {
    private final DemoFixture fixtureReader;
    private final PatientRepository patients;
    private final CgmReadingRepository readings;

    public DemoDataLoader(DemoFixture fixtureReader, PatientRepository patients,
                          CgmReadingRepository readings) {
        this.fixtureReader = fixtureReader;
        this.patients = patients;
        this.readings = readings;
    }

    @Override
    @Transactional
    public void run(ApplicationArguments args) {
        var fixture = fixtureReader.read();
        var source = fixture.patient();
        if (!patients.existsById(source.patientId())) {
            patients.save(new PatientProfile(
                    source.patientId(), source.displayName(), source.sex(), source.ageYears(),
                    source.bmiKgM2(), source.diabetesDurationYears(), source.hba1cPercent(),
                    source.fastingPlasmaGlucoseMgDl(), source.diagnoses(), source.medications()));
        }
        long currentQuarterHour = (Instant.now().getEpochSecond() / 900L) * 900L;
        Instant anchor = Instant.ofEpochSecond(currentQuarterHour);
        for (var item : fixture.cgmHistory()) {
            String eventId = "fixture-" + source.patientId() + "-" + item.minutesBefore();
            if (!readings.existsByEventId(eventId)) {
                readings.save(new CgmReading(eventId, source.patientId(),
                        anchor.minusSeconds(item.minutesBefore() * 60L),
                        item.glucoseMgDl(), "synthetic-demo-fixture"));
            }
        }
    }
}
