from imu_visualizer.pid_controller import PIDController


pid = PIDController(
    kp=2.0,
    ki=0.0,
    kd=0.15
)


setpoint = 0.0
measurement = 10.0
dt = 0.02


output = pid.update(
    setpoint,
    measurement,
    dt
)


print("Setpoint:", setpoint)
print("Measurement:", measurement)
print("PID Output:", output)