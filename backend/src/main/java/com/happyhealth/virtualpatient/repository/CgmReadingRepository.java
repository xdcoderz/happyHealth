package com.happyhealth.virtualpatient.repository;

import com.happyhealth.virtualpatient.domain.CgmReading;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CgmReadingRepository extends JpaRepository<CgmReading, Long> {
    boolean existsByEventId(String eventId);
    List<CgmReading> findTop96ByPatientIdOrderByObservedAtDesc(String patientId);
}
