"""讀 KiCad 官方封裝（.kicad_mod），轉成本專案座標。

KiCad 封裝座標：x 向右、y 向下。本專案：x 向右、y 向上（+Y = 機頭）。
所以讀進來先把 y 取負號，再依元件的旋轉角（逆時針，度）旋轉、平移到板上位置。
"""
import math, os, re

LIB = os.environ.get('KICAD_FP', '/home/claude/kfp')


def _tokens(s):
    return re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', s)


def _parse(tokens):
    stack, cur = [], []
    for t in tokens:
        if t == '(':
            stack.append(cur); cur = []
        elif t == ')':
            done = cur; cur = stack.pop(); cur.append(done)
        else:
            cur.append(t.strip('"'))
    return cur[0]


def _find(node, key):
    return [n for n in node if isinstance(n, list) and n and n[0] == key]


class Pad:
    def __init__(self, name, kind, shape, x, y, w, h, rot, drill=None, layers=()):
        self.name, self.kind, self.shape = name, kind, shape     # kind: smd / tht / npth
        self.x, self.y, self.w, self.h, self.rot = x, y, w, h, rot  # rot：焊墊自身旋轉（本專案座標，逆時針）
        self.drill = drill            # (dw, dh)，圓孔 dw == dh
        self.layers = layers
        self.net = None
        self.ref = None

    def __repr__(self):
        return f'<Pad {self.ref}.{self.name} {self.kind} ({self.x:.3f},{self.y:.3f}) {self.w}x{self.h}@{self.rot} {self.net}>'


class Footprint:
    def __init__(self, name):
        path = os.path.join(LIB, name + '.kicad_mod')
        tree = _parse(_tokens(open(path, encoding='utf-8').read()))
        self.name = name
        self.pads = []
        for p in _find(tree, 'pad'):
            pname, ptype, shape = p[1], p[2], p[3]
            at = _find(p, 'at')[0]
            x, y = float(at[1]), -float(at[2])
            r = float(at[3]) if len(at) > 3 else 0.0
            size = _find(p, 'size')[0]
            w, h = float(size[1]), float(size[2])
            drill = None
            d = _find(p, 'drill')
            if d:
                d = d[0]
                if d[1] == 'oval':
                    drill = (float(d[2]), float(d[3]))
                else:
                    drill = (float(d[1]), float(d[1]))
            layers = tuple(_find(p, 'layers')[0][1:])
            kind = {'smd': 'smd', 'thru_hole': 'tht', 'np_thru_hole': 'npth'}[ptype]
            # KiCad 的焊墊旋轉是順時針為正（因為 y 向下）；翻 y 後變成逆時針為正，角度數值相同
            self.pads.append(Pad(pname, kind, shape, x, y, w, h, r, drill, layers))
        self.courtyard = self._outline(tree, 'F.CrtYd')
        self.fab = self._outline(tree, 'F.Fab')

    @staticmethod
    def _outline(tree, layer):
        segs = []
        for ln in _find(tree, 'fp_line'):
            if _find(ln, 'layer')[0][1] != layer: continue
            s, e = _find(ln, 'start')[0], _find(ln, 'end')[0]
            segs.append(((float(s[1]), -float(s[2])), (float(e[1]), -float(e[2]))))
        return segs


def place(fp, ref, x0, y0, rot, nets):
    """回傳放好的焊墊（本專案座標）。nets: {焊墊名稱: 網路}，沒列的焊墊網路設成 NC_<ref>_<pad>。"""
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    out = []
    for p in fp.pads:
        x = x0 + p.x * c - p.y * s
        y = y0 + p.x * s + p.y * c
        q = Pad(p.name, p.kind, p.shape, x, y, p.w, p.h, (p.rot + rot) % 360, p.drill, p.layers)
        q.ref = ref
        if p.kind == 'npth':
            q.net = None
        else:
            q.net = nets.get(p.name, f'NC_{ref}_{p.name}')
        out.append(q)
    return out


def transform_pts(pts, x0, y0, rot):
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return [(x0 + x * c - y * s, y0 + x * s + y * c) for x, y in pts]
