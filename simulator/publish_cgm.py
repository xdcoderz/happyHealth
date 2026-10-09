"""Publish a deterministic synthetic CGM stream for the public demo."""

from __future__ import annotations

import argparse
import json
import os
import time
import uuid
from datetime import datetime, timedelta, timezone

import paho.mqtt.client as mqtt


GLUCOSE_PATTERN = (148, 155, 164, 176, 188, 198, 205, 201, 194, 182, 169, 158)


def quarter_hour_now() -> datetime:
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    return now.replace(minute=(now.minute // 15) * 15)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--broker", default=os.getenv("MQTT_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MQTT_PORT", "1883")))
    parser.add_argument("--patient", default=os.getenv("PATIENT_ID", "DEMO-001"))
    parser.add_argument("--interval", type=float, default=float(os.getenv("PUBLISH_INTERVAL_SECONDS", "5")))
    parser.add_argument("--startup-delay", type=float, default=float(os.getenv("STARTUP_DELAY_SECONDS", "15")))
    args = parser.parse_args()

    time.sleep(args.startup_delay)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"synthetic-cgm-{uuid.uuid4()}")
    while True:
        try:
            client.connect(args.broker, args.port, keepalive=30)
            break
        except OSError as error:
            print(f"Broker not ready ({error}); retrying in 3 seconds", flush=True)
            time.sleep(3)
    client.loop_start()

    topic = f"happyhealth/patients/{args.patient}/cgm"
    observed_at = quarter_hour_now() + timedelta(minutes=15)
    print(f"Publishing synthetic CGM to {topic}", flush=True)
    index = 0
    try:
        while True:
            glucose = GLUCOSE_PATTERN[index % len(GLUCOSE_PATTERN)]
            event = {
                "eventId": f"sim-{args.patient}-{observed_at.isoformat()}-{index}",
                "observedAt": observed_at.isoformat().replace("+00:00", "Z"),
                "glucoseMgDl": float(glucose),
                "source": "synthetic-cgm-simulator",
            }
            result = client.publish(topic, json.dumps(event), qos=1)
            result.wait_for_publish()
            print(json.dumps(event), flush=True)
            index += 1
            observed_at += timedelta(minutes=15)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
