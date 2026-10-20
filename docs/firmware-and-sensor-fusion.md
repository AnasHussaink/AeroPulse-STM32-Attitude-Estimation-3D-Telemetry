# Firmware and attitude estimation

Main implementation: `firmware/Core/Src/main.c`. LCD driver: `lcd_i2c.c`. Project configuration: `STM32_IMU_FlightVisualizer.ioc`.

## From reset to telemetry

1. Initialise HAL, clock, GPIO, SPI1, I2C2 and USART1.
2. Wake the MPU6500 by writing its power-management register. Read WHO_AM_I (`0x75`); the code comments expect `0x70`, but no comparison blocks operation on an unexpected value.
3. Estimate gyro bias using 500 stationary samples with a 5 ms delay between samples (roughly 2.5 seconds plus execution time).
4. Read a 14-byte register burst from `0x3B`, reconstruct signed acceleration/gyro readings and skip the temperature bytes.
5. Convert using 16384 LSB/g and 131 LSB/(degree/s), assuming the sensor's default +/-2 g and +/-250 degree/s ranges.
6. Estimate roll and pitch from acceleration; integrate bias-corrected angular rate; blend roll/pitch with a complementary filter.
7. Apply master zero offsets and transmit the canonical angles to the LCD and UART.
8. Repeat, accepting `Z` or `z` to update the reference offsets.

## Equations used

```text
roll_acc  = atan2(ay, az) * 180/pi
pitch_acc = atan2(-ax, sqrt(ay*ay + az*az)) * 180/pi
roll  = 0.98 * (previous_roll  + corrected_gx * dt) + 0.02 * roll_acc
pitch = 0.98 * (previous_pitch + corrected_gy * dt) + 0.02 * pitch_acc
yaw   = previous_yaw + corrected_gz * dt
```

Gyro integration follows rapid movement but accumulates bias error. Accelerometer inclination provides a low-frequency gravity reference for roll/pitch, but linear acceleration can disturb it. Yaw has no absolute reference and can drift.

`dt` comes from HAL tick differences. Values <= 0 or > 0.1 seconds are replaced with 0.02 seconds. The loop includes `HAL_Delay(20)` and blocking communication; LCD updates are eligible every 200 ms. These are software settings, not verified sampling-frequency measurements.

## Protocol

```text
ROLL:-10.50,PITCH:3.25,YAW:42.00
LCD1:<display row 1>
LCD2:<display row 2>
```

Lines are terminated with CR/LF. The Python worker handles LCD prefixes separately from the three-field attitude parser. A PC-to-MCU `Z` command requests a new reference; zeroing is owned by the STM32 so local and desktop views use the same values.

## Building

Import the existing `firmware/` directory into STM32CubeIDE, review the selected STM32F103C8 device and build configuration, then build and flash via SWD. Build output folders were intentionally excluded from publication. No fresh embedded build or hardware flash was performed during repository preparation. If UART float fields are blank, check the toolchain's floating-point printf option (`-u _printf_float`) and available flash space.
