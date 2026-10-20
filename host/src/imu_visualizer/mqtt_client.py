import json
import ssl
import time

import paho.mqtt.client as mqtt

from PySide6.QtCore import (
    QObject,
    Signal,
)


class MQTTTelemetryClient(QObject):

    status_changed = Signal(
        bool,
        str,
    )

    TELEMETRY_TOPIC = (
        "v1/devices/me/telemetry"
    )

    def __init__(
        self,
        host,
        access_token,
        port=8883,
        use_tls=True,
    ):
        super().__init__()

        self.host = host
        self.port = port

        self.access_token = (
            access_token
        )

        self.use_tls = use_tls

        self.connected = False

        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id="stm32_imu_gateway",
        )

        # ThingsBoard:
        # access token = MQTT username
        self.client.username_pw_set(
            username=self.access_token,
            password=None,
        )

        if self.use_tls:

            self.client.tls_set(
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLS_CLIENT,
            )

        self.client.on_connect = (
            self._on_connect
        )

        self.client.on_disconnect = (
            self._on_disconnect
        )

    # ========================================================
    # CALLBACKS
    # ========================================================

    def _on_connect(
        self,
        client,
        userdata,
        flags,
        reason_code,
        properties,
    ):

        if reason_code == 0:

            self.connected = True

            # Qt Signal:
            # safe crossing from MQTT thread
            # into GUI thread.
            self.status_changed.emit(
                True,
                "MQTT connected to ThingsBoard EU"
            )

        else:

            self.connected = False

            self.status_changed.emit(
                False,
                f"MQTT connection rejected: "
                f"{reason_code}"
            )

    def _on_disconnect(
        self,
        client,
        userdata,
        disconnect_flags,
        reason_code,
        properties,
    ):

        self.connected = False

        self.status_changed.emit(
            False,
            f"MQTT disconnected: "
            f"{reason_code}"
        )

    # ========================================================
    # CONNECTION
    # ========================================================

    def connect_cloud(self):

        try:

            self.status_changed.emit(
                False,
                "MQTT connecting..."
            )

            self.client.connect_async(
                self.host,
                self.port,
                keepalive=60,
            )

            self.client.loop_start()

        except Exception as exc:

            self.connected = False

            self.status_changed.emit(
                False,
                f"MQTT startup error: {exc}"
            )

    def disconnect_cloud(self):

        try:

            self.client.disconnect()

            self.client.loop_stop()

        except Exception:
            pass

        self.connected = False

    # ========================================================
    # TELEMETRY
    # ========================================================

    def publish_telemetry(
        self,
        roll,
        pitch,
        yaw,
        motor_outputs,
        roll_correction,
        pitch_correction,
        yaw_enabled,
    ):

        if not self.connected:

            return False

        payload = {

            "ts": int(
                time.time() * 1000
            ),

            "values": {

                "roll": round(
                    float(roll),
                    3,
                ),

                "pitch": round(
                    float(pitch),
                    3,
                ),

                "yaw": round(
                    float(yaw),
                    3,
                ),

                "yaw_enabled": bool(
                    yaw_enabled
                ),

                "roll_pid": round(
                    float(
                        roll_correction
                    ),
                    3,
                ),

                "pitch_pid": round(
                    float(
                        pitch_correction
                    ),
                    3,
                ),

                "motor_m1": round(
                    float(
                        motor_outputs["M1"]
                    ),
                    2,
                ),

                "motor_m2": round(
                    float(
                        motor_outputs["M2"]
                    ),
                    2,
                ),

                "motor_m3": round(
                    float(
                        motor_outputs["M3"]
                    ),
                    2,
                ),

                "motor_m4": round(
                    float(
                        motor_outputs["M4"]
                    ),
                    2,
                ),
            },
        }

        try:

            result = self.client.publish(
                self.TELEMETRY_TOPIC,
                json.dumps(payload),
                qos=0,
            )

            return (
                result.rc
                == mqtt.MQTT_ERR_SUCCESS
            )

        except Exception as exc:

            self.status_changed.emit(
                False,
                f"MQTT publish error: {exc}"
            )

            return False