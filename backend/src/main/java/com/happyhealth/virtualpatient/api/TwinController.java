package com.happyhealth.virtualpatient.api;

import com.happyhealth.virtualpatient.api.ApiModels.CgmIngestRequest;
import com.happyhealth.virtualpatient.api.ApiModels.TwinView;
import com.happyhealth.virtualpatient.service.PredictionCoordinator;
import com.happyhealth.virtualpatient.service.TwinService;
import jakarta.validation.Valid;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class TwinController {
    private final TwinService twins;
    private final PredictionCoordinator predictions;

    public TwinController(TwinService twins, PredictionCoordinator predictions) {
        this.twins = twins;
        this.predictions = predictions;
    }

    @GetMapping("/patients/{patientId}/twin")
    public TwinView getTwin(@PathVariable String patientId) {
        return twins.view(patientId);
    }

    @PostMapping("/patients/{patientId}/cgm")
    public ResponseEntity<Map<String, Object>> ingest(
            @PathVariable String patientId, @Valid @RequestBody CgmIngestRequest request) {
        boolean created = twins.ingest(patientId, request);
        return ResponseEntity.status(created ? 201 : 200)
                .body(Map.of("accepted", true, "created", created));
    }

    @PostMapping("/predictions/{patientId}/refresh")
    public TwinView refresh(@PathVariable String patientId) {
        return predictions.refresh(patientId);
    }
}
