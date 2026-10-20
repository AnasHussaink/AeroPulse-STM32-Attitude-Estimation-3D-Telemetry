from .models import Attitude

def parse_attitude_line(line: str) -> Attitude:
    parts = line.strip().split(",")
    if len(parts) != 3:
        raise ValueError("Expected 3 comma-separated fields")

    values = {}
    for part in parts:
        key, value = part.split(":", 1)
        values[key.strip().upper()] = float(value)

    return Attitude(
        roll=values["ROLL"],
        pitch=values["PITCH"],
        yaw=values["YAW"],
    )
