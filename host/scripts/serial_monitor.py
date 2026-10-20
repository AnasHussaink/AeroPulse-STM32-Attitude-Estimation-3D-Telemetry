import serial

PORT = "COM3"
BAUD = 115200

with serial.Serial(PORT, BAUD, timeout=1) as ser:
    print(f"Listening on {PORT}...")
    try:
        while True:
            line = ser.readline().decode(errors="ignore").strip()
            if line:
                print(line)
    except KeyboardInterrupt:
        pass
