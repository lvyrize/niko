import json, struct, sys, os, math


def qrot(q, v):
    x, y, z, w = q
    vx, vy, vz = v
    tx = 2 * (y * vz - z * vy); ty = 2 * (z * vx - x * vz); tz = 2 * (x * vy - y * vx)
    return (vx + w * tx + (y * tz - z * ty), vy + w * ty + (z * tx - x * tz), vz + w * tz + (x * ty - y * tx))


def load(path):
    g = json.load(open(path))
    blob = open(os.path.join(os.path.dirname(path), g["buffers"][0]["uri"]), "rb").read()

    def acc(i):
        a = g["accessors"][i]; bv = g["bufferViews"][a["bufferView"]]
        n = {"SCALAR": 1, "VEC2": 2, "VEC3": 3}[a["type"]] * a["count"]
        fmt = {5126: "f", 5125: "I"}[a["componentType"]]
        return list(struct.unpack_from("<%d%s" % (n, fmt), blob, bv["byteOffset"]))
    return g, acc


def world_points(g, acc, node):
    m = g["meshes"][node["mesh"]]
    t, q, s = node["translation"], node["rotation"], node["scale"]
    pts = []
    for p in m["primitives"]:
        pos = acc(p["attributes"]["POSITION"])
        for i in range(0, len(pos), 3):
            v = (pos[i] * s[0], pos[i + 1] * s[1], pos[i + 2] * s[2])
            v = qrot(q, v)
            pts.append((v[0] + t[0], v[1] + t[1], v[2] + t[2]))
    return pts


if __name__ == "__main__":
    g, acc = load(sys.argv[1])
    for n in g["nodes"]:
        pts = world_points(g, acc, n)
        mn = [min(p[i] for p in pts) for i in range(3)]
        mx = [max(p[i] for p in pts) for i in range(3)]
        print(f"{n['name']:14s} x[{mn[0]:7.1f},{mx[0]:7.1f}] y[{mn[1]:7.1f},{mx[1]:7.1f}] z[{mn[2]:7.1f},{mx[2]:7.1f}] verts {len(pts)}")
    if len(sys.argv) > 2:
        node = next(n for n in g["nodes"] if n["name"] == sys.argv[2])
        pts = world_points(g, acc, node)
        lo = min(p[1] for p in pts); hi = max(p[1] for p in pts)
        steps = 16
        for k in range(steps):
            a = lo + (hi - lo) * k / steps; b = lo + (hi - lo) * (k + 1) / steps
            band = [p for p in pts if a <= p[1] < b]
            if band:
                print(f"  y {a:6.1f}..{b:6.1f}  x[{min(p[0] for p in band):6.1f},{max(p[0] for p in band):6.1f}]  z[{min(p[2] for p in band):6.1f},{max(p[2] for p in band):6.1f}]  n={len(band)}")
