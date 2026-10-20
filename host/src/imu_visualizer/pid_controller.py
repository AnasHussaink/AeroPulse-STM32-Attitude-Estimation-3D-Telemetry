class PIDController:
    """
    Simple PID controller for simulated drone attitude control.

    P = proportional correction
    I = accumulated error correction
    D = rate-of-change correction
    """

    def __init__(
        self,
        kp,
        ki,
        kd,
        output_min=-100.0,
        output_max=100.0,
    ):
        self.kp = kp
        self.ki = ki
        self.kd = kd

        self.output_min = output_min
        self.output_max = output_max

        self.integral = 0.0
        self.previous_error = 0.0

        self.first_update = True


    def reset(self):
        """
        Clear stored PID history.
        """

        self.integral = 0.0
        self.previous_error = 0.0
        self.first_update = True


    def update(
        self,
        setpoint,
        measurement,
        dt
    ):
        """
        Calculate PID correction.

        setpoint:
            Desired angle.

        measurement:
            Current measured angle.

        dt:
            Time since previous update in seconds.
        """

        if dt <= 0.0:
            return 0.0

        # ---------------------------------------------
        # Error
        # ---------------------------------------------

        error = (
            setpoint
            - measurement
        )

        # ---------------------------------------------
        # Proportional
        # ---------------------------------------------

        proportional = (
            self.kp
            * error
        )

        # ---------------------------------------------
        # Integral
        # ---------------------------------------------

        self.integral += (
            error
            * dt
        )

        integral_term = (
            self.ki
            * self.integral
        )

        # ---------------------------------------------
        # Derivative
        # ---------------------------------------------

        if self.first_update:

            derivative = 0.0
            self.first_update = False

        else:

            derivative = (
                error
                - self.previous_error
            ) / dt

        derivative_term = (
            self.kd
            * derivative
        )

        self.previous_error = error

        # ---------------------------------------------
        # PID output
        # ---------------------------------------------

        output = (
            proportional
            + integral_term
            + derivative_term
        )

        # ---------------------------------------------
        # Output limiting
        # ---------------------------------------------

        output = max(
            self.output_min,
            min(
                self.output_max,
                output
            )
        )

        return output