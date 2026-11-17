"""把設計資料變成銅箔圖形：焊墊、走線、過孔、鋪銅。每個圖形都帶網路名稱，給 DRC 與連通檢查用。"""
from shapely.geometry import Point, Polygon, box, LineString, MultiPolygon
from shapely.ops import unary_union
from design import *

class Copper:
    """一個銅箔圖形。gerber: ('flash', shape, w, h, x, y) | ('draw', width, pts) | ('region', polygon)"""
    def __init__(self, layer, net, geom, gerber, kind, ref=None):
        self.layer, self.net, self.geom, self.gerber, self.kind, self.ref = layer, net, geom, gerber, kind, ref

FEATS = []      # 所有銅箔
DRILLS = []     # (x, y, d, plated, net)
SMD = []        # (ref, pad, x, y, w, h)  給防焊、鋼網
THT = []        # (x, y, pad_d, drill, net, ref)

def flash_circle(layer, net, x, y, d, kind='pad', ref=None):
    FEATS.append(Copper(layer, net, Point(x, y).buffer(d / 2, 32), ('flash', 'C', d, d, x, y), kind, ref))

def flash_rect(layer, net, x, y, w, h, kind='pad', ref=None):
    FEATS.append(Copper(layer, net, box(x - w / 2, y - h / 2, x + w / 2, y + h / 2), ('flash', 'R', w, h, x, y), kind, ref))

def track(layer, net, pts, w):
    g = LineString(pts).buffer(w / 2, 16)
    FEATS.append(Copper(layer, net, g, ('draw', w, list(pts)), 'track'))

def region(layer, net, poly):
    FEATS.append(Copper(layer, net, poly, ('region', poly), 'region'))

def tht(x, y, pad, drill, net, ref):
    for L in 'FB':
        flash_circle(L, net, x, y, pad, 'tht', ref)
    DRILLS.append((x, y, drill, True, net))
    THT.append((x, y, pad, drill, net, ref))

def via(x, y, net):
    for L in 'FB':
        flash_circle(L, net, x, y, VIA_PAD, 'via')
    DRILLS.append((x, y, VIA_DRILL, True, net))

# ---------------- 元件焊墊 ----------------
for col, names in MINI_PINS.items():
    for n in range(1, 11):
        x, y = pin_xy(col, n)
        net = PIN_NET.get((col, n), f'NC_{col}{n}')
        tht(x, y, HDR_PAD, HDR_DRILL, net, f'J1-{col}{n}')

for name, y in GY_PINS:
    tht(GY_X, y, HDR_PAD, HDR_DRILL, GY_NET[name], f'J2-{name}')

tht(*BAT['BAT+'], BAT_PAD, BAT_DRILL, 'VBAT', 'BAT+')
tht(*BAT['BAT-'], BAT_PAD, BAT_DRILL, 'GND', 'BAT-')

for M in MOTORS:
    m = M['m']
    tht(*M['mpos'], MOT_PAD, MOT_DRILL, 'VBAT', f'M{m}+')
    tht(*M['mneg'], MOT_PAD, MOT_DRILL, f'DRAIN{m}', f'M{m}-')
    for p, net in (('G', f'GATE{m}'), ('S', 'GND'), ('D', f'DRAIN{m}')):
        x, y = q_pad(M, p)
        flash_rect('F', net, x, y, *SOT_PAD, 'smd', f'Q{m}')
        SMD.append((f'Q{m}', p, x, y, *SOT_PAD))
    for k in '12':
        x, y = r_pad(M, k)
        pg = r_pad_for(M, 'G')
        net = f'GATE{m}' if (x, y) == pg else 'GND'
        flash_rect('F', net, x, y, *R_PAD, 'smd', f'R{m}')
        SMD.append((f'R{m}', k, x, y, *R_PAD))
    # 元件內部連線：電阻 ↔ G、電阻 ↔ S、D ↔ 馬達負極
    track('F', f'GATE{m}', [r_pad_for(M, 'G'), q_pad(M, 'G')], 0.3)
    track('F', 'GND', [r_pad_for(M, 'S'), q_pad(M, 'S')], 0.5)
    track('F', f'DRAIN{m}', [q_pad(M, 'D'), M['mneg']], W_MOT)

# ---------------- 電源 VBAT（上層大面積） ----------------
region('F', 'VBAT', box(20.6, -15.4, 22.4, 13.2))          # 右側直條
region('F', 'VBAT', box(-22.4, -15.4, -20.6, 13.2))        # 左側直條
region('F', 'VBAT', box(-22.4, -15.4, 22.4, -13.4))        # 後方橫條
region('F', 'VBAT', box(-3.5, -23.0, -1.5, -15.4))         # 往下接 BAT+
track('F', 'VBAT', [pin_xy('RI', 8), (12.7, -7.62), (12.7, -13.6)], W_PWR)   # MINI32 VCC

# ---------------- IMU（SPI）走線 ----------------
gy = {n: (GY_X, y) for n, y in GY_PINS}
track('F', 'SCK',  [pin_xy('LI', 4), (-8.89, 3.81), (-6.35, 1.27), gy['SCL']], W_SIG)
track('F', 'MOSI', [pin_xy('LI', 6), gy['SDA']], W_SIG)
track('F', 'CS',   [pin_xy('LI', 7), (-8.89, -3.81), (-6.35, -6.35), gy['NCS']], W_SIG)
track('B', 'MISO', [pin_xy('LI', 5), (-10.16, 0.0), (-8.0, 0.0), (-6.27, -2.54), gy['SDO']], W_SIG)
track('B', '3V3',  [pin_xy('LI', 8), (-10.16, -7.62), (-2.6, -7.62), (-2.6, 6.35), gy['3V3']], W_PWR)

# ---------------- 閘極走線（全部要左右交叉，照 Flix 腳位） ----------------
M0, M1, M2, M3 = MOTORS
# GATE0：IO12（右外排）→ 左後 Q0。下層往下，過孔上來，上層往左
track('B', 'GATE0', [pin_xy('RO', 5), (12.7, 0.0), (12.7, -10.16), (9.8, -10.16)], W_SIG)
via(9.8, -10.16, 'GATE0')
g0 = q_pad(M0, 'G')
track('F', 'GATE0', [(9.8, -10.16), (-16.6, -10.16), (-16.6, g0[1]), g0], W_SIG)
# GATE3：IO15（右內排）→ 左前 Q3。上層走 y = 0 這條通道
r3g = r_pad_for(M3, 'G')
track('F', 'GATE3', [pin_xy('RI', 9), (9.6, -7.06), (9.6, 0.0), (-16.0, 0.0), (-16.0, 3.7), (r3g[0], 3.7), r3g], W_SIG)
# GATE1：IO13（左內排）→ 右後 Q1。下層走後方，過孔上來接電阻
r1g = r_pad_for(M1, 'G')
track('B', 'GATE1', [pin_xy('LI', 9), (-10.16, -10.16), (-10.16, -13.4), (15.5, -13.4), (15.5, -3.6)], W_SIG)
via(15.5, -3.6, 'GATE1')
track('F', 'GATE1', [(15.5, -3.6), (r1g[0], -3.6), r1g], W_SIG)
# GATE2：IO14（左外排）→ 右前 Q2。下層走後方最外圈，過孔上來接 G
g2 = q_pad(M2, 'G')
track('B', 'GATE2', [pin_xy('LO', 7), (-12.7, -5.08), (-12.7, -14.2), (16.3, -14.2), (16.3, g2[1])], W_SIG)
via(16.3, g2[1], 'GATE2')
track('F', 'GATE2', [(16.3, g2[1]), g2], W_SIG)

# ---------------- 接地鋪銅（兩面） ----------------
NPTH = [Point(x, y).buffer(MOUNT_D / 2, 32) for x, y in MOUNT_HOLES]

def make_pour(layer, extra_vias=()):
    base = BOARD.buffer(-EDGE_CLR, join_style=2).difference(ANTENNA_KEEPOUT)
    base = base.difference(unary_union([h.buffer(0.5) for h in NPTH]))
    others = [f.geom for f in FEATS if f.layer == layer and f.net != 'GND']
    base = base.difference(unary_union(others).buffer(POUR_CLR, 16))
    # 接地的穿孔焊墊做散熱十字（好焊），貼片的 S 腳直接連
    spokes = []
    for (x, y, pad, drill, net, ref) in THT:
        if net != 'GND': continue
        gap = 0.3
        base = base.difference(Point(x, y).buffer(pad / 2 + gap, 32))
        L = pad / 2 + gap + 0.4
        sw = 0.5 if ref == 'BAT-' else 0.35
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            spokes.append(LineString([(x, y), (x + dx * L, y + dy * L)]).buffer(sw / 2, 8))
    pour = unary_union([base] + spokes + [f.geom for f in FEATS if f.layer == layer and f.net == 'GND'])
    # 外框外的十字修掉；與其他網路再修一次距離
    pour = pour.intersection(BOARD.buffer(-EDGE_CLR, join_style=2)).difference(ANTENNA_KEEPOUT)
    pour = pour.difference(unary_union(others).buffer(POUR_CLR, 16))
    # 只留跟接地焊墊/過孔相連的島
    gnd_feats = unary_union([f.geom for f in FEATS if f.layer == layer and f.net == 'GND'])
    polys = list(pour.geoms) if isinstance(pour, MultiPolygon) else [pour]
    keep = [p for p in polys if p.intersects(gnd_feats) and p.area > 0.5]
    return unary_union(keep)

def add_stitching():
    """在兩面鋪銅都有的地方打接地過孔（2 mm 格點）。"""
    top, bot = make_pour('F'), make_pour('B')
    both = top.intersection(bot).buffer(-(VIA_PAD / 2 + 0.05))
    drills = [Point(x, y).buffer(d / 2 + 0.45) for x, y, d, *_ in DRILLS] + [h.buffer(0.6) for h in NPTH]
    smd_area = unary_union([box(x - w / 2 - 0.4, y - h / 2 - 0.4, x + w / 2 + 0.4, y + h / 2 + 0.4) for _, _, x, y, w, h in SMD])
    keep_out = unary_union(drills + [smd_area] + [z.buffer(0.4) for z in SILK_TEXT_ZONES])
    added = []
    import numpy as np
    # 先在每顆 MOSFET 的 S 腳附近放 3 個（馬達電流從這裡回到電池負極）
    for M in MOTORS:
        sx, sy = q_pad(M, 'S')
        cand = [(sx + dx, sy + dy) for dx in np.arange(-3, 3.01, 0.25) for dy in np.arange(-3, 3.01, 0.25)]
        cand.sort(key=lambda p: (p[0] - sx) ** 2 + (p[1] - sy) ** 2)
        n = 0
        for x, y in cand:
            p = Point(x, y)
            if both.contains(p) and not keep_out.contains(p) and all(p.distance(Point(a)) > 1.0 for a in added):
                added.append((x, y)); n += 1
                if n == 3: break
    for x in np.arange(-22, 22.01, 1.5):
        for y in np.arange(-25, 19.01, 1.5):
            p = Point(x, y)
            if both.contains(p) and not keep_out.contains(p) and all(p.distance(Point(a)) > 3.4 for a in added):
                added.append((x, y))
    for x, y in added:
        via(round(x, 3), round(y, 3), 'GND')
    return added

STITCH = add_stitching()
POUR = {L: make_pour(L) for L in 'FB'}
for L in 'FB':
    region(L, 'GND', POUR[L])
