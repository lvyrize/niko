import QtQuick
import QtQuick3D

Node {
    id: root

    property real blink: 0
    property real sleepy: 0
    property real headTilt: 0
    property real headTurn: 0
    property real headSway: 0
    property real bob: 0
    property real bulbGlow: 1.0
    property real wave: 0
    property real waveMix: 0
    property real kick: 0
    property real sit: 0
    property string expression: "neutral"

    readonly property string shownFace: {
        const e = root.expression;
        if (root.blink <= 0.5) return e;
        if (e === "happy" || e === "laugh" || e === "asleep") return e;
        return (e === "sad" || e === "worried" || e === "sleepy") ? "asleep" : "blink";
    }

    MorphTarget {
        id: sit_morphtarget
        objectName: "sit"
        weight: root.sit
        attributes: MorphTarget.Position | MorphTarget.Normal
    }
    MorphTarget {
        id: sit_morphtarget25
        objectName: "sit"
        weight: root.sit
        attributes: MorphTarget.Position | MorphTarget.Normal
    }
    PrincipledMaterial {
        id: material_005_material
        objectName: "Material.005"
        baseColor: "#ff322f55"
        roughness: 0.699999988079071
        alphaMode: PrincipledMaterial.Opaque
    }
    MorphTarget {
        id: kickL_morphtarget
        objectName: "kickL"
        weight: Math.max(0, root.kick)
        attributes: MorphTarget.Position | MorphTarget.Normal
    }
    MorphTarget {
        id: kickR_morphtarget
        objectName: "kickR"
        weight: Math.max(0, -root.kick)
        attributes: MorphTarget.Position | MorphTarget.Normal
    }
    MorphTarget {
        id: sit_morphtarget31
        objectName: "sit"
        weight: root.sit
        attributes: MorphTarget.Position | MorphTarget.Normal
    }
    PrincipledMaterial {
        id: material_006_material
        objectName: "Material.006"
        baseColor: "#ff4b4b96"
        roughness: 0.699999988079071
        alphaMode: PrincipledMaterial.Opaque
    }
    PrincipledMaterial {
        id: material_009_material
        objectName: "Material.009"
        baseColor: "#ffe79cc8"
        roughness: 0.699999988079071
        alphaMode: PrincipledMaterial.Opaque
    }
    PrincipledMaterial {
        id: material_007_material
        objectName: "Material.007"
        emissiveFactor: Qt.vector3d(1 * root.bulbGlow, 1 * root.bulbGlow, 1 * root.bulbGlow)
        roughness: 0.699999988079071
        alphaMode: PrincipledMaterial.Opaque
    }
    PrincipledMaterial {
        id: material_008_material
        objectName: "Material.008"
        emissiveFactor: Qt.vector3d(1 * root.bulbGlow, 0.376 * root.bulbGlow, 0 * root.bulbGlow)
        baseColor: "#ffff7000"
        roughness: 0.699999988079071
        alphaMode: PrincipledMaterial.Opaque
    }
    PrincipledMaterial {
        id: material_011_material
        objectName: "Material.011"
        emissiveFactor: Qt.vector3d(1 * root.bulbGlow, 0.515 * root.bulbGlow, 0.045 * root.bulbGlow)
        baseColor: "#80fffa28"
        roughness: 0.699999988079071
        alphaMode: PrincipledMaterial.Blend
        opacity: 0.5
    }
    PrincipledMaterial {
        id: material_material
        objectName: "Material"
        baseColor: "#ff813d3f"
        roughness: 0.699999988079071
        alphaMode: PrincipledMaterial.Opaque
    }
    PrincipledMaterial {
        id: face_material
        objectName: "Face"
        baseColorMap: faceTexture
        roughness: 0.699999988079071
        alphaMode: PrincipledMaterial.Opaque
    }
    PrincipledMaterial {
        id: material_002_material
        objectName: "Material.002"
        baseColor: "#ffd67272"
        roughness: 0.699999988079071
        alphaMode: PrincipledMaterial.Opaque
    }
    PrincipledMaterial {
        id: material_004_material
        objectName: "Material.004"
        baseColor: "#ff4957d2"
        roughness: 0.699999988079071
        alphaMode: PrincipledMaterial.Opaque
    }
    PrincipledMaterial {
        id: material_001_material
        objectName: "Material.001"
        baseColor: "#ff9e424c"
        roughness: 0.699999988079071
        alphaMode: PrincipledMaterial.Opaque
    }
    MorphTarget {
        id: waveB_morphtarget
        objectName: "waveB"
        weight: root.wave * root.waveMix
        attributes: MorphTarget.Position | MorphTarget.Normal
    }
    MorphTarget {
        id: waveA_morphtarget
        objectName: "waveA"
        weight: root.wave * (1 - root.waveMix)
        attributes: MorphTarget.Position | MorphTarget.Normal
    }
    MorphTarget {
        id: waveB_morphtarget7
        objectName: "waveB"
        weight: root.wave * root.waveMix
        attributes: MorphTarget.Position | MorphTarget.Normal
    }
    MorphTarget {
        id: waveA_morphtarget6
        objectName: "waveA"
        weight: root.wave * (1 - root.waveMix)
        attributes: MorphTarget.Position | MorphTarget.Normal
    }
    PrincipledMaterial {
        id: material_003_material
        objectName: "Material.003"
        baseColor: "#ff5a3333"
        roughness: 0.699999988079071
        alphaMode: PrincipledMaterial.Opaque
    }

    Texture {
        id: faceTexture
        generateMipmaps: true
        mipFilter: Texture.Linear
        source: "maps/face_" + root.shownFace + ".png"
    }


    Node {
        id: body
        y: 83.2 + root.bob - root.sit * 47
        scale.y: 1 + root.bob * 0.006

        Model {
            id: coat
            objectName: "coat"
            source: "meshes/coat_mesh.mesh"
            materials: [
                material_material,
                material_003_material
            ]
            morphTargets: [
                waveA_morphtarget6,
                waveB_morphtarget7,
                waveA_morphtarget,
                waveB_morphtarget
            ]
        }
        Model {
            id: collar
            objectName: "collar"
            source: "meshes/collar_mesh.mesh"
            materials: [
                material_001_material
            ]
        }
        Model {
            id: scarfWrap
            objectName: "scarfWrap"
            source: "meshes/scarfWrap_mesh.mesh"
            materials: [
                material_004_material
            ]
        }
        Model {
            id: scarfTails
            objectName: "scarfTails"
            source: "meshes/scarfTails_mesh.mesh"
            materials: [
                material_004_material
            ]
            morphTargets: [
                sit_morphtarget25
            ]
        }
        Model {
            id: legs
            objectName: "legs"
            source: "meshes/legs_mesh.mesh"
            materials: [
                material_005_material
            ]
            morphTargets: [
                kickL_morphtarget,
                kickR_morphtarget,
                sit_morphtarget31
            ]
        }
        Model {
            id: scarfFringe
            objectName: "scarfFringe"
            source: "meshes/scarfFringe_mesh.mesh"
            materials: [
                material_004_material
            ]
            morphTargets: [
                sit_morphtarget
            ]
        }
        Model {
            id: bulb
            z: 7
            objectName: "bulb"
            source: "meshes/bulb_mesh.mesh"
            materials: [
                material_009_material,
                material_007_material,
                material_008_material,
                material_011_material
            ]
        }

        Node {
            id: head
            y: 26.0
            eulerRotation: Qt.vector3d(root.sleepy * 14, root.headTurn, root.headTilt + root.headSway)
            Node {
                y: -26.0
                Model {
                    id: face
                    objectName: "face"
                    source: "meshes/face_mesh.mesh"
                    materials: [
                        face_material
                    ]
                }
                Model {
                    id: hairWhiskers
                    objectName: "hairWhiskers"
                    source: "meshes/hairWhiskers_mesh.mesh"
                    materials: [
                        material_006_material
                    ]
                }
                Model {
                    id: hat
                    objectName: "hat"
                    source: "meshes/hat_mesh.mesh"
                    materials: [
                        material_material,
                        material_002_material
                    ]
                }
            }
        }
    }
}
