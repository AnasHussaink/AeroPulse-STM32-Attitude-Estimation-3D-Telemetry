import QtQuick
import QtQuick3D


Item {
    id: root

    // ========================================================
    // DATA FROM PYTHON
    // ========================================================

    property real rollAngle: 0
    property real pitchAngle: 0
    property real yawAngle: 0

    property real rollCorrection: 0
    property real pitchCorrection: 0

    property real motor1: 50
    property real motor2: 50
    property real motor3: 50
    property real motor4: 50

    property bool pidEnabled: true

    // 0 ISO
    // 1 TOP
    // 2 FRONT
    // 3 CLOSE
    property int cameraMode: 0

    property real propellerSpin: 0


    NumberAnimation on propellerSpin {
        from: 0
        to: 360
        duration: 420
        loops: Animation.Infinite
    }


    // ========================================================
    // BACKGROUND
    // ========================================================

    Rectangle {
        anchors.fill: parent

        gradient: Gradient {

            GradientStop {
                position: 0.0
                color: "#101a17"
            }

            GradientStop {
                position: 0.55
                color: "#070d0b"
            }

            GradientStop {
                position: 1.0
                color: "#020403"
            }
        }
    }


    // ========================================================
    // 3D SCENE
    // ========================================================

    View3D {
        id: view3d

        anchors.fill: parent

        camera: activeCamera


        environment: SceneEnvironment {

            backgroundMode:
                SceneEnvironment.Transparent

            antialiasingMode:
                SceneEnvironment.MSAA

            antialiasingQuality:
                SceneEnvironment.High

            specularAAEnabled: true

            aoEnabled: true
            aoStrength: 28
            aoDistance: 150
            aoSoftness: 35

            tonemapMode:
                SceneEnvironment.TonemapModeFilmic
        }


        // ====================================================
        // CAMERAS
        // ====================================================

        PerspectiveCamera {
            id: isoCamera

            position: Qt.vector3d(
                430,
                310,
                580
            )

            eulerRotation: Qt.vector3d(
                -19,
                36,
                0
            )

            fieldOfView: 42
        }


        PerspectiveCamera {
            id: topCamera

            position: Qt.vector3d(
                0,
                760,
                0
            )

            eulerRotation: Qt.vector3d(
                -90,
                0,
                0
            )

            fieldOfView: 42
        }


        PerspectiveCamera {
            id: frontCamera

            position: Qt.vector3d(
                0,
                115,
                720
            )

            eulerRotation: Qt.vector3d(
                -8,
                0,
                0
            )

            fieldOfView: 42
        }


        PerspectiveCamera {
            id: closeCamera

            position: Qt.vector3d(
                315,
                220,
                410
            )

            eulerRotation: Qt.vector3d(
                -18,
                37,
                0
            )

            fieldOfView: 45
        }


        property Camera activeCamera:
            root.cameraMode === 1
            ? topCamera
            :
            root.cameraMode === 2
            ? frontCamera
            :
            root.cameraMode === 3
            ? closeCamera
            :
            isoCamera


        // ====================================================
        // LIGHTS
        // ====================================================

        DirectionalLight {

            eulerRotation.x: -48
            eulerRotation.y: -32

            brightness: 1.1

            color: "#ffffff"

            ambientColor: "#33483e"

            castsShadow: true

            shadowFactor: 65

            shadowMapFar: 2000

            shadowMapQuality:
                Light.ShadowMapQualityHigh
        }


        PointLight {

            position: Qt.vector3d(
                -250,
                320,
                250
            )

            brightness: 0.45

            color: "#6ce9b4"
        }


        PointLight {

            position: Qt.vector3d(
                300,
                180,
                -220
            )

            brightness: 0.28

            color: "#5ac8fa"
        }


        // ====================================================
        // GROUND
        // ====================================================

        Model {
            source: "#Rectangle"

            position.y: -130

            eulerRotation.x: -90

            scale: Qt.vector3d(
                10,
                10,
                10
            )

            castsShadows: false
            receivesShadows: true

            materials: [

                PrincipledMaterial {

                    baseColor: "#080d0b"

                    roughness: 0.92
                }
            ]
        }


        // ====================================================
        // TEST PLATFORM
        // ====================================================

        Model {
            source: "#Cylinder"

            position.y: -118

            scale: Qt.vector3d(
                4.1,
                0.09,
                4.1
            )

            receivesShadows: true

            materials: [

                PrincipledMaterial {

                    baseColor: "#111b17"

                    metalness: 0.25
                    roughness: 0.58
                }
            ]
        }


        Model {
            source: "#Cylinder"

            position.y: -108

            scale: Qt.vector3d(
                3.65,
                0.018,
                3.65
            )

            castsShadows: false

            materials: [

                PrincipledMaterial {

                    baseColor: "#154d35"

                    emissiveFactor:
                        Qt.vector3d(
                            0.02,
                            0.22,
                            0.09
                        )

                    roughness: 0.50
                }
            ]
        }


        // Platform center lines

        Model {
            source: "#Cube"

            position.y: -101

            scale: Qt.vector3d(
                3.25,
                0.015,
                0.025
            )

            materials: [

                PrincipledMaterial {

                    baseColor: "#40d98f"

                    emissiveFactor:
                        Qt.vector3d(
                            0.02,
                            0.28,
                            0.10
                        )
                }
            ]

            castsShadows: false
        }


        Model {
            source: "#Cube"

            position.y: -101

            scale: Qt.vector3d(
                0.025,
                0.015,
                3.25
            )

            materials: [

                PrincipledMaterial {

                    baseColor: "#40d98f"

                    emissiveFactor:
                        Qt.vector3d(
                            0.02,
                            0.28,
                            0.10
                        )
                }
            ]

            castsShadows: false
        }


        // ====================================================
        // GHOST REFERENCE DRONE
        // ====================================================

        Node {
            id: ghostDrone

            visible: root.pidEnabled

            opacity: 0.13


            Model {
                source: "#Cube"

                scale: Qt.vector3d(
                    1.0,
                    0.055,
                    0.82
                )

                materials: [

                    PrincipledMaterial {
                        baseColor: "#55f0bd"
                    }
                ]

                castsShadows: false
            }


            Model {
                source: "#Cube"

                eulerRotation.y: 45

                scale: Qt.vector3d(
                    2.65,
                    0.025,
                    0.10
                )

                materials: [

                    PrincipledMaterial {
                        baseColor: "#55f0bd"
                    }
                ]

                castsShadows: false
            }


            Model {
                source: "#Cube"

                eulerRotation.y: -45

                scale: Qt.vector3d(
                    2.65,
                    0.025,
                    0.10
                )

                materials: [

                    PrincipledMaterial {
                        baseColor: "#55f0bd"
                    }
                ]

                castsShadows: false
            }
        }


        // ====================================================
        // ACTUAL DRONE
        // ====================================================

        Node {
            id: droneRoot

            // Quick3D:
            // X = side
            // Y = up
            // Z = front

            eulerRotation.x:
                root.pitchAngle

            eulerRotation.y:
                root.yawAngle

            eulerRotation.z:
                root.rollAngle


            // =================================================
            // CENTRAL LOWER FRAME
            // =================================================

            Model {
                source: "#Cube"

                scale: Qt.vector3d(
                    1.12,
                    0.10,
                    0.96
                )

                materials: [

                    PrincipledMaterial {

                        baseColor: "#858c56"

                        roughness: 0.64
                        metalness: 0.04
                    }
                ]
            }


            // =================================================
            // X ARMS
            // =================================================

            Model {
                source: "#Cube"

                eulerRotation.y: 45

                scale: Qt.vector3d(
                    2.72,
                    0.055,
                    0.13
                )

                materials: [

                    PrincipledMaterial {

                        baseColor: "#9ba36a"

                        roughness: 0.65
                    }
                ]
            }


            Model {
                source: "#Cube"

                eulerRotation.y: -45

                scale: Qt.vector3d(
                    2.72,
                    0.055,
                    0.13
                )

                materials: [

                    PrincipledMaterial {

                        baseColor: "#9ba36a"

                        roughness: 0.65
                    }
                ]
            }


            // =================================================
            // PCB
            // =================================================

            Model {
                source: "#Cube"

                position.y: 17

                scale: Qt.vector3d(
                    1.05,
                    0.085,
                    0.84
                )

                materials: [

                    PrincipledMaterial {

                        baseColor: "#0c493b"

                        roughness: 0.42
                        metalness: 0.10
                    }
                ]
            }


            // MCU
            Model {
                source: "#Cube"

                position: Qt.vector3d(
                    9,
                    29,
                    2
                )

                scale: Qt.vector3d(
                    0.31,
                    0.05,
                    0.28
                )

                materials: [

                    PrincipledMaterial {

                        baseColor: "#111514"

                        roughness: 0.30
                        metalness: 0.42
                    }
                ]
            }


            // =================================================
            // FRONT LEFT MOTOR
            // =================================================

            Node {
                id: m1

                position: Qt.vector3d(
                    -160,
                    0,
                    160
                )


                Model {
                    source: "#Cylinder"

                    position.y: 20

                    scale: Qt.vector3d(
                        0.34,
                        0.27,
                        0.34
                    )

                    materials: [

                        PrincipledMaterial {

                            baseColor: "#242928"

                            metalness: 0.72
                            roughness: 0.23
                        }
                    ]
                }


                Model {
                    source: "#Cylinder"

                    position.y: 47

                    scale: Qt.vector3d(
                        0.075,
                        0.19,
                        0.075
                    )

                    materials: [

                        PrincipledMaterial {

                            baseColor: "#c3cbc9"

                            metalness: 0.92
                            roughness: 0.13
                        }
                    ]
                }


                Node {
                    position.y: 59

                    eulerRotation.y:
                        root.propellerSpin


                    Model {
                        source: "#Cube"

                        scale: Qt.vector3d(
                            1.19,
                            0.020,
                            0.10
                        )

                        materials: [

                            PrincipledMaterial {

                                baseColor: "#e9433b"

                                roughness: 0.42
                            }
                        ]
                    }
                }


                Model {
                    source: "#Cylinder"

                    position.y: 58

                    scale: Qt.vector3d(
                        1.25,
                        0.007,
                        1.25
                    )

                    materials: [

                        PrincipledMaterial {

                            baseColor:
                                Qt.rgba(
                                    0.95,
                                    0.12,
                                    0.08,
                                    0.08
                                )

                            alphaMode:
                                PrincipledMaterial.Blend
                        }
                    ]

                    castsShadows: false
                }
            }


            // =================================================
            // FRONT RIGHT MOTOR
            // =================================================

            Node {
                id: m2

                position: Qt.vector3d(
                    160,
                    0,
                    160
                )


                Model {
                    source: "#Cylinder"

                    position.y: 20

                    scale: Qt.vector3d(
                        0.34,
                        0.27,
                        0.34
                    )

                    materials: [

                        PrincipledMaterial {

                            baseColor: "#242928"

                            metalness: 0.72
                            roughness: 0.23
                        }
                    ]
                }


                Model {
                    source: "#Cylinder"

                    position.y: 47

                    scale: Qt.vector3d(
                        0.075,
                        0.19,
                        0.075
                    )

                    materials: [

                        PrincipledMaterial {

                            baseColor: "#c3cbc9"

                            metalness: 0.92
                            roughness: 0.13
                        }
                    ]
                }


                Node {
                    position.y: 59

                    eulerRotation.y:
                        -root.propellerSpin


                    Model {
                        source: "#Cube"

                        scale: Qt.vector3d(
                            1.19,
                            0.020,
                            0.10
                        )

                        materials: [

                            PrincipledMaterial {

                                baseColor: "#e9433b"

                                roughness: 0.42
                            }
                        ]
                    }
                }


                Model {
                    source: "#Cylinder"

                    position.y: 58

                    scale: Qt.vector3d(
                        1.25,
                        0.007,
                        1.25
                    )

                    materials: [

                        PrincipledMaterial {

                            baseColor:
                                Qt.rgba(
                                    0.95,
                                    0.12,
                                    0.08,
                                    0.08
                                )

                            alphaMode:
                                PrincipledMaterial.Blend
                        }
                    ]

                    castsShadows: false
                }
            }


            // =================================================
            // REAR LEFT MOTOR
            // =================================================

            Node {
                id: m3

                position: Qt.vector3d(
                    -160,
                    0,
                    -160
                )


                Model {
                    source: "#Cylinder"

                    position.y: 20

                    scale: Qt.vector3d(
                        0.34,
                        0.27,
                        0.34
                    )

                    materials: [

                        PrincipledMaterial {

                            baseColor: "#242928"

                            metalness: 0.72
                            roughness: 0.23
                        }
                    ]
                }


                Model {
                    source: "#Cylinder"

                    position.y: 47

                    scale: Qt.vector3d(
                        0.075,
                        0.19,
                        0.075
                    )

                    materials: [

                        PrincipledMaterial {

                            baseColor: "#c3cbc9"

                            metalness: 0.92
                            roughness: 0.13
                        }
                    ]
                }


                Node {
                    position.y: 59

                    eulerRotation.y:
                        -root.propellerSpin


                    Model {
                        source: "#Cube"

                        scale: Qt.vector3d(
                            1.19,
                            0.020,
                            0.10
                        )

                        materials: [

                            PrincipledMaterial {

                                baseColor: "#e9433b"

                                roughness: 0.42
                            }
                        ]
                    }
                }


                Model {
                    source: "#Cylinder"

                    position.y: 58

                    scale: Qt.vector3d(
                        1.25,
                        0.007,
                        1.25
                    )

                    materials: [

                        PrincipledMaterial {

                            baseColor:
                                Qt.rgba(
                                    0.95,
                                    0.12,
                                    0.08,
                                    0.08
                                )

                            alphaMode:
                                PrincipledMaterial.Blend
                        }
                    ]

                    castsShadows: false
                }
            }


            // =================================================
            // REAR RIGHT MOTOR
            // =================================================

            Node {
                id: m4

                position: Qt.vector3d(
                    160,
                    0,
                    -160
                )


                Model {
                    source: "#Cylinder"

                    position.y: 20

                    scale: Qt.vector3d(
                        0.34,
                        0.27,
                        0.34
                    )

                    materials: [

                        PrincipledMaterial {

                            baseColor: "#242928"

                            metalness: 0.72
                            roughness: 0.23
                        }
                    ]
                }


                Model {
                    source: "#Cylinder"

                    position.y: 47

                    scale: Qt.vector3d(
                        0.075,
                        0.19,
                        0.075
                    )

                    materials: [

                        PrincipledMaterial {

                            baseColor: "#c3cbc9"

                            metalness: 0.92
                            roughness: 0.13
                        }
                    ]
                }


                Node {
                    position.y: 59

                    eulerRotation.y:
                        root.propellerSpin


                    Model {
                        source: "#Cube"

                        scale: Qt.vector3d(
                            1.19,
                            0.020,
                            0.10
                        )

                        materials: [

                            PrincipledMaterial {

                                baseColor: "#e9433b"

                                roughness: 0.42
                            }
                        ]
                    }
                }


                Model {
                    source: "#Cylinder"

                    position.y: 58

                    scale: Qt.vector3d(
                        1.25,
                        0.007,
                        1.25
                    )

                    materials: [

                        PrincipledMaterial {

                            baseColor:
                                Qt.rgba(
                                    0.95,
                                    0.12,
                                    0.08,
                                    0.08
                                )

                            alphaMode:
                                PrincipledMaterial.Blend
                        }
                    ]

                    castsShadows: false
                }
            }


            // =================================================
            // FRONT NAVIGATION LED
            // =================================================

            Model {
                source: "#Sphere"

                position: Qt.vector3d(
                    0,
                    31,
                    68
                )

                scale: Qt.vector3d(
                    0.10,
                    0.10,
                    0.10
                )

                materials: [

                    PrincipledMaterial {

                        baseColor: "#43ff92"

                        emissiveFactor:
                            Qt.vector3d(
                                0.12,
                                0.85,
                                0.28
                            )

                        roughness: 0.20
                    }
                ]
            }
        }


        // ====================================================
        // MOTOR THRUST
        // ====================================================

        Node {
            id: thrustVisualization

            visible:
                root.pidEnabled


            // M1
            Model {
                source: "#Cylinder"

                position: Qt.vector3d(
                    -160,
                    -58,
                    160
                )

                scale: Qt.vector3d(
                    0.11,
                    0.22
                    +
                    root.motor1
                    / 125,
                    0.11
                )

                materials: [

                    PrincipledMaterial {

                        baseColor:
                            Qt.rgba(
                                0.15,
                                0.78,
                                1.0,
                                0.22
                            )

                        alphaMode:
                            PrincipledMaterial.Blend

                        emissiveFactor:
                            Qt.vector3d(
                                0.01,
                                0.18,
                                0.28
                            )
                    }
                ]

                castsShadows: false
            }


            // M2
            Model {
                source: "#Cylinder"

                position: Qt.vector3d(
                    160,
                    -58,
                    160
                )

                scale: Qt.vector3d(
                    0.11,
                    0.22
                    +
                    root.motor2
                    / 125,
                    0.11
                )

                materials: [

                    PrincipledMaterial {

                        baseColor:
                            Qt.rgba(
                                0.15,
                                0.78,
                                1.0,
                                0.22
                            )

                        alphaMode:
                            PrincipledMaterial.Blend

                        emissiveFactor:
                            Qt.vector3d(
                                0.01,
                                0.18,
                                0.28
                            )
                    }
                ]

                castsShadows: false
            }


            // M3
            Model {
                source: "#Cylinder"

                position: Qt.vector3d(
                    -160,
                    -58,
                    -160
                )

                scale: Qt.vector3d(
                    0.11,
                    0.22
                    +
                    root.motor3
                    / 125,
                    0.11
                )

                materials: [

                    PrincipledMaterial {

                        baseColor:
                            Qt.rgba(
                                0.15,
                                0.78,
                                1.0,
                                0.22
                            )

                        alphaMode:
                            PrincipledMaterial.Blend

                        emissiveFactor:
                            Qt.vector3d(
                                0.01,
                                0.18,
                                0.28
                            )
                    }
                ]

                castsShadows: false
            }


            // M4
            Model {
                source: "#Cylinder"

                position: Qt.vector3d(
                    160,
                    -58,
                    -160
                )

                scale: Qt.vector3d(
                    0.11,
                    0.22
                    +
                    root.motor4
                    / 125,
                    0.11
                )

                materials: [

                    PrincipledMaterial {

                        baseColor:
                            Qt.rgba(
                                0.15,
                                0.78,
                                1.0,
                                0.22
                            )

                        alphaMode:
                            PrincipledMaterial.Blend

                        emissiveFactor:
                            Qt.vector3d(
                                0.01,
                                0.18,
                                0.28
                            )
                    }
                ]

                castsShadows: false
            }
        }
    }


    // ========================================================
    // SMALL HUD
    // ========================================================

    Rectangle {

        anchors.left:
            parent.left

        anchors.top:
            parent.top

        anchors.leftMargin: 14
        anchors.topMargin: 14

        width: 190
        height: 78

        radius: 6

        color: "#b009100d"

        border.color:
            "#365c49"


        Column {

            anchors.centerIn:
                parent

            spacing: 4


            Text {

                text:
                    "ROLL    "
                    +
                    root.rollAngle.toFixed(1)
                    +
                    "°"

                color: "#e7f9ee"

                font.family:
                    "Consolas"

                font.pixelSize: 13
            }


            Text {

                text:
                    "PITCH   "
                    +
                    root.pitchAngle.toFixed(1)
                    +
                    "°"

                color: "#e7f9ee"

                font.family:
                    "Consolas"

                font.pixelSize: 13
            }


            Text {

                text:
                    root.pidEnabled
                    ?
                    "REFERENCE: LEVEL"
                    :
                    "PID VISUAL OFF"

                color:
                    root.pidEnabled
                    ?
                    "#45e39a"
                    :
                    "#84948c"

                font.family:
                    "Consolas"

                font.pixelSize: 11
            }
        }
    }
}