from imu_visualizer.motor_mixer import MotorMixer


mixer = MotorMixer(
    base_throttle=50.0
)


motors = mixer.mix(
    roll_correction=-10.0,
    pitch_correction=5.0,
)


for motor, value in motors.items():
    print(
        motor,
        f"{value:.1f}%"
    )