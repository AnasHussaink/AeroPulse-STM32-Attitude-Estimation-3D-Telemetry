import serial

PORT = "COM3"
BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=1)

start_roll = None
start_pitch = None
start_yaw = None

print("Orientation mapping test")
print("------------------------")
print("Keep sensor still when starting.")
print("First valid reading becomes ZERO reference.")
print("Press Ctrl+C to stop.\n")


def parse_line(line):
    parts = line.split(",")

    roll = float(parts[0].split(":")[1])
    pitch = float(parts[1].split(":")[1])
    yaw = float(parts[2].split(":")[1])

    return roll, pitch, yaw


try:
    while True:

        line = ser.readline().decode(errors="ignore").strip()

        if not line:
            continue

        try:
            roll, pitch, yaw = parse_line(line)

            # First reading becomes our reference position
            if start_roll is None:
                start_roll = roll
                start_pitch = pitch
                start_yaw = yaw

                print("Reference captured:")
                print(
                    f"ROLL={start_roll:.2f}, "
                    f"PITCH={start_pitch:.2f}, "
                    f"YAW={start_yaw:.2f}"
                )
                print("\nNow move ONE axis at a time.\n")
                continue

            roll_delta = roll - start_roll
            pitch_delta = pitch - start_pitch
            yaw_delta = yaw - start_yaw

            print(
                f"dROLL:{roll_delta:7.2f}   "
                f"dPITCH:{pitch_delta:7.2f}   "
                f"dYAW:{yaw_delta:7.2f}"
            )

        except (ValueError, IndexError):
            pass

except KeyboardInterrupt:
    print("\nStopped.")

finally:
    ser.close()