package com.happyhealth.virtualpatient.service;

import com.happyhealth.virtualpatient.api.ApiModels.PredictionView;
import java.time.Instant;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.stereotype.Component;

@Component
public class PredictionStore {
    public record StoredPrediction(PredictionView prediction, Instant updatedAt) {}
    private final ConcurrentHashMap<String, StoredPrediction> values = new ConcurrentHashMap<>();

    public StoredPrediction get(String patientId) { return values.get(patientId); }
    public void put(String patientId, PredictionView prediction) {
        values.put(patientId, new StoredPrediction(prediction, Instant.now()));
    }
}
