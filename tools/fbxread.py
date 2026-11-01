import struct, zlib, sys


class Node:
    __slots__ = ("name", "props", "children")

    def __init__(self, name, props, children):
        self.name, self.props, self.children = name, props, children

    def find(self, name):
        for c in self.children:
            if c.name == name:
                return c
        return None

    def findall(self, name):
        return [c for c in self.children if c.name == name]


def _read_prop(data, o):
    t = chr(data[o]); o += 1
    if t == 'Y': return struct.unpack_from('<h', data, o)[0], o + 2
    if t == 'C': return bool(data[o]), o + 1
    if t == 'I': return struct.unpack_from('<i', data, o)[0], o + 4
    if t == 'F': return struct.unpack_from('<f', data, o)[0], o + 4
    if t == 'D': return struct.unpack_from('<d', data, o)[0], o + 8
    if t == 'L': return struct.unpack_from('<q', data, o)[0], o + 8
    if t in 'SR':
        n = struct.unpack_from('<I', data, o)[0]; o += 4
        raw = bytes(data[o:o + n]); o += n
        return (raw.decode('utf-8', 'replace') if t == 'S' else raw), o
    if t in 'fdlib':
        count, enc, clen = struct.unpack_from('<III', data, o); o += 12
        raw = bytes(data[o:o + clen]); o += clen
        if enc == 1:
            raw = zlib.decompress(raw)
        fmt = {'f': 'f', 'd': 'd', 'l': 'q', 'i': 'i', 'b': 'B'}[t]
        return list(struct.unpack('<%d%s' % (count, fmt), raw)), o
    raise ValueError("unknown property type %r at %d" % (t, o - 1))


def _read_node(data, o, wide):
    if wide:
        end, nprops, plen = struct.unpack_from('<QQQ', data, o); o += 24
    else:
        end, nprops, plen = struct.unpack_from('<III', data, o); o += 12
    nlen = data[o]; o += 1
    if end == 0:
        return None, o
    name = bytes(data[o:o + nlen]).decode('ascii', 'replace'); o += nlen
    props = []
    for _ in range(nprops):
        v, o = _read_prop(data, o)
        props.append(v)
    children = []
    sentinel = 25 if wide else 13
    while o < end:
        if end - o == sentinel:
            o = end
            break
        child, o = _read_node(data, o, wide)
        if child is None:
            break
        children.append(child)
    return Node(name, props, children), end


def load(path):
    data = memoryview(open(path, 'rb').read())
    if bytes(data[:20]) != b'Kaydara FBX Binary  ':
        raise ValueError("not a binary FBX")
    version = struct.unpack_from('<I', data, 23)[0]
    wide = version >= 7500
    o, top = 27, []
    while o < len(data) - 200:
        node, o2 = _read_node(data, o, wide)
        if node is None:
            break
        top.append(node)
        o = o2
    return version, Node("root", [], top)


if __name__ == "__main__":
    version, root = load(sys.argv[1])
    print("FBX version", version)
    objs = root.find("Objects")
    counts = {}
    for c in objs.children:
        key = c.name + (":" + str(c.props[2]) if len(c.props) > 2 else "")
        counts[key] = counts.get(key, 0) + 1
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")
    for g in objs.findall("Geometry"):
        v = g.find("Vertices"); p = g.find("PolygonVertexIndex")
        layers = [c.name for c in g.children if c.name.startswith("Layer")]
        print("Geometry", g.props[1].split(b'\x00')[0] if isinstance(g.props[1], bytes) else g.props[1],
              "verts", len(v.props[0]) // 3 if v else 0, "idx", len(p.props[0]) if p else 0, layers)
    for m in objs.findall("Model"):
        print("Model", m.props[1], m.props[2])
    for m in objs.findall("Material"):
        print("Material", m.props[1])
    for t in objs.findall("Texture"):
        fn = t.find("RelativeFilename") or t.find("FileName")
        print("Texture", t.props[1], fn.props[0] if fn else "")
