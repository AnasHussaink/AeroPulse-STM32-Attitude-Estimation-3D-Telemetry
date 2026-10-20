"""Local configuration; credentials are never stored in the repository."""
import os
MQTT_ACCESS_TOKEN = os.getenv("THINGSBOARD_ACCESS_TOKEN", "")
MQTT_ENABLED = os.getenv("MQTT_ENABLED", "1" if MQTT_ACCESS_TOKEN else "0") == "1"
MQTT_HOST = os.getenv("MQTT_HOST", "mqtt.eu.thingsboard.cloud")
MQTT_PORT = 8883
MQTT_USE_TLS = True
MQTT_PUBLISH_INTERVAL_MS = 200
