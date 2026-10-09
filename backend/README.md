# HappyHealth Digital-Twin Backend

Java 21 · Spring Boot 3.4.5 · Spring MVC · JPA/H2 · Eclipse Paho MQTT

This service is the coordinator between the two challenge data streams. It loads
the synthetic EHR profile, stores CGM readings in time order, rejects duplicate
events, builds a feature-compatible prediction request, calls FastAPI, and returns
one combined virtual-patient response to the React dashboard.

## Run locally

Start the FastAPI service first, then run from this directory:

```powershell
.\mvnw.cmd spring-boot:run
```

MQTT is disabled by default for local development, so the canonical fixture is
enough to use the API. Enable streaming with:

```powershell
$env:HAPPYHEALTH_MQTT_ENABLED='true'
$env:HAPPYHEALTH_MQTT_BROKER_URL='tcp://localhost:1883'
.\mvnw.cmd spring-boot:run
```

## Main endpoints

- `GET /api/patients/DEMO-001/twin` — combined profile, ordered CGM, and prediction
- `POST /api/patients/DEMO-001/cgm` — ingest one synthetic CGM event
- `POST /api/predictions/DEMO-001/refresh` — request a fresh model prediction
- `GET /actuator/health` — backend health

The authoritative field definitions and examples are in
[`docs/API_CONTRACT.md`](../docs/API_CONTRACT.md).

## Test

```powershell
.\mvnw.cmd test
```

The automated controller tests cover the joined twin response and idempotent,
time-ordered CGM ingestion. This is a research prototype and not a clinical system.
