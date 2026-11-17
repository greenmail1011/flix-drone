"""絲印（文字轉成多邊形）。上層給學生看：G/D/S、GPIO、馬達位置、正負極。"""
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from shapely.geometry import Polygon, LineString, box, Point
from shapely.ops import unary_union
from shapely import affinity
from design import *
import layout as L

FONT = FontProperties(family='DejaVu Sans', weight='bold')
LW = 0.16   # 線寬（JLC 最小 0.153）

def text(s, x, y, h=1.0, anchor='c', mirror=False, angle=0):
    """h = 大寫字高（mm）。anchor: c 置中 / l 靠左 / r 靠右。"""
    tp = TextPath((0, 0), s, size=1.0, prop=FONT)
    geom = Polygon()
    for ring in tp.to_polygons():
        if len(ring) < 3: continue
        geom = geom.symmetric_difference(Polygon(ring).buffer(0))
    cap = TextPath((0, 0), 'H', size=1.0, prop=FONT).get_extents().height
    k = h / cap
    geom = affinity.scale(geom, k, k, origin=(0, 0))
    minx, miny, maxx, maxy = geom.bounds
    cy = h / 2
    dx = {'c': -(minx + maxx) / 2, 'l': -minx, 'r': -maxx}[anchor]
    geom = affinity.translate(geom, dx, -cy)
    if angle: geom = affinity.rotate(geom, angle, origin=(0, 0))
    if mirror: geom = affinity.scale(geom, -1, 1, origin=(0, 0))
    return affinity.translate(geom, x, y)

def line(pts, w=LW):
    return LineString(pts).buffer(w / 2, 8)

def dashed_rect(x0, y0, x1, y1, dash=1.2, gap=0.8):
    out = []
    for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        seg = LineString([a, b]); t = 0
        while t < seg.length:
            out.append(line([seg.interpolate(t).coords[0], seg.interpolate(min(t + dash, seg.length)).coords[0]]))
            t += dash + gap
    return unary_union(out)

def top():
    g = []
    # 機頭方向
    g.append(Polygon([(0, 18.6), (-1.1, 16.9), (1.1, 16.9)]))
    g.append(text('FRONT', 0, 15.7, 1.0))
    g.append(text('MINI32: ANTENNA THIS END', 0, 14.2, 0.75))
    g.append(text('USB THIS END', 0, -12.2, 0.75))
    g.append(dashed_rect(-15.5, -19.3, 15.5, 19.3))
    for col, lab_x in (('LO', -13.97), ('LI', -11.43), ('RI', 11.43), ('RO', 13.97)):
        g.append(text(col, lab_x, 13.55, 0.75))
    # GY-91 焊點
    g.append(text('GY-91 (IMU)', GY_X - 0.2, 8.5, 0.8))
    for name, y in GY_PINS:
        g.append(text(name, GY_X + 1.3, y, 0.8, 'l'))
    # 板名 + JLC 訂單號位置
    g.append(text('FutureZebra x Flix  CARRIER v1.0', 0, -17.6, 0.9))
    g.append(text('JLCJLCJLCJLC', 3.0, 9.7, 0.8))
    # 電池
    g.append(text('+', BAT['BAT+'][0] - 2.3, BAT['BAT+'][1], 1.3))
    g.append(text('-', BAT['BAT-'][0] + 2.3, BAT['BAT-'][1], 1.3))
    g.append(text('BAT 1S', 0, -25.0, 0.8))
    g.append(text('RED', BAT['BAT+'][0] - 2.4, -21.0, 0.7))
    g.append(text('BLK', BAT['BAT-'][0] + 2.4, -21.0, 0.7))
    # 每顆馬達
    for M in MOTORS:
        m, s, f = M['m'], M['side'], M['fr']
        qx, qy = M['q']
        # 腳位字母
        gx, gy = q_pad(M, 'G'); sx, sy = q_pad(M, 'S'); dx, dy = q_pad(M, 'D')
        g.append(text('G', gx + (-0.75 if gx < sx else 0.75), gy - 0.55 * f, 0.65))
        g.append(text('S', sx + (0.75 if sx > gx else -0.75), sy - 0.55 * f, 0.65))
        g.append(text('D', dx - 1.0, dy + 0.1 * f, 0.65))
        # 編號寫在旁邊的 VBAT 直條上（防焊漆蓋住，可以印字）
        g.append(text(f'Q{m}', 21.5 * s, qy, 0.75))
        rx, ry = M['r']
        g.append(text(f'R{m}', 21.5 * s, ry + 0.1 * f, 0.7))
        g.append(text('10k', 21.5 * s, ry - 1.2 * f, 0.6))
        # 馬達焊點
        px, py = M['mpos']; nx, ny = M['mneg']
        g.append(text('+', px, py + 1.75 * f, 1.0))
        g.append(text('-', nx, ny + 1.75 * f, 1.0))
        lx = 18.4 * s
        g.append(text(f'M{m} {M["dir"]}', lx, 16.0 * f, 0.85))
        g.append(text(f'IO{M["gpio"]}', lx, 17.4 * f if f > 0 else -17.1, 0.8))
    return unary_union(g)

def bottom():
    g = [text('FZ Flix carrier v1.0 (bottom)', 0, -17.6, 0.8, mirror=True),
         text('github.com/greenmail1011/flix-drone', 0, 9.6, 0.6, mirror=True)]
    return unary_union(g)

def mask_openings(layer):
    """防焊開窗（與 gerber.py 同一套數字）。"""
    ops = []
    for f in L.FEATS:
        if f.layer == layer and f.kind in ('tht', 'smd'):
            _, shp, w, h, x, y = f.gerber
            if shp == 'C': ops.append(Point(x, y).buffer(w / 2 + 0.05, 32))
            else: ops.append(box(x - w / 2 - 0.05, y - h / 2 - 0.05, x + w / 2 + 0.05, y + h / 2 + 0.05))
    ops += [Point(x, y).buffer(MOUNT_D / 2 + 0.1, 32) for x, y in MOUNT_HOLES]
    return unary_union(ops)

def clipped(layer):
    g = top() if layer == 'F' else bottom()
    g = g.difference(mask_openings(layer).buffer(0.1))
    return g.intersection(BOARD.buffer(-0.2))
