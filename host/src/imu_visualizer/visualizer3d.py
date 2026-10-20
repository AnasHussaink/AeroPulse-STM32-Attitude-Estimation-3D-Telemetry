import os
from pathlib import Path

import PySide6


# ============================================================
# WINDOWS / QT QUICK 3D DLL SEARCH PATH FIX
# ============================================================

_QT_DLL_HANDLE = None

if os.name == "nt":

    _PYSIDE_DIR = (
        Path(PySide6.__file__)
        .resolve()
        .parent
    )

    # Python 3.8+ Windows DLL search path
    _QT_DLL_HANDLE = os.add_dll_directory(
        str(_PYSIDE_DIR)
    )

    # Also prepend to PATH for Qt/QML plugin loader
    os.environ["PATH"] = (
        str(_PYSIDE_DIR)
        + os.pathsep
        + os.environ.get(
            "PATH",
            ""
        )
    )

from pathlib import Path

from PySide6.QtCore import (
    QUrl,
)

from PySide6.QtQuick import (
    QQuickView,
)

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
)


class DroneVisualizer3D(QWidget):
    """
    Qt Quick 3D based drone renderer.

    Python sends:
        Roll
        Pitch
        Yaw
        PID corrections
        Motor outputs

    QML handles:
        3D rendering
        Lighting
        Shadows
        Materials
        Propeller animation
        Ghost reference
        Thrust visualization
        Camera positions
    """

    def __init__(self):
        super().__init__()

        self.yaw_enabled = False

        self._build_ui()

    # =========================================================
    # UI
    # =========================================================

    def _build_ui(self):

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout.setSpacing(
            5
        )

        # =====================================================
        # QT QUICK 3D VIEW
        # =====================================================

        self.quick_view = QQuickView()

        self.quick_view.setResizeMode(
            QQuickView.ResizeMode.SizeRootObjectToView
        )

        qml_path = (
            Path(__file__)
            .resolve()
            .with_name(
                "drone_view.qml"
            )
        )

        self.quick_view.setSource(
            QUrl.fromLocalFile(
                str(qml_path)
            )
        )
        if self.quick_view.status() == QQuickView.Status.Error:
            print("\nQML LOAD ERROR:")
            for error in self.quick_view.errors():
                print(error.toString())

        self.root = (
            self.quick_view.rootObject()
        )

        self.container = (
            QWidget.createWindowContainer(
                self.quick_view,
                self
            )
        )

        self.container.setMinimumHeight(
            420
        )

        layout.addWidget(
            self.container
        )

        # =====================================================
        # CAMERA BUTTONS
        # =====================================================

        camera_layout = QHBoxLayout()

        camera_layout.setSpacing(
            5
        )

        iso_button = QPushButton(
            "ISO"
        )

        top_button = QPushButton(
            "TOP"
        )

        front_button = QPushButton(
            "FRONT"
        )

        close_button = QPushButton(
            "CLOSE"
        )

        iso_button.clicked.connect(
            lambda:
            self.set_camera_mode(0)
        )

        top_button.clicked.connect(
            lambda:
            self.set_camera_mode(1)
        )

        front_button.clicked.connect(
            lambda:
            self.set_camera_mode(2)
        )

        close_button.clicked.connect(
            lambda:
            self.set_camera_mode(3)
        )

        camera_layout.addWidget(
            iso_button
        )

        camera_layout.addWidget(
            top_button
        )

        camera_layout.addWidget(
            front_button
        )

        camera_layout.addWidget(
            close_button
        )

        layout.addLayout(
            camera_layout
        )

    # =========================================================
    # HELPER
    # =========================================================

    def _set_property(
        self,
        name,
        value
    ):

        if self.root is not None:

            self.root.setProperty(
                name,
                value
            )

    # =========================================================
    # ATTITUDE
    # =========================================================

    def set_attitude(
        self,
        roll,
        pitch,
        yaw
    ):

        self._set_property(
            "rollAngle",
            float(roll)
        )

        self._set_property(
            "pitchAngle",
            float(pitch)
        )

        if self.yaw_enabled:

            self._set_property(
                "yawAngle",
                float(yaw)
            )

        else:

            self._set_property(
                "yawAngle",
                0.0
            )

    # =========================================================
    # MOTOR OUTPUTS
    # =========================================================

    def set_motor_outputs(
        self,
        motors
    ):

        self._set_property(
            "motor1",
            float(
                motors["M1"]
            )
        )

        self._set_property(
            "motor2",
            float(
                motors["M2"]
            )
        )

        self._set_property(
            "motor3",
            float(
                motors["M3"]
            )
        )

        self._set_property(
            "motor4",
            float(
                motors["M4"]
            )
        )

    # =========================================================
    # PID VISUALIZATION
    # =========================================================

    def set_pid_corrections(
        self,
        roll_correction,
        pitch_correction
    ):

        self._set_property(
            "rollCorrection",
            float(
                roll_correction
            )
        )

        self._set_property(
            "pitchCorrection",
            float(
                pitch_correction
            )
        )

    def set_pid_enabled(
        self,
        enabled
    ):

        self._set_property(
            "pidEnabled",
            bool(enabled)
        )

    # =========================================================
    # CAMERA
    # =========================================================

    def set_camera_mode(
        self,
        mode
    ):

        self._set_property(
            "cameraMode",
            int(mode)
        )

    # =========================================================
    # LEGACY API COMPATIBILITY
    # =========================================================

    def animate(self):
        """
        Kept only because old app_3d.py may still call animate().

        Qt Quick 3D renders independently, so nothing is
        required here.
        """
        pass