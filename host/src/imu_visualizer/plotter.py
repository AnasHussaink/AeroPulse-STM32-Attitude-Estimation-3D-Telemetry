from collections import deque
import matplotlib.pyplot as plt

class LivePlotter:
    def __init__(self, history: int = 200):
        self.roll = deque(maxlen=history)
        self.pitch = deque(maxlen=history)
        self.yaw = deque(maxlen=history)

        plt.ion()
        self.fig, self.ax = plt.subplots()
        self.roll_line, = self.ax.plot([], [], label="Roll")
        self.pitch_line, = self.ax.plot([], [], label="Pitch")
        self.yaw_line, = self.ax.plot([], [], label="Yaw")
        self.ax.set_ylim(-180, 180)
        self.ax.set_xlabel("Samples")
        self.ax.set_ylabel("Angle (degrees)")
        self.ax.legend()

    def update(self, attitude):
        self.roll.append(attitude.roll)
        self.pitch.append(attitude.pitch)
        self.yaw.append(attitude.yaw)

        x = range(len(self.roll))
        self.roll_line.set_data(x, self.roll)
        self.pitch_line.set_data(x, self.pitch)
        self.yaw_line.set_data(x, self.yaw)
        self.ax.set_xlim(0, max(10, len(self.roll)))
        plt.pause(0.01)
