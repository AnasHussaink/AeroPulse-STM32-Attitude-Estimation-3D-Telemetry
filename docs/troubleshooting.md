# Troubleshooting

| Symptom | Check |
|---|---|
| Port cannot open | Correct COM number, USB-UART driver, cable and whether another terminal owns it |
| No attitude data | Common ground, crossed TX/RX, 115200 baud, firmware and sensor connections |
| Blank LCD | Power compatibility, contrast adjustment, I2C address and PB10/PB11 wiring |
| Blank floating-point UART fields | STM32 linker float-printf support and flash size |
| Incorrect startup reference | Restart with the sensor stationary, then use zero |
| Yaw slowly changes | Relative yaw integrates gyro; no absolute heading reference is present |
| 3D scene fails | Correct virtual environment, PySide6/Qt Quick 3D installation and graphics drivers |
| MQTT import error | Install requirements including `paho-mqtt>=2.0,<3` |
| MQTT does not connect | Token, enabled flag, tenant host, internet access and TLS certificate/time settings |
| Serial link lost | Check wiring/power and reconnect manually; automatic recovery is not implemented |

The Windows DLL-directory handling in `visualizer3d.py` is retained. Other operating systems have not been validated with this publication copy.
