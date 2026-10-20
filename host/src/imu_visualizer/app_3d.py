import sys
import csv
import time

from pathlib import Path
from datetime import datetime
from collections import deque
from queue import Queue, Empty

import serial
import pyqtgraph as pg

from PySide6.QtCore import (
    QThread,
    Signal,
    QTimer,
    Qt,
)

from PySide6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QBrush,
    QFont,
)

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QFrame,
    QProgressBar,
    QPlainTextEdit,
    QScrollArea,
)

from .config import (
    SERIAL_PORT,
    BAUD_RATE,
)

from .config_mqtt import (
    MQTT_ENABLED,
    MQTT_HOST,
    MQTT_PORT,
    MQTT_USE_TLS,
    MQTT_ACCESS_TOKEN,
    MQTT_PUBLISH_INTERVAL_MS,
)

from .parser import (
    parse_attitude_line,
)

from .visualizer3d import (
    DroneVisualizer3D,
)

from .pid_controller import (
    PIDController,
)

from .motor_mixer import (
    MotorMixer,
)

from .mqtt_client import (
    MQTTTelemetryClient,
)


# ============================================================
# SERIAL WORKER
# ============================================================

class SerialWorker(QThread):

    attitude_received = Signal(
        float,
        float,
        float,
    )

    lcd_received = Signal(
        int,
        str,
    )

    connection_changed = Signal(
        bool,
        str,
    )

    def __init__(
        self,
        port,
        baud,
    ):
        super().__init__()

        self.port = port
        self.baud = baud

        self.running = True

        # Python -> STM32 command queue
        self.tx_queue = Queue()

    # ========================================================
    # SEND COMMAND
    # ========================================================

    def send_command(
        self,
        command,
    ):

        self.tx_queue.put(
            command.encode(
                "ascii"
            )
        )

    # ========================================================
    # THREAD
    # ========================================================

    def run(self):

        try:

            ser = serial.Serial(
                self.port,
                self.baud,
                timeout=0.03,
            )

            ser.reset_input_buffer()

            self.connection_changed.emit(
                True,
                f"Connected: {self.port}",
            )

        except serial.SerialException as exc:

            self.connection_changed.emit(
                False,
                str(exc),
            )

            return

        while self.running:

            try:

                # =================================================
                # PYTHON -> STM32
                # =================================================

                try:

                    while True:

                        command = (
                            self.tx_queue
                            .get_nowait()
                        )

                        ser.write(
                            command
                        )

                except Empty:
                    pass

                # =================================================
                # STM32 -> PYTHON
                # =================================================

                line = (
                    ser.readline()
                    .decode(
                        errors="ignore"
                    )
                    .strip()
                )

                if not line:
                    continue

                # -------------------------------------------------
                # LCD ROW 1
                # -------------------------------------------------

                if line.startswith(
                    "LCD1:"
                ):

                    self.lcd_received.emit(
                        1,
                        line[5:],
                    )

                    continue

                # -------------------------------------------------
                # LCD ROW 2
                # -------------------------------------------------

                if line.startswith(
                    "LCD2:"
                ):

                    self.lcd_received.emit(
                        2,
                        line[5:],
                    )

                    continue

                # -------------------------------------------------
                # ATTITUDE TELEMETRY
                # -------------------------------------------------

                try:

                    attitude = (
                        parse_attitude_line(
                            line
                        )
                    )

                    self.attitude_received.emit(
                        attitude.roll,
                        attitude.pitch,
                        attitude.yaw,
                    )

                except (
                    ValueError,
                    KeyError,
                    IndexError,
                ):
                    continue

            except serial.SerialException:

                self.connection_changed.emit(
                    False,
                    "Serial disconnected",
                )

                break

        try:

            ser.close()

        except Exception:
            pass

    # ========================================================
    # STOP THREAD
    # ========================================================

    def stop(self):

        self.running = False

        self.wait(
            1000
        )


# ============================================================
# TELEMETRY CARD
# ============================================================

class TelemetryCard(QFrame):

    def __init__(
        self,
        title,
    ):
        super().__init__()

        self.setObjectName(
            "TelemetryCard"
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            8,
            5,
            8,
            7,
        )

        layout.setSpacing(
            2
        )

        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "SmallTitle"
        )

        title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.value_label = QLabel(
            "0.0°"
        )

        self.value_label.setObjectName(
            "BigValue"
        )

        self.value_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            self.value_label
        )

    def set_value(
        self,
        value,
    ):

        self.value_label.setText(
            f"{value:+.1f}°"
        )

    def set_disabled_value(
        self,
    ):

        self.value_label.setText(
            "OFF"
        )


# ============================================================
# MOTOR BAR
# ============================================================

class MotorBar(QFrame):

    def __init__(
        self,
        title,
    ):
        super().__init__()

        self.setObjectName(
            "MotorCard"
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            8,
            5,
            8,
            5,
        )

        layout.setSpacing(
            3
        )

        label = QLabel(
            title
        )

        label.setObjectName(
            "MotorTitle"
        )

        label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.bar = QProgressBar()

        self.bar.setRange(
            0,
            100,
        )

        self.bar.setValue(
            50
        )

        self.bar.setFormat(
            "%p%"
        )

        self.bar.setTextVisible(
            True
        )

        layout.addWidget(
            label
        )

        layout.addWidget(
            self.bar
        )

    def set_value(
        self,
        value,
    ):

        value = max(
            0.0,
            min(
                100.0,
                value,
            ),
        )

        self.bar.setValue(
            int(
                round(value)
            )
        )


# ============================================================
# VIRTUAL LCD
# ============================================================

class VirtualLCD(QFrame):

    def __init__(self):
        super().__init__()

        self.setObjectName(
            "Panel"
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            8,
            7,
            8,
            8,
        )

        title = QLabel(
            "PHYSICAL LCD MIRROR"
        )

        title.setObjectName(
            "SectionTitle"
        )

        title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.display = QLabel(
            "                \n"
            "                "
        )

        self.display.setObjectName(
            "VirtualLCD"
        )

        self.display.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.display.setMinimumHeight(
            82
        )

        layout.addWidget(
            title
        )

        layout.addWidget(
            self.display
        )

    def set_lines(
        self,
        line1,
        line2,
    ):

        line1 = (
            line1[:16]
            .ljust(16)
        )

        line2 = (
            line2[:16]
            .ljust(16)
        )

        self.display.setText(
            f"{line1}\n{line2}"
        )


# ============================================================
# ARTIFICIAL HORIZON
# ============================================================

class ArtificialHorizon(QWidget):

    def __init__(self):
        super().__init__()

        self.roll = 0.0
        self.pitch = 0.0

        self.setMinimumSize(
            250,
            210,
        )

    def set_attitude(
        self,
        roll,
        pitch,
    ):

        self.roll = roll
        self.pitch = pitch

        self.update()

    def paintEvent(
        self,
        event,
    ):

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        width = self.width()
        height = self.height()

        center_x = width / 2
        center_y = height / 2

        painter.fillRect(
            self.rect(),
            QColor(
                "#080b0a"
            ),
        )

        painter.save()

        painter.translate(
            center_x,
            center_y,
        )

        painter.rotate(
            -self.roll
        )

        pitch_scale = 1.8

        horizon_y = (
            self.pitch
            * pitch_scale
        )

        large = max(
            width,
            height,
        ) * 3

        # ====================================================
        # SKY
        # ====================================================

        painter.fillRect(
            int(-large),
            int(
                -large
                + horizon_y
            ),
            int(
                large * 2
            ),
            int(large),
            QColor(
                "#163c43"
            ),
        )

        # ====================================================
        # GROUND
        # ====================================================

        painter.fillRect(
            int(-large),
            int(horizon_y),
            int(
                large * 2
            ),
            int(large),
            QColor(
                "#313526"
            ),
        )

        # ====================================================
        # HORIZON LINE
        # ====================================================

        painter.setPen(
            QPen(
                QColor(
                    "#e7f8ed"
                ),
                2,
            )
        )

        painter.drawLine(
            int(-large),
            int(horizon_y),
            int(large),
            int(horizon_y),
        )

        # ====================================================
        # PITCH LADDER
        # ====================================================

        painter.setFont(
            QFont(
                "Consolas",
                8,
            )
        )

        for angle in range(
            -30,
            31,
            10,
        ):

            if angle == 0:
                continue

            y = (
                horizon_y
                - angle
                * pitch_scale
            )

            painter.setPen(
                QPen(
                    QColor(
                        "#8fcdb1"
                    ),
                    1,
                )
            )

            painter.drawLine(
                -28,
                int(y),
                28,
                int(y),
            )

            painter.drawText(
                35,
                int(y + 4),
                str(angle),
            )

        painter.restore()

        # ====================================================
        # FIXED AIRCRAFT MARKER
        # ====================================================

        painter.setPen(
            QPen(
                QColor(
                    "#45e39a"
                ),
                4,
            )
        )

        painter.drawLine(
            int(
                center_x - 38
            ),
            int(center_y),
            int(
                center_x - 8
            ),
            int(center_y),
        )

        painter.drawLine(
            int(
                center_x + 8
            ),
            int(center_y),
            int(
                center_x + 38
            ),
            int(center_y),
        )

        painter.drawLine(
            int(center_x),
            int(center_y),
            int(center_x),
            int(
                center_y + 11
            ),
        )

        painter.setBrush(
            QBrush(
                QColor(
                    "#45e39a"
                )
            )
        )

        painter.drawEllipse(
            int(
                center_x - 4
            ),
            int(
                center_y - 4
            ),
            8,
            8,
        )

        painter.setPen(
            QColor(
                "#d9eee2"
            )
        )

        painter.setFont(
            QFont(
                "Consolas",
                9,
                QFont.Weight.Bold,
            )
        )

        painter.drawText(
            10,
            20,
            f"ROLL  {self.roll:+.1f}°",
        )

        painter.drawText(
            10,
            40,
            f"PITCH {self.pitch:+.1f}°",
        )


# ============================================================
# MAIN DASHBOARD
# ============================================================

class FlightDashboard(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "STM32 Drone Control Station"
        )

        self.resize(
            1500,
            950,
        )

        # ====================================================
        # CANONICAL ATTITUDE FROM STM32
        # ====================================================

        self.roll = 0.0
        self.pitch = 0.0

        self.yaw_raw = 0.0
        self.yaw = 0.0

        self.yaw_enabled = False

        # ====================================================
        # PID
        # ====================================================

        self.pid_enabled = True

        self.roll_setpoint = 0.0
        self.pitch_setpoint = 0.0

        self.roll_pid = PIDController(
            kp=1.2,
            ki=0.0,
            kd=0.08,
            output_min=-25.0,
            output_max=25.0,
        )

        self.pitch_pid = PIDController(
            kp=1.2,
            ki=0.0,
            kd=0.08,
            output_min=-25.0,
            output_max=25.0,
        )

        self.motor_mixer = MotorMixer(
            base_throttle=50.0
        )

        self.roll_correction = 0.0
        self.pitch_correction = 0.0

        self.motor_outputs = {
            "M1": 50.0,
            "M2": 50.0,
            "M3": 50.0,
            "M4": 50.0,
        }

        self.pid_previous_time = (
            time.perf_counter()
        )

        # ====================================================
        # LCD
        # ====================================================

        self.lcd_line1 = ""
        self.lcd_line2 = ""

        self.lcd_seen = False

        # ====================================================
        # MQTT
        # ====================================================

        self.mqtt_client = None
        self.mqtt_connected = False

        # ====================================================
        # GUI UPDATE FLAGS
        # ====================================================

        self.dashboard_dirty = False
        self.graph_dirty = False

        # ====================================================
        # GRAPH DATA
        # ====================================================

        self.graph_points = 220

        self.graph_time = deque(
            maxlen=self.graph_points
        )

        self.graph_roll = deque(
            maxlen=self.graph_points
        )

        self.graph_pitch = deque(
            maxlen=self.graph_points
        )

        self.graph_yaw = deque(
            maxlen=self.graph_points
        )

        self.graph_start_time = (
            time.perf_counter()
        )

        # ====================================================
        # CSV RECORDING
        # ====================================================

        self.recording = False

        self.csv_file = None
        self.csv_writer = None

        self.record_start_time = None

        self.record_sample_count = 0

        self.current_record_path = None

        self.data_directory = (
            Path(__file__)
            .resolve()
            .parents[3]
            / "data"
        )

        # ====================================================
        # START APPLICATION
        # ====================================================

        self._build_ui()

        self._start_serial()

        self._start_mqtt()

        self._start_timers()

        self.log_event(
            "Ground station started"
        )

    # ========================================================
    # BUILD UI
    # ========================================================

    def _build_ui(self):

        # ====================================================
        # SCROLL AREA
        # ====================================================

        scroll_area = QScrollArea()

        scroll_area.setWidgetResizable(
            True
        )

        scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        root = QWidget()

        scroll_area.setWidget(
            root
        )

        self.setCentralWidget(
            scroll_area
        )

        root_layout = QVBoxLayout(
            root
        )

        root_layout.setContentsMargins(
            8,
            8,
            8,
            8,
        )

        root_layout.setSpacing(
            8
        )

        # ====================================================
        # HEADER
        # ====================================================

        header = QFrame()

        header.setObjectName(
            "Header"
        )

        header_layout = QHBoxLayout(
            header
        )

        header_layout.setContentsMargins(
            14,
            8,
            14,
            8,
        )

        title = QLabel(
            "STM32 DRONE CONTROL STATION"
        )

        title.setObjectName(
            "MainTitle"
        )

        subtitle = QLabel(
            "MPU6500  •  SPI  •  UART  •  I2C  •  MQTT"
        )

        subtitle.setObjectName(
            "MutedText"
        )

        self.system_badge = QLabel(
            "● SYSTEM STARTING"
        )

        self.system_badge.setObjectName(
            "StatusBadge"
        )

        header_layout.addWidget(
            title
        )

        header_layout.addWidget(
            subtitle
        )

        header_layout.addStretch()

        header_layout.addWidget(
            self.system_badge
        )

        root_layout.addWidget(
            header
        )

        # ====================================================
        # MAIN CONTENT
        # ====================================================

        main_layout = QHBoxLayout()

        main_layout.setSpacing(
            8
        )

        # ====================================================
        # CENTER
        # ====================================================

        center_layout = QVBoxLayout()

        center_layout.setSpacing(
            8
        )

        # ====================================================
        # 3D DRONE VIEW
        # ====================================================

        drone_frame = QFrame()

        drone_frame.setObjectName(
            "Panel"
        )

        drone_frame.setMinimumHeight(
            480
        )

        drone_layout = QVBoxLayout(
            drone_frame
        )

        drone_title = QLabel(
            "REAL-TIME ATTITUDE VISUALIZATION"
        )

        drone_title.setObjectName(
            "SectionTitle"
        )

        drone_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.drone = DroneVisualizer3D()

        self.drone.setMinimumHeight(
            430
        )

        self.drone.yaw_enabled = False

        drone_layout.addWidget(
            drone_title
        )

        drone_layout.addWidget(
            self.drone
        )

        center_layout.addWidget(
            drone_frame
        )

        # ====================================================
        # HORIZON + GRAPH
        # ====================================================

        instrument_layout = QHBoxLayout()

        instrument_layout.setSpacing(
            8
        )

        # ----------------------------------------------------
        # LEFT
        # ----------------------------------------------------

        left_instruments = QVBoxLayout()

        horizon_frame = QFrame()

        horizon_frame.setObjectName(
            "Panel"
        )

        horizon_layout = QVBoxLayout(
            horizon_frame
        )

        horizon_title = QLabel(
            "ARTIFICIAL HORIZON"
        )

        horizon_title.setObjectName(
            "SectionTitle"
        )

        horizon_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.horizon = ArtificialHorizon()

        horizon_layout.addWidget(
            horizon_title
        )

        horizon_layout.addWidget(
            self.horizon
        )

        left_instruments.addWidget(
            horizon_frame
        )

        self.virtual_lcd = VirtualLCD()

        left_instruments.addWidget(
            self.virtual_lcd
        )

        instrument_layout.addLayout(
            left_instruments,
            1,
        )

        # ====================================================
        # GRAPH
        # ====================================================

        graph_frame = QFrame()

        graph_frame.setObjectName(
            "Panel"
        )

        graph_layout = QVBoxLayout(
            graph_frame
        )

        graph_title = QLabel(
            "LIVE ATTITUDE TELEMETRY"
        )

        graph_title.setObjectName(
            "SectionTitle"
        )

        graph_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.graph = pg.PlotWidget()

        self.graph.setBackground(
            "#080b0a"
        )

        self.graph.showGrid(
            x=True,
            y=True,
            alpha=0.12,
        )

        self.graph.setLabel(
            "left",
            "Angle",
            units="°",
        )

        self.graph.setLabel(
            "bottom",
            "Time",
            units="s",
        )

        self.graph.setYRange(
            -100,
            100,
        )

        self.graph.addLegend()

        self.graph.getPlotItem().setClipToView(
            True
        )

        self.graph.getPlotItem().setDownsampling(
            auto=True,
            mode="peak",
        )

        self.roll_curve = self.graph.plot(
            name="Roll",
            pen=pg.mkPen(
                "#45e39a",
                width=1,
            ),
            antialias=False,
        )

        self.pitch_curve = self.graph.plot(
            name="Pitch",
            pen=pg.mkPen(
                "#59d8ff",
                width=1,
            ),
            antialias=False,
        )

        self.yaw_curve = self.graph.plot(
            name="Yaw",
            pen=pg.mkPen(
                "#f0b84d",
                width=1,
            ),
            antialias=False,
        )

        graph_layout.addWidget(
            graph_title
        )

        graph_layout.addWidget(
            self.graph
        )

        instrument_layout.addWidget(
            graph_frame,
            2,
        )

        center_layout.addLayout(
            instrument_layout
        )

        # ====================================================
        # MOTOR MIX
        # ====================================================

        motor_frame = QFrame()

        motor_frame.setObjectName(
            "Panel"
        )

        motor_layout = QVBoxLayout(
            motor_frame
        )

        motor_title = QLabel(
            "SIMULATED PID MOTOR MIX"
        )

        motor_title.setObjectName(
            "SectionTitle"
        )

        motor_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        motor_grid = QGridLayout()

        self.motor_m1 = MotorBar(
            "M1  FRONT-L"
        )

        self.motor_m2 = MotorBar(
            "M2  FRONT-R"
        )

        self.motor_m3 = MotorBar(
            "M3  REAR-L"
        )

        self.motor_m4 = MotorBar(
            "M4  REAR-R"
        )

        motor_grid.addWidget(
            self.motor_m1,
            0,
            0,
        )

        motor_grid.addWidget(
            self.motor_m2,
            0,
            1,
        )

        motor_grid.addWidget(
            self.motor_m3,
            1,
            0,
        )

        motor_grid.addWidget(
            self.motor_m4,
            1,
            1,
        )

        motor_layout.addWidget(
            motor_title
        )

        motor_layout.addLayout(
            motor_grid
        )

        center_layout.addWidget(
            motor_frame
        )

        # ====================================================
        # EVENT LOG
        # ====================================================

        console_frame = QFrame()

        console_frame.setObjectName(
            "Panel"
        )

        console_layout = QVBoxLayout(
            console_frame
        )

        console_title = QLabel(
            "SYSTEM EVENT LOG"
        )

        console_title.setObjectName(
            "SectionTitle"
        )

        console_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.console = QPlainTextEdit()

        self.console.setObjectName(
            "Console"
        )

        self.console.setReadOnly(
            True
        )

        self.console.setMaximumBlockCount(
            80
        )

        self.console.setMaximumHeight(
            90
        )

        console_layout.addWidget(
            console_title
        )

        console_layout.addWidget(
            self.console
        )

        center_layout.addWidget(
            console_frame
        )

        main_layout.addLayout(
            center_layout,
            5,
        )

        # ====================================================
        # RIGHT SIDE PANEL
        # ====================================================

        side_panel = QFrame()

        side_panel.setObjectName(
            "SidePanel"
        )

        side_panel.setMinimumWidth(
            260
        )

        side_panel.setMaximumWidth(
            300
        )

        panel_layout = QVBoxLayout(
            side_panel
        )

        panel_layout.setContentsMargins(
            9,
            9,
            9,
            9,
        )

        panel_layout.setSpacing(
            7
        )

        # ====================================================
        # ATTITUDE
        # ====================================================

        title = QLabel(
            "FLIGHT ATTITUDE"
        )

        title.setObjectName(
            "PanelTitle"
        )

        title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        panel_layout.addWidget(
            title
        )

        self.roll_card = TelemetryCard(
            "ROLL"
        )

        self.pitch_card = TelemetryCard(
            "PITCH"
        )

        self.yaw_card = TelemetryCard(
            "YAW"
        )

        panel_layout.addWidget(
            self.roll_card
        )

        panel_layout.addWidget(
            self.pitch_card
        )

        panel_layout.addWidget(
            self.yaw_card
        )

        # ====================================================
        # ZERO
        # ====================================================

        self.zero_button = QPushButton(
            "ZERO ATTITUDE"
        )

        self.zero_button.setMinimumHeight(
            42
        )

        self.zero_button.clicked.connect(
            self.zero_attitude
        )

        panel_layout.addWidget(
            self.zero_button
        )

        self.yaw_checkbox = QCheckBox(
            "Enable yaw"
        )

        self.yaw_checkbox.setChecked(
            False
        )

        self.yaw_checkbox.toggled.connect(
            self.toggle_yaw
        )

        panel_layout.addWidget(
            self.yaw_checkbox
        )

        self.reference_label = QLabel(
            "Reference: STM32 MASTER"
        )

        self.reference_label.setObjectName(
            "MutedText"
        )

        self.reference_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        panel_layout.addWidget(
            self.reference_label
        )

        # ====================================================
        # PID
        # ====================================================

        pid_title = QLabel(
            "PID ATTITUDE CONTROL"
        )

        pid_title.setObjectName(
            "PanelTitle"
        )

        pid_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        panel_layout.addWidget(
            pid_title
        )

        self.pid_checkbox = QCheckBox(
            "Enable PID simulation"
        )

        self.pid_checkbox.setChecked(
            True
        )

        self.pid_checkbox.toggled.connect(
            self.toggle_pid
        )

        panel_layout.addWidget(
            self.pid_checkbox
        )

        self.pid_status_label = QLabel(
            "PID ACTIVE\n"
            "Setpoint R 0° / P 0°"
        )

        self.pid_status_label.setObjectName(
            "PidStatus"
        )

        self.pid_status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        panel_layout.addWidget(
            self.pid_status_label
        )

        self.pid_output_label = QLabel(
            "R correction: +0.0\n"
            "P correction: +0.0"
        )

        self.pid_output_label.setObjectName(
            "MutedText"
        )

        self.pid_output_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        panel_layout.addWidget(
            self.pid_output_label
        )

        # ====================================================
        # RECORDING
        # ====================================================

        recording_title = QLabel(
            "TELEMETRY RECORDING"
        )

        recording_title.setObjectName(
            "PanelTitle"
        )

        recording_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        panel_layout.addWidget(
            recording_title
        )

        self.record_button = QPushButton(
            "● START RECORDING"
        )

        self.record_button.setMinimumHeight(
            40
        )

        self.record_button.clicked.connect(
            self.toggle_recording
        )

        panel_layout.addWidget(
            self.record_button
        )

        self.record_status_label = QLabel(
            "Not recording"
        )

        self.record_status_label.setObjectName(
            "MutedText"
        )

        self.record_status_label.setWordWrap(
            True
        )

        self.record_status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        panel_layout.addWidget(
            self.record_status_label
        )

        self.sample_label = QLabel(
            "Samples: 0"
        )

        self.sample_label.setObjectName(
            "MutedText"
        )

        self.sample_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        panel_layout.addWidget(
            self.sample_label
        )

        # ====================================================
        # COMMUNICATION
        # ====================================================

        communication_title = QLabel(
            "COMMUNICATION"
        )

        communication_title.setObjectName(
            "PanelTitle"
        )

        communication_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        panel_layout.addWidget(
            communication_title
        )

        self.status_label = QLabel(
            "UART: connecting..."
        )

        self.status_label.setObjectName(
            "ConnectionStatus"
        )

        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        panel_layout.addWidget(
            self.status_label
        )

        self.lcd_status_label = QLabel(
            "LCD mirror: waiting"
        )

        self.lcd_status_label.setObjectName(
            "MutedText"
        )

        self.lcd_status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        panel_layout.addWidget(
            self.lcd_status_label
        )

        # ====================================================
        # MQTT STATUS
        # ====================================================

        self.mqtt_status_label = QLabel(
            "MQTT: STARTING..."
        )

        self.mqtt_status_label.setObjectName(
            "MQTTStatus"
        )

        self.mqtt_status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        panel_layout.addWidget(
            self.mqtt_status_label
        )

        panel_layout.addStretch()

        main_layout.addWidget(
            side_panel,
            1,
        )

        root_layout.addLayout(
            main_layout
        )

    # ========================================================
    # EVENT LOG
    # ========================================================

    def log_event(
        self,
        message,
    ):

        timestamp = (
            datetime.now()
            .strftime(
                "%H:%M:%S"
            )
        )

        self.console.appendPlainText(
            f"[{timestamp}] {message}"
        )

    # ========================================================
    # SERIAL START
    # ========================================================

    def _start_serial(self):

        self.serial_worker = SerialWorker(
            SERIAL_PORT,
            BAUD_RATE,
        )

        self.serial_worker.attitude_received.connect(
            self.on_attitude
        )

        self.serial_worker.lcd_received.connect(
            self.on_lcd_line
        )

        self.serial_worker.connection_changed.connect(
            self.on_connection
        )

        self.serial_worker.start()

    # ========================================================
    # MQTT START
    # ========================================================

    def _start_mqtt(self):

        if not MQTT_ENABLED:

            self.mqtt_status_label.setText(
                "MQTT: DISABLED"
            )

            self.log_event(
                "MQTT disabled in configuration"
            )

            return

        if not MQTT_ACCESS_TOKEN:

            self.mqtt_status_label.setText(
                "MQTT: TOKEN REQUIRED"
            )

            self.log_event(
                "MQTT access token missing"
            )

            return

        if (
            MQTT_ACCESS_TOKEN.startswith(
                "PASTE_"
            )
            or
            MQTT_ACCESS_TOKEN.startswith(
                "PUT_"
            )
        ):

            self.mqtt_status_label.setText(
                "MQTT: TOKEN REQUIRED"
            )

            self.log_event(
                "MQTT access token not configured"
            )

            return

        self.mqtt_client = (
            MQTTTelemetryClient(
                host=MQTT_HOST,
                port=MQTT_PORT,
                access_token=
                    MQTT_ACCESS_TOKEN,
                use_tls=
                    MQTT_USE_TLS,
            )
        )

        self.mqtt_client.status_changed.connect(
            self.on_mqtt_status
        )

        self.mqtt_status_label.setText(
            "MQTT: CONNECTING..."
        )

        self.log_event(
            f"Connecting MQTT to {MQTT_HOST}"
        )

        self.mqtt_client.connect_cloud()

    # ========================================================
    # MQTT STATUS
    # ========================================================

    def on_mqtt_status(
        self,
        connected,
        message,
    ):

        self.mqtt_connected = connected

        if connected:

            self.mqtt_status_label.setText(
                "MQTT: CLOUD ONLINE"
            )

            self.mqtt_status_label.setProperty(
                "connected",
                True,
            )

        else:

            self.mqtt_status_label.setText(
                "MQTT: OFFLINE"
            )

            self.mqtt_status_label.setProperty(
                "connected",
                False,
            )

        self.mqtt_status_label.style().unpolish(
            self.mqtt_status_label
        )

        self.mqtt_status_label.style().polish(
            self.mqtt_status_label
        )

        self.log_event(
            message
        )

    # ========================================================
    # TIMERS
    # ========================================================

    def _start_timers(self):

        # Dashboard + PID = 20 Hz
        self.dashboard_timer = QTimer(
            self
        )

        self.dashboard_timer.timeout.connect(
            self.update_dashboard
        )

        self.dashboard_timer.start(
            50
        )

        # Graph = 10 Hz
        self.graph_timer = QTimer(
            self
        )

        self.graph_timer.timeout.connect(
            self.update_graph
        )

        self.graph_timer.start(
            100
        )

        # Cloud = 5 Hz by default
        self.mqtt_timer = QTimer(
            self
        )

        self.mqtt_timer.timeout.connect(
            self.publish_mqtt_telemetry
        )

        self.mqtt_timer.start(
            MQTT_PUBLISH_INTERVAL_MS
        )

    # ========================================================
    # ATTITUDE FROM STM32
    # ========================================================

    def on_attitude(
        self,
        roll,
        pitch,
        yaw,
    ):

        # STM32 already applies zero reference.
        self.roll = roll
        self.pitch = pitch

        self.yaw_raw = yaw

        if self.yaw_enabled:

            self.yaw = yaw

        else:

            self.yaw = 0.0

        # ====================================================
        # QT QUICK 3D
        # ====================================================

        self.drone.set_attitude(
            self.roll,
            self.pitch,
            self.yaw,
        )

        # ====================================================
        # CSV
        # ====================================================

        if self.recording:

            self._record_sample()

        self.dashboard_dirty = True
        self.graph_dirty = True

    # ========================================================
    # LCD
    # ========================================================

    def on_lcd_line(
        self,
        row,
        text,
    ):

        if row == 1:

            self.lcd_line1 = text

        elif row == 2:

            self.lcd_line2 = text

        self.virtual_lcd.set_lines(
            self.lcd_line1,
            self.lcd_line2,
        )

        if not self.lcd_seen:

            self.lcd_seen = True

            self.lcd_status_label.setText(
                "LCD mirror: ONLINE"
            )

            self.log_event(
                "Physical LCD mirror synchronized"
            )

    # ========================================================
    # ZERO ATTITUDE
    # ========================================================

    def zero_attitude(self):

        # STM32 owns zero reference.
        self.serial_worker.send_command(
            "Z"
        )

        self.roll_pid.reset()
        self.pitch_pid.reset()

        self.pid_previous_time = (
            time.perf_counter()
        )

        # Reset graph
        self.graph_time.clear()
        self.graph_roll.clear()
        self.graph_pitch.clear()
        self.graph_yaw.clear()

        self.graph_start_time = (
            time.perf_counter()
        )

        self.roll_curve.setData(
            [],
            [],
        )

        self.pitch_curve.setData(
            [],
            [],
        )

        self.yaw_curve.setData(
            [],
            [],
        )

        self.reference_label.setText(
            "Reference: ZERO requested"
        )

        self.log_event(
            "ZERO command sent to STM32"
        )

    # ========================================================
    # YAW
    # ========================================================

    def toggle_yaw(
        self,
        enabled,
    ):

        self.yaw_enabled = enabled

        self.drone.yaw_enabled = enabled

        if enabled:

            self.yaw = (
                self.yaw_raw
            )

            self.log_event(
                "Yaw visualization enabled"
            )

        else:

            self.yaw = 0.0

            self.drone.set_attitude(
                self.roll,
                self.pitch,
                0.0,
            )

            self.log_event(
                "Yaw visualization disabled"
            )

    # ========================================================
    # PID
    # ========================================================

    def toggle_pid(
        self,
        enabled,
    ):

        self.pid_enabled = enabled

        self.roll_pid.reset()
        self.pitch_pid.reset()

        self.pid_previous_time = (
            time.perf_counter()
        )

        self.drone.set_pid_enabled(
            enabled
        )

        if enabled:

            self.pid_status_label.setText(
                "PID ACTIVE\n"
                "Setpoint R 0° / P 0°"
            )

            self.log_event(
                "PID simulation enabled"
            )

        else:

            self.pid_status_label.setText(
                "PID OFF"
            )

            self.log_event(
                "PID simulation disabled"
            )

    # ========================================================
    # PID CALCULATION
    # ========================================================

    def update_pid_control(self):

        current_time = (
            time.perf_counter()
        )

        dt = (
            current_time
            - self.pid_previous_time
        )

        self.pid_previous_time = (
            current_time
        )

        if (
            dt <= 0.0
            or dt > 0.2
        ):

            dt = 0.05

        if not self.pid_enabled:

            self.roll_correction = 0.0
            self.pitch_correction = 0.0

            self.motor_outputs = {
                "M1": 50.0,
                "M2": 50.0,
                "M3": 50.0,
                "M4": 50.0,
            }

            return

        self.roll_correction = (
            self.roll_pid.update(
                self.roll_setpoint,
                self.roll,
                dt,
            )
        )

        self.pitch_correction = (
            self.pitch_pid.update(
                self.pitch_setpoint,
                self.pitch,
                dt,
            )
        )

        self.motor_outputs = (
            self.motor_mixer.mix(
                self.roll_correction,
                self.pitch_correction,
            )
        )

    # ========================================================
    # DASHBOARD
    # ========================================================

    def update_dashboard(self):

        if not self.dashboard_dirty:
            return

        self.dashboard_dirty = False

        # ====================================================
        # ATTITUDE CARDS
        # ====================================================

        self.roll_card.set_value(
            self.roll
        )

        self.pitch_card.set_value(
            self.pitch
        )

        if self.yaw_enabled:

            self.yaw_card.set_value(
                self.yaw
            )

        else:

            self.yaw_card.set_disabled_value()

        # ====================================================
        # HORIZON
        # ====================================================

        self.horizon.set_attitude(
            self.roll,
            self.pitch,
        )

        # ====================================================
        # PID
        # ====================================================

        self.update_pid_control()

        self.pid_output_label.setText(
            f"R correction: "
            f"{self.roll_correction:+.1f}\n"
            f"P correction: "
            f"{self.pitch_correction:+.1f}"
        )

        # ====================================================
        # MOTOR BARS
        # ====================================================

        self.motor_m1.set_value(
            self.motor_outputs["M1"]
        )

        self.motor_m2.set_value(
            self.motor_outputs["M2"]
        )

        self.motor_m3.set_value(
            self.motor_outputs["M3"]
        )

        self.motor_m4.set_value(
            self.motor_outputs["M4"]
        )

        # ====================================================
        # QT QUICK 3D MOTOR THRUST
        # ====================================================

        self.drone.set_motor_outputs(
            self.motor_outputs
        )

        self.drone.set_pid_corrections(
            self.roll_correction,
            self.pitch_correction,
        )

        # ====================================================
        # RECORDING
        # ====================================================

        if self.recording:

            self.sample_label.setText(
                f"Samples: "
                f"{self.record_sample_count}"
            )

    # ========================================================
    # GRAPH
    # ========================================================

    def update_graph(self):

        if not self.graph_dirty:
            return

        self.graph_dirty = False

        elapsed = (
            time.perf_counter()
            - self.graph_start_time
        )

        self.graph_time.append(
            elapsed
        )

        self.graph_roll.append(
            self.roll
        )

        self.graph_pitch.append(
            self.pitch
        )

        self.graph_yaw.append(
            self.yaw
        )

        x = list(
            self.graph_time
        )

        self.roll_curve.setData(
            x,
            list(
                self.graph_roll
            ),
        )

        self.pitch_curve.setData(
            x,
            list(
                self.graph_pitch
            ),
        )

        self.yaw_curve.setData(
            x,
            list(
                self.graph_yaw
            ),
        )

        if len(x) > 1:

            right = x[-1]

            left = max(
                0.0,
                right - 8.0,
            )

            self.graph.setXRange(
                left,
                max(
                    8.0,
                    right,
                ),
                padding=0,
            )

    # ========================================================
    # MQTT PUBLISH
    # ========================================================

    def publish_mqtt_telemetry(self):

        if self.mqtt_client is None:
            return

        if not self.mqtt_connected:
            return

        self.mqtt_client.publish_telemetry(
            roll=self.roll,
            pitch=self.pitch,
            yaw=self.yaw,

            motor_outputs=
                self.motor_outputs,

            roll_correction=
                self.roll_correction,

            pitch_correction=
                self.pitch_correction,

            yaw_enabled=
                self.yaw_enabled,
        )

    # ========================================================
    # RECORDING
    # ========================================================

    def toggle_recording(self):

        if self.recording:

            self.stop_recording()

        else:

            self.start_recording()

    def start_recording(self):

        self.data_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp = (
            datetime.now()
            .strftime(
                "%Y-%m-%d_%H-%M-%S"
            )
        )

        self.current_record_path = (
            self.data_directory
            /
            f"imu_telemetry_{timestamp}.csv"
        )

        self.csv_file = open(
            self.current_record_path,
            "w",
            newline="",
            encoding="utf-8",
        )

        self.csv_writer = csv.writer(
            self.csv_file
        )

        self.csv_writer.writerow(
            [
                "time_s",

                "roll_deg",
                "pitch_deg",
                "yaw_deg",

                "roll_pid",
                "pitch_pid",

                "motor_m1",
                "motor_m2",
                "motor_m3",
                "motor_m4",

                "mqtt_connected",
            ]
        )

        self.record_start_time = (
            time.perf_counter()
        )

        self.record_sample_count = 0

        self.recording = True

        self.record_button.setText(
            "■ STOP RECORDING"
        )

        self.record_button.setProperty(
            "recording",
            True,
        )

        self.record_button.style().unpolish(
            self.record_button
        )

        self.record_button.style().polish(
            self.record_button
        )

        self.record_status_label.setText(
            self.current_record_path.name
        )

        self.log_event(
            "CSV recording started"
        )

    def _record_sample(self):

        if (
            not self.recording
            or
            self.csv_writer is None
        ):
            return

        elapsed = (
            time.perf_counter()
            -
            self.record_start_time
        )

        self.csv_writer.writerow(
            [
                f"{elapsed:.4f}",

                f"{self.roll:.3f}",
                f"{self.pitch:.3f}",
                f"{self.yaw:.3f}",

                f"{self.roll_correction:.3f}",
                f"{self.pitch_correction:.3f}",

                f"{self.motor_outputs['M1']:.2f}",
                f"{self.motor_outputs['M2']:.2f}",
                f"{self.motor_outputs['M3']:.2f}",
                f"{self.motor_outputs['M4']:.2f}",

                int(
                    self.mqtt_connected
                ),
            ]
        )

        self.record_sample_count += 1

        if (
            self.record_sample_count
            % 25
            == 0
        ):

            self.csv_file.flush()

    def stop_recording(self):

        if not self.recording:
            return

        self.recording = False

        if self.csv_file is not None:

            self.csv_file.flush()
            self.csv_file.close()

        self.csv_file = None
        self.csv_writer = None

        self.record_button.setText(
            "● START RECORDING"
        )

        self.record_button.setProperty(
            "recording",
            False,
        )

        self.record_button.style().unpolish(
            self.record_button
        )

        self.record_button.style().polish(
            self.record_button
        )

        if self.current_record_path:

            self.record_status_label.setText(
                "Saved: "
                +
                self.current_record_path.name
            )

        self.log_event(
            "CSV recording stopped"
        )

    # ========================================================
    # UART CONNECTION
    # ========================================================

    def on_connection(
        self,
        connected,
        message,
    ):

        if connected:

            self.status_label.setText(
                f"UART: {SERIAL_PORT}\n"
                f"{BAUD_RATE} baud"
            )

            self.status_label.setProperty(
                "connected",
                True,
            )

            self.system_badge.setText(
                "● SYSTEM ONLINE"
            )

            self.system_badge.setProperty(
                "online",
                True,
            )

            self.log_event(
                f"UART connected on "
                f"{SERIAL_PORT}"
            )

        else:

            self.status_label.setText(
                "UART: DISCONNECTED"
            )

            self.status_label.setProperty(
                "connected",
                False,
            )

            self.system_badge.setText(
                "● SYSTEM OFFLINE"
            )

            self.system_badge.setProperty(
                "online",
                False,
            )

            self.log_event(
                f"UART disconnected: "
                f"{message}"
            )

        for widget in (
            self.status_label,
            self.system_badge,
        ):

            widget.style().unpolish(
                widget
            )

            widget.style().polish(
                widget
            )

    # ========================================================
    # CLOSE
    # ========================================================

    def closeEvent(
        self,
        event,
    ):

        self.dashboard_timer.stop()
        self.graph_timer.stop()
        self.mqtt_timer.stop()

        if self.recording:

            self.stop_recording()

        if self.mqtt_client is not None:

            self.mqtt_client.disconnect_cloud()

        self.serial_worker.stop()

        event.accept()


# ============================================================
# MAIN
# ============================================================

def main():

    pg.setConfigOptions(
        antialias=False
    )

    app = QApplication(
        sys.argv
    )

    app.setStyle(
        "Fusion"
    )

    # ========================================================
    # AVIONICS THEME
    # ========================================================

    app.setStyleSheet(
        """
        QMainWindow,
        QWidget {
            background-color: #080B0A;
            color: #D9EEE2;
            font-family: Segoe UI;
        }

        QFrame#Header {
            background-color: #0C1210;
            border: 1px solid #244335;
            border-radius: 8px;
        }

        QFrame#Panel,
        QFrame#SidePanel {
            background-color: #101613;
            border: 1px solid #233C30;
            border-radius: 8px;
        }

        QFrame#TelemetryCard,
        QFrame#MotorCard {
            background-color: #121C17;
            border: 1px solid #294537;
            border-radius: 6px;
        }

        QLabel#MainTitle {
            color: #45E39A;
            font-size: 20px;
            font-weight: 800;
        }

        QLabel#PanelTitle,
        QLabel#SectionTitle {
            color: #59D8FF;
            font-size: 12px;
            font-weight: 700;
            padding: 4px;
        }

        QLabel#SmallTitle,
        QLabel#MotorTitle {
            color: #82A995;
            font-size: 10px;
            font-weight: 600;
        }

        QLabel#BigValue {
            color: #F0FFF5;
            font-size: 25px;
            font-weight: 750;
        }

        QLabel#MutedText {
            color: #789A86;
            font-size: 11px;
        }

        QLabel#PidStatus {
            color: #45E39A;
            background-color: #0A2015;
            border: 1px solid #296A47;
            border-radius: 5px;
            padding: 7px;
            font-weight: 700;
        }

        QLabel#ConnectionStatus {
            background-color: #0A1811;
            border: 1px solid #294537;
            border-radius: 6px;
            padding: 8px;
        }

        QLabel#ConnectionStatus[connected="true"] {
            color: #45E39A;
        }

        QLabel#ConnectionStatus[connected="false"] {
            color: #FF6565;
        }

        QLabel#MQTTStatus {
            background-color: #0A1811;
            border: 1px solid #294537;
            border-radius: 5px;
            padding: 6px;
            font-weight: 700;
        }

        QLabel#MQTTStatus[connected="true"] {
            color: #45E39A;
        }

        QLabel#MQTTStatus[connected="false"] {
            color: #FFB84D;
        }

        QLabel#StatusBadge {
            min-width: 140px;
            padding: 6px 10px;
            border-radius: 6px;
            font-weight: 800;
        }

        QLabel#StatusBadge[online="true"] {
            color: #45E39A;
            background-color: #0A2015;
            border: 1px solid #296A47;
        }

        QLabel#StatusBadge[online="false"] {
            color: #FF6565;
            background-color: #251010;
            border: 1px solid #6B3030;
        }

        QLabel#VirtualLCD {
            background-color: #123B70;
            color: #D7F6FF;

            border: 4px solid #263D4A;
            border-radius: 5px;

            font-family: Consolas;
            font-size: 18px;
            font-weight: 800;

            padding: 10px;
        }

        QPushButton {
            background-color: #173C2A;
            color: #E2FFF0;

            border: 1px solid #347755;
            border-radius: 6px;

            padding: 8px;

            font-weight: 700;
        }

        QPushButton:hover {
            background-color: #205238;
            border: 1px solid #45E39A;
        }

        QPushButton:pressed {
            background-color: #0D2A1C;
        }

        QPushButton[recording="true"] {
            background-color: #702525;
            border: 1px solid #FF6565;
            color: white;
        }

        QCheckBox {
            color: #D2E6DA;
            padding: 5px;
        }

        QCheckBox::indicator {
            width: 16px;
            height: 16px;
        }

        QProgressBar {
            border: 1px solid #294537;
            border-radius: 4px;

            background-color: #060B08;

            color: #E3FFF0;
            text-align: center;

            min-height: 18px;
        }

        QProgressBar::chunk {
            background-color: #45E39A;
            border-radius: 3px;
        }

        QPlainTextEdit#Console {
            background-color: #050807;

            color: #78DFA5;

            border: 1px solid #233C30;
            border-radius: 5px;

            font-family: Consolas;
            font-size: 10px;

            padding: 5px;
        }

        QScrollBar:vertical {
            background: #0B100D;
            width: 12px;
            margin: 0px;
        }

        QScrollBar::handle:vertical {
            background: #315D47;
            min-height: 30px;
            border-radius: 5px;
        }

        QScrollBar::handle:vertical:hover {
            background: #45A873;
        }

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0px;
        }
        """
    )

    window = FlightDashboard()

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()