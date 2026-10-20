import serial

class SerialReader:
    def __init__(self, port: str, baud_rate: int, timeout: float = 1.0):
        self.ser = serial.Serial(port, baud_rate, timeout=timeout)

    def read_line(self) -> str:
        return self.ser.readline().decode(errors="ignore").strip()

    def close(self) -> None:
        if self.ser.is_open:
            self.ser.close()
