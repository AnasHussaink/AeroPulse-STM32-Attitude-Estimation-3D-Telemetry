import numpy as np

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
)

import pyqtgraph.opengl as gl


class DroneVisualizer3D(QWidget):
    """
    Real-time X-frame mini quadcopter visualizer.

    STM32 already provides zero-referenced attitude.

    Coordinate convention:
        +X = front
        +Y = side
        +Z = up
    """

    def __init__(self):
        super().__init__()

        # =====================================================
        # ATTITUDE
        # =====================================================

        self.target_roll = 0.0
        self.target_pitch = 0.0
        self.target_yaw = 0.0

        self.display_roll = 0.0
        self.display_pitch = 0.0
        self.display_yaw = 0.0

        # Higher = faster response.
        # STM32 already filters data, so only light
        # visual interpolation is required.
        self.smoothing = 0.52

        self.yaw_enabled = False

        # =====================================================
        # PROPELLERS
        # =====================================================

        self.prop_angle = 0.0
        self.prop_speed = 22.0

        self._build_ui()
        self._build_world()
        self._build_drone()

    # =========================================================
    # UI
    # =========================================================

    def _build_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.view = gl.GLViewWidget()

        # Charcoal / avionics background
        self.view.setBackgroundColor(
            (
                7,
                10,
                9,
                255,
            )
        )

        # Realistic three-quarter camera
        self.view.setCameraPosition(
            distance=8.2,
            elevation=27,
            azimuth=-38,
        )

        layout.addWidget(
            self.view
        )

    # =========================================================
    # WORLD
    # =========================================================

    def _build_world(self):

        # -----------------------------------------------------
        # Ground grid
        # -----------------------------------------------------

        self.grid = gl.GLGridItem()

        self.grid.setSize(
            x=11,
            y=11,
        )

        self.grid.setSpacing(
            x=1,
            y=1,
        )

        try:
            self.grid.setColor(
                (
                    35,
                    130,
                    92,
                    65,
                )
            )
        except Exception:
            pass

        self.grid.translate(
            0,
            0,
            -1.18,
        )

        self.view.addItem(
            self.grid
        )

        # -----------------------------------------------------
        # Soft ground shadow
        # -----------------------------------------------------

        angles = np.linspace(
            0.0,
            2.0 * np.pi,
            72,
        )

        shadow = np.column_stack(
            (
                1.85 * np.cos(angles),
                1.15 * np.sin(angles),
                np.full_like(
                    angles,
                    -1.12,
                ),
            )
        )

        self.shadow_item = gl.GLLinePlotItem(
            pos=shadow,
            color=(
                0.12,
                0.75,
                0.42,
                0.13,
            ),
            width=2,
            antialias=False,
        )

        self.view.addItem(
            self.shadow_item
        )

        # -----------------------------------------------------
        # Heading ring
        # -----------------------------------------------------

        radius = 3.0

        ring = np.column_stack(
            (
                radius * np.cos(angles),
                radius * np.sin(angles),
                np.full_like(
                    angles,
                    -1.10,
                ),
            )
        )

        self.heading_ring = gl.GLLinePlotItem(
            pos=ring,
            color=(
                0.20,
                0.75,
                0.55,
                0.16,
            ),
            width=1,
            antialias=False,
        )

        self.view.addItem(
            self.heading_ring
        )

        # Forward reference mark
        front_mark = np.array(
            [
                [2.65, 0.0, -1.09],
                [3.28, 0.0, -1.09],
            ],
            dtype=float,
        )

        self.heading_front = gl.GLLinePlotItem(
            pos=front_mark,
            color=(
                0.28,
                1.0,
                0.58,
                0.70,
            ),
            width=3,
            antialias=False,
        )

        self.view.addItem(
            self.heading_front
        )

    # =========================================================
    # GEOMETRY HELPERS
    # =========================================================

    @staticmethod
    def _box_mesh(
        center,
        size,
    ):

        cx, cy, cz = center
        sx, sy, sz = size

        x = sx / 2.0
        y = sy / 2.0
        z = sz / 2.0

        vertices = np.array(
            [
                [cx - x, cy - y, cz - z],
                [cx + x, cy - y, cz - z],
                [cx + x, cy + y, cz - z],
                [cx - x, cy + y, cz - z],

                [cx - x, cy - y, cz + z],
                [cx + x, cy - y, cz + z],
                [cx + x, cy + y, cz + z],
                [cx - x, cy + y, cz + z],
            ],
            dtype=float,
        )

        faces = np.array(
            [
                [0, 1, 2],
                [0, 2, 3],

                [4, 6, 5],
                [4, 7, 6],

                [0, 4, 5],
                [0, 5, 1],

                [3, 2, 6],
                [3, 6, 7],

                [0, 3, 7],
                [0, 7, 4],

                [1, 5, 6],
                [1, 6, 2],
            ],
            dtype=int,
        )

        return (
            vertices,
            faces,
        )

    @staticmethod
    def _arm_mesh(
        start,
        end,
        width=0.14,
        height=0.055,
    ):

        start = np.array(
            start,
            dtype=float,
        )

        end = np.array(
            end,
            dtype=float,
        )

        direction = end - start

        direction[2] = 0.0

        direction /= np.linalg.norm(
            direction
        )

        perpendicular = np.array(
            [
                -direction[1],
                direction[0],
                0.0,
            ]
        )

        half_width = (
            perpendicular
            * width
            / 2.0
        )

        z = np.array(
            [
                0.0,
                0.0,
                height / 2.0,
            ]
        )

        vertices = np.array(
            [
                start - half_width - z,
                start + half_width - z,
                end + half_width - z,
                end - half_width - z,

                start - half_width + z,
                start + half_width + z,
                end + half_width + z,
                end - half_width + z,
            ]
        )

        faces = np.array(
            [
                [0, 1, 2],
                [0, 2, 3],

                [4, 6, 5],
                [4, 7, 6],

                [0, 4, 5],
                [0, 5, 1],

                [3, 2, 6],
                [3, 6, 7],

                [0, 3, 7],
                [0, 7, 4],

                [1, 5, 6],
                [1, 6, 2],
            ],
            dtype=int,
        )

        return (
            vertices,
            faces,
        )

    @staticmethod
    def _cylinder_mesh(
        center,
        radius,
        height,
        segments=16,
    ):

        cx, cy, cz = center

        angles = np.linspace(
            0.0,
            2.0 * np.pi,
            segments,
            endpoint=False,
        )

        bottom_z = (
            cz - height / 2.0
        )

        top_z = (
            cz + height / 2.0
        )

        vertices = []

        for angle in angles:

            vertices.append(
                [
                    cx + radius * np.cos(angle),
                    cy + radius * np.sin(angle),
                    bottom_z,
                ]
            )

        for angle in angles:

            vertices.append(
                [
                    cx + radius * np.cos(angle),
                    cy + radius * np.sin(angle),
                    top_z,
                ]
            )

        vertices.append(
            [
                cx,
                cy,
                bottom_z,
            ]
        )

        vertices.append(
            [
                cx,
                cy,
                top_z,
            ]
        )

        bottom_center = (
            2 * segments
        )

        top_center = (
            2 * segments + 1
        )

        faces = []

        for i in range(segments):

            nxt = (
                i + 1
            ) % segments

            bottom_i = i
            bottom_next = nxt

            top_i = (
                i + segments
            )

            top_next = (
                nxt + segments
            )

            faces.append(
                [
                    bottom_i,
                    bottom_next,
                    top_next,
                ]
            )

            faces.append(
                [
                    bottom_i,
                    top_next,
                    top_i,
                ]
            )

            faces.append(
                [
                    bottom_center,
                    bottom_next,
                    bottom_i,
                ]
            )

            faces.append(
                [
                    top_center,
                    top_i,
                    top_next,
                ]
            )

        return (
            np.array(
                vertices,
                dtype=float,
            ),
            np.array(
                faces,
                dtype=int,
            ),
        )

    @staticmethod
    def _combine_meshes(
        meshes,
    ):

        vertices_all = []
        faces_all = []

        offset = 0

        for (
            vertices,
            faces,
        ) in meshes:

            vertices_all.append(
                vertices
            )

            faces_all.append(
                faces + offset
            )

            offset += len(
                vertices
            )

        return (
            np.vstack(
                vertices_all
            ),
            np.vstack(
                faces_all
            ),
        )

    def _create_mesh(
        self,
        vertices,
        faces,
        color,
    ):

        item = gl.GLMeshItem(
            vertexes=vertices,
            faces=faces,
            smooth=False,
            color=color,
            shader="shaded",
            drawEdges=False,
        )

        self.view.addItem(
            item
        )

        return item

    # =========================================================
    # DRONE MODEL
    # =========================================================

    def _build_drone(self):

        arm_length = 1.90

        self.motor_centers = np.array(
            [
                [ arm_length,  arm_length, 0.04],
                [ arm_length, -arm_length, 0.04],
                [-arm_length,  arm_length, 0.04],
                [-arm_length, -arm_length, 0.04],
            ],
            dtype=float,
        )

        # =====================================================
        # FRAME
        # =====================================================

        frame_parts = [
            self._box_mesh(
                center=(
                    0.0,
                    0.0,
                    0.02,
                ),
                size=(
                    1.20,
                    1.20,
                    0.10,
                ),
            )
        ]

        for center in self.motor_centers:

            direction = center.copy()

            direction[2] = 0.0

            direction /= np.linalg.norm(
                direction
            )

            start = (
                direction * 0.40
            )

            start[2] = 0.02

            end = center.copy()

            end[2] = 0.02

            frame_parts.append(
                self._arm_mesh(
                    start,
                    end,
                    width=0.14,
                    height=0.055,
                )
            )

        (
            self.frame_vertices,
            self.frame_faces,
        ) = self._combine_meshes(
            frame_parts
        )

        self.frame_item = self._create_mesh(
            self.frame_vertices,
            self.frame_faces,
            color=(
                0.47,
                0.56,
                0.30,
                1.0,
            ),
        )

        # =====================================================
        # CENTER PCB / ELECTRONICS
        # =====================================================

        electronics_parts = [
            self._box_mesh(
                center=(
                    0.0,
                    0.0,
                    0.24,
                ),
                size=(
                    1.30,
                    1.08,
                    0.15,
                ),
            ),

            self._box_mesh(
                center=(
                    0.14,
                    0.03,
                    0.36,
                ),
                size=(
                    0.34,
                    0.34,
                    0.07,
                ),
            ),
        ]

        (
            self.electronics_vertices,
            self.electronics_faces,
        ) = self._combine_meshes(
            electronics_parts
        )

        self.electronics_item = self._create_mesh(
            self.electronics_vertices,
            self.electronics_faces,
            color=(
                0.03,
                0.20,
                0.15,
                1.0,
            ),
        )

        # =====================================================
        # MOTORS
        # =====================================================

        motor_parts = []
        shaft_parts = []

        for center in self.motor_centers:

            motor_center = center.copy()

            motor_center[2] = 0.14

            motor_parts.append(
                self._cylinder_mesh(
                    motor_center,
                    radius=0.20,
                    height=0.24,
                    segments=16,
                )
            )

            shaft_center = center.copy()

            shaft_center[2] = 0.34

            shaft_parts.append(
                self._cylinder_mesh(
                    shaft_center,
                    radius=0.055,
                    height=0.19,
                    segments=12,
                )
            )

        (
            self.motor_vertices,
            self.motor_faces,
        ) = self._combine_meshes(
            motor_parts
        )

        self.motor_item = self._create_mesh(
            self.motor_vertices,
            self.motor_faces,
            color=(
                0.08,
                0.09,
                0.09,
                1.0,
            ),
        )

        (
            self.shaft_vertices,
            self.shaft_faces,
        ) = self._combine_meshes(
            shaft_parts
        )

        self.shaft_item = self._create_mesh(
            self.shaft_vertices,
            self.shaft_faces,
            color=(
                0.72,
                0.75,
                0.74,
                1.0,
            ),
        )

        # =====================================================
        # PROPELLERS
        # =====================================================

        self.prop_radius = 0.66

        self.propeller_items = []
        self.prop_blur_items = []
        self.hub_items = []

        ring_angles = np.linspace(
            0.0,
            2.0 * np.pi,
            32,
        )

        self.prop_ring_local = np.column_stack(
            (
                self.prop_radius
                * np.cos(
                    ring_angles
                ),

                self.prop_radius
                * np.sin(
                    ring_angles
                ),

                np.zeros_like(
                    ring_angles
                ),
            )
        )

        for center in self.motor_centers:

            prop = gl.GLLinePlotItem(
                pos=np.zeros(
                    (2, 3)
                ),
                color=(
                    1.0,
                    0.12,
                    0.08,
                    0.86,
                ),
                width=4,
                antialias=False,
            )

            self.view.addItem(
                prop
            )

            self.propeller_items.append(
                prop
            )

            blur = gl.GLLinePlotItem(
                pos=np.zeros(
                    (32, 3)
                ),
                color=(
                    1.0,
                    0.18,
                    0.12,
                    0.14,
                ),
                width=2,
                antialias=False,
            )

            self.view.addItem(
                blur
            )

            self.prop_blur_items.append(
                blur
            )

            hub_position = center.copy()

            hub_position[2] = 0.47

            hub = gl.GLScatterPlotItem(
                pos=np.array(
                    [hub_position]
                ),
                size=7,
                color=(
                    0.92,
                    0.94,
                    0.92,
                    1.0,
                ),
                pxMode=True,
            )

            self.view.addItem(
                hub
            )

            self.hub_items.append(
                hub
            )

        # =====================================================
        # FRONT DIRECTION MARKER
        # =====================================================

        self.nose_original = np.array(
            [
                [0.15, 0.0, 0.43],
                [1.20, 0.0, 0.43],
            ],
            dtype=float,
        )

        self.nose_item = gl.GLLinePlotItem(
            pos=self.nose_original,
            color=(
                0.25,
                1.0,
                0.55,
                0.82,
            ),
            width=4,
            antialias=False,
        )

        self.view.addItem(
            self.nose_item
        )

        # =====================================================
        # FRONT NAVIGATION LED
        # =====================================================

        self.front_led_original = np.array(
            [
                [0.68, 0.0, 0.43]
            ],
            dtype=float,
        )

        self.front_led_item = gl.GLScatterPlotItem(
            pos=self.front_led_original,
            size=11,
            color=(
                0.18,
                1.0,
                0.42,
                1.0,
            ),
            pxMode=True,
        )

        self.view.addItem(
            self.front_led_item
        )

    # =========================================================
    # ATTITUDE MATH
    # =========================================================

    @staticmethod
    def _wrap(
        angle,
    ):

        return (
            angle + 180.0
        ) % 360.0 - 180.0

    def _rotation_matrix(
        self,
        roll,
        pitch,
        yaw,
    ):

        r = np.radians(
            roll
        )

        p = np.radians(
            pitch
        )

        y = np.radians(
            yaw
        )

        rx = np.array(
            [
                [1, 0, 0],

                [
                    0,
                    np.cos(r),
                    -np.sin(r),
                ],

                [
                    0,
                    np.sin(r),
                    np.cos(r),
                ],
            ]
        )

        # Preserve previously tested pitch convention
        ry = np.array(
            [
                [
                    np.cos(p),
                    0,
                    -np.sin(p),
                ],

                [0, 1, 0],

                [
                    np.sin(p),
                    0,
                    np.cos(p),
                ],
            ]
        )

        rz = np.array(
            [
                [
                    np.cos(y),
                    -np.sin(y),
                    0,
                ],

                [
                    np.sin(y),
                    np.cos(y),
                    0,
                ],

                [0, 0, 1],
            ]
        )

        return (
            rz
            @ ry
            @ rx
        )

    # =========================================================
    # NEW STM32 ATTITUDE
    # =========================================================

    def set_attitude(
        self,
        roll,
        pitch,
        yaw,
    ):

        # STM32 has already applied the master zero reference.

        self.target_roll = self._wrap(
            roll
        )

        self.target_pitch = self._wrap(
            pitch
        )

        if self.yaw_enabled:

            self.target_yaw = self._wrap(
                yaw
            )

        else:

            self.target_yaw = 0.0

    # =========================================================
    # ANIMATION
    # =========================================================

    def animate(self):

        roll_error = self._wrap(
            self.target_roll
            - self.display_roll
        )

        pitch_error = self._wrap(
            self.target_pitch
            - self.display_pitch
        )

        yaw_error = self._wrap(
            self.target_yaw
            - self.display_yaw
        )

        self.display_roll += (
            self.smoothing
            * roll_error
        )

        self.display_pitch += (
            self.smoothing
            * pitch_error
        )

        self.display_yaw += (
            self.smoothing
            * yaw_error
        )

        self.prop_angle = (
            self.prop_angle
            + self.prop_speed
        ) % 360.0

        rotation = (
            self._rotation_matrix(
                self.display_roll,
                self.display_pitch,
                self.display_yaw,
            )
        )

        self._apply_rotation(
            rotation
        )

    # =========================================================
    # APPLY DRONE ROTATION
    # =========================================================

    def _apply_rotation(
        self,
        rotation,
    ):

        # -----------------------------------------------------
        # Main frame
        # -----------------------------------------------------

        self.frame_item.setMeshData(
            vertexes=(
                self.frame_vertices
                @ rotation.T
            ),
            faces=self.frame_faces,
        )

        # -----------------------------------------------------
        # PCB
        # -----------------------------------------------------

        self.electronics_item.setMeshData(
            vertexes=(
                self.electronics_vertices
                @ rotation.T
            ),
            faces=self.electronics_faces,
        )

        # -----------------------------------------------------
        # Motors
        # -----------------------------------------------------

        self.motor_item.setMeshData(
            vertexes=(
                self.motor_vertices
                @ rotation.T
            ),
            faces=self.motor_faces,
        )

        # -----------------------------------------------------
        # Shafts
        # -----------------------------------------------------

        self.shaft_item.setMeshData(
            vertexes=(
                self.shaft_vertices
                @ rotation.T
            ),
            faces=self.shaft_faces,
        )

        # -----------------------------------------------------
        # Front marker
        # -----------------------------------------------------

        self.nose_item.setData(
            pos=(
                self.nose_original
                @ rotation.T
            )
        )

        # -----------------------------------------------------
        # Navigation LED
        # -----------------------------------------------------

        self.front_led_item.setData(
            pos=(
                self.front_led_original
                @ rotation.T
            )
        )

        # -----------------------------------------------------
        # Propellers
        # -----------------------------------------------------

        for (
            index,
            center,
        ) in enumerate(
            self.motor_centers
        ):

            direction = (
                1.0
                if index in (0, 3)
                else -1.0
            )

            angle = np.radians(
                direction
                * self.prop_angle
            )

            blade = np.array(
                [
                    [
                        center[0]
                        - self.prop_radius
                        * np.cos(angle),

                        center[1]
                        - self.prop_radius
                        * np.sin(angle),

                        0.47,
                    ],

                    [
                        center[0]
                        + self.prop_radius
                        * np.cos(angle),

                        center[1]
                        + self.prop_radius
                        * np.sin(angle),

                        0.47,
                    ],
                ]
            )

            self.propeller_items[
                index
            ].setData(
                pos=(
                    blade
                    @ rotation.T
                )
            )

            # Blur ring
            ring = (
                self.prop_ring_local
                .copy()
            )

            ring[:, 0] += center[0]
            ring[:, 1] += center[1]
            ring[:, 2] += 0.47

            self.prop_blur_items[
                index
            ].setData(
                pos=(
                    ring
                    @ rotation.T
                )
            )

            hub = np.array(
                [
                    [
                        center[0],
                        center[1],
                        0.47,
                    ]
                ]
            )

            self.hub_items[
                index
            ].setData(
                pos=(
                    hub
                    @ rotation.T
                )
            )