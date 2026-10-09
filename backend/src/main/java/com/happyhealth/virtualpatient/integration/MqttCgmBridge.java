package com.happyhealth.virtualpatient.integration;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.happyhealth.virtualpatient.api.ApiModels.CgmIngestRequest;
import com.happyhealth.virtualpatient.service.TwinService;
import jakarta.annotation.PreDestroy;
import java.nio.charset.StandardCharsets;
import java.util.UUID;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnProperty(name = "happyhealth.mqtt.enabled", havingValue = "true")
public class MqttCgmBridge {
    private static final Logger log = LoggerFactory.getLogger(MqttCgmBridge.class);
    private final ObjectMapper mapper;
    private final TwinService twins;
    private final String brokerUrl;
    private MqttClient client;

    public MqttCgmBridge(ObjectMapper mapper, TwinService twins,
                         @Value("${happyhealth.mqtt.broker-url}") String brokerUrl) {
        this.mapper = mapper;
        this.twins = twins;
        this.brokerUrl = brokerUrl;
    }

    @Scheduled(initialDelay = 1_000, fixedDelay = 5_000)
    public synchronized void ensureConnected() {
        if (client != null && client.isConnected()) return;
        try {
            client = new MqttClient(brokerUrl,
                    "happyhealth-backend-" + UUID.randomUUID(), new MemoryPersistence());
            var options = new MqttConnectOptions();
            options.setAutomaticReconnect(true);
            options.setCleanSession(true);
            options.setConnectionTimeout(3);
            client.connect(options);
            client.subscribe("happyhealth/patients/+/cgm", (topic, message) -> {
                try {
                    String[] parts = topic.split("/");
                    String patientId = parts[2];
                    var request = mapper.readValue(
                            new String(message.getPayload(), StandardCharsets.UTF_8),
                            CgmIngestRequest.class);
                    twins.ingest(patientId, request);
                } catch (Exception error) {
                    log.warn("Rejected MQTT CGM event: {}", error.getMessage());
                }
            });
            log.info("Subscribed to synthetic CGM events at {}", brokerUrl);
        } catch (Exception error) {
            log.warn("MQTT connection pending: {}", error.getMessage());
        }
    }

    @PreDestroy
    public void close() throws Exception {
        if (client != null && client.isConnected()) client.disconnect();
    }
}
