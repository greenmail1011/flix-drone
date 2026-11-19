"""絲印：元件編號、馬達/電池正負極、USB、機頭方向；背面印 Flix 參數設定。
文字轉成多邊形，避開焊墊開窗，超出板子的部分剪掉。"""
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from shapely.geometry import Polygon, LineString, box, Point
from shapely.ops import unary_union
from shapely import affinity
import board as B
from route import pad_geom

FONT = FontProperties(family='DejaVu Sans', weight='bold')
LW = 0.16          # JLC 最小絲印線寬 0.153 mm
H = 0.9            # 一般字高


def text(s, x, y, h=H, anchor='c', angle=0, mirror=False):
    tp = TextPath((0, 0), s, size=1.0, prop=FONT)
    geom = Polygon()
    for ring in tp.to_polygons():
        if len(ring) < 3: continue
        geom = geom.symmetric_difference(Polygon(ring).buffer(0))
    cap = TextPath((0, 0), 'H', size=1.0, prop=FONT).get_extents().height
    k = h / cap
    geom = affinity.scale(geom, k, k, origin=(0, 0))
    minx, miny, maxx, maxy = geom.bounds
    dx = {'c': -(minx + maxx) / 2, 'l': -minx, 'r': -maxx}[anchor]
    geom = affinity.translate(geom, dx, -h / 2)
    if mirror: geom = affinity.scale(geom, -1, 1, origin=(0, 0))
    if angle: geom = affinity.rotate(geom, angle, origin=(0, 0))
    return affinity.translate(geom, x, y)


def line(pts, w=LW):
    return LineString(pts).buffer(w / 2, 8)


def circle(x, y, r, w=LW):
    return Point(x, y).buffer(r + w / 2, 32).difference(Point(x, y).buffer(r - w / 2, 32))


def pad_of(ref, name):
    return [p for p in B.PADS if p.ref == ref and p.name == name][0]


def comp(ref):
    return [c for c in B.COMPS if c['ref'] == ref][0]


class Placer:
    """依序放字：每個字試幾個候選位置，選第一個不壓到焊墊、不和其他字重疊、在板內的。"""
    def __init__(self, keep_out, area):
        self.keep_out = keep_out
        self.area = area
        self.used = []

    def put(self, cands, s, h=H, angle=0, force=False):
        for x, y in cands:
            g = text(s, x, y, h, angle=angle)
            if not g.within(self.area): continue
            if g.intersects(self.keep_out): continue
            if any(g.buffer(0.15).intersects(u) for u in self.used): continue
            self.used.append(g)
            return g
        if force:
            x, y = cands[0]; g = text(s, x, y, h, angle=angle); self.used.append(g); return g
        return None


def mask_openings(R, layer):
    ops = [pad_geom(f.gerber[1]).buffer(0.05) for f in R.feats if f.layer == layer and f.kind in ('smd', 'tht')]
    ops += [Point(x, y).buffer(B.MOUNT_D / 2 + 0.1, 32) for x, y in B.MOUNT_HOLES]
    ops += [Point(x, y).buffer(max(dw, dh) / 2 + 0.1, 32) for x, y, dw, dh, pl, n in R.drills if not pl]
    return unary_union(ops)


def top(R):
    keep = mask_openings(R, 'F').buffer(0.12)
    # 元件本體（字印在本體下面會被蓋住）
    bodies = unary_union([B.COURTS[r] for r in B.COURTS if r[0] in 'UJ'])
    P = Placer(keep, B.BOARD.buffer(-0.25))
    g = []
    # 機頭方向與板名（天線禁區可以印字）
    g.append(Polygon([(0, 19.0), (-1.2, 17.3), (1.2, 17.3)]))
    g.append(text('FRONT', 0, 16.3, 1.0))
    g.append(text(f'FutureZebra x Flix  ONBOARD {B.VERSION}', 0, 14.8, 0.8))
    P.used += g
    # 安裝孔：螺絲頭範圍
    for x, y in B.MOUNT_HOLES: g.append(circle(x, y, 1.45))
    # 馬達插座：板邊直立文字、腳位旁 + / −
    for nm, gpio, s, y, *_ in B.MOTORS:
        n = B.MOTOR_NO[nm]
        ref = f'J{3 + n}'
        d = dict(FL='CW', FR='CCW', RL='CCW', RR='CW')[nm]
        lab = P.put([(s * 22.35, y), (s * 22.35, y + 0.6), (s * 22.35, y - 0.6)], f'M{n} {nm} {d}', 0.8, angle=90 if s < 0 else -90, force=True)
        if lab: g.append(lab)
        p1, p2 = pad_of(ref, '1'), pad_of(ref, '2')
        for p, t in ((p1, '+'), (p2, '-')):
            ox = -s * 1.35
            c = P.put([(p.x + ox, p.y), (p.x + ox * 1.4, p.y), (p.x, p.y + (1.2 if t == '+' else -1.2) * (1 if p1.y > p2.y else -1))], t, 1.0)
            if c: g.append(c)
        q = comp(f'Q{1 + n}')
        c = P.put([(q['x'], q['y'] + 2.3), (q['x'], q['y'] - 2.3), (q['x'] + 2.6 * s, q['y']), (q['x'] - 2.6 * s, q['y'])], f'Q{1 + n}', 0.8)
        if c: g.append(c)
        c = P.put([(q['x'], q['y'] - 2.3), (q['x'], q['y'] + 2.3), (q['x'] - 2.6 * s, q['y'])], f'IO{gpio}', 0.7)
        if c: g.append(c)
    # 電池
    j2 = comp('J2'); p1, p2 = pad_of('J2', '1'), pad_of('J2', '2')
    for p, t in ((p1, '+'), (p2, '-')):
        c = P.put([(p.x + (-1.25 if t == '+' else 1.25), p.y - 2.6), (p.x + (-1.3 if t == '+' else 1.3), p.y)], t, 1.4)
        if c: g.append(c)
    c = P.put([(0, -26 + 0.9), (0, -25.0)], 'BATTERY 1S', 0.8)
    if c: g.append(c)
    # 電池備用焊墊（BT1，不貼片）：通孔旁 + / −
    for nm, t in (('1', '+'), ('2', '-')):
        p = pad_of('BT1', nm)
        c = P.put([(p.x, p.y - 1.75), (p.x, p.y + 1.6), (p.x + (-0.0), p.y - 1.9)], t, 1.2)
        if c: g.append(c)
    # 擴充插座 J7（Qwiic 腳位）：板邊直立文字
    j7 = comp('J7')
    c = P.put([(22.35, j7['y']), (22.35, j7['y'] - 0.6), (22.35, j7['y'] + 0.6)], 'I2C', 0.8, angle=-90, force=True)
    if c: g.append(c)
    # 感測器插座 J8（v2.0.2）：編號、1 號腳記號（GND，靠安裝孔）、TX／RX 標在保護電阻旁
    j8 = comp('J8'); p1 = pad_of('J8', '1')
    c = P.put([(j8['x'] - 1.2, j8['y'] + 4.6), (j8['x'], j8['y'] + 4.6), (j8['x'] - 3.4, j8['y']), (j8['x'] + 3.2, j8['y'] + 4.3)], 'J8', 0.8, force=True)
    if c: g.append(c)
    g.append(Point(p1.x + 0.1, p1.y - 0.78).buffer(0.22))
    for ref, t in (('R19', 'TX'), ('R20', 'RX')):
        r = comp(ref)
        c = P.put([(r['x'] + 1.75, r['y']), (r['x'] + 1.9, r['y'])], t, 0.6)
        if c: g.append(c)
    # USB
    c = P.put([(-21.9, -11.0)], 'USB', 0.8, angle=90, force=True)
    if c: g.append(c)
    # IC 與其他
    for ref, s, h in (('U2', 'IMU', 0.8), ('U3', 'CH340C', 0.8), ('U4', 'U4', 0.7), ('Q5', 'Q5', 0.7), ('Q6', 'Q6', 0.7), ('Q7', 'Q7', 0.7),
                      ('D1', 'D1', 0.7), ('D2', 'LED', 0.7), ('U5', '5V', 0.7)):
        cm = comp(ref); cy = B.COURTS[ref]
        minx, miny, maxx, maxy = cy.bounds
        cands = [((minx + maxx) / 2, maxy + 0.6), ((minx + maxx) / 2, miny - 0.6), (minx - 1.2, (miny + maxy) / 2), (maxx + 1.2, (miny + maxy) / 2)]
        c = P.put(cands, s, h)
        if c: g.append(c)
    # IMU 第 1 腳標記
    p = pad_of('U2', '1')
    u = comp('U2')
    g.append(Point(u['x'] + (p.x - u['x']) * 1.45, u['y'] + (p.y - u['y']) * 1.45).buffer(0.25))
    return unary_union(g)


def bottom(R):
    m = True
    g = [text(f'FutureZebra x Flix  ONBOARD {B.VERSION}', 0, 15.0, 0.9, mirror=m),
         text('github.com/greenmail1011/flix-drone', 0, 13.6, 0.7, mirror=m),
         text('Flix params:', 0, -3.0, 0.8, mirror=m),
         text('IMU_MODEL 4   PWR_VOLT_PIN 33   PWR_VOLT_SCALE 2', 0, -4.4, 0.7, mirror=m),
         text('Motors: RL=12  RR=13  FR=14  FL=15 (default)', 0, -5.7, 0.7, mirror=m),
         text('I2C (Qwiic): SDA=21  SCL=22', 0, -7.0, 0.7, mirror=m),
         text('J8 sensor: 1 GND  2 5V  3 TX=17  4 RX=16  5V on: IO4', 0, -8.3, 0.7, mirror=m)]
    # 背面：電池備用焊墊 + / −（背面看左右相反，字照實際位置印）
    for nm, t in (('1', '+'), ('2', '-')):
        p = pad_of('BT1', nm)
        g.append(text(t, p.x, p.y + 1.6, 1.2, mirror=m))
    return unary_union(g)


def rails():
    """工藝邊上的字（不在板子上）。"""
    g = [text(f'FutureZebra x Flix ONBOARD {B.VERSION} - break off rails', 0, 29.6, 1.0),
         text('JLCJLCJLCJLC', 0, -36.4, 1.0)]
    return unary_union(g)


def clipped(R, layer, material=None):
    g = top(R) if layer == 'F' else bottom(R)
    g = g.difference(mask_openings(R, layer).buffer(0.1))
    g = g.intersection(B.BOARD.buffer(-0.2))
    if layer == 'F' and material is not None:
        g = unary_union([g, rails().intersection(material.difference(B.BOARD.buffer(1.0)))])
    return g
