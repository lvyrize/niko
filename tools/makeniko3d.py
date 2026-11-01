import re, sys

src, dst = sys.argv[1], sys.argv[2]
s = open(src).read()

FEET = 83.2
NECK_Y = 26.0

blocks = {}
for m in re.finditer(r"\n        Model \{\n            id: (\w+)\n.*?\n        \}", s, re.S):
    blocks[m.group(1)] = m.group(0)
resources = s[s.index("    // Resources"):s.index("    // Nodes:")]

weights = {
    "waveA": "root.wave * (1 - root.waveMix)",
    "waveB": "root.wave * root.waveMix",
    "kickL": "Math.max(0, root.kick)",
    "kickR": "Math.max(0, -root.kick)",
    "sit": "root.sit",
}
def bind_weight(m):
    name = m.group(2)
    return m.group(1) + "\n        weight: " + weights.get(name, "0")
resources = re.sub(r'(        objectName: "(\w+)")(?=\n        attributes: MorphTarget)', bind_weight, resources)

def glow(m):
    return "emissiveFactor: Qt.vector3d(%s * root.bulbGlow, %s * root.bulbGlow, %s * root.bulbGlow)" % m.groups()
resources = re.sub(r"emissiveFactor: Qt\.vector3d\(([\d.e-]+), ([\d.e-]+), ([\d.e-]+)\)", glow, resources)

EMISSIVE = {"Material.011": (1, 0.515, 0.045), "Material.007": (1, 1, 1), "Material.008": (1, 0.376, 0)}
for name, (r, g, b) in EMISSIVE.items():
    resources = resources.replace('objectName: "%s"' % name,
        'objectName: "%s"\n        emissiveFactor: Qt.vector3d(%s * root.bulbGlow, %s * root.bulbGlow, %s * root.bulbGlow)' % (name, r, g, b), 1)

resources = resources.replace(
    "baseColorMap: nikoFace_DefaultMaterial_Diffuse_png_texture",
    "baseColorMap: faceTexture")
resources = re.sub(r"    Texture \{\n        id: nikoFace_DefaultMaterial_Diffuse_png_texture\n.*?\n    \}\n", "", resources, flags=re.S)
resources += """    Texture {
        id: faceTexture
        generateMipmaps: true
        mipFilter: Texture.Linear
        source: "maps/face_" + root.shownFace + ".png"
    }

"""

def indent(block, n):
    return "\n".join((" " * n + line[8:]) if line.startswith("        ") else line for line in block.strip("\n").split("\n"))

head_parts = ["face", "hairWhiskers", "hat"]
body_parts = [k for k in blocks if k not in head_parts and k != "bulb"]

out = """import QtQuick
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

""" + resources + """
    Node {
        id: body
        y: %(feet)s + root.bob - root.sit * 47
        scale.y: 1 + root.bob * 0.006

""" % {"feet": FEET}
for k in body_parts:
    out += indent(blocks[k], 8) + "\n"
out += indent(blocks["bulb"], 8).replace("            id: bulb", "            id: bulb\n            z: 7", 1) + "\n"
out += """
        Node {
            id: head
            y: %(neck)s
            eulerRotation: Qt.vector3d(root.sleepy * 14, root.headTurn, root.headTilt + root.headSway)
            Node {
                y: -%(neck)s
""" % {"neck": NECK_Y}
for k in head_parts:
    out += indent(blocks[k], 16) + "\n"
out += """            }
        }
    }
}
"""
open(dst, "w").write(out)
print("body:", body_parts, "head:", head_parts)
