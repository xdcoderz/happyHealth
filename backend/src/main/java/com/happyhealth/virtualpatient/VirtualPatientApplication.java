package com.happyhealth.virtualpatient;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@EnableScheduling
@SpringBootApplication
public class VirtualPatientApplication {
    public static void main(String[] args) {
        SpringApplication.run(VirtualPatientApplication.class, args);
    }
}
