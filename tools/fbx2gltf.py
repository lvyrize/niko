import sys, os, json, math, struct, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fbxread


def p70(node):
    out = {}
    p = node.find("Properties70")
    if p:
        for c in p.children:
            if c.name == "P":
                out[c.props[0]] = c.props[4:]
    return out


def name_of(node):
    n = node.props[1]
    if isinstance(n, bytes):
        n = n.decode("utf-8", "replace")
    return n.split("\x00")[0]


def quat_from_euler_xyz(rx, ry, rz):
    def axis(ax, deg):
        h = math.radians(deg) / 2
        s, c = math.sin(h), math.cos(h)
        return {"x": (s, 0, 0, c), "y": (0, s, 0, c), "z": (0, 0, s, c)}[ax]

    def mul(a, b):
        ax, ay, az, aw = a; bx, by, bz, bw = b
        return (aw * bx + ax * bw + ay * bz - az * by,
                aw * by - ax * bz + ay * bw + az * bx,
                aw * bz + ax * by - ay * bx + az * bw,
                aw * bw - ax * bx - ay * by - az * bz)
    return mul(axis("z", rz), mul(axis("y", ry), axis("x", rx)))


def quat_mul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz)


def layer_values(geom, layer_name, data_name, index_name, n_poly_verts, poly_vert_ctrl, poly_of_pv):
    le = geom.find(layer_name)
    if not le:
        return None
    mapping = le.find("MappingInformationType").props[0]
    ref = le.find("ReferenceInformationType").props[0]
    data = le.find(data_name).props[0]
    idx = le.find(index_name).props[0] if (le.find(index_name) and ref in ("IndexToDirect", "Index")) else None

    def get(pv):
        if mapping == "ByPolygonVertex":
            i = pv
        elif mapping in ("ByVertice", "ByVertex"):
            i = poly_vert_ctrl[pv]
        elif mapping == "ByPolygon":
            i = poly_of_pv[pv]
        else:
            i = 0
        return idx[i] if idx is not None else i
    return get, data


def convert(fbx_path, out_dir):
    version, root = fbxread.load(fbx_path)
    objs = root.find("Objects")
    conns = root.find("Connections")
    by_id = {c.props[0]: c for c in objs.children}

    children_of = {}
    tex_of_mat = {}
    for c in conns.children:
        kind, child, parent = c.props[0], c.props[1], c.props[2]
        children_of.setdefault(parent, []).append(child)
        if kind == "OP" and child in by_id and by_id[child].name == "Texture" and len(c.props) > 3 and "Diffuse" in str(c.props[3]):
            tex_of_mat[parent] = child

    gl = {"asset": {"version": "2.0", "generator": "fbx2gltf.py"}, "scenes": [{"nodes": []}], "scene": 0,
          "nodes": [], "meshes": [], "materials": [], "accessors": [], "bufferViews": [], "buffers": [],
          "images": [], "textures": [], "samplers": [{}]}
    blob = bytearray()
    mat_index = {}
    img_index = {}

    def add_view(data, target):
        while len(blob) % 4:
            blob.append(0)
        off = len(blob)
        blob.extend(data)
        gl["bufferViews"].append({"buffer": 0, "byteOffset": off, "byteLength": len(data), "target": target})
        return len(gl["bufferViews"]) - 1

    def add_accessor(values, comps, ctype, target, minmax=False):
        fmt = {5126: "f", 5125: "I"}[ctype]
        data = struct.pack("<%d%s" % (len(values), fmt), *values)
        acc = {"bufferView": add_view(data, target), "componentType": ctype, "count": len(values) // comps,
               "type": {1: "SCALAR", 2: "VEC2", 3: "VEC3"}[comps]}
        if minmax:
            acc["min"] = [min(values[i::comps]) for i in range(comps)]
            acc["max"] = [max(values[i::comps]) for i in range(comps)]
        gl["accessors"].append(acc)
        return len(gl["accessors"]) - 1

    def material_for(mid):
        if mid in mat_index:
            return mat_index[mid]
        m = by_id[mid]
        props = p70(m)
        col = props.get("DiffuseColor") or props.get("Diffuse") or [0.8, 0.8, 0.8]
        fac = (props.get("DiffuseFactor") or [1.0])[0]
        pbr = {"baseColorFactor": [col[0] * fac, col[1] * fac, col[2] * fac, 1.0], "metallicFactor": 0.0, "roughnessFactor": 0.7}
        em = props.get("EmissiveColor")
        emf = (props.get("EmissiveFactor") or [0.0])[0]
        mat = {"name": name_of(m), "pbrMetallicRoughness": pbr}
        if em and emf > 0 and sum(em) > 0:
            mat["emissiveFactor"] = [min(1, em[0] * emf), min(1, em[1] * emf), min(1, em[2] * emf)]
        op = props.get("Opacity")
        if op and op[0] < 0.999:
            pbr["baseColorFactor"][3] = op[0]
            mat["alphaMode"] = "BLEND"
        tid = tex_of_mat.get(mid)
        if tid:
            t = by_id[tid]
            fn = (t.find("RelativeFilename") or t.find("FileName")).props[0]
            base = os.path.basename(fn.replace("\\", "/"))
            if base not in img_index:
                gl["images"].append({"uri": base})
                gl["textures"].append({"source": len(gl["images"]) - 1, "sampler": 0})
                img_index[base] = len(gl["textures"]) - 1
            pbr["baseColorTexture"] = {"index": img_index[base]}
            pbr["baseColorFactor"] = [1, 1, 1, 1]
        gl["materials"].append(mat)
        mat_index[mid] = len(gl["materials"]) - 1
        return mat_index[mid]

    for model in objs.findall("Model"):
        mid_model = model.props[0]
        kids = children_of.get(mid_model, [])
        geom = next((by_id[k] for k in kids if k in by_id and by_id[k].name == "Geometry"), None)
        mats = [k for k in kids if k in by_id and by_id[k].name == "Material"]
        props = p70(model)
        t = props.get("Lcl Translation", [0, 0, 0])
        r = props.get("Lcl Rotation", [0, 0, 0])
        s = props.get("Lcl Scaling", [1, 1, 1])
        pre = props.get("PreRotation")
        q = quat_from_euler_xyz(*r)
        if pre:
            q = quat_mul(quat_from_euler_xyz(*pre), q)
        node = {"name": name_of(model), "translation": list(t), "rotation": list(q), "scale": list(s)}

        if geom:
            gt = props.get("GeometricTranslation")
            verts = geom.find("Vertices").props[0]
            pvi = geom.find("PolygonVertexIndex").props[0]
            ctrl, poly_of = [], []
            polys, cur, pi = [], [], 0
            for pv, v in enumerate(pvi):
                last = v < 0
                ci = ~v if last else v
                ctrl.append(ci); poly_of.append(pi); cur.append(pv)
                if last:
                    polys.append(cur); cur = []; pi += 1
            nrm = layer_values(geom, "LayerElementNormal", "Normals", "NormalsIndex", len(pvi), ctrl, poly_of)
            uv = layer_values(geom, "LayerElementUV", "UV", "UVIndex", len(pvi), ctrl, poly_of)
            mle = geom.find("LayerElementMaterial")
            mat_data = mle.find("Materials").props[0] if mle else [0]
            mat_map = mle.find("MappingInformationType").props[0] if mle else "AllSame"

            groups = {}
            for p_i, poly in enumerate(polys):
                slot = mat_data[p_i] if mat_map == "ByPolygon" and p_i < len(mat_data) else mat_data[0]
                for k in range(1, len(poly) - 1):
                    groups.setdefault(slot, []).extend((poly[0], poly[k], poly[k + 1]))

            prims = []
            for slot, tri_pvs in groups.items():
                remap, pos, nor, tex, ind = {}, [], [], [], []
                for pv in tri_pvs:
                    ci = ctrl[pv]
                    key = (ci, nrm[0](pv) if nrm else 0, uv[0](pv) if uv else 0)
                    if key not in remap:
                        remap[key] = len(pos) // 3
                        x, y, z = verts[ci * 3:ci * 3 + 3]
                        if gt:
                            x, y, z = x + gt[0], y + gt[1], z + gt[2]
                        pos += [x, y, z]
                        if nrm:
                            ni = nrm[0](pv); nd = nrm[1]
                            nor += nd[ni * 3:ni * 3 + 3]
                        if uv:
                            ui = uv[0](pv); ud = uv[1]
                            tex += [ud[ui * 2], 1.0 - ud[ui * 2 + 1]]
                    ind.append(remap[key])
                attrs = {"POSITION": add_accessor(pos, 3, 5126, 34962, True)}
                if nor:
                    attrs["NORMAL"] = add_accessor(nor, 3, 5126, 34962)
                if tex:
                    attrs["TEXCOORD_0"] = add_accessor(tex, 2, 5126, 34962)
                prim = {"attributes": attrs, "indices": add_accessor(ind, 1, 5125, 34963)}
                if slot < len(mats):
                    prim["material"] = material_for(mats[slot])
                prims.append(prim)
            gl["meshes"].append({"name": name_of(geom), "primitives": prims})
            node["mesh"] = len(gl["meshes"]) - 1

        gl["nodes"].append(node)
    model_ids = [m.props[0] for m in objs.findall("Model")]
    index_of = {mid: i for i, mid in enumerate(model_ids)}
    has_parent = set()
    for c in conns.children:
        if c.props[0] == "OO" and c.props[1] in index_of and c.props[2] in index_of:
            gl["nodes"][index_of[c.props[2]]].setdefault("children", []).append(index_of[c.props[1]])
            has_parent.add(c.props[1])
    gl["scenes"][0]["nodes"] = [index_of[m] for m in model_ids if m not in has_parent]

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "niko.bin"), "wb") as f:
        f.write(blob)
    gl["buffers"].append({"uri": "niko.bin", "byteLength": len(blob)})
    if not gl["images"]:
        del gl["images"], gl["textures"], gl["samplers"]
    with open(os.path.join(out_dir, "niko.gltf"), "w") as f:
        json.dump(gl, f, indent=1)
    for n in gl["nodes"]:
        print(n["name"], "mesh" if "mesh" in n else "", [round(v, 2) for v in n["translation"]], [round(v, 2) for v in n["scale"]])
    for m in gl["materials"]:
        print("mat", m["name"], m["pbrMetallicRoughness"].get("baseColorFactor"), "tex" if "baseColorTexture" in m["pbrMetallicRoughness"] else "", m.get("emissiveFactor", ""))


if __name__ == "__main__":
    convert(sys.argv[1], sys.argv[2])
