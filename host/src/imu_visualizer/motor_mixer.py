class MotorMixer:
    """
    Simple simulated X-frame quadcopter motor mixer.

    Motor layout:

            FRONT

        M1         M2
      Front-L    Front-R

        M3         M4
       Rear-L     Rear-R
    """

    def __init__(
        self,
        base_throttle=50.0,
        minimum=0.0,
        maximum=100.0,
    ):
        self.base_throttle = base_throttle
        self.minimum = minimum
        self.maximum = maximum


    def _limit(self, value):
        """
        Keep simulated motor output between
        minimum and maximum percentage.
        """

        return max(
            self.minimum,
            min(
                self.maximum,
                value
            )
        )


    def mix(
        self,
        roll_correction,
        pitch_correction,
    ):
        """
        Convert roll and pitch correction into
        four simulated motor commands.
        """

        base = self.base_throttle

        m1 = (
            base
            - roll_correction
            + pitch_correction
        )

        m2 = (
            base
            + roll_correction
            + pitch_correction
        )

        m3 = (
            base
            - roll_correction
            - pitch_correction
        )

        m4 = (
            base
            + roll_correction
            - pitch_correction
        )

        return {
            "M1": self._limit(m1),
            "M2": self._limit(m2),
            "M3": self._limit(m3),
            "M4": self._limit(m4),
        }