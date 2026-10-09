package com.happyhealth.virtualpatient.service;

import com.happyhealth.virtualpatient.api.ApiModels.FactorView;
import com.happyhealth.virtualpatient.api.ApiModels.PredictionView;
import com.happyhealth.virtualpatient.api.ApiModels.TwinView;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

@Service
public class PredictionCoordinator {
    private static final Logger log = LoggerFactory.getLogger(PredictionCoordinator.class);
    private final TwinService twins;
    private final PredictionStore store;
    private final DemoFixture demoFixture;
    private final RestClient modelClient;

    public PredictionCoordinator(TwinService twins, PredictionStore store,
                                 DemoFixture demoFixture, RestClient.Builder restClientBuilder,
                                 @Value("${happyhealth.ml.base-url}") String modelBaseUrl) {
        this.twins = twins;
        this.store = store;
        this.demoFixture = demoFixture;
        var requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(3_000);
        requestFactory.setReadTimeout(10_000);
        this.modelClient = restClientBuilder.requestFactory(requestFactory)
                .baseUrl(modelBaseUrl).build();
    }

    public TwinView refresh(String patientId) {
        var patient = twins.patient(patientId);
        var readings = twins.recentReadings(patientId);
        if (readings.isEmpty()) {
            store.put(patientId, unavailable(Instant.now(), "No CGM readings are available."));
            return twins.view(patientId);
        }
        Instant predictionTime = readings.get(readings.size() - 1).getObservedAt();
        var fixture = demoFixture.read();
        Map<String, Object> request = new LinkedHashMap<>();
        request.put("schemaVersion", "1.0");
        request.put("patient", Map.of(
                "patientId", patient.getPatientId(), "sex", patient.getSex(),
                "ageYears", patient.getAgeYears(), "bmiKgM2", patient.getBmiKgM2(),
                "diabetesDurationYears", patient.getDiabetesDurationYears(),
                "hba1cPercent", patient.getHba1cPercent(),
                "fastingPlasmaGlucoseMgDl", patient.getFastingPlasmaGlucoseMgDl()));
        request.put("predictionTime", predictionTime);
        request.put("meal", fixture.currentMeal());
        request.put("cgmReadings", readings.stream().map(item -> Map.of(
                "observedAt", item.getObservedAt(), "glucoseMgDl", item.getGlucoseMgDl())).toList());
        try {
            ModelResponse result = modelClient.post().uri("/ml/predict-glucose-spike")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(request).retrieve().body(ModelResponse.class);
            if (result == null) {
                throw new IllegalStateException("Model service returned an empty response");
            }
            store.put(patientId, result.toView());
        } catch (RuntimeException error) {
            log.warn("Prediction unavailable for {}: {}", patientId, error.getMessage());
            store.put(patientId, unavailable(predictionTime,
                    "Prediction service unavailable; no score was fabricated."));
        }
        return twins.view(patientId);
    }

    private static PredictionView unavailable(Instant time, String warning) {
        return new PredictionView("unavailable", null, null, 120, time,
                "unavailable", List.of(), List.of(warning));
    }

    public record ModelResponse(String status, Double probability, String riskBand,
                                int predictionWindowMinutes, Instant predictionTime,
                                String modelVersion, List<FactorView> topFactors,
                                List<String> warnings) {
        PredictionView toView() {
            return new PredictionView(status, probability, riskBand,
                    predictionWindowMinutes, predictionTime, modelVersion,
                    topFactors == null ? List.of() : topFactors,
                    warnings == null ? List.of() : warnings);
        }
    }
}
