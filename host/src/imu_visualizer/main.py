from .config import SERIAL_PORT, BAUD_RATE, SERIAL_TIMEOUT, GRAPH_HISTORY
from .serial_reader import SerialReader
from .parser import parse_attitude_line
from .plotter import LivePlotter

def main():
    reader = SerialReader(SERIAL_PORT, BAUD_RATE, SERIAL_TIMEOUT)
    plotter = LivePlotter(GRAPH_HISTORY)
    print(f"Listening on {SERIAL_PORT} @ {BAUD_RATE} baud")

    try:
        while True:
            line = reader.read_line()
            if not line:
                continue
            try:
                attitude = parse_attitude_line(line)
                plotter.update(attitude)
            except (ValueError, KeyError):
                continue
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        reader.close()

if __name__ == "__main__":
    main()
