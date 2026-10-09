package com.happyhealth.virtualpatient.repository;

import com.happyhealth.virtualpatient.domain.PatientProfile;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PatientRepository extends JpaRepository<PatientProfile, String> {}
