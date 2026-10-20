import pytest
from imu_visualizer.parser import parse_attitude_line

def test_parse_valid_line():
    attitude = parse_attitude_line("ROLL:-10.5,PITCH:3.25,YAW:42.0")
    assert attitude.roll == pytest.approx(-10.5)
    assert attitude.pitch == pytest.approx(3.25)
    assert attitude.yaw == pytest.approx(42.0)

def test_invalid_line():
    with pytest.raises(ValueError):
        parse_attitude_line("bad-data")
