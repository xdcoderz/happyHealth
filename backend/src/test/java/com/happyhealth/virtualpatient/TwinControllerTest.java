package com.happyhealth.virtualpatient;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.happyhealth.virtualpatient.repository.CgmReadingRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest(properties = "happyhealth.mqtt.enabled=false")
@AutoConfigureMockMvc
class TwinControllerTest {
    @Autowired MockMvc mvc;
    @Autowired CgmReadingRepository readings;

    @Test
    void demoTwinFusesStaticProfileAndDynamicCgm() throws Exception {
        mvc.perform(get("/api/patients/DEMO-001/twin"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.synthetic").value(true))
                .andExpect(jsonPath("$.patient.hba1cPercent").value(7.6))
                .andExpect(jsonPath("$.cgmReadings").isArray())
                .andExpect(jsonPath("$.latestCgm.glucoseMgDl").value(142.0));
    }

    @Test
    void repeatedEventIdIsIdempotent() throws Exception {
        String event = """
                {"eventId":"test-event-1","observedAt":"2026-10-09T10:15:00Z",
                 "glucoseMgDl":148.0,"source":"test"}
                """;
        long before = readings.count();
        mvc.perform(post("/api/patients/DEMO-001/cgm")
                        .contentType(MediaType.APPLICATION_JSON).content(event))
                .andExpect(status().isCreated());
        mvc.perform(post("/api/patients/DEMO-001/cgm")
                        .contentType(MediaType.APPLICATION_JSON).content(event))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.created").value(false));
        assertThat(readings.count()).isEqualTo(before + 1);
    }
}
