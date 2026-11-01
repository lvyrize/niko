import json, struct, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gltfparts import load, qrot

SHOULDER_Y = 16.0
SHOULDER_X = 16.0
HIP_Y = -27.0


def norm(v):
    l = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / l for c in v)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def rodrigues(v, axis, ang):
    c, s = math.cos(ang), math.sin(ang)
    kx, ky, kz = axis
    dot = kx * v[0] + ky * v[1] + kz * v[2]
    cr = cross(axis, v)
    return tuple(v[i] * c + cr[i] * s + axis[i] * dot * (1 - c) for i in range(3))


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def arm_rotation(target_dir):
    d = norm(target_dir)
    axis = cross((1, 0, 0), d)
    ang = math.acos(max(-1.0, min(1.0, d[0])))
    return norm(axis), ang


def pose_arm(p, n, side_dirs):
    x, y, z = p
    side = 1 if x >= 0 else -1
    d = side_dirs.get(side)
    if d is None:
        return p, n
    w = smoothstep(SHOULDER_X - 3, SHOULDER_X + 11, abs(x)) * smoothstep(-8.0, -4.0, y)
    if w <= 0:
        return p, n
    lp = (x * side - SHOULDER_X, y - SHOULDER_Y, z)
    ln = (n[0] * side, n[1], n[2])
    axis, ang = arm_rotation(d)
    rp = rodrigues(lp, axis, ang * w)
    rn = rodrigues(ln, axis, ang * w)
    return ((rp[0] + SHOULDER_X) * side, rp[1] + SHOULDER_Y, rp[2]), (rn[0] * side, rn[1], rn[2])


HOLD = (0.34, -0.36, 0.87)
WAVE_A = (0.45, 0.85, 0.28)
WAVE_B = (0.28, 0.9, 0.34)


def kick(p, n, side, deg):
    x, y, z = p
    if (x >= 0) != (side > 0):
        return p, n
    w = smoothstep(HIP_Y + 2, HIP_Y - 10, y)
    ang = math.radians(deg) * w
    lp = (x, y - HIP_Y, z)
    rp = rodrigues(lp, (1, 0, 0), ang)
    rn = rodrigues(n, (1, 0, 0), ang)
    return (rp[0], rp[1] + HIP_Y, rp[2]), rn


SIT_DROP = 47.0
FLOOR_Y = -83.0


def sit_leg(p, n):
    x, y, z = p
    w = smoothstep(HIP_Y + 2, HIP_Y - 8, y)
    ang = math.radians(-86) * w
    rp = rodrigues((x, y - HIP_Y, z), (1, 0, 0), ang)
    rn = rodrigues(n, (1, 0, 0), ang)
    return (rp[0], rp[1] + HIP_Y, rp[2]), rn


def sit_scarf(p, n):
    x, y, z = p
    floor = FLOOR_Y + SIT_DROP
    if y >= floor:
        return p, n
    depth = floor - y
    return (x * 1.15, floor + depth * 0.08, z - depth * 0.55), norm((n[0], n[1] + 1.5, n[2]))


def main(src, out_dir):
    g, acc = load(src)
    out = {"asset": {"version": "2.0", "generator": "posenico.py"}, "scenes": [{"nodes": []}], "scene": 0,
           "nodes": [], "meshes": [], "materials": g["materials"], "accessors": [], "bufferViews": [],
           "buffers": [], "images": g.get("images", []), "textures": g.get("textures", []), "samplers": g.get("samplers", [{}])}
    blob = bytearray()

    def add(values, comps, ctype, target, minmax=False):
        while len(blob) % 4:
            blob.append(0)
        fmt = {5126: "f", 5125: "I"}[ctype]
        data = struct.pack("<%d%s" % (len(values), fmt), *values)
        out["bufferViews"].append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(data), **({"target": target} if target else {})})
        blob.extend(data)
        a = {"bufferView": len(out["bufferViews"]) - 1, "componentType": ctype, "count": len(values) // comps,
             "type": {1: "SCALAR", 2: "VEC2", 3: "VEC3"}[comps]}
        if minmax:
            a["min"] = [min(values[i::comps]) for i in range(comps)]
            a["max"] = [max(values[i::comps]) for i in range(comps)]
        out["accessors"].append(a)
        return len(out["accessors"]) - 1

    names = {"Plane": "coat", "Plane.001": "collar", "Cube": "scarfWrap", "Plane.002": "hat", "Plane.003": "face",
             "Plane.004": "scarfTails", "Plane.005": "legs", "Plane.006": "scarfFringe", "NurbsPath.001": "hairWhiskers",
             "Cylinder": "bulb"}

    for node in g["nodes"]:
        mesh = g["meshes"][node["mesh"]]
        t, q, s = node["translation"], node["rotation"], node["scale"]
        part = names.get(node["name"], node["name"])
        prims = []
        target_names = []
        for prim in mesh["primitives"]:
            pos = acc(prim["attributes"]["POSITION"])
            nor = acc(prim["attributes"]["NORMAL"]) if "NORMAL" in prim["attributes"] else None
            P, N = [], []
            for i in range(0, len(pos), 3):
                v = qrot(q, (pos[i] * s[0], pos[i + 1] * s[1], pos[i + 2] * s[2]))
                P.append((v[0] + t[0], v[1] + t[1], v[2] + t[2]))
                if nor:
                    nn = qrot(q, (nor[i] / s[0], nor[i + 1] / s[1], nor[i + 2] / s[2]))
                    N.append(norm(nn))
                else:
                    N.append((0, 1, 0))

            targets = []
            if part == "coat":
                base = [pose_arm(p, n, {1: HOLD, -1: HOLD}) for p, n in zip(P, N)]
                for wave in (WAVE_A, WAVE_B):
                    posed = [pose_arm(p, n, {1: wave, -1: HOLD}) for p, n in zip(P, N)]
                    targets.append(posed)
                target_names = ["waveA", "waveB"]
                P = [b[0] for b in base]; N = [b[1] for b in base]
            elif part in ("scarfTails", "scarfFringe"):
                def gather(p, n):
                    f = 0.36 + 0.64 * smoothstep(8.0, 24.0, p[1])
                    return (p[0] * f, p[1], p[2] * (0.75 + 0.25 * f)), norm((n[0] * (1 / f), n[1], n[2]))
                g2 = [gather(p, n) for p, n in zip(P, N)]
                P = [x[0] for x in g2]; N = [x[1] for x in g2]
                targets = [[sit_scarf(p, n) for p, n in zip(P, N)]]
                target_names = ["sit"]
            elif part == "legs":
                targets = [[kick(p, n, -1, 28) for p, n in zip(P, N)], [kick(p, n, 1, 28) for p, n in zip(P, N)],
                           [sit_leg(p, n) for p, n in zip(P, N)]]
                target_names = ["kickL", "kickR", "sit"]

            flatP = [c for p in P for c in p]
            flatN = [c for n in N for c in n]
            attrs = {"POSITION": add(flatP, 3, 5126, 34962, True), "NORMAL": add(flatN, 3, 5126, 34962)}
            if "TEXCOORD_0" in prim["attributes"]:
                attrs["TEXCOORD_0"] = add(acc(prim["attributes"]["TEXCOORD_0"]), 2, 5126, 34962)
            newp = {"attributes": attrs, "indices": add(acc(prim["indices"]), 1, 5125, 34963)}
            if "material" in prim:
                newp["material"] = prim["material"]
            if targets:
                tl = []
                for tgt in targets:
                    dp = [c for (tp, _), bp in zip(tgt, P) for c in (tp[0] - bp[0], tp[1] - bp[1], tp[2] - bp[2])]
                    dn = [c for (_, tn), bn in zip(tgt, N) for c in (tn[0] - bn[0], tn[1] - bn[1], tn[2] - bn[2])]
                    tl.append({"POSITION": add(dp, 3, 5126, None, True), "NORMAL": add(dn, 3, 5126, None)})
                newp["targets"] = tl
            prims.append(newp)
        m = {"name": part, "primitives": prims}
        if target_names:
            m["weights"] = [0.0] * len(target_names)
            m["extras"] = {"targetNames": target_names}
        out["meshes"].append(m)
        out["nodes"].append({"name": part, "mesh": len(out["meshes"]) - 1})
        out["scenes"][0]["nodes"].append(len(out["nodes"]) - 1)

    os.makedirs(out_dir, exist_ok=True)
    open(os.path.join(out_dir, "nikoposed.bin"), "wb").write(blob)
    out["buffers"].append({"uri": "nikoposed.bin", "byteLength": len(blob)})
    json.dump(out, open(os.path.join(out_dir, "nikoposed.gltf"), "w"), indent=1)
    print("wrote", len(out["nodes"]), "parts,", len(blob) // 1024, "KiB")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
